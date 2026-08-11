#!/usr/bin/env python3
"""Hostile offline checks for the forced-command Proxmox controller."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts/alpha2-proxmox-restricted-controller.py"
SPEC = importlib.util.spec_from_file_location("alpha2_restricted_controller", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def refused(command: str | None, text: str) -> None:
    try:
        MODULE.parse_original_command(command)
    except MODULE.ControllerError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError("Unsafe forced command was accepted.")


def main() -> int:
    status = MODULE.parse_original_command("status")
    assert status["action"] == "status" and status["target"] is None
    targeted = MODULE.parse_original_command("status fedora-44-gnome")
    assert targeted["target"] == "fedora-44-gnome"
    start = MODULE.parse_original_command(
        "start fedora-44-gnome 0123456789abcdef0123456789abcdef"
    )
    assert start["action"] == "start"
    shutdown = MODULE.parse_original_command(
        "shutdown fedora-44-gnome fedcba9876543210fedcba9876543210"
    )
    assert shutdown["action"] == "shutdown"
    guarded_stop = MODULE.parse_original_command(
        "guarded-stop fedora-44-gnome 11111111111111111111111111111111"
    )
    assert guarded_stop["action"] == "guarded-stop"
    checks = 6

    hostile = {
        None: "required",
        "": "unsafe size or character",
        "stop fedora-44-gnome " + "0" * 32: "not exposed",
        "start ../../guest " + "0" * 32: "logical target",
        "start fedora-44-gnome invalid": "request id",
        "start  fedora-44-gnome " + "0" * 32: "not exposed",
        "status\nstart fedora-44-gnome " + "0" * 32: "unsafe size or character",
        "status;id": "not exposed",
        "gpu-attach fedora-44-gnome " + "0" * 32: "not exposed",
        "status " + "a" * 300: "unsafe size or character",
    }
    for command, message in hostile.items():
        refused(command, message)
    checks += len(hostile)

    calls: list[tuple[str, ...]] = []
    original_run = MODULE.subprocess.run

    def fake_run(argv, **kwargs):
        calls.append(tuple(argv))
        assert kwargs["shell"] is False
        assert kwargs["stdin"] is subprocess.DEVNULL
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    MODULE.subprocess.run = fake_run
    try:
        MODULE._run_qm((MODULE.QM, "start", "108"), 120)
        MODULE._run_qm((MODULE.QM, "shutdown", "108", "--timeout", "180"), 210)
        MODULE._run_qm((MODULE.QM, "stop", "108"), 120)
        assert calls == [
            (MODULE.QM, "start", "108"),
            (MODULE.QM, "shutdown", "108", "--timeout", "180"),
            (MODULE.QM, "stop", "108"),
        ]
        checks += 5
        for argv in (
            (MODULE.QM, "destroy", "108"),
            (MODULE.QM, "start", "../../102"),
            (MODULE.QM, "shutdown", "108"),
            ("/bin/sh", "-c", "id"),
        ):
            try:
                MODULE._run_qm(argv, 10)
            except MODULE.ControllerError:
                checks += 1
            else:
                raise AssertionError("A non-allowlisted subprocess was accepted.")
    finally:
        MODULE.subprocess.run = original_run

    policy = {
        "campaignId": "alpha2-linux-long-term",
        "targets": [
            {"id": "fedora-44-gnome", "vmid": 108},
            {"id": "arch-linux-kde", "vmid": 110},
            {"id": "windows-11-nvidia", "vmid": 111},
        ],
        "limits": {"minimumLocalZfsFreePercent": 16},
    }
    state = {
        "vms": {"108": "stopped", "110": "running", "111": "stopped"},
        "gpuConfiguredVmIds": [],
        "gpuOwners": [],
        "protectedContainerGpuOwners": [200],
        "unknownPassthroughVmIds": [],
        "unknownPassthroughContainerIds": [],
        "zfsFreePercent": 17.0,
    }
    payload = MODULE._status_payload(policy, state, None)
    assert payload["targets"] == {
        "arch-linux-kde": "running",
        "fedora-44-gnome": "stopped",
        "windows-11-nvidia": "stopped",
    }
    assert payload["gpuAvailableForAssignment"] is False
    assert payload["storageAdmissionPassed"] is True
    encoded = str(payload)
    assert "108" not in encoded and "110" not in encoded and "111" not in encoded and "200" not in encoded
    checks += 5

    original_state_root = MODULE.STATE_ROOT
    with tempfile.TemporaryDirectory() as temporary_name:
        MODULE.STATE_ROOT = Path(temporary_name)
        (MODULE.STATE_ROOT / "mutation-journal.json").write_text("{}", encoding="utf-8")

        class FakeJournal:
            def __init__(self, record):
                self.value = {
                    "records": [record],
                }
                self.resolved = False
                self.saved = False

            def load_journal(self, _root):
                return self.value

            def resolve_uncertain_request(self, journal, request_id, outcome):
                assert journal is self.value
                assert request_id == "2" * 32
                assert outcome == "shutdown-timeout-verified"
                self.resolved = True

            def save_journal(self, _root, journal):
                assert journal is self.value
                self.saved = True

        guarded_policy = {
            "targets": [{"id": "windows-11-nvidia", "vmid": 111}],
        }
        guarded_request = {
            "action": "guarded-stop",
            "target": "windows-11-nvidia",
        }
        guarded_state = {"vms": {"111": "running"}, "shutdownTimedOutVmIds": []}
        completed_journal = FakeJournal({
            "action": "shutdown",
            "target": "windows-11-nvidia",
            "requestId": "1" * 32,
            "status": "completed",
            "outcomeCode": "command-failed",
        })
        MODULE._admit_verified_shutdown_timeout(
            {"journal": completed_journal}, guarded_policy, guarded_request, guarded_state
        )
        assert guarded_state["shutdownTimedOutVmIds"] == [111]
        assert not completed_journal.resolved and not completed_journal.saved

        guarded_state["shutdownTimedOutVmIds"] = []
        uncertain_journal = FakeJournal({
            "action": "shutdown",
            "target": "windows-11-nvidia",
            "requestId": "2" * 32,
            "status": "uncertain",
            "outcomeCode": "controller-interrupted",
        })
        MODULE._admit_verified_shutdown_timeout(
            {"journal": uncertain_journal}, guarded_policy, guarded_request, guarded_state
        )
        assert guarded_state["shutdownTimedOutVmIds"] == [111]
        assert uncertain_journal.resolved and uncertain_journal.saved
        checks += 6
    MODULE.STATE_ROOT = original_state_root

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    calls_in_source = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"system", "popen"}
    ]
    assert not calls_in_source
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "shell=True" not in source
    assert "pct " not in source
    checks += 3
    print(f"Alpha 2 restricted Proxmox controller passed {checks} hostile checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
