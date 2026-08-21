#!/usr/bin/env python3
"""Validate sanitized Apple M4 llama.cpp/OpenCode coding evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    pass


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError("expected-object")
    return value


def validate(result: dict[str, Any], plan: dict[str, Any], qualification: dict[str, Any], policy: dict[str, Any]) -> None:
    if result.get("schemaVersion") != 1 or result.get("kind") != "haven42-apple-silicon-llamacpp-coding-agent-qualification-result":
        raise ValidationError("invalid-result-kind")
    bindings = (("planCanonicalSha256", plan), ("qualificationCanonicalSha256", qualification), ("policyCanonicalSha256", policy))
    if any(result.get(key) != digest(value) for key, value in bindings) or result.get("runtime") != plan.get("runtime"):
        raise ValidationError("stale-evidence-binding")
    if any(result.get(key) is not False for key in ("rawPromptsOrResponsesRetained", "privateIdentityRetained", "automaticDefaultChangeAllowed", "automaticSelectionEvidenceAllowed", "automaticSupportChangeAllowed")):
        raise ValidationError("unsafe-result-authority")
    candidates, records = plan.get("candidates"), result.get("results")
    if not isinstance(candidates, list) or not isinstance(records, list) or len(candidates) != len(records):
        raise ValidationError("result-coverage-mismatch")
    required = {gate["id"]: set(gate["checks"]) for gate in policy.get("requiredGates", [])}
    for candidate, record in zip(candidates, records):
        if record.get("modelId") != candidate.get("modelId") or record.get("modelSha256") != candidate.get("modelSha256") or record.get("rawResponseRetained") is not False:
            raise ValidationError("candidate-binding-mismatch")
        gates = record.get("gates")
        if not isinstance(gates, dict) or set(gates) != set(required):
            raise ValidationError("gate-coverage-mismatch")
        all_passed = True
        for gate_id, check_ids in required.items():
            gate = gates[gate_id]
            checks = gate.get("checks") if isinstance(gate, dict) else None
            if not isinstance(checks, dict) or set(checks) != check_ids or any(value not in {"passed", "failed", "blocked", "not-run"} for value in checks.values()):
                raise ValidationError("invalid-gate")
            passed = all(value == "passed" for value in checks.values())
            if gate.get("status") != ("passed" if passed else "failed"):
                raise ValidationError("gate-status-mismatch")
            all_passed = all_passed and passed
        if record.get("status") != ("passed" if all_passed else "failed"):
            raise ValidationError("record-status-mismatch")
        if record.get("codingRecommendationEligible") is not False:
            raise ValidationError("coding-recommendation-overclaim")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("qualification", type=Path)
    parser.add_argument("policy", type=Path)
    args = parser.parse_args()
    try:
        validate(load(args.result), load(args.plan), load(args.qualification), load(args.policy))
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        parser.error(str(error))
    print("Apple M4 llama.cpp/OpenCode coding evidence validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
