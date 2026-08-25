#!/usr/bin/env python3
"""Build sanitized RX 6800 Windows qualification evidence from local review data.

The source directory is always treated as private and untrusted.  This program scans
every source file, but publishes only allow-listed scalar measurements, model IDs,
and digests.  It never copies raw telemetry, prompts, responses, paths, host names,
or device identifiers into repository evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
RESULT = ROOT / "config/alpha-2-amd-rx6800-windows-qualification-result.json"
REPORT = ROOT / "examples/amd-rx6800-windows-model-qualification.md"
CATALOG = ROOT / "config/evidence-catalog.tsv"
INVENTORY = ROOT / "config/alpha-2-model-version-inventory.json"
CATALOG_SUBJECT = "Windows AMD Radeon RX 6800 16 GB nineteen-model qualification"
EXPECTED_MODELS = 19
EXPECTED_SOURCE_FILES = 429


SENSITIVE_PATTERNS = {
    "private-network-address": re.compile(
        rb"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|"
        rb"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
    ),
    "absolute-windows-path": re.compile(rb"(?i)\b[A-Z]:\\(?:Users|Windows|ProgramData|Temp)\\"),
    "user-profile-path": re.compile(rb"(?i)\\Users\\[^\\\r\n\t,\"]+"),
    "posix-home-path": re.compile(rb"/(?:home|Users)/[^/\r\n\t,\"]+"),
    "email-address": re.compile(rb"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    "ssh-key-material": re.compile(rb"(?:ssh-(?:ed25519|rsa)|BEGIN (?:OPENSSH|RSA) PRIVATE KEY)"),
    "mac-address": re.compile(rb"(?i)\b(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}\b"),
    "uuid": re.compile(
        rb"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
    ),
    "lab-host-label": re.compile(
        rb"(?i)\bhaven42(?:intel|winintel|ubuntu|localai|pbs|server)[a-z0-9-]*\b"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = data.decode("utf-16")
    else:
        text = data.decode("utf-8-sig")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def inventory_candidates() -> dict[str, dict[str, Any]]:
    inventory = read_json(INVENTORY)
    candidates: dict[str, dict[str, Any]] = {}
    for family in inventory["families"]:
        for version in family["versions"]:
            for candidate in version.get("candidates", []):
                candidates[candidate["id"]] = candidate
    return candidates


def scan_source(source: Path) -> dict[str, Any]:
    files = sorted(path for path in source.rglob("*") if path.is_file())
    if len(files) != EXPECTED_SOURCE_FILES:
        raise ValueError(f"source file count changed: expected {EXPECTED_SOURCE_FILES}, got {len(files)}")

    findings: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    total_bytes = 0
    for path in files:
        size = path.stat().st_size
        total_bytes += size
        extension_counts[path.suffix.lower() or "[none]"] += 1

        # Every file is scanned. Binary data is searched byte-for-byte; source text is
        # never emitted. Counts are evidence that raw material was treated as private.
        data = path.read_bytes()
        for category, pattern in SENSITIVE_PATTERNS.items():
            findings[category] += len(pattern.findall(data))

    # HWiNFO exports a wide hardware inventory alongside metrics. Treat the entire
    # telemetry source as machine-identifying even when a generic pattern does not
    # recognize a vendor-specific serial format. The file is never copied.
    findings["raw-hardware-inventory-telemetry-file"] += 1
    findings["binary-intermediate-file"] += sum(path.suffix.lower() == ".pyc" for path in files)

    telemetry = source / "telemetry/Haven42-RX6800-HWiNFO.CSV"
    telemetry_summary = source / "telemetry/hwinfo-summary.json"
    if not telemetry.is_file() or not telemetry_summary.is_file():
        raise ValueError("required telemetry source or summary is missing")
    summary = read_json(telemetry_summary)
    if summary["sourceBytes"] != telemetry.stat().st_size:
        raise ValueError("telemetry byte count does not match its summary")
    if summary["sha256"].lower() != sha256(telemetry):
        raise ValueError("telemetry SHA-256 does not match its summary")

    return {
        "filesScanned": len(files),
        "sourceBytesScanned": total_bytes,
        "fileTypes": dict(sorted(extension_counts.items())),
        "sensitiveFindingCounts": dict(sorted(findings.items())),
        "sourceTreatment": "private-untrusted-not-published",
        "sanitizationMethod": "allow-listed-derived-fields-only",
        "rawTelemetryRetainedInRepository": False,
    }


def load_models(source: Path) -> list[dict[str, Any]]:
    core_rows = read_tsv(source / "results/core/summary.tsv")
    soak_rows = read_tsv(source / "results/soak/summary.tsv")
    core = {row["model_id"]: row for row in core_rows}
    soak = {row["model_id"]: row for row in soak_rows}
    if len(core) != EXPECTED_MODELS or len(soak) != EXPECTED_MODELS or set(core) != set(soak):
        raise ValueError("core and soak summaries do not contain the same 19 models")
    if any(row["status"] != "passed" for row in core_rows + soak_rows):
        raise ValueError("a core or soak summary contains a non-passing outcome")

    inventory = inventory_candidates()
    models: list[dict[str, Any]] = []
    for model_id in core:
        candidate = inventory.get(model_id)
        if candidate is None:
            raise ValueError(f"model is absent from the pinned inventory: {model_id}")

        core_dir = source / "results/core" / model_id
        task_files = sorted(
            path for path in core_dir.glob("*.json") if path.name != "download.json"
        )
        if len(task_files) != 9:
            raise ValueError(f"expected nine core samples for {model_id}")
        task_records = [read_json(path) for path in task_files]
        if any(record.get("outcome") != "passed" for record in task_records):
            raise ValueError(f"non-passing core record for {model_id}")

        soak_record = read_json(source / "results/soak" / f"{model_id}.json")
        if soak_record.get("outcome") != "passed":
            raise ValueError(f"non-passing soak record for {model_id}")
        manifest = soak_record["evidence"]["manifestDigest"]
        if manifest != candidate["manifestDigest"]:
            raise ValueError(f"manifest digest mismatch for {model_id}")
        if any(record["evidence"]["manifestDigest"] != manifest for record in task_records):
            raise ValueError(f"core manifest digest mismatch for {model_id}")

        capability_counts = Counter(record["evidence"]["capability"] for record in task_records)
        if capability_counts != {
            "general.chat": 3,
            "content.write": 3,
            "content.summarize": 3,
        }:
            raise ValueError(f"unexpected core capability coverage for {model_id}")

        models.append(
            {
                "modelId": model_id,
                "model": candidate["model"],
                "manifestDigest": manifest,
                "quantization": candidate["quantization"],
                "coreTaskGate": "passed",
                "coreSamplesPassed": sum(record["metrics"]["samplesPassed"] for record in task_records),
                "soak": "passed",
                "soakDurationSeconds": round(float(soak_record["durationSeconds"]), 3),
                "soakSamplesPassed": soak_record["metrics"]["samplesPassed"],
                "soakUnloadPasses": soak_record["metrics"]["unloadPasses"],
                "averageTokensPerSecond": soak_record["metrics"]["averageTokensPerSecond"],
                "peakGpuMemoryBytes": soak_record["metrics"]["peakGpuMemoryBytes"],
            }
        )
    return models


def build_result(source: Path) -> dict[str, Any]:
    scan = scan_source(source)
    models = load_models(source)
    campaign = read_json(source / "campaign-status.json")
    telemetry = read_json(source / "telemetry/hwinfo-summary.json")
    if campaign.get("status") != "passed" or campaign.get("complete") is not True:
        raise ValueError("campaign status is not complete and passing")
    if campaign.get("totalModels") != EXPECTED_MODELS or campaign.get("failedModels") != 0:
        raise ValueError("campaign aggregate does not match the 19-model summaries")
    if telemetry["qualificationSoak"]["modelsPassed"] != EXPECTED_MODELS:
        raise ValueError("telemetry aggregate does not match the soak summary")

    core_samples = sum(model["coreSamplesPassed"] for model in models)
    soak_samples = sum(model["soakSamplesPassed"] for model in models)
    unloads = sum(model["soakUnloadPasses"] for model in models)
    soak_seconds = round(sum(model["soakDurationSeconds"] for model in models), 3)
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-amd-rx6800-windows-qualification-result",
        "release": "0.4.0-alpha.2",
        "observedThroughUtc": campaign["updatedAtUtc"],
        "status": "exact-profile-engineering-evidence-complete",
        "environment": {
            "operatingSystem": "Windows 11",
            "architecture": "x64",
            "accelerator": "AMD Radeon RX 6800 non-XT 16 GB",
            "backend": "rocm",
            "graphicsDriverVersion": "not-captured-in-sanitized-campaign-evidence",
            "systemMemoryGiB": 127.0,
            "usableGpuMemoryGiB": 16.0,
        },
        "runtime": {
            "provider": "ollama",
            "version": "0.32.14",
            "releaseAdmission": "qualification-only",
        },
        "qualificationProfileId": "rocm-16gib-system-128gib-windows",
        "counts": {
            "sourceFilesPrivacyScanned": scan["filesScanned"],
            "exactArtifactsChecked": len(models),
            "coreCapabilityCellsPassed": len(models) * 3,
            "coreSamplesPassed": core_samples,
            "thirtyMinuteSoaksPassed": len(models),
            "soakSamplesPassed": soak_samples,
            "soakUnloadPasses": unloads,
            "aggregateSoakDurationSeconds": soak_seconds,
        },
        "models": models,
        "power": {
            "telemetrySource": "HWiNFO64",
            "scope": "gpu-asic-sensor-only",
            "rawTelemetry": {
                "bytes": telemetry["sourceBytes"],
                "sha256": telemetry["sha256"].lower(),
                "committed": False,
            },
            "telemetryRows": telemetry["recording"]["dataRows"],
            "soakRows": telemetry["qualificationSoak"]["matchingTelemetryRows"],
            "soakCovered": telemetry["qualificationSoak"]["coveredByTelemetry"],
            "activeSampleDefinition": telemetry["method"]["activeSampleDefinition"],
            "activeSamples": telemetry["method"]["activeSamples"],
            "allSoakSamplesAverageWatts": telemetry["metricsDuringSoak"]["gpuAsicPowerWatts"]["allSampleAverage"],
            "activeSamplesAverageWatts": telemetry["metricsDuringSoak"]["gpuAsicPowerWatts"]["activeSampleAverage"],
            "minimumWatts": telemetry["metricsDuringSoak"]["gpuAsicPowerWatts"]["minimum"],
            "maximumWatts": telemetry["metricsDuringSoak"]["gpuAsicPowerWatts"]["maximum"],
            "averageGpuTemperatureCelsius": telemetry["metricsDuringSoak"]["gpuTemperatureCelsius"]["average"],
            "maximumGpuTemperatureCelsius": telemetry["metricsDuringSoak"]["gpuTemperatureCelsius"]["maximum"],
            "maximumGpuHotSpotTemperatureCelsius": telemetry["metricsDuringSoak"]["gpuHotSpotTemperatureCelsius"]["maximum"],
            "perModelAttributionAvailable": False,
            "eligibleForEndUserCostEstimate": False,
            "includesCpuRamStorageCoolingDisplayOrPsuLosses": False,
        },
        "privacyAudit": scan,
        "limitations": [
            "The Windows graphics-driver version was not captured in the sanitized campaign evidence and is left explicit rather than inferred.",
            "Raw HWiNFO telemetry contains machine-specific device metadata and is excluded from the repository.",
            "HWiNFO GPU memory readings were physically impossible and were excluded.",
            "Power is an aggregate GPU ASIC sensor summary; it is not attributed per model and is not wall power.",
        ],
        "evidence": "examples/amd-rx6800-windows-model-qualification.md",
        "containsPrivateMachineIdentity": False,
        "containsNetworkIdentity": False,
        "containsRawPromptsOrResponses": False,
        "automaticDefaultChangeAllowed": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticSupportChangeAllowed": False,
    }


def render_report(result: dict[str, Any]) -> str:
    counts = result["counts"]
    power = result["power"]
    rows = []
    for model in result["models"]:
        rows.append(
            f"| {model['model']} | `{model['manifestDigest']}` | Passed, {model['coreSamplesPassed']} samples | "
            f"Passed, {model['soakSamplesPassed']} samples | {model['averageTokensPerSecond']:.3f} tok/s | "
            f"{model['peakGpuMemoryBytes'] / (1024 ** 3):.2f} GiB |"
        )
    return f"""# AMD Radeon RX 6800 16 GB Windows model qualification

