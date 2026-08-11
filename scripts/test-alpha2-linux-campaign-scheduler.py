#!/usr/bin/env python3
"""Hostile offline tests for the Alpha 2 campaign scheduler."""

from __future__ import annotations

import ast
import copy
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts/alpha2-linux-campaign-scheduler.py"
SPEC = importlib.util.spec_from_file_location("alpha2_scheduler", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

TARGETS = [target["id"] for target in MODULE.CHECKPOINT.PLANNER.load_contract(
    MODULE.CHECKPOINT.CONTRACT_PATH
)["targets"]]
CONTROLLER_TARGETS = [*TARGETS, "windows-11-nvidia"]


def policy() -> dict:
    return {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "deploymentState": "reviewed-and-enabled",
        "nodeName": "test-node",
        "gpuMappingId": "approved-gpu",
        "gpuMappingCanonicalSha256": "a" * 64,
        "gpuSlot": "hostpci0",
        "targets": [
            {"id": target, "vmid": 200 + index}
            for index, target in enumerate(CONTROLLER_TARGETS)
        ],
        "excludedVmIds": [299],
        "excludedContainerIds": [300],
        "limits": {
            "gracefulShutdownSeconds": 180,
            "maximumConcurrentGpuOwners": 1,
            "minimumLocalZfsFreePercent": 16,
            "maximumRequestBytes": 4096,
        },
    }


def state() -> dict:
    return {
        "nodeName": "test-node",
        "gpuMappingCanonicalSha256": "a" * 64,
        "zfsFreePercent": 20.0,
        "vms": {
            str(200 + index): "stopped"
            for index in range(len(CONTROLLER_TARGETS))
        },
        "protectedVms": {"299": "stopped"},
        "protectedContainers": {"300": "running"},
        "gpuConfiguredVmIds": [
            200 + index for index in range(len(CONTROLLER_TARGETS))
        ],
        "gpuOwners": [],
        "protectedContainerGpuOwners": [],
        "unknownPassthroughVmIds": [],
        "unknownPassthroughContainerIds": [],
        "shutdownTimedOutVmIds": [],
    }


def result_for(task: dict) -> dict:
    metrics = {}
    evidence = None
    if task["taskKind"] == "model-validation":
        metrics = {
            "samplesAttempted": 3,
            "samplesPassed": 3,
            "samplesFailed": 0,
            "unloadPasses": 3,
        }
        policy_sha, bindings = MODULE.CHECKPOINT._load_model_bindings()
        evidence = {
            "selectorPolicyCanonicalSha256": policy_sha,
            "modelId": task["candidateId"],
            "manifestDigest": bindings[task["candidateId"]],
            "platformFamily": "linux",
            "operatingSystemId": "linux-test-1",
            "architecture": "x64",
            "backendMode": (
                "cpu" if task["stage"] == "cpu-selection" else "cuda"
            ),
            "provider": "ollama",
            "providerVersion": "0.0.0-test",
            "systemMemoryGiB": 16,
            "usableGpuMemoryGiB": 0 if task["stage"] == "cpu-selection" else 16,
            "storageAdmitted": True,
            "capability": task["capabilityId"],
            "capabilityPassed": True,
            "automaticEvidenceCandidate": (
                task["evidenceUse"] == "automatic-candidate"
            ),
        }
    return {
        "outcome": "passed",
        "errorCode": None,
        "durationSeconds": 1,
        "metrics": metrics,
        "evidence": evidence,
    }


def checkpoint_at(index: int) -> dict:
    checkpoint = MODULE.CHECKPOINT.new_checkpoint("a" * 64, "2026-08-08T00:00:00Z")
    for position in range(index):
        task = checkpoint["tasks"][position]
        task["status"] = "passed"
        task["attempts"] = 1
        task["result"] = result_for(task)
    checkpoint["nextTaskIndex"] = index
    checkpoint["revision"] = index
    MODULE.CHECKPOINT.validate_checkpoint(checkpoint)
    return checkpoint


def refused(policy_value: dict, checkpoint: dict, state_value: dict, text: str) -> None:
    try:
        MODULE.next_step(policy_value, checkpoint, state_value)
    except (MODULE.SchedulerRefusal, MODULE.CONTROL.PolicyRefusal) as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError("Unsafe campaign state was scheduled.")


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    private_policy = policy()
    live = state()
    checkpoint = checkpoint_at(0)
    assert MODULE.next_step(private_policy, checkpoint, live).action == "begin-next"
    MODULE.CHECKPOINT.begin_next(checkpoint, "2026-08-08T00:01:00Z")
    assert MODULE.next_step(private_policy, checkpoint, live).action == "start"
    live["vms"]["200"] = "running"
    assert MODULE.next_step(private_policy, checkpoint, live).action == "execute-task"
    MODULE.CHECKPOINT.stage_result(
        checkpoint, result_for(checkpoint["tasks"][0]), "2026-08-08T00:02:00Z"
    )
    assert MODULE.next_step(private_policy, checkpoint, live).action == "shutdown"
    live["shutdownTimedOutVmIds"] = [200]
    refused(private_policy, checkpoint, live, "graceful guest shutdown timed out")
    live["shutdownTimedOutVmIds"] = []
    live["vms"]["200"] = "stopped"
    assert MODULE.next_step(private_policy, checkpoint, live).action == "finalize-staged-result"
    checks = 7

    gpu_checkpoint = checkpoint_at(4)
    MODULE.CHECKPOINT.begin_next(gpu_checkpoint, "2026-08-08T01:00:00Z")
    gpu_task = gpu_checkpoint["tasks"][4]
    assert gpu_task["requiresGpu"]
    assert MODULE.next_step(private_policy, gpu_checkpoint, live).action == "start"
    live["vms"]["200"] = "running"
    live["gpuOwners"] = [200]
    assert MODULE.next_step(private_policy, gpu_checkpoint, live).action == "execute-task"
    MODULE.CHECKPOINT.stage_result(
        gpu_checkpoint, result_for(gpu_task), "2026-08-08T01:02:00Z"
    )
    assert MODULE.next_step(private_policy, gpu_checkpoint, live).action == "shutdown"
    live["vms"]["200"] = "stopped"
    live["gpuOwners"] = []
    assert MODULE.next_step(private_policy, gpu_checkpoint, live).action == "finalize-staged-result"
    checks += 5

    gpu_prepare = checkpoint_at(4)
    MODULE.CHECKPOINT.begin_next(gpu_prepare, "2026-08-08T01:10:00Z")
    protected = state()
    protected["protectedContainerGpuOwners"] = [300]
    refused(private_policy, gpu_prepare, protected, "protected container")
    other_running = state()
    other_running["vms"]["201"] = "running"
    refused(private_policy, gpu_prepare, other_running, "Another approved")
    missing_mapping = state()
    missing_mapping["gpuConfiguredVmIds"].remove(200)
    refused(private_policy, gpu_prepare, missing_mapping, "static GPU mapping")
    checks += 3

    external = checkpoint_at(117)
    MODULE.CHECKPOINT.begin_next(external, "2026-08-08T02:00:00Z")
    assert external["tasks"][117]["target"] is None
    protected = state()
    protected["protectedContainerGpuOwners"] = [300]
    assert MODULE.next_step(private_policy, external, protected).action == "execute-task"
    MODULE.CHECKPOINT.stage_result(
        external, result_for(external["tasks"][117]), "2026-08-08T02:02:00Z"
    )
    assert MODULE.next_step(private_policy, external, protected).action == "finalize-staged-result"
    protected["vms"]["200"] = "running"
    refused(private_policy, external, protected, "Every test VM")
    checks += 4

    paused = checkpoint_at(0)
    MODULE.CHECKPOINT.begin_next(paused, "2026-08-08T03:00:00Z")
    MODULE.CHECKPOINT.recover_interrupted(paused, "2026-08-08T03:01:00Z")
    assert MODULE.next_step(private_policy, paused, state()).action == "await-explicit-retry"
    checks += 1

    forbidden = {"asyncio", "http", "os", "requests", "socket", "subprocess", "urllib"}
    assert imported_roots(MODULE_PATH).isdisjoint(forbidden)
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert all(value not in source for value in ("shell=True", "ssh ", "qm ", "pct ", "pvesh "))
    checks += 2
    print(f"Alpha 2 campaign scheduler passed {checks} hostile offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
