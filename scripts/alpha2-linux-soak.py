#!/usr/bin/env python3
"""Run a bounded, sanitized Alpha 2 local inference soak.

The runner contacts only an IPv4-loopback Ollama endpoint and reuses the
reviewed model-cell validator. Model output is never retained or printed. Each
cell performs three samples and proves that the model unloads after every
sample. A quiet interval between cells also exercises idle/runtime recovery.

This tool does not download models, start Ollama, change automatic-selection
policy, or modify a machine. Its JSON output is evidence for owner review.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
MODEL_RUNNER_PATH = ROOT / "scripts/alpha2-linux-model-validation.py"
QUALIFICATION_MATRIX_PATH = ROOT / "config/alpha-2-model-qualification-matrix.json"
QUALIFICATION_INVENTORY_PATH = ROOT / "config/alpha-2-model-version-inventory.json"
MIN_DURATION_MINUTES = 5
MAX_DURATION_MINUTES = 720
MIN_INTERVAL_SECONDS = 30
MAX_INTERVAL_SECONDS = 300
MAX_CELLS = 1_500
CAPABILITIES = ("general.chat", "content.write", "content.summarize")
ACCELERATED_BACKENDS = {"cuda", "rocm", "vulkan"}
GIB_BYTES = 1024 ** 3


def _load_model_runner():
    if (
        MODEL_RUNNER_PATH.is_symlink()
        or not MODEL_RUNNER_PATH.is_file()
        or MODEL_RUNNER_PATH.stat().st_size > 2 * 1024 * 1024
    ):
        raise ValueError("unsafe-model-runner")
    specification = importlib.util.spec_from_file_location(
        "alpha2_linux_model_validation_for_soak", MODEL_RUNNER_PATH
    )
    if specification is None or specification.loader is None:
        raise ValueError("invalid-model-runner")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


MODEL_RUNNER = _load_model_runner()


class SoakError(ValueError):
    """The requested soak or one of its bounded cells failed closed."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise SoakError("unsafe-qualification-metadata")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SoakError("invalid-qualification-metadata") from error
    if not isinstance(value, dict):
        raise SoakError("invalid-qualification-metadata")
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _qualification_profile(model_id: str, profile_id: str) -> dict[str, Any]:
    inventory = _load_json(QUALIFICATION_INVENTORY_PATH)
    matrix = _load_json(QUALIFICATION_MATRIX_PATH)
    if (
        matrix.get("schemaVersion") != 1
        or matrix.get("status") != "qualification-only-no-product-promotion"
        or matrix.get("inventoryBinding") != {
            "path": "config/alpha-2-model-version-inventory.json",
            "canonicalSha256": _canonical_sha256(inventory),
        }
        or matrix.get("provider") != inventory.get("qualificationProvider")
        or matrix.get("soakGate") != {
            "allTaskChecksMustPass": True,
            "durationMinutes": 30,
            "intervalSeconds": 120,
            "unloadAfterEverySampleRequired": True,
            "rawPromptsOrResponsesAllowed": False,
            "automaticSelectionEvidenceAllowed": False,
            "automaticDefaultChangeAllowed": False,
        }
    ):
        raise SoakError("invalid-qualification-matrix")
    candidates = matrix.get("candidates")
    profiles = matrix.get("profiles")
    candidate_matches = [
        item for item in candidates
        if isinstance(item, dict) and item.get("modelId") == model_id
    ] if isinstance(candidates, list) else []
    profile_matches = [
        item for item in profiles
        if isinstance(item, dict) and item.get("id") == profile_id
    ] if isinstance(profiles, list) else []
    if len(candidate_matches) != 1 or len(profile_matches) != 1:
        raise SoakError("unreviewed-qualification-cell")
    candidate = candidate_matches[0]
    if (
        candidate.get("state") != "ready-for-qualification"
        or profile_id not in candidate.get("requiredProfiles", [])
    ):
        raise SoakError("unreviewed-qualification-cell")
    return profile_matches[0]


