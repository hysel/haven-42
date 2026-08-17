#!/usr/bin/env python3
"""Run sanitized task-quality checks for one reviewed Alpha 2 candidate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import time
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MODEL_RUNNER_PATH = ROOT / "scripts/alpha2-linux-model-validation.py"
MATRIX_PATH = ROOT / "config/alpha-2-model-qualification-matrix.json"
INVENTORY_PATH = ROOT / "config/alpha-2-model-version-inventory.json"
WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SENTENCE_END = re.compile(r"[.!?](?=(?:[\"']?)(?:\s|$))")
TASKS = {
    "general.chat": {
        "prompt": "Reply with exactly HAVEN42_READY and nothing else.",
        "check": "exact-sentinel-response",
    },
    "content.write": {
        "prompt": (
            "Write exactly one sentence of 8 to 18 words about careful software "
            "testing. Include the word testing."
        ),
        "check": "single-sentence-word-range-and-required-topic",
    },
    "content.summarize": {
        "prompt": (
            "Summarize these facts in one sentence of 12 to 30 words, mention "
            "folder and service, and use no numbers: the runtime stays in a folder "
            "beside the app; it does not create a Windows service; deleting that "
            "folder removes its managed files."
        ),
        "check": "single-sentence-required-facts-no-invented-number",
    },
}
ACCELERATED_BACKENDS = {"cuda", "rocm", "vulkan"}
GIB_BYTES = 1024 ** 3


class QualificationError(ValueError):
    """The reviewed task-quality check failed closed."""


def _load_model_runner():
    if (
        MODEL_RUNNER_PATH.is_symlink()
        or not MODEL_RUNNER_PATH.is_file()
        or MODEL_RUNNER_PATH.stat().st_size > 2 * 1024 * 1024
    ):
        raise QualificationError("unsafe-model-runner")
    specification = importlib.util.spec_from_file_location(
        "alpha2_model_validation_for_task_qualification", MODEL_RUNNER_PATH
    )
    if specification is None or specification.loader is None:
        raise QualificationError("invalid-model-runner")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


MODEL_RUNNER = _load_model_runner()


def _load(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise QualificationError("unsafe-qualification-metadata")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise QualificationError("invalid-qualification-metadata") from error
    if not isinstance(value, dict):
        raise QualificationError("invalid-qualification-metadata")
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _review_matrix(model_id: str, profile_id: str) -> tuple[dict[str, Any], str]:
    inventory = _load(INVENTORY_PATH)
    matrix = _load(MATRIX_PATH)
    binding = matrix.get("inventoryBinding")
    if (
        matrix.get("schemaVersion") != 1
        or matrix.get("matrixId") != "haven42.alpha2.cross-family-qualification"
        or matrix.get("status") != "qualification-only-no-product-promotion"
        or binding != {
            "path": "config/alpha-2-model-version-inventory.json",
            "canonicalSha256": _canonical_sha256(inventory),
        }
        or matrix.get("provider") != inventory.get("qualificationProvider")
        or matrix.get("soakGate", {}).get("automaticSelectionEvidenceAllowed") is not False
        or matrix.get("soakGate", {}).get("automaticDefaultChangeAllowed") is not False
        or matrix.get("soakGate", {}).get("rawPromptsOrResponsesAllowed") is not False
    ):
        raise QualificationError("invalid-qualification-matrix")
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
        raise QualificationError("unreviewed-qualification-cell")
    candidate = candidate_matches[0]
    if (
        candidate.get("state") != "ready-for-qualification"
        or profile_id not in candidate.get("requiredProfiles", [])
    ):
        raise QualificationError("unreviewed-qualification-cell")
    return profile_matches[0], _canonical_sha256(matrix)


def _one_sentence(text: str) -> bool:
    return "\n" not in text and len(SENTENCE_END.findall(text.strip())) == 1


def _check_response(capability: str, response: Any) -> None:
    if not isinstance(response, str) or not response.strip() or len(response.encode("utf-8")) > 64 * 1024:
        raise QualificationError("task-response-contract-failed")
    text = response.strip()
    if capability == "general.chat":
        if text != "HAVEN42_READY":
            raise QualificationError("chat-exact-response-failed")
        return
    words = WORD.findall(text)
    if capability == "content.write":
        if not _one_sentence(text):
            raise QualificationError("writing-one-sentence-required")
        if not 8 <= len(words) <= 18:
            raise QualificationError("writing-word-count-out-of-range")
        if "testing" not in text.lower():
            raise QualificationError("writing-required-topic-missing")
        return
    if capability == "content.summarize":
        lowered = text.lower()
        if not _one_sentence(text):
            raise QualificationError("summary-one-sentence-required")
        if not 12 <= len(words) <= 30:
            raise QualificationError("summary-word-count-out-of-range")
        if "folder" not in lowered or "service" not in lowered:
            raise QualificationError("summary-required-facts-missing")
        if re.search(r"\d", text):
            raise QualificationError("summary-invented-number")
        return
    raise QualificationError("unreviewed-capability")


def run_qualification(
    *, origin: str, model_id: str, capability: str, profile_id: str,
    operating_system_id: str, system_memory_gib: float,
    usable_gpu_memory_gib: float, repetitions: int = 3,
    platform_family: str = "linux",
) -> dict[str, Any]:
    if capability not in TASKS:
        raise QualificationError("unreviewed-capability")
    if repetitions != 3:
        raise QualificationError("invalid-repetition-count")
    profile, matrix_sha = _review_matrix(model_id, profile_id)
    try:
        checked_origin = MODEL_RUNNER.validate_origin(origin)
        model, inventory_sha, provider_version = (
            MODEL_RUNNER.reviewed_qualification_model(model_id)
        )
    except MODEL_RUNNER.ValidationError as error:
        raise QualificationError(str(error)) from error
    if not MODEL_RUNNER.SAFE_PROFILE.fullmatch(operating_system_id):
        raise QualificationError("invalid-operating-system-id")
    if platform_family not in {"linux", "windows"}:
        raise QualificationError("unreviewed-platform-family")
    backend = profile.get("backend")
    if backend not in {"cpu", *ACCELERATED_BACKENDS}:
        raise QualificationError("invalid-qualification-matrix")
    for value in (system_memory_gib, usable_gpu_memory_gib):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or not 0 <= float(value) <= 1024
        ):
            raise QualificationError("invalid-memory-measurement")
    if (
        system_memory_gib < profile["minimumSystemMemoryGiB"]
        or usable_gpu_memory_gib < profile["minimumUsableGpuMemoryGiB"]
        or (backend == "cpu" and usable_gpu_memory_gib != 0)
    ):
        raise QualificationError("profile-memory-requirement-not-met")
    try:
        MODEL_RUNNER.verify_provider(checked_origin, model, provider_version)
    except MODEL_RUNNER.ValidationError as error:
        raise QualificationError(str(error)) from error

    started = time.monotonic()
    rates: list[float] = []
    peak_vram = 0
    unloads = 0
    output_tokens = 0
    for _ in range(repetitions):
        sample_error: Exception | None = None
        try:
            generated = MODEL_RUNNER._json_request(
                checked_origin,
                "/api/generate",
                {
                    "model": model["name"],
                    "prompt": TASKS[capability]["prompt"],
                    "stream": False,
                    "think": False,
                    "keep_alive": "5m",
                    "options": {"temperature": 0, "seed": 42, "num_predict": 96},
                },
                timeout=600,
            )
            _check_response(capability, generated.get("response"))
            _, tokens, rate = MODEL_RUNNER._validate_generate(generated)
            output_tokens += tokens
            rates.append(rate)
            peak_vram = max(
                peak_vram,
                MODEL_RUNNER._verify_residency(checked_origin, model, backend),
            )
        except (QualificationError, MODEL_RUNNER.ValidationError) as error:
            sample_error = error
        try:
            MODEL_RUNNER._unload(checked_origin, model)
            unloads += 1
        except MODEL_RUNNER.ValidationError as unload_error:
            if sample_error is not None:
                raise QualificationError(
                    "task-check-failed-and-unload-unverified"
                ) from sample_error
            raise QualificationError(str(unload_error)) from unload_error
        if sample_error is not None:
            raise QualificationError(str(sample_error)) from sample_error
    if backend == "cpu" and peak_vram != 0:
        raise QualificationError("cpu-cell-used-gpu")
    if backend in ACCELERATED_BACKENDS and peak_vram <= 0:
        raise QualificationError(f"{backend}-residency-not-observed")
    minimum_free_gpu_memory_gib = profile.get("minimumFreeGpuMemoryGiB", 0)
    if (
        isinstance(minimum_free_gpu_memory_gib, bool)
        or not isinstance(minimum_free_gpu_memory_gib, (int, float))
        or not 0 <= minimum_free_gpu_memory_gib <= usable_gpu_memory_gib
    ):
        raise QualificationError("invalid-qualification-matrix")
    if (
        backend in ACCELERATED_BACKENDS
        and usable_gpu_memory_gib * GIB_BYTES - peak_vram
        < minimum_free_gpu_memory_gib * GIB_BYTES
    ):
        raise QualificationError("insufficient-gpu-headroom")
    return {
        "schemaVersion": 1,
        "kind": "alpha2-model-task-qualification-evidence",
        "outcome": "passed",
        "errorCode": None,
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "durationSeconds": round(time.monotonic() - started, 3),
        "metrics": {
            "samplesPassed": repetitions,
            "unloadPasses": unloads,
            "outputTokens": output_tokens,
            "tokensPerSecond": round(sum(rates) / len(rates), 3),
            "peakGpuMemoryBytes": peak_vram,
        },
        "evidence": {
            "qualificationInventoryCanonicalSha256": inventory_sha,
            "qualificationMatrixCanonicalSha256": matrix_sha,
            "modelId": model_id,
            "manifestDigest": model["manifestDigest"],
            "capability": capability,
            "check": TASKS[capability]["check"],
            "profileId": profile_id,
            "platformFamily": platform_family,
            "operatingSystemId": operating_system_id,
            "backendMode": backend,
            "provider": "ollama",
            "providerVersion": provider_version,
            "systemMemoryGiB": system_memory_gib,
            "usableGpuMemoryGiB": usable_gpu_memory_gib,
            "automaticPromotionAllowed": False,
        },
    }


def _failure_result(args: argparse.Namespace, error: QualificationError) -> dict[str, Any]:
    error_code = str(error)
    if not re.fullmatch(r"[a-z0-9-]{1,96}", error_code):
        error_code = "qualification-failed"
    evidence: dict[str, Any] = {"automaticPromotionAllowed": False}
    if isinstance(args.capability, str) and args.capability in TASKS:
        evidence["capability"] = args.capability
        evidence["check"] = TASKS[args.capability]["check"]
    if isinstance(args.operating_system_id, str) and MODEL_RUNNER.SAFE_PROFILE.fullmatch(
        args.operating_system_id
    ):
        evidence["operatingSystemId"] = args.operating_system_id
    if args.platform_family in {"linux", "windows"}:
        evidence["platformFamily"] = args.platform_family
    if isinstance(args.profile_id, str) and MODEL_RUNNER.SAFE_PROFILE.fullmatch(
        args.profile_id
    ):
        evidence["profileId"] = args.profile_id
    try:
        model, inventory_sha, provider_version = (
            MODEL_RUNNER.reviewed_qualification_model(args.model_id)
        )
        profile, matrix_sha = _review_matrix(args.model_id, args.profile_id)
    except (QualificationError, MODEL_RUNNER.ValidationError):
        pass
    else:
        evidence.update(
            {
                "qualificationInventoryCanonicalSha256": inventory_sha,
                "qualificationMatrixCanonicalSha256": matrix_sha,
                "modelId": model["id"],
                "manifestDigest": model["manifestDigest"],
                "profileId": args.profile_id,
                "backendMode": profile["backend"],
                "provider": "ollama",
                "providerVersion": provider_version,
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "alpha2-model-task-qualification-evidence",
        "outcome": "failed",
        "errorCode": error_code,
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--capability", choices=sorted(TASKS), required=True)
    parser.add_argument("--profile-id", required=True)
    parser.add_argument("--operating-system-id", required=True)
    parser.add_argument(
        "--platform-family", choices=("linux", "windows"), default="linux"
    )
    parser.add_argument("--system-memory-gib", type=float, required=True)
    parser.add_argument("--usable-gpu-memory-gib", type=float, required=True)
    args = parser.parse_args()
    try:
        result = run_qualification(
            origin=args.origin,
            model_id=args.model_id,
            capability=args.capability,
            profile_id=args.profile_id,
            operating_system_id=args.operating_system_id,
            system_memory_gib=args.system_memory_gib,
            usable_gpu_memory_gib=args.usable_gpu_memory_gib,
            platform_family=args.platform_family,
        )
    except QualificationError as error:
        print(json.dumps(_failure_result(args, error), indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
