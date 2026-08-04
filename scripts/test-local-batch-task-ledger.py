#!/usr/bin/env python3
"""Validate the recovered 374-item local-batch reconciliation ledger."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "local-batch-task-ledger.json"
EXPECTED_PHASE_COUNTS = {
    0: 9,
    1: 35,
    2: 20,
    3: 25,
    4: 19,
    5: 17,
    6: 30,
    7: 19,
    8: 16,
    9: 23,
    10: 20,
    11: 17,
    12: 12,
    13: 33,
    14: 16,
    15: 13,
    16: 22,
    17: 28,
}
HEADERS = [
    "task_id",
    "phase",
    "phase_title",
    "status",
    "blocker",
    "task",
    "evidence",
    "notes",
]
PRIVATE_VALUE = re.compile(
    r"(?:[A-Za-z]:\\|/" r"home/|/" r"Users/|(?:\d{1,3}\.){3}\d{1,3}|"
    r"BEGIN [A-Z ]*PRIVATE KEY)"
)
GIT_EVIDENCE = re.compile(r"git:[0-9a-f]{7,40}")


def validate_evidence(value: str) -> None:
    for reference in value.split(";"):
        reference = reference.strip()
        assert reference
        if GIT_EVIDENCE.fullmatch(reference):
            continue
        path = Path(reference)
        assert not path.is_absolute() and ".." not in path.parts
        assert (ROOT / path).exists(), f"evidence path does not exist: {reference}"


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schemaVersion"] == 1
    assert contract["phaseCount"] == 18
    assert contract["taskCount"] == 374
    assert re.fullmatch(r"[0-9a-f]{64}", contract["sourceSha256"])
    assert contract["authority"] and all(
        value is False for value in contract["authority"].values()
    )

    ledger = ROOT / contract["taskLedger"]
    with ledger.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        assert reader.fieldnames == HEADERS
        rows = list(reader)

    assert len(rows) == contract["taskCount"]
    statuses = set(contract["statuses"])
    blockers = set(contract["blockers"])
    ids: set[str] = set()
    actual_phase_counts = {phase: 0 for phase in EXPECTED_PHASE_COUNTS}
    phase_sequences = {phase: 0 for phase in EXPECTED_PHASE_COUNTS}

    for row in rows:
        phase = int(row["phase"])
        assert phase in EXPECTED_PHASE_COUNTS
        phase_sequences[phase] += 1
        expected_id = f"P{phase:02d}-{phase_sequences[phase]:03d}"
        assert row["task_id"] == expected_id
        assert row["task_id"] not in ids
        ids.add(row["task_id"])
        actual_phase_counts[phase] += 1

        task = " ".join(row["task"].split())
        assert task
        assert row["phase_title"].strip()
        assert row["status"] in statuses
        assert row["blocker"] in blockers
        assert not PRIVATE_VALUE.search(" ".join(row.values()))

        if row["status"] == "completed":
            assert row["evidence"], f"{row['task_id']} completion lacks evidence"
            assert row["blocker"] == "none"
            validate_evidence(row["evidence"])
        elif row["status"] == "blocked":
            assert row["blocker"] != "none"
            assert row["evidence"] and row["notes"]
            validate_evidence(row["evidence"])
        elif row["status"] == "deferred":
            assert row["blocker"] in {"owner", "signing-release"}
            assert row["evidence"] and row["notes"]
            validate_evidence(row["evidence"])
        elif row["status"] == "partial":
            assert row["evidence"] and row["notes"]
            validate_evidence(row["evidence"])
        else:
            assert row["blocker"] == "none"

    assert actual_phase_counts == EXPECTED_PHASE_COUNTS
    print("Local batch task ledger passed 374 exact tasks across 18 phases.")


if __name__ == "__main__":
    main()
