#!/usr/bin/env python3
"""Effect-free tests for the Apple M4 MLX lifecycle runner and validator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RUNNER = load("macos_mlx_lifecycle", "alpha2-macos-mlx-lifecycle.py")
VALIDATOR = load(
    "macos_mlx_lifecycle_validator",
    "validate-alpha2-macos-mlx-lifecycle-result.py",
)


def generation() -> dict[str, object]:
    return {
        "status": "passed", "durationSeconds": 1.5, "exitCode": 0,
        "outputSha256": "a" * 64, "outputCharacters": 120,
        "requiredTokenObserved": True, "generationTokensPerSecond": 42.0,
        "peakMetalMemoryGiB": 1.25, "processExited": True,
        "responseRetained": False,
    }


def result_fixture() -> dict[str, object]:
    artifact = {"fileCount": 2, "totalBytes": 42, "canonicalSha256": "b" * 64}
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-mlx-lifecycle-result",
        "observedAtUtc": "2026-08-21T00:00:00Z", "status": "passed",
        "hardwareProfile": {
            "platformFamily": "macos", "architecture": "arm64",
            "acceleratorFamily": "Apple M4", "systemMemoryGiB": 16,
        },
        "runtime": {
            "pythonVersion": "3.14.6",
            "packages": {"mlx-lm": "0.31.3", "mlx": "0.32.1", "mlx-metal": "0.32.1"},
            "wheelhouse": artifact,
            "globalPythonRequiredForFuturePackage": False,
            "productionServerAdmitted": False,
        },
        "model": {
            "id": "mlx-community/Qwen3.5-0.8B-OptiQ-4bit@ef605869", **artifact,
        },
        "tests": {
            "offlineOnly": True, "firstGeneration": generation(),
            "forcedTimeout": {
                "status": "timed-out", "durationSeconds": 0.01,
                "processExited": True, "responseRetained": False,
            },
            "recoveryGeneration": generation(), "listenerOpened": False,
            "processResidueRetained": False,
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
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-mlx-lifecycle-") as temporary:
        root = Path(temporary)
        artifact_root = root / "artifact"
        artifact_root.mkdir()
        first = artifact_root / "model.bin"
        second = artifact_root / "config.json"
        first.write_bytes(b"model")
        second.write_text("{}", encoding="utf-8")
        manifest = root / "files.sha256"
        manifest.write_text(
            f"{RUNNER.sha256(first)}  {first}\n{RUNNER.sha256(second)}  {second}\n",
            encoding="utf-8",
        )
        evidence = RUNNER.verified_manifest(manifest, artifact_root)
        assert evidence["fileCount"] == 2 and evidence["totalBytes"] == 7
        checks += 2
        metadata = artifact_root / ".cache" / "huggingface" / "download"
        metadata.mkdir(parents=True)
        (metadata / "model.bin.metadata").write_text("transport only", encoding="utf-8")
        evidence = RUNNER.verified_manifest(manifest, artifact_root)
        assert evidence["fileCount"] == 2
        checks += 1
        extra = artifact_root / "unexpected"
        extra.write_text("x", encoding="utf-8")
        try:
            RUNNER.verified_manifest(manifest, artifact_root)
        except RUNNER.LifecycleError as error:
            assert str(error) == "checksum-inventory-mismatch"
        else:
            raise AssertionError("Unlisted MLX artifact was accepted.")
        checks += 1

        output = (
            "MLX_M4_OK\nGeneration: 6 tokens, 42.50 tokens-per-sec\n"
            "Peak memory: 1.25 GB\n"
        )
        with patch.object(
            RUNNER.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0, output, ""),
        ) as run_mock:
            generated = RUNNER.run_generation(
                Path("/fixed/python"), Path("/fixed/model"), {}, 30,
            )
        assert generated["status"] == "passed"
        assert generated["generationTokensPerSecond"] == 42.5
        assert generated["peakMetalMemoryGiB"] == 1.25
        assert "MLX_M4_OK" not in json.dumps(generated)
        command = run_mock.call_args.args[0]
        config_index = command.index("--chat-template-config")
        assert command[config_index + 1] == '{"enable_thinking":false}'
        checks += 5
        with patch.object(
            RUNNER.subprocess, "run", side_effect=subprocess.TimeoutExpired([], 0.01),
        ):
            timed_out = RUNNER.run_generation(
                Path("/fixed/python"), Path("/fixed/model"), {}, 0.01,
            )
        assert timed_out["status"] == "timed-out" and timed_out["processExited"] is True
        checks += 2

        result_path = root / "result.json"
        result_path.write_text(
            json.dumps(result_fixture(), sort_keys=True), encoding="utf-8",
        )
        assert VALIDATOR.validate(result_path)["status"] == "passed"
        checks += 1
        hostile = result_fixture()
        hostile["debug"] = "/" + "Users/private/model"
        result_path.write_text(json.dumps(hostile), encoding="utf-8")
        try:
            VALIDATOR.validate(result_path)
        except VALIDATOR.ValidationError as error:
            assert str(error) == "private-data-detected"
        else:
            raise AssertionError("Private MLX result was accepted.")
        checks += 1
    print(f"Apple M4 MLX lifecycle tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
