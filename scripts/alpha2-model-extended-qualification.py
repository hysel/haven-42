#!/usr/bin/env python3
"""Run one sanitized, fail-closed extended model capability check."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import time
from typing import Any
import urllib.error
import urllib.request
import zlib


ROOT = Path(__file__).resolve().parent.parent
MODEL_RUNNER_PATH = ROOT / "scripts/alpha2-linux-model-validation.py"
MATRIX_PATH = ROOT / "config/alpha-2-model-qualification-matrix.json"
INVENTORY_PATH = ROOT / "config/alpha-2-model-version-inventory.json"
CAPABILITIES = {
    "coding",
    "tools",
    "thinking",
    "vision",
    "long-context",
    "failure-recovery",
}
ACCELERATED_BACKENDS = {"cuda", "rocm", "vulkan"}
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class ExtendedQualificationError(ValueError):
    """The reviewed extended capability check failed closed."""


def _load_model_runner():
    if (
        MODEL_RUNNER_PATH.is_symlink()
        or not MODEL_RUNNER_PATH.is_file()
        or MODEL_RUNNER_PATH.stat().st_size > 2 * 1024 * 1024
    ):
        raise ExtendedQualificationError("unsafe-model-runner")
    specification = importlib.util.spec_from_file_location(
        "alpha2_model_validation_for_extended_qualification", MODEL_RUNNER_PATH
    )
    if specification is None or specification.loader is None:
        raise ExtendedQualificationError("invalid-model-runner")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


MODEL_RUNNER = _load_model_runner()


def _load(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise ExtendedQualificationError("unsafe-qualification-metadata")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ExtendedQualificationError("invalid-qualification-metadata") from error
    if not isinstance(value, dict):
        raise ExtendedQualificationError("invalid-qualification-metadata")
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _review_cell(model_id: str, profile_id: str, capability: str) -> tuple[dict[str, Any], str]:
    inventory = _load(INVENTORY_PATH)
    matrix = _load(MATRIX_PATH)
    if matrix.get("inventoryBinding") != {
        "path": "config/alpha-2-model-version-inventory.json",
        "canonicalSha256": _canonical_sha256(inventory),
    }:
        raise ExtendedQualificationError("invalid-qualification-matrix")
    candidates = [
        item for item in matrix.get("candidates", [])
        if isinstance(item, dict) and item.get("modelId") == model_id
    ]
    profiles = [
        item for item in matrix.get("profiles", [])
        if isinstance(item, dict) and item.get("id") == profile_id
    ]
    if len(candidates) != 1 or len(profiles) != 1:
        raise ExtendedQualificationError("unreviewed-qualification-cell")
    candidate = candidates[0]
    checks = candidate.get("plannedTest", {}).get("capabilityChecks", [])
    if (
        candidate.get("state") != "ready-for-qualification"
        or profile_id not in candidate.get("requiredProfiles", [])
        or capability not in checks
    ):
        raise ExtendedQualificationError("unreviewed-capability-cell")
    return profiles[0], _canonical_sha256(matrix)


def _request(origin: str, route: str, body: dict[str, Any], timeout: float = 600) -> dict[str, Any]:
    if route not in {"/api/chat", "/api/generate"}:
        raise ExtendedQualificationError("invalid-provider-route")
    encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        origin + route,
        data=encoded,
        headers={"Content-Type": "application/json", "User-Agent": "Haven42-Alpha2-Extended/1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.URLError) as error:
        raise ExtendedQualificationError("provider-request-failed") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ExtendedQualificationError("provider-response-too-large")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ExtendedQualificationError("invalid-provider-response") from error
    if not isinstance(value, dict):
        raise ExtendedQualificationError("invalid-provider-response")
    return value


def _png(width: int, height: int, rgb: tuple[int, int, int]) -> str:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        )

    rows = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    raw = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, 9))
        + chunk(b"IEND", b"")
    )
    return base64.b64encode(raw).decode("ascii")


def _message_content(value: dict[str, Any]) -> str:
    message = value.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or len(content.encode("utf-8")) > 64 * 1024:
        raise ExtendedQualificationError("invalid-chat-content")
    return content.strip()


def _run_capability(origin: str, model_name: str, capability: str) -> dict[str, Any]:
    common = {"model": model_name, "stream": False, "keep_alive": "5m"}
    if capability == "coding":
        value = _request(origin, "/api/chat", {
            **common,
            "messages": [{"role": "user", "content": (
                "Return only JSON with keys language and code. language must be python. "
                "code must define add(a, b) and return a + b without imports."
            )}],
            "format": "json",
            "options": {"temperature": 0, "seed": 42, "num_predict": 160},
        })
        try:
            result = json.loads(_message_content(value))
        except json.JSONDecodeError as error:
            raise ExtendedQualificationError("coding-json-invalid") from error
        if (
            not isinstance(result, dict)
            or set(result) != {"language", "code"}
            or result["language"] != "python"
            or not isinstance(result["code"], str)
            or "def add(a, b):" not in result["code"]
            or "return a + b" not in result["code"]
            or "import " in result["code"]
        ):
            raise ExtendedQualificationError("coding-contract-failed")
        return {"structuredOutput": True}
    if capability == "tools":
        value = _request(origin, "/api/chat", {
            **common,
            "messages": [{"role": "user", "content": (
                "Use lookup_status exactly once for item alpha. Do not answer directly."
            )}],
            "tools": [{"type": "function", "function": {
                "name": "lookup_status",
                "description": "Look up the status of one synthetic item.",
                "parameters": {"type": "object", "properties": {
                    "item": {"type": "string"}
                }, "required": ["item"], "additionalProperties": False},
            }}],
            "options": {"temperature": 0, "seed": 42, "num_predict": 128},
        })
        message = value.get("message")
        calls = message.get("tool_calls") if isinstance(message, dict) else None
        if not isinstance(calls, list) or len(calls) != 1:
            raise ExtendedQualificationError("tool-call-count-failed")
        function = calls[0].get("function") if isinstance(calls[0], dict) else None
        if (
            not isinstance(function, dict)
            or function.get("name") != "lookup_status"
            or function.get("arguments") != {"item": "alpha"}
        ):
            raise ExtendedQualificationError("tool-call-contract-failed")
        return {"toolCallCount": 1, "toolArgumentsValidated": True}
    if capability == "thinking":
        value = _request(origin, "/api/generate", {
            **common,
            "prompt": "What is six multiplied by seven? Reply with exactly 42.",
            "think": True,
            "options": {"temperature": 0, "seed": 42, "num_predict": 128},
        })
        response = value.get("response")
        thinking = value.get("thinking")
        if not isinstance(response, str) or response.strip() != "42":
            raise ExtendedQualificationError("thinking-answer-contract-failed")
        if not isinstance(thinking, str) or not thinking.strip():
            raise ExtendedQualificationError("thinking-trace-missing")
        return {"thinkingObserved": True}
    if capability == "vision":
        results = []
        for color, rgb in (("RED", (255, 0, 0)), ("BLUE", (0, 0, 255))):
            value = _request(origin, "/api/chat", {
                **common,
                "messages": [{"role": "user", "content": (
                    "Identify the image's single solid color. Reply with only its uppercase basic color name."
                ), "images": [_png(48, 48, rgb)]}],
                "options": {"temperature": 0, "seed": 42, "num_predict": 24},
            })
            results.append(_message_content(value) == color)
        if results != [True, True]:
            raise ExtendedQualificationError("vision-grounding-contract-failed")
        return {"syntheticImages": 2, "groundedAnswers": 2}
    if capability == "long-context":
        expected = "HAVEN42_BEGIN|HAVEN42_MIDDLE|HAVEN42_END"
        filler = "local context verification filler " * 650
        prompt = (
            "Remember these three exact codes and return them at the end in the "
            "same order, joined by vertical bars and with no other text. "
            "First code: HAVEN42_BEGIN. " + filler
            + " Middle code: HAVEN42_MIDDLE. " + filler
            + " Final code: HAVEN42_END. Return the three codes now."
        )
        value = _request(origin, "/api/generate", {
            **common,
            "prompt": prompt,
            "think": False,
            "options": {
                "temperature": 0,
                "seed": 42,
                "num_ctx": 16384,
                "num_predict": 64,
            },
        })
        if value.get("response", "").strip() != expected:
            raise ExtendedQualificationError("long-context-recall-failed")
        return {
            "inputCharacters": len(prompt),
            "contextWindowRequested": 16384,
            "sentinelsRecalled": 3,
        }
    if capability == "failure-recovery":
        timed_out = False
        try:
            _request(origin, "/api/generate", {
                **common,
                "prompt": "Write a long numbered list of testing considerations.",
                "options": {"temperature": 0, "seed": 42, "num_predict": 1024},
            }, timeout=0.001)
        except ExtendedQualificationError as error:
            if str(error) != "provider-request-failed":
                raise
            timed_out = True
        if not timed_out:
            raise ExtendedQualificationError("expected-timeout-not-observed")
        time.sleep(2)
        MODEL_RUNNER._unload(origin, {"name": model_name})
        value = _request(origin, "/api/generate", {
            **common,
            "prompt": "Reply with exactly HAVEN42_RECOVERED and nothing else.",
            "think": False,
            "options": {"temperature": 0, "seed": 42, "num_predict": 32},
        })
        if value.get("response", "").strip() != "HAVEN42_RECOVERED":
            raise ExtendedQualificationError("post-timeout-recovery-failed")
        return {"timeoutObserved": True, "postTimeoutRequestPassed": True}
    raise ExtendedQualificationError("unreviewed-capability")


def run_qualification(
    *, origin: str, model_id: str, capability: str, profile_id: str,
    operating_system_id: str, platform_family: str, system_memory_gib: float,
    usable_gpu_memory_gib: float,
) -> dict[str, Any]:
    if capability not in CAPABILITIES:
        raise ExtendedQualificationError("unreviewed-capability")
    profile, matrix_sha = _review_cell(model_id, profile_id, capability)
    checked_origin = MODEL_RUNNER.validate_origin(origin)
    model, inventory_sha, provider_version = MODEL_RUNNER.reviewed_qualification_model(model_id)
    if platform_family not in {"linux", "windows"}:
        raise ExtendedQualificationError("unreviewed-platform-family")
    if not MODEL_RUNNER.SAFE_PROFILE.fullmatch(operating_system_id):
        raise ExtendedQualificationError("invalid-operating-system-id")
    for value in (system_memory_gib, usable_gpu_memory_gib):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ExtendedQualificationError("invalid-memory-measurement")
    backend = profile.get("backend")
    if (
        backend not in {"cpu", *ACCELERATED_BACKENDS}
        or system_memory_gib < profile.get("minimumSystemMemoryGiB", math.inf)
        or usable_gpu_memory_gib < profile.get("minimumUsableGpuMemoryGiB", math.inf)
    ):
        raise ExtendedQualificationError("profile-memory-requirement-not-met")
    MODEL_RUNNER.verify_provider(checked_origin, model, provider_version)
    started = time.monotonic()
    sample_error: Exception | None = None
    details: dict[str, Any] = {}
    peak_vram = 0
    try:
        details = _run_capability(checked_origin, model["name"], capability)
        peak_vram = MODEL_RUNNER._verify_residency(checked_origin, model, backend)
    except (ExtendedQualificationError, MODEL_RUNNER.ValidationError) as error:
        sample_error = error
    try:
        MODEL_RUNNER._unload(checked_origin, model)
    except MODEL_RUNNER.ValidationError as error:
        raise ExtendedQualificationError("unload-unverified") from error
    if sample_error is not None:
        raise ExtendedQualificationError(str(sample_error)) from sample_error
    if backend in ACCELERATED_BACKENDS and peak_vram <= 0:
        raise ExtendedQualificationError(f"{backend}-residency-not-observed")
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-extended-model-qualification",
        "modelId": model_id,
        "capability": capability,
        "outcome": "passed",
        "platformFamily": platform_family,
        "operatingSystemId": operating_system_id,
        "backend": backend,
        "profileId": profile_id,
        "provider": "ollama",
        "providerVersion": provider_version,
        "manifestDigest": model["manifestDigest"],
        "systemMemoryGiB": system_memory_gib,
        "usableGpuMemoryGiB": usable_gpu_memory_gib,
        "inventorySha256": inventory_sha,
        "matrixSha256": matrix_sha,
        "peakObservedGpuResidencyBytes": peak_vram,
        "durationMilliseconds": round((time.monotonic() - started) * 1000),
        "details": details,
        "rawPromptRecorded": False,
        "rawResponseRecorded": False,
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "automaticPromotionAllowed": False,
    }


def _failed_result(args: argparse.Namespace, error_code: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-extended-model-qualification",
        "modelId": args.model_id,
        "capability": args.capability,
        "outcome": "failed",
        "errorCode": error_code,
        "platformFamily": args.platform_family,
        "operatingSystemId": args.operating_system_id,
        "profileId": args.profile_id,
        "systemMemoryGiB": args.system_memory_gib,
        "usableGpuMemoryGiB": args.usable_gpu_memory_gib,
        "rawPromptRecorded": False,
        "rawResponseRecorded": False,
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "automaticPromotionAllowed": False,
        "bindingComplete": False,
    }
    try:
        profile, matrix_sha = _review_cell(
            args.model_id, args.profile_id, args.capability
        )
        model, inventory_sha, provider_version = (
            MODEL_RUNNER.reviewed_qualification_model(args.model_id)
        )
    except (ExtendedQualificationError, MODEL_RUNNER.ValidationError):
        return result
    result.update({
        "backend": profile["backend"],
        "provider": "ollama",
        "providerVersion": provider_version,
        "manifestDigest": model["manifestDigest"],
        "inventorySha256": inventory_sha,
        "matrixSha256": matrix_sha,
        "bindingComplete": True,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--capability", required=True, choices=sorted(CAPABILITIES))
    parser.add_argument("--profile-id", required=True)
    parser.add_argument("--operating-system-id", required=True)
    parser.add_argument("--platform-family", required=True, choices=("linux", "windows"))
    parser.add_argument("--system-memory-gib", required=True, type=float)
    parser.add_argument("--usable-gpu-memory-gib", required=True, type=float)
    args = parser.parse_args()
    try:
        result = run_qualification(
            origin=args.origin,
            model_id=args.model_id,
            capability=args.capability,
            profile_id=args.profile_id,
            operating_system_id=args.operating_system_id,
            platform_family=args.platform_family,
            system_memory_gib=args.system_memory_gib,
            usable_gpu_memory_gib=args.usable_gpu_memory_gib,
        )
    except (ExtendedQualificationError, MODEL_RUNNER.ValidationError) as error:
        print(json.dumps(_failed_result(args, str(error)), sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
