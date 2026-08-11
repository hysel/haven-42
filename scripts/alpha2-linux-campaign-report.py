#!/usr/bin/env python3
"""Build a sanitized Alpha 2 campaign report and selector evidence export."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT_PATH = ROOT / "scripts/alpha2-linux-campaign-checkpoint.py"
SPEC = importlib.util.spec_from_file_location("alpha2_report_checkpoint", CHECKPOINT_PATH)
CHECKPOINT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = CHECKPOINT
SPEC.loader.exec_module(CHECKPOINT)


def _group_key(task: dict[str, Any], evidence: dict[str, Any]) -> tuple[Any, ...]:
    return (
        task["target"],
        evidence["modelId"],
        evidence["manifestDigest"],
        evidence["platformFamily"],
        evidence["operatingSystemId"],
        evidence["architecture"],
        evidence["backendMode"],
        evidence["provider"],
        evidence["providerVersion"],
        evidence["selectorPolicyCanonicalSha256"],
        evidence["systemMemoryGiB"],
        evidence["usableGpuMemoryGiB"],
        evidence["automaticEvidenceCandidate"],
    )


def _evidence_id(key: tuple[Any, ...]) -> str:
    encoded = json.dumps(key, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "a2-" + hashlib.sha256(encoded).hexdigest()[:24]


def build_report(checkpoint: dict[str, Any]) -> dict[str, Any]:
    CHECKPOINT.validate_checkpoint(checkpoint)
    contract = CHECKPOINT.PLANNER.load_contract(CHECKPOINT.CONTRACT_PATH)
    capability_order = ["general.chat", "content.write", "content.summarize"]
    status_counts = {status: 0 for status in CHECKPOINT.TASK_STATUS}
    distribution_counts: dict[str, dict[str, int]] = {
        target["id"]: {status: 0 for status in CHECKPOINT.TASK_STATUS}
        for target in contract["targets"]
    }
    groups: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(
        lambda: {"capabilities": set(), "taskIds": []}
    )
    for task in checkpoint["tasks"]:
        status_counts[task["status"]] += 1
        if task["taskKind"] == "distribution-stage":
            distribution_counts[task["target"]][task["status"]] += 1
        if (
            task["taskKind"] == "model-validation"
            and task["status"] == "passed"
            and task["result"] is not None
            and task["result"]["evidence"] is not None
        ):
            evidence = task["result"]["evidence"]
            key = _group_key(task, evidence)
            groups[key]["capabilities"].add(evidence["capability"])
            groups[key]["taskIds"].append(task["id"])

    automatic: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    incomplete_automatic = 0
    for key, group in sorted(groups.items(), key=lambda item: str(item[0])):
        (
            target,
            model_id,
            digest,
            platform,
            operating_system,
            architecture,
            backend,
            provider,
            provider_version,
            selector_policy_sha,
            system_memory,
            gpu_memory,
            automatic_candidate,
        ) = key
        capabilities = [item for item in capability_order if item in group["capabilities"]]
        complete = capabilities == capability_order
        if automatic_candidate and complete:
            automatic.append(
                {
                    "evidenceId": _evidence_id(key),
                    "modelId": model_id,
                    "manifestDigest": digest,
                    "platformFamily": platform,
                    "operatingSystemId": operating_system,
                    "architecture": architecture,
                    "backendMode": backend,
                    "provider": provider,
                    "providerVersion": provider_version,
                    "selectorPolicyCanonicalSha256": selector_policy_sha,
                    "minimumTestedSystemMemoryGiB": system_memory,
                    "minimumTestedUsableGpuMemoryGiB": gpu_memory,
                    "capabilities": capabilities,
                    "status": "passed",
                }
            )
        elif automatic_candidate:
            incomplete_automatic += 1
        else:
            comparisons.append(
                {
                    "candidateId": model_id,
                    "manifestDigest": digest,
                    "platformFamily": platform,
                    "operatingSystemId": operating_system,
                    "architecture": architecture,
                    "backendMode": backend,
                    "provider": provider,
                    "providerVersion": provider_version,
                    "selectorPolicyCanonicalSha256": selector_policy_sha,
                    "systemMemoryGiB": system_memory,
                    "usableGpuMemoryGiB": gpu_memory,
                    "capabilitiesPassed": capabilities,
                    "allCapabilitiesPassed": complete,
                    "automaticPromotionAllowed": False,
                }
            )

    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-linux-campaign-report",
        "campaignId": checkpoint["campaignId"],
        "release": checkpoint["release"],
        "contractSha256": checkpoint["contractSha256"],
        "candidateSha256": checkpoint["candidateSha256"],
        "campaignStatus": checkpoint["status"],
        "taskCounts": status_counts,
        "distributionTaskCounts": distribution_counts,
        "automaticSelectionEvidence": automatic,
        "incompleteAutomaticEvidenceGroups": incomplete_automatic,
        "comparisonResults": comparisons,
        "deferredHardwareTiers": contract["modelValidation"]["deferredHardwareTiers"],
        "promotionDecision": "owner-review-required" if automatic else "no-new-evidence",
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        checkpoint = CHECKPOINT.load_checkpoint(args.checkpoint_root)
        print(json.dumps(build_report(checkpoint), indent=2, sort_keys=True))
    except CHECKPOINT.CheckpointError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
