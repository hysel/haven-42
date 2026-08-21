#!/usr/bin/env python3
"""Validate sanitized Apple M4 MLX lifecycle evidence fail closed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


SHA256 = re.compile(r"[0-9a-f]{64}")
PRIVATE = re.compile(
    r"(?:" + re.escape("/" + "Users/") + r"|/home/|[A-Za-z]:\\|192\.168\.|10\.\d+\.\d+\.\d+|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|ssh-|authorized_keys)",
    re.IGNORECASE,
)


class ValidationError(RuntimeError):
    """Raised when MLX lifecycle evidence is incomplete or unsafe."""


def positive_generation(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get("status") == "passed"
        and value.get("exitCode") == 0
        and isinstance(value.get("durationSeconds"), (int, float))
        and value["durationSeconds"] > 0
        and isinstance(value.get("outputCharacters"), int)
        and value["outputCharacters"] > 0
        and isinstance(value.get("outputSha256"), str)
        and SHA256.fullmatch(value["outputSha256"]) is not None
        and value.get("requiredTokenObserved") is True
        and isinstance(value.get("generationTokensPerSecond"), (int, float))
        and value["generationTokensPerSecond"] > 0
        and isinstance(value.get("peakMetalMemoryGiB"), (int, float))
        and value["peakMetalMemoryGiB"] > 0
        and value.get("processExited") is True
        and value.get("responseRetained") is False
    )


def artifact(value: object) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("fileCount"), int)
        and value["fileCount"] > 0
        and isinstance(value.get("totalBytes"), int)
        and value["totalBytes"] > 0
        and isinstance(value.get("canonicalSha256"), str)
        and SHA256.fullmatch(value["canonicalSha256"]) is not None
    )


def validate(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("invalid-json-result") from error
    if PRIVATE.search(raw):
        raise ValidationError("private-data-detected")
    expected_hardware = {
        "platformFamily": "macos", "architecture": "arm64",
        "acceleratorFamily": "Apple M4", "systemMemoryGiB": 16,
    }
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != 1
        or value.get("kind") != "haven42-sanitized-physical-macos-mlx-lifecycle-result"
        or value.get("status") != "passed"
        or value.get("hardwareProfile") != expected_hardware
    ):
        raise ValidationError("invalid-result-identity")
    runtime = value.get("runtime")
    if (
        not isinstance(runtime, dict)
        or runtime.get("pythonVersion") != "3.14.6"
        or runtime.get("packages") != {
            "mlx-lm": "0.31.3", "mlx": "0.32.1", "mlx-metal": "0.32.1",
        }
        or runtime.get("globalPythonRequiredForFuturePackage") is not False
        or runtime.get("productionServerAdmitted") is not False
        or not artifact(runtime.get("wheelhouse"))
    ):
        raise ValidationError("invalid-runtime-evidence")
    model = value.get("model")
    if (
        not artifact(model)
        or model.get("id") != "mlx-community/Qwen3.5-0.8B-OptiQ-4bit@ef605869"
    ):
        raise ValidationError("invalid-model-evidence")
    tests = value.get("tests")
    forced = tests.get("forcedTimeout") if isinstance(tests, dict) else None
    if (
        not isinstance(tests, dict)
        or tests.get("offlineOnly") is not True
        or not positive_generation(tests.get("firstGeneration"))
        or not positive_generation(tests.get("recoveryGeneration"))
        or not isinstance(forced, dict)
        or forced != {
            "durationSeconds": forced.get("durationSeconds"),
            "processExited": True,
            "responseRetained": False,
            "status": "timed-out",
        }
        or not isinstance(forced.get("durationSeconds"), (int, float))
        or forced["durationSeconds"] <= 0
        or tests.get("listenerOpened") is not False
        or tests.get("processResidueRetained") is not False
    ):
        raise ValidationError("invalid-lifecycle-evidence")
    if value.get("authority") != {
        "automaticSelectionAllowed": False,
        "packageAdmissionGranted": False,
        "runtimeAdmissionGranted": False,
        "supportLabelChangeAllowed": False,
    } or value.get("privacy") != {
        "networkEndpointRetained": False,
        "privateIdentityRetained": False,
        "privatePathRetained": False,
        "rawPromptOrResponseRetained": False,
    }:
        raise ValidationError("invalid-authority-or-privacy-boundary")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    args = parser.parse_args()
    try:
        value = validate(Path(args.result).resolve())
    except ValidationError as error:
        parser.error(str(error))
    print(json.dumps({
        "kind": value["kind"], "status": "passed",
        "model": value["model"]["id"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
