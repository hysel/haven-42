#!/usr/bin/env python3
"""Plan local image-provider lifecycle transitions without machine effects."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config" / "local-image-lifecycle-contract.json"
ONBOARDING_PATH = ROOT / "config" / "local-image-onboarding-contract.json"
FIXTURE_PATH = ROOT / "examples" / "fixtures" / "local-image-lifecycle-request.json"
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9.-]{0,95}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
OPERATION_ID = re.compile(r"^[0-9a-f]{32}$")


class ImageLifecycleError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ImageLifecycleError("configuration-unavailable") from error
    if not isinstance(value, dict):
        raise ImageLifecycleError("configuration-invalid")
    return value


def _strict(value: Any, fields: list[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ImageLifecycleError(f"invalid-{label}-shape")
    return value


def _boolean_map(value: Any, fields: list[str], label: str) -> dict[str, bool]:
    result = _strict(value, fields, label)
    if any(type(result[field]) is not bool for field in fields):
        raise ImageLifecycleError(f"invalid-{label}-boolean")
    return result


def _scan_forbidden(value: Any, contract: dict[str, Any]) -> None:
    pending = [(value, 0)]
    visited = 0
    forbidden = set(contract["request"]["forbiddenFieldNames"])
    while pending:
        current, depth = pending.pop()
        if depth > contract["request"]["maximumNestingDepth"]:
            raise ImageLifecycleError("request-nesting-too-deep")
        if not isinstance(current, (dict, list)):
            continue
        visited += 1
        if visited > contract["request"]["maximumContainerNodes"]:
            raise ImageLifecycleError("request-too-complex")
        if isinstance(current, dict):
            if any(key in forbidden for key in current):
                raise ImageLifecycleError("forbidden-request-authority")
            pending.extend((child, depth + 1) for child in current.values())
        else:
            pending.extend((child, depth + 1) for child in current)


def _artifact(value: Any, contract: dict[str, Any], label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    result = _strict(value, contract["artifactRequiredFields"], f"{label}-artifact")
    if not isinstance(result["artifactId"], str) or IDENTIFIER.fullmatch(result["artifactId"]) is None:
        raise ImageLifecycleError(f"invalid-{label}-artifact-id")
    if not isinstance(result["version"], str) or IDENTIFIER.fullmatch(result["version"]) is None:
        raise ImageLifecycleError(f"invalid-{label}-version")
    if not isinstance(result["sha256"], str) or DIGEST.fullmatch(result["sha256"]) is None:
        raise ImageLifecycleError(f"invalid-{label}-digest")
    if type(result["knownGood"]) is not bool:
        raise ImageLifecycleError(f"invalid-{label}-known-good")
    return result


def _result(
    contract: dict[str, Any],
    request: dict[str, Any],
    *,
    status: str,
    transitions: list[str],
    rollback_required: bool = False,
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "local-image-lifecycle-simulation",
        "status": status,
        "operation": request["operation"],
        "requestId": request["requestId"],
        "profileId": request["profileId"],
        "transitions": transitions,
        "rollbackRequired": rollback_required,
        "retentionPlan": dict(request["retention"]),
        "runtimeAdmitted": False,
        "machineModificationAllowed": False,
        "scenarioEvidenceAuthoritative": False,
        "effects": dict(contract["effects"]),
    }


def evaluate(request: dict[str, Any]) -> dict[str, Any]:
    contract = _load(CONTRACT_PATH)
    onboarding = _load(ONBOARDING_PATH)
    if (
        contract.get("status") != "simulation-only-not-runtime-admitted"
        or contract.get("runtimeAdmitted") is not False
        or contract.get("scenarioEvidenceIsAuthoritative") is not False
        or any(contract.get("effects", {}).values())
    ):
        raise ImageLifecycleError("unsafe-lifecycle-contract")
    serialized = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(serialized) > contract["request"]["maximumSerializedBytes"]:
        raise ImageLifecycleError("request-too-large")
    _scan_forbidden(request, contract)
    _strict(request, contract["request"]["requiredFields"], "request")
    if request["schemaVersion"] != contract["schemaVersion"]:
        raise ImageLifecycleError("unsupported-schema")
    if request["operation"] not in contract["operations"]:
        raise ImageLifecycleError("unsupported-operation")
    if not isinstance(request["requestId"], str) or IDENTIFIER.fullmatch(request["requestId"]) is None:
        raise ImageLifecycleError("invalid-request-id")

    profiles = {
        profile["id"]: profile
        for profile in onboarding["profiles"]
        if isinstance(profile, dict) and isinstance(profile.get("id"), str)
    }
    profile = profiles.get(request["profileId"])
    if profile is None:
        raise ImageLifecycleError("unknown-profile")

    current = _artifact(request["currentArtifact"], contract, "current")
    candidate = _artifact(request["candidateArtifact"], contract, "candidate")
    evidence = _boolean_map(
        request["evidence"], contract["evidenceRequiredFields"], "evidence"
    )
    compatibility = _boolean_map(
        request["compatibility"],
        contract["compatibilityRequiredFields"],
        "compatibility",
    )
    health = _boolean_map(
        request["health"], contract["healthRequiredFields"], "health"
    )
    journal = _strict(
        request["journal"], contract["journal"]["requiredFields"], "journal"
    )
    if journal["phase"] not in contract["journal"]["phases"]:
        raise ImageLifecycleError("invalid-journal-phase")
    for field in ("activeArtifactId", "candidateArtifactId", "previousArtifactId"):
        value = journal[field]
        if value is not None and (
            not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None
        ):
            raise ImageLifecycleError("invalid-journal-artifact-id")
    if journal["operationId"] is not None and (
        not isinstance(journal["operationId"], str)
        or OPERATION_ID.fullmatch(journal["operationId"]) is None
    ):
        raise ImageLifecycleError("invalid-operation-id")

    retention = _strict(
        request["retention"], contract["retention"]["requiredFields"], "retention"
    )
    choice_map = {
        "providerData": "providerDataChoices",
        "generatedArtifacts": "generatedArtifactChoices",
        "previousRuntime": "previousRuntimeChoices",
    }
    for field, choices in choice_map.items():
        if retention[field] not in contract["retention"][choices]:
            raise ImageLifecycleError(f"invalid-retention-{field}")

    operation = request["operation"]
    if operation == "inspect-eligibility":
        return _result(
            contract,
            request,
            status=(
                "eligible-for-effect-free-planning"
                if profile["status"] == "tested-passed"
                else "candidate-unavailable"
            ),
            transitions=["profile-evidence-inspected"],
        )
    if profile["status"] != "tested-passed":
        raise ImageLifecycleError("profile-not-promoted")

    if operation == "recover-interrupted":
        if journal["phase"] not in {
            "staging",
            "activating",
            "post-health",
            "rollback-required",
            "uninstalling",
        }:
            raise ImageLifecycleError("no-interrupted-operation")
        if journal["operationId"] is None:
            raise ImageLifecycleError("interrupted-journal-incomplete")
        return _result(
            contract,
            request,
            status="interrupted-recovery-plan",
            transitions=[
                "stop-before-new-effects",
                "preserve-user-data",
                "restore-known-good-selection",
                "verify-rollback-health",
            ],
            rollback_required=True,
        )

    if journal["phase"] != "idle" or journal["operationId"] is not None:
        raise ImageLifecycleError("lifecycle-already-in-progress")
    if current is None and journal["activeArtifactId"] is not None:
        raise ImageLifecycleError("journal-active-artifact-mismatch")
    if current is not None and journal["activeArtifactId"] != current["artifactId"]:
        raise ImageLifecycleError("journal-active-artifact-mismatch")
    if any(journal[field] is not None for field in ("candidateArtifactId", "previousArtifactId")):
        raise ImageLifecycleError("idle-journal-not-empty")

    if operation == "plan-uninstall":
        if current is None or candidate is not None or current["knownGood"] is not True:
            raise ImageLifecycleError("invalid-uninstall-artifacts")
        return _result(
            contract,
            request,
            status="uninstall-plan-only",
            transitions=[
                "disclose-retention-choice",
                "stop-provider-planned",
                "remove-runtime-planned",
                "verify-user-data-disposition",
            ],
        )

    if operation == "plan-install":
        if current is not None or candidate is None:
            raise ImageLifecycleError("invalid-install-artifacts")
    elif operation in ("plan-update", "plan-rollback"):
        if current is None or candidate is None:
            raise ImageLifecycleError("two-artifacts-required")
        if current["artifactId"] == candidate["artifactId"]:
            raise ImageLifecycleError("artifact-id-replay")
        if current["sha256"] == candidate["sha256"]:
            raise ImageLifecycleError("artifact-digest-replay")
        if current["knownGood"] is not True:
            raise ImageLifecycleError("current-artifact-not-known-good")
        if operation == "plan-rollback" and candidate["knownGood"] is not True:
            raise ImageLifecycleError("rollback-target-not-known-good")

    missing_evidence = [field for field, value in evidence.items() if value is not True]
    if missing_evidence:
        raise ImageLifecycleError(f"evidence-missing:{missing_evidence[0]}")
    missing_compatibility = [
        field for field, value in compatibility.items() if value is not True
    ]
    if missing_compatibility:
        raise ImageLifecycleError(
            f"compatibility-failed:{missing_compatibility[0]}"
        )
    if health["stagedPreflightPassed"] is not True:
        raise ImageLifecycleError("staged-health-failed")

    if operation == "plan-rollback":
        if health["rollbackHealthPassed"] is not True:
            raise ImageLifecycleError("rollback-health-failed")
        return _result(
            contract,
            request,
            status="rollback-plan-only",
            transitions=[
                "evidence-validated",
                "rollback-target-validated",
                "atomic-selection-planned",
                "rollback-health-planned",
            ],
        )

    transitions = [
        "evidence-validated",
        "compatibility-validated",
        "staging-planned",
        "staged-health-planned",
        "atomic-selection-planned",
    ]
    if health["postActivationPassed"]:
        transitions.extend(["post-health-planned", "retention-cleanup-planned"])
        return _result(
            contract,
            request,
            status=(
                "install-plan-only"
                if operation == "plan-install"
                else "update-plan-only"
            ),
            transitions=transitions,
        )
    if operation == "plan-install":
        transitions.extend(["post-health-failed", "remove-failed-install-planned"])
    else:
        transitions.extend(
            [
                "post-health-failed",
                "rollback-required",
                "restore-known-good-selection",
                "verify-rollback-health",
            ]
        )
    return _result(
        contract,
        request,
        status="failed-health-recovery-plan",
        transitions=transitions,
        rollback_required=operation == "plan-update",
    )


def _self_test() -> int:
    fixture = _load(FIXTURE_PATH)
    passed = 0

    def allow(mutator=None, status="update-plan-only") -> dict[str, Any]:
        nonlocal passed
        value = copy.deepcopy(fixture)
        if mutator:
            mutator(value)
        result = evaluate(value)
        assert result["status"] == status
        assert result["runtimeAdmitted"] is False
        assert result["machineModificationAllowed"] is False
        assert result["scenarioEvidenceAuthoritative"] is False
        assert not any(result["effects"].values())
        passed += 1
        return result

    def deny(mutator, code: str) -> None:
        nonlocal passed
        value = copy.deepcopy(fixture)
        mutator(value)
        try:
            evaluate(value)
        except ImageLifecycleError as error:
            assert str(error) == code, (str(error), code)
            passed += 1
            return
        raise AssertionError(f"image lifecycle request unexpectedly admitted: {code}")

    allow()
    allow(
        lambda value: value["health"].update(postActivationPassed=False),
        "failed-health-recovery-plan",
    )
    allow(
        lambda value: value.update(operation="inspect-eligibility"),
        "eligible-for-effect-free-planning",
    )

    def install(value):
        value["operation"] = "plan-install"
        value["currentArtifact"] = None
        value["journal"]["activeArtifactId"] = None

    allow(install, "install-plan-only")

    def uninstall(value):
        value["operation"] = "plan-uninstall"
        value["candidateArtifact"] = None

    allow(uninstall, "uninstall-plan-only")

    def rollback(value):
        value["operation"] = "plan-rollback"
        value["candidateArtifact"]["knownGood"] = True

    allow(rollback, "rollback-plan-only")

    def interrupted(value):
        value["operation"] = "recover-interrupted"
        value["journal"].update(
            phase="post-health",
            operationId="a" * 32,
            candidateArtifactId=value["candidateArtifact"]["artifactId"],
            previousArtifactId=value["currentArtifact"]["artifactId"],
        )

    allow(interrupted, "interrupted-recovery-plan")
    allow(
        lambda value: value.update(
            operation="inspect-eligibility",
            profileId="comfyui-sdxl-windows-amd",
        ),
        "candidate-unavailable",
    )

    cases = [
        (lambda v: v.update(extra=True), "invalid-request-shape"),
        (lambda v: v.update(schemaVersion=2), "unsupported-schema"),
        (lambda v: v.update(operation="execute-install"), "unsupported-operation"),
        (lambda v: v.update(profileId="unknown-profile"), "unknown-profile"),
        (lambda v: v.update(profileId="comfyui-sdxl-windows-amd"), "profile-not-promoted"),
        (lambda v: v.update(path="C:\\runtime"), "forbidden-request-authority"),
        (lambda v: v["candidateArtifact"].update(sha256="ABC"), "invalid-candidate-digest"),
        (lambda v: v["candidateArtifact"].update(sha256=v["currentArtifact"]["sha256"]), "artifact-digest-replay"),
        (lambda v: v["candidateArtifact"].update(artifactId=v["currentArtifact"]["artifactId"]), "artifact-id-replay"),
        (lambda v: v["currentArtifact"].update(knownGood=False), "current-artifact-not-known-good"),
        (lambda v: v["evidence"].update(checksumVerified=False), "evidence-missing:checksumVerified"),
        (lambda v: v["compatibility"].update(acceleratorMatched=False), "compatibility-failed:acceleratorMatched"),
        (lambda v: v["health"].update(stagedPreflightPassed=False), "staged-health-failed"),
        (lambda v: v["journal"].update(phase="activating"), "lifecycle-already-in-progress"),
        (lambda v: v["journal"].update(activeArtifactId="other"), "journal-active-artifact-mismatch"),
        (lambda v: v["journal"].update(candidateArtifactId="candidate"), "idle-journal-not-empty"),
        (lambda v: v["retention"].update(providerData="automatic-delete"), "invalid-retention-providerData"),
    ]
    for mutator, code in cases:
        deny(mutator, code)

    def bad_rollback(value):
        value["operation"] = "plan-rollback"

    deny(bad_rollback, "rollback-target-not-known-good")
    deny(
        lambda value: value.update(operation="recover-interrupted"),
        "no-interrupted-operation",
    )

    def incomplete_recovery(value):
        interrupted(value)
        value["journal"]["operationId"] = None

    deny(incomplete_recovery, "interrupted-journal-incomplete")
    print(f"Local image lifecycle hostile self-test passed: {passed} cases.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simulate local image-provider lifecycle decisions without effects."
    )
    parser.add_argument("--scenario-path")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    if not args.scenario_path:
        parser.error("--scenario-path is required unless --self-test is used")
    try:
        result = evaluate(_load(Path(args.scenario_path)))
    except ImageLifecycleError as error:
        print(f"Local image lifecycle rejected input: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