## What this evidence answers

On August 22–23, 2026, Haven 42 tested 19 exact local model artifacts on one
Windows 11 computer with an AMD Radeon RX 6800 non-XT 16 GB. The run used an
isolated Ollama 0.32.14 qualification runtime with its ROCm backend.

This evidence applies only to that exact operating-system, runtime, hardware,
and model-digest set. The graphics-driver version was not captured in the
sanitized campaign evidence, so it is reported as unknown rather than inferred.
No automatic default, support label, managed-runtime choice, or another
hardware or operating-system result changes because of this run.

## Result at a glance

- All 19 exact artifacts passed Chat, Writing, and Summarization: {counts['coreSamplesPassed']} bounded core samples in total.
- All 19 artifacts passed independent 30-minute reliability soaks: {counts['soakSamplesPassed']} bounded soak samples and {counts['soakUnloadPasses']} unload proofs.
- The aggregate measured soak duration was {counts['aggregateSoakDurationSeconds'] / 3600:.2f} hours.
- Every one of the {counts['sourceFilesPrivacyScanned']} local review files was scanned. None of those raw files is published.
- Raw HWiNFO telemetry is represented only by its byte count and SHA-256 digest.

## Model outcomes

| Exact artifact | Manifest SHA-256 | Core gate | 30-minute soak | Average generation | Peak GPU memory |
| --- | --- | --- | --- | ---: | ---: |
{chr(10).join(rows)}

