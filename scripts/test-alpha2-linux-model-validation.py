#!/usr/bin/env python3
"""Offline hostile tests for the native cross-platform model cell runner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "alpha2_linux_model_validation",
    ROOT / "scripts/alpha2-linux-model-validation.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.ValidationError as error:
        assert str(error) == code, str(error)
    else:
        raise AssertionError(f"Expected {code}")


def main() -> None:
    model, policy_sha, provider_version = MODULE.reviewed_model("qwen35-08b-q8")
    assert model["manifestDigest"] == "f3817196d142eaf72ce79dfebe53dcb20bd21da87ce13e138a8f8e10a866b3a4"
    assert model["automaticEvidenceCandidate"] is True
    assert len(policy_sha) == 64
    assert provider_version == "0.32.5"
    comparison, comparison_policy_sha, comparison_provider_version = MODULE.reviewed_model("qwen35-9b-control")
    assert comparison == {
        "id": "qwen35-9b-control",
        "name": "qwen3.5:9b",
        "manifestDigest": "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
        "automaticEvidenceCandidate": False,
    }
    assert comparison_policy_sha == policy_sha
    assert comparison_provider_version == "0.32.6"
    qualification, inventory_sha, qualification_provider = (
        MODULE.reviewed_qualification_model("granite41-3b-q4")
    )
    assert qualification == {
        "id": "granite41-3b-q4",
        "name": "granite4.1:3b-q4_K_M",
        "manifestDigest": "6fd349357287c7ffc9e38189a93b48ea175d24fc566b38f09cfc564fb7f303eb",
        "modelBytes": 2099501664,
        "downloadBytes": 2099519864,
        "automaticEvidenceCandidate": False,
        "qualificationOnly": True,
    }
    assert len(inventory_sha) == 64 and inventory_sha != policy_sha
    assert qualification_provider == "0.32.5"
    refused(
        lambda: MODULE.reviewed_model("granite41-3b-q4"),
        "unreviewed-model-cell",
    )
    refused(
        lambda: MODULE.reviewed_qualification_model("qwen35-08b-q8"),
        "unreviewed-qualification-model",
    )
    refused(
        lambda: MODULE.run_cell(
            origin="http://127.0.0.1:11435",
            model_id="qwen35-9b-control",
            capability="general.chat",
            operating_system_id="protected-provider",
            backend="cuda",
            system_memory_gib=128,
            usable_gpu_memory_gib=32,
            provider_version="0.32.5",
        ),
        "unreviewed-provider-version",
    )
    assert MODULE.validate_origin("http://127.0.0.1:11435") == "http://127.0.0.1:11435"
    for value in (
        "https://127.0.0.1:11435", "http://localhost:11435", "http://0.0.0.0:11435",
        "http://127.0.0.1:80", "http://user@127.0.0.1:11435", "http://127.0.0.1:11435/path",
    ):
        refused(lambda v=value: MODULE.validate_origin(v), "invalid-loopback-origin")
    refused(lambda: MODULE.reviewed_model("qwen35-9b-q4"), "unreviewed-model-cell")
    refused(
        lambda: MODULE.run_cell(
            origin="http://127.0.0.1:11435",
            model_id="qwen35-08b-q8",
            capability="general.chat",
            operating_system_id="test-platform",
            backend="cpu",
            system_memory_gib=16,
            usable_gpu_memory_gib=0,
            platform_family="macos",
        ),
        "unreviewed-platform-family",
    )
    with tempfile.TemporaryDirectory() as temporary:
        original = MODULE.COMPARISON_CONTRACT_PATH
        contract = json.loads(original.read_text(encoding="utf-8"))
        contract["provider"]["exactVersion"] = "0.32.7"
        altered = Path(temporary) / "comparison.json"
        altered.write_text(json.dumps(contract), encoding="utf-8")
        MODULE.COMPARISON_CONTRACT_PATH = altered
        try:
            refused(
                lambda: MODULE.reviewed_model("qwen35-9b-control"),
                "invalid-comparison-contract",
            )
        finally:
            MODULE.COMPARISON_CONTRACT_PATH = original
    with tempfile.TemporaryDirectory() as temporary:
        original = MODULE.QUALIFICATION_INVENTORY_PATH
        inventory = json.loads(original.read_text(encoding="utf-8"))
        inventory["qualificationProvider"]["exactVersion"] = "0.32.6"
        altered = Path(temporary) / "inventory.json"
        altered.write_text(json.dumps(inventory), encoding="utf-8")
        MODULE.QUALIFICATION_INVENTORY_PATH = altered
        try:
            refused(
                lambda: MODULE.reviewed_qualification_model("granite41-3b-q4"),
                "invalid-qualification-inventory",
            )
        finally:
            MODULE.QUALIFICATION_INVENTORY_PATH = original
    refused(lambda: MODULE._json_request("http://127.0.0.1:11435", "/shell"), "invalid-provider-route")
    prompt, output, rate = MODULE._validate_generate({
        "done": True, "response": "ready", "eval_count": 2,
        "prompt_eval_count": 3, "eval_duration": 1_000_000_000,
    })
    assert (prompt, output, rate) == (3, 2, 2.0)
    for hostile in (
        {"done": True, "response": "", "eval_count": 2, "prompt_eval_count": 3, "eval_duration": 1},
        {"done": False, "response": "ready", "eval_count": 2, "prompt_eval_count": 3, "eval_duration": 1},
        {"done": True, "response": "ready", "eval_count": True, "prompt_eval_count": 3, "eval_duration": 1},
        {"done": True, "response": "ready", "eval_count": 2, "prompt_eval_count": 3, "eval_duration": 0},
    ):
        refused(lambda v=hostile: MODULE._validate_generate(v), "inference-response-contract-failed")

    originals = {
        "reviewed_model": MODULE.reviewed_model,
        "verify_provider": MODULE.verify_provider,
        "_json_request": MODULE._json_request,
        "_unload": MODULE._unload,
    }
    unload_calls = []
    try:
        MODULE.reviewed_model = lambda _model_id: ({
            "id": "qwen35-08b-q8",
            "name": "qwen3.5:0.8b",
            "manifestDigest": "a" * 64,
            "automaticEvidenceCandidate": True,
        }, "b" * 64, "0.32.5")
        MODULE.verify_provider = lambda *_args: None
        MODULE._json_request = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            MODULE.ValidationError("simulated-generation-failure")
        )
        MODULE._unload = lambda *_args: unload_calls.append(True)
        refused(
            lambda: MODULE.run_cell(
                origin="http://127.0.0.1:11435",
                model_id="qwen35-08b-q8",
                capability="general.chat",
                operating_system_id="test-linux",
                backend="cpu",
                system_memory_gib=16,
                usable_gpu_memory_gib=0,
            ),
            "simulated-generation-failure",
        )
        assert unload_calls == [True]
        MODULE._unload = lambda *_args: (_ for _ in ()).throw(
            MODULE.ValidationError("simulated-unload-failure")
        )
        refused(
            lambda: MODULE.run_cell(
                origin="http://127.0.0.1:11435",
                model_id="qwen35-08b-q8",
                capability="general.chat",
                operating_system_id="test-linux",
                backend="cpu",
                system_memory_gib=16,
                usable_gpu_memory_gib=0,
            ),
            "model-cell-failed-and-unload-unverified",
        )
    finally:
        for name, value in originals.items():
            setattr(MODULE, name, value)
    source = (ROOT / "scripts/alpha2-linux-model-validation.py").read_text(encoding="utf-8")
    assert "response\": response" not in source
    assert "subprocess" not in source and "shell=True" not in source
    print("Alpha 2 cross-platform model validation passed hostile offline checks.")


if __name__ == "__main__":
    main()
