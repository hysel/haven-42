#!/usr/bin/env python3
"""Pure next-step scheduler for the Alpha 2 Linux validation campaign.

This module cannot execute commands or contact a machine. It combines the
reviewed campaign checkpoint with trusted Proxmox live state and returns one
bounded next step. The live adapter must execute control steps through the
separate Proxmox policy engine and persist every checkpoint transition.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKPOINT = _load(
    "alpha2_campaign_checkpoint",
    ROOT / "scripts/alpha2-linux-campaign-checkpoint.py",
)
CONTROL = _load(
    "alpha2_proxmox_control_policy",
    ROOT / "scripts/alpha2-proxmox-control-policy.py",
)


class SchedulerRefusal(RuntimeError):
    """Current trusted state cannot safely advance the campaign."""


@dataclass(frozen=True)
class Step:
    kind: str
    action: str
    target: str | None
    task_id: str | None
    reason: str

    def public_result(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "action": self.action,
            "target": self.target,
            "taskId": self.task_id,
            "reason": self.reason,
        }


def _request(action: str, target: str | None) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "requestId": "00000000000000000000000000000000",
        "action": action,
        "target": target,
    }


def _control_step(
    policy: dict[str, Any],
    state: dict[str, Any],
    task: dict[str, Any],
    action: str,
) -> Step:
    decision = CONTROL.decide(policy, _request(action, task["target"]), state)
    return Step("control", action, task["target"], task["id"], decision.reason)


def _shutdown_step(
    policy: dict[str, Any], state: dict[str, Any], task: dict[str, Any]
) -> Step:
    vmid = {item["id"]: item["vmid"] for item in policy["targets"]}[task["target"]]
    if vmid in state["shutdownTimedOutVmIds"]:
        raise SchedulerRefusal("The graceful guest shutdown timed out; manual review is required.")
    return _control_step(policy, state, task, "shutdown")


def next_step(
    policy: dict[str, Any],
    checkpoint: dict[str, Any],
    state: dict[str, Any],
) -> Step:
    """Return one safe next step without changing any input object."""
    CHECKPOINT.validate_checkpoint(checkpoint)
    CONTROL.validate_private_policy(policy)
    CONTROL.validate_live_state(policy, state)

    if checkpoint["status"] == "complete":
        return Step("terminal", "complete", None, None, "all-reviewed-tasks-passed")
    if checkpoint["status"] == "paused":
        return Step(
            "terminal",
            "await-explicit-retry",
            None,
            checkpoint["tasks"][checkpoint["nextTaskIndex"]]["id"],
            checkpoint["pauseCode"] or "campaign-paused",
        )
    task = checkpoint["tasks"][checkpoint["nextTaskIndex"]]
    if checkpoint["status"] == "ready":
        return Step("checkpoint", "begin-next", task["target"], task["id"], "task-ready")
    if task["status"] != "running":
        raise SchedulerRefusal("The active checkpoint task is not running.")

    running_vmids = {
        int(vmid) for vmid, power in state["vms"].items() if power == "running"
    }
    target_map = {item["id"]: item["vmid"] for item in policy["targets"]}

    # The protected external provider is never controlled by this scheduler.
    if task["target"] is None:
        if running_vmids:
            raise SchedulerRefusal(
                "Every test VM must be stopped for protected-provider comparison."
            )
        if task["result"] is None:
            return Step(
                "execute", "execute-task", None, task["id"], "protected-provider-ready"
            )
        return Step(
            "checkpoint", "finalize-staged-result", None, task["id"], "cleanup-proved"
        )

    vmid = target_map[task["target"]]
    other_running = running_vmids - {vmid}
    if other_running:
        raise SchedulerRefusal("Another approved test VM is still running.")
    power = state["vms"][str(vmid)]
    configured_vmids = set(state["gpuConfiguredVmIds"])
    vm_owners = set(state["gpuOwners"])
    protected_owners = set(state["protectedContainerGpuOwners"])

    if task["result"] is not None:
        if power == "running":
            return _shutdown_step(policy, state, task)
        return Step(
            "checkpoint",
            "finalize-staged-result",
            task["target"],
            task["id"],
            "shutdown-proved-static-gpu-mapping-unchanged",
        )

    if task["requiresGpu"]:
        if protected_owners:
            raise SchedulerRefusal("The protected container currently owns the GPU.")
        if vm_owners and vm_owners != {vmid}:
            raise SchedulerRefusal("Another approved VM currently owns the GPU.")
        if vmid not in configured_vmids:
            raise SchedulerRefusal("The target lacks its owner-configured static GPU mapping.")
        if power == "stopped":
            return _control_step(policy, state, task, "start")
        return Step(
            "execute", "execute-task", task["target"], task["id"], "exclusive-gpu-ready"
        )

    # CPU work uses a fixed guest-side CPU mode and must prove zero GPU
    # residency. The Proxmox mapping is immutable under this controller.
    if power == "stopped":
        return _control_step(policy, state, task, "start")
    return Step(
        "execute", "execute-task", task["target"], task["id"],
        "cpu-target-ready-static-gpu-mapping-unchanged",
    )
