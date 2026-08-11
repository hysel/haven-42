#!/usr/bin/env python3
"""Summarize sanitized Alpha 2 model qualification evidence offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
INVENTORY_PATH = ROOT / "config/alpha-2-model-version-inventory.json"
MATRIX_PATH = ROOT / "config/alpha-2-model-qualification-matrix.json"
MAX_EVIDENCE_BYTES = 2 * 1024 * 1024
CAPABILITIES = ("general.chat", "content.write", "content.summarize")
LEGACY_LINUX_OPERATING_SYSTEM_IDS = frozenset({"bazzite-44"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ReportError(ValueError):
    """Evidence was unsafe, stale, ambiguous, or structurally invalid."""


def _load(path: Path, code: str) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_EVIDENCE_BYTES:
            raise ReportError(code)
        # Windows PowerShell 5.1 writes a UTF-8 BOM for ``-Encoding utf8``.
        # Accept that standard marker while retaining strict UTF-8 decoding.
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportError(code) from error
    if not isinstance(value, dict):
        raise ReportError(code)
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _reviewed_context(
    inventory_path: Path = INVENTORY_PATH,
    matrix_path: Path = MATRIX_PATH,
) -> tuple[dict[tuple[str, str], dict[str, Any]], str, str]:
    inventory = _load(inventory_path, "invalid-qualification-inventory")
    matrix = _load(matrix_path, "invalid-qualification-matrix")
    inventory_sha = _canonical_sha256(inventory)
    if matrix.get("inventoryBinding") != {
        "path": "config/alpha-2-model-version-inventory.json",
        "canonicalSha256": inventory_sha,
    }:
        raise ReportError("stale-qualification-matrix")
    matrix_sha = _canonical_sha256(matrix)
    inventory_candidates: dict[str, dict[str, Any]] = {}
    for family in inventory.get("families", []):
        if not isinstance(family, dict):
            raise ReportError("invalid-qualification-inventory")
        for version in family.get("versions", []):
            if not isinstance(version, dict):
                raise ReportError("invalid-qualification-inventory")
            for candidate in version.get("candidates", []):
                if not isinstance(candidate, dict):
                    raise ReportError("invalid-qualification-inventory")
                model_id = candidate.get("id")
                manifest = candidate.get("manifestDigest")
                if (
                    not isinstance(model_id, str)
                    or not model_id
                    or not isinstance(manifest, str)
                    or not SHA256.fullmatch(manifest)
                    or model_id in inventory_candidates
                ):
                    raise ReportError("invalid-qualification-inventory")
                inventory_candidates[model_id] = candidate
    provider = matrix.get("provider")
    profiles = matrix.get("profiles")
    task_checks = matrix.get("taskChecks")
    if (
        not isinstance(provider, dict)
        or provider.get("name") != "ollama"
        or not isinstance(provider.get("exactVersion"), str)
        or not provider.get("exactVersion")
        or not isinstance(profiles, list)
        or not isinstance(task_checks, list)
    ):
        raise ReportError("invalid-qualification-matrix")
    reviewed_profiles: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        if (
            not isinstance(profile, dict)
            or not isinstance(profile.get("id"), str)
            or profile.get("backend") not in {"cpu", "cuda"}
            or isinstance(profile.get("minimumSystemMemoryGiB"), bool)
            or not isinstance(profile.get("minimumSystemMemoryGiB"), (int, float))
            or isinstance(profile.get("minimumUsableGpuMemoryGiB"), bool)
            or not isinstance(profile.get("minimumUsableGpuMemoryGiB"), (int, float))
            or not math.isfinite(float(profile["minimumSystemMemoryGiB"]))
            or not math.isfinite(float(profile["minimumUsableGpuMemoryGiB"]))
            or profile["minimumSystemMemoryGiB"] < 0
            or profile["minimumUsableGpuMemoryGiB"] < 0
            or profile["id"] in reviewed_profiles
        ):
            raise ReportError("invalid-qualification-matrix")
        reviewed_profiles[profile["id"]] = profile
    reviewed_checks: dict[str, str] = {}
    for check in task_checks:
        if (
            not isinstance(check, dict)
            or check.get("capability") not in CAPABILITIES
            or not isinstance(check.get("check"), str)
            or check["capability"] in reviewed_checks
            or check.get("samples") != 3
        ):
            raise ReportError("invalid-qualification-matrix")
        reviewed_checks[check["capability"]] = check["check"]
    if set(reviewed_checks) != set(CAPABILITIES):
        raise ReportError("invalid-qualification-matrix")
    cells: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in matrix.get("candidates", []):
        if not isinstance(candidate, dict) or candidate.get("state") != "ready-for-qualification":
            continue
        model_id = candidate.get("modelId")
        inventory_candidate = inventory_candidates.get(model_id)
        required_profiles = candidate.get("requiredProfiles")
        if inventory_candidate is None or not isinstance(required_profiles, list):
            raise ReportError("invalid-qualification-matrix")
        for profile_id in required_profiles:
            profile = reviewed_profiles.get(profile_id)
            key = (model_id, profile_id)
            if profile is None or key in cells:
                raise ReportError("invalid-qualification-matrix")
            cells[key] = {
                "manifestDigest": inventory_candidate["manifestDigest"],
                "provider": provider["name"],
                "providerVersion": provider["exactVersion"],
                "backendMode": profile["backend"],
                "minimumSystemMemoryGiB": float(profile["minimumSystemMemoryGiB"]),
                "minimumUsableGpuMemoryGiB": float(profile["minimumUsableGpuMemoryGiB"]),
                "checks": reviewed_checks,
            }
    if not cells:
        raise ReportError("invalid-qualification-matrix")
    return cells, inventory_sha, matrix_sha


def _reviewed_cells(
    inventory_path: Path = INVENTORY_PATH,
    matrix_path: Path = MATRIX_PATH,
) -> tuple[set[tuple[str, str]], str, str]:
    context, inventory_sha, matrix_sha = _reviewed_context(
        inventory_path, matrix_path
    )
    return set(context), inventory_sha, matrix_sha


def _common_evidence(record: dict[str, Any], inventory_sha: str) -> dict[str, Any]:
    if (
        record.get("containsRawPromptsOrResponses") is not False
        or record.get("containsPrivateMachineIdentity") is not False
    ):
        raise ReportError("unsafe-qualification-evidence")
    evidence = record.get("evidence")
    if (
        not isinstance(evidence, dict)
        or evidence.get("qualificationInventoryCanonicalSha256") != inventory_sha
        or evidence.get("automaticPromotionAllowed") is not False
    ):
        raise ReportError("stale-qualification-evidence")
    return evidence


def _finite_measurement(value: Any, minimum: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < minimum
    ):
        raise ReportError("invalid-qualification-binding")
    return float(value)


def _validate_binding(
    evidence: dict[str, Any], expected: dict[str, Any], outcome: Any
) -> None:
    if (
        outcome not in {"passed", "failed"}
        or evidence.get("manifestDigest") != expected["manifestDigest"]
        or evidence.get("provider") != expected["provider"]
        or evidence.get("providerVersion") != expected["providerVersion"]
        or evidence.get("backendMode") != expected["backendMode"]
    ):
        raise ReportError("invalid-qualification-binding")
    system_value = evidence.get("systemMemoryGiB")
    gpu_value = evidence.get("usableGpuMemoryGiB")
    if outcome == "failed" and system_value is None and gpu_value is None:
        return
    system_memory = _finite_measurement(system_value, 0)
    gpu_memory = _finite_measurement(gpu_value, 0)
    if (
        system_memory < expected["minimumSystemMemoryGiB"]
        or gpu_memory < expected["minimumUsableGpuMemoryGiB"]
        or (expected["backendMode"] == "cpu" and gpu_memory != 0)
    ):
        raise ReportError("invalid-qualification-binding")


def _task_metrics(
    record: dict[str, Any], backend: str
) -> dict[str, int | float] | None:
    if record.get("outcome") != "passed":
        return None
    metrics = record.get("metrics")
    if not isinstance(metrics, dict):
        raise ReportError("invalid-task-qualification-evidence")
    integers = {
        "samplesPassed": metrics.get("samplesPassed"),
        "unloadPasses": metrics.get("unloadPasses"),
        "outputTokens": metrics.get("outputTokens"),
        "peakGpuMemoryBytes": metrics.get("peakGpuMemoryBytes"),
    }
    if (
        any(isinstance(value, bool) or not isinstance(value, int) for value in integers.values())
        or integers["samplesPassed"] != 3
        or integers["unloadPasses"] != 3
        or integers["outputTokens"] <= 0
        or integers["peakGpuMemoryBytes"] < 0
        or (backend == "cpu" and integers["peakGpuMemoryBytes"] != 0)
        or (backend == "cuda" and integers["peakGpuMemoryBytes"] <= 0)
    ):
        raise ReportError("invalid-task-qualification-evidence")
    rate = metrics.get("tokensPerSecond")
    if (
        isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(float(rate))
        or rate <= 0
    ):
        raise ReportError("invalid-task-qualification-evidence")
    return {**integers, "tokensPerSecond": float(rate)}


def _soak_metrics(
    record: dict[str, Any], backend: str
) -> dict[str, int | float] | None:
    if record.get("outcome") != "passed":
        return None
    metrics = record.get("metrics")
    duration = record.get("durationSeconds")
    if not isinstance(metrics, dict):
        raise ReportError("invalid-soak-evidence")
    integers = {
        "cellsPassed": metrics.get("cellsPassed"),
        "samplesPassed": metrics.get("samplesPassed"),
        "unloadPasses": metrics.get("unloadPasses"),
        "outputTokens": metrics.get("outputTokens"),
        "peakGpuMemoryBytes": metrics.get("peakGpuMemoryBytes"),
    }
    rate = metrics.get("averageTokensPerSecond")
    capability_cells = metrics.get("capabilityCells")
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(float(duration))
        or duration < 1800
        or any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in integers.values()
        )
        or integers["cellsPassed"] < len(CAPABILITIES)
        or integers["samplesPassed"] != integers["cellsPassed"] * 3
        or integers["samplesPassed"] != integers["unloadPasses"]
        or integers["outputTokens"] <= 0
        or integers["peakGpuMemoryBytes"] < 0
        or (backend == "cpu" and integers["peakGpuMemoryBytes"] != 0)
        or (backend == "cuda" and integers["peakGpuMemoryBytes"] <= 0)
        or not isinstance(capability_cells, dict)
        or set(capability_cells) != set(CAPABILITIES)
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 1
            for value in capability_cells.values()
        )
        or sum(capability_cells.values()) != integers["cellsPassed"]
        or isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(float(rate))
        or rate <= 0
    ):
        raise ReportError("invalid-soak-evidence")
    return {
        "durationSeconds": float(duration),
        **integers,
        "averageTokensPerSecond": float(rate),
    }


def build_report(
    evidence_directory: Path,
    inventory_path: Path = INVENTORY_PATH,
    matrix_path: Path = MATRIX_PATH,
) -> dict[str, Any]:
    cells, inventory_sha, matrix_sha = _reviewed_context(
        inventory_path, matrix_path
    )
    try:
        base = evidence_directory.resolve(strict=True)
    except OSError as error:
        raise ReportError("invalid-evidence-directory") from error
    if not base.is_dir() or evidence_directory.is_symlink():
        raise ReportError("invalid-evidence-directory")

    tasks: dict[tuple[str, str, str, str], dict[str, dict[str, Any]]] = {}
    soaks: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    recognized = 0
    for path in sorted(base.rglob("*.json")):
        if path.is_symlink() or base not in path.resolve().parents:
            raise ReportError("unsafe-evidence-file")
        record = _load(path, "invalid-evidence-file")
        kind = record.get("kind")
        if kind not in {
            "alpha2-model-task-qualification-evidence",
            "alpha2-linux-model-soak-evidence",
            "alpha2-windows-model-soak-evidence",
        }:
            continue
        recognized += 1
        evidence = _common_evidence(record, inventory_sha)
        model_id = evidence.get("modelId")
        profile_id = evidence.get("profileId", evidence.get("qualificationProfileId"))
        operating_system_id = evidence.get("operatingSystemId")
        platform_family = evidence.get("platformFamily")
        if kind == "alpha2-model-task-qualification-evidence" and platform_family is None:
            # Only the exact pre-Windows Bazzite record set may omit this field.
            if operating_system_id not in LEGACY_LINUX_OPERATING_SYSTEM_IDS:
                raise ReportError("unreviewed-qualification-evidence")
            platform_family = "linux"
        if (
            (model_id, profile_id) not in cells
            or not isinstance(operating_system_id, str)
            or not operating_system_id
            or platform_family not in {"linux", "windows"}
            or (
                kind == "alpha2-linux-model-soak-evidence"
                and platform_family != "linux"
            )
            or (
                kind == "alpha2-windows-model-soak-evidence"
                and platform_family != "windows"
            )
        ):
            raise ReportError("unreviewed-qualification-evidence")
        expected = cells[(model_id, profile_id)]
        _validate_binding(evidence, expected, record.get("outcome"))
        key = (model_id, profile_id, platform_family, operating_system_id)
        if kind == "alpha2-model-task-qualification-evidence":
            if evidence.get("qualificationMatrixCanonicalSha256") != matrix_sha:
                raise ReportError("stale-qualification-evidence")
            capability = evidence.get("capability")
            if (
                capability not in CAPABILITIES
                or evidence.get("check") != expected["checks"][capability]
            ):
                raise ReportError("unreviewed-qualification-evidence")
            bucket = tasks.setdefault(key, {})
            if capability in bucket:
                raise ReportError("duplicate-qualification-evidence")
            bucket[capability] = {
                "outcome": record.get("outcome"),
                "errorCode": record.get("errorCode"),
                "metrics": _task_metrics(record, expected["backendMode"]),
            }
        else:
            if evidence.get("qualificationOnly") is not True or key in soaks:
                raise ReportError("invalid-soak-evidence")
            metrics = _soak_metrics(record, expected["backendMode"])
            soaks[key] = {
                "outcome": record.get("outcome"),
                "errorCode": record.get("errorCode"),
                **(metrics or {}),
            }

    if recognized == 0:
        raise ReportError("no-qualification-evidence")
    results = []
    for key in sorted(set(tasks) | set(soaks)):
        task_results = tasks.get(key, {})
        soak = soaks.get(key)
        all_tasks_present = set(task_results) == set(CAPABILITIES)
        all_tasks_passed = all_tasks_present and all(
            value["outcome"] == "passed" for value in task_results.values()
        )
        soak_passed = (
            isinstance(soak, dict)
            and soak.get("outcome") == "passed"
        )
        if any(value["outcome"] == "failed" for value in task_results.values()) or (
            isinstance(soak, dict) and soak.get("outcome") == "failed"
        ):
            status = "failed"
        elif all_tasks_passed and soak_passed:
            status = "passed"
        else:
            status = "incomplete"
        results.append(
            {
                "modelId": key[0],
                "profileId": key[1],
                "platformFamily": key[2],
                "operatingSystemId": key[3],
                "status": status,
                "tasks": {
                    capability: task_results.get(
                        capability,
                        {"outcome": "missing", "errorCode": None, "metrics": None},
                    )
                    for capability in CAPABILITIES
                },
                "soak": soak or {"outcome": "missing", "errorCode": None},
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "alpha2-model-qualification-summary",
        "qualificationInventoryCanonicalSha256": inventory_sha,
        "qualificationMatrixCanonicalSha256": matrix_sha,
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticDefaultChangeAllowed": False,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument(
        "--inventory",
        type=Path,
        help="Pinned inventory snapshot used to create historical evidence.",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        help="Pinned matrix snapshot bound to the historical inventory.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (args.inventory is None) != (args.matrix is None):
        parser.error("inventory-and-matrix-must-be-supplied-together")
    try:
        result = build_report(
            args.evidence_dir,
            args.inventory or INVENTORY_PATH,
            args.matrix or MATRIX_PATH,
        )
    except ReportError as error:
        parser.error(str(error))
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        if args.output.exists() or args.output.is_symlink():
            parser.error("output-already-exists")
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
