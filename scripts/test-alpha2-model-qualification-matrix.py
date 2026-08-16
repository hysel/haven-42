#!/usr/bin/env python3
"""Validate the cross-family model qualification matrix."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "config" / "alpha-2-model-qualification-matrix.json"
INVENTORY_PATH = ROOT / "config" / "alpha-2-model-version-inventory.json"


def canonical_sha256(value: dict) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    assert matrix["schemaVersion"] == 1
    assert matrix["status"] == "qualification-only-no-product-promotion"
    assert matrix["inventoryBinding"] == {
        "path": "config/alpha-2-model-version-inventory.json",
        "canonicalSha256": canonical_sha256(inventory),
    }
    assert matrix["provider"] == inventory["qualificationProvider"]
    assert [item["capability"] for item in matrix["taskChecks"]] == [
        "general.chat",
        "content.write",
        "content.summarize",
    ]
    assert all(item["samples"] == 3 for item in matrix["taskChecks"])

    inventory_candidates = {
        candidate["id"]
        for family in inventory["families"]
        for version in family["versions"]
        for candidate in version.get("candidates", [])
    }
    profile_records = {profile["id"]: profile for profile in matrix["profiles"]}
    profiles = set(profile_records)
    matrix_ids = [candidate["modelId"] for candidate in matrix["candidates"]]
    assert len(matrix_ids) == len(set(matrix_ids))
    assert set(matrix_ids) <= inventory_candidates
    for candidate in matrix["candidates"]:
        assert set(candidate["requiredProfiles"]) <= profiles
        if candidate["state"] == "ready-for-qualification":
            assert candidate["requiredProfiles"]
        else:
            assert candidate["state"].startswith(("deferred-", "failed-"))
            assert candidate["requiredProfiles"] == []

    candidate_profiles = {
        candidate["modelId"]: candidate["requiredProfiles"]
        for candidate in matrix["candidates"]
    }
    assert candidate_profiles["gemma4-e2b-qat"] == ["cpu-16gib", "cuda-16gib"]
    assert candidate_profiles["gemma4-e4b-qat"] == ["cpu-16gib", "cuda-16gib"]
    assert candidate_profiles["gemma4-12b-qat"] == ["cuda-16gib"]
    assert candidate_profiles["qwen36-27b-q4"] == [
        "cuda-32gib-system-16gib"
    ]
    assert candidate_profiles["qwen36-35b-a3b-q4"] == []
    assert candidate_profiles["muse-glimmer-30b-q4"] == []
    assert candidate_profiles["muse-glimmer-30b-mlx-nvfp4"] == []
    assert profile_records["cuda-32gib-system-16gib"] == {
        "id": "cuda-32gib-system-16gib",
        "backend": "cuda",
        "minimumSystemMemoryGiB": 31,
        "minimumUsableGpuMemoryGiB": 16,
    }
    for model_id in (
        "phi4-mini-38b-q4",
        "llama32-3b-q4",
        "ministral3-3b-q4",
        "ministral3-8b-q4",
    ):
        assert candidate_profiles[model_id] == ["cpu-16gib", "cuda-16gib"]

    muse_candidates = {
        candidate["modelId"]: candidate
        for candidate in matrix["candidates"]
        if candidate["modelId"].startswith("muse-glimmer-")
    }
    assert set(muse_candidates) == {
        "muse-glimmer-30b-q4",
        "muse-glimmer-30b-mlx-nvfp4",
    }
    assert muse_candidates["muse-glimmer-30b-q4"]["state"] == (
        "failed-needs-retest-ollama-0.32.9-task-contract"
    )
    assert muse_candidates["muse-glimmer-30b-mlx-nvfp4"]["state"] == (
        "deferred-owner-hardware-not-available"
    )
    for candidate in muse_candidates.values():
        plan = candidate["plannedTest"]
        assert plan["exactRuntimeVersionRequiredAtExecution"] is True
        assert plan["explicitOwnerStartPromptRequired"] is True
        assert plan["capabilityChecks"] == [
            "general.chat",
            "content.write",
            "content.summarize",
            "vision",
            "tools",
            "failure-recovery",
        ]
    assert muse_candidates["muse-glimmer-30b-q4"]["plannedTest"] == {
        "runtimeRequirementReference": "config/alpha-2-model-runtime-requirements.json#muse-glimmer-30b-q4",
        "negativeEvidenceReference": "examples/nvidia-v100-ollama0329-task-contract-retry.md",
        "minimumOllamaVersion": "0.32.8",
        "exactRuntimeVersionRequiredAtExecution": True,
        "admissionFloor": {
            "backend": "cuda",
            "minimumSystemMemoryGiB": 32,
            "minimumUsableGpuMemoryGiB": 24,
        },
        "capabilityChecks": [
            "general.chat",
            "content.write",
            "content.summarize",
            "vision",
            "tools",
            "failure-recovery",
        ],
        "explicitOwnerStartPromptRequired": True,
    }
    assert muse_candidates["muse-glimmer-30b-mlx-nvfp4"]["plannedTest"] == {
        "runtimeRequirementReference": "config/alpha-2-model-runtime-requirements.json#muse-glimmer-30b-mlx-nvfp4",
        "minimumOllamaVersion": "0.32.7",
        "exactRuntimeVersionRequiredAtExecution": True,
        "admissionFloor": {
            "backend": "mlx",
            "minimumUnifiedMemoryGiB": 48,
        },
        "capabilityChecks": [
            "general.chat",
            "content.write",
            "content.summarize",
            "vision",
            "tools",
            "failure-recovery",
        ],
        "explicitOwnerStartPromptRequired": True,
        "ownerDeferredUntilHardwareAvailable": True,
    }

    nemotron_candidates = {
        candidate["modelId"]: candidate
        for candidate in matrix["candidates"]
        if candidate["modelId"].startswith("nemotron35-lightning-")
    }
    assert set(nemotron_candidates) == {
        "nemotron35-lightning-30b-a3b-q4",
        "nemotron35-lightning-30b-a3b-q8",
        "nemotron35-lightning-30b-a3b-bf16",
        "nemotron35-lightning-30b-a3b-mlx-nvfp4",
        "nemotron35-lightning-30b-a3b-mlx-mxfp8",
        "nemotron35-lightning-30b-a3b-mlx-bf16",
    }
    assert all(
        candidate["requiredProfiles"] == []
        and candidate["state"].startswith("deferred-")
        and candidate["plannedTest"]["explicitOwnerStartPromptRequired"] is True
        and candidate["plannedTest"][
            "exactRuntimeCompatibilityRequiredAtExecution"
        ]
        is True
        for candidate in nemotron_candidates.values()
    )
    assert nemotron_candidates[
        "nemotron35-lightning-30b-a3b-q4"
    ]["plannedTest"]["admissionFloor"] == {
        "backend": "cuda",
        "minimumSystemMemoryGiB": 64,
        "minimumAggregateUsableGpuMemoryGiB": 48,
    }
    assert nemotron_candidates[
        "nemotron35-lightning-30b-a3b-q4"
    ]["plannedTest"]["minimumOllamaVersion"] == "0.32.9"
    for model_id in (
        "nemotron35-lightning-30b-a3b-q4",
        "nemotron35-lightning-30b-a3b-q8",
    ):
        candidate = nemotron_candidates[model_id]
        assert candidate["state"] == "deferred-partial-qualification-remaining-gates"
        assert candidate["plannedTest"]["completedEvidence"] == {
            "path": "examples/nvidia-v100-nemotron-validation.md",
            "profile": "ubuntu-24.04-dual-tesla-v100-32gib",
            "runtimeVersion": "0.32.9",
            "outcome": "chat-writing-summary-soak-passed",
            "automaticPromotionAllowed": False,
        }
        assert {
            "tools", "thinking", "failure-recovery", "context-8192",
            "context-32768", "exact-multi-gpu-distribution",
            "human-quality-review",
        } == set(candidate["plannedTest"]["remainingChecks"])
    assert nemotron_candidates[
        "nemotron35-lightning-30b-a3b-q4"
    ]["plannedTest"]["runtimeRequirementReference"] == (
        "config/alpha-2-model-runtime-requirements.json#nemotron35-lightning-30b-a3b-q4"
    )
    assert nemotron_candidates[
        "nemotron35-lightning-30b-a3b-q8"
    ]["plannedTest"]["minimumOllamaVersion"] == "0.32.9"
    assert nemotron_candidates[
        "nemotron35-lightning-30b-a3b-q8"
    ]["plannedTest"]["runtimeRequirementReference"] == (
        "config/alpha-2-model-runtime-requirements.json#nemotron35-lightning-30b-a3b-q8"
    )
    assert nemotron_candidates[
        "nemotron35-lightning-30b-a3b-q8"
    ]["plannedTest"]["admissionFloor"] == {
        "backend": "cuda",
        "minimumSystemMemoryGiB": 96,
        "minimumAggregateUsableGpuMemoryGiB": 56,
    }
    assert nemotron_candidates[
        "nemotron35-lightning-30b-a3b-bf16"
    ]["state"] == "deferred-outside-current-full-offload-envelope"
    for model_id in (
        "nemotron35-lightning-30b-a3b-mlx-nvfp4",
        "nemotron35-lightning-30b-a3b-mlx-mxfp8",
        "nemotron35-lightning-30b-a3b-mlx-bf16",
    ):
        assert nemotron_candidates[model_id]["state"] == (
            "deferred-owner-hardware-not-available"
        )
        assert nemotron_candidates[model_id]["plannedTest"][
            "ownerDeferredUntilHardwareAvailable"
        ] is True

    gate = matrix["soakGate"]
    assert gate == {
        "allTaskChecksMustPass": True,
        "durationMinutes": 30,
        "intervalSeconds": 120,
        "unloadAfterEverySampleRequired": True,
        "rawPromptsOrResponsesAllowed": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticDefaultChangeAllowed": False,
    }
    print("Alpha 2 cross-family qualification matrix passed fail-closed checks.")


if __name__ == "__main__":
    main()
