#!/usr/bin/env python3
"""Pure policy engine for restricted Alpha 2 Proxmox control.

This module cannot execute commands or contact a host. It validates a private
allowlist and decides whether an already-authenticated wrapper may perform one
bounded operation from trusted live state.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUEST_ID = re.compile(r"^[0-9a-f]{32}$")
TARGET_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
ALLOWED_ACTIONS = {
    "status",
    "start",
    "shutdown",
    "guarded-stop",
    "gpu-attach",
    "gpu-detach",
}
MUTATING_ACTIONS = ALLOWED_ACTIONS - {"status"}
POWER_STATES = {"running", "stopped"}
DEPLOYMENT_STATES = {"inventory-only", "reviewed-and-enabled"}


class PolicyError(ValueError):
    """The private policy, request, or live state is invalid."""


class PolicyRefusal(RuntimeError):
    """A valid request is unsafe in the trusted current state."""


@dataclass(frozen=True)
class Decision:
    action: str
    target: str | None
    vmid: int | None
    mutating: bool
    reason: str

    def public_result(self) -> dict[str, Any]:
        """Return a result that contains no private host or VM identity."""
        return {
            "action": self.action,
            "target": self.target,
            "mutating": self.mutating,
            "reason": self.reason,
        }


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024:
            raise PolicyError(f"Unsafe {label} file.")
        value = json.loads(path.read_text(encoding="utf-8"))
    except PolicyError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PolicyError(f"Cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise PolicyError(f"{label} must be a JSON object.")
    return value


def load_private_policy(path: Path) -> dict[str, Any]:
    value = _load_object(path, "private policy")
    validate_private_policy(value)
    return value


def load_request(path: Path) -> dict[str, Any]:
    value = _load_object(path, "control request")
    validate_request(value)
    return value


def _integer(value: Any, minimum: int, maximum: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
        raise PolicyError(f"{label} must be an integer from {minimum} through {maximum}.")
    return value


def validate_private_policy(policy: Any) -> None:
    expected = {
        "schemaVersion",
        "campaignId",
        "deploymentState",
        "nodeName",
        "gpuMappingId",
        "gpuMappingCanonicalSha256",
        "gpuSlot",
        "targets",
        "excludedVmIds",
        "excludedContainerIds",
        "limits",
    }
    if not isinstance(policy, dict) or set(policy) != expected:
        raise PolicyError("Private policy fields do not match the reviewed schema.")
    if policy["schemaVersion"] != 1 or policy["campaignId"] != "alpha2-linux-long-term":
        raise PolicyError("Private policy is not bound to the Alpha 2 Linux campaign.")
    if policy["deploymentState"] not in DEPLOYMENT_STATES:
        raise PolicyError("Private policy deployment state is invalid.")
    if not isinstance(policy["nodeName"], str) or not SAFE_ID.fullmatch(policy["nodeName"]):
        raise PolicyError("nodeName is invalid.")
    if not isinstance(policy["gpuMappingId"], str) or not SAFE_ID.fullmatch(policy["gpuMappingId"]):
        raise PolicyError("gpuMappingId is invalid.")
    if (
        not isinstance(policy["gpuMappingCanonicalSha256"], str)
        or not SHA256.fullmatch(policy["gpuMappingCanonicalSha256"])
    ):
        raise PolicyError("gpuMappingCanonicalSha256 is invalid.")
    if policy["gpuSlot"] != "hostpci0":
        raise PolicyError("Only the reviewed hostpci0 slot is allowed.")

    targets = policy["targets"]
    if not isinstance(targets, list) or len(targets) != 10:
        raise PolicyError("Private policy requires exactly ten campaign targets.")
    target_ids: set[str] = set()
    vmids: set[int] = set()
    for target in targets:
        if not isinstance(target, dict) or set(target) != {"id", "vmid"}:
            raise PolicyError("Every private target requires only id and vmid.")
        target_id = target["id"]
        if not isinstance(target_id, str) or not TARGET_ID.fullmatch(target_id):
            raise PolicyError("Private target id is invalid.")
        vmid = _integer(target["vmid"], 100, 999_999_999, f"VM id for {target_id}")
        if target_id in target_ids or vmid in vmids:
            raise PolicyError("Private target ids and VM ids must be unique.")
        target_ids.add(target_id)
        vmids.add(vmid)

    excluded = policy["excludedVmIds"]
    if not isinstance(excluded, list):
        raise PolicyError("Excluded VM ids must be a list.")
    excluded_ids = {
        _integer(value, 100, 999_999_999, "excluded VM id") for value in excluded
    }
    if len(excluded_ids) != len(excluded) or excluded_ids & vmids:
        raise PolicyError("Excluded VM ids must be unique and outside the target allowlist.")

    excluded_containers = policy["excludedContainerIds"]
    if not isinstance(excluded_containers, list) or not excluded_containers:
        raise PolicyError("At least one explicitly excluded container id is required.")
    excluded_container_ids = {
        _integer(value, 100, 999_999_999, "excluded container id")
        for value in excluded_containers
    }
    if (
        len(excluded_container_ids) != len(excluded_containers)
        or excluded_container_ids & vmids
        or excluded_container_ids & excluded_ids
    ):
        raise PolicyError(
            "Excluded container ids must be unique and outside every VM id set."
        )

    limits = policy["limits"]
    if not isinstance(limits, dict) or set(limits) != {
        "gracefulShutdownSeconds",
        "maximumConcurrentGpuOwners",
        "minimumLocalZfsFreePercent",
        "maximumRequestBytes",
    }:
        raise PolicyError("Private policy limits do not match the reviewed schema.")
    _integer(limits["gracefulShutdownSeconds"], 60, 900, "graceful shutdown limit")
    if limits["maximumConcurrentGpuOwners"] != 1:
        raise PolicyError("Exactly one concurrent GPU owner is allowed.")
    _integer(limits["minimumLocalZfsFreePercent"], 16, 50, "minimum ZFS free percent")
    _integer(limits["maximumRequestBytes"], 256, 16_384, "maximum request bytes")


def validate_request(request: Any) -> None:
    if not isinstance(request, dict) or set(request) != {
        "schemaVersion",
        "campaignId",
        "requestId",
        "action",
        "target",
    }:
        raise PolicyError("Control request fields do not match the reviewed schema.")
    if request["schemaVersion"] != 1 or request["campaignId"] != "alpha2-linux-long-term":
        raise PolicyError("Control request is not bound to the Alpha 2 Linux campaign.")
    if not isinstance(request["requestId"], str) or not REQUEST_ID.fullmatch(request["requestId"]):
        raise PolicyError("Control requestId must be 32 lowercase hexadecimal characters.")
    if request["action"] not in ALLOWED_ACTIONS:
        raise PolicyError("Control action is not allowlisted.")
    target = request["target"]
    if request["action"] == "status":
        if target is not None and (
            not isinstance(target, str) or not TARGET_ID.fullmatch(target)
        ):
            raise PolicyError("Status target is invalid.")
    elif not isinstance(target, str) or not TARGET_ID.fullmatch(target):
        raise PolicyError("A safe target id is required for this action.")


def _target_map(policy: dict[str, Any]) -> dict[str, int]:
    return {target["id"]: target["vmid"] for target in policy["targets"]}


def validate_live_state(policy: dict[str, Any], state: Any) -> None:
    if not isinstance(state, dict) or set(state) != {
        "nodeName",
        "gpuMappingCanonicalSha256",
        "zfsFreePercent",
        "vms",
        "protectedVms",
        "protectedContainers",
        "gpuConfiguredVmIds",
        "gpuOwners",
        "protectedContainerGpuOwners",
        "unknownPassthroughVmIds",
        "unknownPassthroughContainerIds",
        "shutdownTimedOutVmIds",
    }:
        raise PolicyError("Trusted live-state fields do not match the reviewed schema.")
    if state["nodeName"] != policy["nodeName"]:
        raise PolicyRefusal("The Proxmox node identity changed.")
    free = state["zfsFreePercent"]
    if not isinstance(free, (int, float)) or isinstance(free, bool) or not 0 <= free <= 100:
        raise PolicyError("Trusted ZFS free percentage is invalid.")

    expected_vmids = set(_target_map(policy).values())
    vms = state["vms"]
    if not isinstance(vms, dict) or set(vms) != {str(value) for value in expected_vmids}:
        raise PolicyRefusal("Trusted live state does not contain the exact VM allowlist.")
    if any(value not in POWER_STATES for value in vms.values()):
        raise PolicyError("Trusted VM state is invalid.")

    expected_protected_vmids = {str(value) for value in policy["excludedVmIds"]}
    protected_vms = state["protectedVms"]
    if not isinstance(protected_vms, dict) or set(protected_vms) != expected_protected_vmids:
        raise PolicyRefusal("Trusted live state does not contain the exact protected VM set.")
    if any(value not in POWER_STATES for value in protected_vms.values()):
        raise PolicyError("Trusted protected-VM state is invalid.")

    expected_container_ids = {str(value) for value in policy["excludedContainerIds"]}
    containers = state["protectedContainers"]
    if not isinstance(containers, dict) or set(containers) != expected_container_ids:
        raise PolicyRefusal(
            "Trusted live state does not contain the exact protected container set."
        )
    if any(value not in POWER_STATES for value in containers.values()):
        raise PolicyError("Trusted protected-container state is invalid.")

    for field in (
        "gpuConfiguredVmIds",
        "gpuOwners",
        "protectedContainerGpuOwners",
        "unknownPassthroughVmIds",
        "unknownPassthroughContainerIds",
        "shutdownTimedOutVmIds",
    ):
        values = state[field]
        if not isinstance(values, list) or any(
            not isinstance(value, int) or isinstance(value, bool) for value in values
        ) or len(values) != len(set(values)):
            raise PolicyError(f"Trusted {field} must be a unique integer array.")
    owners = set(state["gpuOwners"])
    configured = set(state["gpuConfiguredVmIds"])
    container_owners = set(state["protectedContainerGpuOwners"])
    expected_container_vmids = set(policy["excludedContainerIds"])
    if (
        not configured.issubset(expected_vmids)
        or not owners.issubset(configured)
        or not container_owners.issubset(
        expected_container_vmids
        )
    ):
        raise PolicyRefusal("The GPU ownership inventory escaped the reviewed sets.")
    if not set(state["shutdownTimedOutVmIds"]).issubset(expected_vmids):
        raise PolicyRefusal("Shutdown timeout state contains an unapproved VM.")


def decide(policy: dict[str, Any], request: dict[str, Any], state: dict[str, Any]) -> Decision:
    validate_private_policy(policy)
    validate_request(request)
    validate_live_state(policy, state)
    target_map = _target_map(policy)
    target = request["target"]
    action = request["action"]
    if target is not None and target not in target_map:
        raise PolicyRefusal("The requested target is outside the private allowlist.")
    vmid = target_map.get(target) if target is not None else None
    if action == "status":
        return Decision(action, target, vmid, False, "approved-read-only-status")
    if policy["deploymentState"] != "reviewed-and-enabled":
        raise PolicyRefusal("Private policy is inventory-only; mutation is not enabled.")

    assert vmid is not None
    vm_state = state["vms"][str(vmid)]
    owners = set(state["gpuOwners"])
    configured = set(state["gpuConfiguredVmIds"])
    protected_container_owners = set(state["protectedContainerGpuOwners"])
    running_vmids = {
        int(candidate) for candidate, power in state["vms"].items() if power == "running"
    }
    mapping_changed = (
        state["gpuMappingCanonicalSha256"]
        != policy["gpuMappingCanonicalSha256"]
    )
    if action == "start":
        if mapping_changed:
            raise PolicyRefusal("The reviewed GPU resource mapping changed.")
        if state["zfsFreePercent"] < policy["limits"]["minimumLocalZfsFreePercent"]:
            raise PolicyRefusal("The ZFS free-space stop threshold was reached.")
        if vm_state != "stopped":
            raise PolicyRefusal("The target VM is not stopped.")
        if running_vmids:
            raise PolicyRefusal("Another approved VM is already running.")
        if vmid in state["unknownPassthroughVmIds"]:
            raise PolicyRefusal("The target VM has an unapproved passthrough entry.")
        if vmid in configured and (
            protected_container_owners
            or owners
            or any(power == "running" for power in state["protectedVms"].values())
        ):
            raise PolicyRefusal("The target GPU is not exclusively available.")
        return Decision(action, target, vmid, True, "approved-allowlisted-start")
    if action == "shutdown":
        if vm_state != "running":
            raise PolicyRefusal("The target VM is not running.")
        return Decision(action, target, vmid, True, "approved-graceful-shutdown")
    if action == "guarded-stop":
        if vm_state != "running" or vmid not in state["shutdownTimedOutVmIds"]:
            raise PolicyRefusal("A verified graceful-shutdown timeout is required.")
        return Decision(action, target, vmid, True, "approved-stop-after-timeout")
    if action == "gpu-attach":
        if mapping_changed:
            raise PolicyRefusal("The reviewed GPU resource mapping changed.")
        if state["zfsFreePercent"] < policy["limits"]["minimumLocalZfsFreePercent"]:
            raise PolicyRefusal("The ZFS free-space stop threshold was reached.")
        if running_vmids:
            raise PolicyRefusal("Every approved VM must be stopped before GPU assignment.")
        if owners or protected_container_owners or configured:
            raise PolicyRefusal("The GPU mapping already has an owner.")
        if state["unknownPassthroughVmIds"]:
            raise PolicyRefusal("An unapproved passthrough entry is present.")
        if state["unknownPassthroughContainerIds"]:
            raise PolicyRefusal("An unapproved container passthrough entry is present.")
        return Decision(action, target, vmid, True, "approved-exclusive-gpu-attach")
    if action == "gpu-detach":
        if vm_state != "stopped":
            raise PolicyRefusal("The GPU owner must be stopped before detach.")
        if vmid not in configured or owners:
            raise PolicyRefusal("The requested VM is not a stopped configured GPU owner.")
        return Decision(action, target, vmid, True, "approved-exclusive-gpu-detach")
    raise AssertionError("Validated action was not handled.")
