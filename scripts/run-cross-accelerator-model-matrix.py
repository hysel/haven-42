#!/usr/bin/env python3
"""Run a fail-closed, development-only llama.cpp accelerator matrix.

The runner never downloads artifacts, opens listeners, invokes a shell, or
records raw prompts/responses. Model bytes and runtime binaries must be staged
out of band and are verified before any executable is started.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROFILE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
OFFLOAD_RE = re.compile(r"offloaded\s+(\d+)/(\d+)\s+layers\s+to GPU", re.I)
EXPECTED_BACKEND = {
    "cuda": re.compile(r"(?:CUDA|NVIDIA)", re.I),
    "hip": re.compile(r"(?:HIP|ROCm|AMD Radeon)", re.I),
}
ALLOWED_TESTS = {
    "benchmark",
    "bounded-exact-output",
    "context-4k",
    "context-8k",
    "patch",
    "tool-call",
    "vision",
}
EXECUTION_BOUNDS = {
    "contextTokens": (512, 32768),
    "gpuLayers": (1, 999),
    "promptTokens": (1, 4096),
    "generatedTokens": (1, 4096),
    "benchmarkRepetitions": (1, 10),
    "timeoutSeconds": (10, 1800),
    "minimumFreeBytesBeforeStaging": (0, 2**50),
}
REQUIRED_SECURITY_POLICY = {
    "networkUseDuringInference": False,
    "listenersAllowed": False,
    "shellExecutionAllowed": False,
    "rawPromptsOrResponsesInSummary": False,
    "absoluteOrParentRelativeArtifactPathsAllowed": False,
    "symlinkedArtifactsAllowed": False,
    "hashVerificationRequired": True,
    "fullGpuOffloadRequired": True,
}
EXACT_MARKER = "HAVEN42_MATRIX_OK"
EXACT_PROMPT = (
    "Reply with exactly HAVEN42_MATRIX_OK and nothing else. "
    "Do not explain your answer."
)


class MatrixError(RuntimeError):
    """A controlled validation failure."""


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MatrixError(f"Cannot read manifest: {exc}") from exc
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schemaVersion") != 1:
        raise MatrixError("Unsupported manifest schemaVersion.")
    runtime = manifest.get("runtime")
    execution = manifest.get("execution")
    security = manifest.get("security")
    models = manifest.get("models")
    if (
        not isinstance(runtime, dict)
        or not isinstance(execution, dict)
        or not isinstance(security, dict)
    ):
        raise MatrixError("Manifest runtime, execution, and security objects are required.")
    if not isinstance(models, list) or not models:
        raise MatrixError("Manifest models must be a non-empty array.")
    commit = runtime.get("commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise MatrixError("Runtime commit must be a full lowercase Git SHA.")
    if runtime.get("project") != "ggml-org/llama.cpp":
        raise MatrixError("Runtime project must be the reviewed llama.cpp source.")
    if not PROFILE_RE.fullmatch(str(runtime.get("buildTag", ""))):
        raise MatrixError("Runtime buildTag must be a safe label.")
    build_number = runtime.get("expectedBuildNumber")
    if not isinstance(build_number, int) or isinstance(build_number, bool):
        raise MatrixError("Runtime expectedBuildNumber must be an integer.")
    if not 1 <= build_number <= 10_000_000:
        raise MatrixError("Runtime expectedBuildNumber is outside its allowed range.")
    if set(execution) != set(EXECUTION_BOUNDS):
        raise MatrixError("Manifest execution fields do not match the reviewed schema.")
    for field, (minimum, maximum) in EXECUTION_BOUNDS.items():
        value = execution[field]
        if not isinstance(value, int) or isinstance(value, bool):
            raise MatrixError(f"Execution {field} must be an integer.")
        if not minimum <= value <= maximum:
            raise MatrixError(f"Execution {field} is outside its allowed range.")
    if security != REQUIRED_SECURITY_POLICY:
        raise MatrixError("Manifest security policy must match the fail-closed baseline.")
    ids: set[str] = set()
    for model in models:
        if not isinstance(model, dict) or not PROFILE_RE.fullmatch(model.get("id", "")):
            raise MatrixError("Every model needs a safe, unique id.")
        if model["id"] in ids:
            raise MatrixError(f"Duplicate model id: {model['id']}")
        ids.add(model["id"])
        validate_artifact(model.get("artifact"), f"{model['id']} artifact")
        if "projector" in model:
            validate_artifact(model["projector"], f"{model['id']} projector")
        tests = model.get("tests")
        if (
            not isinstance(tests, list)
            or not tests
            or any(not isinstance(test, str) for test in tests)
            or len(tests) != len(set(tests))
            or not set(tests).issubset(ALLOWED_TESTS)
            or "benchmark" not in tests
            or "bounded-exact-output" not in tests
        ):
            raise MatrixError(f"{model['id']} tests do not match the reviewed allowlist.")
        if "vision" in tests and "projector" not in model:
            raise MatrixError(f"{model['id']} vision test requires a pinned projector.")


def validate_artifact(artifact: Any, label: str) -> None:
    if not isinstance(artifact, dict):
        raise MatrixError(f"{label} is required.")
    relative = Path(str(artifact.get("path", "")))
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise MatrixError(f"{label} path must be a safe relative path.")
    if any(part in ("", ".") for part in relative.parts):
        raise MatrixError(f"{label} path contains an empty or dot component.")
    if relative.suffix.lower() != ".gguf":
        raise MatrixError(f"{label} must be a GGUF file.")
    size = artifact.get("sizeBytes")
    digest = artifact.get("sha256", "")
    if not isinstance(size, int) or size <= 0:
        raise MatrixError(f"{label} sizeBytes must be positive.")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise MatrixError(f"{label} sha256 must be lowercase SHA-256.")


def resolve_beneath(root: Path, relative: str, label: str) -> Path:
    root = root.resolve(strict=True)
    candidate = root.joinpath(*Path(relative).parts)
    if candidate.is_symlink():
        raise MatrixError(f"{label} must not be a symlink.")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise MatrixError(f"{label} is missing or outside its approved root.") from exc
    if not resolved.is_file():
        raise MatrixError(f"{label} must be a regular file.")
    return resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact(root: Path, artifact: dict[str, Any], label: str) -> Path:
    path = resolve_beneath(root, artifact["path"], label)
    if path.stat().st_size != artifact["sizeBytes"]:
        raise MatrixError(f"{label} size does not match the manifest.")
    if sha256_file(path) != artifact["sha256"]:
        raise MatrixError(f"{label} SHA-256 does not match the manifest.")
    return path


def runtime_binary(runtime_root: Path, stem: str) -> Path:
    names = (f"{stem}.exe", stem) if os.name == "nt" else (stem, f"{stem}.exe")
    for name in names:
        candidate = runtime_root / name
        if candidate.exists():
            return resolve_beneath(runtime_root, name, f"runtime binary {stem}")
    raise MatrixError(f"Required runtime binary is missing: {stem}")


def run_process(command: list[str], timeout: int, environment: dict[str, str]) -> dict[str, Any]:
    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise MatrixError(f"Runtime command exceeded the {timeout}-second limit.") from exc
    return {
        "returnCode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "durationSeconds": round(time.monotonic() - started, 3),
    }


def safe_environment(
    runtime_root: Path,
    backend: str,
    device: str | None,
    library_paths: list[Path],
) -> dict[str, str]:
    allowed = ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR")
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    trusted_libraries = [runtime_root]
    for path in library_paths:
        if path.is_symlink():
            raise MatrixError("Library paths must not be symlinks.")
        resolved = path.resolve(strict=True)
        if not resolved.is_dir():
            raise MatrixError("Every library path must be a directory.")
        trusted_libraries.append(resolved)
    if os.name == "nt":
        windows = Path(environment.get("SYSTEMROOT", environment.get("WINDIR", "C:/Windows")))
        environment["PATH"] = os.pathsep.join(
            str(path) for path in (*trusted_libraries, windows / "System32", windows)
        )
    else:
        environment["PATH"] = "/usr/local/bin:/usr/bin:/bin"
        environment["LD_LIBRARY_PATH"] = os.pathsep.join(
            str(path) for path in trusted_libraries
        )
    if device is not None:
        if not re.fullmatch(r"\d{1,3}", device):
            raise MatrixError("Device must be a numeric accelerator index.")
        environment["CUDA_VISIBLE_DEVICES" if backend == "cuda" else "HIP_VISIBLE_DEVICES"] = device
    if backend == "cuda":
        environment["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    return environment


def parse_benchmark(stdout: str) -> dict[str, Any]:
    try:
        records = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise MatrixError("llama-bench did not return valid JSON.") from exc
    if not isinstance(records, list) or not records:
        raise MatrixError("llama-bench returned no benchmark records.")
    prompt = next((row for row in records if row.get("n_prompt", 0) > 0), None)
    generation = next((row for row in records if row.get("n_gen", 0) > 0), None)
    if not prompt or not generation:
        raise MatrixError("llama-bench omitted prompt or generation throughput.")
    return {
        "buildCommit": str(prompt.get("build_commit", "")),
        "buildNumber": prompt.get("build_number"),
        "backend": str(prompt.get("backends", "")),
        "gpu": str(prompt.get("gpu_info", "")),
        "modelType": str(prompt.get("model_type", "")),
        "modelParameters": prompt.get("model_n_params"),
        "promptTokensPerSecond": round(float(prompt["avg_ts"]), 3),
        "generationTokensPerSecond": round(float(generation["avg_ts"]), 3),
        "gpuLayers": prompt.get("n_gpu_layers"),
    }


def offload_result(log: str, backend: str) -> dict[str, Any]:
    matches = OFFLOAD_RE.findall(log)
    full = any(int(loaded) == int(total) and int(total) > 0 for loaded, total in matches)
    backend_seen = bool(EXPECTED_BACKEND[backend].search(log))
    return {
        "fullGpuOffload": full,
        "backendObserved": backend_seen,
        "offloadStatements": len(matches),
    }


def extract_cli_response(stdout: str) -> str:
    prompt_marker = f"> {EXACT_PROMPT}"
    marker_at = stdout.rfind(prompt_marker)
    if marker_at >= 0:
        response = stdout[marker_at + len(prompt_marker) :]
        footer = re.search(r"\n\[ Prompt:.*?\]\s*(?:\n|$)", response, flags=re.S)
        if footer:
            response = response[: footer.start()]
        return response.strip()
    return stdout.strip()


def exact_output_passed(stdout: str) -> bool:
    response = extract_cli_response(stdout)
    compact = re.sub(r"<think>.*?</think>", "", response, flags=re.I | re.S).strip()
    compact = re.sub(
        r"\[Start thinking\].*?\[End thinking\]",
        "",
        compact,
        flags=re.I | re.S,
    ).strip()
    compact = compact.strip("` \r\n\t\"'")
    return compact == EXACT_MARKER


def selected_models(manifest: dict[str, Any], requested: list[str]) -> list[dict[str, Any]]:
    by_id = {model["id"]: model for model in manifest["models"]}
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise MatrixError(f"Unknown model ids: {', '.join(unknown)}")
    return [by_id[model_id] for model_id in requested] if requested else manifest["models"]


def preflight(
    manifest: dict[str, Any],
    model_root: Path,
    runtime_root: Path,
    models: list[dict[str, Any]],
) -> dict[str, Any]:
    runtime_binary(runtime_root, "llama-cli")
    runtime_binary(runtime_root, "llama-bench")
    verified = []
    for model in models:
        verify_artifact(model_root, model["artifact"], f"{model['id']} artifact")
        if "projector" in model:
            verify_artifact(model_root, model["projector"], f"{model['id']} projector")
        verified.append(model["id"])
    runtime_drive = shutil.disk_usage(runtime_root)
    model_drive = shutil.disk_usage(model_root)
    minimum_free = manifest["execution"]["minimumFreeBytesBeforeStaging"]
    if runtime_drive.free < minimum_free or model_drive.free < minimum_free:
        raise MatrixError("Free space is below the manifest's required safety floor.")
    return {
        "runtimeCommit": manifest["runtime"]["commit"],
        "verifiedModels": verified,
        "runtimeFreeBytes": runtime_drive.free,
        "modelFreeBytes": model_drive.free,
    }


def execute_model(
    model: dict[str, Any],
    manifest: dict[str, Any],
    model_root: Path,
    runtime_root: Path,
    backend: str,
    device: str | None,
    library_paths: list[Path],
) -> dict[str, Any]:
    execution = manifest["execution"]
    timeout = int(execution["timeoutSeconds"])
    model_path = verify_artifact(model_root, model["artifact"], f"{model['id']} artifact")
    bench = runtime_binary(runtime_root, "llama-bench")
    cli = runtime_binary(runtime_root, "llama-cli")
    environment = safe_environment(runtime_root, backend, device, library_paths)
    benchmark = run_process(
        [
            str(bench),
            "-m",
            str(model_path),
            "-ngl",
            str(execution["gpuLayers"]),
            "-p",
            str(execution["promptTokens"]),
            "-n",
            str(execution["generatedTokens"]),
            "-r",
            str(execution["benchmarkRepetitions"]),
            "-o",
            "json",
            "--offline",
        ],
        timeout,
        environment,
    )
    if benchmark["returnCode"] != 0:
        raise MatrixError(f"{model['id']} benchmark failed.")
    metrics = parse_benchmark(benchmark["stdout"])
    expected_commit = manifest["runtime"]["commit"][: len(metrics["buildCommit"])]
    if metrics["buildCommit"] != expected_commit:
        raise MatrixError(f"{model['id']} used an unexpected llama.cpp commit.")
    if metrics["buildNumber"] != manifest["runtime"]["expectedBuildNumber"]:
        raise MatrixError(f"{model['id']} used an unexpected llama.cpp build number.")
    if not EXPECTED_BACKEND[backend].search(metrics["backend"] + " " + metrics["gpu"]):
        raise MatrixError(f"{model['id']} benchmark did not identify the requested backend.")
    exact = run_process(
        [
            str(cli),
            "-m",
            str(model_path),
            "-ngl",
            str(execution["gpuLayers"]),
            "-c",
            str(execution["contextTokens"]),
            "-n",
            "48",
            "--seed",
            "42",
            "--temp",
            "0",
            "--no-display-prompt",
            "--single-turn",
            "--simple-io",
            "--no-warmup",
            "--verbose",
            "--log-colors",
            "off",
            "--offline",
            "-p",
            EXACT_PROMPT,
        ],
        timeout,
        environment,
    )
    if exact["returnCode"] != 0:
        raise MatrixError(f"{model['id']} bounded inference failed.")
    offload = offload_result(exact["stderr"] + "\n" + exact["stdout"], backend)
    if not offload["fullGpuOffload"] or not offload["backendObserved"]:
        raise MatrixError(f"{model['id']} did not prove full requested-backend offload.")
    return {
        "id": model["id"],
        "artifactSha256": model["artifact"]["sha256"],
        "artifactBytes": model["artifact"]["sizeBytes"],
        "operational": "pass",
        "exactOutput": "pass" if exact_output_passed(exact["stdout"]) else "fail",
        "benchmark": metrics,
        "offload": offload,
        "benchmarkSeconds": benchmark["durationSeconds"],
        "inferenceSeconds": exact["durationSeconds"],
        "declaredTests": model["tests"],
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    requested_parent = path.parent.absolute()
    parent = requested_parent.resolve(strict=True)
    if os.path.normcase(str(parent)) != os.path.normcase(str(requested_parent)):
        raise MatrixError("Output parent directory must not use a symbolic link.")
    if path.exists() and path.is_symlink():
        raise MatrixError("Output summary must not be a symlink.")
    temporary = parent / f".{path.name}.{os.getpid()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    created = False
    try:
        descriptor = os.open(temporary, flags, 0o600)
        created = True
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(summary, indent=2) + "\n")
        os.replace(temporary, parent / path.name)
    except OSError as exc:
        if created:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise MatrixError("Cannot write the sanitized output summary safely.") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--backend", choices=sorted(EXPECTED_BACKEND), required=True)
    parser.add_argument("--hardware-profile", required=True)
    parser.add_argument("--device")
    parser.add_argument(
        "--library-path",
        action="append",
        type=Path,
        default=[],
        help="Explicit trusted runtime-library directory; may be repeated.",
    )
    parser.add_argument("--model-id", action="append", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not PROFILE_RE.fullmatch(args.hardware_profile):
            raise MatrixError("hardware-profile must be a short sanitized label.")
        manifest = load_manifest(args.manifest.resolve(strict=True))
        model_root = args.model_root.resolve(strict=True)
        runtime_root = args.runtime_root.resolve(strict=True)
        models = selected_models(manifest, args.model_id)
        output = args.output.absolute() if args.output else None
        if output and (not output.parent.exists() or not output.parent.is_dir()):
            raise MatrixError("Output parent directory must already exist.")
        if output and output.exists() and output.is_symlink():
            raise MatrixError("Output summary must not be a symlink.")
        result: dict[str, Any] = {
            "schemaVersion": 1,
            "status": "preflight-pass",
            "hardwareProfile": args.hardware_profile,
            "backend": args.backend,
            "runtime": {
                "project": manifest["runtime"]["project"],
                "buildTag": manifest["runtime"]["buildTag"],
                "commit": manifest["runtime"]["commit"],
            },
            "preflight": preflight(manifest, model_root, runtime_root, models),
            "models": [],
        }
        if not args.preflight_only:
            result["status"] = "running"
            for model in models:
                try:
                    model_result = execute_model(
                        model,
                        manifest,
                        model_root,
                        runtime_root,
                        args.backend,
                        args.device,
                        args.library_path,
                    )
                except MatrixError as exc:
                    result["status"] = "fail"
                    result["failureModel"] = model["id"]
                    result["failureReason"] = str(exc)
                    if output:
                        write_summary(output, result)
                    raise MatrixError(f"{model['id']}: {exc}") from exc
                result["models"].append(model_result)
                if output:
                    write_summary(output, result)
            result["status"] = "pass"
        if output:
            write_summary(output, result)
        print(json.dumps(result, indent=2))
        return 0
    except MatrixError as exc:
        print(f"Cross-accelerator matrix failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
