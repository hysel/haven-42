#!/usr/bin/env python3
"""Validate the sanitized Ubuntu Radeon RX 6800 qualification result."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
RESULT_PATH = ROOT / "config/alpha-2-amd-rx6800-linux-qualification-result.json"
PRIVATE_NETWORK = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
)


def main() -> None:
    text = RESULT_PATH.read_text(encoding="utf-8")
    result = json.loads(text)

    assert result["kind"] == "haven42-alpha2-amd-rx6800-linux-qualification-result"
    assert result["status"] == "exact-profile-engineering-evidence-complete"
    assert result["environment"]["operatingSystem"] == "Ubuntu 26.04 LTS"
    assert result["environment"]["accelerator"] == "AMD Radeon RX 6800 non-XT 16 GB"
    assert result["environment"]["backend"] == "vulkan"
    assert result["runtime"]["provider"] == "ollama"
    assert result["runtime"]["version"] == "0.32.14"

    models = result["models"]
    ids = [model["modelId"] for model in models]
    assert len(ids) == len(set(ids)) == 13
    passed = [model for model in models if model["taskGate"] == "passed"]
    failed = [model for model in models if model["taskGate"] == "failed"]
    assert len(passed) == 10
    assert len(failed) == 3
    assert all(model["soak"] == "passed" for model in passed)
    assert all(model["soak"] == "not-run" for model in failed)
    assert all(len(model["manifestDigest"]) == 64 for model in models)

    counts = result["counts"]
    assert counts["exactArtifactsChecked"] == 13
    assert counts["taskCellsChecked"] == 39
    assert counts["taskCellsPassed"] + counts["taskCellsFailed"] == 39
    assert counts["thirtyMinuteSoaksPassed"] == 10
    assert counts["thirtyMinuteSoaksFailed"] == 0

    telemetry = result["telemetry"]
    assert telemetry["base"]["sampleCount"] == 2684
    assert telemetry["expansion"]["sampleCount"] == 1146
    assert telemetry["powerEvidenceStatus"] == (
        "telemetry-collected-standard-idle-baseline-not-established"
    )
    assert telemetry["eligibleForEndUserCostEstimate"] is False
    assert telemetry["includesCpuRamStorageCoolingDisplayOrPsuLosses"] is False

    evidence = (ROOT / result["evidence"]).read_text(encoding="utf-8")
    assert "standardized idle windows" in evidence
    assert "not wall power" in evidence
    assert "No automatic default or support" in evidence

    assert PRIVATE_NETWORK.search(text) is None
    assert result["containsPrivateMachineIdentity"] is False
    assert result["containsNetworkIdentity"] is False
    assert result["containsRawPromptsOrResponses"] is False
    assert result["automaticDefaultChangeAllowed"] is False
    assert result["automaticSelectionEvidenceAllowed"] is False
    assert result["automaticSupportChangeAllowed"] is False

    print("alpha2 Ubuntu RX 6800 qualification result checks passed")


if __name__ == "__main__":
    main()
