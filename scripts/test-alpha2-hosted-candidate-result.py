#!/usr/bin/env python3
"""Hostile tests for the sanitized hosted Alpha 2 candidate result."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "config" / "alpha-2-hosted-candidate-result.json"
SPEC = importlib.util.spec_from_file_location(
    "alpha2_hosted_candidate_result",
    ROOT / "scripts" / "verify-alpha2-hosted-candidate-result.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rejected(value: object, code: str) -> None:
    try:
        MODULE.verify(value)
    except MODULE.HostedCandidateResultError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"unsafe hosted candidate result accepted: {code}")


def main() -> int:
    baseline = json.loads(RECORD.read_text(encoding="utf-8"))
    report = MODULE.verify(copy.deepcopy(baseline))
    assert report == {
        "SchemaVersion": 1,
        "Version": "0.4.0-alpha.2",
        "WorkflowRunId": 33124565721,
        "SourceCommit": "9cd1c7dad92040429493576a7c882388ed6fc4f3",
        "Platforms": ["windows-x64", "linux-x64"],
        "SameKnownLimitations": True,
        "CandidatePairReadyForNativeValidation": True,
        "NativeValidationComplete": False,
        "PublicationAllowed": False,
        "ProductionReady": False,
    }
    checks = 1

    cases = (
        (lambda value: value.update(schemaVersion=2), "invalid-result-identity"),
        (lambda value: value["workflowRun"].update(conclusion="failure"), "invalid-workflow-run"),
        (lambda value: value["workflowRun"].update(sourceCommit="main"), "invalid-workflow-run"),
        (lambda value: value["workflowRun"].update(url="https://example.invalid/run"), "invalid-workflow-run-url"),
        (lambda value: value["workflowRun"]["jobs"].pop(), "hosted-candidate-jobs-incomplete"),
        (lambda value: value["candidates"].reverse(), "candidate-platform-mismatch"),
        (lambda value: value["candidates"][0]["archive"].update(sha256="0"), "invalid-candidate-archive"),
        (lambda value: value["candidates"][1]["archive"].update(sizeBytes=0), "invalid-candidate-archive"),
        (lambda value: value["candidates"][0]["knownLimitations"].update(sha256="a" * 64), "candidate-pair-not-ready"),
        (lambda value: value["pairVerification"].update(sameSourceCommit=False), "candidate-pair-not-ready"),
        (lambda value: value["pairVerification"].update(nativeValidationComplete=True), "candidate-pair-not-ready"),
        (lambda value: value.update(artifactRetentionDays=0), "invalid-artifact-retention"),
        (lambda value: value["authority"].update(signed=True), "publication-authority-overstated"),
        (lambda value: value["authority"].update(publicationAllowed=True), "publication-authority-overstated"),
        (lambda value: value["authority"].update(productionReady=True), "publication-authority-overstated"),
    )
    for mutate, code in cases:
        hostile = copy.deepcopy(baseline)
        mutate(hostile)
        rejected(hostile, code)
        checks += 1

    print(f"Alpha 2 hosted candidate result tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
