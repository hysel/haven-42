#!/usr/bin/env python3
"""Hostile offline tests for the restricted Proxmox control policy."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
POLICY_MODULE = ROOT / "scripts/alpha2-proxmox-control-policy.py"
SPEC = importlib.util.spec_from_file_location("alpha2_proxmox_policy", POLICY_MODULE)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


TARGETS = [
    "ubuntu-26-04-gnome",
    "ubuntu-24-04-gnome",
    "debian-13-gnome",
    "linux-mint-22-cinnamon",
    "pop-os-24-04-cosmic",
    "fedora-44-gnome",
    "bazzite-kde",
    "cachyos-kde",
    "arch-linux-kde",
    "windows-11-nvidia",
]


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
            {"id": target, "vmid": 200 + index} for index, target in enumerate(TARGETS)
        ],
        "excludedVmIds": [299],
        "excludedContainerIds": [300, 301],
        "limits": {
            "gracefulShutdownSeconds": 180,
            "maximumConcurrentGpuOwners": 1,
            "minimumLocalZfsFreePercent": 16,
            "maximumRequestBytes": 4096,
        },
    }


def request(action: str, target: str | None) -> dict:
    return {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "requestId": "0123456789abcdef0123456789abcdef",
        "action": action,
        "target": target,
    }


def state() -> dict:
    return {
        "nodeName": "test-node",
        "gpuMappingCanonicalSha256": "a" * 64,
        "zfsFreePercent": 20.0,
        "vms": {str(200 + index): "stopped" for index in range(len(TARGETS))},
        "protectedVms": {"299": "stopped"},
        "protectedContainers": {"300": "running", "301": "running"},
        "gpuConfiguredVmIds": [],
        "gpuOwners": [],
        "protectedContainerGpuOwners": [],
        "unknownPassthroughVmIds": [],
        "unknownPassthroughContainerIds": [],
        "shutdownTimedOutVmIds": [],
    }


def refused(policy_value: dict, request_value: dict, state_value: dict, text: str) -> None:
    try:
        MODULE.decide(policy_value, request_value, state_value)
    except (MODULE.PolicyError, MODULE.PolicyRefusal) as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError("Unsafe operation was approved.")


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
    base_policy = policy()
    base_state = state()
    MODULE.validate_private_policy(base_policy)
    checks = 1

    decision = MODULE.decide(base_policy, request("status", None), base_state)
    assert not decision.mutating and decision.vmid is None
    assert "vmid" not in decision.public_result()
    checks += 2
    decision = MODULE.decide(
        base_policy, request("gpu-attach", "ubuntu-26-04-gnome"), base_state
    )
    assert decision.mutating and decision.vmid == 200
    assert "vmid" not in decision.public_result()
    checks += 2

    changed = copy.deepcopy(base_policy)
    changed["deploymentState"] = "review-only"
    refused(changed, request("status", None), base_state, "deployment state")
    changed = copy.deepcopy(base_policy)
    changed["deploymentState"] = "inventory-only"
    assert not MODULE.decide(changed, request("status", None), base_state).mutating
    refused(
        changed,
        request("start", TARGETS[0]),
        base_state,
        "inventory-only",
    )
    changed = copy.deepcopy(base_policy)
    changed["gpuSlot"] = "hostpci1"
    refused(changed, request("status", None), base_state, "hostpci0")
    changed = copy.deepcopy(base_policy)
    changed["targets"][0]["vmid"] = 299
    refused(changed, request("status", None), base_state, "outside the target")
    changed = copy.deepcopy(base_policy)
    changed["limits"]["maximumConcurrentGpuOwners"] = 2
    refused(changed, request("status", None), base_state, "one concurrent GPU")
    changed = copy.deepcopy(base_policy)
    changed["excludedContainerIds"] = []
    refused(changed, request("status", None), base_state, "excluded container")
    changed = copy.deepcopy(base_policy)
    changed["excludedVmIds"] = []
    MODULE.validate_private_policy(changed)
    changed = copy.deepcopy(base_policy)
    changed["excludedContainerIds"] = [300, 300]
    refused(changed, request("status", None), base_state, "must be unique")
    changed = copy.deepcopy(base_policy)
    changed["excludedContainerIds"] = [200, 300]
    refused(changed, request("status", None), base_state, "outside every VM")
    checks += 10

    hostile = request("delete", "ubuntu-26-04-gnome")
    refused(base_policy, hostile, base_state, "not allowlisted")
    hostile = request("start", "../../102")
    refused(base_policy, hostile, base_state, "safe target")
    hostile = request("start", "windows-guest")
    refused(base_policy, hostile, base_state, "outside the private allowlist")
    hostile = request("status", None)
    hostile["command"] = "qm destroy 102"
    refused(base_policy, hostile, base_state, "fields do not match")
    checks += 4

    changed_state = copy.deepcopy(base_state)
    changed_state["nodeName"] = "other-node"
    refused(base_policy, request("status", None), changed_state, "identity changed")
    changed_state = copy.deepcopy(base_state)
    changed_state["gpuMappingCanonicalSha256"] = "b" * 64
    assert MODULE.decide(base_policy, request("status", None), changed_state).reason == (
        "approved-read-only-status"
    )
    refused(base_policy, request("start", TARGETS[0]), changed_state, "resource mapping changed")
    changed_state = copy.deepcopy(base_state)
    changed_state["zfsFreePercent"] = 15.99
    refused(base_policy, request("start", TARGETS[0]), changed_state, "stop threshold")
    changed_state["vms"]["200"] = "running"
    assert MODULE.decide(
        base_policy, request("shutdown", TARGETS[0]), changed_state
    ).reason == "approved-graceful-shutdown"
    changed_state = copy.deepcopy(base_state)
    changed_state["gpuConfiguredVmIds"] = [200, 201]
    changed_state["gpuOwners"] = [200, 201]
    assert MODULE.decide(base_policy, request("status", None), changed_state).reason == (
        "approved-read-only-status"
    )
    changed_state = copy.deepcopy(base_state)
    changed_state["unknownPassthroughVmIds"] = [299]
    assert MODULE.decide(
        base_policy, request("start", TARGETS[0]), changed_state
    ).reason == "approved-allowlisted-start"
    changed_state["unknownPassthroughVmIds"] = [200]
    refused(base_policy, request("start", TARGETS[0]), changed_state, "target VM")
    changed_state = copy.deepcopy(base_state)
    changed_state["protectedContainers"].pop("300")
    refused(base_policy, request("status", None), changed_state, "protected container set")
    changed_state = copy.deepcopy(base_state)
    changed_state["unknownPassthroughContainerIds"] = [300]
    refused(
        base_policy,
        request("gpu-attach", TARGETS[0]),
        changed_state,
        "container passthrough",
    )
    changed_state = copy.deepcopy(base_state)
    changed_state["protectedContainerGpuOwners"] = [300]
    refused(base_policy, request("gpu-attach", TARGETS[0]), changed_state, "already has an owner")
    changed_state = copy.deepcopy(base_state)
    changed_state["vms"]["200"] = "running"
    refused(base_policy, request("gpu-attach", TARGETS[1]), changed_state, "must be stopped")
    refused(base_policy, request("start", TARGETS[1]), changed_state, "already running")
    changed_state = copy.deepcopy(base_state)
    changed_state["gpuConfiguredVmIds"] = [200]
    changed_state["gpuOwners"] = [200]
    refused(base_policy, request("gpu-attach", TARGETS[1]), changed_state, "already has an owner")
    changed_state = copy.deepcopy(base_state)
    changed_state["gpuConfiguredVmIds"] = [200]
    changed_state["gpuOwners"] = [200]
    refused(base_policy, request("gpu-detach", TARGETS[1]), changed_state, "not a stopped configured")
    changed_state = copy.deepcopy(base_state)
    changed_state["vms"]["200"] = "running"
    refused(base_policy, request("guarded-stop", TARGETS[0]), changed_state, "timeout is required")
    changed_state["shutdownTimedOutVmIds"] = [200]
    assert MODULE.decide(
        base_policy, request("guarded-stop", TARGETS[0]), changed_state
    ).reason == "approved-stop-after-timeout"
    checks += 18

    forbidden = {"asyncio", "http", "os", "requests", "socket", "subprocess", "urllib"}
    assert imported_roots(POLICY_MODULE).isdisjoint(forbidden)
    source = POLICY_MODULE.read_text(encoding="utf-8")
    assert all(value not in source for value in ("shell=True", "qm ", "pvesh ", "hostpci0="))
    checks += 2

    with tempfile.TemporaryDirectory() as temporary_name:
        root = Path(temporary_name)
        valid = root / "policy.json"
        valid.write_text(json.dumps(base_policy), encoding="utf-8")
        assert MODULE.load_private_policy(valid) == base_policy
        oversized = root / "oversized.json"
        oversized.write_bytes(b"{" + b" " * (64 * 1024))
        try:
            MODULE.load_private_policy(oversized)
        except MODULE.PolicyError as exc:
            assert "Unsafe" in str(exc)
        else:
            raise AssertionError("Oversized private policy was accepted.")
        link = root / "policy-link.json"
        try:
            link.symlink_to(valid)
        except OSError:
            pass
        else:
            try:
                MODULE.load_private_policy(link)
            except MODULE.PolicyError as exc:
                assert "Unsafe" in str(exc)
            else:
                raise AssertionError("Symlink private policy was accepted.")
        checks += 3
    print(f"Alpha 2 Proxmox policy passed {checks} hostile offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
