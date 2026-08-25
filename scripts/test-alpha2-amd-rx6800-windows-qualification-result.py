#!/usr/bin/env python3
"""Validate sanitized Windows Radeon RX 6800 qualification evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent.parent
RESULT_PATH = ROOT / "config/alpha-2-amd-rx6800-windows-qualification-result.json"
REPORT_PATH = ROOT / "examples/amd-rx6800-windows-model-qualification.md"
CATALOG_PATH = ROOT / "config/evidence-catalog.tsv"
INVENTORY_PATH = ROOT / "config/alpha-2-model-version-inventory.json"
PRIVATE_NETWORK = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
)
PRIVATE_PATH = re.compile(r"(?i)(?:\b[A-Z]:\\Users\\|/(?:home|Users)/[^/\s]+)")


def inventory_digests() -> dict[str, str]:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    output: dict[str, str] = {}
    for family in inventory["families"]:
        for version in family["versions"]:
            for candidate in version.get("candidates", []):
                output[candidate["id"]] = candidate["manifestDigest"]
    return output


def main() -> None:
    text = RESULT_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")
    result = json.loads(text)

    assert result["schemaVersion"] == 1
    assert result["kind"] == "haven42-alpha2-amd-rx6800-windows-qualification-result"
    assert result["status"] == "exact-profile-engineering-evidence-complete"
    assert result["environment"]["operatingSystem"] == "Windows 11"
    assert result["environment"]["accelerator"] == "AMD Radeon RX 6800 non-XT 16 GB"
    assert result["environment"]["backend"] == "rocm"
    assert result["environment"]["graphicsDriverVersion"] == (
        "not-captured-in-sanitized-campaign-evidence"
    )
    assert result["runtime"] == {
        "provider": "ollama",
        "version": "0.32.14",
        "releaseAdmission": "qualification-only",
    }

    models = result["models"]
    assert len(models) == 19
    assert len({model["modelId"] for model in models}) == 19
    digests = inventory_digests()
    for model in models:
        assert model["manifestDigest"] == digests[model["modelId"]]
        assert model["coreTaskGate"] == "passed"
        assert model["coreSamplesPassed"] == 27
        assert model["soak"] == "passed"
        assert model["soakDurationSeconds"] >= 1800
        assert model["soakSamplesPassed"] == model["soakUnloadPasses"]
        assert model["averageTokensPerSecond"] > 0
        assert model["peakGpuMemoryBytes"] > 0

    counts = result["counts"]
    assert counts["sourceFilesPrivacyScanned"] == 429
    assert counts["exactArtifactsChecked"] == 19
    assert counts["coreCapabilityCellsPassed"] == 57
    assert counts["coreSamplesPassed"] == 513
    assert counts["thirtyMinuteSoaksPassed"] == 19
    assert counts["soakSamplesPassed"] == counts["soakUnloadPasses"] == 699
    assert counts["aggregateSoakDurationSeconds"] >= 19 * 1800

    privacy = result["privacyAudit"]
    assert privacy["filesScanned"] == 429
    assert privacy["sourceBytesScanned"] == 58062183
    assert "sourceTreeSha256" not in privacy
    assert privacy["sourceTreatment"] == "private-untrusted-not-published"
    assert privacy["sanitizationMethod"] == "allow-listed-derived-fields-only"
    assert privacy["rawTelemetryRetainedInRepository"] is False
    assert privacy["sensitiveFindingCounts"]["raw-hardware-inventory-telemetry-file"] == 1
    assert privacy["sensitiveFindingCounts"]["binary-intermediate-file"] == 1

    raw = result["power"]["rawTelemetry"]
    assert set(raw) == {"bytes", "sha256", "committed"}
    assert raw["bytes"] == 57595855
    assert raw["sha256"] == "36607f7d608efbf6ab4efabf55abd6d0e6c6e6a3223356fa1ad0a16823ee7583"
    assert raw["committed"] is False
    assert result["power"]["perModelAttributionAvailable"] is False
    assert result["power"]["eligibleForEndUserCostEstimate"] is False
    assert result["power"]["includesCpuRamStorageCoolingDisplayOrPsuLosses"] is False

    assert "All 19 exact artifacts passed" in report
    assert "not wall power" in " ".join(report.split())
    assert "Size: 57,595,855 bytes" in report
    assert raw["sha256"] in report
    assert "graphics-driver version was not captured" in report

    with CATALOG_PATH.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    matches = [
        row for row in rows
        if row["subject"] == "Windows AMD Radeon RX 6800 16 GB nineteen-model qualification"
    ]
    assert len(matches) == 1
    assert matches[0]["status"] == "partial-pass"
    assert matches[0]["evidence"] == "examples/amd-rx6800-windows-model-qualification.md"

    combined = text + "\n" + report
    assert PRIVATE_NETWORK.search(combined) is None
    assert PRIVATE_PATH.search(combined) is None
    assert result["containsPrivateMachineIdentity"] is False
    assert result["containsNetworkIdentity"] is False
    assert result["containsRawPromptsOrResponses"] is False
    assert result["automaticDefaultChangeAllowed"] is False
    assert result["automaticSelectionEvidenceAllowed"] is False
    assert result["automaticSupportChangeAllowed"] is False

    tracked = subprocess.run(
        ["git", "ls-files", "dist/local-review/rx6800-windows"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tracked == "", "raw RX 6800 local-review files must not be committed"
    print("alpha2 Windows RX 6800 qualification result checks passed")


if __name__ == "__main__":
    main()
