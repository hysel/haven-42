#!/usr/bin/env python3
"""Hostile tests for the read-only project status consistency verifier."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "verify-project-status-consistency.py"
SPEC = importlib.util.spec_from_file_location("status_verifier", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def copy_inputs(target: Path, contract: dict) -> None:
    relatives = set(contract["documents"]) | set(contract["requiredMarkers"])
    for relative in relatives:
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())


def main() -> int:
    contract = MODULE.load_contract()
    checks = 0
    require(MODULE.verify(ROOT, contract) == [], "repository status should align")
    checks += 1

    hostile_mutations = [
        ("README.md", "Milestone 27:", "Milestone 127:"),
        ("ROADMAP.md", "Milestone 28:", "Milestone 128:"),
        (
            "docs/solution-architecture-review.md",
            "| 22: Unified Product UI And Task Composition | In progress;",
            "| 22: Unified Product UI And Task Composition | Complete;",
        ),
        (
            "README.md",
            "| Milestone 25: Local Video Generation | Research in progress |",
            "| Milestone 25: Local Video Generation | Complete |",
        ),
        (
            "ROADMAP.md",
            "| Milestone 26: Hardware-Adaptive Model Quantization | Engine evidence expanded |",
            "| Milestone 26: Hardware-Adaptive Model Quantization | Proposed |",
        ),
        (
            "TODO.md",
            "## Milestone 28: Controlled Web Research",
            "## Removed Milestone",
        ),
        (
            "PROJECT.md",
            "Milestones 24 and 25 retain documentation-only",
            "Milestones XX retain documentation-only",
        ),
    ]
    with tempfile.TemporaryDirectory(prefix="haven42-status-") as raw:
        base = Path(raw)
        for index, (relative, old, new) in enumerate(hostile_mutations):
            case = base / str(index)
            copy_inputs(case, contract)
            path = case / relative
            text = path.read_text(encoding="utf-8")
            require(old in text, f"test mutation marker missing: {old}")
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            require(MODULE.verify(case, contract), f"mutation {index} was accepted")
            checks += 1

    malformed = json.loads(json.dumps(contract))
    malformed["effects"]["networkAllowed"] = True
    with tempfile.TemporaryDirectory(prefix="haven42-status-contract-") as raw:
        path = Path(raw) / "contract.json"
        path.write_text(json.dumps(malformed), encoding="utf-8")
        try:
            MODULE.load_contract(path)
        except MODULE.StatusError:
            checks += 1
        else:
            raise AssertionError("effect-enabling contract was accepted")

    duplicate = (
        "| Milestone 28: Controlled Web Research | Proposed | first |\n"
        "| Milestone 28: Controlled Web Research | Proposed | second |\n"
    )
    try:
        MODULE.table_statuses(duplicate, "Milestone ")
    except MODULE.StatusError:
        checks += 1
    else:
        raise AssertionError("duplicate table row was accepted")

    print(f"Project status consistency hostile tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
