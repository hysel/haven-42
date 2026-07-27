#!/usr/bin/env python3
"""Hostile tests for the effect-free future execution-admission boundary."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "task_execution_admission",
    ROOT / "scripts" / "simulate-task-execution-admission.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT = json.loads((ROOT / "config/task-execution-admission-contract.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "config/workflows.json").read_text(encoding="utf-8"))
ARTIFACTS = json.loads((ROOT / "config/typed-artifact-contract.json").read_text(encoding="utf-8"))
FIXTURE_PATH = ROOT / "examples" / "fixtures" / "task-execution-admission-request.json"


def evaluate(value):
    return MODULE.evaluate(value, CONTRACT, REGISTRY, ARTIFACTS)


def rejected(value, code):
    try:
        evaluate(value)
    except MODULE.ExecutionAdmissionError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"execution admission unexpectedly accepted: {code}")


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["approvalReceipt"]["scopeDigest"] = MODULE.scope_digest(fixture)
    result = evaluate(copy.deepcopy(fixture))
    assert result["State"] == "preconditions-modeled"
    assert result["ApprovalScopeMatched"] is True
    assert result["ApprovalAcceptedForExecution"] is False
    assert result["ExecutionAllowed"] is False
    effect_fields = [
        key for key in result
        if key.endswith(("Created", "Accessed", "Used", "Modified", "Issued", "Consumed", "Read", "Written"))
    ]
    assert effect_fields and all(result[key] is False for key in effect_fields)
    passed = 1

    def deny(mutator, code):
        nonlocal passed
        value = copy.deepcopy(fixture)
        mutator(value)
        rejected(value, code)
        passed += 1

    cases = [
        (lambda value: value.update(extra=True), "invalid-request-shape"),
        (lambda value: value.update(schemaVersion=2), "unsupported-schema"),
        (lambda value: value.update(admissionId="../bad"), "invalid-admission-id"),
        (lambda value: value.update(compositionId="../bad"), "invalid-composition-id"),
        (lambda value: value.update(stepId="../bad"), "invalid-step-id"),
        (lambda value: value.update(workflowId="unknown"), "workflow-not-admitted"),
        (lambda value: value.update(attempt=True), "invalid-attempt"),
        (lambda value: value.update(attempt=3), "invalid-attempt"),
        (lambda value: value.update(requestedEffects=["process-create", "filesystem-write"]), "invalid-requested-effects"),
        (lambda value: value.update(requestedEffects=["process-create", "process-create"]), "invalid-requested-effects"),
        (lambda value: value.update(requestedEffects=["machine-modification"]), "prohibited-effect-requested"),
        (lambda value: value.update(requestedEffects=["unknown-effect"]), "unknown-effect-requested"),
        (lambda value: value.update(requestedEffects=["process-create"]), "workflow-effect-disclosure-mismatch"),
        (lambda value: value["intermediateArtifacts"].append(copy.deepcopy(value["intermediateArtifacts"][0])), "invalid-or-duplicate-artifact-id"),
        (lambda value: value["intermediateArtifacts"][0].update(extra=True), "invalid-intermediate-artifact-shape"),
        (lambda value: value["intermediateArtifacts"][0].update(schemaVersion=2), "unsupported-intermediate-artifact-schema"),
        (lambda value: value["intermediateArtifacts"][0].update(artifactType="unknown"), "unknown-intermediate-artifact-type"),
        (lambda value: value["intermediateArtifacts"][0].update(mediaType="image/png"), "intermediate-artifact-media-type-mismatch"),
        (lambda value: value["intermediateArtifacts"][0].update(sha256="ABC"), "invalid-intermediate-artifact-digest"),
        (lambda value: value["intermediateArtifacts"][0].update(byteCount=0), "invalid-intermediate-artifact-size"),
        (lambda value: value["intermediateArtifacts"][0].update(sourceStepId="../bad"), "invalid-intermediate-source-step"),
        (lambda value: value["intermediateArtifacts"][0].update(sourceStepId=value["stepId"]), "self-sourced-intermediate-artifact"),
        (lambda value: value["intermediateArtifacts"][0].update(validationStatus="renderer-validated"), "intermediate-artifact-not-validated"),
        (lambda value: value["lifecycle"].update(extra=True), "invalid-lifecycle-shape"),
        (lambda value: value["lifecycle"].update(mode="resume"), "invalid-lifecycle-mode"),
        (lambda value: value["lifecycle"].update(cancelRequested="false"), "invalid-lifecycle-boolean"),
        (lambda value: value["approvalReceipt"].update(present=False), "approval-receipt-required"),
        (lambda value: value["approvalReceipt"].update(extra=True), "invalid-approval-receipt-shape"),
        (lambda value: value["approvalReceipt"].update(receiptId="short"), "invalid-approval-receipt-id"),
        (lambda value: value["approvalReceipt"].update(issuer="renderer"), "approval-issuer-mismatch"),
        (lambda value: value["approvalReceipt"].update(audience="other"), "approval-audience-mismatch"),
        (lambda value: value["approvalReceipt"].update(effectIds=["process-create"]), "approval-effect-scope-mismatch"),
        (lambda value: value["approvalReceipt"].update(used=True), "approval-replay"),
        (lambda value: value["approvalReceipt"].update(revoked=True), "approval-revoked"),
        (lambda value: value["approvalReceipt"].update(issuedAtUtc="2026-07-27T12:30:00Z"), "approval-issued-in-future"),
        (lambda value: value["approvalReceipt"].update(expiresAtUtc="2026-07-27T11:00:00Z"), "invalid-approval-lifetime"),
        (lambda value: value["approvalReceipt"].update(evaluationTimeUtc="2026-07-27T13:00:00Z"), "approval-expired"),
        (lambda value: value["approvalReceipt"].update(scopeDigest="ABC"), "invalid-approval-scope-digest"),
        (lambda value: value.update(rawPath="C:\\repo"), "invalid-request-shape"),
        (lambda value: value.update(arguments=["--hostile"]), "invalid-request-shape"),
    ]
    for mutator, code in cases:
        deny(mutator, code)

    retry = copy.deepcopy(fixture)
    retry["attempt"] = 1
    retry["lifecycle"] = {
        "mode": "retry",
        "retryOf": "prior-admission",
        "recoveryOf": None,
        "cancelRequested": False,
        "priorAttemptCompleted": True,
        "priorSideEffectsPossible": False,
    }
    retry["approvalReceipt"]["scopeDigest"] = MODULE.scope_digest(retry)
    assert evaluate(retry)["State"] == "preconditions-modeled"
    passed += 1

    recovery = copy.deepcopy(fixture)
    recovery["attempt"] = 1
    recovery["lifecycle"] = {
        "mode": "recover",
        "retryOf": None,
        "recoveryOf": "prior-admission",
        "cancelRequested": False,
        "priorAttemptCompleted": False,
        "priorSideEffectsPossible": True,
    }
    recovery["approvalReceipt"] = {
        "present": False,
        "receiptId": None,
        "scopeDigest": None,
        "effectIds": [],
        "issuer": None,
        "audience": None,
        "issuedAtUtc": None,
        "expiresAtUtc": None,
        "evaluationTimeUtc": None,
        "used": False,
        "revoked": False,
    }
    assert evaluate(recovery)["State"] == "recovery-blocked"
    passed += 1

    cancelled = copy.deepcopy(fixture)
    cancelled["lifecycle"] = {
        "mode": "cancel",
        "retryOf": None,
        "recoveryOf": None,
        "cancelRequested": True,
        "priorAttemptCompleted": False,
        "priorSideEffectsPossible": False,
    }
    cancelled["approvalReceipt"] = copy.deepcopy(recovery["approvalReceipt"])
    assert evaluate(cancelled)["State"] == "cancelled"
    passed += 1
    cancelled_with_approval = copy.deepcopy(cancelled)
    cancelled_with_approval["approvalReceipt"] = copy.deepcopy(fixture["approvalReceipt"])
    rejected(cancelled_with_approval, "approval-not-allowed-for-nonexecution")
    passed += 1
    cancelled_with_extra = copy.deepcopy(cancelled)
    cancelled_with_extra["approvalReceipt"]["rawToken"] = "renderer-secret"
    rejected(cancelled_with_extra, "invalid-approval-receipt-shape")
    passed += 1

    invalid_retry = copy.deepcopy(retry)
    invalid_retry["lifecycle"]["priorSideEffectsPossible"] = True
    rejected(invalid_retry, "invalid-retry-lifecycle")
    passed += 1
    invalid_fresh = copy.deepcopy(fixture)
    invalid_fresh["lifecycle"]["priorAttemptCompleted"] = True
    rejected(invalid_fresh, "invalid-fresh-lifecycle")
    passed += 1
    mismatched_scope = copy.deepcopy(fixture)
    mismatched_scope["approvalReceipt"]["scopeDigest"] = "f" * 64
    rejected(mismatched_scope, "approval-scope-mismatch")
    passed += 1

    print(f"Task execution admission self-test passed: {passed} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
