#!/usr/bin/env python3
"""Model future composition execution preconditions without executing anything."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config" / "task-execution-admission-contract.json"
WORKFLOWS_PATH = ROOT / "config" / "workflows.json"
ARTIFACTS_PATH = ROOT / "config" / "typed-artifact-contract.json"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,95}$")
RECEIPT_ID = re.compile(r"^[a-z][a-z0-9-]{15,95}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ExecutionAdmissionError(ValueError):
    pass


def _strict(value: object, required: list[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(required):
        raise ExecutionAdmissionError(f"invalid-{label}-shape")
    return value


def _timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ExecutionAdmissionError(f"invalid-{label}-timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ExecutionAdmissionError(f"invalid-{label}-timestamp") from error
    if parsed.tzinfo != timezone.utc:
        raise ExecutionAdmissionError(f"invalid-{label}-timestamp")
    return parsed


def _scope_payload(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": request["schemaVersion"],
        "admissionId": request["admissionId"],
        "compositionId": request["compositionId"],
        "stepId": request["stepId"],
        "workflowId": request["workflowId"],
        "attempt": request["attempt"],
        "requestedEffects": sorted(request["requestedEffects"]),
        "lifecycle": {
            "mode": request["lifecycle"]["mode"],
            "retryOf": request["lifecycle"]["retryOf"],
            "recoveryOf": request["lifecycle"]["recoveryOf"],
            "cancelRequested": request["lifecycle"]["cancelRequested"],
            "priorAttemptCompleted": request["lifecycle"]["priorAttemptCompleted"],
            "priorSideEffectsPossible": request["lifecycle"]["priorSideEffectsPossible"],
        },
        "intermediateArtifacts": sorted(
            [
                {
                    "artifactId": item["artifactId"],
                    "artifactType": item["artifactType"],
                    "mediaType": item["mediaType"],
                    "sha256": item["sha256"],
                    "byteCount": item["byteCount"],
                    "sourceStepId": item["sourceStepId"],
                }
                for item in request["intermediateArtifacts"]
            ],
            key=lambda item: item["artifactId"],
        ),
    }


def scope_digest(request: dict[str, Any]) -> str:
    encoded = json.dumps(
        _scope_payload(request),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _workflow(registry: dict[str, Any], workflow_id: str) -> dict[str, Any]:
    if registry.get("schemaVersion") != 1 or not isinstance(registry.get("workflows"), list):
        raise ExecutionAdmissionError("workflow-registry-invalid")
    matches = [
        item for item in registry["workflows"]
        if isinstance(item, dict) and item.get("id") == workflow_id
    ]
    if len(matches) != 1 or matches[0].get("uiReady") is not True:
        raise ExecutionAdmissionError("workflow-not-admitted")
    return matches[0]


def _required_effects(workflow: dict[str, Any]) -> list[str]:
    safety = workflow.get("safetyLevel")
    mapping = {
        "read-only": ["process-create"],
        "network-read": ["network-read", "process-create"],
        "controlled-write": ["filesystem-write", "process-create"],
        "approved-write": ["filesystem-write", "process-create"],
        "network-write": ["filesystem-write", "network-read", "process-create"],
    }
    if safety not in mapping:
        raise ExecutionAdmissionError("workflow-safety-level-unsupported")
    return mapping[safety]


def _validate_absent_approval(approval: dict[str, Any]) -> None:
    if (
        approval["present"] is not False
        or approval["receiptId"] is not None
        or approval["scopeDigest"] is not None
        or approval["effectIds"] != []
        or approval["issuer"] is not None
        or approval["audience"] is not None
        or approval["issuedAtUtc"] is not None
        or approval["expiresAtUtc"] is not None
        or approval["evaluationTimeUtc"] is not None
        or approval["used"] is not False
        or approval["revoked"] is not False
    ):
        raise ExecutionAdmissionError("approval-not-allowed-for-nonexecution")


def _validate_artifacts(
    request: dict[str, Any],
    contract: dict[str, Any],
    artifact_contract: dict[str, Any],
) -> None:
    artifacts = request["intermediateArtifacts"]
    maximum = contract["request"]["maximumIntermediateArtifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > maximum:
        raise ExecutionAdmissionError("invalid-intermediate-artifact-count")
    known_types = {
        item["id"]: set(item["mediaTypes"])
        for item in artifact_contract.get("artifactTypes", [])
        if isinstance(item, dict)
    }
    seen: set[str] = set()
    required = contract["intermediateArtifact"]["required"]
    for value in artifacts:
        item = _strict(value, required, "intermediate-artifact")
        artifact_id = item["artifactId"]
        if not isinstance(artifact_id, str) or not RECEIPT_ID.fullmatch(artifact_id) or artifact_id in seen:
            raise ExecutionAdmissionError("invalid-or-duplicate-artifact-id")
        seen.add(artifact_id)
        if item["schemaVersion"] != 1:
            raise ExecutionAdmissionError("unsupported-intermediate-artifact-schema")
        if item["artifactType"] not in known_types:
            raise ExecutionAdmissionError("unknown-intermediate-artifact-type")
        if item["mediaType"] not in known_types[item["artifactType"]]:
            raise ExecutionAdmissionError("intermediate-artifact-media-type-mismatch")
        if not isinstance(item["sha256"], str) or not SHA256.fullmatch(item["sha256"]):
            raise ExecutionAdmissionError("invalid-intermediate-artifact-digest")
        if (
            isinstance(item["byteCount"], bool)
            or not isinstance(item["byteCount"], int)
            or item["byteCount"] <= 0
            or item["byteCount"] > contract["intermediateArtifact"]["maximumByteCount"]
        ):
            raise ExecutionAdmissionError("invalid-intermediate-artifact-size")
        if not isinstance(item["sourceStepId"], str) or not IDENTIFIER.fullmatch(item["sourceStepId"]):
            raise ExecutionAdmissionError("invalid-intermediate-source-step")
        if item["sourceStepId"] == request["stepId"]:
            raise ExecutionAdmissionError("self-sourced-intermediate-artifact")
        if item["validationStatus"] != contract["intermediateArtifact"]["validationStatus"]:
            raise ExecutionAdmissionError("intermediate-artifact-not-validated")


def _result(
    contract: dict[str, Any],
    *,
    state: str,
    request: dict[str, Any],
    workflow: dict[str, Any],
    approval_scope_matched: bool,
    next_gate: str,
) -> dict[str, Any]:
    effects = {
        key[0].upper() + key[1:]: value
        for key, value in contract["effects"].items()
    }
    return {
        "SchemaVersion": 1,
        "Kind": "task-execution-admission-simulation",
        "State": state,
        "AdmissionId": request["admissionId"],
        "CompositionId": request["compositionId"],
        "StepId": request["stepId"],
        "WorkflowId": request["workflowId"],
        "WorkflowSafetyLevel": workflow["safetyLevel"],
        "ScopeDigest": scope_digest(request),
        "ApprovalScopeMatched": approval_scope_matched,
        "ApprovalAcceptedForExecution": False,
        "ExecutionAllowed": False,
        "NextGate": next_gate,
        **effects,
    }


def evaluate(
    request: dict[str, Any],
    contract: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    artifact_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract or json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    registry = registry or json.loads(WORKFLOWS_PATH.read_text(encoding="utf-8"))
    artifact_contract = artifact_contract or json.loads(ARTIFACTS_PATH.read_text(encoding="utf-8"))
    if (
        contract.get("runtimeAdmitted") is not False
        or contract.get("implementationStatus") != "simulation-only"
        or contract["approvalReceipt"].get("opaqueSecretAcceptedBySimulation") is not False
        or contract["approvalReceipt"].get("rendererMayIssue") is not False
        or any(contract["request"].get(field) is not False for field in (
            "rawArgumentsAllowed",
            "rawContentAllowed",
            "rawPathAllowed",
            "rawUrlAllowed",
            "environmentAllowed",
        ))
    ):
        raise ExecutionAdmissionError("unsafe-execution-admission-contract")

    _strict(request, contract["request"]["required"], "request")
    if request["schemaVersion"] != contract["schemaVersion"]:
        raise ExecutionAdmissionError("unsupported-schema")
    for field in ("admissionId", "compositionId", "stepId", "workflowId"):
        if not isinstance(request[field], str) or not IDENTIFIER.fullmatch(request[field]):
            raise ExecutionAdmissionError(f"invalid-{field.replace('Id', '-id').lower()}")
    attempt = request["attempt"]
    if (
        isinstance(attempt, bool)
        or not isinstance(attempt, int)
        or attempt < 0
        or attempt > contract["request"]["maximumAttempts"]
    ):
        raise ExecutionAdmissionError("invalid-attempt")
    workflow = _workflow(registry, request["workflowId"])
    effects = request["requestedEffects"]
    allowed = set(contract["requestedEffects"]["allowedForStructuralEvaluation"])
    prohibited = set(contract["requestedEffects"]["alwaysProhibited"])
    if (
        not isinstance(effects, list)
        or effects != sorted(effects)
        or len(effects) != len(set(effects))
        or not all(isinstance(item, str) for item in effects)
    ):
        raise ExecutionAdmissionError("invalid-requested-effects")
    if any(item in prohibited for item in effects):
        raise ExecutionAdmissionError("prohibited-effect-requested")
    if any(item not in allowed for item in effects):
        raise ExecutionAdmissionError("unknown-effect-requested")
    if effects != _required_effects(workflow):
        raise ExecutionAdmissionError("workflow-effect-disclosure-mismatch")
    _validate_artifacts(request, contract, artifact_contract)
    approval = _strict(
        request["approvalReceipt"],
        contract["approvalReceipt"]["required"],
        "approval-receipt",
    )
    if type(approval["present"]) is not bool:
        raise ExecutionAdmissionError("invalid-approval-presence")

    lifecycle = _strict(request["lifecycle"], contract["lifecycle"]["required"], "lifecycle")
    if lifecycle["mode"] not in contract["lifecycle"]["modes"]:
        raise ExecutionAdmissionError("invalid-lifecycle-mode")
    for field in ("cancelRequested", "priorAttemptCompleted", "priorSideEffectsPossible"):
        if type(lifecycle[field]) is not bool:
            raise ExecutionAdmissionError("invalid-lifecycle-boolean")
    for field in ("retryOf", "recoveryOf"):
        if lifecycle[field] is not None and (
            not isinstance(lifecycle[field], str) or not IDENTIFIER.fullmatch(lifecycle[field])
        ):
            raise ExecutionAdmissionError(f"invalid-{field.replace('Of', '-of').lower()}")
    mode = lifecycle["mode"]
    if mode == "fresh" and (
        attempt != 0
        or lifecycle["retryOf"] is not None
        or lifecycle["recoveryOf"] is not None
        or lifecycle["cancelRequested"]
        or lifecycle["priorAttemptCompleted"]
        or lifecycle["priorSideEffectsPossible"]
    ):
        raise ExecutionAdmissionError("invalid-fresh-lifecycle")
    if mode == "retry" and (
        attempt < 1
        or lifecycle["retryOf"] is None
        or lifecycle["recoveryOf"] is not None
        or lifecycle["cancelRequested"]
        or not lifecycle["priorAttemptCompleted"]
        or lifecycle["priorSideEffectsPossible"]
    ):
        raise ExecutionAdmissionError("invalid-retry-lifecycle")
    if mode == "recover" and (
        attempt < 1
        or lifecycle["recoveryOf"] is None
        or lifecycle["retryOf"] is not None
        or lifecycle["cancelRequested"]
        or lifecycle["priorAttemptCompleted"]
    ):
        raise ExecutionAdmissionError("invalid-recovery-lifecycle")
    if mode == "cancel":
        if (
            not lifecycle["cancelRequested"]
            or lifecycle["retryOf"] is not None
            or lifecycle["recoveryOf"] is not None
        ):
            raise ExecutionAdmissionError("invalid-cancel-lifecycle")
        _validate_absent_approval(approval)
        return _result(
            contract,
            state="cancelled",
            request=request,
            workflow=workflow,
            approval_scope_matched=False,
            next_gate="none; cancellation ends before approval or execution",
        )
    if mode == "recover" and lifecycle["priorSideEffectsPossible"]:
        _validate_absent_approval(approval)
        return _result(
            contract,
            state="recovery-blocked",
            request=request,
            workflow=workflow,
            approval_scope_matched=False,
            next_gate="native effect journal and verified rollback evidence are required",
        )

    if approval["present"] is not True:
        raise ExecutionAdmissionError("approval-receipt-required")
    if not isinstance(approval["receiptId"], str) or not RECEIPT_ID.fullmatch(approval["receiptId"]):
        raise ExecutionAdmissionError("invalid-approval-receipt-id")
    if approval["issuer"] != contract["approvalReceipt"]["issuer"]:
        raise ExecutionAdmissionError("approval-issuer-mismatch")
    if approval["audience"] != contract["approvalReceipt"]["audience"]:
        raise ExecutionAdmissionError("approval-audience-mismatch")
    if approval["effectIds"] != effects:
        raise ExecutionAdmissionError("approval-effect-scope-mismatch")
    if type(approval["used"]) is not bool or type(approval["revoked"]) is not bool:
        raise ExecutionAdmissionError("invalid-approval-state")
    if approval["used"]:
        raise ExecutionAdmissionError("approval-replay")
    if approval["revoked"]:
        raise ExecutionAdmissionError("approval-revoked")
    issued = _timestamp(approval["issuedAtUtc"], "approval-issued")
    expires = _timestamp(approval["expiresAtUtc"], "approval-expiry")
    evaluated = _timestamp(approval["evaluationTimeUtc"], "approval-evaluation")
    if issued > evaluated:
        raise ExecutionAdmissionError("approval-issued-in-future")
    if expires <= issued:
        raise ExecutionAdmissionError("invalid-approval-lifetime")
    if evaluated >= expires:
        raise ExecutionAdmissionError("approval-expired")
    expected_scope = scope_digest(request)
    if not isinstance(approval["scopeDigest"], str) or not SHA256.fullmatch(approval["scopeDigest"]):
        raise ExecutionAdmissionError("invalid-approval-scope-digest")
    if approval["scopeDigest"] != expected_scope:
        raise ExecutionAdmissionError("approval-scope-mismatch")

    return _result(
        contract,
        state="preconditions-modeled",
        request=request,
        workflow=workflow,
        approval_scope_matched=True,
        next_gate="native opaque-token issuer, executor, effect journal, and cross-platform evidence",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Model future task execution admission without runtime authority."
    )
    parser.add_argument("--request", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        result = evaluate(request)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ExecutionAdmissionError) as error:
        print(f"Task execution admission rejected input: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Task execution preconditions modeled; execution remains disabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
