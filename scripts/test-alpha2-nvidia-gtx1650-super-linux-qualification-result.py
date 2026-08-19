#!/usr/bin/env python3
"""Validate the sanitized Ubuntu GTX 1650 Super qualification result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
RESULT_PATH = ROOT / "config/alpha-2-nvidia-gtx1650-super-linux-qualification-result.json"
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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    result_text = RESULT_PATH.read_text(encoding="utf-8")
    result = json.loads(result_text)

    assert result["kind"] == "haven42-alpha2-nvidia-gtx1650-super-linux-qualification-result"
    assert result["status"] == "exact-profile-engineering-evidence-complete"
    assert result["environment"]["operatingSystem"] == "Ubuntu 26.04 LTS"
    assert result["environment"]["accelerator"] == "NVIDIA GeForce GTX 1650 Super 4 GB"
    assert result["runtime"]["version"] == "0.32.14"
    assert result["qualificationProfileId"] == "cuda-4gib-system-16gib"

    for name in ("inventory", "matrix"):
        binding = result["sourceBindings"][name]
        assert binding["canonicalSha256"] == canonical_sha256(load(ROOT / binding["path"]))
    for name in ("coreValidator", "soakValidator", "orchestrator"):
        binding = result["sourceBindings"][name]
        assert binding["sha256"] == file_sha256(ROOT / binding["path"])

    passed = result["modelsPassed"]
    stopped = result["modelsStoppedAtResidencyGate"]
    assert len(passed) == len(set(passed)) == 5
    assert len(stopped) == len(set(stopped)) == 3
    assert set(passed).isdisjoint(stopped)
    assert result["counts"] == {
        "exactArtifactsChecked": 8,
        "coreTaskGatePassed": 5,
        "coreTaskGateFailed": 3,
        "thirtyMinuteSoaksPassed": 5,
        "thirtyMinuteSoaksFailed": 0,
    }
    assert result["coreTaskGate"]["failureReason"] == "cuda-full-residency-not-observed"
    assert result["coreTaskGate"]["unloadRequiredAfterEverySample"] is True
    assert result["soak"]["unloadRequiredAfterEverySample"] is True

    power = result["power"]
    assert power["telemetrySampleCount"] == 9879
    assert set(power["perModel"]) == set(passed)
    assert power["scope"] == "gpu-board-only"
    assert power["includesCpuRamStorageCoolingDisplayOrPsuLosses"] is False

    evidence = (ROOT / result["evidence"]).read_text(encoding="utf-8")
    assert "not wall power" in evidence
    assert "does not change" in evidence
    assert "4 GB hardware-fit boundary" in evidence

    assert PRIVATE_NETWORK.search(result_text) is None
    assert result["containsPrivateMachineIdentity"] is False
    assert result["containsNetworkIdentity"] is False
    assert result["containsRawPromptsOrResponses"] is False
    assert result["automaticDefaultChangeAllowed"] is False
    assert result["automaticSelectionEvidenceAllowed"] is False
    assert result["automaticSupportChangeAllowed"] is False

    print("alpha2 Ubuntu GTX 1650 Super qualification result checks passed")


if __name__ == "__main__":
    main()
