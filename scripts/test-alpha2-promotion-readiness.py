#!/usr/bin/env python3
"""Hostile tests for the fail-closed Alpha 2 promotion-readiness report."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "alpha-2-promotion-readiness.json"
SPEC = importlib.util.spec_from_file_location(
    "alpha2_promotion_readiness",
    ROOT / "scripts" / "evaluate-alpha2-promotion-readiness.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rejected(value: object, code: str) -> None:
    try:
        MODULE.evaluate(value)
    except MODULE.Alpha2PromotionError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"unsafe Alpha 2 promotion record accepted: {code}")


def gate(value: dict, gate_id: str) -> dict:
    return next(item for item in value["gates"] if item["id"] == gate_id)


def main() -> int:
    baseline = json.loads(CONTRACT.read_text(encoding="utf-8"))
    report = MODULE.evaluate(copy.deepcopy(baseline))
    assert report["Version"] == "0.4.0-alpha.2"
    assert report["PublicationPlatforms"] == ["windows-x64", "linux-x64"]
    assert report["PrimaryNativeValidationCells"] == [
        "windows-11-x64-nvidia",
        "ubuntu-26.04-x64-nvidia",
        "bazzite-44-x64-nvidia",
    ]
    assert report["LinuxCpuCompatibilityCellCount"] == 9
    assert report["ManagedRuntimeSelected"] == "0.32.14"
    assert report["StatusCounts"] == {
        "candidate-required": 10,
        "owner-required": 1,
        "satisfied": 6,
    }
    assert report["GateCount"] == 17
    assert report["ReadyForCandidateBuild"] is True
    assert report["ReadyForOwnerReview"] is False
    assert report["PublicationAllowed"] is False
    assert report["ProductionReady"] is False
    checks = 11

    assert MODULE._admitted_runtime("0.32.14")["admissionState"] == "admitted"
    try:
        MODULE._admitted_runtime("0.32.13")
    except MODULE.Alpha2PromotionError as error:
        assert str(error) == "managed-runtime-not-admitted"
    else:
        raise AssertionError("candidate runtime unexpectedly accepted")
    try:
        MODULE._admitted_runtime("0.32.15")
    except MODULE.Alpha2PromotionError as error:
        assert str(error) == "managed-runtime-not-admitted"
    else:
        raise AssertionError("unregistered runtime unexpectedly accepted")
    checks += 3

    cases = (
        (lambda value: value.update(schemaVersion=2), "invalid-contract-identity"),
        (lambda value: value["release"].update(platforms=["windows-x64"]), "release-scope-mismatch"),
        (lambda value: value["release"].update(productionReady=True), "release-scope-mismatch"),
        (lambda value: value["scopeProposal"].update(status="owner-review-required"), "scope-authority-broadened"),
        (lambda value: value["scopeProposal"].update(changesSupportLabels=True), "scope-authority-broadened"),
        (lambda value: value["scopeProposal"]["primaryNativeValidationCells"].append("macos-arm64"), "scope-authority-broadened"),
        (lambda value: value["scopeProposal"]["compatibilityCoverage"].update(promotionInheritanceAllowed=True), "scope-authority-broadened"),
        (lambda value: value["managedRuntimeDecision"].update(selectedVersion="0.32.5"), "runtime-decision-overstated"),
        (lambda value: value["managedRuntimeDecision"].update(crossVersionEvidenceInheritanceAllowed=True), "runtime-decision-overstated"),
        (lambda value: value["gates"].pop(), "invalid-gate-registry"),
        (lambda value: value["gates"][1].update(id=value["gates"][0]["id"]), "invalid-gate-registry"),
        (lambda value: value["gates"][0].update(status="complete"), "invalid-gate-registry"),
        (lambda value: gate(value, "release-contract").update(status="candidate-required"), "foundation-evidence-regressed"),
        (lambda value: gate(value, "support-matrix-freeze").update(status="owner-required"), "foundation-evidence-regressed"),
        (lambda value: gate(value, "publication-approval").update(status="satisfied"), "owner-authority-mismatch"),
        (lambda value: value["gates"][0]["evidence"].__setitem__(0, "../private"), "invalid-evidence-reference"),
        (lambda value: value["gates"][0]["evidence"].__setitem__(0, "docs/missing.md"), "missing-evidence-reference"),
        (lambda value: value["gates"][0]["evidence"].append(value["gates"][0]["evidence"][0]), "duplicate-evidence-reference"),
        (lambda value: value["authority"].update(scopeApproved=False), "promotion-authority-must-remain-denied"),
        (lambda value: value["authority"].update(readyForOwnerReview=True), "promotion-authority-must-remain-denied"),
        (lambda value: value["authority"].update(publicationAuthorized=True), "promotion-authority-must-remain-denied"),
        (lambda value: value["authority"].update(productionReady=True), "promotion-authority-must-remain-denied"),
    )
    for mutate, code in cases:
        hostile = copy.deepcopy(baseline)
        mutate(hostile)
        rejected(hostile, code)
        checks += 1

    print(f"Alpha 2 promotion readiness hostile tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
