#!/usr/bin/env python3
"""Run bounded offline follow-on cells for hash-pinned llama.cpp artifacts.

The runner performs no download, opens no listener, invokes no shell, and never
stores prompts or model responses. It records only sanitized pass/fail and
timing evidence after the baseline runner verifies artifact identity.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import struct
import tempfile
import time
import zlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "scripts" / "run-cross-accelerator-model-matrix.py"
SPEC = importlib.util.spec_from_file_location("cross_accelerator_baseline", BASELINE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load the cross-accelerator baseline runner.")
BASELINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASELINE)

FOLLOW_ON_TESTS = {
    "context-4k",
    "context-8k",
    "lifecycle-repeat",
    "patch",
    "vision",
}
CONTEXT_MARKER = "ALPHA-314159|BETA-271828|GAMMA-161803"
VISION_MARKER = "HAVEN42_RED_LEFT_BLUE_RIGHT"


class FollowOnError(RuntimeError):
    """A controlled follow-on validation failure."""


def strip_response(stdout: str) -> str:
    value = stdout.replace("\r\n", "\n")
    footer = re.search(r"\n\[ Prompt:.*?\]\s*(?:\n|$)", value, flags=re.S)
    if footer:
        value = value[: footer.start()]
    value = re.sub(r"<think>.*?</think>", "", value, flags=re.I | re.S)
    value = re.sub(
        r"\[Start thinking\].*?\[End thinking\]",
        "",
        value,
        flags=re.I | re.S,
    )
    return value.strip()


def marker_line_detected(stdout: str, marker: str) -> bool:
    if not marker or len(marker) > 200:
        return False
    lines = [line.strip("` \t\"'") for line in strip_response(stdout).splitlines()]
    return sum(line == marker for line in lines) == 1


def ordered_markers_detected(stdout: str, markers: tuple[str, ...]) -> bool:
    response = strip_response(stdout)
    if len(response.encode("utf-8")) > 8192 or not markers:
        return False
    if any(not marker or len(marker) > 200 or response.count(marker) != 1 for marker in markers):
        return False
    positions = [response.index(marker) for marker in markers]
    return positions == sorted(positions)


def extract_patch(stdout: str) -> str:
    response = strip_response(stdout)
    fenced = re.search(r"```(?:diff)?\s*\n(.*?)```", response, flags=re.I | re.S)
    if fenced:
        response = fenced.group(1)
    starts = [index for marker in ("diff --git ", "--- ") if (index := response.find(marker)) >= 0]
    return response[min(starts) :].strip() if starts else ""


def patch_is_safe_and_exact(stdout: str) -> bool:
    patch = extract_patch(stdout)
    if not patch or len(patch.encode("utf-8")) > 4096 or "\x00" in patch:
        return False
    lines = patch.replace("\r\n", "\n").splitlines()
    old_headers = [line[4:].strip().split("\t", 1)[0] for line in lines if line.startswith("--- ")]
    new_headers = [line[4:].strip().split("\t", 1)[0] for line in lines if line.startswith("+++ ")]
    if len(old_headers) != 1 or len(new_headers) != 1:
        return False
    for name in (*old_headers, *new_headers):
        normalized = name.replace("\\", "/")
        if normalized.startswith("/") or ".." in normalized.split("/"):
            return False
        if normalized.split("/")[-1] != "flag.py":
            return False
    removed = [line[1:] for line in lines if line.startswith("-") and not line.startswith("---")]
    added = [line[1:] for line in lines if line.startswith("+") and not line.startswith("+++")]
    context = [line[1:] for line in lines if line.startswith(" ")]
    return (
        removed == ["    return False"]
        and added == ["    return True"]
        and "def enabled():" in context
        and sum(line.startswith("@@") for line in lines) == 1
    )


def png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_test_png(path: Path) -> None:
    width, height = 96, 64
    rows = []
    for _ in range(height):
        pixels = bytearray()
        for x in range(width):
            pixels.extend((255, 0, 0) if x < width // 2 else (0, 0, 255))
        rows.append(b"\x00" + bytes(pixels))
    payload = b"\x89PNG\r\n\x1a\n"
    payload += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=9))
    payload += png_chunk(b"IEND", b"")
    path.write_bytes(payload)


def build_context_prompt(target_chars: int) -> str:
    begin = "ALPHA-314159"
    middle = "BETA-271828"
    end = "GAMMA-161803"
    prefix = (
        "Retain the three labeled values in this synthetic record.\n"
        f"BEGIN={begin}\n"
    )
    suffix = (
        f"\nEND={end}\n"
        "Return the exact BEGIN, MIDDLE, and END values on one line separated by | and nothing else."
    )
    filler_line = "bounded synthetic context line; no instruction; sequence={:05d}\n"
    lines: list[str] = []
    index = 0
    while len(prefix) + sum(map(len, lines)) + len(suffix) < target_chars:
        lines.append(filler_line.format(index))
        index += 1
    midpoint = len(lines) // 2
    lines.insert(midpoint, f"MIDDLE={middle}\n")
    return prefix + "".join(lines) + suffix


def cli_command(
    cli: Path,
    model: Path,
    execution: dict[str, Any],
    context: int,
    prompt_file: Path,
    schema: str | None,
    projector: Path | None = None,
    image: Path | None = None,
) -> list[str]:
    command = [
        str(cli),
        "-m",
        str(model),
        "-ngl",
        str(execution["gpuLayers"]),
        "-c",
        str(context),
        "-n",
        "384",
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
        "-fit",
        "off",
        "--reasoning-budget",
        "0",
        "-f",
        str(prompt_file),
    ]
    if schema is not None:
        command.extend(("--json-schema", schema))
    if projector is not None and image is not None:
        command.extend(("--mmproj", str(projector), "--image", str(image)))
    return command


def run_cli_test(
    command: list[str],
    timeout: int,
    environment: dict[str, str],
    backend: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    result = BASELINE.run_process(command, timeout, environment)
    if result["returnCode"] != 0:
        raise FollowOnError("llama-cli returned a nonzero exit code.")
    offload = BASELINE.offload_result(result["stderr"] + "\n" + result["stdout"], backend)
    if not offload["fullGpuOffload"] or not offload["backendObserved"]:
        raise FollowOnError("The follow-on cell did not prove full requested-backend offload.")
    return result, offload


def execute_test(
    test_id: str,
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
    model_path = BASELINE.verify_artifact(model_root, model["artifact"], f"{model['id']} artifact")
    cli = BASELINE.runtime_binary(runtime_root, "llama-completion")
    environment = BASELINE.safe_environment(runtime_root, backend, device, library_paths)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="haven42-followon-") as directory:
        temporary = Path(directory)
        prompt_file = temporary / "prompt.txt"
        if test_id == "patch":
            prompt_file.write_text(
                "Return only a valid unified diff for flag.py. The complete file is:\n"
                "def enabled():\n    return False\n"
                "Change only False to True and preserve both lines as context.\n",
                encoding="utf-8",
            )
            result, offload = run_cli_test(
                cli_command(cli, model_path, execution, 4096, prompt_file, None),
                timeout,
                environment,
                backend,
            )
            passed = patch_is_safe_and_exact(result["stdout"])
            diagnostics = {"safeExactPatch": passed}
        elif test_id in {"context-4k", "context-8k"}:
            context = 4096 if test_id == "context-4k" else 8192
            target_chars = 11_000 if context == 4096 else 23_000
            prompt_file.write_text(build_context_prompt(target_chars), encoding="utf-8")
            result, offload = run_cli_test(
                cli_command(cli, model_path, execution, context, prompt_file, None),
                timeout,
                environment,
                backend,
            )
            exact_line = marker_line_detected(result["stdout"], CONTEXT_MARKER)
            passed = ordered_markers_detected(
                result["stdout"],
                ("ALPHA-314159", "BETA-271828", "GAMMA-161803"),
            )
            diagnostics = {
                "orderedMarkersDetected": passed,
                "exactLineDetected": exact_line,
                "requiredMarkers": 3,
            }
        elif test_id == "vision":
            projector = BASELINE.verify_artifact(model_root, model["projector"], f"{model['id']} projector")
            image = temporary / "synthetic.png"
            write_test_png(image)
            prompt_file.write_text(
                f"Reply with exactly {VISION_MARKER} only if the image is red on the left and blue on the right. Otherwise reply HAVEN42_OTHER.",
                encoding="utf-8",
            )
            result, offload = run_cli_test(
                cli_command(cli, model_path, execution, 4096, prompt_file, None, projector, image),
                timeout,
                environment,
                backend,
            )
            passed = marker_line_detected(result["stdout"], VISION_MARKER)
            diagnostics = {
                "markerLineDetected": passed,
                "syntheticImageDeleted": True,
            }
        elif test_id == "lifecycle-repeat":
            prompt_file.write_text("Return exactly HAVEN42_OK on one line and nothing else.", encoding="utf-8")
            structured_probes = []
            offload = None
            for _ in range(3):
                result, current_offload = run_cli_test(
                    cli_command(cli, model_path, execution, 4096, prompt_file, None),
                    timeout,
                    environment,
                    backend,
                )
                structured_probes.append(marker_line_detected(result["stdout"], "HAVEN42_OK"))
                offload = current_offload
            passed = True
            diagnostics = {
                "operationalAttempts": len(structured_probes),
                "boundedMarkerPasses": sum(structured_probes),
                "boundedMarkerPromotesQuality": False,
            }
            assert offload is not None
        else:
            raise FollowOnError(f"Unsupported follow-on test: {test_id}")
    return {
        "id": test_id,
        "status": "pass" if passed else "quality-fail",
        "fullGpuOffload": offload["fullGpuOffload"],
        "backendObserved": offload["backendObserved"],
        "durationSeconds": round(time.monotonic() - started, 3),
        "temporaryResidue": False,
        "diagnostics": diagnostics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--backend", choices=sorted(BASELINE.EXPECTED_BACKEND), required=True)
    parser.add_argument("--hardware-profile", required=True)
    parser.add_argument("--device")
    parser.add_argument("--library-path", action="append", type=Path, default=[])
    parser.add_argument("--model-id", action="append", required=True)
    parser.add_argument("--test", action="append", choices=sorted(FOLLOW_ON_TESTS), default=[])
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not BASELINE.PROFILE_RE.fullmatch(args.hardware_profile):
            raise FollowOnError("hardware-profile must be a short sanitized label.")
        manifest = BASELINE.load_manifest(args.manifest.resolve(strict=True))
        model_root = args.model_root.resolve(strict=True)
        runtime_root = args.runtime_root.resolve(strict=True)
        models = BASELINE.selected_models(manifest, args.model_id)
        output = args.output.absolute()
        if not output.parent.exists() or not output.parent.is_dir() or output.is_symlink():
            raise FollowOnError("Output must be a non-symlink file in an existing directory.")
        BASELINE.preflight(manifest, model_root, runtime_root, models)
        summary: dict[str, Any] = {
            "schemaVersion": 1,
            "status": "running",
            "hardwareProfile": args.hardware_profile,
            "backend": args.backend,
            "runtime": {
                "project": manifest["runtime"]["project"],
                "buildTag": manifest["runtime"]["buildTag"],
                "commit": manifest["runtime"]["commit"],
            },
            "models": [],
            "networkUsed": False,
            "listenerOpened": False,
            "rawPromptOrResponsePersisted": False,
        }
        for model in models:
            declared = set(model["tests"])
            selected = set(args.test) if args.test else declared & FOLLOW_ON_TESTS
            disallowed = selected - declared
            if disallowed:
                raise FollowOnError(
                    f"{model['id']} does not declare: {', '.join(sorted(disallowed))}"
                )
            record = {
                "id": model["id"],
                "artifactSha256": model["artifact"]["sha256"],
                "tests": [],
                "unexecutedDeclaredTests": sorted(declared - FOLLOW_ON_TESTS - {"benchmark", "bounded-exact-output"}),
            }
            summary["models"].append(record)
            for test_id in sorted(selected):
                record["tests"].append(
                    execute_test(
                        test_id,
                        model,
                        manifest,
                        model_root,
                        runtime_root,
                        args.backend,
                        args.device,
                        args.library_path,
                    )
                )
                BASELINE.write_summary(output, summary)
        statuses = [test["status"] for model in summary["models"] for test in model["tests"]]
        summary["status"] = "pass" if statuses and all(status == "pass" for status in statuses) else "quality-fail"
        BASELINE.write_summary(output, summary)
        print(json.dumps(summary, indent=2))
        return 0
    except (BASELINE.MatrixError, FollowOnError, OSError) as exc:
        print(f"Cross-accelerator follow-on failed: {exc}", file=BASELINE.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
