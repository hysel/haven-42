#!/usr/bin/env python3
"""Root-owned, read-only Proxmox state collector for Alpha 2.

The command set is fixed and contains no shell. The collector cannot start,
stop, configure, or delete a guest. It emits strict live state for a separate
policy decision and intentionally does not declare that state safe.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


POLICY = _load(
    "alpha2_collector_policy", ROOT / "scripts/alpha2-proxmox-control-policy.py"
)
LIVE = _load(
    "alpha2_collector_live", ROOT / "scripts/alpha2-proxmox-live-state.py"
)

POLICY_FILE = Path("/etc/haven42-alpha2/policy.json")
BINARIES = {
    "hostname": "/usr/bin/hostname",
    "pvesh": "/usr/bin/pvesh",
    "pvesm": "/usr/sbin/pvesm",
    "qm": "/usr/sbin/qm",
    "pct": "/usr/sbin/pct",
    "nvidia-smi": "/usr/bin/nvidia-smi",
}
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_GUESTS = 256


class CollectionError(RuntimeError):
    """A fixed read-only inventory command failed or returned unsafe output."""


Runner = Callable[[tuple[str, ...]], str]


def _allowed_command(argv: tuple[str, ...]) -> bool:
    fixed = {
        (BINARIES["hostname"],),
        (
            BINARIES["pvesh"], "get", "/cluster/mapping/pci",
            "--output-format", "json",
        ),
        (BINARIES["pvesm"], "status"),
        (
            BINARIES["nvidia-smi"],
            "--query-gpu=index,name,pci.bus_id,uuid",
            "--format=csv,noheader",
        ),
        (BINARIES["qm"], "list"),
        (BINARIES["pct"], "list"),
    }
    if argv in fixed:
        return True
    return (
        len(argv) == 3
        and argv[0] in {BINARIES["qm"], BINARIES["pct"]}
        and argv[1] in {"status", "config"}
        and argv[2].isdigit()
        and 100 <= int(argv[2]) <= 999_999_999
    )


def run_fixed(argv: tuple[str, ...]) -> str:
    if not _allowed_command(argv):
        raise CollectionError("Collector attempted a non-allowlisted command.")
    try:
        completed = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
            shell=False,
            close_fds=True,
            env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CollectionError("A fixed inventory command could not run.") from exc
    if completed.returncode != 0:
        raise CollectionError("A fixed inventory command returned a failure status.")
    if len(completed.stdout) > MAX_OUTPUT_BYTES:
        raise CollectionError("A fixed inventory command exceeded its output limit.")
    try:
        return completed.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CollectionError("A fixed inventory command returned non-UTF-8 output.") from exc


def _run(runner: Runner, *argv: str) -> str:
    value = runner(tuple(argv))
    if not isinstance(value, str) or len(value.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise CollectionError("Inventory runner returned invalid output.")
    return value


def collect_live_state(
    policy: dict[str, Any], runner: Runner = run_fixed
) -> dict[str, Any]:
    POLICY.validate_private_policy(policy)
    node_name = _run(runner, BINARIES["hostname"]).strip()
    if not node_name:
        raise CollectionError("Host identity command returned no node name.")
    mapping_text = _run(
        runner,
        BINARIES["pvesh"],
        "get",
        "/cluster/mapping/pci",
        "--output-format",
        "json",
    )
    try:
        mappings = json.loads(mapping_text)
    except json.JSONDecodeError as exc:
        raise CollectionError("PCI resource mapping output is not valid JSON.") from exc
    storage = _run(runner, BINARIES["pvesm"], "status")
    gpu_csv = _run(
        runner,
        BINARIES["nvidia-smi"],
        "--query-gpu=index,name,pci.bus_id,uuid",
        "--format=csv,noheader",
    )
    vm_list = _run(runner, BINARIES["qm"], "list")
    container_list = _run(runner, BINARIES["pct"], "list")
    vmids = LIVE._parse_list_ids(vm_list, "VM list")
    container_ids = LIVE._parse_list_ids(container_list, "container list")
    if len(vmids) > MAX_GUESTS or len(container_ids) > MAX_GUESTS:
        raise CollectionError("Guest inventory exceeds the reviewed limit.")

    vm_statuses = {
        str(vmid): _run(runner, BINARIES["qm"], "status", str(vmid))
        for vmid in sorted(vmids)
    }
    vm_configs = {
        str(vmid): _run(runner, BINARIES["qm"], "config", str(vmid))
        for vmid in sorted(vmids)
    }
    container_statuses = {
        str(container_id): _run(
            runner, BINARIES["pct"], "status", str(container_id)
        )
        for container_id in sorted(container_ids)
    }
    container_configs = {
        str(container_id): _run(
            runner, BINARIES["pct"], "config", str(container_id)
        )
        for container_id in sorted(container_ids)
    }
    snapshot = {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "nodeName": node_name,
        "storageStatus": storage,
        "pciMappings": mappings,
        "hostNvidiaSmiCsv": gpu_csv,
        "vmList": vm_list,
        "containerList": container_list,
        "vmStatuses": vm_statuses,
        "vmConfigs": vm_configs,
        "containerStatuses": container_statuses,
        "containerConfigs": container_configs,
        "shutdownTimedOutVmIds": [],
    }
    return LIVE.build_live_state(policy, snapshot, enforce_control_policy=False)


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("This collector accepts no command-line arguments.")
    if os.geteuid() != 0:
        raise SystemExit("This collector must run as root on the reviewed Proxmox node.")
    try:
        policy = POLICY.load_private_policy(POLICY_FILE)
        state = collect_live_state(policy)
        print(json.dumps(state, indent=2, sort_keys=True))
    except (CollectionError, POLICY.PolicyError, POLICY.PolicyRefusal, LIVE.LiveStateError) as exc:
        raise SystemExit(f"Inventory refused: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
