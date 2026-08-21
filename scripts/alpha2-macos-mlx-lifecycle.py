#!/usr/bin/env python3
"""Run one sanitized, offline MLX lifecycle cell on physical Apple Silicon."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time


EXPECTED_PACKAGES = {"mlx-lm": "0.31.3", "mlx": "0.32.1", "mlx-metal": "0.32.1"}
MODEL_ID = "mlx-community/Qwen3.5-0.8B-OptiQ-4bit@ef605869"
RATE = re.compile(
    r"Generation:\s+(?:[0-9]+(?:\.[0-9]+)?\s+tokens,\s+)?"
    r"([0-9]+(?:\.[0-9]+)?)\s+tokens-per-sec"
)
MEMORY = re.compile(r"Peak memory:\s+([0-9]+(?:\.[0-9]+)?) GB")


class LifecycleError(RuntimeError):
    """Raised when an MLX lifecycle precondition or result is unsafe."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()


def verified_manifest(manifest: Path, root: Path, suffix: str | None = None) -> dict[str, object]:
    if not manifest.is_file() or manifest.is_symlink() or not root.is_dir() or root.is_symlink():
        raise LifecycleError("invalid-checksum-boundary")
    resolved_root = root.resolve()
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise LifecycleError("invalid-checksum-manifest")
        path = Path(match.group(2)).resolve()
        try:
            relative = path.relative_to(resolved_root).as_posix()
        except ValueError as error:
            raise LifecycleError("checksum-path-escaped-root") from error
        if relative == manifest.name and resolved_root == manifest.parent.resolve():
            continue
        if relative in seen or not path.is_file() or path.is_symlink():
            raise LifecycleError("invalid-checksum-entry")
        if suffix is not None and not relative.endswith(suffix):
            raise LifecycleError("unexpected-checksum-entry")
        if sha256(path) != match.group(1):
            raise LifecycleError("checksum-mismatch")
        seen.add(relative)
        records.append({
            "path": relative,
            "sha256": match.group(1),
            "sizeBytes": path.stat().st_size,
        })
    if not records:
        raise LifecycleError("empty-checksum-manifest")
    records.sort(key=lambda item: str(item["path"]))
    actual_files: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise LifecycleError("artifact-links-are-not-allowed")
        if path.is_file() and path.resolve() != manifest.resolve():
            relative = path.resolve().relative_to(resolved_root).as_posix()
            # Hugging Face's downloader leaves transport-only lock and
            # metadata records here.  MLX does not load this directory, and
            # its contents can include mutable download state, so it is kept
            # outside the immutable runtime artifact inventory.
            if relative.startswith(".cache/huggingface/"):
                continue
            actual_files.add(relative)
    if actual_files != seen:
        raise LifecycleError("checksum-inventory-mismatch")
    return {
        "fileCount": len(records),
        "totalBytes": sum(int(item["sizeBytes"]) for item in records),
        "canonicalSha256": canonical_sha256(records),
    }


def safe_environment(home: Path) -> dict[str, str]:
    result = {
        "HOME": str(home),
        "PATH": "/usr/bin:/bin",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "PYTHONNOUSERSITE": "1",
    }
    for name in ("TMPDIR", "SYSTEM_VERSION_COMPAT"):
        if name in os.environ:
            result[name] = os.environ[name]
    return result


