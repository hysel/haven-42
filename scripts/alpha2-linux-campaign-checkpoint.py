#!/usr/bin/env python3
"""Restartable, sanitized checkpoint state for Alpha 2 Linux validation.

The module has no network, process, VM, or GPU authority. It records only
bounded test identifiers and measurements. Machine identity and model content
are intentionally absent from the schema.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config/alpha-2-linux-long-term-validation.json"
MODEL_POLICY_PATH = ROOT / "config/alpha-2-model-selection-policy.json"
MODEL_CATALOG_PATH = ROOT / "config/alpha-2-model-catalog.json"
PLANNER_PATH = ROOT / "scripts/plan-alpha2-linux-long-term-validation.py"
SPEC = importlib.util.spec_from_file_location("alpha2_linux_plan", PLANNER_PATH)
PLANNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = PLANNER
SPEC.loader.exec_module(PLANNER)

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_CODE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
SAFE_PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{0,79}$")
SAFE_VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}$")
TASK_STATUS = {"pending", "running", "passed", "failed", "blocked"}
CAMPAIGN_STATUS = {"ready", "running", "paused", "complete"}
OUTCOMES = {"passed", "failed", "blocked"}
EVIDENCE_BACKENDS = {"cpu", "cuda", "rocm", "vulkan", "metal"}
METRIC_BOUNDS = {
    "promptTokens": (0, 10_000_000),
    "outputTokens": (0, 10_000_000),
    "sessionTokens": (0, 100_000_000),
    "tokensPerSecond": (0, 1_000_000),
    "peakCpuPercent": (0, 100),
    "peakRamBytes": (0, 2**60),
    "peakGpuPercent": (0, 100),
    "peakGpuMemoryBytes": (0, 2**60),
    "samplesAttempted": (0, 10),
    "samplesPassed": (0, 10),
    "samplesFailed": (0, 10),
    "unloadPasses": (0, 10),
}


class CheckpointError(ValueError):
    """Checkpoint input or state is unsafe or inconsistent."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_contract_sha256(contract: dict[str, Any]) -> str:
    encoded = json.dumps(
        contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_model_bindings() -> tuple[str, dict[str, str]]:
    try:
        policy = json.loads(MODEL_POLICY_PATH.read_text(encoding="utf-8"))
        catalog = json.loads(MODEL_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CheckpointError("Cannot read reviewed model bindings.") from exc
    policy_sha = canonical_contract_sha256(policy)
    contract = PLANNER.load_contract(CONTRACT_PATH)
    if policy_sha != contract["modelValidation"]["selectorPolicyCanonicalSha256"]:
        raise CheckpointError("Model policy digest does not match the campaign contract.")
    bindings = {
        item["id"]: item["manifestDigest"] for item in catalog.get("models", [])
    }
    for item in policy.get("comparisonCandidates", []):
        bindings[item["id"]] = item["digest"]
    if any(not SHA256.fullmatch(str(value)) for value in bindings.values()):
        raise CheckpointError("Reviewed model binding contains an invalid digest.")
    return policy_sha, bindings


def build_tasks(contract: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    # Finish one guest before advancing to the next. This is the owner-approved
    # campaign order and avoids repeatedly cycling the same VM and GPU mapping.
    for target in contract["targets"]:
        for stage in contract["stages"]:
            task_id = f"{stage['id']}--{target['id']}"
            tasks.append(
                {
                    "id": task_id,
                    "taskKind": "distribution-stage",
                    "stage": stage["id"],
                    "target": target["id"],
                    "candidateId": None,
                    "capabilityId": None,
                    "evidenceUse": None,
                    "repetitions": 1,
                    "requiresGpu": stage["requiresGpu"],
                    "maximumMinutes": stage["maximumMinutes"],
                    "status": "pending",
                    "attempts": 0,
                    "result": None,
                }
            )
    promotion_targets = [
        target["id"]
        for target in contract["targets"]
        if target["nvidiaLane"] == "promotion-candidate"
    ]
    scope_targets = {
        "all-linux-targets": [target["id"] for target in contract["targets"]],
        "nvidia-promotion-targets": promotion_targets,
        "protected-external-provider": [None],
    }
    repetitions = contract["modelValidation"]["repetitionsPerCell"]
    for lane in contract["modelValidation"]["lanes"]:
        for target in scope_targets[lane["targetScope"]]:
            target_label = target or "protected-external-provider"
            for candidate_id in lane["candidateIds"]:
                for capability_id in lane["capabilities"]:
                    capability_label = capability_id.replace(".", "-")
                    task_id = (
                        f"model--{lane['id']}--{target_label}--"
                        f"{candidate_id}--{capability_label}"
                    )
                    tasks.append(
                        {
                            "id": task_id,
                            "taskKind": "model-validation",
                            "stage": lane["id"],
                            "target": target,
                            "candidateId": candidate_id,
                            "capabilityId": capability_id,
                            "evidenceUse": lane["evidenceUse"],
                            "repetitions": repetitions,
                            "requiresGpu": lane["requiresGpu"],
                            "maximumMinutes": lane["maximumMinutes"],
                            "status": "pending",
                            "attempts": 0,
                            "result": None,
                        }
                    )
    return tasks


def new_checkpoint(candidate_sha256: str, timestamp: str | None = None) -> dict[str, Any]:
    if not isinstance(candidate_sha256, str) or not SHA256.fullmatch(candidate_sha256):
        raise CheckpointError("Candidate SHA-256 must be 64 lowercase hexadecimal characters.")
    contract = PLANNER.load_contract(CONTRACT_PATH)
    created = timestamp or utc_now()
    checkpoint = {
        "schemaVersion": 1,
        "campaignId": contract["campaignId"],
        "release": contract["release"],
        "contractSha256": canonical_contract_sha256(contract),
        "candidateSha256": candidate_sha256,
        "status": "ready",
        "revision": 0,
        "nextTaskIndex": 0,
        "createdAtUtc": created,
        "updatedAtUtc": created,
        "pauseCode": None,
        "tasks": build_tasks(contract),
    }
    validate_checkpoint(checkpoint)
    return checkpoint


def _bounded_number(value: Any, bounds: tuple[float, float], label: str) -> None:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or not bounds[0] <= value <= bounds[1]
    ):
        raise CheckpointError(f"{label} is outside its allowed range.")


def validate_result(result: Any, task: dict[str, Any]) -> None:
    if not isinstance(result, dict) or set(result) != {
        "outcome",
        "errorCode",
        "durationSeconds",
        "metrics",
        "evidence",
    }:
        raise CheckpointError("Task result fields do not match the sanitized schema.")
    if result["outcome"] not in OUTCOMES:
        raise CheckpointError("Task outcome is invalid.")
    error = result["errorCode"]
    if result["outcome"] == "passed":
        if error is not None:
            raise CheckpointError("A passing result cannot contain an error code.")
    elif not isinstance(error, str) or not SAFE_CODE.fullmatch(error):
        raise CheckpointError("A failing or blocked result requires a stable error code.")
    _bounded_number(
        result["durationSeconds"],
        (0, task["maximumMinutes"] * 60 + 60),
        "Task duration",
    )
    metrics = result["metrics"]
    if not isinstance(metrics, dict) or not set(metrics).issubset(METRIC_BOUNDS):
        raise CheckpointError("Task metrics contain an unapproved field.")
    for field, value in metrics.items():
        _bounded_number(value, METRIC_BOUNDS[field], f"Metric {field}")
    sample_fields = {
        "samplesAttempted", "samplesPassed", "samplesFailed", "unloadPasses"
    }
    if task["taskKind"] == "model-validation":
        if not sample_fields.issubset(metrics):
            raise CheckpointError("Model-validation result lacks sample metrics.")
        attempted = metrics["samplesAttempted"]
        passed = metrics["samplesPassed"]
        failed = metrics["samplesFailed"]
        unloaded = metrics["unloadPasses"]
        if (
            any(isinstance(value, bool) or not isinstance(value, int) for value in (
                attempted, passed, failed, unloaded
            ))
            or attempted != passed + failed
            or attempted > task["repetitions"]
            or unloaded > attempted
        ):
            raise CheckpointError("Model-validation sample metrics are inconsistent.")
        if result["outcome"] == "passed" and (
            attempted != task["repetitions"]
            or passed != task["repetitions"]
            or failed != 0
            or unloaded != task["repetitions"]
        ):
            raise CheckpointError("Passing model validation requires every sample and unload.")
        if result["outcome"] == "passed":
            validate_model_evidence(result["evidence"], task)
        elif result["evidence"] is not None:
            validate_model_evidence(result["evidence"], task)
    elif sample_fields & set(metrics):
        raise CheckpointError("Distribution-stage result contains model sample metrics.")
    elif result["evidence"] is not None:
        raise CheckpointError("Distribution-stage result cannot contain model evidence.")


def validate_model_evidence(evidence: Any, task: dict[str, Any]) -> None:
    expected = {
        "selectorPolicyCanonicalSha256",
        "modelId",
        "manifestDigest",
        "platformFamily",
        "operatingSystemId",
        "architecture",
        "backendMode",
        "provider",
        "providerVersion",
        "systemMemoryGiB",
        "usableGpuMemoryGiB",
        "storageAdmitted",
        "capability",
        "capabilityPassed",
        "automaticEvidenceCandidate",
    }
    if not isinstance(evidence, dict) or set(evidence) != expected:
        raise CheckpointError("Model evidence fields do not match the reviewed schema.")
    policy_sha, bindings = _load_model_bindings()
    model_id = task["candidateId"]
    if (
        evidence["selectorPolicyCanonicalSha256"] != policy_sha
        or evidence["modelId"] != model_id
        or evidence["manifestDigest"] != bindings.get(model_id)
    ):
        raise CheckpointError("Model evidence is not bound to the exact reviewed artifact.")
    if (
        evidence["platformFamily"] != "linux"
        or not isinstance(evidence["operatingSystemId"], str)
        or not SAFE_PROFILE_ID.fullmatch(evidence["operatingSystemId"])
        or evidence["architecture"] != "x64"
        or evidence["backendMode"] not in EVIDENCE_BACKENDS
        or evidence["provider"] != "ollama"
        or not isinstance(evidence["providerVersion"], str)
        or not SAFE_VERSION.fullmatch(evidence["providerVersion"])
    ):
        raise CheckpointError("Model evidence execution profile is invalid.")
    for field in ("systemMemoryGiB", "usableGpuMemoryGiB"):
        _bounded_number(evidence[field], (0, 1024), f"Evidence {field}")
    if (
        evidence["storageAdmitted"] is not True
        or evidence["capability"] != task["capabilityId"]
        or evidence["capabilityPassed"] is not True
    ):
        raise CheckpointError("Model evidence does not prove the tested capability.")
    expected_candidate = task["evidenceUse"] == "automatic-candidate"
    if evidence["automaticEvidenceCandidate"] is not expected_candidate:
        raise CheckpointError("Model evidence promotion boundary changed.")
    if task["stage"] == "cpu-selection" and (
        evidence["backendMode"] != "cpu" or evidence["usableGpuMemoryGiB"] != 0
    ):
        raise CheckpointError("CPU-selection evidence must prove the CPU execution path.")
    if task["stage"] == "cuda-selection" and evidence["backendMode"] != "cuda":
        raise CheckpointError("CUDA-selection evidence must prove the CUDA execution path.")


def validate_checkpoint(checkpoint: Any) -> None:
    expected = {
        "schemaVersion",
        "campaignId",
        "release",
        "contractSha256",
        "candidateSha256",
        "status",
        "revision",
        "nextTaskIndex",
        "createdAtUtc",
        "updatedAtUtc",
        "pauseCode",
        "tasks",
    }
    if not isinstance(checkpoint, dict) or set(checkpoint) != expected:
        raise CheckpointError("Checkpoint fields do not match the reviewed schema.")
    if checkpoint["schemaVersion"] != 1:
        raise CheckpointError("Unsupported checkpoint schemaVersion.")
    if checkpoint["campaignId"] != "alpha2-linux-long-term" or checkpoint["release"] != "0.4.0-alpha.2":
        raise CheckpointError("Checkpoint is not bound to the Alpha 2 Linux campaign.")
    if not SHA256.fullmatch(str(checkpoint["candidateSha256"])):
        raise CheckpointError("Checkpoint candidate digest is invalid.")
    if checkpoint["status"] not in CAMPAIGN_STATUS:
        raise CheckpointError("Checkpoint campaign status is invalid.")
    revision = checkpoint["revision"]
    index = checkpoint["nextTaskIndex"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise CheckpointError("Checkpoint revision is invalid.")
    if not isinstance(index, int) or isinstance(index, bool):
        raise CheckpointError("Checkpoint task index is invalid.")
    if checkpoint["pauseCode"] is not None and (
        not isinstance(checkpoint["pauseCode"], str)
        or not SAFE_CODE.fullmatch(checkpoint["pauseCode"])
    ):
        raise CheckpointError("Checkpoint pause code is invalid.")

    contract = PLANNER.load_contract(CONTRACT_PATH)
    if checkpoint["contractSha256"] != canonical_contract_sha256(contract):
        raise CheckpointError("Checkpoint contract digest does not match the reviewed contract.")
    expected_tasks = build_tasks(contract)
    tasks = checkpoint["tasks"]
    if not isinstance(tasks, list) or len(tasks) != len(expected_tasks):
        raise CheckpointError("Checkpoint does not contain the exact campaign task set.")
    if not 0 <= index <= len(tasks):
        raise CheckpointError("Checkpoint task index is outside the task set.")
    running = 0
    for position, (task, expected_task) in enumerate(zip(tasks, expected_tasks)):
        if not isinstance(task, dict) or set(task) != set(expected_task):
            raise CheckpointError("Checkpoint task fields do not match the reviewed schema.")
        for field in (
            "id", "taskKind", "stage", "target", "candidateId", "capabilityId",
            "evidenceUse", "repetitions", "requiresGpu", "maximumMinutes",
        ):
            if task[field] != expected_task[field]:
                raise CheckpointError("Checkpoint task identity or boundary changed.")
        if task["status"] not in TASK_STATUS:
            raise CheckpointError("Checkpoint task status is invalid.")
        attempts = task["attempts"]
        if not isinstance(attempts, int) or isinstance(attempts, bool) or not 0 <= attempts <= 100:
            raise CheckpointError("Checkpoint task attempt count is invalid.")
        if task["status"] == "running":
            running += 1
        if task["result"] is not None:
            validate_result(task["result"], task)
        if task["status"] == "pending" and task["result"] is not None:
            raise CheckpointError("A pending task cannot contain a result.")
        if task["status"] in {"passed", "failed", "blocked"}:
            if task["result"] is None or task["result"]["outcome"] != task["status"]:
                raise CheckpointError("A terminal task requires its matching result.")
        if position < index and task["status"] != "passed":
            raise CheckpointError("A task before nextTaskIndex is not passed.")
        if position > index and task["status"] != "pending":
            raise CheckpointError("A future task is not pending.")
    if running > 1:
        raise CheckpointError("More than one task is running.")
    if checkpoint["status"] == "complete" and index != len(tasks):
        raise CheckpointError("An incomplete task set cannot be marked complete.")


def begin_next(checkpoint: dict[str, Any], timestamp: str | None = None) -> dict[str, Any]:
    validate_checkpoint(checkpoint)
    if checkpoint["status"] not in {"ready", "running"}:
        raise CheckpointError("A paused or complete campaign cannot begin a task.")
    index = checkpoint["nextTaskIndex"]
    if index == len(checkpoint["tasks"]):
        raise CheckpointError("The campaign has no pending task.")
    task = checkpoint["tasks"][index]
    if task["status"] == "running":
        return checkpoint
    if task["status"] != "pending":
        raise CheckpointError("The next campaign task is not pending.")
    task["status"] = "running"
    task["attempts"] += 1
    task["result"] = None
    checkpoint["status"] = "running"
    checkpoint["revision"] += 1
    checkpoint["updatedAtUtc"] = timestamp or utc_now()
    validate_checkpoint(checkpoint)
    return checkpoint


def record_result(
    checkpoint: dict[str, Any], result: dict[str, Any], timestamp: str | None = None
) -> dict[str, Any]:
    """Record and immediately finalize a result.

    This convenience path is retained for offline tooling. The live campaign
    controller must use ``stage_result`` followed by ``finalize_staged_result``
    so that a result is durably saved before VM and GPU cleanup begins.
    """
    stage_result(checkpoint, result, timestamp)
    return finalize_staged_result(checkpoint, timestamp)


def stage_result(
    checkpoint: dict[str, Any], result: dict[str, Any], timestamp: str | None = None
) -> dict[str, Any]:
    """Durably stage a sanitized result while its task remains running."""
    validate_checkpoint(checkpoint)
    index = checkpoint["nextTaskIndex"]
    if index == len(checkpoint["tasks"]):
        raise CheckpointError("The campaign is already complete.")
    task = checkpoint["tasks"][index]
    if task["status"] != "running":
        raise CheckpointError("Only the running task can receive a result.")
    if task["result"] is not None:
        raise CheckpointError("The running task already has a staged result.")
    validate_result(result, task)
    task["result"] = result
    checkpoint["revision"] += 1
    checkpoint["updatedAtUtc"] = timestamp or utc_now()
    validate_checkpoint(checkpoint)
    return checkpoint


def finalize_staged_result(
    checkpoint: dict[str, Any], timestamp: str | None = None
) -> dict[str, Any]:
    """Finalize a staged result after the live controller proves cleanup."""
    validate_checkpoint(checkpoint)
    index = checkpoint["nextTaskIndex"]
    if index == len(checkpoint["tasks"]):
        raise CheckpointError("The campaign is already complete.")
    task = checkpoint["tasks"][index]
    if task["status"] != "running" or task["result"] is None:
        raise CheckpointError("The running task has no staged result to finalize.")
    result = task["result"]
    task["status"] = result["outcome"]
    if result["outcome"] == "passed":
        checkpoint["nextTaskIndex"] += 1
        checkpoint["status"] = (
            "complete"
            if checkpoint["nextTaskIndex"] == len(checkpoint["tasks"])
            else "ready"
        )
        checkpoint["pauseCode"] = None
    else:
        checkpoint["status"] = "paused"
        checkpoint["pauseCode"] = result["errorCode"]
    checkpoint["revision"] += 1
    checkpoint["updatedAtUtc"] = timestamp or utc_now()
    validate_checkpoint(checkpoint)
    return checkpoint


def recover_interrupted(
    checkpoint: dict[str, Any], timestamp: str | None = None
) -> dict[str, Any]:
    validate_checkpoint(checkpoint)
    index = checkpoint["nextTaskIndex"]
    if index == len(checkpoint["tasks"]) or checkpoint["tasks"][index]["status"] != "running":
        raise CheckpointError("No interrupted running task exists.")
    task = checkpoint["tasks"][index]
    if task["result"] is not None:
        # The test result is already durable. Keep the task running so the
        # controller can re-prove shutdown and GPU cleanup before finalizing.
        checkpoint["revision"] += 1
        checkpoint["updatedAtUtc"] = timestamp or utc_now()
        validate_checkpoint(checkpoint)
        return checkpoint
    task["status"] = "blocked"
    task["result"] = {
        "outcome": "blocked",
        "errorCode": "controller-interrupted",
        "durationSeconds": 0,
        "metrics": {},
        "evidence": None,
    }
    checkpoint["status"] = "paused"
    checkpoint["pauseCode"] = "controller-interrupted"
    checkpoint["revision"] += 1
    checkpoint["updatedAtUtc"] = timestamp or utc_now()
    validate_checkpoint(checkpoint)
    return checkpoint


def approve_retry(checkpoint: dict[str, Any], timestamp: str | None = None) -> dict[str, Any]:
    validate_checkpoint(checkpoint)
    index = checkpoint["nextTaskIndex"]
    if checkpoint["status"] != "paused" or index == len(checkpoint["tasks"]):
        raise CheckpointError("No paused task is available for explicit retry.")
    task = checkpoint["tasks"][index]
    if task["status"] not in {"failed", "blocked"}:
        raise CheckpointError("The paused task is not retryable.")
    task["status"] = "pending"
    task["result"] = None
    checkpoint["status"] = "ready"
    checkpoint["pauseCode"] = None
    checkpoint["revision"] += 1
    checkpoint["updatedAtUtc"] = timestamp or utc_now()
    validate_checkpoint(checkpoint)
    return checkpoint


def resolve_checkpoint(root: Path) -> Path:
    if root.is_symlink():
        raise CheckpointError("Checkpoint root must not be a symlink.")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise CheckpointError("Checkpoint root must already exist.") from exc
    if not resolved.is_dir():
        raise CheckpointError("Checkpoint root must be a directory.")
    if os.name == "posix" and stat.S_IMODE(resolved.stat().st_mode) & 0o022:
        raise CheckpointError("Checkpoint root must not be group or world writable.")
    target = resolved / "checkpoint.json"
    if target.is_symlink():
        raise CheckpointError("Checkpoint file must not be a symlink.")
    return target


def load_checkpoint(root: Path) -> dict[str, Any]:
    target = resolve_checkpoint(root)
    try:
        if target.stat().st_size > 2 * 1024 * 1024:
            raise CheckpointError("Checkpoint exceeds its size limit.")
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CheckpointError(f"Cannot read checkpoint: {exc}") from exc
    validate_checkpoint(value)
    return value


def save_checkpoint(root: Path, checkpoint: dict[str, Any]) -> None:
    validate_checkpoint(checkpoint)
    target = resolve_checkpoint(root)
    encoded = (json.dumps(checkpoint, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".checkpoint-", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        if os.name == "posix":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        if os.name == "posix":
            directory = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def public_summary(checkpoint: dict[str, Any]) -> dict[str, Any]:
    validate_checkpoint(checkpoint)
    counts = {status: 0 for status in TASK_STATUS}
    for task in checkpoint["tasks"]:
        counts[task["status"]] += 1
    current = None
    if checkpoint["nextTaskIndex"] < len(checkpoint["tasks"]):
        task = checkpoint["tasks"][checkpoint["nextTaskIndex"]]
        current = {
            "id": task["id"],
            "taskKind": task["taskKind"],
            "stage": task["stage"],
            "target": task["target"],
        }
    return {
        "campaignId": checkpoint["campaignId"],
        "release": checkpoint["release"],
        "status": checkpoint["status"],
        "revision": checkpoint["revision"],
        "taskCounts": counts,
        "currentTask": current,
        "pauseCode": checkpoint["pauseCode"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    initialize = subparsers.add_parser("init")
    initialize.add_argument("--candidate-sha256", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("begin-next")
    subparsers.add_parser("recover-interrupted")
    subparsers.add_parser("approve-retry")
    arguments = parser.parse_args()
    try:
        if arguments.command == "init":
            target = resolve_checkpoint(arguments.root)
            if target.exists():
                raise CheckpointError("Checkpoint already exists; initialization refused.")
            checkpoint = new_checkpoint(arguments.candidate_sha256)
            save_checkpoint(arguments.root, checkpoint)
        else:
            checkpoint = load_checkpoint(arguments.root)
            if arguments.command == "begin-next":
                begin_next(checkpoint)
                save_checkpoint(arguments.root, checkpoint)
            elif arguments.command == "recover-interrupted":
                recover_interrupted(checkpoint)
                save_checkpoint(arguments.root, checkpoint)
            elif arguments.command == "approve-retry":
                approve_retry(checkpoint)
                save_checkpoint(arguments.root, checkpoint)
        print(json.dumps(public_summary(checkpoint), indent=2, sort_keys=True))
    except CheckpointError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
