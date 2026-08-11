#!/usr/bin/env python3
"""Combine three sanitized model cells into one reviewable selector record.

This command is effect-free. It accepts exactly one passing Chat, Writing, and
Summarization result for the same exact runtime profile. It emits no record when
the inputs disagree or any repetition, residency, or unload proof is missing.
The output is a candidate for owner review; it does not update product policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


CAPABILITIES = ("general.chat", "content.write", "content.summarize")
RESULT_KEYS = {"durationSeconds", "errorCode", "evidence", "metrics", "outcome"}
EVIDENCE_KEYS = {
    "architecture", "automaticEvidenceCandidate", "backendMode", "capability",
    "capabilityPassed", "manifestDigest", "modelId", "operatingSystemId",
    "platformFamily", "provider", "providerVersion",
    "selectorPolicyCanonicalSha256", "storageAdmitted", "systemMemoryGiB",
    "usableGpuMemoryGiB",
}
METRIC_KEYS = {
    "outputTokens", "peakGpuMemoryBytes", "promptTokens", "samplesAttempted",
    "samplesFailed", "samplesPassed", "tokensPerSecond", "unloadPasses",
}
PROFILE_FIELDS = tuple(sorted(EVIDENCE_KEYS - {"capability", "capabilityPassed"}))
MAX_INPUT_BYTES = 64 * 1024


class EvidenceError(ValueError):
    """A model-cell group is incomplete, inconsistent, or unsafe."""


def _read_result(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
            raise EvidenceError("unsafe-result-file")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceError("invalid-result-file") from error
    if not isinstance(value, dict) or set(value) != RESULT_KEYS:
        raise EvidenceError("invalid-result-contract")
    return value


def _finite_number(value: Any, *, minimum: float = 0) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and value >= minimum
    )


def _validate_result(result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence = result.get("evidence")
    metrics = result.get("metrics")
    if (
        result.get("outcome") != "passed"
        or result.get("errorCode") is not None
        or not _finite_number(result.get("durationSeconds"), minimum=0.001)
        or not isinstance(evidence, dict)
        or set(evidence) != EVIDENCE_KEYS
        or not isinstance(metrics, dict)
        or set(metrics) != METRIC_KEYS
    ):
        raise EvidenceError("result-did-not-pass-contract")
    if (
        evidence["capability"] not in CAPABILITIES
        or evidence["capabilityPassed"] is not True
        or evidence["automaticEvidenceCandidate"] is not True
        or evidence["storageAdmitted"] is not True
        or evidence["provider"] != "ollama"
        or evidence["platformFamily"] != "linux"
        or evidence["backendMode"] not in {"cpu", "cuda"}
    ):
        raise EvidenceError("result-not-eligible-for-automatic-evidence")
    integer_metrics = (
        "outputTokens", "peakGpuMemoryBytes", "promptTokens", "samplesAttempted",
        "samplesFailed", "samplesPassed", "unloadPasses",
    )
    if any(isinstance(metrics[key], bool) or not isinstance(metrics[key], int) for key in integer_metrics):
        raise EvidenceError("invalid-result-metrics")
    if (
        metrics["samplesAttempted"] != 3
        or metrics["samplesPassed"] != 3
        or metrics["samplesFailed"] != 0
        or metrics["unloadPasses"] != 3
        or metrics["promptTokens"] <= 0
        or metrics["outputTokens"] <= 0
        or not _finite_number(metrics["tokensPerSecond"], minimum=0.001)
        or metrics["peakGpuMemoryBytes"] < 0
        or (evidence["backendMode"] == "cpu" and metrics["peakGpuMemoryBytes"] != 0)
        or (evidence["backendMode"] == "cuda" and metrics["peakGpuMemoryBytes"] <= 0)
        or (evidence["backendMode"] == "cpu" and evidence["usableGpuMemoryGiB"] != 0)
    ):
        raise EvidenceError("required-repetition-or-residency-proof-missing")
    return evidence, metrics


def build_group(results: list[dict[str, Any]]) -> dict[str, Any]:
    if len(results) != len(CAPABILITIES):
        raise EvidenceError("exactly-three-results-required")
    validated = [_validate_result(result) for result in results]
    evidence_records = [item[0] for item in validated]
    metrics = [item[1] for item in validated]
    by_capability = {item["capability"]: item for item in evidence_records}
    if set(by_capability) != set(CAPABILITIES) or len(by_capability) != len(evidence_records):
        raise EvidenceError("capability-set-incomplete-or-duplicated")
    first = evidence_records[0]
    profile = {field: first[field] for field in PROFILE_FIELDS}
    if any({field: item[field] for field in PROFILE_FIELDS} != profile for item in evidence_records[1:]):
        raise EvidenceError("exact-profile-mismatch")
    selector_record = {
        "evidenceId": "a2-" + hashlib.sha256(
            json.dumps(
                [profile[field] for field in PROFILE_FIELDS],
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:24],
        "modelId": profile["modelId"],
        "manifestDigest": profile["manifestDigest"],
        "platformFamily": profile["platformFamily"],
        "operatingSystemId": profile["operatingSystemId"],
        "architecture": profile["architecture"],
        "backendMode": profile["backendMode"],
        "provider": profile["provider"],
        "providerVersion": profile["providerVersion"],
        "selectorPolicyCanonicalSha256": profile["selectorPolicyCanonicalSha256"],
        "minimumTestedSystemMemoryGiB": profile["systemMemoryGiB"],
        "minimumTestedUsableGpuMemoryGiB": profile["usableGpuMemoryGiB"],
        "capabilities": list(CAPABILITIES),
        "status": "passed",
    }
    return {
        "schemaVersion": 1,
        "kind": "alpha2-model-selection-evidence-candidate",
        "promotionDecision": "owner-review-required",
        "automaticSelectionEvidence": selector_record,
        "measurements": {
            "systemMemoryGiB": profile["systemMemoryGiB"],
            "usableGpuMemoryGiB": profile["usableGpuMemoryGiB"],
            "averageTokensPerSecond": round(
                sum(item["tokensPerSecond"] for item in metrics) / len(metrics), 3
            ),
            "peakGpuMemoryBytes": max(item["peakGpuMemoryBytes"] for item in metrics),
            "samplesPassed": sum(item["samplesPassed"] for item in metrics),
            "unloadPasses": sum(item["unloadPasses"] for item in metrics),
        },
        "selectorPolicyCanonicalSha256": profile["selectorPolicyCanonicalSha256"],
        "containsPrivateMachineIdentity": False,
        "containsRawPromptsOrResponses": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, nargs=3)
    args = parser.parse_args()
    try:
        print(json.dumps(build_group([_read_result(path) for path in args.results]), indent=2, sort_keys=True))
    except EvidenceError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
