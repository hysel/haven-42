#!/usr/bin/env python3
"""Hostile tests for the inactive post-quantum readiness foundation."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-post-quantum-readiness.py"
SPEC = importlib.util.spec_from_file_location("pqc_readiness", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main() -> None:
    inventory = json.loads((ROOT / "config" / "cryptographic-inventory.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "config" / "post-quantum-cryptography-contract.json").read_text(encoding="utf-8"))
    passed = 0

    result = MODULE.validate(copy.deepcopy(inventory), copy.deepcopy(contract))
    assert result["Status"] == "validated-inactive-foundation"
    assert result["InventoryEntryCount"] == 8
    assert result["StandardCount"] == 3
    assert result["CandidateProfileCount"] == 3
    assert all(result[name] is False for name in ("RuntimeAdmitted", "AlgorithmActivated", "SignatureVerified", "TlsPolicyChanged", "MachineModified"))
    passed += 1

    def deny(inventory_mutator, contract_mutator, expected: str) -> None:
        nonlocal passed
        candidate_inventory = copy.deepcopy(inventory)
        candidate_contract = copy.deepcopy(contract)
        if inventory_mutator:
            inventory_mutator(candidate_inventory)
        if contract_mutator:
            contract_mutator(candidate_contract)
        try:
            MODULE.validate(candidate_inventory, candidate_contract)
        except MODULE.PostQuantumReadinessError as error:
            assert str(error) == expected, (str(error), expected)
            passed += 1
            return
        raise AssertionError(f"expected rejection: {expected}")

    cases = [
        (lambda value: value.update(extra=True), None, "invalid-inventory-shape"),
        (None, lambda value: value.update(extra=True), "invalid-contract-shape"),
        (lambda value: value.update(schemaVersion=2), None, "unsupported-schema"),
        (lambda value: value.update(inventoryId="other"), None, "invalid-inventory-id"),
        (None, lambda value: value.update(contractId="other"), "invalid-contract-id"),
        (None, lambda value: value.update(reviewedOn="2026-08-05"), "review-date-mismatch"),
        (lambda value: value.update(status="active"), None, "unsafe-inventory-status"),
        (None, lambda value: value.update(runtimeAdmitted=True), "unsafe-contract-status"),
        (lambda value: value.update(entries=[]), None, "invalid-inventory-entry-count"),
        (lambda value: value["entries"][0].update(extra=True), None, "invalid-inventory-entry-shape"),
        (lambda value: value["entries"][0].update(purpose=""), None, "invalid-inventory-entry-value"),
        (lambda value: value["entries"].reverse(), None, "unsorted-or-duplicate-inventory-entry"),
        (lambda value: value["entries"][0].update(id=value["entries"][1]["id"]), None, "unsorted-or-duplicate-inventory-entry"),
        (lambda value: value["entries"][6].update(id="replacement-boundary"), None, "missing-critical-inventory-boundary"),
        (None, lambda value: value["standards"][0].update(algorithm="Kyber"), "invalid-standards-registry"),
        (None, lambda value: value["candidateProfiles"].update(extra={}), "invalid-candidate-profiles-shape"),
        (None, lambda value: value["candidateProfiles"]["providerTls"].update(group="MLKEM768"), "unsafe-tls-profile"),
        (None, lambda value: value["candidateProfiles"]["providerTls"].update(selected=True), "unsafe-tls-profile"),
        (None, lambda value: value["candidateProfiles"]["providerTls"].update(pqcRequiredForConnection=True), "unsafe-tls-profile"),
        (None, lambda value: value["candidateProfiles"]["providerTls"].update(classicalFallbackAllowed=False), "unsafe-tls-profile"),
        (None, lambda value: value["candidateProfiles"]["providerTls"].update(fallbackMustBeReported=False), "unsafe-tls-profile"),
        (None, lambda value: value["candidateProfiles"]["updateAuthorization"].update(mode="pqc-only"), "unsafe-update-profile"),
        (None, lambda value: value["candidateProfiles"]["updateAuthorization"].update(parameterSetSelected=True), "unsafe-update-profile"),
        (None, lambda value: value["candidateProfiles"]["alternativeSignature"].update(selected=True), "unsafe-alternative-profile"),
        (None, lambda value: value["candidateProfiles"]["providerTls"].update(requiredEvidence=[]), "invalid-providerTls-evidence"),
        (None, lambda value: value["migrationRules"].update(silentDowngradeAllowed=True), "unsafe-migration-rule"),
        (None, lambda value: value["migrationRules"].update(pqcRequiredForConnection=True), "unsafe-migration-rule"),
        (None, lambda value: value["migrationRules"].update(secureClassicalFallbackAllowed=False), "unsafe-migration-rule"),
        (None, lambda value: value["migrationRules"].update(classicalFallbackMustBeReported=False), "unsafe-migration-rule"),
        (None, lambda value: value["migrationRules"].update(classicalProtectionRetainedDuringTransition=False), "unsafe-migration-rule"),
        (None, lambda value: value.update(activationGates=[]), "invalid-activation-gates"),
        (None, lambda value: value["evidence"].update(algorithmActivated=True), "unsafe-evidence-claim"),
        (lambda value: value["effects"].update(keysRead=True), None, "unsafe-inventory-effects-authority"),
        (None, lambda value: value["effects"].update(dependencyAdded=True), "unsafe-contract-effects-authority"),
        (None, lambda value: value["effects"].update(signatureVerified=True), "unsafe-contract-effects-authority"),
        (None, lambda value: value["effects"].update(machineModified=True), "unsafe-contract-effects-authority"),
    ]
    for inventory_mutator, contract_mutator, expected in cases:
        deny(inventory_mutator, contract_mutator, expected)
    print(f"Post-quantum readiness hostile tests passed: {passed} cases.")


if __name__ == "__main__":
    main()
