#!/usr/bin/env python3
"""Hostile tests for the Alpha 2 Proxmox mutation request journal."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts/alpha2-proxmox-request-journal.py"
SPEC = importlib.util.spec_from_file_location("alpha2_journal", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def request(request_id: str = "0" * 32) -> dict:
    return {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "requestId": request_id,
        "action": "start",
        "target": "ubuntu-26-04-gnome",
    }


def rejected(value: dict, text: str) -> None:
    try:
        MODULE.validate_journal(value)
    except MODULE.JournalError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError("Unsafe mutation journal was accepted.")


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
    journal = MODULE.new_journal()
    MODULE.prepare_request(journal, request(), "2026-08-08T00:00:00Z")
    assert journal["records"][0]["status"] == "prepared"
    assert journal["revision"] == 1
    try:
        MODULE.prepare_request(journal, request("1" * 32), "2026-08-08T00:00:01Z")
    except MODULE.JournalError as exc:
        assert "unresolved mutation" in str(exc)
    else:
        raise AssertionError("Concurrent mutation was prepared.")
    MODULE.complete_request(
        journal, "0" * 32, "command-completed", "2026-08-08T00:00:02Z"
    )
    assert journal["records"][0]["status"] == "completed"
    checks = 5

    try:
        MODULE.prepare_request(journal, request(), "2026-08-08T00:00:03Z")
    except MODULE.JournalError as exc:
        assert "already used" in str(exc)
    else:
        raise AssertionError("Replayed request id was prepared.")
    MODULE.prepare_request(journal, request("1" * 32), "2026-08-08T00:00:04Z")
    MODULE.mark_interrupted_uncertain(journal, "2026-08-08T00:00:05Z")
    assert journal["records"][1]["status"] == "uncertain"
    try:
        MODULE.prepare_request(journal, request("2" * 32), "2026-08-08T00:00:06Z")
    except MODULE.JournalError as exc:
        assert "unresolved mutation" in str(exc)
    else:
        raise AssertionError("Mutation followed uncertain state.")
    MODULE.resolve_uncertain_request(
        journal, "1" * 32, "shutdown-timeout-verified", "2026-08-08T00:00:07Z"
    )
    assert journal["records"][1]["status"] == "completed"
    MODULE.prepare_request(journal, request("2" * 32), "2026-08-08T00:00:08Z")
    MODULE.complete_request(
        journal, "2" * 32, "state-verified", "2026-08-08T00:00:09Z"
    )
    checks += 7

    hostile = copy.deepcopy(journal)
    hostile["records"][1]["requestId"] = hostile["records"][0]["requestId"]
    rejected(hostile, "replayed request id")
    hostile = copy.deepcopy(journal)
    hostile["records"][0]["action"] = "status"
    rejected(hostile, "do not belong")
    hostile = copy.deepcopy(journal)
    hostile["records"][0]["target"] = "../../guest"
    rejected(hostile, "invalid request")
    hostile = copy.deepcopy(journal)
    hostile["records"][0]["outcomeCode"] = "private/path"
    rejected(hostile, "safe outcome")
    checks += 4

    clean = MODULE.new_journal()
    with tempfile.TemporaryDirectory() as temporary_name:
        root = Path(temporary_name)
        MODULE.save_journal(root, clean)
        assert MODULE.load_journal(root) == clean
        assert (root / "mutation-journal.json").read_bytes().endswith(b"\n")
        if os.name == "posix":
            assert (root / "mutation-journal.json").stat().st_mode & 0o077 == 0
        checks += 3
        link = root / "unsafe"
        try:
            link.symlink_to(root, target_is_directory=True)
        except OSError:
            pass
        else:
            try:
                MODULE.resolve_root(link)
            except MODULE.JournalError as exc:
                assert "must not be a symlink" in str(exc)
            else:
                raise AssertionError("Symlink journal root was accepted.")
            checks += 1

    forbidden = {"asyncio", "http", "requests", "socket", "subprocess", "urllib"}
    assert imports(MODULE_PATH).isdisjoint(forbidden)
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert all(value not in source for value in ("shell=True", "ssh ", "qm ", "pct ", "pvesh "))
    encoded = json.dumps(journal)
    assert all(marker not in encoded for marker in ("192.168.", "hostname", "username"))
    checks += 3
    print(f"Alpha 2 Proxmox request journal passed {checks} hostile persistence checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
