#!/usr/bin/env python3
"""Atomic anti-replay journal for future Alpha 2 Proxmox mutations.

This module has no command, network, VM, container, or GPU authority. It makes
request intent durable before a separate adapter executes one approved action.
An interrupted prepared request becomes uncertain and blocks automatic retry.
"""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "scripts/alpha2-proxmox-control-policy.py"
SPEC = importlib.util.spec_from_file_location("alpha2_journal_policy", POLICY_PATH)
POLICY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = POLICY
SPEC.loader.exec_module(POLICY)

JOURNAL_STATUS = {"prepared", "completed", "uncertain"}
SAFE_CODE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
MAX_RECORDS = 4096


class JournalError(ValueError):
    """The mutation journal or requested transition is unsafe."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_journal() -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "campaignId": "alpha2-linux-long-term",
        "revision": 0,
        "records": [],
    }
    validate_journal(value)
    return value


def validate_journal(value: Any) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"schemaVersion", "campaignId", "revision", "records"}
        or value.get("schemaVersion") != 1
        or value.get("campaignId") != "alpha2-linux-long-term"
        or not isinstance(value.get("revision"), int)
        or isinstance(value.get("revision"), bool)
        or value["revision"] < 0
        or not isinstance(value.get("records"), list)
        or len(value["records"]) > MAX_RECORDS
    ):
        raise JournalError("Mutation journal fields do not match the reviewed schema.")
    seen: set[str] = set()
    prepared = 0
    uncertain_seen = False
    for record in value["records"]:
        if not isinstance(record, dict) or set(record) != {
            "requestId", "action", "target", "status", "preparedAtUtc",
            "finishedAtUtc", "outcomeCode",
        }:
            raise JournalError("Mutation journal record fields are invalid.")
        request = {
            "schemaVersion": 1,
            "campaignId": "alpha2-linux-long-term",
            "requestId": record["requestId"],
            "action": record["action"],
            "target": record["target"],
        }
        try:
            POLICY.validate_request(request)
        except POLICY.PolicyError as exc:
            raise JournalError("Mutation journal contains an invalid request.") from exc
        if record["action"] not in POLICY.MUTATING_ACTIONS:
            raise JournalError("Read-only status requests do not belong in the mutation journal.")
        if record["requestId"] in seen:
            raise JournalError("Mutation journal contains a replayed request id.")
        seen.add(record["requestId"])
        if record["status"] not in JOURNAL_STATUS or not TIMESTAMP.fullmatch(
            str(record["preparedAtUtc"])
        ):
            raise JournalError("Mutation journal record status or timestamp is invalid.")
        if record["status"] == "prepared":
            prepared += 1
            if record["finishedAtUtc"] is not None or record["outcomeCode"] is not None:
                raise JournalError("Prepared mutation record cannot be final.")
        else:
            if (
                not isinstance(record["finishedAtUtc"], str)
                or not TIMESTAMP.fullmatch(record["finishedAtUtc"])
                or not isinstance(record["outcomeCode"], str)
                or not SAFE_CODE.fullmatch(record["outcomeCode"])
            ):
                raise JournalError("Final mutation record lacks a safe outcome.")
        if record["status"] == "uncertain":
            uncertain_seen = True
        elif uncertain_seen:
            raise JournalError("No mutation may follow an unresolved uncertain record.")
    if prepared > 1:
        raise JournalError("More than one mutation request is prepared.")


def prepare_request(
    journal: dict[str, Any], request: dict[str, Any], timestamp: str | None = None
) -> dict[str, Any]:
    validate_journal(journal)
    try:
        POLICY.validate_request(request)
    except POLICY.PolicyError as exc:
        raise JournalError("Cannot journal an invalid control request.") from exc
    if request["action"] not in POLICY.MUTATING_ACTIONS:
        raise JournalError("Read-only status requests are not journaled.")
    if len(journal["records"]) >= MAX_RECORDS:
        raise JournalError("Mutation journal reached its reviewed record limit.")
    if any(record["status"] in {"prepared", "uncertain"} for record in journal["records"]):
        raise JournalError("An unresolved mutation blocks every new request.")
    if any(record["requestId"] == request["requestId"] for record in journal["records"]):
        raise JournalError("Mutation request id was already used.")
    prepared = timestamp or utc_now()
    if not TIMESTAMP.fullmatch(prepared):
        raise JournalError("Prepared timestamp is invalid.")
    journal["records"].append(
        {
            "requestId": request["requestId"],
            "action": request["action"],
            "target": request["target"],
            "status": "prepared",
            "preparedAtUtc": prepared,
            "finishedAtUtc": None,
            "outcomeCode": None,
        }
    )
    journal["revision"] += 1
    validate_journal(journal)
    return journal


def complete_request(
    journal: dict[str, Any], request_id: str, outcome_code: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    validate_journal(journal)
    prepared = [record for record in journal["records"] if record["status"] == "prepared"]
    if len(prepared) != 1 or prepared[0]["requestId"] != request_id:
        raise JournalError("The requested mutation is not the one prepared.")
    finished = timestamp or utc_now()
    if not TIMESTAMP.fullmatch(finished) or not SAFE_CODE.fullmatch(str(outcome_code)):
        raise JournalError("Mutation completion timestamp or outcome is invalid.")
    prepared[0]["status"] = "completed"
    prepared[0]["finishedAtUtc"] = finished
    prepared[0]["outcomeCode"] = outcome_code
    journal["revision"] += 1
    validate_journal(journal)
    return journal


def mark_interrupted_uncertain(
    journal: dict[str, Any], timestamp: str | None = None
) -> dict[str, Any]:
    validate_journal(journal)
    prepared = [record for record in journal["records"] if record["status"] == "prepared"]
    if len(prepared) != 1:
        raise JournalError("No single prepared mutation requires recovery.")
    finished = timestamp or utc_now()
    if not TIMESTAMP.fullmatch(finished):
        raise JournalError("Mutation recovery timestamp is invalid.")
    prepared[0]["status"] = "uncertain"
    prepared[0]["finishedAtUtc"] = finished
    prepared[0]["outcomeCode"] = "controller-interrupted"
    journal["revision"] += 1
    validate_journal(journal)
    return journal


def resolve_uncertain_request(
    journal: dict[str, Any], request_id: str, outcome_code: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Resolve the latest uncertain record after separate live-state proof."""
    validate_journal(journal)
    uncertain = [record for record in journal["records"] if record["status"] == "uncertain"]
    if (
        len(uncertain) != 1
        or uncertain[0]["requestId"] != request_id
        or journal["records"][-1] is not uncertain[0]
    ):
        raise JournalError("The requested uncertain mutation is not the latest record.")
    finished = timestamp or utc_now()
    if not TIMESTAMP.fullmatch(finished) or not SAFE_CODE.fullmatch(str(outcome_code)):
        raise JournalError("Mutation resolution timestamp or outcome is invalid.")
    uncertain[0]["status"] = "completed"
    uncertain[0]["finishedAtUtc"] = finished
    uncertain[0]["outcomeCode"] = outcome_code
    journal["revision"] += 1
    validate_journal(journal)
    return journal


def resolve_root(root: Path) -> Path:
    if root.is_symlink():
        raise JournalError("Mutation journal root must not be a symlink.")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise JournalError("Mutation journal root must already exist.") from exc
    if not resolved.is_dir():
        raise JournalError("Mutation journal root must be a directory.")
    if os.name == "posix" and stat.S_IMODE(resolved.stat().st_mode) & 0o022:
        raise JournalError("Mutation journal root must not be group or world writable.")
    target = resolved / "mutation-journal.json"
    if target.is_symlink():
        raise JournalError("Mutation journal file must not be a symlink.")
    return target


def load_journal(root: Path) -> dict[str, Any]:
    target = resolve_root(root)
    try:
        if target.stat().st_size > 2 * 1024 * 1024:
            raise JournalError("Mutation journal exceeds its size limit.")
        value = json.loads(target.read_text(encoding="utf-8"))
    except JournalError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise JournalError("Cannot read mutation journal.") from exc
    validate_journal(value)
    return value


def save_journal(root: Path, journal: dict[str, Any]) -> None:
    validate_journal(journal)
    target = resolve_root(root)
    encoded = (json.dumps(journal, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".mutation-journal-", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        if os.name == "posix":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        if os.name == "posix":
            directory = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()
