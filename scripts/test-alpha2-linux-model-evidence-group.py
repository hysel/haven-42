#!/usr/bin/env python3
"""Hostile and happy-path checks for Alpha 2 model evidence grouping."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts/alpha2-linux-model-evidence-group.py"
SPEC = importlib.util.spec_from_file_location("alpha2_model_evidence_group", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def cell(capability: str, backend: str = "cuda") -> dict:
    return {
        "durationSeconds": 2.5,
        "errorCode": None,
        "evidence": {
            "architecture": "x64",
            "automaticEvidenceCandidate": True,
            "backendMode": backend,
            "capability": capability,
            "capabilityPassed": True,
            "manifestDigest": "a" * 64,
            "modelId": "qwen35-08b-q8",
            "operatingSystemId": "ubuntu-26.04",
            "platformFamily": "linux",
            "provider": "ollama",
            "providerVersion": "0.32.5",
            "selectorPolicyCanonicalSha256": "b" * 64,
            "storageAdmitted": True,
            "systemMemoryGiB": 15.0,
            "usableGpuMemoryGiB": 0.0 if backend == "cpu" else 16.0,
        },
        "metrics": {
            "outputTokens": 24,
            "peakGpuMemoryBytes": 0 if backend == "cpu" else 100,
            "promptTokens": 20,
            "samplesAttempted": 3,
            "samplesFailed": 0,
            "samplesPassed": 3,
            "tokensPerSecond": 42.0,
            "unloadPasses": 3,
        },
        "outcome": "passed",
    }


def expect_failure(results: list[dict], code: str) -> None:
    try:
        MODULE.build_group(results)
    except MODULE.EvidenceError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError(f"Expected failure: {code}")


def main() -> int:
    good = [cell(item) for item in MODULE.CAPABILITIES]
    grouped = MODULE.build_group(good)
    assert grouped["promotionDecision"] == "owner-review-required"
    assert grouped["measurements"]["samplesPassed"] == 9
    assert grouped["measurements"]["unloadPasses"] == 9
    assert grouped["automaticSelectionEvidence"]["capabilities"] == list(MODULE.CAPABILITIES)
    assert grouped["automaticSelectionEvidence"]["selectorPolicyCanonicalSha256"] == "b" * 64
    assert grouped["automaticSelectionEvidence"]["minimumTestedSystemMemoryGiB"] == 15.0
    assert grouped["automaticSelectionEvidence"]["minimumTestedUsableGpuMemoryGiB"] == 16.0

    expect_failure(good[:2], "exactly-three-results-required")
    duplicate = copy.deepcopy(good)
    duplicate[2]["evidence"]["capability"] = "general.chat"
    expect_failure(duplicate, "capability-set-incomplete-or-duplicated")
    mismatch = copy.deepcopy(good)
    mismatch[2]["evidence"]["providerVersion"] = "0.32.6"
    expect_failure(mismatch, "exact-profile-mismatch")
    stale_policy = copy.deepcopy(good)
    stale_policy[2]["evidence"]["selectorPolicyCanonicalSha256"] = "c" * 64
    expect_failure(stale_policy, "exact-profile-mismatch")
    for field, value in (
        ("samplesAttempted", 2), ("samplesPassed", 2), ("samplesFailed", 1),
        ("unloadPasses", 2), ("peakGpuMemoryBytes", 0),
    ):
        broken = copy.deepcopy(good)
        broken[0]["metrics"][field] = value
        expect_failure(broken, "required-repetition-or-residency-proof-missing")
    failed = copy.deepcopy(good)
    failed[0]["outcome"] = "failed"
    expect_failure(failed, "result-did-not-pass-contract")
    not_candidate = copy.deepcopy(good)
    not_candidate[0]["evidence"]["automaticEvidenceCandidate"] = False
    expect_failure(not_candidate, "result-not-eligible-for-automatic-evidence")
    cpu = [cell(item, "cpu") for item in MODULE.CAPABILITIES]
    assert MODULE.build_group(cpu)["measurements"]["peakGpuMemoryBytes"] == 0
    cpu_gpu = copy.deepcopy(cpu)
    cpu_gpu[0]["metrics"]["peakGpuMemoryBytes"] = 1
    expect_failure(cpu_gpu, "required-repetition-or-residency-proof-missing")
    extra = copy.deepcopy(good)
    extra[0]["metrics"]["unexpected"] = 1
    expect_failure(extra, "result-did-not-pass-contract")
    print("Alpha 2 Linux model evidence group checks passed: 16")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
