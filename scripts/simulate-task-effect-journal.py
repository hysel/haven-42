#!/usr/bin/env python3
"""Model a future execution effect journal without executing or persisting anything."""

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
CONTRACT_PATH = ROOT / "config" / "task-effect-journal-contract.json"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,95}$")
LONG_ID = re.compile(r"^[a-z][a-z0-9-]{15,95}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EffectJournalError(ValueError):
    pass


def _strict(value: object, required: list[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(required):
        raise EffectJournalError(f"invalid-{label}-shape")
    return value


def _timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise EffectJournalError(f"invalid-{label}-timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise EffectJournalError(f"invalid-{label}-timestamp") from error
    if parsed.tzinfo != timezone.utc:
        raise EffectJournalError(f"invalid-{label}-timestamp")
    return parsed


def record_digest(binding: dict[str, Any], record: dict[str, Any]) -> str:
    payload = {
        "admissionBinding": binding,
        "record": {
            key: value
            for key, value in record.items()
            if key != "recordSha256"
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_binding(request: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    binding = _strict(
        request["admissionBinding"],
        contract["admissionBinding"]["required"],
        "admission-binding",
    )
    for field in ("admissionId", "compositionId", "stepId", "workflowId"):
        if not isinstance(binding[field], str) or not IDENTIFIER.fullmatch(binding[field]):
            raise EffectJournalError(f"invalid-{field.replace('Id', '-id').lower()}")
    if (
        isinstance(binding["attempt"], bool)
        or not isinstance(binding["attempt"], int)
        or binding["attempt"] < 0
        or binding["attempt"] > 2
    ):
        raise EffectJournalError("invalid-attempt")
    if not isinstance(binding["scopeDigest"], str) or not SHA256.fullmatch(binding["scopeDigest"]):
        raise EffectJournalError("invalid-scope-digest")
    if (
        not isinstance(binding["approvalReceiptId"], str)
        or not LONG_ID.fullmatch(binding["approvalReceiptId"])
    ):
        raise EffectJournalError("invalid-approval-receipt-id")
    effects = binding["requestedEffects"]
    allowed = set(contract["admissionBinding"]["allowedEffects"])
    prohibited = set(contract["admissionBinding"]["alwaysProhibited"])
    if (
        not isinstance(effects, list)
        or effects != sorted(effects)
        or len(effects) != len(set(effects))
        or not all(isinstance(value, str) for value in effects)
    ):
        raise EffectJournalError("invalid-requested-effects")
    if any(value in prohibited for value in effects):
        raise EffectJournalError("prohibited-effect-bound")
    if not effects or any(value not in allowed for value in effects):
        raise EffectJournalError("unknown-effect-bound")
    return binding


def _validate_lifecycle(request: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    lifecycle = _strict(
        request["lifecycle"],
        contract["lifecycle"]["required"],
        "lifecycle",
    )
    if lifecycle["mode"] not in contract["lifecycle"]["modes"]:
        raise EffectJournalError("invalid-lifecycle-mode")
    if type(lifecycle["cancelRequested"]) is not bool or type(lifecycle["priorEffectsPossible"]) is not bool:
        raise EffectJournalError("invalid-lifecycle-boolean")
    prior = lifecycle["priorEvaluationId"]
    if prior is not None and (not isinstance(prior, str) or not LONG_ID.fullmatch(prior)):
        raise EffectJournalError("invalid-prior-evaluation-id")
    mode = lifecycle["mode"]
    if mode == "fresh" and (
        prior is not None
        or lifecycle["cancelRequested"]
        or lifecycle["priorEffectsPossible"]
    ):
        raise EffectJournalError("invalid-fresh-lifecycle")
    if mode == "cancel" and (not lifecycle["cancelRequested"] or prior is not None):
        raise EffectJournalError("invalid-cancel-lifecycle")
    if mode in {"retry", "recover"} and prior is None:
        raise EffectJournalError(f"invalid-{mode}-lifecycle")
    if mode == "retry" and (
        lifecycle["cancelRequested"]
        or lifecycle["priorEffectsPossible"]
    ):
        raise EffectJournalError("unsafe-retry-lifecycle")
    if mode == "recover" and lifecycle["cancelRequested"]:
        raise EffectJournalError("invalid-recover-lifecycle")
    return lifecycle


def _validate_records(
    request: dict[str, Any],
    contract: dict[str, Any],
    binding: dict[str, Any],
    evaluation_time: datetime,
) -> tuple[list[dict[str, Any]], set[str], bool, bool, bool]:
    records = request["records"]
    if (
        not isinstance(records, list)
        or not records
        or len(records) > contract["request"]["maximumRecords"]
    ):
        raise EffectJournalError("invalid-record-count")
    required = contract["record"]["required"]
    allowed_events = set(contract["record"]["events"])
    expected_outcomes = {
        "admission-bound": "structurally-admitted",
        "execution-started": "intent-observed",
        "effect-started": "intent-observed",
        "effect-completed": "completion-claimed",
        "cancellation-requested": "cancellation-claimed",
        "execution-failed": "failure-claimed",
        "execution-completed": "completion-claimed",
    }
    seen_ids: set[str] = set()
    started_effects: set[str] = set()
    completed_effects: set[str] = set()
    previous_digest: str | None = None
    previous_time: datetime | None = None
    execution_started = False
    cancelled = False
    terminal = False
    validated: list[dict[str, Any]] = []
    for index, value in enumerate(records, start=1):
        record = _strict(value, required, "record")
        if record["sequence"] != index:
            raise EffectJournalError("record-sequence-gap-or-reorder")
        record_id = record["recordId"]
        if not isinstance(record_id, str) or not LONG_ID.fullmatch(record_id) or record_id in seen_ids:
            raise EffectJournalError("invalid-or-duplicate-record-id")
        seen_ids.add(record_id)
        event = record["event"]
        if event not in allowed_events:
            raise EffectJournalError("unknown-record-event")
        if record["outcome"] != expected_outcomes[event]:
            raise EffectJournalError("record-outcome-mismatch")
        recorded_at = _timestamp(record["recordedAtUtc"], "record")
        if recorded_at > evaluation_time:
            raise EffectJournalError("record-after-evaluation")
        if previous_time is not None and recorded_at < previous_time:
            raise EffectJournalError("record-time-reordered")
        previous_time = recorded_at
        if record["previousRecordSha256"] != previous_digest:
            raise EffectJournalError("record-chain-mismatch")
        if not isinstance(record["recordSha256"], str) or not SHA256.fullmatch(record["recordSha256"]):
            raise EffectJournalError("invalid-record-digest")
        expected_digest = record_digest(binding, record)
        if record["recordSha256"] != expected_digest:
            raise EffectJournalError("record-digest-mismatch")
        previous_digest = expected_digest
        effect_id = record["effectId"]
        if event in {"effect-started", "effect-completed"}:
            if effect_id not in binding["requestedEffects"]:
                raise EffectJournalError("record-effect-scope-mismatch")
        elif effect_id is not None:
            raise EffectJournalError("unexpected-record-effect")
        if terminal:
            raise EffectJournalError("record-after-terminal")
        if index == 1 and event != "admission-bound":
            raise EffectJournalError("journal-missing-admission-binding")
        if index > 1 and event == "admission-bound":
            raise EffectJournalError("duplicate-admission-binding")
        if event == "execution-started":
            if execution_started or cancelled:
                raise EffectJournalError("invalid-execution-start-order")
            execution_started = True
        elif event == "effect-started":
            if not execution_started or cancelled or effect_id in started_effects:
                raise EffectJournalError("invalid-effect-start-order")
            started_effects.add(effect_id)
        elif event == "effect-completed":
            if effect_id not in started_effects or effect_id in completed_effects:
                raise EffectJournalError("invalid-effect-completion-order")
            completed_effects.add(effect_id)
        elif event == "cancellation-requested":
            if cancelled:
                raise EffectJournalError("duplicate-cancellation")
            cancelled = True
        elif event == "execution-failed":
            if not execution_started:
                raise EffectJournalError("failure-before-execution-start")
            terminal = True
        elif event == "execution-completed":
            if not execution_started:
                raise EffectJournalError("completion-before-execution-start")
            if completed_effects != set(binding["requestedEffects"]):
                raise EffectJournalError("completion-missing-effect-records")
            terminal = True
        validated.append(record)
    return validated, started_effects, execution_started, cancelled, terminal


def evaluate(request: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if (
        contract.get("runtimeAdmitted") is not False
        or contract.get("implementationStatus") != "simulation-only"
        or contract["record"].get("scenarioClaimsAreAuthoritativeEvidence") is not False
        or any(contract["request"].get(field) is not False for field in (
            "rawArgumentsAllowed",
            "rawContentAllowed",
            "rawPathAllowed",
            "rawUrlAllowed",
            "environmentAllowed",
        ))
    ):
        raise EffectJournalError("unsafe-effect-journal-contract")
    _strict(request, contract["request"]["required"], "request")
    if request["schemaVersion"] != contract["schemaVersion"]:
        raise EffectJournalError("unsupported-schema")
    if not isinstance(request["evaluationId"], str) or not LONG_ID.fullmatch(request["evaluationId"]):
        raise EffectJournalError("invalid-evaluation-id")
    evaluation_time = _timestamp(request["evaluationTimeUtc"], "evaluation")
    binding = _validate_binding(request, contract)
    lifecycle = _validate_lifecycle(request, contract)
    records, started_effects, execution_started, cancelled, terminal = _validate_records(
        request,
        contract,
        binding,
        evaluation_time,
    )
    mode = lifecycle["mode"]
    if mode == "fresh" and len(records) != 1:
        raise EffectJournalError("fresh-journal-contains-runtime-claims")
    if mode == "cancel":
        if not cancelled:
            raise EffectJournalError("cancel-journal-missing-cancellation")
        if lifecycle["priorEffectsPossible"] != execution_started:
            raise EffectJournalError("cancellation-effect-state-mismatch")
        state = "cancellation-review-blocked" if execution_started else "cancelled-before-start"
    elif mode == "retry":
        if len(records) != 1:
            raise EffectJournalError("retry-journal-contains-runtime-claims")
        state = "retry-modeled"
    elif mode == "recover":
        claims_possible = bool(started_effects or execution_started or terminal)
        if lifecycle["priorEffectsPossible"] != claims_possible:
            raise EffectJournalError("recovery-effect-state-mismatch")
        state = "recovery-blocked" if claims_possible else "recovery-modeled"
    else:
        state = "journal-modeled"
    if terminal:
        state = "effect-claims-untrusted"

    effects = {
        key[0].upper() + key[1:]: value
        for key, value in contract["effects"].items()
    }
    return {
        "SchemaVersion": 1,
        "Kind": "task-effect-journal-simulation",
        "State": state,
        "EvaluationId": request["evaluationId"],
        "AdmissionId": binding["admissionId"],
        "ScopeDigest": binding["scopeDigest"],
        "ApprovalReceiptId": binding["approvalReceiptId"],
        "LastRecordSha256": records[-1]["recordSha256"],
        "ScenarioRecordsValidated": len(records),
        "ScenarioClaimsAuthoritative": False,
        "JournalPersisted": False,
        "EffectCompletionProven": False,
        "RetryAuthorized": False,
        "RecoveryAuthorized": False,
        "ExecutionAllowed": False,
        "NextGate": "native durable journal, executor binding, rollback evidence, and cross-platform runtime tests",
        **effects,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Model a future effect journal without execution or persistence."
    )
    parser.add_argument("--request", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        result = evaluate(request)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, EffectJournalError) as error:
        print(f"Task effect journal rejected input: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Task effect journal modeled; no journal was written and no effect was proven.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
