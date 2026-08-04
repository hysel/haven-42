#!/usr/bin/env python3
"""Fail when an open roadmap item is absent or ambiguously classified."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "TODO.md"
LEDGER = ROOT / "config" / "roadmap-closure-ledger.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def open_item_hashes() -> set[str]:
    lines = TODO.read_text(encoding="utf-8").splitlines()
    hashes: set[str] = set()
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)- \[ \] (.*)$", line)
        if match is None:
            continue
        indent = len(match.group(1))
        text = match.group(2).strip()
        cursor = index + 1
        while cursor < len(lines):
            continuation = lines[cursor]
            if not continuation.strip() or continuation.startswith("## "):
                break
            if re.match(r"^\s*- \[[ x]\] ", continuation):
                break
            if len(continuation) - len(continuation.lstrip()) <= indent:
                break
            text += " " + continuation.strip()
            cursor += 1
        normalized = " ".join(text.split())
        hashes.add(hashlib.sha256(normalized.encode("utf-8")).hexdigest())
    return hashes


def main() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert ledger["schemaVersion"] == 1
    assert ledger["source"] == "TODO.md"
    categories = ledger["categories"]
    assert len(categories) == 7
    recorded: list[str] = []
    for name, values in categories.items():
        assert re.fullmatch(r"[a-z][a-z0-9-]{2,63}", name)
        assert isinstance(values, list) and values
        assert all(isinstance(value, str) and SHA256.fullmatch(value) for value in values)
        recorded.extend(values)
    assert len(recorded) == len(set(recorded)), "an open item has multiple classifications"
    actual = open_item_hashes()
    assert set(recorded) == actual, "the closure ledger does not exactly cover open TODO items"
    assert len(actual) == 48
    authority = ledger["authority"]
    assert authority and all(value is False for value in authority.values())
    print("Roadmap closure ledger passed 48 exact open-item classifications.")


if __name__ == "__main__":
    main()
