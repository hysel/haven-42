#!/usr/bin/env python3
"""Hostile tests for the private-alpha preparation contract."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "private-alpha-readiness-contract.json"
SPEC = importlib.util.spec_from_file_location(
    "private_alpha_readiness",
    ROOT / "scripts" / "evaluate-private-alpha-readiness.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rejected(value: object, code: str) -> None:
    try:
        MODULE.evaluate(value)
    except MODULE.AlphaReadinessError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"unsafe alpha contract accepted: {code}")


def main() -> int:
    baseline = json.loads(CONTRACT.read_text(encoding="utf-8"))
    result = MODULE.evaluate(copy.deepcopy(baseline))
    assert result["StatusCounts"] == {
        "candidate-required": 4,
        "owner-required": 1,
        "satisfied": 5,
    }
    assert "candidate-version-and-commit" in result["RemainingGates"]
    assert result["PreparationDocumentsComplete"] is True
    assert result["AlphaCandidateAdmitted"] is False
    assert result["ArtifactDistributionActivated"] is False
    assert result["PublicReleaseAllowed"] is False
    assert result["ProductionReady"] is False
    checks = 2

    cases = (
        (lambda value: value.update(schemaVersion=2), "invalid-contract-identity"),
        (lambda value: value.update(implementationStatus="admitted"), "invalid-contract-identity"),
        (lambda value: value["alphaIdentity"].update(candidateVersion="0.4.0-alpha.2"), "alpha-identity-selected-without-approval"),
        (lambda value: value["alphaIdentity"].update(candidateCommit="a" * 40), "alpha-identity-selected-without-approval"),
        (lambda value: value["audience"].update(testerGroupSelected=False), "alpha-audience-authority-broadened"),
        (lambda value: value["audience"].update(publicEnrollmentAllowed=True), "alpha-audience-authority-broadened"),
        (lambda value: value["scope"].update(externalSoftwareBundled=True), "alpha-scope-authority-broadened"),
        (lambda value: value["scope"].update(installerIncluded=True), "alpha-scope-authority-broadened"),
        (lambda value: value["scope"].update(onlineUpdaterEnabled=True), "alpha-scope-authority-broadened"),
        (lambda value: value["targetCells"][1].update(selectedForAlpha=True), "target-cell-promotion-without-evidence"),
        (lambda value: value["targetCells"][2].update(physicalDevelopmentEvidence=True), "target-cell-promotion-without-evidence"),
        (lambda value: value["gates"].pop(), "invalid-gate-registry"),
        (lambda value: value["gates"][1].update(id=value["gates"][0]["id"]), "invalid-gate-registry"),
        (lambda value: value["gates"][0].update(status="complete"), "invalid-gate-registry"),
        (lambda value: value["gates"][0]["evidence"].__setitem__(0, "../private"), "invalid-evidence-reference"),
        (lambda value: value["gates"][0]["evidence"].__setitem__(0, "docs/missing.md"), "missing-evidence-reference"),
        (lambda value: value["gates"][0]["evidence"].append(value["gates"][0]["evidence"][0]), "duplicate-evidence-reference"),
        (lambda value: value["authority"].update(alphaCandidateAdmitted=True), "alpha-authority-must-remain-denied"),
        (lambda value: value["authority"].update(publicReleaseAllowed=True), "alpha-authority-must-remain-denied"),
        (lambda value: value["authority"].update(productionReadinessClaimAllowed=True), "alpha-authority-must-remain-denied"),
    )
    for mutate, code in cases:
        hostile = copy.deepcopy(baseline)
        mutate(hostile)
        rejected(hostile, code)
        checks += 1
    print(f"Private alpha readiness hostile tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
