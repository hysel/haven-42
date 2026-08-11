#!/usr/bin/env python3
"""Hostile offline tests for sanitized Alpha 2 campaign reports."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts/alpha2-linux-campaign-report.py"
SPEC = importlib.util.spec_from_file_location("alpha2_report", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
SELECTOR_SPEC = importlib.util.spec_from_file_location(
    "alpha2_report_selector", ROOT / "scripts/alpha2_model_selector.py"
)
SELECTOR = importlib.util.module_from_spec(SELECTOR_SPEC)
assert SELECTOR_SPEC.loader is not None
sys.modules[SELECTOR_SPEC.name] = SELECTOR
SELECTOR_SPEC.loader.exec_module(SELECTOR)


def result_for(task: dict, provider_version: str = "0.0.0-test") -> dict:
    if task["taskKind"] == "distribution-stage":
        return {
            "outcome": "passed",
            "errorCode": None,
            "durationSeconds": 1,
            "metrics": {},
            "evidence": None,
        }
    policy_sha, bindings = MODULE.CHECKPOINT._load_model_bindings()
    automatic = task["evidenceUse"] == "automatic-candidate"
    return {
        "outcome": "passed",
        "errorCode": None,
        "durationSeconds": 1,
        "metrics": {
            "samplesAttempted": 3,
            "samplesPassed": 3,
            "samplesFailed": 0,
            "unloadPasses": 3,
        },
        "evidence": {
            "selectorPolicyCanonicalSha256": policy_sha,
            "modelId": task["candidateId"],
            "manifestDigest": bindings[task["candidateId"]],
            "platformFamily": "linux",
            "operatingSystemId": "ubuntu-26-04",
            "architecture": "x64",
            "backendMode": "cpu" if task["stage"] == "cpu-selection" else "cuda",
            "provider": "ollama",
            "providerVersion": provider_version,
            "systemMemoryGiB": 16,
            "usableGpuMemoryGiB": 0 if task["stage"] == "cpu-selection" else 16,
            "storageAdmitted": True,
            "capability": task["capabilityId"],
            "capabilityPassed": True,
            "automaticEvidenceCandidate": automatic,
        },
    }


def checkpoint_through(index: int) -> dict:
    value = MODULE.CHECKPOINT.new_checkpoint("a" * 64, "2026-08-08T00:00:00Z")
    for position in range(index):
        task = value["tasks"][position]
        task["status"] = "passed"
        task["attempts"] = 1
        task["result"] = result_for(task)
    value["nextTaskIndex"] = index
    value["revision"] = index
    MODULE.CHECKPOINT.validate_checkpoint(value)
    return value


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    empty = MODULE.build_report(checkpoint_through(0))
    assert empty["automaticSelectionEvidence"] == []
    assert empty["promotionDecision"] == "no-new-evidence"
    assert not empty["containsRawPromptsOrResponses"]
    checks = 3

    complete_profile = checkpoint_through(75)
    report = MODULE.build_report(complete_profile)
    assert len(report["automaticSelectionEvidence"]) == 1
    evidence = report["automaticSelectionEvidence"][0]
    assert evidence["modelId"] == "qwen35-08b-q8"
    assert evidence["capabilities"] == [
        "general.chat", "content.write", "content.summarize"
    ]
    assert evidence["minimumTestedSystemMemoryGiB"] == 16
    assert evidence["minimumTestedUsableGpuMemoryGiB"] == 0
    expected_policy_sha, _ = MODULE.CHECKPOINT._load_model_bindings()
    assert evidence["selectorPolicyCanonicalSha256"] == expected_policy_sha
    assert report["promotionDecision"] == "owner-review-required"
    MODULE.CHECKPOINT.validate_checkpoint(complete_profile)
    decision = SELECTOR.select_model(
        {
            "platformFamily": "linux",
            "operatingSystemId": "ubuntu-26-04",
            "architecture": "x64",
            "backendMode": "cpu",
            "systemMemoryGiB": 16,
            "usableGpuMemoryGiB": 0,
            "storageAdmittedModelIds": ["qwen35-08b-q8"],
            "requestedCapabilities": [
                "general.chat", "content.write", "content.summarize"
            ],
            "provider": "ollama",
            "providerVersion": "0.0.0-test",
        },
        report["automaticSelectionEvidence"],
    )
    assert decision["decision"] == "automatic-selection"
    assert decision["selectedModelId"] == "qwen35-08b-q8"
    checks += 8

    split_profile = copy.deepcopy(complete_profile)
    split_profile["tasks"][74]["result"] = result_for(
        split_profile["tasks"][74], "0.0.1-test"
    )
    MODULE.CHECKPOINT.validate_checkpoint(split_profile)
    split_report = MODULE.build_report(split_profile)
    assert split_report["automaticSelectionEvidence"] == []
    assert split_report["incompleteAutomaticEvidenceGroups"] == 2
    checks += 2

    policy_bound_task = complete_profile["tasks"][72]
    policy_bound_evidence = policy_bound_task["result"]["evidence"]
    stale_policy_evidence = copy.deepcopy(policy_bound_evidence)
    stale_policy_evidence["selectorPolicyCanonicalSha256"] = "0" * 64
    assert MODULE._group_key(policy_bound_task, policy_bound_evidence) != MODULE._group_key(
        policy_bound_task, stale_policy_evidence
    )
    checks += 1

    encoded = json.dumps(report)
    assert all(
        marker not in encoded
        for marker in ("192.168.", "SHA256:", "hostname", "username", "prompt", "response")
    )
    forbidden = {"asyncio", "http", "os", "requests", "socket", "subprocess", "urllib"}
    assert imports(MODULE_PATH).isdisjoint(forbidden)
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert all(value not in source for value in ("shell=True", "ssh ", "qm ", "pct ", "pvesh "))
    checks += 3
    print(f"Alpha 2 campaign report passed {checks} hostile offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
