#!/usr/bin/env python3
"""Executable fail-closed model for future native-bridge authority.

This module starts no process, opens no link, grants no filesystem authority,
and contains no Tauri runtime. It makes the native boundary testable while the
published dependency graph remains blocked.
"""

from __future__ import annotations

import argparse
import copy
import json
import ntpath
import posixpath
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class BoundaryError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise BoundaryError("invalid-time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise BoundaryError("invalid-time") from error
    if parsed.tzinfo is None:
        raise BoundaryError("invalid-time")
    return parsed.astimezone(timezone.utc)


class NativeBridgeBoundaryPolicy:
    def __init__(self) -> None:
        self.contract = json.loads((ROOT / "config/native-bridge-boundary-contract.json").read_text(encoding="utf-8"))

    def issue_path_grant(self, selection: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
        required = {
            "selectionSource", "grantType", "platform", "canonicalRoot", "resolvedRoot",
            "exists", "networkPath", "symlinkOrReparseEscape", "protectedPurpose",
            "sessionId", "issuedAtUtc", "expiresAtUtc", "grantId"
        }
        if set(selection) != required:
            raise BoundaryError("selection-shape-invalid")
        string_fields = ("selectionSource", "grantType", "platform", "canonicalRoot", "resolvedRoot", "sessionId", "issuedAtUtc", "expiresAtUtc", "grantId")
        boolean_fields = ("exists", "networkPath", "symlinkOrReparseEscape")
        if not all(isinstance(selection[field], str) for field in string_fields):
            raise BoundaryError("selection-type-invalid")
        if not all(isinstance(selection[field], bool) for field in boolean_fields):
            raise BoundaryError("selection-type-invalid")
        if selection["protectedPurpose"] is not None and not isinstance(selection["protectedPurpose"], str):
            raise BoundaryError("selection-type-invalid")
        policy = self.contract["pathGrants"]
        if selection["selectionSource"] not in policy["allowedSelectionSources"]:
            raise BoundaryError("selection-source-invalid")
        if selection["grantType"] not in policy["allowedTypes"]:
            raise BoundaryError("grant-type-invalid")
        if selection["sessionId"] != runtime.get("sessionId"):
            raise BoundaryError("grant-session-mismatch")
        if not isinstance(selection["grantId"], str) or not ID.fullmatch(selection["grantId"]):
            raise BoundaryError("grant-id-invalid")
        if selection["grantId"] in set(runtime.get("issuedGrantIds", [])):
            raise BoundaryError("grant-id-reused")
        if selection["exists"] is not True:
            raise BoundaryError("canonical-root-missing")
        if selection["networkPath"] is not False:
            raise BoundaryError("network-path-rejected")
        if selection["symlinkOrReparseEscape"] is not False:
            raise BoundaryError("path-escape-rejected")
        if selection["protectedPurpose"] is not None:
            if selection["protectedPurpose"] in policy["protectedPurposes"]:
                raise BoundaryError("protected-path-rejected")
            raise BoundaryError("protected-purpose-invalid")
        platform = selection["platform"]
        if platform == "windows":
            path_api = ntpath
            canonical = path_api.normcase(path_api.normpath(selection["canonicalRoot"]))
            resolved = path_api.normcase(path_api.normpath(selection["resolvedRoot"]))
            absolute = path_api.isabs(canonical)
            network = canonical.startswith("\\\\")
        elif platform in {"linux", "macos"}:
            path_api = posixpath
            canonical = path_api.normpath(selection["canonicalRoot"])
            resolved = path_api.normpath(selection["resolvedRoot"])
            absolute = path_api.isabs(canonical)
            network = False
        else:
            raise BoundaryError("platform-invalid")
        if not absolute or network:
            raise BoundaryError("canonical-root-invalid")
        if any(part == ".." for part in selection["canonicalRoot"].replace("\\", "/").split("/")):
            raise BoundaryError("path-traversal-rejected")
        if canonical != resolved:
            raise BoundaryError("canonical-resolution-mismatch")
        issued = _utc(selection["issuedAtUtc"])
        expires = _utc(selection["expiresAtUtc"])
        now = _utc(runtime["nowUtc"])
        lifetime = (expires - issued).total_seconds()
        if issued > now or expires <= now or lifetime <= 0 or lifetime > policy["maximumLifetimeSeconds"]:
            raise BoundaryError("grant-lifetime-invalid")
        return {
            "decision": "allow",
            "grantId": selection["grantId"],
            "grantType": selection["grantType"],
            "sessionId": selection["sessionId"],
            "expiresAtUtc": selection["expiresAtUtc"],
            "canonicalRootReturned": False,
        }

    def validate_external_link(self, request: dict[str, Any]) -> dict[str, Any]:
        if set(request) != {"url", "explicitUserGesture"}:
            raise BoundaryError("external-link-shape-invalid")
        if request["explicitUserGesture"] is not True:
            raise BoundaryError("external-link-gesture-required")
        if not isinstance(request["url"], str) or len(request["url"]) > 2048:
            raise BoundaryError("external-link-invalid")
        if any(ord(character) < 32 or ord(character) == 127 for character in request["url"]):
            raise BoundaryError("external-link-invalid")
        parsed = urlsplit(request["url"])
        policy = self.contract["externalLinks"]
        if parsed.scheme not in policy["allowedSchemes"]:
            raise BoundaryError("external-link-scheme-rejected")
        if parsed.username is not None or parsed.password is not None:
            raise BoundaryError("external-link-credentials-rejected")
        try:
            port = parsed.port
        except ValueError as error:
            raise BoundaryError("external-link-port-rejected") from error
        if port not in {None, 443}:
            raise BoundaryError("external-link-port-rejected")
        host = (parsed.hostname or "").lower()
        path = parsed.path or "/"
        if path != unquote(path):
            raise BoundaryError("external-link-invalid")
        def path_matches(path_value: str, prefix: str) -> bool:
            if prefix == "/":
                return path_value.startswith("/")
            boundary = prefix.rstrip("/")
            return path_value == boundary or path_value.startswith(boundary + "/")
        allowed = any(
            host == item["host"] and any(path_matches(path, prefix) for prefix in item["pathPrefixes"])
            for item in policy["allowlist"]
        )
        if not allowed:
            raise BoundaryError("external-link-not-allowlisted")
        return {"decision": "allow", "scheme": "https", "host": host, "userGestureVerified": True}

    def transition_sidecar(self, state: str, event: str, context: dict[str, Any] | None = None) -> str:
        lifecycle = self.contract["sidecarLifecycle"]
        if state not in lifecycle["states"]:
            raise BoundaryError("sidecar-state-invalid")
        next_state = lifecycle["allowedTransitions"].get(state, {}).get(event)
        if next_state is None:
            raise BoundaryError("sidecar-transition-rejected")
        if event == "start-requested":
            required = {
                "packagedBinaryIdentityVerified": True,
                "targetTripleMatched": True,
                "rendererSuppliedBinary": False,
                "rendererSuppliedArguments": False,
                "rendererSuppliedWorkingDirectory": False,
                "singleSidecar": True,
                "privateStdio": True,
                "listeningSocket": False,
                "elevated": False,
                "serviceInstall": False,
                "startupEntry": False,
                "firewallChange": False,
            }
            if context is None or set(context) != set(required):
                raise BoundaryError("sidecar-start-shape-invalid")
            if context != required:
                raise BoundaryError("sidecar-start-policy-rejected")
        elif context is not None:
            raise BoundaryError("sidecar-context-unexpected")
        return next_state

    def filter_environment(self, environment: dict[str, Any]) -> dict[str, str]:
        if not isinstance(environment, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in environment.items()):
            raise BoundaryError("environment-invalid")
        allowed = set(self.contract["sidecarLifecycle"]["environmentAllowlist"])
        return {key: value for key, value in environment.items() if key in allowed}

    @staticmethod
    def validate_cancel(request: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
        if set(request) != {"requestId", "cancelRequestId"}:
            raise BoundaryError("cancel-shape-invalid")
        if not all(isinstance(request[key], str) and ID.fullmatch(request[key]) for key in request):
            raise BoundaryError("cancel-id-invalid")
        owner = runtime.get("activeRequests", {}).get(request["cancelRequestId"])
        if owner is None:
            raise BoundaryError("cancel-target-inactive")
        if owner != runtime.get("sessionId"):
            raise BoundaryError("cancel-session-mismatch")
        return {"decision": "allow", "cancelRequestId": request["cancelRequestId"], "osPidUsed": False, "signalSelectedByRenderer": False}

    def validate_approval(self, token: dict[str, Any], request: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
        bound = set(self.contract["approvalTokens"]["boundFields"])
        required = bound | {"tokenId", "issuedAtUtc", "expiresAtUtc", "used"}
        if set(token) != required:
            raise BoundaryError("approval-shape-invalid")
        if token["used"] is not False:
            raise BoundaryError("approval-reused")
        if token["sessionId"] != runtime.get("sessionId"):
            raise BoundaryError("approval-session-mismatch")
        if not isinstance(token["tokenId"], str) or not ID.fullmatch(token["tokenId"]):
            raise BoundaryError("approval-id-invalid")
        issued = _utc(token["issuedAtUtc"])
        expires = _utc(token["expiresAtUtc"])
        now = _utc(runtime["nowUtc"])
        lifetime = (expires - issued).total_seconds()
        if issued > now or expires <= now or lifetime <= 0 or lifetime > self.contract["approvalTokens"]["maximumLifetimeSeconds"]:
            raise BoundaryError("approval-lifetime-invalid")
        actual = {field: token.get(field) for field in bound}
        expected = {field: request.get(field) for field in bound}
        if actual != expected:
            raise BoundaryError("approval-binding-mismatch")
        return {"decision": "allow", "tokenId": token["tokenId"], "consumeRequired": True}


def _expect(code: str, callback: Any) -> None:
    try:
        callback()
    except BoundaryError as error:
        if error.code != code:
            raise AssertionError(f"expected {code}, received {error.code}") from error
        return
    raise AssertionError(f"expected {code}")


def _runtime() -> dict[str, Any]:
    return {
        "sessionId": "session-a",
        "nowUtc": "2026-07-22T20:00:00Z",
        "issuedGrantIds": [],
        "activeRequests": {"active-a": "session-a", "active-b": "session-b"},
    }


def _selection(**updates: Any) -> dict[str, Any]:
    value = {
        "selectionSource": "native-user-dialog",
        "grantType": "repository-read",
        "platform": "windows",
        "canonicalRoot": "C:\\Haven42Fixture\\project",
        "resolvedRoot": "C:\\Haven42Fixture\\project",
        "exists": True,
        "networkPath": False,
        "symlinkOrReparseEscape": False,
        "protectedPurpose": None,
        "sessionId": "session-a",
        "issuedAtUtc": "2026-07-22T19:59:00Z",
        "expiresAtUtc": "2026-07-22T20:04:00Z",
        "grantId": "grant-a",
    }
    value.update(updates)
    return value


def _start(**updates: Any) -> dict[str, Any]:
    value = {
        "packagedBinaryIdentityVerified": True,
        "targetTripleMatched": True,
        "rendererSuppliedBinary": False,
        "rendererSuppliedArguments": False,
        "rendererSuppliedWorkingDirectory": False,
        "singleSidecar": True,
        "privateStdio": True,
        "listeningSocket": False,
        "elevated": False,
        "serviceInstall": False,
        "startupEntry": False,
        "firewallChange": False,
    }
    value.update(updates)
    return value


def run_self_tests() -> int:
    policy = NativeBridgeBoundaryPolicy()
    runtime = _runtime()
    passed = 0

    def allow(callback: Any) -> Any:
        nonlocal passed
        result = callback()
        passed += 1
        return result

    def deny(code: str, callback: Any) -> None:
        nonlocal passed
        _expect(code, callback)
        passed += 1

    grant = allow(lambda: policy.issue_path_grant(_selection(), runtime))
    assert grant["canonicalRootReturned"] is False
    allow(lambda: policy.issue_path_grant(_selection(platform="linux", canonicalRoot="/srv/haven42/project", resolvedRoot="/srv/haven42/project", grantId="grant-linux"), runtime))
    deny("selection-shape-invalid", lambda: policy.issue_path_grant({**_selection(), "rawRendererPath": "C:\\temp"}, runtime))
    deny("selection-source-invalid", lambda: policy.issue_path_grant(_selection(selectionSource="renderer"), runtime))
    deny("grant-type-invalid", lambda: policy.issue_path_grant(_selection(grantType="engine-write"), runtime))
    deny("grant-session-mismatch", lambda: policy.issue_path_grant(_selection(sessionId="session-b"), runtime))
    deny("grant-id-invalid", lambda: policy.issue_path_grant(_selection(grantId="bad id"), runtime))
    reused_runtime = copy.deepcopy(runtime); reused_runtime["issuedGrantIds"] = ["grant-a"]
    deny("grant-id-reused", lambda: policy.issue_path_grant(_selection(), reused_runtime))
    deny("canonical-root-missing", lambda: policy.issue_path_grant(_selection(exists=False), runtime))
    deny("network-path-rejected", lambda: policy.issue_path_grant(_selection(networkPath=True), runtime))
    deny("path-escape-rejected", lambda: policy.issue_path_grant(_selection(symlinkOrReparseEscape=True), runtime))
    deny("protected-path-rejected", lambda: policy.issue_path_grant(_selection(protectedPurpose="credentials"), runtime))
    deny("protected-purpose-invalid", lambda: policy.issue_path_grant(_selection(protectedPurpose="unknown"), runtime))
    deny("platform-invalid", lambda: policy.issue_path_grant(_selection(platform="android"), runtime))
    deny("canonical-root-invalid", lambda: policy.issue_path_grant(_selection(canonicalRoot="relative\\project", resolvedRoot="relative\\project"), runtime))
    deny("path-traversal-rejected", lambda: policy.issue_path_grant(_selection(canonicalRoot="C:\\Haven42Fixture\\..\\secret", resolvedRoot="C:\\secret"), runtime))
    deny("canonical-resolution-mismatch", lambda: policy.issue_path_grant(_selection(resolvedRoot="C:\\Haven42Fixture\\elsewhere"), runtime))
    deny("grant-lifetime-invalid", lambda: policy.issue_path_grant(_selection(expiresAtUtc="2026-07-22T20:10:00Z"), runtime))
    deny("selection-type-invalid", lambda: policy.issue_path_grant(_selection(canonicalRoot=42), runtime))
    deny("selection-type-invalid", lambda: policy.issue_path_grant(_selection(networkPath="false"), runtime))

    allow(lambda: policy.validate_external_link({"url": "https://github.com/hysel/haven-42/wiki", "explicitUserGesture": True}))
    allow(lambda: policy.validate_external_link({"url": "https://tauri.app/security/capabilities/#scope", "explicitUserGesture": True}))
    deny("external-link-gesture-required", lambda: policy.validate_external_link({"url": "https://github.com/hysel/haven-42", "explicitUserGesture": False}))
    deny("external-link-scheme-rejected", lambda: policy.validate_external_link({"url": "http://github.com/hysel/haven-42", "explicitUserGesture": True}))
    deny("external-link-credentials-rejected", lambda: policy.validate_external_link({"url": "https://user:pass@github.com/hysel/haven-42", "explicitUserGesture": True}))
    deny("external-link-port-rejected", lambda: policy.validate_external_link({"url": "https://github.com:8443/hysel/haven-42", "explicitUserGesture": True}))
    deny("external-link-not-allowlisted", lambda: policy.validate_external_link({"url": "https://example.invalid/hysel/haven-42", "explicitUserGesture": True}))
    deny("external-link-not-allowlisted", lambda: policy.validate_external_link({"url": "https://github.com/other/repository", "explicitUserGesture": True}))
    deny("external-link-not-allowlisted", lambda: policy.validate_external_link({"url": "https://github.com/hysel/haven-42-malicious", "explicitUserGesture": True}))
    deny("external-link-invalid", lambda: policy.validate_external_link({"url": "https://github.com/hysel/haven-42\nmalicious", "explicitUserGesture": True}))
    deny("external-link-invalid", lambda: policy.validate_external_link({"url": "https://github.com/hysel/haven-42%2Fwiki", "explicitUserGesture": True}))

    state = allow(lambda: policy.transition_sidecar("stopped", "start-requested", _start()))
    state = allow(lambda: policy.transition_sidecar(state, "start-succeeded"))
    state = allow(lambda: policy.transition_sidecar(state, "stop-requested"))
    state = allow(lambda: policy.transition_sidecar(state, "exited"))
    assert state == "stopped"
    deny("sidecar-transition-rejected", lambda: policy.transition_sidecar("stopped", "exited"))
    deny("sidecar-context-unexpected", lambda: policy.transition_sidecar("running", "stop-requested", {}))
    deny("sidecar-start-policy-rejected", lambda: policy.transition_sidecar("stopped", "start-requested", _start(rendererSuppliedArguments=True)))
    deny("sidecar-start-policy-rejected", lambda: policy.transition_sidecar("stopped", "start-requested", _start(elevated=True)))
    deny("sidecar-start-policy-rejected", lambda: policy.transition_sidecar("stopped", "start-requested", _start(listeningSocket=True)))
    deny("sidecar-start-policy-rejected", lambda: policy.transition_sidecar("stopped", "start-requested", _start(serviceInstall=True)))
    allow(lambda: policy.transition_sidecar("running", "crashed"))
    allow(lambda: policy.transition_sidecar("crashed", "reset"))
    filtered = allow(lambda: policy.filter_environment({"SystemRoot": "C:\\Windows", "LANG": "en_US.UTF-8", "TOKEN": "secret", "AWS_SECRET_ACCESS_KEY": "secret"}))
    assert set(filtered) == {"SystemRoot", "LANG"}
    deny("environment-invalid", lambda: policy.filter_environment({"LANG": 42}))

    cancel = allow(lambda: policy.validate_cancel({"requestId": "cancel-a", "cancelRequestId": "active-a"}, runtime))
    assert cancel["osPidUsed"] is False
    deny("cancel-target-inactive", lambda: policy.validate_cancel({"requestId": "cancel-a", "cancelRequestId": "missing"}, runtime))
    deny("cancel-session-mismatch", lambda: policy.validate_cancel({"requestId": "cancel-a", "cancelRequestId": "active-b"}, runtime))
    deny("cancel-shape-invalid", lambda: policy.validate_cancel({"requestId": "cancel-a", "cancelRequestId": "active-a", "pid": 1234}, runtime))

    request = {
        "sessionId": "session-a", "requestId": "request-a", "operationId": "apply-agent-config",
        "mode": "apply", "effects": ["file write"], "grantIds": ["grant-a"], "inputDigest": "sha256:fixture"
    }
    token = {**request, "tokenId": "approval-a", "issuedAtUtc": "2026-07-22T19:59:00Z", "expiresAtUtc": "2026-07-22T20:01:00Z", "used": False}
    allow(lambda: policy.validate_approval(token, request, runtime))
    deny("approval-reused", lambda: policy.validate_approval({**token, "used": True}, request, runtime))
    deny("approval-session-mismatch", lambda: policy.validate_approval({**token, "sessionId": "session-b"}, request, runtime))
    deny("approval-lifetime-invalid", lambda: policy.validate_approval({**token, "expiresAtUtc": "2026-07-22T20:05:00Z"}, request, runtime))
    deny("approval-binding-mismatch", lambda: policy.validate_approval(token, {**request, "effects": ["file write", "network access"]}, runtime))
    deny("approval-shape-invalid", lambda: policy.validate_approval({**token, "remember": True}, request, runtime))

    assert passed == 55
    print(f"Native bridge boundary policy self-test passed: {passed} cases")
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the non-runtime native bridge authority policy.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("Only --self-test is available; this policy model grants no production authority.")
    run_self_tests()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
