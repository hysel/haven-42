#!/usr/bin/env python3
"""Hostile offline tests for the Alpha 2 Proxmox live-state parser."""

from __future__ import annotations

import ast
import copy
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts/alpha2-proxmox-live-state.py"
SPEC = importlib.util.spec_from_file_location("alpha2_live_state", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

TARGETS = [
    "ubuntu-26-04-gnome", "ubuntu-24-04-gnome", "debian-13-gnome",
    "linux-mint-22-cinnamon", "pop-os-24-04-cosmic", "fedora-44-gnome",
    "bazzite-kde", "cachyos-kde", "arch-linux-kde", "windows-11-nvidia",
]
MAP_ENTRY = "id=10de:0001,iommugroup=7,node=test-node,path=0000:81:00,subsystem-id=10de:0002"


def policy() -> dict:
    return {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "deploymentState": "inventory-only",
        "nodeName": "test-node",
        "gpuMappingId": "approved-gpu",
        "gpuMappingCanonicalSha256": MODULE._canonical_mapping_sha256([MAP_ENTRY]),
        "gpuSlot": "hostpci0",
        "targets": [
            {"id": target, "vmid": 200 + index} for index, target in enumerate(TARGETS)
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


def snapshot() -> dict:
    vmids = list(range(200, 210)) + [299]
    return {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "nodeName": "test-node",
        "storageStatus": (
            "Name Type Status Total (KiB) Used (KiB) Available (KiB) %\n"
            "local_zfs zfspool active 1000000 800000 200000 80.00%\n"
        ),
        "pciMappings": [{"id": "approved-gpu", "map": [MAP_ENTRY], "type": "pci"}],
        "hostNvidiaSmiCsv": (
            "0, Other GPU, 00000000:01:00.0, GPU-other\n"
            "1, Reviewed GPU, 00000000:81:00.0, GPU-reviewed\n"
        ),
        "vmList": "VMID NAME STATUS\n" + "\n".join(f"{value} vm-{value} stopped" for value in vmids),
        "containerList": "VMID Status Name\n300 running protected\n",
        "vmStatuses": {str(value): "status: stopped\n" for value in vmids},
        "vmConfigs": {str(value): f"name: vm-{value}\n" for value in vmids},
        "containerStatuses": {"300": "status: running\n"},
        "containerConfigs": {"300": "dev0: /dev/nvidia0,gid=44\n"},
        "shutdownTimedOutVmIds": [],
    }


def refused(policy_value: dict, snapshot_value: dict, text: str) -> None:
    try:
        MODULE.build_live_state(policy_value, snapshot_value)
    except (MODULE.LiveStateError, MODULE.POLICY.PolicyError, MODULE.POLICY.PolicyRefusal) as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError("Unsafe inventory was accepted.")


def imports(path: Path) -> set[str]:
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
    raw = snapshot()
    state = MODULE.build_live_state(private_policy, raw)
    assert state["zfsFreePercent"] == 20.0
    assert state["gpuOwners"] == []
    assert state["protectedContainerGpuOwners"] == []
    assert state["unknownPassthroughVmIds"] == []
    checks = 5

    protected_owner = snapshot()
    protected_owner["containerConfigs"]["300"] = "dev0: /dev/nvidia1,gid=44\n"
    state = MODULE.build_live_state(private_policy, protected_owner)
    assert state["protectedContainerGpuOwners"] == [300]
    checks += 1

    mapped = snapshot()
    mapped["vmConfigs"]["200"] += "hostpci0: mapping=approved-gpu,pcie=1\n"
    state = MODULE.build_live_state(private_policy, mapped)
    assert state["gpuConfiguredVmIds"] == [200]
    assert state["gpuOwners"] == []
    checks += 1

    raw_owner = snapshot()
    raw_owner["vmConfigs"]["200"] += "hostpci0: 0000:81:00.0,pcie=1\n"
    state = MODULE.build_live_state(private_policy, raw_owner)
    assert state["unknownPassthroughVmIds"] == [200]
    excluded_owner = snapshot()
    excluded_owner["vmConfigs"]["299"] += "hostpci0: mapping=approved-gpu,pcie=1\n"
    state = MODULE.build_live_state(private_policy, excluded_owner)
    assert state["unknownPassthroughVmIds"] == [299]
    checks += 2

    unknown_container = snapshot()
    unknown_container["containerList"] += "301 running unknown\n"
    unknown_container["containerStatuses"]["301"] = "status: running\n"
    unknown_container["containerConfigs"]["301"] = "dev0: /dev/nvidia1,gid=44\n"
    state = MODULE.build_live_state(private_policy, unknown_container)
    assert state["unknownPassthroughContainerIds"] == [301]
    checks += 1

    changed_mapping = snapshot()
    changed_mapping["pciMappings"][0]["map"][0] = MAP_ENTRY.replace(
        "iommugroup=7", "iommugroup=8"
    )
    state = MODULE.build_live_state(private_policy, changed_mapping)
    assert state["gpuMappingCanonicalSha256"] != private_policy[
        "gpuMappingCanonicalSha256"
    ]
    changed_path = snapshot()
    changed_path["pciMappings"][0]["map"][0] = MAP_ENTRY.replace("81:00", "82:00")
    state = MODULE.build_live_state(private_policy, changed_path)
    assert state["gpuConfiguredVmIds"] == []
    missing_target = snapshot()
    missing_target["vmList"] = missing_target["vmList"].replace("200 vm-200 stopped\n", "")
    missing_target["vmStatuses"].pop("200")
    missing_target["vmConfigs"].pop("200")
    refused(private_policy, missing_target, "missing a reviewed target")
    duplicate_gpu = snapshot()
    duplicate_gpu["hostNvidiaSmiCsv"] += "2, Duplicate, 00000000:81:00.1, GPU-duplicate\n"
    refused(private_policy, duplicate_gpu, "multiple NVIDIA GPU indexes")
    low_storage = snapshot()
    low_storage["storageStatus"] = low_storage["storageStatus"].replace(
        "800000 200000 80.00%", "850000 150000 85.00%"
    )
    assert MODULE.build_live_state(private_policy, low_storage)["zfsFreePercent"] == 15.0
    checks += 5

    malformed = snapshot()
    malformed["vmConfigs"].pop("299")
    refused(private_policy, malformed, "exact guest list")
    changed_node = snapshot()
    changed_node["nodeName"] = "other-node"
    refused(private_policy, changed_node, "one exact path")
    out_of_range = snapshot()
    out_of_range["vmList"] += "\n9999999999 oversized stopped\n"
    out_of_range["vmStatuses"]["9999999999"] = "status: stopped\n"
    out_of_range["vmConfigs"]["9999999999"] = "name: oversized\n"
    refused(private_policy, out_of_range, "out-of-range guest id")
    checks += 3

    forbidden = {"asyncio", "http", "os", "requests", "socket", "subprocess", "urllib"}
    assert imports(MODULE_PATH).isdisjoint(forbidden)
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert all(value not in source for value in ("shell=True", "ssh ", "qm ", "pct ", "pvesh "))
    checks += 2
    print(f"Alpha 2 Proxmox live-state parser passed {checks} hostile offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
