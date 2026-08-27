#!/usr/bin/env python3
"""Validate and summarize the fail-closed Alpha 2 promotion boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config" / "alpha-2-promotion-readiness.json"
RELEASE_CONTRACT = ROOT / "config" / "alpha-2-release-contract.json"
RUNTIME_COMPATIBILITY = ROOT / "config" / "alpha-2-runtime-compatibility.json"
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_STATUSES = {"satisfied", "candidate-required", "owner-required"}
EXPECTED_GATES = {
    "release-contract",
    "candidate-builders",
    "existing-regression-ci",
    "sanitized-model-hardware-evidence",
    "support-matrix-freeze",
    "managed-runtime-freeze",
    "exact-candidate-commit",
    "windows-candidate-packet",
    "linux-candidate-packet",
    "same-source-commit",
    "native-package-validation",
    "manual-accessibility-validation",
    "security-privacy-review",
    "supply-chain-evidence",
    "release-documentation",
    "hosted-candidate-ci",
    "publication-approval",
}
EXPECTED_PRIMARY_CELLS = [
    "windows-11-x64-nvidia",
    "ubuntu-26.04-x64-nvidia",
    "bazzite-44-x64-nvidia",
]
EXPECTED_LINUX_CPU_CELLS = [
    "arch-rolling",
    "bazzite-44",
    "cachyos-rolling",
    "debian-13",
    "fedora-44",
    "linux-mint-22.3",
    "pop-os-24.04",
    "ubuntu-24.04",
    "ubuntu-26.04",
]
EXPECTED_NON_BLOCKING = [
    "macos-packaging",
    "additional-gpu-and-memory-tiers",
    "windows-amd-and-intel-promotion",
    "linux-amd-and-intel-promotion",
    "coding-agent-surfaces",
    "image-audio-and-video-engines",
    "native-installer-and-updater",
    "code-signing",
]


class Alpha2PromotionError(ValueError):
    """Raised when the readiness record overstates evidence or authority."""


def _reference(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise Alpha2PromotionError("invalid-evidence-reference")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise Alpha2PromotionError("invalid-evidence-reference")
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise Alpha2PromotionError("invalid-evidence-reference") from error
    if not resolved.is_file():
        raise Alpha2PromotionError("missing-evidence-reference")
    return value


def _release_contract() -> dict[str, Any]:
    try:
        value = json.loads(RELEASE_CONTRACT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Alpha2PromotionError("release-contract-unreadable") from error
    if (
        value.get("contractId") != "haven42.alpha2.release"
        or value.get("version") != "0.4.0-alpha.2"
        or value.get("capabilities") != [
            "general.chat", "content.write", "content.summarize",
        ]
        or [item.get("id") for item in value.get("platforms", [])]
        != ["windows-x64", "linux-x64"]
        or value.get("releaseControls", {}).get("productionReady") is not False
        or value.get("releaseControls", {}).get("automaticPublicationAllowed") is not False
    ):
        raise Alpha2PromotionError("release-contract-mismatch")
    return value


def _admitted_runtime(version: str) -> dict[str, Any]:
    try:
        registry = json.loads(RUNTIME_COMPATIBILITY.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Alpha2PromotionError("runtime-registry-unreadable") from error
    if (
        registry.get("registryId") != "haven42.alpha2.inference-runtime-compatibility"
        or registry.get("defaultDecision") != "deny"
        or registry.get("policy", {}).get("crossEngineEvidenceInheritanceAllowed") is not False
    ):
        raise Alpha2PromotionError("runtime-registry-mismatch")
    matches = [item for item in registry.get("runtimes", []) if item.get("version") == version]
    if len(matches) != 1 or matches[0].get("admissionState") != "admitted":
        raise Alpha2PromotionError("managed-runtime-not-admitted")
    runtime = matches[0]
    artifacts = runtime.get("artifacts", [])
    platforms = {item.get("platform") for item in artifacts}
    if platforms != {"windows-x64", "linux-x64"}:
        raise Alpha2PromotionError("managed-runtime-platform-evidence-incomplete")
    for artifact in artifacts:
        if (
            not isinstance(artifact.get("byteLength"), int)
            or artifact["byteLength"] <= 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(artifact.get("sha256", "")))
            or not str(artifact.get("sourceUrl", "")).startswith(
                f"https://github.com/ollama/ollama/releases/download/v{version}/"
            )
        ):
            raise Alpha2PromotionError("managed-runtime-artifact-invalid")
    return runtime


def evaluate(value: Any) -> dict[str, Any]:
    expected = {
        "schemaVersion", "contractId", "releaseContract", "implementationStatus",
        "release", "scopeProposal", "managedRuntimeDecision", "gates", "authority",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise Alpha2PromotionError("invalid-contract-shape")
    if (
        value["schemaVersion"] != 1
        or value["contractId"] != "haven42.alpha2.promotion-readiness"
        or value["releaseContract"] != "config/alpha-2-release-contract.json"
        or value["implementationStatus"] != "release-scope-frozen-candidates-required"
    ):
        raise Alpha2PromotionError("invalid-contract-identity")

    release_contract = _release_contract()
    release = value["release"]
    if release != {
        "version": release_contract["version"],
        "audience": release_contract["audience"],
        "platforms": [item["id"] for item in release_contract["platforms"]],
        "capabilities": release_contract["capabilities"],
        "unsigned": release_contract["releaseControls"]["unsigned"],
        "productionReady": False,
    }:
        raise Alpha2PromotionError("release-scope-mismatch")

    scope = value["scopeProposal"]
    if not isinstance(scope, dict) or set(scope) != {
        "status", "primaryNativeValidationCells", "compatibilityCoverage",
        "nonBlockingExpansion", "changesSupportLabels", "changesAutomaticModelDefaults",
    }:
        raise Alpha2PromotionError("invalid-scope-proposal")
    coverage = scope["compatibilityCoverage"]
    if (
        scope["status"] != "approved"
        or scope["primaryNativeValidationCells"] != EXPECTED_PRIMARY_CELLS
        or not isinstance(coverage, dict)
        or coverage != {
            "mode": "cpu-only-package-and-desktop",
            "linuxOperatingSystemIds": EXPECTED_LINUX_CPU_CELLS,
            "promotionInheritanceAllowed": False,
        }
        or scope["nonBlockingExpansion"] != EXPECTED_NON_BLOCKING
        or scope["changesSupportLabels"] is not False
        or scope["changesAutomaticModelDefaults"] is not False
    ):
        raise Alpha2PromotionError("scope-authority-broadened")

    runtime = value["managedRuntimeDecision"]
    if runtime != {
        "status": "approved",
        "selectedProvider": "ollama",
        "selectedVersion": "0.32.14",
        "observedEvidenceVersions": ["0.32.5", "0.32.14", "0.32.15"],
        "crossVersionEvidenceInheritanceAllowed": False,
        "newerUnverifiedRuntimeMayBeUserSelectedWithApproval": True,
        "certifiedRollbackRequired": True,
    }:
        raise Alpha2PromotionError("runtime-decision-overstated")
    _admitted_runtime(runtime["selectedVersion"])

    gates = value["gates"]
    if not isinstance(gates, list) or len(gates) != len(EXPECTED_GATES):
        raise Alpha2PromotionError("invalid-gate-registry")
    seen: set[str] = set()
    statuses: dict[str, str] = {}
    counts = {status: 0 for status in sorted(ALLOWED_STATUSES)}
    blockers: list[dict[str, str]] = []
    for gate in gates:
        if not isinstance(gate, dict) or set(gate) != {"id", "status", "evidence"}:
            raise Alpha2PromotionError("invalid-gate-shape")
        gate_id = gate["id"]
        status = gate["status"]
        if (
            not isinstance(gate_id, str)
            or not SAFE_ID.fullmatch(gate_id)
            or gate_id not in EXPECTED_GATES
            or gate_id in seen
            or status not in ALLOWED_STATUSES
        ):
            raise Alpha2PromotionError("invalid-gate-registry")
        references = gate["evidence"]
        if not isinstance(references, list) or not references or len(references) > 5:
            raise Alpha2PromotionError("invalid-evidence-registry")
        safe_references = [_reference(reference) for reference in references]
        if len(safe_references) != len(set(safe_references)):
            raise Alpha2PromotionError("duplicate-evidence-reference")
        seen.add(gate_id)
        statuses[gate_id] = status
        counts[status] += 1
        if status != "satisfied":
            blockers.append({"id": gate_id, "status": status})
    if seen != EXPECTED_GATES:
        raise Alpha2PromotionError("invalid-gate-registry")
    if any(statuses[gate_id] != "satisfied" for gate_id in (
        "release-contract", "candidate-builders", "existing-regression-ci",
        "sanitized-model-hardware-evidence", "support-matrix-freeze",
        "managed-runtime-freeze",
    )):
        raise Alpha2PromotionError("foundation-evidence-regressed")
    if statuses["publication-approval"] != "owner-required":
        raise Alpha2PromotionError("owner-authority-mismatch")

    authority = value["authority"]
    expected_authority = {
        "scopeApproved", "managedRuntimeApproved", "candidateCommitSelected",
        "releaseCandidatesBuilt", "nativeValidationComplete", "readyForOwnerReview",
        "publicationAuthorized", "productionReady",
    }
    if not isinstance(authority, dict) or set(authority) != expected_authority:
        raise Alpha2PromotionError("invalid-authority-boundary")
    expected_current_authority = {
        "scopeApproved": True,
        "managedRuntimeApproved": True,
        "candidateCommitSelected": False,
        "releaseCandidatesBuilt": False,
        "nativeValidationComplete": False,
        "readyForOwnerReview": False,
        "publicationAuthorized": False,
        "productionReady": False,
    }
    if authority != expected_current_authority:
        raise Alpha2PromotionError("promotion-authority-must-remain-denied")

    return {
        "SchemaVersion": 1,
        "Mode": value["implementationStatus"],
        "Version": release["version"],
        "PublicationPlatforms": release["platforms"],
        "PrimaryNativeValidationCells": scope["primaryNativeValidationCells"],
        "LinuxCpuCompatibilityCellCount": len(coverage["linuxOperatingSystemIds"]),
        "ManagedRuntimeSelected": runtime["selectedVersion"],
        "GateCount": len(gates),
        "StatusCounts": counts,
        "RemainingGates": blockers,
        "ReadyForCandidateBuild": True,
        "ReadyForOwnerReview": False,
        "PublicationAllowed": False,
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
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"contract is unreadable: {error}")
    print(json.dumps(evaluate(value), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
