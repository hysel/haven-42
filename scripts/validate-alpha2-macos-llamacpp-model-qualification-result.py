#!/usr/bin/env python3
"""Validate sanitized Apple M4 llama.cpp model qualification evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    pass


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError("expected-object")
    return value


def validate(result: dict[str, Any], plan: dict[str, Any]) -> None:
    if result.get("kind") != "haven42-apple-silicon-llamacpp-model-qualification-result" or result.get("schemaVersion") != 1:
        raise ValidationError("invalid-result-kind")
    if result.get("planCanonicalSha256") != canonical_sha256(plan) or result.get("runtime") != plan.get("runtime"):
        raise ValidationError("stale-plan-or-runtime-binding")
    if any(result.get(key) is not False for key in (
        "rawPromptsOrResponsesRetained", "privateIdentityRetained", "automaticDefaultChangeAllowed",
        "automaticSelectionEvidenceAllowed", "automaticSupportChangeAllowed",
    )):
        raise ValidationError("unsafe-result-authority")
    candidates = plan.get("candidates")
    records = result.get("results")
    if not isinstance(candidates, list) or not isinstance(records, list) or len(records) != len(candidates):
        raise ValidationError("result-coverage-mismatch")
    expected_checks = set(plan.get("testContract", {})) - {"version"}
    for candidate, record in zip(candidates, records):
        if not isinstance(record, dict) or record.get("modelId") != candidate.get("modelId"):
            raise ValidationError("result-order-mismatch")
        if record.get("modelSha256") != candidate.get("modelSha256") or record.get("repositoryRevision") != candidate.get("repositoryRevision"):
            raise ValidationError("artifact-binding-mismatch")
        checks, metrics = record.get("checks"), record.get("metrics")
        if not isinstance(checks, dict) or not isinstance(metrics, dict) or set(checks) != expected_checks or set(metrics) != expected_checks:
            raise ValidationError("check-coverage-mismatch")
        passed = True
        for name in expected_checks:
            check, measurement = checks[name], metrics[name]
            if not isinstance(check, dict) or check.get("status") not in {"passed", "failed"} or check.get("responseRetained") is not False or not isinstance(measurement, dict):
                raise ValidationError("invalid-check")
            if check["status"] == "passed" and any(measurement.get(key) is not True for key in ("metalDetected", "allLayersOffloaded", "authenticationRequired", "unloadPassed")):
                raise ValidationError("passing-check-lacks-runtime-proof")
            if name == "structuredCode":
                if measurement.get("modelGeneratedCodeExecuted") is not False or measurement.get("validationMethod") != "ast-only":
                    raise ValidationError("unsafe-or-ambiguous-model-code-handling")
                planned = str(plan.get("testContract", {}).get(name, "")).lower()
                if "execute" in planned and check.get("status") != "failed":
                    raise ValidationError("planned-code-execution-not-performed")
                if "execute" in planned and check.get("errorCode") != "planned-execution-not-performed-safety-boundary":
                    raise ValidationError("missing-code-execution-deviation")
            passed = passed and check["status"] == "passed"
        if record.get("corePassed") is not passed or record.get("status") != ("passed" if passed else "failed"):
            raise ValidationError("aggregate-status-mismatch")
        if record.get("codingSurfaceStatus") != "not-run" or record.get("codingRecommendationEligible") is not False:
            raise ValidationError("coding-evidence-overclaim")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        validate(load(args.result), load(args.plan))
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        parser.error(str(error))
    print("Apple M4 llama.cpp model qualification evidence validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