def package_versions(python: Path, environment: dict[str, str]) -> dict[str, object]:
    code = (
        "import importlib.metadata as m,json,platform;"
        "print(json.dumps({'pythonVersion':platform.python_version(),"
        "'packages':{n:m.version(n) for n in "
        "('mlx-lm','mlx','mlx-metal')}},sort_keys=True))"
    )
    try:
        process = subprocess.run(
            [str(python), "-I", "-c", code], capture_output=True, text=True,
            timeout=30, shell=False, env=environment,
        )
        value = json.loads(process.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        raise LifecycleError("package-version-probe-failed") from error
    if (
        process.returncode != 0
        or value.get("pythonVersion") != "3.14.6"
        or value.get("packages") != EXPECTED_PACKAGES
    ):
        raise LifecycleError("package-version-mismatch")
    return value


def hardware_profile() -> dict[str, object]:
    values: list[str] = []
    for name in ("hw.memsize", "machdep.cpu.brand_string"):
        try:
            process = subprocess.run(
                ["/usr/sbin/sysctl", "-n", name], capture_output=True, text=True,
                timeout=10, shell=False, env={"PATH": "/usr/bin:/bin"},
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise LifecycleError("hardware-profile-probe-failed") from error
        if process.returncode != 0:
            raise LifecycleError("hardware-profile-probe-failed")
        values.append(process.stdout.strip())
    if values != [str(16 * 1024**3), "Apple M4"]:
        raise LifecycleError("exact-apple-m4-16gib-profile-required")
    return {
        "platformFamily": "macos", "architecture": "arm64",
        "acceleratorFamily": "Apple M4", "systemMemoryGiB": 16,
    }


def run_generation(
    python: Path,
    model: Path,
    environment: dict[str, str],
    timeout: float,
) -> dict[str, object]:
    command = [
        str(python), "-I", "-m", "mlx_lm", "generate",
        "--model", str(model),
        "--prompt", "Reply with one short sentence containing the token MLX_M4_OK.",
        "--max-tokens", "32", "--temp", "0", "--seed", "42",
        "--chat-template-config", '{"enable_thinking":false}',
        "--verbose", "True",
    ]
    started = time.monotonic()
    try:
        process = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout,
            shell=False, env=environment,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timed-out", "durationSeconds": round(time.monotonic() - started, 3),
            "processExited": True, "responseRetained": False,
        }
    except OSError as error:
        raise LifecycleError("generation-process-failed") from error
    output = process.stdout
    rate = RATE.search(output)
    memory = MEMORY.search(output)
    return {
        "status": "passed" if process.returncode == 0 else "failed",
        "durationSeconds": round(time.monotonic() - started, 3),
        "exitCode": process.returncode,
        "outputSha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "outputCharacters": len(output),
        "requiredTokenObserved": "MLX_M4_OK" in output,
        "generationTokensPerSecond": float(rate.group(1)) if rate else 0.0,
        "peakMetalMemoryGiB": float(memory.group(1)) if memory else 0.0,
        "processExited": True,
        "responseRetained": False,
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise LifecycleError("physical-apple-silicon-required")
    python = Path(args.python).expanduser().resolve()
    model = Path(args.model_directory).expanduser().resolve()
    model_manifest = Path(args.model_manifest).expanduser().resolve()
    wheel_manifest = Path(args.wheel_manifest).expanduser().resolve()
    if not python.is_file() or python.is_symlink() or not os.access(python, os.X_OK):
        raise LifecycleError("invalid-python-runtime")
    environment = safe_environment(Path.home())
    hardware = hardware_profile()
    versions = package_versions(python, environment)
    model_evidence = verified_manifest(model_manifest, model)
    wheel_evidence = verified_manifest(wheel_manifest, wheel_manifest.parent / "wheelhouse", ".whl")
    first = run_generation(python, model, environment, 600)
    forced_timeout = run_generation(python, model, environment, 0.01)
    recovery = run_generation(python, model, environment, 600)
    passed = all((
        first.get("status") == "passed",
        first.get("requiredTokenObserved") is True,
        float(first.get("generationTokensPerSecond", 0)) > 0,
        float(first.get("peakMetalMemoryGiB", 0)) > 0,
        forced_timeout.get("status") == "timed-out",
        recovery.get("status") == "passed",
        recovery.get("requiredTokenObserved") is True,
        float(recovery.get("generationTokensPerSecond", 0)) > 0,
        float(recovery.get("peakMetalMemoryGiB", 0)) > 0,
    ))
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-mlx-lifecycle-result",
        "observedAtUtc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "passed" if passed else "failed",
        "hardwareProfile": hardware,
        "runtime": {
            "pythonVersion": versions["pythonVersion"],
            "packages": versions["packages"],
            "wheelhouse": wheel_evidence,
            "globalPythonRequiredForFuturePackage": False,
            "productionServerAdmitted": False,
        },
        "model": {"id": MODEL_ID, **model_evidence},
        "tests": {
            "offlineOnly": True, "firstGeneration": first,
            "forcedTimeout": forced_timeout, "recoveryGeneration": recovery,
            "listenerOpened": False, "processResidueRetained": False,
        },
        "authority": {
            "runtimeAdmissionGranted": False, "packageAdmissionGranted": False,
            "automaticSelectionAllowed": False, "supportLabelChangeAllowed": False,
        },
        "privacy": {
            "rawPromptOrResponseRetained": False, "privatePathRetained": False,
            "privateIdentityRetained": False, "networkEndpointRetained": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--model-directory", required=True)
    parser.add_argument("--model-manifest", required=True)
    parser.add_argument("--wheel-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    if output.exists() or output.is_symlink():
        parser.error("output-already-exists")
    try:
        result = run(args)
    except LifecycleError as error:
        parser.error(str(error))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
