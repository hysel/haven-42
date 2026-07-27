#!/usr/bin/env python3
"""Hostile tests for the effect-free task effect-journal model."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "task_effect_journal",
    ROOT / "scripts" / "simulate-task-effect-journal.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT = json.loads((ROOT / "config/task-effect-journal-contract.json").read_text(encoding="utf-8"))
FIXTURE_PATH = ROOT / "examples" / "fixtures" / "task-effect-journal-request.json"


def seal(value):
    previous = None
    for record in value["records"]:
        record["previousRecordSha256"] = previous
        record["recordSha256"] = MODULE.record_digest(value["admissionBinding"], record)
        previous = record["recordSha256"]
    return value


def record(sequence, event, effect_id, outcome):
    return {
        "sequence": sequence,
        "recordId": f"record-{sequence:016d}",
        "event": event,
        "effectId": effect_id,
        "outcome": outcome,
        "recordedAtUtc": f"2026-07-27T12:00:{sequence:02d}Z",
        "previousRecordSha256": None,
        "recordSha256": "0" * 64,
    }


def rejected(value, code):
    try:
        MODULE.evaluate(value, CONTRACT)
    except MODULE.EffectJournalError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"effect journal unexpectedly accepted: {code}")


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    admission = json.loads(
        (ROOT / "examples" / "fixtures" / "task-execution-admission-request.json").read_text(
            encoding="utf-8"
        )
    )
    for field in ("admissionId", "compositionId", "stepId", "workflowId", "attempt", "requestedEffects"):
        assert fixture["admissionBinding"][field] == admission[field]
    assert fixture["admissionBinding"]["scopeDigest"] == admission["approvalReceipt"]["scopeDigest"]
    assert fixture["admissionBinding"]["approvalReceiptId"] == admission["approvalReceipt"]["receiptId"]
    seal(fixture)
    result = MODULE.evaluate(copy.deepcopy(fixture), CONTRACT)
    assert result["State"] == "journal-modeled"
    assert result["ScenarioClaimsAuthoritative"] is False
    assert result["JournalPersisted"] is False
    assert result["EffectCompletionProven"] is False
    assert result["RetryAuthorized"] is False
    assert result["RecoveryAuthorized"] is False
    assert result["ExecutionAllowed"] is False
    effect_fields = [
        key for key in result
        if key.endswith(("Created", "Accessed", "Used", "Modified", "Consumed", "Written", "Read"))
    ]
    assert effect_fields and all(result[key] is False for key in effect_fields)
    passed = 1

    def deny(mutator, code, reseal=True):
        nonlocal passed
        value = copy.deepcopy(fixture)
        mutator(value)
        if reseal:
            seal(value)
        rejected(value, code)
        passed += 1

    cases = [
        (lambda value: value.update(extra=True), "invalid-request-shape"),
        (lambda value: value.update(schemaVersion=2), "unsupported-schema"),
        (lambda value: value.update(evaluationTimeUtc="not-a-time"), "invalid-evaluation-timestamp"),
        (lambda value: value.update(evaluationId="short"), "invalid-evaluation-id"),
        (lambda value: value["admissionBinding"].update(extra=True), "invalid-admission-binding-shape"),
        (lambda value: value["admissionBinding"].update(admissionId="../bad"), "invalid-admission-id"),
        (lambda value: value["admissionBinding"].update(scopeDigest="ABC"), "invalid-scope-digest"),
        (lambda value: value["admissionBinding"].update(approvalReceiptId="short"), "invalid-approval-receipt-id"),
        (lambda value: value["admissionBinding"].update(attempt=True), "invalid-attempt"),
        (lambda value: value["admissionBinding"].update(requestedEffects=["process-create", "filesystem-write"]), "invalid-requested-effects"),
        (lambda value: value["admissionBinding"].update(requestedEffects=["process-create", "process-create"]), "invalid-requested-effects"),
        (lambda value: value["admissionBinding"].update(requestedEffects=["machine-modification"]), "prohibited-effect-bound"),
        (lambda value: value["admissionBinding"].update(requestedEffects=["unknown"]), "unknown-effect-bound"),
        (lambda value: value["lifecycle"].update(extra=True), "invalid-lifecycle-shape"),
        (lambda value: value["lifecycle"].update(mode="resume"), "invalid-lifecycle-mode"),
        (lambda value: value["lifecycle"].update(cancelRequested="false"), "invalid-lifecycle-boolean"),
        (lambda value: value["lifecycle"].update(priorEvaluationId="short"), "invalid-prior-evaluation-id"),
        (lambda value: value["records"].clear(), "invalid-record-count"),
        (lambda value: value["records"][0].update(extra=True), "invalid-record-shape"),
        (lambda value: value["records"][0].update(sequence=2), "record-sequence-gap-or-reorder"),
        (lambda value: value["records"][0].update(recordId="short"), "invalid-or-duplicate-record-id"),
        (lambda value: value["records"][0].update(event="forged-completion"), "unknown-record-event"),
        (lambda value: value["records"][0].update(outcome="trusted"), "record-outcome-mismatch"),
        (lambda value: value["records"][0].update(effectId="process-create"), "unexpected-record-effect"),
        (lambda value: value["records"][0].update(recordedAtUtc="not-a-time"), "invalid-record-timestamp"),
        (lambda value: value["records"][0].update(rawPath="C:\\repo"), "invalid-record-shape"),
        (lambda value: value.update(rawArguments=["--unsafe"]), "invalid-request-shape"),
    ]
    for mutator, code in cases:
        deny(mutator, code)

    digest_mismatch = copy.deepcopy(fixture)
    digest_mismatch["records"][0]["outcome"] = "changed"
    rejected(digest_mismatch, "record-outcome-mismatch")
    passed += 1
    chain_mismatch = copy.deepcopy(fixture)
    chain_mismatch["records"][0]["previousRecordSha256"] = "f" * 64
    rejected(chain_mismatch, "record-chain-mismatch")
    passed += 1
    cross_session_reuse = copy.deepcopy(fixture)
    cross_session_reuse["admissionBinding"]["admissionId"] = "admission-other0000001"
    rejected(cross_session_reuse, "record-digest-mismatch")
    passed += 1

    cancelled = copy.deepcopy(fixture)
    cancelled["lifecycle"] = {
        "mode": "cancel",
        "priorEvaluationId": None,
        "cancelRequested": True,
        "priorEffectsPossible": False,
    }
    cancelled["records"].append(record(2, "cancellation-requested", None, "cancellation-claimed"))
    seal(cancelled)
    assert MODULE.evaluate(cancelled, CONTRACT)["State"] == "cancelled-before-start"
    passed += 1

    during = copy.deepcopy(cancelled)
    during["records"] = [
        copy.deepcopy(fixture["records"][0]),
        record(2, "execution-started", None, "intent-observed"),
        record(3, "cancellation-requested", None, "cancellation-claimed"),
    ]
    during["lifecycle"]["priorEffectsPossible"] = True
    seal(during)
    assert MODULE.evaluate(during, CONTRACT)["State"] == "cancellation-review-blocked"
    passed += 1
    understated_cancel = copy.deepcopy(during)
    understated_cancel["lifecycle"]["priorEffectsPossible"] = False
    seal(understated_cancel)
    rejected(understated_cancel, "cancellation-effect-state-mismatch")
    passed += 1

    missing_cancel = copy.deepcopy(cancelled)
    missing_cancel["records"] = [copy.deepcopy(fixture["records"][0])]
    seal(missing_cancel)
    rejected(missing_cancel, "cancel-journal-missing-cancellation")
    passed += 1

    retry = copy.deepcopy(fixture)
    retry["lifecycle"] = {
        "mode": "retry",
        "priorEvaluationId": "evaluation-prior0000001",
        "cancelRequested": False,
        "priorEffectsPossible": False,
    }
    seal(retry)
    assert MODULE.evaluate(retry, CONTRACT)["State"] == "retry-modeled"
    passed += 1
    unsafe_retry = copy.deepcopy(retry)
    unsafe_retry["lifecycle"]["priorEffectsPossible"] = True
    seal(unsafe_retry)
    rejected(unsafe_retry, "unsafe-retry-lifecycle")
    passed += 1

    recover_clean = copy.deepcopy(fixture)
    recover_clean["lifecycle"] = {
        "mode": "recover",
        "priorEvaluationId": "evaluation-prior0000001",
        "cancelRequested": False,
        "priorEffectsPossible": False,
    }
    seal(recover_clean)
    assert MODULE.evaluate(recover_clean, CONTRACT)["State"] == "recovery-modeled"
    passed += 1

    recover_started = copy.deepcopy(recover_clean)
    recover_started["lifecycle"]["priorEffectsPossible"] = True
    recover_started["records"].append(record(2, "execution-started", None, "intent-observed"))
    seal(recover_started)
    assert MODULE.evaluate(recover_started, CONTRACT)["State"] == "recovery-blocked"
    passed += 1

    recover_mismatch = copy.deepcopy(recover_started)
    recover_mismatch["lifecycle"]["priorEffectsPossible"] = False
    seal(recover_mismatch)
    rejected(recover_mismatch, "recovery-effect-state-mismatch")
    passed += 1

    forged_completion = copy.deepcopy(recover_started)
    forged_completion["records"].append(record(3, "execution-completed", None, "completion-claimed"))
    seal(forged_completion)
    rejected(forged_completion, "completion-missing-effect-records")
    passed += 1

    completed = copy.deepcopy(recover_started)
    completed["records"].extend([
        record(3, "effect-started", "filesystem-write", "intent-observed"),
        record(4, "effect-completed", "filesystem-write", "completion-claimed"),
        record(5, "effect-started", "process-create", "intent-observed"),
        record(6, "effect-completed", "process-create", "completion-claimed"),
        record(7, "execution-completed", None, "completion-claimed"),
    ])
    seal(completed)
    completed_result = MODULE.evaluate(completed, CONTRACT)
    assert completed_result["State"] == "effect-claims-untrusted"
    assert completed_result["EffectCompletionProven"] is False
    passed += 1

    reordered = copy.deepcopy(completed)
    reordered["records"][2], reordered["records"][3] = reordered["records"][3], reordered["records"][2]
    for index, item in enumerate(reordered["records"], start=1):
        item["sequence"] = index
        item["recordId"] = f"record-{index:016d}"
        item["recordedAtUtc"] = f"2026-07-27T12:00:{index:02d}Z"
    seal(reordered)
    rejected(reordered, "invalid-effect-completion-order")
    passed += 1

    duplicate_start = copy.deepcopy(recover_started)
    duplicate_start["records"].append(record(3, "execution-started", None, "intent-observed"))
    seal(duplicate_start)
    rejected(duplicate_start, "invalid-execution-start-order")
    passed += 1

    after_terminal = copy.deepcopy(completed)
    after_terminal["records"].append(record(8, "cancellation-requested", None, "cancellation-claimed"))
    seal(after_terminal)
    rejected(after_terminal, "record-after-terminal")
    passed += 1

    future_record = copy.deepcopy(fixture)
    future_record["records"][0]["recordedAtUtc"] = "2026-07-27T12:02:00Z"
    seal(future_record)
    rejected(future_record, "record-after-evaluation")
    passed += 1

    print(f"Task effect journal self-test passed: {passed} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
