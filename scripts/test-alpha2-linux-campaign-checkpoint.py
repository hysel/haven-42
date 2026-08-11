#!/usr/bin/env python3
"""Hostile tests for restartable Alpha 2 Linux campaign checkpoints."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts/alpha2-linux-campaign-checkpoint.py"
SPEC = importlib.util.spec_from_file_location("alpha2_checkpoint", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def rejected(value: dict, text: str) -> None:
    try:
        MODULE.validate_checkpoint(value)
    except MODULE.CheckpointError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError("Unsafe checkpoint was accepted.")


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.add(node.module.split(".", 1)[0])
    return values


def passed_result() -> dict:
    return {
        "outcome": "passed",
        "errorCode": None,
        "durationSeconds": 12.5,
        "metrics": {"peakCpuPercent": 25.0, "peakRamBytes": 1024},
        "evidence": None,
    }


def model_evidence(task: dict) -> dict:
    policy_sha, bindings = MODULE._load_model_bindings()
    return {
        "selectorPolicyCanonicalSha256": policy_sha,
        "modelId": task["candidateId"],
        "manifestDigest": bindings[task["candidateId"]],
        "platformFamily": "linux",
        "operatingSystemId": "linux-test-1",
        "architecture": "x64",
        "backendMode": "cpu" if task["stage"] == "cpu-selection" else "cuda",
        "provider": "ollama",
        "providerVersion": "0.0.0-test",
        "systemMemoryGiB": 16,
        "usableGpuMemoryGiB": 0 if task["stage"] == "cpu-selection" else 16,
        "storageAdmitted": True,
        "capability": task["capabilityId"],
        "capabilityPassed": True,
        "automaticEvidenceCandidate": task["evidenceUse"] == "automatic-candidate",
    }


def main() -> int:
    digest = "a" * 64
    checkpoint = MODULE.new_checkpoint(digest, "2026-08-08T00:00:00Z")
    contract = MODULE.PLANNER.load_contract(MODULE.CONTRACT_PATH)
    crlf_contract = json.loads(json.dumps(contract, indent=2).replace("\n", "\r\n"))
    assert MODULE.canonical_contract_sha256(crlf_contract) == checkpoint["contractSha256"]
    assert len(checkpoint["tasks"]) == 129
    assert sum(task["requiresGpu"] for task in checkpoint["tasks"]) == 45
    assert sum(task["taskKind"] == "distribution-stage" for task in checkpoint["tasks"]) == 72
    assert sum(task["taskKind"] == "model-validation" for task in checkpoint["tasks"]) == 57
    assert MODULE.public_summary(checkpoint)["taskCounts"]["pending"] == 129
    checks = 6

    first_model_task = checkpoint["tasks"][72]
    assert first_model_task["stage"] == "cpu-selection"
    assert first_model_task["candidateId"] == "qwen35-08b-q8"
    assert first_model_task["repetitions"] == 3
    model_result = {
        "outcome": "passed",
        "errorCode": None,
        "durationSeconds": 30,
        "metrics": {
            "samplesAttempted": 3,
            "samplesPassed": 3,
            "samplesFailed": 0,
            "unloadPasses": 3,
            "tokensPerSecond": 10.0,
        },
        "evidence": model_evidence(first_model_task),
    }
    MODULE.validate_result(model_result, first_model_task)
    checks += 4
    missing_samples = copy.deepcopy(model_result)
    missing_samples["metrics"] = {"tokensPerSecond": 10.0}
    try:
        MODULE.validate_result(missing_samples, first_model_task)
    except MODULE.CheckpointError as exc:
        assert "lacks sample metrics" in str(exc)
    else:
        raise AssertionError("Model result without sample metrics was accepted.")
    inconsistent_samples = copy.deepcopy(model_result)
    inconsistent_samples["metrics"]["samplesPassed"] = 2
    try:
        MODULE.validate_result(inconsistent_samples, first_model_task)
    except MODULE.CheckpointError as exc:
        assert "inconsistent" in str(exc)
    else:
        raise AssertionError("Inconsistent sample counts were accepted.")
    incomplete_unload = copy.deepcopy(model_result)
    incomplete_unload["metrics"]["unloadPasses"] = 2
    try:
        MODULE.validate_result(incomplete_unload, first_model_task)
    except MODULE.CheckpointError as exc:
        assert "every sample and unload" in str(exc)
    else:
        raise AssertionError("Passing model result with an incomplete unload was accepted.")
    missing_evidence = copy.deepcopy(model_result)
    missing_evidence["evidence"] = None
    try:
        MODULE.validate_result(missing_evidence, first_model_task)
    except MODULE.CheckpointError as exc:
        assert "evidence fields" in str(exc)
    else:
        raise AssertionError("Passing model result without exact evidence was accepted.")
    wrong_digest = copy.deepcopy(model_result)
    wrong_digest["evidence"]["manifestDigest"] = "0" * 64
    try:
        MODULE.validate_result(wrong_digest, first_model_task)
    except MODULE.CheckpointError as exc:
        assert "exact reviewed artifact" in str(exc)
    else:
        raise AssertionError("Model evidence for a different artifact was accepted.")
    wrong_backend = copy.deepcopy(model_result)
    wrong_backend["evidence"]["backendMode"] = "cuda"
    wrong_backend["evidence"]["usableGpuMemoryGiB"] = 16
    try:
        MODULE.validate_result(wrong_backend, first_model_task)
    except MODULE.CheckpointError as exc:
        assert "CPU execution path" in str(exc)
    else:
        raise AssertionError("CPU evidence from a GPU backend was accepted.")
    wrong_promotion = copy.deepcopy(model_result)
    wrong_promotion["evidence"]["automaticEvidenceCandidate"] = False
    try:
        MODULE.validate_result(wrong_promotion, first_model_task)
    except MODULE.CheckpointError as exc:
        assert "promotion boundary" in str(exc)
    else:
        raise AssertionError("Changed model promotion boundary was accepted.")
    checks += 7

    MODULE.begin_next(checkpoint, "2026-08-08T00:01:00Z")
    assert checkpoint["tasks"][0]["status"] == "running"
    assert checkpoint["tasks"][0]["attempts"] == 1
    MODULE.stage_result(checkpoint, passed_result(), "2026-08-08T00:01:30Z")
    assert checkpoint["tasks"][0]["status"] == "running"
    assert checkpoint["tasks"][0]["result"]["outcome"] == "passed"
    MODULE.finalize_staged_result(checkpoint, "2026-08-08T00:02:00Z")
    assert checkpoint["nextTaskIndex"] == 1 and checkpoint["status"] == "ready"
    checks += 5

    duplicate = MODULE.new_checkpoint(digest, "2026-08-08T00:00:00Z")
    MODULE.begin_next(duplicate, "2026-08-08T00:01:00Z")
    MODULE.stage_result(duplicate, passed_result(), "2026-08-08T00:01:30Z")
    try:
        MODULE.stage_result(duplicate, passed_result(), "2026-08-08T00:01:31Z")
    except MODULE.CheckpointError as exc:
        assert "already has a staged result" in str(exc)
    else:
        raise AssertionError("A staged result was overwritten.")
    MODULE.recover_interrupted(duplicate, "2026-08-08T00:01:32Z")
    assert duplicate["status"] == "running"
    assert duplicate["tasks"][0]["result"]["outcome"] == "passed"
    checks += 3

    MODULE.begin_next(checkpoint, "2026-08-08T00:03:00Z")
    MODULE.recover_interrupted(checkpoint, "2026-08-08T00:04:00Z")
    assert checkpoint["status"] == "paused"
    assert checkpoint["pauseCode"] == "controller-interrupted"
    assert checkpoint["tasks"][1]["status"] == "blocked"
    MODULE.approve_retry(checkpoint, "2026-08-08T00:05:00Z")
    assert checkpoint["tasks"][1]["status"] == "pending"
    assert checkpoint["tasks"][1]["attempts"] == 1
    checks += 5

    hostile = copy.deepcopy(checkpoint)
    hostile["tasks"][0]["target"] = "windows-guest"
    rejected(hostile, "identity or boundary changed")
    hostile = copy.deepcopy(checkpoint)
    hostile["tasks"][72]["candidateId"] = "unreviewed-model"
    rejected(hostile, "identity or boundary changed")
    hostile = copy.deepcopy(checkpoint)
    hostile["tasks"][2]["status"] = "passed"
    hostile["tasks"][2]["result"] = passed_result()
    rejected(hostile, "future task is not pending")
    hostile = copy.deepcopy(checkpoint)
    hostile["tasks"][2]["result"] = passed_result()
    rejected(hostile, "pending task cannot contain")
    hostile = copy.deepcopy(checkpoint)
    hostile["tasks"][1]["status"] = "failed"
    hostile["tasks"][1]["result"] = passed_result()
    rejected(hostile, "matching result")
    hostile = copy.deepcopy(checkpoint)
    hostile["tasks"][1]["result"] = {
        "outcome": "failed",
        "errorCode": "bad",
        "durationSeconds": 1,
        "metrics": {"hostname": "private"},
        "evidence": None,
    }
    rejected(hostile, "unapproved field")
    hostile = copy.deepcopy(checkpoint)
    hostile["tasks"][1]["result"] = {
        "outcome": "failed",
        "errorCode": "../../secret",
        "durationSeconds": 1,
        "metrics": {},
        "evidence": None,
    }
    rejected(hostile, "stable error code")
    hostile = copy.deepcopy(checkpoint)
    hostile["contractSha256"] = "0" * 64
    rejected(hostile, "contract digest")
    hostile = copy.deepcopy(checkpoint)
    hostile["prompt"] = "private content"
    rejected(hostile, "fields do not match")
    checks += 9

    with tempfile.TemporaryDirectory() as temporary_name:
        root = Path(temporary_name)
        MODULE.save_checkpoint(root, checkpoint)
        loaded = MODULE.load_checkpoint(root)
        assert loaded == checkpoint
        assert (root / "checkpoint.json").read_bytes().endswith(b"\n")
        if os.name == "posix":
            assert (root / "checkpoint.json").stat().st_mode & 0o077 == 0
        checks += 3
        link = root / "unsafe"
        try:
            link.symlink_to(root, target_is_directory=True)
        except OSError:
            pass
        else:
            try:
                MODULE.resolve_checkpoint(link)
            except MODULE.CheckpointError as exc:
                assert "must not be a symlink" in str(exc)
            else:
                raise AssertionError("Symlink checkpoint root was accepted.")
            checks += 1
        oversized = root / "checkpoint.json"
        oversized.write_bytes(b"{" + b" " * (2 * 1024 * 1024))
        try:
            MODULE.load_checkpoint(root)
        except MODULE.CheckpointError as exc:
            assert "size limit" in str(exc)
        else:
            raise AssertionError("Oversized checkpoint was accepted.")
        checks += 1

    forbidden = {"asyncio", "http", "requests", "socket", "subprocess", "urllib"}
    assert imports(MODULE_PATH).isdisjoint(forbidden)
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert all(value not in source for value in ("shell=True", "ssh ", "qm ", "pvesh "))
    encoded = json.dumps(checkpoint)
    assert all(
        marker not in encoded
        for marker in ("192.168.", "SHA256:", "hostname", "username", "prompt", "response")
    )
    checks += 3
    print(f"Alpha 2 campaign checkpoint passed {checks} hostile persistence checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
