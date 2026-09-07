#!/usr/bin/env python3
"""Hostile tests for the fail-closed Alpha 2 promotion-readiness report."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


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
    assert report["PublicationPlatforms"] == ["windows-x64", "linux-x64", "macos-arm64"]
    assert report["HistoricalUnsignedCandidatePlatforms"] == ["windows-x64", "linux-x64"]
    assert report["HistoricalUnsignedCandidateBuildComplete"] is True
    assert report["PrimaryNativeValidationCells"] == [
        "windows-11-x64-nvidia",
        "ubuntu-26.04-x64-nvidia",
        "bazzite-44-x64-nvidia",
        "macos-arm64",
    ]
    assert report["LinuxCpuCompatibilityCellCount"] == 9
    assert report["ManagedRuntimeSelected"] == "0.32.14"
    assert report["StatusCounts"] == {
        "candidate-required": 7,
        "owner-required": 1,
        "satisfied": 12,
    }
    assert report["GateCount"] == 20
    assert report["CandidateBuildComplete"] is False
    assert report["ReadyForNativeValidation"] is False
    assert report["ReadyForOwnerReview"] is False
    assert report["PublicationAllowed"] is False
    assert report["ProductionReady"] is False
    checks = 12

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
        (lambda value: value.update(schemaVersion=1), "invalid-contract-identity"),
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
        (lambda value: gate(value, "release-contract").update(status="candidate-required"), "candidate-evidence-regressed"),
        (lambda value: gate(value, "support-matrix-freeze").update(status="owner-required"), "candidate-evidence-regressed"),
        (lambda value: gate(value, "historical-hosted-candidate-ci").update(status="candidate-required"), "candidate-evidence-regressed"),
        (lambda value: gate(value, "native-package-validation").update(status="satisfied"), "native-validation-boundary-mismatch"),
        (lambda value: gate(value, "publication-approval").update(status="satisfied"), "owner-authority-mismatch"),
        (lambda value: value["gates"][0]["evidence"].__setitem__(0, "../private"), "invalid-evidence-reference"),
        (lambda value: value["gates"][0]["evidence"].__setitem__(0, "docs/missing.md"), "missing-evidence-reference"),
        (lambda value: value["gates"][0]["evidence"].append(value["gates"][0]["evidence"][0]), "duplicate-evidence-reference"),
        (lambda value: value["authority"].update(scopeApproved=False), "promotion-authority-must-remain-denied"),
        (lambda value: value["authority"].update(candidateCommitSelected=True), "promotion-authority-must-remain-denied"),
        (lambda value: value["authority"].update(releaseCandidatesBuilt=True), "promotion-authority-must-remain-denied"),
        (lambda value: value["authority"].update(readyForOwnerReview=True), "promotion-authority-must-remain-denied"),
        (lambda value: value["authority"].update(publicationAuthorized=True), "promotion-authority-must-remain-denied"),
        (lambda value: value["authority"].update(productionReady=True), "promotion-authority-must-remain-denied"),
    )
    for mutate, code in cases:
        hostile = copy.deepcopy(baseline)
        mutate(hostile)
        rejected(hostile, code)
        checks += 1

    # New scope cannot inherit the historical pair or omit platform trust.
    for gate_id in ('final-three-platform-candidate-set', 'windows-release-signature', 'macos-release-trust'):
        hostile = copy.deepcopy(baseline)
        gate(hostile, gate_id)['status'] = 'satisfied'
        rejected(hostile, 'native-validation-boundary-mismatch')
    hostile = copy.deepcopy(baseline)
    hostile['release']['signingRequirements']['macos-arm64'].remove('notarization')
    rejected(hostile, 'release-scope-mismatch')
    hostile = copy.deepcopy(baseline)
    hostile['release']['signingRequirements']['windows-x64'] = []
    rejected(hostile, 'release-scope-mismatch')
    checks += 5
    release = json.loads(MODULE.RELEASE_CONTRACT.read_text(encoding='utf-8'))
    mutations = [
        lambda r: r['platforms'][2].update(nativeValidationRequired=False),
        lambda r: r['platforms'][0].update(archive='unsigned.zip'),
        lambda r: r['releaseControls']['signingRequirements']['macos-arm64'].remove('notarization'),
        lambda r: r['releaseControls']['signingRequirements'].update({'windows-x64': []}),
        lambda r: r['releaseControls'].update(ownerApprovalRequiredForPublication=False),
    ]
    with tempfile.TemporaryDirectory(prefix='haven42-release-contract-test-') as directory:
        path = Path(directory)/'contract.json'
        for mutate in mutations:
            hostile = copy.deepcopy(release)
            mutate(hostile)
            path.write_text(json.dumps(hostile), encoding='utf-8')
            with patch.object(MODULE, 'RELEASE_CONTRACT', path):
                rejected(copy.deepcopy(baseline), 'release-contract-mismatch')
            checks += 1

    print(f"Alpha 2 promotion readiness hostile tests passed: {checks} checks.")
    final_spec = importlib.util.spec_from_file_location(
        "alpha2_final_tests", ROOT / "scripts" / "test-alpha2-final-release.py",
    )
    final_tests = importlib.util.module_from_spec(final_spec)
    assert final_spec.loader is not None
    final_spec.loader.exec_module(final_tests)
    assert final_tests.main() == 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
