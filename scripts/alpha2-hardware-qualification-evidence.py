#!/usr/bin/env python3
"""Build sanitized, fail-closed hardware qualification evidence.

The input is an exported campaign directory, never a live lab endpoint. Raw
prompts, responses, host names, addresses, keys, and machine identifiers are
deliberately outside this contract.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import statistics
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FRESHNESS_SPEC = importlib.util.spec_from_file_location(
    "alpha2_evidence_freshness_for_hardware",
    REPOSITORY_ROOT / "scripts/alpha2-evidence-freshness.py",
)
assert FRESHNESS_SPEC and FRESHNESS_SPEC.loader
FRESHNESS = importlib.util.module_from_spec(FRESHNESS_SPEC)
FRESHNESS_SPEC.loader.exec_module(FRESHNESS)


MAX_FILE_BYTES = 8 * 1024 * 1024
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,99}$")
FORBIDDEN_PROFILE_KEYS = {
    "address", "host", "hostname", "ip", "machineid", "machineuuid",
    "serial", "sshkey", "username",
}
ALLOWED_PROFILE_KEYS = {
    "schemaVersion", "release", "operatingSystem", "kernel", "accelerator",
    "driverVersion", "backend", "systemMemoryGiB", "runtimeProvider",
    "runtimeVersion", "runtimeArtifactSha256", "qualificationProfileId",
    "inventoryCanonicalSha256", "matrixCanonicalSha256", "expectedModelIds",
    "telemetryUtcOffset",
}
FINAL_EVENTS = {"core-complete", "soak-complete", "post-idle-complete"}
REQUIRED_BINDING_ROLES = {
    "model-inventory", "qualification-matrix", "core-validator",
    "soak-validator", "core-orchestrator", "soak-orchestrator",
}


class EvidenceError(ValueError):
    """An input cannot safely become qualification evidence."""


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_file(root: Path, relative: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9._/-]{1,300}", relative) or ".." in relative.split("/"):
        raise EvidenceError(f"unsafe relative path: {relative}")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise EvidenceError(f"required regular file is unavailable: {relative}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise EvidenceError(f"input exceeds {MAX_FILE_BYTES} bytes: {relative}")
    if root.resolve() not in path.resolve().parents:
        raise EvidenceError(f"input escaped campaign root: {relative}")
    return path


def read_json(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads(_safe_file(root, relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidenceError(f"JSON object required: {relative}")
    return value


def read_tsv(root: Path, relative: str, fields: list[str]) -> list[dict[str, str]]:
    with _safe_file(root, relative).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != fields:
            raise EvidenceError(f"unexpected columns in {relative}: {reader.fieldnames}")
        rows = list(reader)
    for row in rows:
        if any(value is None or "\n" in value or "\r" in value for value in row.values()):
            raise EvidenceError(f"malformed row in {relative}")
    return rows


def read_events(root: Path) -> list[dict[str, str]]:
    lines = _safe_file(root, "telemetry/events.tsv").read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, str]] = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) != 3:
            raise EvidenceError("event log must contain three tab-separated fields")
        rows.append(dict(zip(("timestamp", "subject", "event"), parts)))
    previous: datetime | None = None
    for row in rows:
        try:
            observed = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        except ValueError as error:
            raise EvidenceError("event timestamp is invalid") from error
        if observed.tzinfo is None or (previous is not None and observed < previous):
            raise EvidenceError("event timestamps must be timezone-aware and ordered")
        if row["subject"] != "campaign" and not SAFE_ID.fullmatch(row["subject"]):
            raise EvidenceError(f"unsafe event subject: {row['subject']}")
        previous = observed
    return rows


def validate_profile(profile: dict[str, Any]) -> None:
    required_strings = (
        "release", "operatingSystem", "kernel", "accelerator", "driverVersion",
        "backend", "runtimeProvider", "runtimeVersion", "runtimeArtifactSha256",
        "qualificationProfileId", "inventoryCanonicalSha256", "matrixCanonicalSha256",
    )
    if profile.get("schemaVersion") != 1:
        raise EvidenceError("profile schemaVersion must be 1")
    lowered = {str(key).replace("_", "").lower() for key in profile}
    forbidden = sorted(lowered & FORBIDDEN_PROFILE_KEYS)
    if forbidden:
        raise EvidenceError(f"private identity fields are forbidden: {', '.join(forbidden)}")
    unknown = sorted(set(profile) - ALLOWED_PROFILE_KEYS)
    if unknown:
        raise EvidenceError(f"unknown profile fields are forbidden: {', '.join(unknown)}")
    for key in required_strings:
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            raise EvidenceError(f"profile requires a non-empty {key}")
        if any(ord(character) < 32 or ord(character) == 127 for character in profile[key]):
            raise EvidenceError(f"profile {key} contains control characters")
    for key in ("runtimeArtifactSha256", "inventoryCanonicalSha256", "matrixCanonicalSha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", profile[key]):
            raise EvidenceError(f"profile {key} must be lowercase SHA-256")
    if not isinstance(profile.get("systemMemoryGiB"), (int, float)) or profile["systemMemoryGiB"] <= 0:
        raise EvidenceError("profile systemMemoryGiB must be positive")
    if not isinstance(profile.get("expectedModelIds"), list) or not profile["expectedModelIds"]:
        raise EvidenceError("profile expectedModelIds must be a non-empty list")
    if len(profile["expectedModelIds"]) != len(set(profile["expectedModelIds"])):
        raise EvidenceError("profile expectedModelIds contains duplicates")
    if any(not isinstance(item, str) or not SAFE_ID.fullmatch(item) for item in profile["expectedModelIds"]):
        raise EvidenceError("profile contains an unsafe model ID")
    if not re.fullmatch(r"[+-](?:0[0-9]|1[0-4]):[0-5][0-9]", str(profile.get("telemetryUtcOffset", ""))):
        raise EvidenceError("profile telemetryUtcOffset must use ±HH:MM")


def parse_telemetry_time(value: str, utc_offset: str) -> datetime:
    value = value.strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = datetime.strptime(value, "%Y/%m/%d %H:%M:%S.%f")
    if parsed.tzinfo is None:
        sign = 1 if utc_offset.startswith("+") else -1
        hours, minutes = (int(part) for part in utc_offset[1:].split(":"))
        parsed = parsed.replace(tzinfo=timezone(sign * timedelta(hours=hours, minutes=minutes)))
    return parsed.astimezone(timezone.utc)


def range_summary(samples: list[tuple[datetime, float]], start: datetime, end: datetime) -> dict[str, Any] | None:
    values = [power for observed, power in samples if start <= observed <= end]
    if not values:
        return None
    duration_hours = max(0.0, (end - start).total_seconds()) / 3600
    average = statistics.fmean(values)
    return {
        "sampleCount": len(values),
        "averageWatts": round(average, 3),
        "peakWatts": round(max(values), 3),
        "estimatedEnergyWh": round(average * duration_hours, 3),
    }


def telemetry_summary(
    root: Path, events: list[dict[str, str]], profile: dict[str, Any],
) -> dict[str, Any]:
    path = _safe_file(root, "telemetry/nvidia-smi.csv")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise EvidenceError("telemetry CSV has no header")
        power_column = next((name for name in reader.fieldnames if "power" in name.lower()), None)
        time_column = next((name for name in reader.fieldnames if "timestamp" in name.lower()), None)
        if power_column is None or time_column is None:
            raise EvidenceError("telemetry CSV requires timestamp and power columns")
        samples: list[tuple[datetime, float]] = []
        for row in reader:
            raw = re.sub(r"[^0-9.+-]", "", row.get(power_column, ""))
            try:
                value = float(raw)
                observed = parse_telemetry_time(row.get(time_column, ""), profile["telemetryUtcOffset"])
            except ValueError:
                continue
            if 0 <= value <= 1000:
                samples.append((observed, value))
    if not samples:
        raise EvidenceError("telemetry CSV contains no valid power samples")
    samples.sort(key=lambda item: item[0])
    result: dict[str, Any] = {
        "telemetrySource": "nvidia-smi",
        "scope": "gpu-board-only",
        "sampleCount": len(samples),
        "averageWatts": round(statistics.fmean(value for _, value in samples), 3),
        "peakWatts": round(max(value for _, value in samples), 3),
        "telemetrySha256": digest,
        "includesCpuRamStorageCoolingDisplayOrPsuLosses": False,
    }
    event_times = {
        (row["subject"], row["event"]): datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        for row in events
    }
    per_model_core: dict[str, Any] = {}
    per_model_soak: dict[str, Any] = {}
    model_ids = profile["expectedModelIds"]
    for model_id in model_ids:
        start = event_times.get((model_id, "download-complete"))
        end_candidates = [
            observed for (subject, event), observed in event_times.items()
            if subject == model_id and event in {"passed", "failed-validation"}
        ]
        if start and end_candidates:
            measured = range_summary(samples, start, max(end_candidates))
            if measured:
                per_model_core[model_id] = measured
        soak_start = event_times.get((model_id, "soak-start"))
        soak_end_candidates = [
            observed for (subject, event), observed in event_times.items()
            if subject == model_id and event in {"soak-passed", "soak-failed"}
        ]
        if soak_start and soak_end_candidates:
            measured = range_summary(samples, soak_start, max(soak_end_candidates))
            if measured:
                per_model_soak[model_id] = measured
    result["perModelCore"] = per_model_core
    result["perModelSoak"] = per_model_soak
    post_start = event_times.get(("campaign", "post-idle-start"))
    post_end = event_times.get(("campaign", "post-idle-complete"))
    result["postIdle"] = range_summary(samples, post_start, post_end) if post_start and post_end else None
    return result


def _freshness_summary(binding_path: Path | None, repository_root: Path) -> dict[str, Any] | None:
    if binding_path is None:
        return None
    if binding_path.is_symlink() or not binding_path.is_file() or binding_path.stat().st_size > MAX_FILE_BYTES:
        raise EvidenceError("evidence input binding must be a bounded regular file")
    try:
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        result = FRESHNESS.assess(binding, repository_root)
    except (OSError, UnicodeError, json.JSONDecodeError, FRESHNESS.FreshnessError) as error:
        raise EvidenceError(f"invalid evidence input binding: {error}") from error
    if result["status"] != "fresh":
        stale = [item["role"] for item in result["checks"] if item["status"] != "matched"]
        raise EvidenceError(f"evidence inputs are stale: {', '.join(stale)}")
    roles = {item["role"] for item in result["checks"]}
    if roles != REQUIRED_BINDING_ROLES:
        missing = sorted(REQUIRED_BINDING_ROLES - roles)
        extra = sorted(roles - REQUIRED_BINDING_ROLES)
        raise EvidenceError(f"evidence input roles mismatch; missing={missing}, extra={extra}")
    return {
        "evidenceId": result["evidenceId"],
        "status": result["status"],
        "roles": [item["role"] for item in result["checks"]],
        "sha256": {item["role"]: item["actualSha256"] for item in result["checks"]},
    }


def build_report(
    root: Path,
    *,
    binding_path: Path | None = None,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    root = root.resolve()
    profile = read_json(root, "profile.json")
    validate_profile(profile)
    events = read_events(root)
    core = read_tsv(root, "results/core/summary.tsv", ["model_id", "status", "failure_cell"])
    soak_path = root / "results/soak/summary.tsv"
    soak = read_tsv(root, "results/soak/summary.tsv", ["model_id", "status"]) if soak_path.is_file() else []
    expected = profile["expectedModelIds"]
    for name, rows in (("core", core), ("soak", soak)):
        ids = [row["model_id"] for row in rows]
        if len(ids) != len(set(ids)) or any(item not in expected for item in ids):
            raise EvidenceError(f"{name} summary has duplicate or unexpected model IDs")
        if name == "core" and ids != expected[:len(ids)]:
            raise EvidenceError("core results are not in the pinned profile order")
    core_passed = [row["model_id"] for row in core if row["status"] == "passed"]
    core_failed = {
        row["model_id"]: [cell for cell in row["failure_cell"].split(",") if cell]
        for row in core if row["status"] != "passed"
    }
    if any(not cells for cells in core_failed.values()):
        raise EvidenceError("every failed core result needs a failure cell")
    soak_passed = [row["model_id"] for row in soak if row["status"] == "passed"]
    soak_failed = {row["model_id"]: ["thirty-minute-soak-failed"] for row in soak if row["status"] != "passed"}
    if any(row["model_id"] not in core_passed for row in soak):
        raise EvidenceError("soak results may only reference core-passing models")
    campaign_events = {row["event"] for row in events if row["subject"] == "campaign"}
    complete = FINAL_EVENTS.issubset(campaign_events)
    if complete and (len(core) != len(expected) or len(soak) != len(core_passed)):
        raise EvidenceError("campaign claims completion with missing model results")
    freshness = _freshness_summary(binding_path, repository_root)
    if complete and freshness is None:
        raise EvidenceError("completed evidence requires exact input bindings")
    observed = events[-1]["timestamp"] if events else None
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-hardware-qualification-result",
        "release": profile["release"],
        "observedThroughUtc": observed,
        "status": "exact-profile-engineering-evidence-complete" if complete else "in-progress-local-review-only",
        "environment": {
            "operatingSystem": profile["operatingSystem"], "kernel": profile["kernel"],
            "accelerator": profile["accelerator"], "driverVersion": profile["driverVersion"],
            "backend": profile["backend"], "systemMemoryGiB": profile["systemMemoryGiB"],
        },
        "runtime": {
            "provider": profile["runtimeProvider"], "version": profile["runtimeVersion"],
            "artifactSha256": profile["runtimeArtifactSha256"], "releaseAdmission": "candidate-only",
        },
        "qualificationProfileId": profile["qualificationProfileId"],
        "sourceBindings": {
            "inventoryCanonicalSha256": profile["inventoryCanonicalSha256"],
            "matrixCanonicalSha256": profile["matrixCanonicalSha256"],
            "inputFreshness": freshness,
        },
        "counts": {
            "expectedArtifacts": len(expected), "exactArtifactsChecked": len(core),
            "coreTaskGatePassed": len(core_passed), "coreTaskGateFailed": len(core_failed),
            "thirtyMinuteSoaksPassed": len(soak_passed), "thirtyMinuteSoaksFailed": len(soak_failed),
        },
        "coreTaskGate": {"passed": core_passed, "failed": core_failed},
        "soak": {"requestedMinutesPerModel": 30, "passed": soak_passed, "failed": soak_failed},
        "power": telemetry_summary(root, events, profile),
        "campaignCanonicalSha256": canonical_sha256({"profile": profile, "events": events, "core": core, "soak": soak, "inputFreshness": freshness}),
        "containsPrivateMachineIdentity": False,
        "containsNetworkIdentity": False,
        "containsRawPromptsOrResponses": False,
        "automaticDefaultChangeAllowed": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticSupportChangeAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="write atomically instead of printing")
    parser.add_argument("--input-binding", type=Path, help="exact repository input binding; required for completed evidence")
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    args = parser.parse_args()
    try:
        report = build_report(
            args.campaign_root,
            binding_path=args.input_binding,
            repository_root=args.repository_root,
        )
    except (EvidenceError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(args.output)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