def _finite_number(value: Any, *, minimum: float, maximum: float, code: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or not minimum <= float(value) <= maximum
    ):
        raise SoakError(code)
    return float(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def run_soak(
    *,
    origin: str,
    model_id: str,
    operating_system_id: str,
    backend: str,
    system_memory_gib: float,
    usable_gpu_memory_gib: float,
    duration_minutes: float,
    interval_seconds: float = 120,
    qualification_inventory: bool = False,
    qualification_profile_id: str | None = None,
    platform_family: str = "linux",
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    cell_runner: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run reviewed cells until the requested monotonic deadline is reached."""

    duration = _finite_number(
        duration_minutes,
        minimum=MIN_DURATION_MINUTES,
        maximum=MAX_DURATION_MINUTES,
        code="invalid-soak-duration",
    )
    interval = _finite_number(
        interval_seconds,
        minimum=MIN_INTERVAL_SECONDS,
        maximum=MAX_INTERVAL_SECONDS,
        code="invalid-soak-interval",
    )
    memory = _finite_number(
        system_memory_gib,
        minimum=0,
        maximum=1024,
        code="invalid-memory-measurement",
    )
    gpu_memory = _finite_number(
        usable_gpu_memory_gib,
        minimum=0,
        maximum=1024,
        code="invalid-memory-measurement",
    )
    try:
        checked_origin = MODEL_RUNNER.validate_origin(origin)
        if not isinstance(qualification_inventory, bool):
            raise SoakError("invalid-qualification-mode")
        if qualification_inventory:
            if not isinstance(qualification_profile_id, str):
                raise SoakError("qualification-profile-required")
            qualification_profile = _qualification_profile(
                model_id, qualification_profile_id
            )
        elif qualification_profile_id is not None:
            raise SoakError("unexpected-qualification-profile")
        else:
            qualification_profile = None
        resolver = (
            MODEL_RUNNER.reviewed_qualification_model
            if qualification_inventory else MODEL_RUNNER.reviewed_model
        )
        model, binding_digest, provider_version = resolver(model_id)
    except MODEL_RUNNER.ValidationError as error:
        raise SoakError(str(error)) from error
    if backend not in {"cpu", *ACCELERATED_BACKENDS}:
        raise SoakError("unreviewed-backend")
    if platform_family not in {"linux", "windows"}:
        raise SoakError("unreviewed-platform-family")
    if backend == "cpu" and gpu_memory != 0:
        raise SoakError("cpu-cell-gpu-memory-mismatch")
    if not MODEL_RUNNER.SAFE_PROFILE.fullmatch(operating_system_id):
        raise SoakError("invalid-operating-system-id")
    if qualification_profile is not None and (
        qualification_profile.get("backend") != backend
        or memory < qualification_profile.get("minimumSystemMemoryGiB", 1025)
        or gpu_memory < qualification_profile.get("minimumUsableGpuMemoryGiB", 1025)
    ):
        raise SoakError("profile-memory-requirement-not-met")

    execute_cell = cell_runner or MODEL_RUNNER.run_cell
    started_monotonic = monotonic()
    if not math.isfinite(started_monotonic):
        raise SoakError("invalid-monotonic-clock")
    deadline = started_monotonic + duration * 60
    started_at = _utc_now()
    cells = 0
    samples = 0
    unloads = 0
    output_tokens = 0
    peak_vram = 0
    rates: list[float] = []
    capability_counts = {capability: 0 for capability in CAPABILITIES}

    while monotonic() < deadline:
        if cells >= MAX_CELLS:
            raise SoakError("soak-cell-limit-exceeded")
        capability = CAPABILITIES[cells % len(CAPABILITIES)]
        try:
            cell_arguments = {
                "origin": checked_origin,
                "model_id": model_id,
                "capability": capability,
                "operating_system_id": operating_system_id,
                "backend": backend,
                "system_memory_gib": memory,
                "usable_gpu_memory_gib": gpu_memory,
                "provider_version": provider_version,
                "platform_family": platform_family,
            }
            if qualification_inventory:
                cell_arguments["qualification_inventory"] = True
            result = execute_cell(
                **cell_arguments,
            )
        except MODEL_RUNNER.ValidationError as error:
            raise SoakError(str(error)) from error
        metrics = result.get("metrics") if isinstance(result, dict) else None
        if (
            result.get("outcome") != "passed"
            or not isinstance(metrics, dict)
            or metrics.get("samplesPassed") != 3
            or metrics.get("unloadPasses") != 3
        ):
            raise SoakError("invalid-cell-result")
        rate = _finite_number(
            metrics.get("tokensPerSecond"),
            minimum=0.000001,
            maximum=1_000_000,
            code="invalid-cell-result",
        )
        cell_vram = metrics.get("peakGpuMemoryBytes")
        cell_tokens = metrics.get("outputTokens")
        if (
            isinstance(cell_vram, bool)
            or not isinstance(cell_vram, int)
            or cell_vram < 0
            or isinstance(cell_tokens, bool)
            or not isinstance(cell_tokens, int)
            or cell_tokens < 1
        ):
            raise SoakError("invalid-cell-result")
        if backend == "cpu" and cell_vram != 0:
            raise SoakError("cpu-cell-used-gpu")
        if backend in ACCELERATED_BACKENDS and cell_vram <= 0:
            raise SoakError(f"{backend}-residency-not-observed")
        if qualification_profile is not None:
            minimum_free_gpu_memory_gib = qualification_profile.get(
                "minimumFreeGpuMemoryGiB", 0
            )
            if (
                isinstance(minimum_free_gpu_memory_gib, bool)
                or not isinstance(minimum_free_gpu_memory_gib, (int, float))
                or not 0 <= minimum_free_gpu_memory_gib <= gpu_memory
            ):
                raise SoakError("invalid-qualification-matrix")
            if (
                backend in ACCELERATED_BACKENDS
                and gpu_memory * GIB_BYTES - cell_vram
                < minimum_free_gpu_memory_gib * GIB_BYTES
            ):
                raise SoakError("insufficient-gpu-headroom")
        cells += 1
        samples += 3
        unloads += 3
        output_tokens += cell_tokens
        peak_vram = max(peak_vram, cell_vram)
        rates.append(rate)
        capability_counts[capability] += 1

        remaining = deadline - monotonic()
        if remaining > 0:
            sleeper(min(interval, remaining))

    elapsed = monotonic() - started_monotonic
    if cells < len(CAPABILITIES) or elapsed < duration * 60:
        raise SoakError("soak-duration-not-proven")
    result = {
        "schemaVersion": 1,
        "kind": (
            "alpha2-linux-model-soak-evidence"
            if platform_family == "linux"
            else "alpha2-windows-model-soak-evidence"
        ),
        "outcome": "passed",
        "errorCode": None,
        "startedAt": started_at,
        "completedAt": _utc_now(),
        "durationSeconds": round(elapsed, 3),
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "metrics": {
            "cellsPassed": cells,
            "samplesPassed": samples,
            "unloadPasses": unloads,
            "outputTokens": output_tokens,
            "averageTokensPerSecond": round(sum(rates) / len(rates), 3),
            "minimumTokensPerSecond": round(min(rates), 3),
            "maximumTokensPerSecond": round(max(rates), 3),
            "peakGpuMemoryBytes": peak_vram,
            "capabilityCells": capability_counts,
        },
        "evidence": {
            "modelId": model_id,
            "manifestDigest": model["manifestDigest"],
            "platformFamily": platform_family,
            "operatingSystemId": operating_system_id,
            "architecture": "x64",
            "backendMode": backend,
            "provider": "ollama",
            "providerVersion": provider_version,
            "systemMemoryGiB": memory,
            "usableGpuMemoryGiB": gpu_memory,
            "requestedDurationMinutes": duration,
            "intervalSeconds": interval,
            "automaticPromotionAllowed": False,
        },
    }
    if qualification_inventory:
        result["evidence"]["qualificationInventoryCanonicalSha256"] = binding_digest
        result["evidence"]["qualificationOnly"] = True
        result["evidence"]["qualificationProfileId"] = qualification_profile_id
    else:
        result["evidence"]["selectorPolicyCanonicalSha256"] = binding_digest
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:11435")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--operating-system-id", required=True)
    parser.add_argument(
        "--platform-family", choices=("linux", "windows"), default="linux"
    )
    parser.add_argument(
        "--backend", choices=("cpu", "cuda", "rocm", "vulkan"), required=True
    )
    parser.add_argument("--system-memory-gib", type=float, required=True)
    parser.add_argument("--usable-gpu-memory-gib", type=float, required=True)
    parser.add_argument("--duration-minutes", type=float, required=True)
    parser.add_argument("--interval-seconds", type=float, default=120)
    parser.add_argument("--qualification-inventory", action="store_true")
    parser.add_argument("--qualification-profile-id")
    args = parser.parse_args()
    try:
        result = run_soak(
            origin=args.origin,
            model_id=args.model_id,
            operating_system_id=args.operating_system_id,
            backend=args.backend,
            system_memory_gib=args.system_memory_gib,
            usable_gpu_memory_gib=args.usable_gpu_memory_gib,
            duration_minutes=args.duration_minutes,
            interval_seconds=args.interval_seconds,
            qualification_inventory=args.qualification_inventory,
            qualification_profile_id=args.qualification_profile_id,
            platform_family=args.platform_family,
        )
    except SoakError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
