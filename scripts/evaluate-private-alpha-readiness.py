#!/usr/bin/env python3
"""Validate and summarize the non-authoritative private-alpha foundation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config" / "private-alpha-readiness-contract.json"
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXPECTED_GATES = {
    "development-foundation",
    "candidate-version-and-commit",
    "target-platform-selection",
    "exact-candidate-security-review",
    "exact-candidate-hosted-ci",
    "exact-candidate-artifact-set",
    "known-limitations-snapshot",
    "tester-runbook",
    "feedback-and-triage",
    "private-distribution-activation",
}
ALLOWED_STATUSES = {"satisfied", "owner-required", "candidate-required"}


class AlphaReadinessError(ValueError):
    """Raised when the alpha-readiness contract broadens authority or drifts."""


def _reference(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise AlphaReadinessError("invalid-evidence-reference")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise AlphaReadinessError("invalid-evidence-reference")
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise AlphaReadinessError("invalid-evidence-reference") from error
    if not resolved.is_file():
        raise AlphaReadinessError("missing-evidence-reference")
    return value


def evaluate(value: Any) -> dict[str, Any]:
    expected = {
        "schemaVersion", "contractId", "implementationStatus",
        "currentReleaseLine", "alphaIdentity", "audience", "scope",
        "targetCells", "gates", "authority",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise AlphaReadinessError("invalid-contract-shape")
    if (
        value["schemaVersion"] != 1
        or value["contractId"] != "haven42.private-alpha-readiness"
        or value["implementationStatus"] != "candidate-implementation-not-admitted"
        or value["currentReleaseLine"] != "0.4.0-alpha.1"
    ):
        raise AlphaReadinessError("invalid-contract-identity")

    identity = value["alphaIdentity"]
    if identity != {
        "label": "Haven 42 0.4 Alpha 1",
        "candidateVersion": "0.4.0-alpha.1",
        "candidateTag": None,
        "candidateCommit": None,
    }:
        raise AlphaReadinessError("alpha-identity-selected-without-approval")
    audience = value["audience"]
    if audience != {
        "mode": "invited-testers-only",
        "testerGroupSelected": True,
        "privateDistributionChannelSelected": False,
        "publicEnrollmentAllowed": False,
    }:
        raise AlphaReadinessError("alpha-audience-authority-broadened")

    scope = value["scope"]
    if set(scope) != {
        "artifactKind", "externalSoftwareBundled", "installerIncluded",
        "administratorAccessRequired", "systemServiceIncluded",
        "onlineUpdaterEnabled", "workflowExecutionEnabled", "tauriOrRustIncluded",
        "admittedCapabilities", "managedUserScopedSetupCandidate",
    } or scope["artifactKind"] != "unsigned-pyinstaller-one-folder-private-alpha":
        raise AlphaReadinessError("invalid-alpha-scope")
    if any(scope[field] is not False for field in (
        "externalSoftwareBundled", "installerIncluded", "administratorAccessRequired",
        "systemServiceIncluded", "onlineUpdaterEnabled", "workflowExecutionEnabled", "tauriOrRustIncluded",
    )):
        raise AlphaReadinessError("alpha-scope-authority-broadened")
    if scope["admittedCapabilities"] != [
        "general.chat", "content.write", "content.summarize",
    ] or scope["managedUserScopedSetupCandidate"] is not True:
        raise AlphaReadinessError("invalid-alpha-scope")

    targets = value["targetCells"]
    if not isinstance(targets, list) or len(targets) != 3:
        raise AlphaReadinessError("invalid-target-cells")
    expected_targets = {
        "windows-x64": (True, True, True, "native-smoke-passed-clean-commit-gates-remain"),
        "linux-x64": (True, True, False, "exact-alpha-candidate-native-smoke"),
        "macos-arm64": (True, False, False, "owner-parked-physical-macos-evidence"),
    }
    seen_targets: set[str] = set()
    for target in targets:
        if not isinstance(target, dict) or set(target) != {
            "id", "hostedPackageEvidence", "physicalDevelopmentEvidence",
            "selectedForAlpha", "remainingBoundary",
        }:
            raise AlphaReadinessError("invalid-target-cell")
        target_id = target["id"]
        if target_id not in expected_targets or target_id in seen_targets:
            raise AlphaReadinessError("invalid-target-cell")
        seen_targets.add(target_id)
        hosted, physical, selected, boundary = expected_targets[target_id]
        if (
            target["hostedPackageEvidence"] is not hosted
            or target["physicalDevelopmentEvidence"] is not physical
            or target["selectedForAlpha"] is not selected
            or target["remainingBoundary"] != boundary
        ):
            raise AlphaReadinessError("target-cell-promotion-without-evidence")

    gates = value["gates"]
    if not isinstance(gates, list) or len(gates) != len(EXPECTED_GATES):
        raise AlphaReadinessError("invalid-gate-registry")
    seen_gates: set[str] = set()
    gate_statuses: dict[str, str] = {}
    status_counts = {status: 0 for status in sorted(ALLOWED_STATUSES)}
    blockers: list[str] = []
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != {"id", "status", "evidence"}:
            raise AlphaReadinessError("invalid-gate-shape")
        gate_id = gate["id"]
        status = gate["status"]
        if (
            not isinstance(gate_id, str)
            or not SAFE_ID.fullmatch(gate_id)
            or gate_id not in EXPECTED_GATES
            or gate_id in seen_gates
            or status not in ALLOWED_STATUSES
        ):
            raise AlphaReadinessError("invalid-gate-registry")
        seen_gates.add(gate_id)
        gate_statuses[gate_id] = status
        references = gate["evidence"]
        if not isinstance(references, list) or not references or len(references) > 5:
            raise AlphaReadinessError("invalid-evidence-registry")
        safe_references = [_reference(reference) for reference in references]
        if len(set(safe_references)) != len(safe_references):
            raise AlphaReadinessError("duplicate-evidence-reference")
        status_counts[status] += 1
        if status != "satisfied":
            blockers.append(gate_id)
    if seen_gates != EXPECTED_GATES:
        raise AlphaReadinessError("invalid-gate-registry")
    preparation_document_gates = {
        "development-foundation", "target-platform-selection",
        "known-limitations-snapshot", "tester-runbook", "feedback-and-triage",
    }

    authority = value["authority"]
    expected_authority = {
        "alphaCandidateAdmitted", "artifactDistributionActivated",
        "publicReleaseAllowed", "releaseTagAllowed", "signingAllowed",
        "notarizationAllowed", "installerActivationAllowed",
        "onlineUpdateActivationAllowed", "machineModificationAllowed",
        "productionReadinessClaimAllowed",
    }
    if not isinstance(authority, dict) or set(authority) != expected_authority:
        raise AlphaReadinessError("invalid-authority-boundary")
    if any(flag is not False for flag in authority.values()):
        raise AlphaReadinessError("alpha-authority-must-remain-denied")

    return {
        "SchemaVersion": 1,
        "Mode": "candidate-implementation-not-admitted",
        "CurrentReleaseLine": value["currentReleaseLine"],
        "TargetCellCount": len(targets),
        "GateCount": len(gates),
        "StatusCounts": status_counts,
        "RemainingGates": blockers,
        "PreparationDocumentsComplete": all(
            gate_statuses[gate_id] == "satisfied"
            for gate_id in preparation_document_gates
        ),
        "AlphaCandidateAdmitted": False,
        "ArtifactDistributionActivated": False,
        "PublicReleaseAllowed": False,
        "ProductionReady": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    path = Path(args.contract).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise SystemExit(f"contract must remain inside the repository: {error}")
    value = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(value), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
