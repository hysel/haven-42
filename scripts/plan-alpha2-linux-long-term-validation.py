#!/usr/bin/env python3
"""Validate and print the effect-free Alpha 2 Linux campaign plan.

This planner deliberately has no host inventory, SSH, Proxmox, subprocess,
socket, or download authority. A private deployment profile and a separately
reviewed controller are required before any machine can be contacted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT = ROOT / "config/alpha-2-linux-long-term-validation.json"
MODEL_POLICY_PATH = ROOT / "config/alpha-2-model-selection-policy.json"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SAFE_OS_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{0,79}$")
ALLOWED_CPU_LANES = {"required"}
ALLOWED_NVIDIA_LANES = {"promotion-candidate", "experimental"}
ALLOWED_CA_TRUST_FAMILIES = {"arch", "debian", "fedora"}
EXPECTED_CAPABILITIES = ["chat", "writing", "summarization"]
EXPECTED_STAGES = [
    "preflight",
    "cpu-smoke",
    "cpu-functional",
    "cpu-soak",
    "nvidia-smoke",
    "nvidia-functional",
    "nvidia-soak",
    "cleanup",
]
EXPECTED_CHECKS = {
    "package-integrity",
    "hardware-detection",
    "automatic-model-selection",
    "chat",
    "writing",
    "summarization",
    "stop-and-retry",
    "new-task-and-recall",
    "attachments",
    "metrics",
    "model-unload",
    "managed-process-cleanup",
    "loopback-only",
    "logs-and-support-report",
    "uninstall-separation",
    "privacy",
}
EXPECTED_SAFETY = {
    "networkContactAllowed": False,
    "machineChangesAllowed": False,
    "proxmoxControlAllowed": False,
    "gpuAssignmentAllowed": False,
    "shellExecutionAllowed": False,
    "maximumConcurrentGpuOwners": 1,
    "minimumLocalZfsFreePercent": 16,
    "rawPromptsOrResponsesAllowed": False,
    "machineIdentityInEvidenceAllowed": False,
    "resumeCheckpointRequired": True,
    "stopOnUnresolvedSecurityFinding": True,
    "stopOnUnresolvedPrivacyFinding": True,
}
EXPECTED_MODEL_CONSTRAINTS = {
    "exactDigestRequired": True,
    "providerVersionRequired": True,
    "rawPromptsOrResponsesAllowed": False,
    "unloadAfterEverySampleRequired": True,
    "protectedProviderDownloadsAllowed": False,
    "comparisonEvidenceMayPromote": False,
    "ownerApprovalRequiredForPromotion": True,
}


class ContractError(ValueError):
    """The campaign contract is unsafe or malformed."""


def load_contract(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot read campaign contract: {exc}") from exc
    validate_contract(value)
    return value


def _unique_safe_ids(values: Any, label: str) -> list[str]:
    if not isinstance(values, list) or not values:
        raise ContractError(f"{label} must be a non-empty array.")
    ids: list[str] = []
    for value in values:
        if not isinstance(value, dict) or not SAFE_ID.fullmatch(str(value.get("id", ""))):
            raise ContractError(f"Every {label} entry needs a safe id.")
        ids.append(value["id"])
    if len(ids) != len(set(ids)):
        raise ContractError(f"{label} ids must be unique.")
    return ids


def validate_contract(contract: Any) -> None:
    if (
        not isinstance(contract, dict)
        or set(contract) != {
            "campaignId", "release", "schemaVersion", "status", "capabilities",
            "targets", "stages", "requiredChecks", "modelValidation", "safety",
        }
        or contract.get("schemaVersion") != 1
    ):
        raise ContractError("Unsupported campaign schemaVersion.")
    if contract.get("campaignId") != "alpha2-linux-long-term":
        raise ContractError("Unexpected campaignId.")
    if contract.get("release") != "0.4.0-alpha.2":
        raise ContractError("The campaign must remain bound to Alpha 2.")
    if contract.get("status") != "review-only-no-machine-authority":
        raise ContractError("The public contract must remain review-only.")
    if contract.get("capabilities") != EXPECTED_CAPABILITIES:
        raise ContractError("Alpha 2 exposes only Chat, Writing, and Summarization.")

    targets = contract.get("targets")
    target_ids = _unique_safe_ids(targets, "target")
    if len(target_ids) != 9:
        raise ContractError("The Linux campaign requires exactly nine target profiles.")
    promotion_targets: set[str] = set()
    for target in targets:
        if set(target) != {
            "id", "distribution", "distributionId", "distributionVersion",
            "operatingSystemId", "caTrustFamily", "desktop", "cpuLane",
            "nvidiaLane",
        }:
            raise ContractError(f"Target {target['id']} has unexpected fields.")
        if not all(
            isinstance(target[field], str) and 1 <= len(target[field]) <= 80
            for field in ("distribution", "desktop")
        ):
            raise ContractError(f"Target {target['id']} has invalid display text.")
        distribution_id = target["distributionId"]
        distribution_version = target["distributionVersion"]
        normalized_id = {
            "linuxmint": "linux-mint", "pop": "pop-os",
        }.get(distribution_id, distribution_id)
        expected_os_id = f"{normalized_id}-{distribution_version}"
        if (
            distribution_id not in {
                "arch", "bazzite", "cachyos", "debian", "fedora",
                "linuxmint", "pop", "ubuntu",
            }
            or not SAFE_OS_ID.fullmatch(expected_os_id)
            or target["operatingSystemId"] != expected_os_id
        ):
            raise ContractError(
                f"Target {target['id']} has an inconsistent exact OS identity."
            )
        if target["caTrustFamily"] not in ALLOWED_CA_TRUST_FAMILIES:
            raise ContractError(f"Target {target['id']} has an unknown CA trust family.")
        if target["cpuLane"] not in ALLOWED_CPU_LANES:
            raise ContractError(f"Target {target['id']} must retain its CPU lane.")
        if target["nvidiaLane"] not in ALLOWED_NVIDIA_LANES:
            raise ContractError(f"Target {target['id']} has an invalid NVIDIA lane.")
        if target["nvidiaLane"] == "promotion-candidate":
            promotion_targets.add(target["id"])
    if promotion_targets != {"ubuntu-26-04-gnome", "bazzite-kde"}:
        raise ContractError("Only Ubuntu 26.04 and Bazzite may be NVIDIA promotion candidates.")

    stages = contract.get("stages")
    if _unique_safe_ids(stages, "stage") != EXPECTED_STAGES:
        raise ContractError("Campaign stages or ordering changed without review.")
    for stage in stages:
        if set(stage) != {"id", "requiresGpu", "maximumMinutes"}:
            raise ContractError(f"Stage {stage['id']} has unexpected fields.")
        if not isinstance(stage["requiresGpu"], bool):
            raise ContractError(f"Stage {stage['id']} requiresGpu must be Boolean.")
        minutes = stage["maximumMinutes"]
        if not isinstance(minutes, int) or isinstance(minutes, bool) or not 1 <= minutes <= 1440:
            raise ContractError(f"Stage {stage['id']} has an unsafe time limit.")
        if stage["requiresGpu"] != stage["id"].startswith("nvidia-"):
            raise ContractError(f"Stage {stage['id']} has an inconsistent GPU boundary.")

    checks = contract.get("requiredChecks")
    if not isinstance(checks, list) or len(checks) != len(set(checks)):
        raise ContractError("requiredChecks must be a unique array.")
    if set(checks) != EXPECTED_CHECKS:
        raise ContractError("The required Alpha 2 validation coverage changed.")
    validate_model_validation(contract.get("modelValidation"), targets)
    if contract.get("safety") != EXPECTED_SAFETY:
        raise ContractError("The review-only safety policy changed.")


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_model_validation(value: Any, targets: list[dict[str, Any]]) -> None:
    if not isinstance(value, dict) or set(value) != {
        "selectorPolicyId", "selectorPolicyCanonicalSha256", "repetitionsPerCell",
        "lanes", "deferredHardwareTiers", "constraints",
    }:
        raise ContractError("Model-validation fields do not match the reviewed schema.")
    try:
        policy = json.loads(MODEL_POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot read model-selection policy: {exc}") from exc
    if (
        value["selectorPolicyId"] != "haven42.alpha2.model-selection"
        or policy.get("policyId") != value["selectorPolicyId"]
        or policy.get("sourceCatalog", {}).get("path")
        != "config/alpha-2-model-catalog.json"
        or value["selectorPolicyCanonicalSha256"] != _canonical_sha256(policy)
        or value["repetitionsPerCell"] != 3
        or value["constraints"] != EXPECTED_MODEL_CONSTRAINTS
    ):
        raise ContractError("Model validation is not bound to the reviewed selector policy.")
    fit_ids = policy.get("fitLadder")
    comparisons = policy.get("comparisonCandidates")
    if (
        not isinstance(fit_ids, list)
        or not isinstance(comparisons, list)
        or any(not isinstance(item, dict) for item in comparisons)
    ):
        raise ContractError("The selector policy candidate sets are invalid.")
    comparison_ids = [item.get("id") for item in comparisons]
    expected_lanes = [
        {
            "id": "cpu-selection",
            "targetScope": "all-linux-targets",
            "requiresGpu": False,
            "evidenceUse": "automatic-candidate",
            "candidateIds": fit_ids[:1],
            "capabilities": ["general.chat", "content.write", "content.summarize"],
            "maximumMinutes": 45,
        },
        {
            "id": "cuda-selection",
            "targetScope": "nvidia-promotion-targets",
            "requiresGpu": True,
            "evidenceUse": "automatic-candidate",
            "candidateIds": fit_ids[:3],
            "capabilities": ["general.chat", "content.write", "content.summarize"],
            "maximumMinutes": 60,
        },
        {
            "id": "external-provider-comparison",
            "targetScope": "protected-external-provider",
            "requiresGpu": False,
            "evidenceUse": "comparison-only",
            "candidateIds": comparison_ids,
            "capabilities": ["general.chat", "content.write", "content.summarize"],
            "maximumMinutes": 90,
        },
    ]
    if value["lanes"] != expected_lanes:
        raise ContractError("Model-validation lanes changed without review.")
    if len({target["id"] for target in targets}) != 9:
        raise ContractError("Model validation requires the exact Linux target set.")
    try:
        catalog = json.loads(
            (ROOT / "config" / "alpha-2-model-catalog.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot read pinned model catalog: {exc}") from exc
    by_id = {item["id"]: item for item in catalog["models"]}
    expected_deferred = [
        {
            "modelId": model_id,
            "minimumSystemMemoryGiB": by_id[model_id]["minimumSystemMemoryGiB"],
            "minimumUsableGpuMemoryGiB": by_id[model_id]["minimumUsableGpuMemoryGiB"],
        }
        for model_id in fit_ids[3:]
    ]
    if value["deferredHardwareTiers"] != expected_deferred:
        raise ContractError("Deferred hardware tiers do not match the pinned catalog.")


def describe(contract: dict[str, Any]) -> dict[str, Any]:
    targets = contract["targets"]
    stages = contract["stages"]
    model_scope_counts = {
        "all-linux-targets": len(targets),
        "nvidia-promotion-targets": sum(
            target["nvidiaLane"] == "promotion-candidate" for target in targets
        ),
        "protected-external-provider": 1,
    }
    model_cells = sum(
        model_scope_counts[lane["targetScope"]]
        * len(lane["candidateIds"])
        * len(lane["capabilities"])
        for lane in contract["modelValidation"]["lanes"]
    )
    return {
        "campaignId": contract["campaignId"],
        "release": contract["release"],
        "status": contract["status"],
        "targetCount": len(targets),
        "cpuTaskCount": len(targets) * sum(not stage["requiresGpu"] for stage in stages),
        "nvidiaTaskCount": len(targets) * sum(stage["requiresGpu"] for stage in stages),
        "modelTaskCount": model_cells,
        "modelSampleCount": model_cells * contract["modelValidation"]["repetitionsPerCell"],
        "promotionCandidates": [
            target["id"]
            for target in targets
            if target["nvidiaLane"] == "promotion-candidate"
        ],
        "securityBoundary": "No network, machine, Proxmox, GPU, or shell authority.",
    }


def print_plan(contract: dict[str, Any]) -> None:
    summary = describe(contract)
    print(f"Campaign: {summary['campaignId']} ({summary['release']})")
    print(f"Status: {summary['status']}")
    print(f"Targets: {summary['targetCount']}")
    print(f"Planned CPU-stage cells: {summary['cpuTaskCount']}")
    print(f"Planned NVIDIA-stage cells: {summary['nvidiaTaskCount']}")
    print(f"Planned model-validation cells: {summary['modelTaskCount']}")
    print(f"Planned bounded model samples: {summary['modelSampleCount']}")
    print("NVIDIA promotion candidates: " + ", ".join(summary["promotionCandidates"]))
    print(f"Boundary: {summary['securityBoundary']}")
    print()
    print(f"{'TARGET':<28} {'CPU':<10} {'NVIDIA'}")
    for target in contract["targets"]:
        print(f"{target['id']:<28} {target['cpuLane']:<10} {target['nvidiaLane']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--json", action="store_true", help="Print a bounded JSON summary.")
    arguments = parser.parse_args()
    try:
        contract = load_contract(arguments.contract)
    except ContractError as exc:
        parser.error(str(exc))
    if arguments.json:
        print(json.dumps(describe(contract), indent=2, sort_keys=True))
    else:
        print_plan(contract)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