Every core and soak result above was cross-checked against the campaign summaries,
the pinned model inventory, and the per-model result records. A passing synthetic
soak is reliability evidence for this profile; it is not a human quality score or a
coding-agent recommendation.

## Filtered graphics-board power summary

HWiNFO recorded {power['telemetryRows']:,} rows, including {power['soakRows']:,}
rows covering the qualification soak. Across all soak rows, the GPU ASIC sensor
averaged {power['allSoakSamplesAverageWatts']:.3f} W. The {power['activeSamples']}
rows meeting the fixed active-sample rule averaged {power['activeSamplesAverageWatts']:.3f} W.
Observed GPU ASIC power ranged from {power['minimumWatts']:.1f} W to
{power['maximumWatts']:.1f} W. Average GPU temperature was
{power['averageGpuTemperatureCelsius']:.2f} C; the highest GPU temperature was
{power['maximumGpuTemperatureCelsius']:.1f} C and the highest hot-spot temperature
was {power['maximumGpuHotSpotTemperatureCelsius']:.1f} C.

These are aggregate GPU ASIC sensor readings, not per-model readings and not wall
power. CPU, memory, storage, cooling, display, and power-supply losses are excluded.
The source memory-usage column was physically impossible and was excluded. This
power evidence is therefore not eligible for an end-user electricity-cost estimate.

