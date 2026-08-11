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
            assert candidate["state"].startswith("deferred-")
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
