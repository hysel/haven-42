#!/usr/bin/env python3
"""Hostile offline tests for the fixed Proxmox read-only collector."""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts/alpha2-proxmox-readonly-collector.py"
SPEC = importlib.util.spec_from_file_location("alpha2_collector", MODULE_PATH)
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
        "gpuMappingCanonicalSha256": MODULE.LIVE._canonical_mapping_sha256([MAP_ENTRY]),
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


def outputs() -> dict[tuple[str, ...], str]:
    vmids = list(range(200, 210)) + [299]
    values: dict[tuple[str, ...], str] = {
        (MODULE.BINARIES["hostname"],): "test-node\n",
        (
            MODULE.BINARIES["pvesh"], "get", "/cluster/mapping/pci",
            "--output-format", "json",
        ): json.dumps([{"id": "approved-gpu", "map": [MAP_ENTRY], "type": "pci"}]),
        (MODULE.BINARIES["pvesm"], "status"): (
            "Name Type Status Total (KiB) Used (KiB) Available (KiB) %\n"
            "local_zfs zfspool active 1000000 800000 200000 80.00%\n"
        ),
        (
            MODULE.BINARIES["nvidia-smi"],
            "--query-gpu=index,name,pci.bus_id,uuid",
            "--format=csv,noheader",
        ): "0, Other GPU, 00000000:01:00.0, GPU-other\n1, Reviewed GPU, 00000000:81:00.0, GPU-reviewed\n",
        (MODULE.BINARIES["qm"], "list"): (
            "VMID NAME STATUS\n" + "\n".join(f"{value} vm-{value} stopped" for value in vmids)
        ),
        (MODULE.BINARIES["pct"], "list"): "VMID Status Name\n300 running protected\n",
    }
    for vmid in vmids:
        values[(MODULE.BINARIES["qm"], "status", str(vmid))] = "status: stopped\n"
        values[(MODULE.BINARIES["qm"], "config", str(vmid))] = f"name: vm-{vmid}\n"
    values[(MODULE.BINARIES["pct"], "status", "300")] = "status: running\n"
    values[(MODULE.BINARIES["pct"], "config", "300")] = "dev0: /dev/nvidia0,gid=44\n"
    return values


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
    expected = outputs()
    calls: list[tuple[str, ...]] = []

    def runner(argv: tuple[str, ...]) -> str:
        calls.append(argv)
        if argv not in expected:
            raise AssertionError(f"Unexpected command: {argv!r}")
        return expected[argv]

    state = MODULE.collect_live_state(policy(), runner)
    assert state["zfsFreePercent"] == 20.0
    assert state["gpuOwners"] == []
    assert state["unknownPassthroughVmIds"] == []
    assert len(calls) == 30
    assert all(isinstance(call, tuple) and call[0].startswith("/usr/") for call in calls)
    assert MODULE._allowed_command((MODULE.BINARIES["qm"], "status", "200"))
    assert not MODULE._allowed_command((MODULE.BINARIES["qm"], "destroy", "200"))
    assert not MODULE._allowed_command((MODULE.BINARIES["pct"], "stop", "300"))
    assert not MODULE._allowed_command((MODULE.BINARIES["qm"], "config", "../../200"))
    checks = 9

    hostile = outputs()
    hostile[(MODULE.BINARIES["qm"], "config", "200")] += "hostpci0: 0000:81:00.0\n"
    state = MODULE.collect_live_state(policy(), lambda argv: hostile[argv])
    assert state["unknownPassthroughVmIds"] == [200]
    checks += 1

    def oversized(argv: tuple[str, ...]) -> str:
        if argv == (MODULE.BINARIES["hostname"],):
            return "x" * (MODULE.MAX_OUTPUT_BYTES + 1)
        return expected[argv]

    try:
        MODULE.collect_live_state(policy(), oversized)
    except MODULE.CollectionError as exc:
        assert "invalid output" in str(exc)
    else:
        raise AssertionError("Oversized inventory output was accepted.")
    checks += 1

    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "shell=False" in source and "shell=True" not in source
    assert "create_subprocess" not in source and "Popen(" not in source
    assert all(path.startswith("/usr/") for path in MODULE.BINARIES.values())
    allowed_imports = imports(MODULE_PATH)
    assert "socket" not in allowed_imports and "requests" not in allowed_imports
    checks += 4
    print(f"Alpha 2 Proxmox read-only collector passed {checks} hostile offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
