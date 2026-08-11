#!/usr/bin/env python3
"""Pure parser for trusted Alpha 2 Proxmox inventory snapshots.

The parser has no process, shell, network, or Proxmox authority. A separate
root-owned collector must supply exact command outputs. This module converts
those outputs into the strict live-state schema consumed by the control policy.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "scripts/alpha2-proxmox-control-policy.py"
SPEC = importlib.util.spec_from_file_location("alpha2_live_policy", POLICY_PATH)
POLICY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = POLICY
SPEC.loader.exec_module(POLICY)

PCI_BASE = re.compile(r"^(?:[0-9a-fA-F]{4,8}:)?([0-9a-fA-F]{2}:[0-9a-fA-F]{2})(?:\.[0-7])?$")
NVIDIA_DEVICE = re.compile(r"(?:^|[\s,=])/?dev/nvidia([0-9]{1,2})(?:$|[\s,])")
HOSTPCI = re.compile(r"^(hostpci[0-9]+):\s*(.+)$", re.MULTILINE)


class LiveStateError(ValueError):
    """The supplied read-only inventory is incomplete or ambiguous."""


def _canonical_mapping_sha256(mapping: list[str]) -> str:
    encoded = json.dumps(
        sorted(mapping), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _pci_base(value: str) -> str:
    match = PCI_BASE.fullmatch(value.strip())
    if not match:
        raise LiveStateError("A PCI address is malformed.")
    return match.group(1).lower()


def _parse_list_ids(text: str, label: str) -> set[int]:
    result: set[int] = set()
    for line in text.splitlines():
        fields = line.split()
        if not fields or not fields[0].isdigit():
            continue
        value = int(fields[0])
        if not 100 <= value <= 999_999_999:
            raise LiveStateError(f"{label} contains an out-of-range guest id.")
        if value in result:
            raise LiveStateError(f"{label} contains a duplicate guest id.")
        result.add(value)
    if not result:
        raise LiveStateError(f"{label} contains no guest ids.")
    return result


def _parse_power(value: str, label: str) -> str:
    match = re.fullmatch(r"status:\s*(running|stopped)\s*", value)
    if not match:
        raise LiveStateError(f"{label} has an invalid power state.")
    return match.group(1)


def _zfs_free_percent(text: str) -> float:
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 7 and fields[0] == "local_zfs":
            if fields[2] != "active":
                raise LiveStateError("local_zfs is not active.")
            try:
                total = int(fields[3])
                available = int(fields[5])
            except ValueError as exc:
                raise LiveStateError("local_zfs capacity is malformed.") from exc
            if total <= 0 or not 0 <= available <= total:
                raise LiveStateError("local_zfs capacity is invalid.")
            return round(available * 100 / total, 4)
    raise LiveStateError("local_zfs is absent from storage status.")


def _mapping_details(
    mappings: Any, mapping_id: str, node_name: str
) -> tuple[str, str]:
    if not isinstance(mappings, list):
        raise LiveStateError("PCI resource mappings must be an array.")
    matches = [item for item in mappings if isinstance(item, dict) and item.get("id") == mapping_id]
    if len(matches) != 1:
        raise LiveStateError("The reviewed PCI resource mapping is absent or duplicated.")
    item = matches[0]
    mapping = item.get("map")
    if item.get("type") != "pci" or not isinstance(mapping, list) or not mapping or any(
        not isinstance(value, str) or not value for value in mapping
    ):
        raise LiveStateError("The reviewed PCI resource mapping is malformed.")
    node_paths: list[str] = []
    for entry in mapping:
        fields = dict(
            part.split("=", 1) for part in entry.split(",") if "=" in part
        )
        if fields.get("node") == node_name and "path" in fields:
            node_paths.append(fields["path"])
    if len(node_paths) != 1:
        raise LiveStateError("The reviewed mapping lacks one exact path for this node.")
    return _canonical_mapping_sha256(mapping), _pci_base(node_paths[0])


def _gpu_index(csv_text: str, expected_pci_base: str) -> int | None:
    matches: list[int] = []
    seen: set[int] = set()
    for line in csv_text.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 4 or not fields[0].isdigit():
            raise LiveStateError("Host NVIDIA inventory is malformed.")
        index = int(fields[0])
        if index in seen or not 0 <= index <= 64:
            raise LiveStateError("Host NVIDIA inventory has an invalid GPU index.")
        seen.add(index)
        if _pci_base(fields[2]) == expected_pci_base:
            matches.append(index)
    if len(matches) > 1:
        raise LiveStateError("The reviewed mapping resolves to multiple NVIDIA GPU indexes.")
    # A GPU bound for PCI passthrough is intentionally absent from nvidia-smi.
    # In that state it cannot be one of the /dev/nvidiaN devices exposed to a
    # container, so None is a safe and meaningful result.
    return matches[0] if matches else None


def _mapping_value(value: str, mapping_id: str) -> bool:
    fields = [field.strip() for field in value.split(",")]
    return f"mapping={mapping_id}" in fields


def _nvidia_indexes(config: str) -> set[int]:
    return {int(match.group(1)) for match in NVIDIA_DEVICE.finditer(config)}


def build_live_state(
    policy: dict[str, Any], snapshot: Any, *, enforce_control_policy: bool = True
) -> dict[str, Any]:
    POLICY.validate_private_policy(policy)
    expected = {
        "schemaVersion",
        "campaignId",
        "nodeName",
        "storageStatus",
        "pciMappings",
        "hostNvidiaSmiCsv",
        "vmList",
        "containerList",
        "vmStatuses",
        "vmConfigs",
        "containerStatuses",
        "containerConfigs",
        "shutdownTimedOutVmIds",
    }
    if (
        not isinstance(snapshot, dict)
        or set(snapshot) != expected
        or snapshot.get("schemaVersion") != 1
        or snapshot.get("campaignId") != "alpha2-linux-long-term"
    ):
        raise LiveStateError("Inventory snapshot fields do not match the reviewed schema.")
    for field in ("nodeName", "storageStatus", "hostNvidiaSmiCsv", "vmList", "containerList"):
        if not isinstance(snapshot[field], str) or not snapshot[field]:
            raise LiveStateError(f"Inventory field {field} is empty or invalid.")

    vm_ids = _parse_list_ids(snapshot["vmList"], "VM list")
    container_ids = _parse_list_ids(snapshot["containerList"], "container list")
    expected_vm_keys = {str(value) for value in vm_ids}
    expected_container_keys = {str(value) for value in container_ids}
    for field, keys in (
        ("vmStatuses", expected_vm_keys),
        ("vmConfigs", expected_vm_keys),
        ("containerStatuses", expected_container_keys),
        ("containerConfigs", expected_container_keys),
    ):
        value = snapshot[field]
        if (
            not isinstance(value, dict)
            or set(value) != keys
            or any(not isinstance(item, str) for item in value.values())
        ):
            raise LiveStateError(f"Inventory field {field} does not cover the exact guest list.")

    mapping_sha, mapping_pci = _mapping_details(
        snapshot["pciMappings"], policy["gpuMappingId"], snapshot["nodeName"]
    )
    reviewed_gpu_index = _gpu_index(snapshot["hostNvidiaSmiCsv"], mapping_pci)
    target_map = {item["vmid"]: item["id"] for item in policy["targets"]}
    target_vmids = set(target_map)
    protected_vmids = set(policy["excludedVmIds"])
    protected_containers = set(policy["excludedContainerIds"])
    if not target_vmids | protected_vmids <= vm_ids:
        raise LiveStateError("The VM inventory is missing a reviewed target or protected VM.")
    if not protected_containers <= container_ids:
        raise LiveStateError("The container inventory is missing a protected container.")

    gpu_configured_vmids: list[int] = []
    gpu_owners: list[int] = []
    unknown_vms: list[int] = []
    for vmid in sorted(vm_ids):
        config = snapshot["vmConfigs"][str(vmid)]
        entries = HOSTPCI.findall(config)
        for slot, value in entries:
            approved_mapping = slot == policy["gpuSlot"] and _mapping_value(
                value, policy["gpuMappingId"]
            )
            if approved_mapping and vmid in target_vmids:
                gpu_configured_vmids.append(vmid)
                if _parse_power(snapshot["vmStatuses"][str(vmid)], f"VM {vmid}") == "running":
                    gpu_owners.append(vmid)
            else:
                unknown_vms.append(vmid)
    protected_container_owners: list[int] = []
    unknown_containers: list[int] = []
    for container_id in sorted(container_ids):
        indexes = _nvidia_indexes(snapshot["containerConfigs"][str(container_id)])
        if reviewed_gpu_index is None or reviewed_gpu_index not in indexes:
            continue
        if _parse_power(
            snapshot["containerStatuses"][str(container_id)],
            f"container {container_id}",
        ) != "running":
            continue
        if container_id in protected_containers:
            protected_container_owners.append(container_id)
        else:
            unknown_containers.append(container_id)

    state = {
        "nodeName": snapshot["nodeName"],
        "gpuMappingCanonicalSha256": mapping_sha,
        "zfsFreePercent": _zfs_free_percent(snapshot["storageStatus"]),
        "vms": {
            str(vmid): _parse_power(snapshot["vmStatuses"][str(vmid)], f"VM {vmid}")
            for vmid in sorted(target_vmids)
        },
        "protectedVms": {
            str(vmid): _parse_power(
                snapshot["vmStatuses"][str(vmid)], f"protected VM {vmid}"
            )
            for vmid in sorted(protected_vmids)
        },
        "protectedContainers": {
            str(container_id): _parse_power(
                snapshot["containerStatuses"][str(container_id)],
                f"protected container {container_id}",
            )
            for container_id in sorted(protected_containers)
        },
        "gpuConfiguredVmIds": sorted(set(gpu_configured_vmids)),
        "gpuOwners": sorted(set(gpu_owners)),
        "protectedContainerGpuOwners": sorted(set(protected_container_owners)),
        "unknownPassthroughVmIds": sorted(set(unknown_vms)),
        "unknownPassthroughContainerIds": sorted(set(unknown_containers)),
        "shutdownTimedOutVmIds": snapshot["shutdownTimedOutVmIds"],
    }
    if enforce_control_policy:
        POLICY.validate_live_state(policy, state)
    return state
