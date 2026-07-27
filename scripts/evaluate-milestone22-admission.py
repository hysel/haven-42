#!/usr/bin/env python3
"""Validate and summarize the effect-free Milestone 22 admission ledger."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT = ROOT / "config" / "milestone22-admission-readiness-contract.json"
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_SCOPE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXPECTED_TOP_LEVEL = {
    "schemaVersion",
    "contractId",
    "implementationStatus",
    "description",
    "permittedStatuses",
    "authorityBoundary",
    "gates",
}
EXPECTED_AUTHORITY = {
    "scenarioClaimsAreEvidence",
    "rendererMayChangeGateState",
    "runtimeAuthorityGranted",
    "machineEffectsAllowed",
    "networkActivationAllowed",
    "platformCodeSigningAllowed",
    "notarizationAllowed",
    "publicationAllowed",
    "tauriOrRustAdmitted",
    "productionReadinessClaimAllowed",
}
EXPECTED_GATE = {
    "id",
    "status",
    "currentScope",
    "blocksUnsignedDevelopmentPackage",
    "currentReadOnlyRuntimeAdmitted",
    "requiresOwnerDecision",
    "satisfiedEvidence",
    "remainingBlockers",
}
EXPECTED_GATE_IDS = {
    "comparative-model-promotion",
    "read-only-validation-integration",
    "tauri-native-runtime",
    "production-package-promotion",
    "installer-runtime",
    "online-updater-activation",
    "executable-composition",
}
ALLOWED_ROOT_EVIDENCE = {
    "CODE-SIGNING-POLICY.md",
    "PRIVACY.md",
}


class AdmissionReadinessError(ValueError):
    """Raised when the admission ledger is unsafe or malformed."""


def _safe_reference(value: Any, root: Path) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise AdmissionReadinessError("invalid-evidence-reference")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise AdmissionReadinessError("invalid-evidence-reference")
    if (
        path.parts[0] not in {"config", "docs", "examples", "scripts"}
        and value not in ALLOWED_ROOT_EVIDENCE
    ):
        raise AdmissionReadinessError("invalid-evidence-reference")
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise AdmissionReadinessError("invalid-evidence-reference") from error
    if not resolved.is_file():
        raise AdmissionReadinessError("missing-evidence-reference")
    return value


def _bounded_ids(values: Any, error_code: str) -> list[str]:
    if not isinstance(values, list) or not values or len(values) > 20:
        raise AdmissionReadinessError(error_code)
    if any(not isinstance(value, str) or not SAFE_ID.fullmatch(value) for value in values):
        raise AdmissionReadinessError(error_code)
    if len(set(values)) != len(values):
        raise AdmissionReadinessError(error_code)
    return values


def evaluate(contract: Any, root: Path = ROOT) -> dict[str, Any]:
    if not isinstance(contract, dict) or set(contract) != EXPECTED_TOP_LEVEL:
        raise AdmissionReadinessError("invalid-contract-shape")
    if contract["schemaVersion"] != 1:
        raise AdmissionReadinessError("unsupported-schema")
    if contract["contractId"] != "haven42.milestone22-admission-readiness":
        raise AdmissionReadinessError("invalid-contract-id")
    if contract["implementationStatus"] != "offline-readiness-only":
        raise AdmissionReadinessError("invalid-implementation-status")
    if not isinstance(contract["description"], str) or not contract["description"].strip():
        raise AdmissionReadinessError("invalid-description")

    statuses = _bounded_ids(contract["permittedStatuses"], "invalid-status-registry")
    authority = contract["authorityBoundary"]
    if not isinstance(authority, dict) or set(authority) != EXPECTED_AUTHORITY:
        raise AdmissionReadinessError("invalid-authority-boundary")
    if any(value is not False for value in authority.values()):
        raise AdmissionReadinessError("authority-must-remain-denied")

    gates = contract["gates"]
    if not isinstance(gates, list) or len(gates) != len(EXPECTED_GATE_IDS):
        raise AdmissionReadinessError("invalid-gate-registry")
    gate_ids: set[str] = set()
    summaries: list[dict[str, Any]] = []
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != EXPECTED_GATE:
            raise AdmissionReadinessError("invalid-gate-shape")
        gate_id = gate["id"]
        if not isinstance(gate_id, str) or not SAFE_ID.fullmatch(gate_id) or gate_id in gate_ids:
            raise AdmissionReadinessError("invalid-or-duplicate-gate-id")
        gate_ids.add(gate_id)
        if gate["status"] not in statuses:
            raise AdmissionReadinessError("unknown-gate-status")
        if not isinstance(gate["currentScope"], str) or not SAFE_SCOPE.fullmatch(gate["currentScope"]):
            raise AdmissionReadinessError("invalid-current-scope")
        for field in (
            "blocksUnsignedDevelopmentPackage",
            "currentReadOnlyRuntimeAdmitted",
            "requiresOwnerDecision",
        ):
            if not isinstance(gate[field], bool):
                raise AdmissionReadinessError("invalid-gate-boolean")
        if gate["blocksUnsignedDevelopmentPackage"]:
            raise AdmissionReadinessError("development-package-must-remain-independent")
        if gate["currentReadOnlyRuntimeAdmitted"] and gate_id != "read-only-validation-integration":
            raise AdmissionReadinessError("unexpected-runtime-admission")
        if gate["status"] == "development-admitted" and not gate["currentReadOnlyRuntimeAdmitted"]:
            raise AdmissionReadinessError("development-admission-scope-mismatch")
        references = gate["satisfiedEvidence"]
        if not isinstance(references, list) or not references or len(references) > 10:
            raise AdmissionReadinessError("invalid-evidence-registry")
        safe_references = [_safe_reference(value, root) for value in references]
        if len(set(safe_references)) != len(safe_references):
            raise AdmissionReadinessError("duplicate-evidence-reference")
        blockers = _bounded_ids(gate["remainingBlockers"], "invalid-blocker-registry")
        summaries.append(
            {
                "id": gate_id,
                "status": gate["status"],
                "currentScope": gate["currentScope"],
                "currentReadOnlyRuntimeAdmitted": gate["currentReadOnlyRuntimeAdmitted"],
                "requiresOwnerDecision": gate["requiresOwnerDecision"],
                "remainingBlockers": blockers,
            }
        )

    if gate_ids != EXPECTED_GATE_IDS:
        raise AdmissionReadinessError("invalid-gate-registry")
    status_counts = {status: 0 for status in statuses}
    for gate in summaries:
        status_counts[gate["status"]] += 1
    return {
        "SchemaVersion": 1,
        "Mode": "offline-readiness-only",
        "GateCount": len(summaries),
        "StatusCounts": status_counts,
        "Gates": summaries,
        "UnsignedDevelopmentPackageBlocked": False,
        "RuntimeAuthorityGranted": False,
        "MachineEffectsAllowed": False,
        "NetworkActivationAllowed": False,
        "PlatformCodeSigningAllowed": False,
        "NotarizationAllowed": False,
        "PublicationAllowed": False,
        "TauriOrRustAdmitted": False,
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
    contract = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(contract), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
