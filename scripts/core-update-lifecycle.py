#!/usr/bin/env python3
"""Effect-free lifecycle planner for Haven 42 core updates."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config/core-update-lifecycle-contract.json"
FIXTURE_PATH = ROOT / "examples/fixtures/core-update-lifecycle-request.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
ACTIVATION_ID = re.compile(r"^[0-9a-f]{32}$")


class LifecyclePolicyError(ValueError):
    pass


def _strict(value: object, required: list[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != set(required):
        raise LifecyclePolicyError(f"invalid-{label}-shape")
    return value


def _version(value: object, label: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise LifecyclePolicyError(f"invalid-{label}-version")
    core = value.split("-", 1)[0].split("+", 1)[0]
    return tuple(int(part) for part in core.split("."))


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise LifecyclePolicyError(f"invalid-{label}-digest")
    return value


def _effects(contract: dict) -> dict:
    effects = contract["simulationEffects"]
    if any(value is not False for value in effects.values()):
        raise LifecyclePolicyError("unsafe-simulation-contract")
    return {
        "".join([part[:1].upper() + part[1:] for part in key.split("-")]): value
        for key, value in effects.items()
    }


def _validate_boolean_map(value: object, required: list[str], label: str) -> dict:
    result = _strict(value, required, label)
    if any(type(result[field]) is not bool for field in required):
        raise LifecyclePolicyError(f"invalid-{label}-boolean")
    return result


def _validate_retained(request: dict, contract: dict) -> list[dict]:
    retained = request["retainedVersions"]
    if not isinstance(retained, list) or not retained:
        raise LifecyclePolicyError("retained-version-required")
    required = contract["retainedVersion"]["required"]
    seen: set[str] = set()
    normalized = []
    for entry in retained:
        item = _strict(entry, required, "retained-version")
        version = item["version"]
        _version(version, "retained")
        _digest(item["sha256"], "retained")
        if type(item["knownGood"]) is not bool:
            raise LifecyclePolicyError("invalid-retained-known-good")
        if version in seen:
            raise LifecyclePolicyError("duplicate-retained-version")
        seen.add(version)
        normalized.append(item)
    current = next(
        (item for item in normalized if item["version"] == request["currentVersion"]),
        None,
    )
    if (
        current is None
        or current["sha256"] != request["currentDigest"]
        or current["knownGood"] is not True
    ):
        raise LifecyclePolicyError("active-version-not-known-good")
    previous = next(
        (
            item
            for item in normalized
            if item["version"] == request["previousKnownGoodVersion"]
        ),
        None,
    )
    if previous is None or previous["knownGood"] is not True:
        raise LifecyclePolicyError("previous-known-good-not-retained")
    return normalized


def _retention_plan(
    request: dict,
    retained: list[dict],
    candidate_is_active: bool,
) -> tuple[list[str], list[str]]:
    active = request["candidateVersion"] if candidate_is_active else request["currentVersion"]
    protected = {active, request["previousKnownGoodVersion"]}
    would_retain = [active]
    if request["previousKnownGoodVersion"] != active:
        would_retain.append(request["previousKnownGoodVersion"])
    would_remove = [
        item["version"]
        for item in retained
        if item["version"] not in protected
    ]
    return would_retain, would_remove


def _result(
    contract: dict,
    *,
    status: str,
    operation: str,
    transitions: list[str],
    would_retain: list[str],
    would_remove: list[str],
    health_outcome: str,
) -> dict:
    return {
        "SchemaVersion": 1,
        "Kind": "core-update-lifecycle-simulation",
        "Status": status,
        "Operation": operation,
        "Transitions": transitions,
        "WouldRetainVersions": would_retain,
        "WouldRemoveVersions": would_remove,
        "HealthOutcome": health_outcome,
        "ActivationAllowed": False,
        "MachineModificationAllowed": False,
        "PreservedDataClasses": contract["mustPreserve"],
        **_effects(contract),
    }


def evaluate(request: dict) -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if (
        contract["runtimeAdmitted"] is not False
        or contract["request"]["rawPathsAllowed"] is not False
        or contract["request"]["rawUrlsAllowed"] is not False
        or contract["request"]["commandsArgumentsOrEnvironmentAllowed"] is not False
        or contract["packageEvidence"]["scenarioInputsAreAuthoritativeEvidence"] is not False
    ):
        raise LifecyclePolicyError("unsafe-lifecycle-contract")
    _strict(request, contract["request"]["required"], "request")
    if request["schemaVersion"] != contract["schemaVersion"]:
        raise LifecyclePolicyError("unsupported-schema")
    operation = request["operation"]
    if operation not in contract["operations"]:
        raise LifecyclePolicyError("unsupported-operation")
    mode = request["updateMode"]
    channel = request["channel"]
    if mode not in contract["updateModes"]:
        raise LifecyclePolicyError("unsupported-update-mode")
    if channel not in contract["channels"]:
        raise LifecyclePolicyError("unsupported-channel")
    if mode == "opt-in-stable" and channel != "stable":
        raise LifecyclePolicyError("mode-channel-mismatch")
    if mode == "opt-in-beta" and channel != "beta":
        raise LifecyclePolicyError("mode-channel-mismatch")

    current_version = _version(request["currentVersion"], "current")
    candidate_version = _version(request["candidateVersion"], "candidate")
    _version(request["previousKnownGoodVersion"], "previous-known-good")
    _digest(request["currentDigest"], "current")
    _digest(request["candidateDigest"], "candidate")
    package = _validate_boolean_map(
        request["packageEvidence"],
        contract["packageEvidence"]["required"],
        "package-evidence",
    )
    compatibility = _validate_boolean_map(
        request["compatibility"],
        contract["compatibility"]["required"],
        "compatibility",
    )
    health = _validate_boolean_map(
        request["health"],
        contract["health"]["required"],
        "health",
    )
    journal = _strict(
        request["activationJournal"],
        contract["activationJournal"]["required"],
        "activation-journal",
    )
    if journal["phase"] not in contract["activationJournal"]["phases"]:
        raise LifecyclePolicyError("invalid-journal-phase")
    for field in ("activeVersion", "candidateVersion", "previousVersion"):
        if journal[field] is not None:
            _version(journal[field], f"journal-{field}")
    if journal["activationId"] is not None and (
        not isinstance(journal["activationId"], str)
        or not ACTIVATION_ID.fullmatch(journal["activationId"])
    ):
        raise LifecyclePolicyError("invalid-activation-id")

    retained = _validate_retained(request, contract)
    if request["candidateDigest"] == request["currentDigest"]:
        raise LifecyclePolicyError("candidate-digest-replay")
    if journal["activeVersion"] not in {
        request["currentVersion"],
        request["candidateVersion"],
    }:
        raise LifecyclePolicyError("journal-active-version-mismatch")

    if mode == "disabled":
        return _result(
            contract,
            status="disabled",
            operation=operation,
            transitions=[],
            would_retain=[item["version"] for item in retained],
            would_remove=[],
            health_outcome="not-run",
        )

    if operation == "recover-interrupted":
        if journal["phase"] not in {"activating", "post-health", "rollback-required"}:
            raise LifecyclePolicyError("no-interrupted-activation")
        if (
            journal["activationId"] is None
            or journal["candidateVersion"] != request["candidateVersion"]
            or journal["previousVersion"] != request["previousKnownGoodVersion"]
        ):
            raise LifecyclePolicyError("interrupted-journal-incomplete")
        if (
            journal["phase"] == "activating"
            and journal["activeVersion"] != request["currentVersion"]
        ):
            raise LifecyclePolicyError("activating-journal-selected-candidate")
        if (
            journal["phase"] in {"post-health", "rollback-required"}
            and journal["activeVersion"] != request["candidateVersion"]
        ):
            raise LifecyclePolicyError("recovery-journal-active-version-mismatch")
        would_retain, would_remove = _retention_plan(request, retained, False)
        return _result(
            contract,
            status="interrupted-recovery-planned",
            operation=operation,
            transitions=["rollback-required", "rollback-validated", "rolled-back"],
            would_retain=would_retain,
            would_remove=would_remove,
            health_outcome="rollback-required",
        )

    if journal["activeVersion"] != request["currentVersion"]:
        raise LifecyclePolicyError("journal-active-version-mismatch")
    if journal["phase"] != "idle":
        raise LifecyclePolicyError("activation-already-in-progress")
    if any(
        journal[field] is not None
        for field in ("activationId", "candidateVersion", "previousVersion")
    ):
        raise LifecyclePolicyError("idle-journal-not-empty")

    if operation == "plan-retention":
        would_retain, would_remove = _retention_plan(request, retained, False)
        return _result(
            contract,
            status="retention-plan-only",
            operation=operation,
            transitions=["retention-inspected", "cleanup-planned"],
            would_retain=would_retain,
            would_remove=would_remove,
            health_outcome="not-run",
        )

    if candidate_version <= current_version:
        raise LifecyclePolicyError("candidate-not-newer")
    retained_candidate = next(
        (
            item for item in retained
            if item["version"] == request["candidateVersion"]
        ),
        None,
    )
    if retained_candidate is not None:
        raise LifecyclePolicyError("candidate-version-already-retained")
    if request["previousKnownGoodVersion"] != request["currentVersion"]:
        raise LifecyclePolicyError("previous-known-good-must-be-active")
    missing_evidence = [field for field, value in package.items() if value is not True]
    if missing_evidence:
        raise LifecyclePolicyError(f"package-evidence-missing:{missing_evidence[0]}")
    for field in ("schemasCompatible", "operatingSystemCompatible", "sufficientStorage"):
        if compatibility[field] is not True:
            raise LifecyclePolicyError(f"compatibility-failed:{field}")
    if (
        compatibility["migrationRequired"]
        and not compatibility["migrationReversibleOrForwardCompatible"]
    ):
        raise LifecyclePolicyError("migration-not-reversible")
    if not health["stagedPreflightPassed"]:
        raise LifecyclePolicyError("staged-health-check-failed")

    would_retain, would_remove = _retention_plan(request, retained, True)
    transitions = [
        "evidence-preconditions-satisfied",
        "compatibility-preflight-passed",
        "staging-planned",
        "staged-health-passed",
        "activation-journal-planned",
    ]
    if health["postActivationPassed"]:
        transitions.extend(
            ["atomic-selection-planned", "post-health-passed", "cleanup-planned"]
        )
        return _result(
            contract,
            status="successful-update-plan",
            operation=operation,
            transitions=transitions,
            would_retain=would_retain,
            would_remove=would_remove,
            health_outcome="healthy",
        )
    transitions.extend(
        [
            "atomic-selection-planned",
            "post-health-failed",
            "rollback-required",
            "rollback-validated",
            "rolled-back",
        ]
    )
    rollback_retain, rollback_remove = _retention_plan(request, retained, False)
    return _result(
        contract,
        status="rollback-plan",
        operation=operation,
        transitions=transitions,
        would_retain=rollback_retain,
        would_remove=rollback_remove,
        health_outcome="rollback-required",
    )


def run_self_tests() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    passed = 0

    def allow(mutator=None, expected_status="successful-update-plan") -> dict:
        nonlocal passed
        candidate = copy.deepcopy(fixture)
        if mutator:
            mutator(candidate)
        result = evaluate(candidate)
        assert result["Status"] == expected_status
        assert result["ActivationAllowed"] is False
        assert result["MachineModificationAllowed"] is False
        effect_keys = [
            key
            for key in result
            if key.endswith(("Used", "Written", "Performed", "Requested", "Changed", "Terminated", "Touched"))
        ]
        assert effect_keys and all(result[key] is False for key in effect_keys)
        passed += 1
        return result

    def deny(mutator, expected: str) -> None:
        nonlocal passed
        candidate = copy.deepcopy(fixture)
        mutator(candidate)
        try:
            evaluate(candidate)
        except LifecyclePolicyError as error:
            if str(error) != expected:
                raise AssertionError(f"expected {expected}, received {error}") from error
            passed += 1
            return
        raise AssertionError(f"expected {expected}")

    result = allow()
    assert result["WouldRetainVersions"] == ["0.4.0", "0.3.0"]
    assert result["WouldRemoveVersions"] == ["0.2.0"]
    rollback = allow(
        lambda value: value["health"].update(postActivationPassed=False),
        "rollback-plan",
    )
    assert "rolled-back" in rollback["Transitions"]
    allow(
        lambda value: value.update(updateMode="disabled"),
        "disabled",
    )
    allow(
        lambda value: value.update(operation="plan-retention"),
        "retention-plan-only",
    )

    def interrupted(value: dict) -> None:
        value["operation"] = "recover-interrupted"
        value["activationJournal"] = {
            "phase": "post-health",
            "activationId": "a" * 32,
            "activeVersion": "0.4.0",
            "candidateVersion": "0.4.0",
            "previousVersion": "0.3.0",
        }

    recovery = allow(interrupted, "interrupted-recovery-planned")
    assert recovery["Transitions"][-1] == "rolled-back"

    cases = [
        (lambda v: v.update(extra=True), "invalid-request-shape"),
        (lambda v: v.update(schemaVersion=2), "unsupported-schema"),
        (lambda v: v.update(operation="install"), "unsupported-operation"),
        (lambda v: v.update(updateMode="automatic"), "unsupported-update-mode"),
        (lambda v: v.update(channel="nightly"), "unsupported-channel"),
        (lambda v: v.update(updateMode="opt-in-beta"), "mode-channel-mismatch"),
        (lambda v: v.update(currentVersion="main"), "invalid-current-version"),
        (lambda v: v.update(candidateVersion="0.3.0"), "candidate-not-newer"),
        (lambda v: v.update(candidateVersion="0.2.0"), "candidate-not-newer"),
        (lambda v: v.update(currentDigest="ABC"), "invalid-current-digest"),
        (lambda v: v.update(candidateDigest="ABC"), "invalid-candidate-digest"),
        (lambda v: v.update(candidateDigest=v["currentDigest"]), "candidate-digest-replay"),
        (lambda v: v["packageEvidence"].update(bytesVerified=False), "package-evidence-missing:bytesVerified"),
        (lambda v: v["packageEvidence"].update(manifestSignatureVerified=False), "package-evidence-missing:manifestSignatureVerified"),
        (lambda v: v["packageEvidence"].update(assetAttestationVerified=False), "package-evidence-missing:assetAttestationVerified"),
        (lambda v: v["packageEvidence"].update(provenanceVerified=False), "package-evidence-missing:provenanceVerified"),
        (lambda v: v["packageEvidence"].update(sbomPresent=False), "package-evidence-missing:sbomPresent"),
        (lambda v: v["packageEvidence"].update(thirdPartyNoticesPresent=False), "package-evidence-missing:thirdPartyNoticesPresent"),
        (lambda v: v["compatibility"].update(schemasCompatible=False), "compatibility-failed:schemasCompatible"),
        (lambda v: v["compatibility"].update(operatingSystemCompatible=False), "compatibility-failed:operatingSystemCompatible"),
        (lambda v: v["compatibility"].update(sufficientStorage=False), "compatibility-failed:sufficientStorage"),
        (lambda v: v["compatibility"].update(migrationRequired=True, migrationReversibleOrForwardCompatible=False), "migration-not-reversible"),
        (lambda v: v["health"].update(stagedPreflightPassed=False), "staged-health-check-failed"),
        (lambda v: v.update(previousKnownGoodVersion="0.2.0"), "previous-known-good-must-be-active"),
        (lambda v: v["retainedVersions"].clear(), "retained-version-required"),
        (lambda v: v["retainedVersions"].append(copy.deepcopy(v["retainedVersions"][0])), "duplicate-retained-version"),
        (
            lambda v: v["retainedVersions"].append({
                "version": v["candidateVersion"],
                "sha256": v["candidateDigest"],
                "knownGood": False,
            }),
            "candidate-version-already-retained",
        ),
        (lambda v: v["retainedVersions"][0].update(knownGood=False), "active-version-not-known-good"),
        (lambda v: v["retainedVersions"][0].update(sha256="3" * 64), "active-version-not-known-good"),
        (lambda v: v["activationJournal"].update(phase="activated"), "invalid-journal-phase"),
        (lambda v: v["activationJournal"].update(phase="activating"), "activation-already-in-progress"),
        (lambda v: v["activationJournal"].update(activationId="a" * 32), "idle-journal-not-empty"),
        (lambda v: v["activationJournal"].update(activeVersion="0.2.0"), "journal-active-version-mismatch"),
        (lambda v: v["activationJournal"].update(activationId="replay"), "invalid-activation-id"),
        (lambda v: v.update(rawPath="../engine"), "invalid-request-shape"),
        (lambda v: v["packageEvidence"].update(bytesVerified="true"), "invalid-package-evidence-boolean"),
    ]
    for mutator, expected in cases:
        deny(mutator, expected)

    def incomplete_recovery(value: dict) -> None:
        interrupted(value)
        value["activationJournal"]["activationId"] = None

    deny(incomplete_recovery, "interrupted-journal-incomplete")
    deny(
        lambda value: value.update(operation="recover-interrupted"),
        "no-interrupted-activation",
    )
    def activating_selected_candidate(value: dict) -> None:
        interrupted(value)
        value["activationJournal"]["phase"] = "activating"

    deny(activating_selected_candidate, "activating-journal-selected-candidate")

    def post_health_selected_current(value: dict) -> None:
        interrupted(value)
        value["activationJournal"]["activeVersion"] = value["currentVersion"]

    deny(post_health_selected_current, "recovery-journal-active-version-mismatch")
    print(f"Core update lifecycle hostile self-test passed: {passed} cases.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simulate update lifecycle decisions without machine effects."
    )
    parser.add_argument("--scenario-path")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_tests()
    if not args.scenario_path:
        parser.error("--scenario-path is required unless --self-test is used")
    try:
        request = json.loads(Path(args.scenario_path).read_text(encoding="utf-8"))
        result = evaluate(request)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, LifecyclePolicyError) as error:
        print(f"Core update lifecycle rejected input: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"Status: {result['Status']}\n"
            f"Operation: {result['Operation']}\n"
            "Activation allowed: false"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
