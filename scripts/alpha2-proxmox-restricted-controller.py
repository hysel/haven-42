#!/usr/bin/env python3
"""Forced-command controller for the private Alpha 2 Proxmox lab.

The SSH key cannot select an executable. This controller reads one narrowly
defined request from SSH_ORIGINAL_COMMAND, obtains fresh host state, applies
the pure policy decision, and invokes one fixed Proxmox command. It never
uses a shell and never accepts a numeric VM id from the caller.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any

try:
    import fcntl
except ModuleNotFoundError:  # Windows can run parser/allowlist tests only.
    fcntl = None


INSTALL_ROOT = Path("/etc/haven42-alpha2")
SCRIPT_ROOT = INSTALL_ROOT / "scripts"
STATE_ROOT = Path("/var/lib/haven42-alpha2")
POLICY_FILE = INSTALL_ROOT / "policy.json"
LOCK_FILE = STATE_ROOT / "controller.lock"
MODULE_FILES = {
    "policy": SCRIPT_ROOT / "alpha2-proxmox-control-policy.py",
    "live": SCRIPT_ROOT / "alpha2-proxmox-live-state.py",
    "collector": SCRIPT_ROOT / "alpha2-proxmox-readonly-collector.py",
    "journal": SCRIPT_ROOT / "alpha2-proxmox-request-journal.py",
}
QM = "/usr/sbin/qm"
REQUEST_ID = re.compile(r"^[0-9a-f]{32}$")
TARGET_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
EXPOSED_ACTIONS = {"status", "start", "shutdown", "guarded-stop"}
MAX_ORIGINAL_COMMAND_BYTES = 256
MAX_COMMAND_OUTPUT_BYTES = 256 * 1024


class ControllerError(RuntimeError):
    """The request or controller installation is unsafe."""


def _secure_root_owned(path: Path, *, directory: bool = False) -> None:
    if path.is_symlink():
        raise ControllerError("A controller path is a symbolic link.")
    try:
        metadata = path.stat()
    except OSError as exc:
        raise ControllerError("A required controller path is unavailable.") from exc
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected_type(metadata.st_mode):
        raise ControllerError("A controller path has the wrong file type.")
    if metadata.st_uid != 0 or stat.S_IMODE(metadata.st_mode) & 0o022:
        raise ControllerError("A controller path is not protected by root ownership.")


def verify_installation() -> None:
    _secure_root_owned(INSTALL_ROOT, directory=True)
    _secure_root_owned(SCRIPT_ROOT, directory=True)
    _secure_root_owned(STATE_ROOT, directory=True)
    _secure_root_owned(POLICY_FILE)
    if POLICY_FILE.stat().st_size > 64 * 1024:
        raise ControllerError("The private policy exceeds its size limit.")
    for path in MODULE_FILES.values():
        _secure_root_owned(path)
        if path.stat().st_size > 256 * 1024:
            raise ControllerError("A controller module exceeds its size limit.")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ControllerError("A controller module could not be loaded.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_modules() -> dict[str, Any]:
    return {
        name: _load(f"alpha2_controller_{name}", path)
        for name, path in MODULE_FILES.items()
    }


def parse_original_command(value: str | None) -> dict[str, Any]:
    if value is None or not isinstance(value, str):
        raise ControllerError("A control command is required.")
    try:
        size = len(value.encode("ascii", errors="strict"))
    except UnicodeEncodeError as exc:
        raise ControllerError("The control command must be ASCII.") from exc
    if not 1 <= size <= MAX_ORIGINAL_COMMAND_BYTES or any(
        character in value for character in "\r\n\t\0"
    ):
        raise ControllerError("The control command has an unsafe size or character.")
    fields = value.split(" ")
    if any(not field for field in fields) or fields[0] not in EXPOSED_ACTIONS:
        raise ControllerError("The control action is not exposed.")
    action = fields[0]
    if action == "status":
        if len(fields) not in {1, 2}:
            raise ControllerError("Status accepts at most one logical target.")
        target = fields[1] if len(fields) == 2 else None
        request_id = "0" * 32
    else:
        if len(fields) != 3:
            raise ControllerError("A mutation requires one target and one request id.")
        target, request_id = fields[1:]
    if target is not None and not TARGET_ID.fullmatch(target):
        raise ControllerError("The logical target is invalid.")
    if not REQUEST_ID.fullmatch(request_id):
        raise ControllerError("The request id is invalid.")
    return {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "requestId": request_id,
        "action": action,
        "target": target,
    }


def _run_qm(argv: tuple[str, ...], timeout: int) -> subprocess.CompletedProcess[bytes]:
    if (
        len(argv) < 3
        or argv[0] != QM
        or argv[1] not in {"start", "shutdown", "stop"}
        or not argv[2].isdigit()
        or not 100 <= int(argv[2]) <= 999_999_999
        or (
            argv[1] in {"start", "stop"} and len(argv) != 3
        )
        or (
            argv[1] == "shutdown"
            and (len(argv) != 5 or argv[3] != "--timeout" or not argv[4].isdigit())
        )
    ):
        raise ControllerError("The controller constructed a non-allowlisted command.")
    return subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        shell=False,
        close_fds=True,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"},
    )


def _safe_output(completed: subprocess.CompletedProcess[bytes]) -> None:
    if len(completed.stdout) > MAX_COMMAND_OUTPUT_BYTES or len(
        completed.stderr
    ) > MAX_COMMAND_OUTPUT_BYTES:
        raise ControllerError("A Proxmox command exceeded its output limit.")


def _status_payload(policy: dict[str, Any], state: dict[str, Any], target: str | None) -> dict[str, Any]:
    target_map = {item["id"]: str(item["vmid"]) for item in policy["targets"]}
    selected = [target] if target is not None else sorted(target_map)
    return {
        "schemaVersion": 1,
        "campaignId": policy["campaignId"],
        "targets": {name: state["vms"][target_map[name]] for name in selected},
        "gpuAvailableForAssignment": not bool(
            state["gpuOwners"]
            or state["gpuConfiguredVmIds"]
            or state["protectedContainerGpuOwners"]
            or state["unknownPassthroughVmIds"]
            or state["unknownPassthroughContainerIds"]
        ),
        "storageAdmissionPassed": state["zfsFreePercent"]
        >= policy["limits"]["minimumLocalZfsFreePercent"],
    }


def _desired_state(action: str) -> str:
    return "running" if action == "start" else "stopped"


def _admit_verified_shutdown_timeout(
    modules: dict[str, Any], policy: dict[str, Any], request: dict[str, Any],
    state: dict[str, Any],
) -> None:
    """Admit a guarded stop only after the latest matching shutdown failed."""
    if request["action"] != "guarded-stop":
        return
    journal_path = STATE_ROOT / "mutation-journal.json"
    if not journal_path.exists():
        return
    journal_module = modules["journal"]
    journal = journal_module.load_journal(STATE_ROOT)
    if not journal["records"]:
        return
    record = journal["records"][-1]
    if (
        record["action"] != "shutdown"
        or record["target"] != request["target"]
        or record["status"] not in {"completed", "uncertain"}
        or (
            record["status"] == "completed"
            and record["outcomeCode"] != "command-failed"
        )
        or (
            record["status"] == "uncertain"
            and record["outcomeCode"] != "controller-interrupted"
        )
    ):
        return
    target_map = {item["id"]: item["vmid"] for item in policy["targets"]}
    vmid = target_map[request["target"]]
    if state["vms"].get(str(vmid)) != "running":
        return
    if record["status"] == "uncertain":
        journal_module.resolve_uncertain_request(
            journal, record["requestId"], "shutdown-timeout-verified"
        )
        journal_module.save_journal(STATE_ROOT, journal)
    state["shutdownTimedOutVmIds"] = [vmid]


def _execute_mutation(
    modules: dict[str, Any], policy: dict[str, Any], request: dict[str, Any], decision: Any
) -> dict[str, Any]:
    journal_module = modules["journal"]
    journal_path = STATE_ROOT / "mutation-journal.json"
    journal = (
        journal_module.load_journal(STATE_ROOT)
        if journal_path.exists()
        else journal_module.new_journal()
    )
    if any(record["status"] == "prepared" for record in journal["records"]):
        journal_module.mark_interrupted_uncertain(journal)
        journal_module.save_journal(STATE_ROOT, journal)
        raise ControllerError("A prior interrupted operation requires manual review.")
    journal_module.prepare_request(journal, request)
    journal_module.save_journal(STATE_ROOT, journal)
    invoked = False
    try:
        if request["action"] == "start":
            argv = (QM, "start", str(decision.vmid))
            timeout = 120
        elif request["action"] == "shutdown":
            grace = policy["limits"]["gracefulShutdownSeconds"]
            argv = (QM, "shutdown", str(decision.vmid), "--timeout", str(grace))
            timeout = grace + 30
        elif request["action"] == "guarded-stop":
            argv = (QM, "stop", str(decision.vmid))
            timeout = 120
        else:
            raise ControllerError("The mutation action is not implemented.")
        invoked = True
        completed = _run_qm(argv, timeout)
        _safe_output(completed)
        refreshed = modules["collector"].collect_live_state(policy)
        desired = _desired_state(request["action"])
        actual = refreshed["vms"][str(decision.vmid)]
        if completed.returncode != 0 or actual != desired:
            journal_module.complete_request(journal, request["requestId"], "command-failed")
            journal_module.save_journal(STATE_ROOT, journal)
            raise ControllerError("The Proxmox operation did not reach its requested state.")
        journal_module.complete_request(journal, request["requestId"], "state-verified")
        journal_module.save_journal(STATE_ROOT, journal)
        return {
            "schemaVersion": 1,
            "action": request["action"],
            "target": request["target"],
            "state": actual,
            "verified": True,
        }
    except subprocess.TimeoutExpired as exc:
        journal_module.mark_interrupted_uncertain(journal)
        journal_module.save_journal(STATE_ROOT, journal)
        raise ControllerError("The Proxmox operation timed out and requires review.") from exc
    except BaseException:
        if invoked and any(record["status"] == "prepared" for record in journal["records"]):
            journal_module.mark_interrupted_uncertain(journal)
            journal_module.save_journal(STATE_ROOT, journal)
        raise


def run(original_command: str | None) -> dict[str, Any]:
    if os.geteuid() != 0:
        raise ControllerError("The restricted controller must run as root.")
    if fcntl is None:
        raise ControllerError("The restricted controller requires POSIX file locking.")
    verify_installation()
    modules = load_modules()
    request = parse_original_command(original_command)
    policy = modules["policy"].load_private_policy(POLICY_FILE)
    state = modules["collector"].collect_live_state(policy)
    if request["action"] == "status":
        modules["policy"].decide(policy, request, state)
        return _status_payload(policy, state, request["target"])
    if LOCK_FILE.is_symlink():
        raise ControllerError("The controller lock path is a symbolic link.")
    LOCK_FILE.touch(mode=0o600, exist_ok=True)
    _secure_root_owned(LOCK_FILE)
    with LOCK_FILE.open("r+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = modules["collector"].collect_live_state(policy)
        _admit_verified_shutdown_timeout(modules, policy, request, state)
        decision = modules["policy"].decide(policy, request, state)
        return _execute_mutation(modules, policy, request, decision)


def main() -> int:
    try:
        result = run(os.environ.get("SSH_ORIGINAL_COMMAND"))
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True, separators=(",", ":")))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
