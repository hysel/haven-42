#!/usr/bin/env python3
"""Offline hostile checks for cross-family task qualification."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alpha2_model_task_qualification",
    ROOT / "scripts/alpha2-model-task-qualification.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.QualificationError as error:
        assert str(error) == code, str(error)
    else:
        raise AssertionError(f"Expected {code}")


def main() -> None:
    MODULE._check_response("general.chat", "HAVEN42_READY")
    MODULE._check_response(
        "content.write", "Careful testing keeps local software reliable, private, predictable, and easier to maintain."
    )
    MODULE._check_response(
        "content.summarize",
        "The runtime remains in a folder beside the app without creating a Windows service, making managed-file removal straightforward."
    )
    refused(
        lambda: MODULE._check_response("general.chat", "Ready"),
        "chat-exact-response-failed",
    )
    refused(
        lambda: MODULE._check_response("content.write", "Testing helps."),
        "writing-word-count-out-of-range",
    )
    refused(
        lambda: MODULE._check_response(
            "content.summarize", "The folder creates 2 services."
        ),
        "summary-word-count-out-of-range",
    )
    profile, matrix_sha = MODULE._review_matrix("granite41-3b-q4", "cpu-16gib")
    assert profile["backend"] == "cpu" and len(matrix_sha) == 64
    qwen_profile, qwen_matrix_sha = MODULE._review_matrix(
        "qwen36-27b-q4", "cuda-32gib-system-16gib"
    )
    assert qwen_profile == {
        "id": "cuda-32gib-system-16gib",
        "backend": "cuda",
        "minimumSystemMemoryGiB": 31,
        "minimumUsableGpuMemoryGiB": 16,
    }
    assert len(qwen_matrix_sha) == 64
    vulkan_profile, vulkan_matrix_sha = MODULE._review_matrix(
        "granite41-3b-q4", "vulkan-8gib-system-16gib"
    )
    assert vulkan_profile == {
        "id": "vulkan-8gib-system-16gib",
        "backend": "vulkan",
        "minimumSystemMemoryGiB": 15,
        "minimumUsableGpuMemoryGiB": 8,
        "minimumFreeGpuMemoryGiB": 2,
    }
    assert len(vulkan_matrix_sha) == 64
    four_gib_profile, four_gib_matrix_sha = MODULE._review_matrix(
        "granite41-3b-q4", "cuda-4gib-system-16gib"
    )
    assert four_gib_profile == {
        "id": "cuda-4gib-system-16gib",
        "backend": "cuda",
        "minimumSystemMemoryGiB": 15,
        "minimumUsableGpuMemoryGiB": 4,
        "minimumFreeGpuMemoryGiB": 1,
    }
    assert len(four_gib_matrix_sha) == 64
    refused(
        lambda: MODULE._review_matrix(
            "qwen35-4b-q4", "cuda-4gib-system-16gib"
        ),
        "unreviewed-qualification-cell",
    )
    refused(
        lambda: MODULE._review_matrix("qwen36-27b-q4", "cpu-16gib"),
        "unreviewed-qualification-cell",
    )
    failure = MODULE._failure_result(
        MODULE.argparse.Namespace(
            capability="content.summarize",
            model_id="gemma3-1b-q4",
            operating_system_id="bazzite-44",
            profile_id="cpu-16gib",
            platform_family="linux",
        ),
        MODULE.QualificationError("summary-one-sentence-required"),
    )
    assert failure["outcome"] == "failed"
    assert failure["errorCode"] == "summary-one-sentence-required"
    assert failure["containsRawPromptsOrResponses"] is False
    assert failure["containsPrivateMachineIdentity"] is False
    assert "origin" not in str(failure).lower()
    assert failure["evidence"]["manifestDigest"]
    hostile_failure = MODULE._failure_result(
        MODULE.argparse.Namespace(
            capability="content.summarize",
            model_id="gemma3-1b-q4",
            operating_system_id="bazzite-44",
            profile_id="cpu-16gib",
            platform_family="linux",
        ),
        MODULE.QualificationError("bad\nprivate text"),
    )
    assert hostile_failure["errorCode"] == "qualification-failed"
    assert "private text" not in str(hostile_failure)

    runner = MODULE.MODEL_RUNNER
    originals = {
        "verify_provider": runner.verify_provider,
        "_json_request": runner._json_request,
        "_verify_residency": runner._verify_residency,
        "_unload": runner._unload,
    }
    unloads: list[bool] = []
    try:
        runner.verify_provider = lambda *_args: None
        runner._json_request = lambda *_args, **_kwargs: {
            "done": True,
            "response": "HAVEN42_READY",
            "eval_count": 2,
            "prompt_eval_count": 3,
            "eval_duration": 1_000_000_000,
        }
        runner._verify_residency = lambda *_args: 0
        runner._unload = lambda *_args: unloads.append(True)
        result = MODULE.run_qualification(
            origin="http://127.0.0.1:11434",
            model_id="granite41-3b-q4",
            capability="general.chat",
            profile_id="cpu-16gib",
            operating_system_id="test-linux",
            system_memory_gib=16,
            usable_gpu_memory_gib=0,
        )
        assert result["outcome"] == "passed"
        assert result["metrics"]["samplesPassed"] == 3
        assert result["metrics"]["unloadPasses"] == 3
        assert result["containsRawPromptsOrResponses"] is False
        assert result["evidence"]["automaticPromotionAllowed"] is False
        assert result["evidence"]["platformFamily"] == "linux"
        assert unloads == [True, True, True]
        runner._verify_residency = lambda *_args: 4 * MODULE.GIB_BYTES
        vulkan_result = MODULE.run_qualification(
            origin="http://127.0.0.1:11434",
            model_id="granite41-3b-q4",
            capability="general.chat",
            profile_id="vulkan-8gib-system-16gib",
            operating_system_id="test-linux",
            system_memory_gib=16,
            usable_gpu_memory_gib=8,
        )
        assert vulkan_result["outcome"] == "passed"
        assert vulkan_result["evidence"]["backendMode"] == "vulkan"
        runner._verify_residency = lambda *_args: 7 * MODULE.GIB_BYTES
        refused(
            lambda: MODULE.run_qualification(
                origin="http://127.0.0.1:11434",
                model_id="granite41-3b-q4",
                capability="general.chat",
                profile_id="vulkan-8gib-system-16gib",
                operating_system_id="test-linux",
                system_memory_gib=16,
                usable_gpu_memory_gib=8,
            ),
            "insufficient-gpu-headroom",
        )
        runner._verify_residency = lambda *_args: 0
        windows_result = MODULE.run_qualification(
            origin="http://127.0.0.1:11434",
            model_id="granite41-3b-q4",
            capability="general.chat",
            profile_id="cpu-16gib",
            operating_system_id="windows-11-x64",
            system_memory_gib=16,
            usable_gpu_memory_gib=0,
            platform_family="windows",
        )
        assert windows_result["evidence"]["platformFamily"] == "windows"
        assert unloads == [True] * 12
        refused(
            lambda: MODULE.run_qualification(
                origin="http://127.0.0.1:11434",
                model_id="granite41-3b-q4",
                capability="general.chat",
                profile_id="cpu-16gib",
                operating_system_id="test-platform",
                system_memory_gib=16,
                usable_gpu_memory_gib=0,
                platform_family="macos",
            ),
            "unreviewed-platform-family",
        )
        runner._json_request = lambda *_args, **_kwargs: {
            "done": True,
            "response": "wrong",
            "eval_count": 2,
            "prompt_eval_count": 3,
            "eval_duration": 1_000_000_000,
        }
        refused(
            lambda: MODULE.run_qualification(
                origin="http://127.0.0.1:11434",
                model_id="granite41-3b-q4",
                capability="general.chat",
                profile_id="cpu-16gib",
                operating_system_id="test-linux",
                system_memory_gib=16,
                usable_gpu_memory_gib=0,
            ),
            "chat-exact-response-failed",
        )
        assert len(unloads) == 13
    finally:
        for name, value in originals.items():
            setattr(runner, name, value)
    source = (ROOT / "scripts/alpha2-model-task-qualification.py").read_text(
        encoding="utf-8"
    )
    assert '"response": response' not in source
    assert "subprocess" not in source and "shell=True" not in source
    print("Alpha 2 model task qualification passed hostile offline checks.")


if __name__ == "__main__":
    main()
