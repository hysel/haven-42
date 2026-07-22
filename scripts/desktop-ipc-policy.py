#!/usr/bin/env python3
"""Fail-closed Haven 42 sidecar IPC admission policy.

This module validates the engine side of the versioned desktop contract. The
future native bridge must independently enforce the same boundary; passing this
module's tests is not native-runtime admission evidence.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class PolicyError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _load_json(relative_path: str) -> dict[str, Any]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise PolicyError("invalid-time")
    return parsed.astimezone(timezone.utc)


def _walk_forbidden(value: Any, forbidden: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden:
                raise PolicyError("forbidden-field")
            _walk_forbidden(child, forbidden)
    elif isinstance(value, list):
        for child in value:
            _walk_forbidden(child, forbidden)


class DesktopIpcPolicy:
    def __init__(self) -> None:
        self.contract = _load_json("config/desktop-ipc-contract.json")
        self.authority = _load_json("config/desktop-capability-policy.json")
        capabilities = _load_json("config/capabilities.json")["capabilities"]
        workflows = _load_json("config/workflows.json")["workflows"]
        self.capabilities = {item["id"]: item for item in capabilities}
        self.workflows = {item["id"]: item for item in workflows}

    def parse_request(self, raw: bytes, runtime: dict[str, Any]) -> dict[str, Any]:
        maximum = self.contract["transport"]["maxMessageBytes"]
        if len(raw) > maximum:
            raise PolicyError("message-too-large")
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise PolicyError("invalid-utf8") from error
        if "\n" in text or "\r" in text:
            raise PolicyError("multiple-lines")
        try:
            request = json.loads(text)
        except json.JSONDecodeError as error:
            raise PolicyError("malformed-json") from error
        if not isinstance(request, dict):
            raise PolicyError("request-not-object")

        definition = self.contract["request"]
        required = set(definition["required"])
        allowed = required | set(definition["properties"])
        keys = set(request)
        if not required <= keys:
            raise PolicyError("missing-required-field")
        if keys - allowed:
            raise PolicyError("additional-property")
        forbidden = set(definition["forbiddenProperties"])
        _walk_forbidden(request, forbidden)

        if request["schemaVersion"] != self.contract["schemaVersion"]:
            raise PolicyError("unsupported-schema")
        if not isinstance(request["requestId"], str) or not REQUEST_ID.fullmatch(request["requestId"]):
            raise PolicyError("invalid-request-id")
        active_ids = set(runtime.get("activeRequestIds", []))
        if request["requestId"] in active_ids:
            raise PolicyError("duplicate-active-request")
        if request["operationKind"] not in {"capability", "workflow"}:
            raise PolicyError("invalid-operation-kind")
        if request["mode"] not in {"plan", "execute", "apply"}:
            raise PolicyError("invalid-mode")
        if not isinstance(request["input"], dict):
            raise PolicyError("input-not-object")
        if "includeOutput" in request and not isinstance(request["includeOutput"], bool):
            raise PolicyError("invalid-include-output")

        operation = self._resolve_operation(request, runtime)
        grants = self._validate_grants(request, runtime)
        effects = self._effects(request, operation)
        if request["mode"] == "apply" and not any(item["type"] in {"repository-write", "artifact-write"} for item in grants):
            raise PolicyError("write-grant-required")
        self._validate_approval(request, runtime, effects, grants)
        return {
            "decision": "allow",
            "requestId": request["requestId"],
            "operationId": request["operationId"],
            "effects": effects,
            "grantIds": [item["grantId"] for item in grants],
        }

    def _resolve_operation(self, request: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
        operation_id = request["operationId"]
        if not isinstance(operation_id, str) or not operation_id:
            raise PolicyError("invalid-operation-id")
        if request["operationKind"] == "workflow":
            operation = self.workflows.get(operation_id)
            if operation is None:
                raise PolicyError("unknown-operation")
            if operation.get("uiReady") is not True:
                raise PolicyError("workflow-not-ui-ready")
            return operation

        operation = self.capabilities.get(operation_id)
        if operation is None:
            raise PolicyError("unknown-operation")
        state = operation["availability"]["state"]
        available_overrides = set(runtime.get("availableCapabilityIds", []))
        if state in {"unavailable", "blocked", "failed"}:
            raise PolicyError("capability-unavailable")
        if state == "configuration-required" and request["mode"] != "plan" and operation_id not in available_overrides:
            raise PolicyError("configuration-required")
        return operation

    def _validate_grants(self, request: dict[str, Any], runtime: dict[str, Any]) -> list[dict[str, Any]]:
        grant_ids = request.get("pathGrantIds", [])
        if not isinstance(grant_ids, list) or len(grant_ids) != len(set(grant_ids)) or not all(isinstance(item, str) for item in grant_ids):
            raise PolicyError("invalid-grant-list")
        grants_by_id = runtime.get("grants", {})
        session_id = runtime.get("sessionId")
        now = _utc(runtime["nowUtc"])
        allowed_types = set(self.contract["pathGrants"]["types"])
        grants: list[dict[str, Any]] = []
        for grant_id in grant_ids:
            grant = grants_by_id.get(grant_id)
            if grant is None:
                raise PolicyError("unknown-grant")
            if grant.get("grantId") != grant_id or grant.get("sessionId") != session_id:
                raise PolicyError("grant-session-mismatch")
            if grant.get("type") not in allowed_types:
                raise PolicyError("grant-type-invalid")
            if _utc(grant["expiresAtUtc"]) <= now:
                raise PolicyError("grant-expired")
            if grant.get("protectedDirectory") is True or grant.get("canonicalizationPassed") is not True:
                raise PolicyError("grant-path-rejected")
            grants.append(grant)
        return grants

    @staticmethod
    def _effects(request: dict[str, Any], operation: dict[str, Any]) -> list[str]:
        if request["mode"] == "plan":
            return []
        effects: set[str] = set()
        if request["operationKind"] == "workflow":
            level = operation.get("safetyLevel")
            if level in {"network-read", "network-write"}:
                effects.add("network access")
            if level == "network-write":
                effects.add("model download")
            if level in {"controlled-write", "approved-write"}:
                effects.add("file write")
        else:
            policy = operation.get("policy", {})
            if policy.get("writesFiles") not in {False, None}:
                effects.add("file write")
            if policy.get("networkAccess") not in {False, "none", None}:
                effects.add("network access")
            if policy.get("downloadsModels") not in {False, None}:
                effects.add("model download")
            if policy.get("externalProvider") not in {False, "none", None}:
                effects.add("external provider")
        if request["mode"] == "apply":
            effects.add("apply mode")
            effects.add("file write")
        return sorted(effects)

    def _validate_approval(
        self,
        request: dict[str, Any],
        runtime: dict[str, Any],
        effects: list[str],
        grants: list[dict[str, Any]],
    ) -> None:
        token_id = request.get("approvalTokenId")
        if not effects and token_id is None:
            return
        if token_id is None:
            raise PolicyError("approval-required")
        token = runtime.get("approvals", {}).get(token_id)
        if token is None:
            raise PolicyError("unknown-approval")
        if token.get("used") is True:
            raise PolicyError("approval-reused")
        if token.get("sessionId") != runtime.get("sessionId"):
            raise PolicyError("approval-session-mismatch")
        if _utc(token["expiresAtUtc"]) <= _utc(runtime["nowUtc"]):
            raise PolicyError("approval-expired")
        expected = {
            "requestId": request["requestId"],
            "operationId": request["operationId"],
            "mode": request["mode"],
            "effects": effects,
            "grantIds": [item["grantId"] for item in grants],
        }
        actual = {key: token.get(key) for key in expected}
        if actual != expected:
            raise PolicyError("approval-binding-mismatch")

    def validate_cancel(self, cancel: dict[str, Any], runtime: dict[str, Any]) -> None:
        if set(cancel) != {"schemaVersion", "requestId", "cancelRequestId"}:
            raise PolicyError("invalid-cancel-shape")
        if cancel["schemaVersion"] != self.contract["schemaVersion"]:
            raise PolicyError("unsupported-schema")
        if not all(isinstance(cancel[key], str) and REQUEST_ID.fullmatch(cancel[key]) for key in ("requestId", "cancelRequestId")):
            raise PolicyError("invalid-request-id")
        owner = runtime.get("activeRequests", {}).get(cancel["cancelRequestId"])
        if owner is None:
            raise PolicyError("cancel-target-inactive")
        if owner != runtime.get("sessionId"):
            raise PolicyError("cancel-session-mismatch")

    def validate_events(self, events: list[dict[str, Any]], request_id: str) -> None:
        allowed_types = set(self.contract["events"]["types"])
        terminal_types = set(self.contract["events"]["terminalTypes"])
        terminal_count = 0
        for expected_sequence, event in enumerate(events, start=1):
            if event.get("requestId") != request_id or event.get("schemaVersion") != self.contract["schemaVersion"]:
                raise PolicyError("event-binding-mismatch")
            if event.get("sequence") != expected_sequence:
                raise PolicyError("event-sequence-invalid")
            if event.get("type") not in allowed_types:
                raise PolicyError("event-type-invalid")
            if event["type"] in terminal_types:
                terminal_count += 1
                if expected_sequence != len(events):
                    raise PolicyError("event-after-terminal")
        if terminal_count != 1:
            raise PolicyError("terminal-event-count")


def _base_runtime() -> dict[str, Any]:
    return {
        "sessionId": "session-a",
        "nowUtc": "2026-07-22T16:00:00Z",
        "activeRequestIds": [],
        "availableCapabilityIds": [],
        "grants": {
            "grant-write": {
                "grantId": "grant-write",
                "type": "repository-write",
                "sessionId": "session-a",
                "expiresAtUtc": "2026-07-22T16:05:00Z",
                "canonicalizationPassed": True,
                "protectedDirectory": False,
            }
        },
        "approvals": {},
        "activeRequests": {"active-a": "session-a", "active-b": "session-b"},
    }


def _request(**updates: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schemaVersion": 1,
        "requestId": "request-1",
        "operationKind": "workflow",
        "operationId": "profile-local-hardware",
        "mode": "plan",
        "input": {},
    }
    value.update(updates)
    return value


def _encoded(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8")


def _expect_error(code: str, callback: Any) -> None:
    try:
        callback()
    except PolicyError as error:
        if error.code != code:
            raise AssertionError(f"expected {code}, received {error.code}") from error
        return
    raise AssertionError(f"expected {code}")


def run_self_tests() -> int:
    policy = DesktopIpcPolicy()
    runtime = _base_runtime()
    passed = 0

    def allow(request: dict[str, Any]) -> None:
        nonlocal passed
        assert policy.parse_request(_encoded(request), copy.deepcopy(runtime))["decision"] == "allow"
        passed += 1

    def deny(code: str, raw: bytes, state: dict[str, Any] | None = None) -> None:
        nonlocal passed
        _expect_error(code, lambda: policy.parse_request(raw, copy.deepcopy(state or runtime)))
        passed += 1

    allow(_request())
    deny("malformed-json", b"{")
    deny("invalid-utf8", b"\xff")
    deny("multiple-lines", _encoded(_request()) + b"\n{}")
    deny("message-too-large", b" " * (policy.contract["transport"]["maxMessageBytes"] + 1))
    deny("unsupported-schema", _encoded(_request(schemaVersion=2)))
    deny("additional-property", _encoded(_request(extra=True)))
    deny("forbidden-field", _encoded(_request(input={"command": "calc.exe"})))
    deny("invalid-request-id", _encoded(_request(requestId="bad request")))
    duplicate = _base_runtime()
    duplicate["activeRequestIds"] = ["request-1"]
    deny("duplicate-active-request", _encoded(_request()), duplicate)
    deny("unknown-operation", _encoded(_request(operationId="unknown.workflow")))
    deny("workflow-not-ui-ready", _encoded(_request(operationId="build-release-package")))
    deny("configuration-required", _encoded(_request(operationKind="capability", operationId="general.chat", mode="execute")))
    allow(_request(operationKind="capability", operationId="general.chat", mode="plan"))
    deny("approval-required", _encoded(_request(operationId="apply-agent-config", mode="apply", pathGrantIds=["grant-write"])))
    deny("write-grant-required", _encoded(_request(operationId="apply-agent-config", mode="apply", approvalTokenId="approval-ok")))
    expired_grant = _base_runtime()
    expired_grant["grants"]["grant-write"]["expiresAtUtc"] = "2026-07-22T15:59:00Z"
    deny("grant-expired", _encoded(_request(pathGrantIds=["grant-write"])), expired_grant)
    cross_grant = _base_runtime()
    cross_grant["grants"]["grant-write"]["sessionId"] = "session-b"
    deny("grant-session-mismatch", _encoded(_request(pathGrantIds=["grant-write"])), cross_grant)
    protected = _base_runtime()
    protected["grants"]["grant-write"]["protectedDirectory"] = True
    deny("grant-path-rejected", _encoded(_request(pathGrantIds=["grant-write"])), protected)

    approved_request = _request(
        operationId="apply-agent-config",
        mode="apply",
        pathGrantIds=["grant-write"],
        approvalTokenId="approval-ok",
    )
    approved_runtime = _base_runtime()
    approved_runtime["approvals"]["approval-ok"] = {
        "requestId": "request-1",
        "operationId": "apply-agent-config",
        "mode": "apply",
        "effects": ["apply mode", "file write"],
        "grantIds": ["grant-write"],
        "sessionId": "session-a",
        "expiresAtUtc": "2026-07-22T16:05:00Z",
        "used": False,
    }
    assert policy.parse_request(_encoded(approved_request), copy.deepcopy(approved_runtime))["decision"] == "allow"
    passed += 1
    reused = copy.deepcopy(approved_runtime)
    reused["approvals"]["approval-ok"]["used"] = True
    deny("approval-reused", _encoded(approved_request), reused)
    altered = copy.deepcopy(approved_runtime)
    altered["approvals"]["approval-ok"]["mode"] = "execute"
    deny("approval-binding-mismatch", _encoded(approved_request), altered)
    expired_approval = copy.deepcopy(approved_runtime)
    expired_approval["approvals"]["approval-ok"]["expiresAtUtc"] = "2026-07-22T15:59:00Z"
    deny("approval-expired", _encoded(approved_request), expired_approval)

    policy.validate_cancel({"schemaVersion": 1, "requestId": "cancel-1", "cancelRequestId": "active-a"}, runtime)
    passed += 1
    _expect_error("cancel-session-mismatch", lambda: policy.validate_cancel({"schemaVersion": 1, "requestId": "cancel-1", "cancelRequestId": "active-b"}, runtime))
    passed += 1
    _expect_error("invalid-cancel-shape", lambda: policy.validate_cancel({"schemaVersion": 1, "requestId": "cancel-1", "cancelRequestId": "active-a", "pid": 1}, runtime))
    passed += 1

    valid_events = [
        {"schemaVersion": 1, "requestId": "request-1", "sequence": 1, "type": "accepted"},
        {"schemaVersion": 1, "requestId": "request-1", "sequence": 2, "type": "result"},
    ]
    policy.validate_events(valid_events, "request-1")
    passed += 1
    bad_sequence = copy.deepcopy(valid_events)
    bad_sequence[1]["sequence"] = 3
    _expect_error("event-sequence-invalid", lambda: policy.validate_events(bad_sequence, "request-1"))
    passed += 1
    duplicate_terminal = valid_events + [{"schemaVersion": 1, "requestId": "request-1", "sequence": 3, "type": "error"}]
    _expect_error("event-after-terminal", lambda: policy.validate_events(duplicate_terminal, "request-1"))
    passed += 1

    print(f"Desktop IPC sidecar policy self-test passed: {passed} cases.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Haven 42 sidecar IPC admission policy.")
    parser.add_argument("--self-test", action="store_true", help="Run the hostile offline regression suite.")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("Only --self-test is exposed until the packaged sidecar lifecycle is admitted.")
    return run_self_tests()


if __name__ == "__main__":
    sys.exit(main())
