#!/usr/bin/env python3
"""Validate the inactive post-quantum readiness inventory and contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "config" / "cryptographic-inventory.json"
CONTRACT_PATH = ROOT / "config" / "post-quantum-cryptography-contract.json"


class PostQuantumReadinessError(ValueError):
    """Raised when readiness metadata broadens authority or loses integrity."""


def _exact(value: object, required: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != required:
        raise PostQuantumReadinessError(f"invalid-{label}-shape")
    return value


def _false_map(value: object, required: set[str], label: str) -> None:
    mapping = _exact(value, required, label)
    if any(item is not False for item in mapping.values()):
        raise PostQuantumReadinessError(f"unsafe-{label}-authority")


def validate(inventory: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    inventory = _exact(
        inventory,
        {
            "schemaVersion",
            "inventoryId",
            "reviewedOn",
            "status",
            "description",
            "entries",
            "effects",
        },
        "inventory",
    )
    contract = _exact(
        contract,
        {
            "schemaVersion",
            "contractId",
            "reviewedOn",
            "status",
            "runtimeAdmitted",
            "description",
            "standards",
            "candidateProfiles",
            "migrationRules",
            "activationGates",
            "evidence",
            "effects",
        },
        "contract",
    )
    if inventory["schemaVersion"] != 1 or contract["schemaVersion"] != 1:
        raise PostQuantumReadinessError("unsupported-schema")
    if inventory["inventoryId"] != "haven42.cryptographic-inventory":
        raise PostQuantumReadinessError("invalid-inventory-id")
    if contract["contractId"] != "haven42.post-quantum-cryptography-readiness":
        raise PostQuantumReadinessError("invalid-contract-id")
    if inventory["reviewedOn"] != contract["reviewedOn"]:
        raise PostQuantumReadinessError("review-date-mismatch")
    if inventory["status"] != "readiness-inventory-only":
        raise PostQuantumReadinessError("unsafe-inventory-status")
    if contract["status"] != "crypto-agility-foundation-only" or contract["runtimeAdmitted"] is not False:
        raise PostQuantumReadinessError("unsafe-contract-status")

    entries = inventory["entries"]
    if not isinstance(entries, list) or len(entries) != 8:
        raise PostQuantumReadinessError("invalid-inventory-entry-count")
    entry_fields = {"id", "boundary", "state", "mechanism", "purpose", "quantumConcern", "pqcAction"}
    ids: list[str] = []
    for entry in entries:
        entry = _exact(entry, entry_fields, "inventory-entry")
        if not all(isinstance(entry[field], str) and entry[field] for field in entry_fields):
            raise PostQuantumReadinessError("invalid-inventory-entry-value")
        ids.append(entry["id"])
    expected_inventory_order = [
        "browser-loopback-transport",
        "package-and-resource-integrity",
        "provider-https-transport",
        "provider-http-transport",
        "session-and-csrf-authority",
        "conversation-history-encryption",
        "core-update-authorization",
        "platform-code-signing",
    ]
    if "core-update-authorization" not in ids or "provider-https-transport" not in ids:
        raise PostQuantumReadinessError("missing-critical-inventory-boundary")
    if ids != expected_inventory_order or len(ids) != len(set(ids)):
        raise PostQuantumReadinessError("unsorted-or-duplicate-inventory-entry")

    standards = contract["standards"]
    expected_standards = [
        ("FIPS-203", "ML-KEM", "key-establishment-candidate"),
        ("FIPS-204", "ML-DSA", "primary-signature-candidate"),
        ("FIPS-205", "SLH-DSA", "alternative-signature-candidate"),
    ]
    if not isinstance(standards, list) or [
        (item.get("id"), item.get("algorithm"), item.get("role"))
        for item in standards
        if isinstance(item, dict)
    ] != expected_standards or any(set(item) != {"id", "algorithm", "role"} for item in standards):
        raise PostQuantumReadinessError("invalid-standards-registry")

    profiles = _exact(
        contract["candidateProfiles"],
        {"providerTls", "updateAuthorization", "alternativeSignature"},
        "candidate-profiles",
    )
    tls = _exact(
        profiles["providerTls"],
        {
            "profileId", "group", "mode", "pqcRequiredForConnection",
            "classicalFallbackAllowed", "fallbackMustBeReported", "selected",
            "requiredEvidence",
        },
        "tls-profile",
    )
    if (
        tls["group"] != "X25519MLKEM768"
        or tls["mode"] != "prefer-hybrid-with-visible-classical-fallback"
        or tls["pqcRequiredForConnection"] is not False
        or tls["classicalFallbackAllowed"] is not True
        or tls["fallbackMustBeReported"] is not True
        or tls["selected"] is not False
    ):
        raise PostQuantumReadinessError("unsafe-tls-profile")
    update = _exact(profiles["updateAuthorization"], {"profileId", "mode", "parameterSetSelected", "selected", "requiredEvidence"}, "update-profile")
    if update["mode"] != "require-both-during-transition" or update["parameterSetSelected"] is not False or update["selected"] is not False:
        raise PostQuantumReadinessError("unsafe-update-profile")
    alternative = _exact(profiles["alternativeSignature"], {"profileId", "mode", "parameterSetSelected", "selected", "requiredEvidence"}, "alternative-profile")
    if alternative["parameterSetSelected"] is not False or alternative["selected"] is not False:
        raise PostQuantumReadinessError("unsafe-alternative-profile")
    for name, profile in profiles.items():
        evidence = profile["requiredEvidence"]
        if not isinstance(evidence, list) or len(evidence) < 5 or len(evidence) != len(set(evidence)) or not all(isinstance(item, str) and item for item in evidence):
            raise PostQuantumReadinessError(f"invalid-{name}-evidence")

    rules = _exact(
        contract["migrationRules"],
        {
            "customCryptographicImplementationAllowed",
            "experimentalAlgorithmAllowed",
            "rawPrivateKeyInRepositoryAllowed",
            "rawPrivateKeyInLogsAllowed",
            "rendererKeyAccessAllowed",
            "modelKeyAccessAllowed",
            "algorithmIdentifierRequired",
            "versionedEnvelopeRequired",
            "unknownAlgorithmFailsClosed",
            "missingRequiredSignatureFailsClosed",
            "silentDowngradeAllowed",
            "pqcRequiredForConnection",
            "secureClassicalFallbackAllowed",
            "classicalFallbackMustBeReported",
            "classicalProtectionRetainedDuringTransition",
            "pqcReplacesPlatformSigning",
            "pqcMakesHttpSecure",
            "negotiatedTlsClaimWithoutObservationAllowed",
            "bulkContentEncryptionUsesPqc",
        },
        "migration-rules",
    )
    required_true = {
        "algorithmIdentifierRequired",
        "versionedEnvelopeRequired",
        "unknownAlgorithmFailsClosed",
        "missingRequiredSignatureFailsClosed",
        "secureClassicalFallbackAllowed",
        "classicalFallbackMustBeReported",
        "classicalProtectionRetainedDuringTransition",
    }
    if any(rules[name] is not True for name in required_true) or any(
        rules[name] is not False for name in set(rules) - required_true
    ):
        raise PostQuantumReadinessError("unsafe-migration-rule")

    gates = contract["activationGates"]
    if not isinstance(gates, list) or len(gates) != 12 or len(gates) != len(set(gates)) or "production-admission-decision" not in gates:
        raise PostQuantumReadinessError("invalid-activation-gates")
    evidence = _exact(
        contract["evidence"],
        {
            "inventoryCompleteForCurrentKnownBoundaries",
            "algorithmActivated",
            "tlsHybridNegotiationVerified",
            "updateSignatureVerified",
            "nativeWindowsVerified",
            "nativeLinuxVerified",
            "nativeMacosVerified",
            "sourcePackageParityVerified",
            "productionReady",
        },
        "evidence",
    )
    if evidence["inventoryCompleteForCurrentKnownBoundaries"] is not True or any(
        evidence[name] is not False for name in set(evidence) - {"inventoryCompleteForCurrentKnownBoundaries"}
    ):
        raise PostQuantumReadinessError("unsafe-evidence-claim")

    _false_map(
        inventory["effects"],
        {"networkUsed", "filesWritten", "keysGenerated", "keysRead", "trustStoreChanged", "tlsPolicyChanged", "signatureVerified", "packageAuthorized", "updateActivated"},
        "inventory-effects",
    )
    _false_map(
        contract["effects"],
        {"networkUsed", "filesWritten", "dependencyAdded", "keysGenerated", "keysRead", "trustStoreChanged", "tlsPolicyChanged", "signatureVerified", "packageAuthorized", "updateActivated", "machineModified"},
        "contract-effects",
    )
    return {
        "SchemaVersion": 1,
        "Kind": "post-quantum-cryptography-readiness",
        "Status": "validated-inactive-foundation",
        "InventoryEntryCount": len(entries),
        "StandardCount": len(standards),
        "CandidateProfileCount": len(profiles),
        "RuntimeAdmitted": False,
        "AlgorithmActivated": False,
        "SignatureVerified": False,
        "TlsPolicyChanged": False,
        "MachineModified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate inactive Haven 42 PQC readiness metadata.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        result = validate(inventory, contract)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, PostQuantumReadinessError) as error:
        print(f"Post-quantum readiness validation failed: {error}")
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Post-quantum readiness foundation validated; no cryptography or authority was activated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
