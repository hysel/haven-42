#!/usr/bin/env python3
"""Hostile tests for the effect-free Milestone 22 admission ledger."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "milestone22_admission",
    ROOT / "scripts" / "evaluate-milestone22-admission.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = ROOT / "config" / "milestone22-admission-readiness-contract.json"


def rejected(value, code):
    try:
        MODULE.evaluate(value)
    except MODULE.AdmissionReadinessError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"admission ledger unexpectedly accepted: {code}")


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    result = MODULE.evaluate(copy.deepcopy(contract))
    assert result["GateCount"] == 7
    assert result["StatusCounts"] == {
        "development-admitted": 1,
        "owner-deferred": 1,
        "policy-blocked": 1,
        "security-blocked": 3,
        "external-blocked": 1,
    }
    assert result["UnsignedDevelopmentPackageBlocked"] is False
    assert result["RuntimeAuthorityGranted"] is False
    assert result["MachineEffectsAllowed"] is False
    assert result["NetworkActivationAllowed"] is False
    assert result["PlatformCodeSigningAllowed"] is False
    assert result["NotarizationAllowed"] is False
    assert result["PublicationAllowed"] is False
    assert result["TauriOrRustAdmitted"] is False
    assert result["ProductionReady"] is False
    assert sum(gate["currentReadOnlyRuntimeAdmitted"] for gate in result["Gates"]) == 1
    passed = 1

    def deny(mutator, code):
        nonlocal passed
        value = copy.deepcopy(contract)
        mutator(value)
        rejected(value, code)
        passed += 1

    cases = [
        (lambda value: value.update(extra=True), "invalid-contract-shape"),
        (lambda value: value.update(schemaVersion=2), "unsupported-schema"),
        (lambda value: value.update(contractId="other"), "invalid-contract-id"),
        (lambda value: value.update(implementationStatus="runtime"), "invalid-implementation-status"),
        (lambda value: value["authorityBoundary"].update(platformCodeSigningAllowed=True), "authority-must-remain-denied"),
        (lambda value: value["authorityBoundary"].update(tauriOrRustAdmitted=True), "authority-must-remain-denied"),
        (lambda value: value["authorityBoundary"].update(publicationAllowed=True), "authority-must-remain-denied"),
        (lambda value: value["gates"].pop(), "invalid-gate-registry"),
        (lambda value: value["gates"][0].update(extra=True), "invalid-gate-shape"),
        (lambda value: value["gates"][1].update(id=value["gates"][0]["id"]), "invalid-or-duplicate-gate-id"),
        (lambda value: value["gates"][0].update(status="complete"), "unknown-gate-status"),
        (lambda value: value["gates"][0].update(currentScope="../runtime"), "invalid-current-scope"),
        (lambda value: value["gates"][0].update(blocksUnsignedDevelopmentPackage=True), "development-package-must-remain-independent"),
        (lambda value: value["gates"][2].update(currentReadOnlyRuntimeAdmitted=True), "unexpected-runtime-admission"),
        (lambda value: value["gates"][1].update(currentReadOnlyRuntimeAdmitted=False), "development-admission-scope-mismatch"),
        (lambda value: value["gates"][0]["satisfiedEvidence"].__setitem__(0, "../secret"), "invalid-evidence-reference"),
        (lambda value: value["gates"][0]["satisfiedEvidence"].__setitem__(0, "docs/missing.md"), "missing-evidence-reference"),
        (lambda value: value["gates"][0]["satisfiedEvidence"].append(value["gates"][0]["satisfiedEvidence"][0]), "duplicate-evidence-reference"),
        (lambda value: value["gates"][0]["remainingBlockers"].append("Bad Blocker"), "invalid-blocker-registry"),
    ]
    for mutator, code in cases:
        deny(mutator, code)

    print(f"Milestone 22 admission-readiness self-test passed: {passed} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
