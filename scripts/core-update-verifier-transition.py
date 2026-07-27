#!/usr/bin/env python3
"""Validate verifier-registry transitions without changing trust or runtime state."""

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
CONTRACT_PATH = ROOT / "config" / "core-update-verifier-transition-contract.json"
FIXTURE_PATH = ROOT / "examples" / "fixtures" / "core-update-verifier-transition.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
IDENTIFIER = re.compile(r"^[a-z][a-z0-9.-]{0,127}$")
TRANSITION_ID = re.compile(r"^[a-z][a-z0-9-]{15,95}$")


class VerifierTransitionError(ValueError):
    pass


def _strict(value: object, required: list[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(required):
        raise VerifierTransitionError(f"invalid-{label}-shape")
    return value


def _timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise VerifierTransitionError(f"invalid-{label}-timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise VerifierTransitionError(f"invalid-{label}-timestamp") from error
    if parsed.tzinfo != timezone.utc:
        raise VerifierTransitionError(f"invalid-{label}-timestamp")
    return parsed


def _registry(
    value: object,
    contract: dict[str, Any],
    label: str,
) -> tuple[dict[str, Any], datetime, datetime, set[tuple[str, str, str, str]], set[str]]:
    registry = _strict(value, contract["registry"]["required"], f"{label}-registry")
    version = registry["registryVersion"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise VerifierTransitionError(f"invalid-{label}-registry-version")
    valid_from = _timestamp(registry["validFromUtc"], f"{label}-registry-valid-from")
    valid_until = _timestamp(registry["validUntilUtc"], f"{label}-registry-valid-until")
    if valid_until <= valid_from:
        raise VerifierTransitionError(f"invalid-{label}-registry-lifetime")
    entries = registry["entries"]
    if (
        not isinstance(entries, list)
        or not entries
        or len(entries) > contract["request"]["maximumEntries"]
    ):
        raise VerifierTransitionError(f"invalid-{label}-registry-entry-count")
    required = contract["registry"]["entryRequired"]
    profiles = set(contract["registry"]["candidateProfiles"])
    statuses = set(contract["registry"]["statuses"])
    keys: list[tuple[str, str, str, str]] = []
    active_roots: set[str] = set()
    for value in entries:
        entry = _strict(value, required, f"{label}-registry-entry")
        if entry["profile"] not in profiles:
            raise VerifierTransitionError(f"unknown-{label}-verifier-profile")
        if not isinstance(entry["verifierVersion"], str) or not VERSION.fullmatch(entry["verifierVersion"]):
            raise VerifierTransitionError(f"invalid-{label}-verifier-version")
        if not isinstance(entry["binarySha256"], str) or not SHA256.fullmatch(entry["binarySha256"]):
            raise VerifierTransitionError(f"invalid-{label}-verifier-digest")
        if not isinstance(entry["trustRootId"], str) or not IDENTIFIER.fullmatch(entry["trustRootId"]):
            raise VerifierTransitionError(f"invalid-{label}-trust-root-id")
        if entry["status"] not in statuses:
            raise VerifierTransitionError(f"invalid-{label}-entry-status")
        key = (
            entry["profile"],
            entry["verifierVersion"],
            entry["binarySha256"],
            entry["trustRootId"],
        )
        keys.append(key)
        if entry["status"] == "active":
            active_roots.add(entry["trustRootId"])
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise VerifierTransitionError(f"unsorted-or-duplicate-{label}-registry-entry")
    if not active_roots:
        raise VerifierTransitionError(f"{label}-registry-has-no-active-root")
    return registry, valid_from, valid_until, set(keys), active_roots


def evaluate(
    request: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract or json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if (
        contract.get("runtimeAdmitted") is not False
        or contract.get("implementationStatus") != "structural-transition-only"
        or contract["authorization"].get("scenarioClaimsAreAuthoritativeEvidence") is not False
        or any(contract["request"].get(field) is not False for field in (
            "rawSignatureAllowed",
            "rawCertificateAllowed",
            "rawTransparencyProofAllowed",
            "rawKeyAllowed",
            "rawPathAllowed",
            "rawUrlAllowed",
        ))
    ):
        raise VerifierTransitionError("unsafe-verifier-transition-contract")
    _strict(request, contract["request"]["required"], "request")
    if request["schemaVersion"] != contract["schemaVersion"]:
        raise VerifierTransitionError("unsupported-schema")
    transition_id = request["transitionId"]
    if not isinstance(transition_id, str) or not TRANSITION_ID.fullmatch(transition_id):
        raise VerifierTransitionError("invalid-transition-id")
    evaluation = _timestamp(request["evaluationTimeUtc"], "evaluation")
    current, current_from, current_until, current_keys, current_roots = _registry(
        request["currentRegistry"],
        contract,
        "current",
    )
    candidate, candidate_from, candidate_until, candidate_keys, candidate_roots = _registry(
        request["candidateRegistry"],
        contract,
        "candidate",
    )
    if not (current_from <= evaluation < current_until):
        raise VerifierTransitionError("current-registry-not-valid-at-evaluation")
    if candidate["registryVersion"] != current["registryVersion"] + 1:
        raise VerifierTransitionError("registry-version-transition-mismatch")
    if candidate_from < evaluation:
        raise VerifierTransitionError("candidate-registry-backdated")
    if candidate_from >= current_until:
        raise VerifierTransitionError("registry-validity-has-no-overlap")
    if candidate_until <= current_until:
        raise VerifierTransitionError("candidate-registry-does-not-extend-validity")
    continuity = current_keys & candidate_keys
    if len(continuity) < contract["registry"]["minimumContinuityAnchors"]:
        raise VerifierTransitionError("trust-continuity-anchor-missing")
    if not (current_roots & candidate_roots):
        raise VerifierTransitionError("active-trust-root-continuity-missing")

    authorization = _strict(
        request["authorization"],
        contract["authorization"]["required"],
        "authorization",
    )
    threshold = authorization["threshold"]
    signers = authorization["signerTrustRootIds"]
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 1:
        raise VerifierTransitionError("invalid-authorization-threshold")
    if (
        not isinstance(signers, list)
        or signers != sorted(signers)
        or len(signers) != len(set(signers))
        or not all(isinstance(value, str) and IDENTIFIER.fullmatch(value) for value in signers)
    ):
        raise VerifierTransitionError("invalid-authorization-signers")
    if threshold > len(signers):
        raise VerifierTransitionError("authorization-threshold-not-met")
    if any(value not in current_roots for value in signers):
        raise VerifierTransitionError("authorization-signer-not-current")
    for field in ("registryDigestVerified", "transitionIdentityVerified", "expiryVerified"):
        if type(authorization[field]) is not bool:
            raise VerifierTransitionError("invalid-authorization-claim")
        if authorization[field] is not True:
            raise VerifierTransitionError(f"authorization-claim-failed:{field}")

    used = request["usedTransitionIds"]
    if (
        not isinstance(used, list)
        or len(used) > contract["request"]["maximumUsedTransitionIds"]
        or len(used) != len(set(used))
        or not all(isinstance(value, str) and TRANSITION_ID.fullmatch(value) for value in used)
    ):
        raise VerifierTransitionError("invalid-used-transition-ids")
    if transition_id in used:
        raise VerifierTransitionError("transition-replay")

    effects = {
        key[0].upper() + key[1:]: value
        for key, value in contract["effects"].items()
    }
    return {
        "SchemaVersion": 1,
        "Kind": "core-update-verifier-transition",
        "State": "structurally-modeled-awaiting-native-authorization",
        "TransitionId": transition_id,
        "CurrentRegistryVersion": current["registryVersion"],
        "CandidateRegistryVersion": candidate["registryVersion"],
        "ContinuityAnchorCount": len(continuity),
        "CandidateActiveRootCount": len(candidate_roots),
        "StructuralTransition": True,
        "AuthorizationClaimsAuthoritative": False,
        "AuthorizationCryptographicallyVerified": False,
        "TrustEstablished": False,
        "TransitionAccepted": False,
        "RegistryModified": False,
        "RuntimeVerifierChanged": False,
        "NextGate": "pinned native authorization verifier, immutable registry evidence, and rollback-tested platform runtime",
        **effects,
    }


def run_self_tests() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    passed = 0

    def allow(mutator=None):
        nonlocal passed
        value = copy.deepcopy(fixture)
        if mutator:
            mutator(value)
        result = evaluate(value, contract)
        assert result["StructuralTransition"] is True
        assert result["AuthorizationClaimsAuthoritative"] is False
        assert result["AuthorizationCryptographicallyVerified"] is False
        assert result["TrustEstablished"] is False
        assert result["TransitionAccepted"] is False
        assert result["RegistryModified"] is False
        assert result["RuntimeVerifierChanged"] is False
        effect_fields = [
            field for field in result
            if field.endswith(("Used", "Written", "Changed", "Read", "Staged", "Activated"))
        ]
        assert effect_fields and all(result[field] is False for field in effect_fields)
        passed += 1

    def deny(mutator, code):
        nonlocal passed
        value = copy.deepcopy(fixture)
        mutator(value)
        try:
            evaluate(value, contract)
        except VerifierTransitionError as error:
            if str(error) != code:
                raise AssertionError(f"expected {code}, received {error}") from error
            passed += 1
            return
        raise AssertionError(f"expected {code}")

    allow()
    cases = [
        (lambda value: value.update(extra=True), "invalid-request-shape"),
        (lambda value: value.update(schemaVersion=2), "unsupported-schema"),
        (lambda value: value.update(transitionId="short"), "invalid-transition-id"),
        (lambda value: value.update(evaluationTimeUtc="not-a-time"), "invalid-evaluation-timestamp"),
        (lambda value: value["currentRegistry"].update(extra=True), "invalid-current-registry-shape"),
        (lambda value: value["currentRegistry"].update(registryVersion=True), "invalid-current-registry-version"),
        (lambda value: value["currentRegistry"].update(validUntilUtc="2025-01-01T00:00:00Z"), "invalid-current-registry-lifetime"),
        (lambda value: value["currentRegistry"].update(entries=[]), "invalid-current-registry-entry-count"),
        (lambda value: value["currentRegistry"]["entries"][0].update(extra=True), "invalid-current-registry-entry-shape"),
        (lambda value: value["currentRegistry"]["entries"][0].update(profile="unknown"), "unknown-current-verifier-profile"),
        (lambda value: value["currentRegistry"]["entries"][0].update(verifierVersion="latest"), "invalid-current-verifier-version"),
        (lambda value: value["currentRegistry"]["entries"][0].update(binarySha256="ABC"), "invalid-current-verifier-digest"),
        (lambda value: value["currentRegistry"]["entries"][0].update(trustRootId="../root"), "invalid-current-trust-root-id"),
        (lambda value: value["currentRegistry"]["entries"][0].update(status="revoked"), "invalid-current-entry-status"),
        (lambda value: value["currentRegistry"]["entries"][0].update(status="retiring"), "current-registry-has-no-active-root"),
        (lambda value: value["candidateRegistry"].update(registryVersion=3), "registry-version-transition-mismatch"),
        (lambda value: value["candidateRegistry"].update(validFromUtc="2026-01-01T00:00:00Z"), "candidate-registry-backdated"),
        (lambda value: value["candidateRegistry"].update(validFromUtc="2027-01-01T00:00:00Z"), "registry-validity-has-no-overlap"),
        (lambda value: value["candidateRegistry"].update(validUntilUtc="2026-12-01T00:00:00Z"), "candidate-registry-does-not-extend-validity"),
        (lambda value: value["candidateRegistry"]["entries"][1].update(binarySha256="3" * 64), "trust-continuity-anchor-missing"),
        (lambda value: value["candidateRegistry"]["entries"][1].update(status="retiring"), "active-trust-root-continuity-missing"),
        (lambda value: value["authorization"].update(extra=True), "invalid-authorization-shape"),
        (lambda value: value["authorization"].update(threshold=0), "invalid-authorization-threshold"),
        (lambda value: value["authorization"].update(threshold=2), "authorization-threshold-not-met"),
        (lambda value: value["authorization"].update(signerTrustRootIds=["new-root"]), "authorization-signer-not-current"),
        (lambda value: value["authorization"].update(registryDigestVerified="true"), "invalid-authorization-claim"),
        (lambda value: value["authorization"].update(expiryVerified=False), "authorization-claim-failed:expiryVerified"),
        (lambda value: value.update(usedTransitionIds=["invalid"]), "invalid-used-transition-ids"),
        (lambda value: value.update(usedTransitionIds=[value["transitionId"]]), "transition-replay"),
        (lambda value: value.update(rawSignature="secret"), "invalid-request-shape"),
        (lambda value: value.update(rawKey="secret"), "invalid-request-shape"),
        (lambda value: value.update(rawPath="C:\\trust"), "invalid-request-shape"),
    ]
    for mutator, code in cases:
        deny(mutator, code)
    print(f"Core update verifier transition self-test passed: {passed} cases.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Model a verifier-registry transition without changing trust."
    )
    parser.add_argument("--request")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_tests()
    if not args.request:
        parser.error("--request is required unless --self-test is used")
    try:
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        result = evaluate(request)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, VerifierTransitionError) as error:
        print(f"Core update verifier transition rejected input: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Verifier transition modeled; no authorization was verified and no trust changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