## Privacy and provenance

The private source set contained {result['privacyAudit']['filesScanned']} files and
{result['privacyAudit']['sourceBytesScanned']:,} bytes. The sanitizer scanned every
file and produced this report through an allow list: only fixed public profile labels,
validated model IDs and digests, pass counts, and aggregate measurements could enter
the published result. Raw prompts, responses, local paths, network identities, host
names, user names, and device identifiers were not copied.

The raw telemetry file is not committed. Its provenance is retained only as:

- Size: {power['rawTelemetry']['bytes']:,} bytes
- SHA-256: `{power['rawTelemetry']['sha256']}`

The machine-readable summary is
[`config/alpha-2-amd-rx6800-windows-qualification-result.json`](https://github.com/hysel/haven-42/blob/main/config/alpha-2-amd-rx6800-windows-qualification-result.json).
"""


def update_catalog() -> None:
    lines = CATALOG.read_text(encoding="utf-8").splitlines()
    if any(f"\t{CATALOG_SUBJECT}\t" in line for line in lines[1:]):
        write_lf(CATALOG, "\n".join(lines) + "\n")
        return
    row = [
        "2",
        "hardware-qualification",
        CATALOG_SUBJECT,
        "Ollama ROCm",
        "0.32.14",
        "Ollama",
        "Windows 11",
        "digest-pinned-nineteen-model-corpus",
        "exact-artifact-core-task-gate-30-minute-soak-and-filtered-power-summary",
        "local-endpoint",
        "partial-pass",
        "examples/amd-rx6800-windows-model-qualification.md",
        "All 19 exact artifacts passed Chat, Writing, and Summarization and then passed independent 30-minute soaks on this exact RX 6800 Windows profile. Filtered HWiNFO GPU ASIC telemetry is aggregate-only; the raw file is excluded and represented only by SHA-256 and size. Driver version, per-model power, wall power, coding surfaces, automatic defaults, and support changes remain out of scope.",
    ]
    if any("\t" in field or "\n" in field or "\r" in field for field in row):
        raise ValueError("catalog row contains unsafe whitespace")
    write_lf(CATALOG, "\n".join(lines + ["\t".join(row)]) + "\n")


def assert_sanitized_outputs() -> None:
    combined = RESULT.read_bytes() + b"\n" + REPORT.read_bytes()
    for category, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(combined):
            raise ValueError(f"sanitized output contains forbidden category: {category}")
    lowered = combined.lower()
    forbidden = (b'"sourcefile"', b"hwinfo.csv")
    if any(token in lowered for token in forbidden):
        raise ValueError("sanitized output contains a forbidden raw-data reference")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    if not source.is_dir():
        raise SystemExit("source root is not a directory")
    result = build_result(source)
    write_lf(RESULT, json.dumps(result, indent=2) + "\n")
    write_lf(REPORT, render_report(result))
    update_catalog()
    assert_sanitized_outputs()
    print(
        json.dumps(
            {
                "filesScanned": result["privacyAudit"]["filesScanned"],
                "modelsCrossChecked": len(result["models"]),
                "coreSamplesPassed": result["counts"]["coreSamplesPassed"],
                "soakSamplesPassed": result["counts"]["soakSamplesPassed"],
                "rawTelemetryCommitted": False,
                "result": RESULT.relative_to(ROOT).as_posix(),
                "report": REPORT.relative_to(ROOT).as_posix(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
