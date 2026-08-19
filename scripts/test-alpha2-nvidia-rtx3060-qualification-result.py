#!/usr/bin/env python3
"""Validate the sanitized RTX 3060 qualification result and its bindings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
RESULT_PATH = ROOT / "config/alpha-2-nvidia-rtx3060-qualification-result.json"
PRIVATE_NETWORK = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def canonical_sha256(value: dict) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    result_text = RESULT_PATH.read_text(encoding="utf-8")
    result = json.loads(result_text)

    assert result["kind"] == "haven42-alpha2-nvidia-rtx3060-qualification-result"
    assert result["status"] == "exact-profile-engineering-evidence-complete"
    assert result["runtime"] == {
        "provider": "ollama",
        "version": "0.32.14",
        "releaseAdmission": "admitted",
    }
    assert result["qualificationProfileId"] == "cuda-12gib-system-32gib"

    for name in ("inventory", "matrix"):
        binding = result["sourceBindings"][name]
        source = load(ROOT / binding["path"])
        assert binding["canonicalSha256"] == canonical_sha256(source)

    runtime = load(ROOT / result["sourceBindings"]["runtimeCompatibility"])
    runtime_candidates = [
        item
        for item in runtime["runtimes"]
        if item.get("version") == "0.32.14"
    ]
    assert len(runtime_candidates) == 1
    assert (
        runtime_candidates[0]["admissionState"]
        == "admitted"
    )

    passed = set(result["coreTaskGate"]["passed"])
    failed = set(result["coreTaskGate"]["failed"])
    soaked = set(result["soak"]["passed"])
    assert len(passed) == result["counts"]["coreTaskGatePassed"] == 14
    assert len(failed) == result["counts"]["coreTaskGateFailed"] == 5
    assert passed.isdisjoint(failed)
    assert soaked == passed
    assert result["soak"]["failed"] == []
    assert result["counts"]["exactArtifactsChecked"] == len(passed | failed) == 19

    inventory = load(ROOT / result["sourceBindings"]["inventory"]["path"])
    inventory_ids = {
        candidate["id"]
        for family in inventory["families"]
        for version in family["versions"]
        for candidate in version.get("candidates", [])
    }
    assert passed | failed <= inventory_ids

    assert result["codingAgent"]["fullWorkflowPassed"] == ["granite41-8b-q4"]
    assert result["codingAgent"]["codingRecommendationAllowed"] is False
    assert result["extendedCapabilities"]["minicpm-v46-1b-q4"]["vision"] == "failed"

    power = result["power"]
    assert power["telemetrySampleCount"] == 39327
    assert power["idleSampleCount"] == 596
    assert power["scope"] == "gpu-board-only"
    assert power["includesCpuRamStorageCoolingDisplayOrPsuLosses"] is False

    evidence_path = ROOT / result["evidence"]
    evidence = evidence_path.read_text(encoding="utf-8")
    assert "not wall power" in evidence
    assert "No coding-agent recommendation was granted" in evidence
    assert "does not make" in evidence

    assert PRIVATE_NETWORK.search(result_text) is None
    assert result["containsPrivateMachineIdentity"] is False
    assert result["containsNetworkIdentity"] is False
    assert result["containsRawPromptsOrResponses"] is False
    assert result["automaticDefaultChangeAllowed"] is False
    assert result["automaticSelectionEvidenceAllowed"] is False
    assert result["automaticSupportChangeAllowed"] is False

    print("alpha2 RTX 3060 qualification result checks passed")


if __name__ == "__main__":
    main()
