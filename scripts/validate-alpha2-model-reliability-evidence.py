#!/usr/bin/env python3
"""Validate sanitized results produced from an approved reliability plan."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any


MAX_INPUT_BYTES = 8 * 1024 * 1024
SAFE_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,79}")


class ReliabilityEvidenceError(ValueError):
    """Reliability evidence was incomplete, inconsistent, or unsafe."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_INPUT_BYTES:
            raise ReliabilityEvidenceError("unsafe-reliability-evidence")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReliabilityEvidenceError("invalid-reliability-evidence") from error
    if not isinstance(value, dict):
        raise ReliabilityEvidenceError("invalid-reliability-evidence")
    return value


def canonical_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ReliabilityEvidenceError("invalid-evidence-timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReliabilityEvidenceError("invalid-evidence-timestamp") from error
    if parsed.tzinfo is None:
        raise ReliabilityEvidenceError("invalid-evidence-timestamp")
    return parsed


def approval_reference(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value or len(value) > 300:
        raise ReliabilityEvidenceError("invalid-execution-approval-reference")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ReliabilityEvidenceError("invalid-execution-approval-reference")
    return value


def number(value: Any, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not 0 <= float(value) <= maximum:
        raise ReliabilityEvidenceError("invalid-reliability-metric")
    return float(value)


def validate_metrics(value: Any, attempts: int, passed: bool) -> dict[str, Any]:
    required = {
        "checksPassed", "checksFailed", "firstTokenLatencyMs", "tokensPerSecond",
        "peakSystemMemoryMiB", "peakAcceleratorMemoryMiB", "acceleratorUseObserved",
        "modelUnloadPasses", "listenerCleanupPasses", "processCleanupPasses",
        "boundedErrorCodes",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ReliabilityEvidenceError("invalid-reliability-metrics")
    integer_fields = ("checksPassed", "checksFailed", "modelUnloadPasses", "listenerCleanupPasses", "processCleanupPasses")
    for name in integer_fields:
        item = value[name]
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise ReliabilityEvidenceError("invalid-reliability-metrics")
    for name in ("firstTokenLatencyMs", "tokensPerSecond"):
        items = value[name]
        if not isinstance(items, list) or any(number(item, 1_000_000) <= 0 for item in items):
            raise ReliabilityEvidenceError("invalid-reliability-metrics")
    number(value["peakSystemMemoryMiB"], 4_000_000)
    number(value["peakAcceleratorMemoryMiB"], 1_000_000)
    if value["acceleratorUseObserved"] is not True and value["acceleratorUseObserved"] is not False and value["acceleratorUseObserved"] is not None:
        raise ReliabilityEvidenceError("invalid-reliability-metrics")
    codes = value["boundedErrorCodes"]
    if not isinstance(codes, list) or len(codes) != len(set(codes)) or any(not isinstance(code, str) or not SAFE_CODE.fullmatch(code) for code in codes):
        raise ReliabilityEvidenceError("invalid-reliability-metrics")
    if passed and (
        value["checksPassed"] < attempts
        or value["checksFailed"] != 0
        or value["acceleratorUseObserved"] is not True
        or value["modelUnloadPasses"] < attempts
        or value["listenerCleanupPasses"] < attempts
        or value["processCleanupPasses"] < attempts
        or not value["firstTokenLatencyMs"]
        or not value["tokensPerSecond"]
    ):
        raise ReliabilityEvidenceError("passing-reliability-evidence-incomplete")
    return value


def validate(plan: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    if plan.get("schemaVersion") != 1 or plan.get("kind") != "haven42-alpha2-model-reliability-plan":
        raise ReliabilityEvidenceError("invalid-reliability-plan")
    required = {
        "schemaVersion", "kind", "planBinding", "campaignId", "identity", "environment",
        "executionApprovalReference", "startedAtUtc", "completedAtUtc", "scenarios", "evidence",
    }
    if set(evidence) != required or evidence.get("schemaVersion") != 1 or evidence.get("kind") != "haven42-alpha2-model-reliability-evidence":
        raise ReliabilityEvidenceError("invalid-reliability-evidence")
    if evidence["planBinding"] != {"canonicalSha256": canonical_sha256(plan)}:
        raise ReliabilityEvidenceError("reliability-plan-binding-mismatch")
    if evidence["campaignId"] != plan.get("campaignId") or evidence["identity"] != plan.get("identity") or evidence["environment"] != plan.get("environment"):
        raise ReliabilityEvidenceError("reliability-identity-mismatch")
    approval_reference(evidence["executionApprovalReference"])
    started, completed = timestamp(evidence["startedAtUtc"]), timestamp(evidence["completedAtUtc"])
    if completed <= started:
        raise ReliabilityEvidenceError("invalid-evidence-timestamp")
    disclosure = evidence["evidence"]
    expected_disclosure = {
        "containsRawPromptsOrResponses": False, "containsPrivateMachineIdentity": False,
        "containsProviderEndpoint": False, "automaticPromotionAllowed": False,
        "automaticDefaultChangeAllowed": False,
    }
    if disclosure != expected_disclosure:
        raise ReliabilityEvidenceError("unsafe-reliability-disclosure")
    actions = plan.get("actions")
    results = evidence["scenarios"]
    if not isinstance(actions, list) or not isinstance(results, list) or len(actions) != len(results):
        raise ReliabilityEvidenceError("incomplete-reliability-scenarios")
    by_id = {item.get("scenarioId"): item for item in results if isinstance(item, dict)}
    if len(by_id) != len(results):
        raise ReliabilityEvidenceError("incomplete-reliability-scenarios")
    counts = {"passed": 0, "failed": 0, "not-supported": 0}
    normalized = []
    for action in actions:
        scenario_id = action.get("scenarioId")
        item = by_id.get(scenario_id)
        if not isinstance(item, dict) or set(item) != {"scenarioId", "outcome", "attempts", "metrics"}:
            raise ReliabilityEvidenceError("incomplete-reliability-scenarios")
        outcome, attempts = item["outcome"], item["attempts"]
        if outcome not in counts or not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 0:
            raise ReliabilityEvidenceError("invalid-reliability-scenario")
        if action.get("status") == "not-supported":
            if outcome != "not-supported" or attempts != 0 or item["metrics"] is not None:
                raise ReliabilityEvidenceError("unsupported-scenario-was-executed")
        else:
            if outcome == "not-supported" or attempts < action.get("minimumAttempts", 1):
                raise ReliabilityEvidenceError("insufficient-reliability-attempts")
            validate_metrics(item["metrics"], attempts, outcome == "passed")
        counts[outcome] += 1
        normalized.append(item)
    return {
        "schemaVersion": 1, "kind": "haven42-alpha2-model-reliability-validation",
        "campaignId": evidence["campaignId"], "outcome": "passed" if counts["failed"] == 0 else "failed-needs-retest",
        "scenarioCounts": counts, "scenarios": normalized,
        "automaticPromotionAllowed": False, "automaticDefaultChangeAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("output already exists or is unsafe")
    try:
        result = validate(load_json(args.plan), load_json(args.evidence))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ReliabilityEvidenceError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({"outcome": result["outcome"], "scenarioCounts": result["scenarioCounts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
