#!/usr/bin/env python3
"""Validate future updater verifier receipts without establishing trust."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config" / "core-update-trust-handoff-contract.json"
FIXTURE_PATH = ROOT / "examples" / "fixtures" / "core-update-trust-receipt.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
IDENTIFIER = re.compile(r"^[a-z][a-z0-9.-]{0,127}$")
RECEIPT_ID = re.compile(r"^[a-z][a-z0-9-]{15,95}$")
TARGET_TRIPLE = re.compile(r"^[a-z0-9_]+(?:-[a-z0-9_]+){2,4}$")


class TrustHandoffError(ValueError):
    pass


def _strict(value: object, required: list[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(required):
        raise TrustHandoffError(f"invalid-{label}-shape")
    return value


def _timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise TrustHandoffError(f"invalid-{label}-timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise TrustHandoffError(f"invalid-{label}-timestamp") from error
    if parsed.tzinfo != timezone.utc:
        raise TrustHandoffError(f"invalid-{label}-timestamp")
    return parsed


def _digest(value: object, label: str) -> None:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise TrustHandoffError(f"invalid-{label}-digest")


def evaluate(receipt: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if (
        contract.get("runtimeAdmitted") is not False
        or contract.get("implementationStatus") != "structural-admission-only"
        or contract["verification"].get("scenarioValuesAreAuthoritativeEvidence") is not False
        or any(contract["request"].get(field) is not False for field in (
            "rawSignatureAllowed",
            "rawCertificateAllowed",
            "rawTransparencyProofAllowed",
            "rawPathAllowed",
            "rawUrlAllowed",
        ))
    ):
        raise TrustHandoffError("unsafe-trust-handoff-contract")

    _strict(receipt, contract["request"]["required"], "receipt")
    if receipt["schemaVersion"] != contract["schemaVersion"]:
        raise TrustHandoffError("unsupported-schema")
    receipt_id = receipt["receiptId"]
    if not isinstance(receipt_id, str) or not RECEIPT_ID.fullmatch(receipt_id):
        raise TrustHandoffError("invalid-receipt-id")

    verifier = _strict(receipt["verifier"], contract["verifier"]["required"], "verifier")
    if verifier["profile"] not in contract["verifier"]["candidateProfiles"]:
        raise TrustHandoffError("unknown-verifier-profile")
    if not isinstance(verifier["version"], str) or not VERSION.fullmatch(verifier["version"]):
        raise TrustHandoffError("invalid-verifier-version")
    _digest(verifier["binarySha256"], "verifier-binary")
    if not isinstance(verifier["trustRootId"], str) or not IDENTIFIER.fullmatch(verifier["trustRootId"]):
        raise TrustHandoffError("invalid-trust-root-id")

    subject = _strict(receipt["subject"], contract["subject"]["required"], "subject")
    if subject["repository"] != contract["subject"]["repository"]:
        raise TrustHandoffError("repository-identity-mismatch")
    if (
        not isinstance(subject["releaseTag"], str)
        or not subject["releaseTag"].startswith("v")
        or not VERSION.fullmatch(subject["releaseTag"][1:])
    ):
        raise TrustHandoffError("invalid-release-tag")
    if not isinstance(subject["releaseCommit"], str) or not FULL_SHA.fullmatch(subject["releaseCommit"]):
        raise TrustHandoffError("invalid-release-commit")
    _digest(subject["manifestSha256"], "manifest")
    _digest(subject["assetSha256"], "asset")
    if not isinstance(subject["assetId"], str) or not IDENTIFIER.fullmatch(subject["assetId"]):
        raise TrustHandoffError("invalid-asset-id")
    if subject["operatingSystem"] not in contract["subject"]["operatingSystems"]:
        raise TrustHandoffError("unsupported-operating-system")
    if subject["architecture"] not in contract["subject"]["architectures"]:
        raise TrustHandoffError("unsupported-architecture")
    if not isinstance(subject["targetTriple"], str) or not TARGET_TRIPLE.fullmatch(subject["targetTriple"]):
        raise TrustHandoffError("invalid-target-triple")

    verification = _strict(
        receipt["verification"],
        contract["verification"]["required"],
        "verification",
    )
    if any(type(verification[field]) is not bool for field in contract["verification"]["required"]):
        raise TrustHandoffError("invalid-verification-boolean")
    missing = [field for field, value in verification.items() if value is not True]
    if missing:
        raise TrustHandoffError(f"verification-claim-failed:{missing[0]}")

    evaluation_time = _timestamp(receipt["evaluationTimeUtc"], "evaluation")
    issued_at = _timestamp(receipt["issuedAtUtc"], "issued")
    expires_at = _timestamp(receipt["expiresAtUtc"], "expiry")
    if issued_at > evaluation_time:
        raise TrustHandoffError("receipt-issued-in-future")
    if expires_at <= issued_at:
        raise TrustHandoffError("invalid-receipt-lifetime")
    if evaluation_time >= expires_at:
        raise TrustHandoffError("receipt-expired")

    used = receipt["usedReceiptIds"]
    maximum_used = contract["request"]["maximumUsedReceiptIds"]
    if (
        not isinstance(used, list)
        or len(used) > maximum_used
        or len(used) != len(set(used))
        or not all(isinstance(item, str) and RECEIPT_ID.fullmatch(item) for item in used)
    ):
        raise TrustHandoffError("invalid-used-receipt-ids")
    if receipt_id in used:
        raise TrustHandoffError("receipt-replay")

    effects = {
        key[0].upper() + key[1:]: value
        for key, value in contract["effects"].items()
    }
    return {
        "SchemaVersion": 1,
        "Kind": "core-update-trust-handoff",
        "Status": "structurally-admissible-awaiting-native-verification",
        "ReceiptId": receipt_id,
        "VerifierProfile": verifier["profile"],
        "ReleaseTag": subject["releaseTag"],
        "AssetId": subject["assetId"],
        "StructuralAdmission": True,
        "CryptographicVerificationPerformed": False,
        "TrustEstablished": False,
        "PackageEvidencePromoted": False,
        "StagingAllowed": False,
        "ActivationAllowed": False,
        "NextGate": "pinned native verifier registry and real signature or attestation verification",
        **effects,
    }


def run_self_tests() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    passed = 0

    def allow(mutator=None) -> None:
        nonlocal passed
        candidate = copy.deepcopy(fixture)
        if mutator:
            mutator(candidate)
        result = evaluate(candidate, contract)
        assert result["StructuralAdmission"] is True
        assert result["CryptographicVerificationPerformed"] is False
        assert result["TrustEstablished"] is False
        assert result["StagingAllowed"] is False
        assert result["ActivationAllowed"] is False
        effect_fields = [
            field for field in result
            if field.endswith(("Used", "Written", "Performed", "Changed", "Read", "Touched"))
        ]
        assert effect_fields and all(result[field] is False for field in effect_fields)
        passed += 1

    def deny(mutator, expected: str) -> None:
        nonlocal passed
        candidate = copy.deepcopy(fixture)
        mutator(candidate)
        try:
            evaluate(candidate, contract)
        except TrustHandoffError as error:
            if str(error) != expected:
                raise AssertionError(f"expected {expected}, received {error}") from error
            passed += 1
            return
        raise AssertionError(f"expected {expected}")

    allow()
    allow(lambda value: value["verifier"].update(profile="platform-signature-v1"))
    cases = [
        (lambda value: value.update(extra=True), "invalid-receipt-shape"),
        (lambda value: value.update(schemaVersion=2), "unsupported-schema"),
        (lambda value: value.update(receiptId="short"), "invalid-receipt-id"),
        (lambda value: value["verifier"].update(extra=True), "invalid-verifier-shape"),
        (lambda value: value["verifier"].update(profile="unknown"), "unknown-verifier-profile"),
        (lambda value: value["verifier"].update(version="latest"), "invalid-verifier-version"),
        (lambda value: value["verifier"].update(binarySha256="ABC"), "invalid-verifier-binary-digest"),
        (lambda value: value["verifier"].update(trustRootId="../root"), "invalid-trust-root-id"),
        (lambda value: value["subject"].update(repository="other/repo"), "repository-identity-mismatch"),
        (lambda value: value["subject"].update(releaseTag="main"), "invalid-release-tag"),
        (lambda value: value["subject"].update(releaseCommit="main"), "invalid-release-commit"),
        (lambda value: value["subject"].update(manifestSha256="0"), "invalid-manifest-digest"),
        (lambda value: value["subject"].update(assetSha256="0"), "invalid-asset-digest"),
        (lambda value: value["subject"].update(assetId="../asset"), "invalid-asset-id"),
        (lambda value: value["subject"].update(operatingSystem="freebsd"), "unsupported-operating-system"),
        (lambda value: value["subject"].update(architecture="x86"), "unsupported-architecture"),
        (lambda value: value["subject"].update(targetTriple="../target"), "invalid-target-triple"),
        (lambda value: value["verification"].update(extra=True), "invalid-verification-shape"),
        (lambda value: value["verification"].update(manifestSignatureVerified="true"), "invalid-verification-boolean"),
        (lambda value: value["verification"].update(assetAttestationVerified=False), "verification-claim-failed:assetAttestationVerified"),
        (lambda value: value.update(evaluationTimeUtc="not-a-time"), "invalid-evaluation-timestamp"),
        (lambda value: value.update(issuedAtUtc="2026-07-27T12:30:00Z"), "receipt-issued-in-future"),
        (lambda value: value.update(expiresAtUtc="2026-07-27T11:00:00Z"), "invalid-receipt-lifetime"),
        (lambda value: value.update(evaluationTimeUtc="2026-07-27T13:00:00Z"), "receipt-expired"),
        (lambda value: value.update(usedReceiptIds=["invalid"]), "invalid-used-receipt-ids"),
        (lambda value: value.update(usedReceiptIds=[value["receiptId"]]), "receipt-replay"),
        (lambda value: value.update(rawSignature="secret"), "invalid-receipt-shape"),
        (lambda value: value.update(rawPath="C:\\engine"), "invalid-receipt-shape"),
    ]
    for mutator, expected in cases:
        deny(mutator, expected)
    print(f"Core update trust handoff self-test passed: {passed} cases.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a future verifier receipt without establishing trust."
    )
    parser.add_argument("--receipt-path")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_tests()
    if not args.receipt_path:
        parser.error("--receipt-path is required unless --self-test is used")
    try:
        receipt = json.loads(Path(args.receipt_path).read_text(encoding="utf-8"))
        result = evaluate(receipt)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TrustHandoffError) as error:
        print(f"Core update trust handoff rejected input: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Core update verifier receipt is structurally admissible; trust is not established.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
