#!/usr/bin/env python3
"""Validate the sanitized Ubuntu RTX 3060 qualification result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
RESULT_PATH = ROOT / "config/alpha-2-nvidia-rtx3060-linux-qualification-result.json"
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

    assert result["kind"] == "haven42-alpha2-nvidia-rtx3060-linux-qualification-result"
    assert result["status"] == "exact-profile-engineering-evidence-complete"
    assert result["environment"]["operatingSystem"] == "Ubuntu 26.04 LTS"
    assert result["environment"]["accelerator"] == "NVIDIA GeForce RTX 3060 12 GB"
    assert result["runtime"]["provider"] == "ollama"
    assert result["runtime"]["version"] == "0.32.14"
    assert result["runtime"]["releaseAdmission"] == "admitted"
    assert result["qualificationProfileId"] == "cuda-12gib-system-32gib"

    for name in ("inventory", "matrix"):
        binding = result["sourceBindings"][name]
        assert binding["canonicalSha256"] == canonical_sha256(load(ROOT / binding["path"]))

    models = result["modelsPassed"]
    assert len(models) == len(set(models)) == 19
    assert result["counts"] == {
        "exactArtifactsChecked": 19,
        "coreTaskGatePassed": 19,
        "coreTaskGateFailed": 0,
        "thirtyMinuteSoaksPassed": 19,
    }
    assert result["coreTaskGate"]["passed"] == 19
    assert result["coreTaskGate"]["failed"] == 0
    assert result["soak"]["passed"] == 19
    assert result["soak"]["failed"] == 0
    assert result["coreTaskGate"]["unloadRequiredAfterEverySample"] is True
    assert result["soak"]["unloadRequiredAfterEverySample"] is True

    inventory = load(ROOT / result["sourceBindings"]["inventory"]["path"])
    inventory_ids = {
        candidate["id"]
        for family in inventory["families"]
        for version in family["versions"]
        for candidate in version.get("candidates", [])
    }
    assert set(models) <= inventory_ids

    power = result["power"]
    assert power["telemetrySampleCount"] == 37443
    assert len(power["perModel"]) == 19
    assert set(power["perModel"]) == set(models)
    assert power["scope"] == "gpu-board-only"
    assert power["includesCpuRamStorageCoolingDisplayOrPsuLosses"] is False

    evidence = (ROOT / result["evidence"]).read_text(encoding="utf-8")
    assert "not wall power" in evidence
    assert "does not change" in evidence
    assert "separate Windows RTX 3060 campaign" in evidence

    assert PRIVATE_NETWORK.search(result_text) is None
    assert result["containsPrivateMachineIdentity"] is False
    assert result["containsNetworkIdentity"] is False
    assert result["containsRawPromptsOrResponses"] is False
    assert result["automaticDefaultChangeAllowed"] is False
    assert result["automaticSelectionEvidenceAllowed"] is False
    assert result["automaticSupportChangeAllowed"] is False

    print("alpha2 Ubuntu RTX 3060 qualification result checks passed")


if __name__ == "__main__":
    main()
