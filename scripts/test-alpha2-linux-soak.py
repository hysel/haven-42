#!/usr/bin/env python3
"""Offline hostile checks for the bounded Alpha 2 cross-platform soak runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "alpha2_linux_soak", ROOT / "scripts/alpha2-linux-soak.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        assert 0 <= seconds <= MODULE.MAX_INTERVAL_SECONDS
        self.value += seconds


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.SoakError as error:
        assert str(error) == code, str(error)
    else:
        raise AssertionError(f"Expected {code}")


def passing_cell(**arguments):
    assert arguments["origin"] == "http://127.0.0.1:11435"
    assert arguments["provider_version"] == "0.32.5"
    return {
        "outcome": "passed",
        "metrics": {
            "samplesPassed": 3,
            "unloadPasses": 3,
            "outputTokens": 12,
            "tokensPerSecond": 42.5,
            "peakGpuMemoryBytes": 0,
        },
    }


def passing_qualification_cell(**arguments):
    assert arguments.pop("qualification_inventory") is True
    assert arguments.pop("provider_version") == "0.32.13"
    arguments["provider_version"] = "0.32.5"
    return passing_cell(**arguments)


def passing_vulkan_qualification_cell(**arguments):
    value = passing_qualification_cell(**arguments)
    value["metrics"]["peakGpuMemoryBytes"] = 4 * MODULE.GIB_BYTES
    return value


def run(**overrides):
    clock = Clock()
    arguments = {
        "origin": "http://127.0.0.1:11435",
        "model_id": "qwen35-08b-q8",
        "operating_system_id": "test-linux",
        "backend": "cpu",
        "system_memory_gib": 16,
        "usable_gpu_memory_gib": 0,
        "duration_minutes": 5,
        "interval_seconds": 120,
        "monotonic": clock.monotonic,
        "sleeper": clock.sleep,
        "cell_runner": passing_cell,
    }
    arguments.update(overrides)
    return MODULE.run_soak(**arguments)


def main() -> None:
    result = run()
    assert result["outcome"] == "passed"
    assert result["durationSeconds"] == 300
    assert result["metrics"]["cellsPassed"] == 3
    assert result["metrics"]["samplesPassed"] == 9
    assert result["metrics"]["unloadPasses"] == 9
    assert result["metrics"]["capabilityCells"] == {
        "general.chat": 1,
        "content.write": 1,
        "content.summarize": 1,
    }
    assert result["containsRawPromptsOrResponses"] is False
    assert result["containsPrivateMachineIdentity"] is False
    assert result["evidence"]["automaticPromotionAllowed"] is False
    assert result["kind"] == "alpha2-linux-model-soak-evidence"
    assert result["evidence"]["platformFamily"] == "linux"
    windows = run(
        operating_system_id="windows-11-x64",
        platform_family="windows",
    )
    assert windows["kind"] == "alpha2-windows-model-soak-evidence"
    assert windows["evidence"]["platformFamily"] == "windows"
    refused(
        lambda: run(platform_family="macos"),
        "unreviewed-platform-family",
    )
    qualification = run(
        model_id="granite41-3b-q4",
        qualification_inventory=True,
        qualification_profile_id="cpu-16gib",
        cell_runner=passing_qualification_cell,
    )
    assert qualification["evidence"]["qualificationOnly"] is True
    assert len(
        qualification["evidence"]["qualificationInventoryCanonicalSha256"]
    ) == 64
    assert "selectorPolicyCanonicalSha256" not in qualification["evidence"]
    assert qualification["evidence"]["qualificationProfileId"] == "cpu-16gib"
    refused(
        lambda: run(
            model_id="granite41-3b-q4",
            qualification_inventory=True,
            cell_runner=passing_qualification_cell,
        ),
        "qualification-profile-required",
    )
    refused(
        lambda: run(
            model_id="qwen36-27b-q4",
            qualification_inventory=True,
            qualification_profile_id="cpu-16gib",
            cell_runner=passing_qualification_cell,
        ),
        "unreviewed-qualification-cell",
    )
    for deferred_model in (
        "muse-glimmer-30b-q4",
        "muse-glimmer-30b-mlx-nvfp4",
    ):
        refused(
            lambda model_id=deferred_model: run(
                model_id=model_id,
                qualification_inventory=True,
                qualification_profile_id="cuda-16gib",
                backend="cuda",
                system_memory_gib=64,
                usable_gpu_memory_gib=32,
                cell_runner=passing_qualification_cell,
            ),
            "unreviewed-qualification-cell",
        )
    for duration in (0, 4.999, 721, float("inf"), float("nan"), True):
        refused(lambda value=duration: run(duration_minutes=value), "invalid-soak-duration")
    for interval in (0, 29.999, 301, float("inf"), True):
        refused(lambda value=interval: run(interval_seconds=value), "invalid-soak-interval")
    refused(
        lambda: run(origin="http://localhost:11435"), "invalid-loopback-origin"
    )
    refused(lambda: run(model_id="qwen35-9b-q4"), "unreviewed-model-cell")
    refused(lambda: run(backend="metal"), "unreviewed-backend")
    refused(
        lambda: run(usable_gpu_memory_gib=1), "cpu-cell-gpu-memory-mismatch"
    )
    vulkan = run(
        model_id="granite41-3b-q4",
        qualification_inventory=True,
        qualification_profile_id="vulkan-8gib-system-16gib",
        backend="vulkan",
        system_memory_gib=16,
        usable_gpu_memory_gib=8,
        cell_runner=passing_vulkan_qualification_cell,
    )
    assert vulkan["outcome"] == "passed"
    assert vulkan["evidence"]["backendMode"] == "vulkan"

    def low_headroom_vulkan_cell(**arguments):
        value = passing_vulkan_qualification_cell(**arguments)
        value["metrics"]["peakGpuMemoryBytes"] = 7 * MODULE.GIB_BYTES
        return value

    refused(
        lambda: run(
            model_id="granite41-3b-q4",
            qualification_inventory=True,
            qualification_profile_id="vulkan-8gib-system-16gib",
            backend="vulkan",
            system_memory_gib=16,
            usable_gpu_memory_gib=8,
            cell_runner=low_headroom_vulkan_cell,
        ),
        "insufficient-gpu-headroom",
    )
    refused(
        lambda: run(operating_system_id="private host"),
        "invalid-operating-system-id",
    )

    def bad_result(**_arguments):
        return {"outcome": "passed", "metrics": {"samplesPassed": 2}}

    refused(lambda: run(cell_runner=bad_result), "invalid-cell-result")

    def leaking_cpu_result(**_arguments):
        value = passing_cell(**_arguments)
        value["metrics"]["peakGpuMemoryBytes"] = 1
        return value

    refused(lambda: run(cell_runner=leaking_cpu_result), "cpu-cell-used-gpu")
    source = (ROOT / "scripts/alpha2-linux-soak.py").read_text(encoding="utf-8")
    assert "response\": response" not in source
    assert "subprocess" not in source and "shell=True" not in source
    assert "automaticPromotionAllowed\": False" in source
    print("Alpha 2 cross-platform soak passed offline safety and behavior checks.")


if __name__ == "__main__":
    main()
