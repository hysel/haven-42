#!/usr/bin/env python3
"""Validate the Windows Alpha stage ledger and its authority boundary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    value = json.loads((ROOT / "config/windows-alpha-stage-ledger.json").read_text(encoding="utf-8"))
    assert set(value) == {"schemaVersion", "ledgerId", "version", "distributionStatus", "stages", "stopBoundaries"}
    assert value["schemaVersion"] == 1
    assert value["ledgerId"] == "haven42.windows-alpha-0.4-alpha-1"
    assert value["version"] == "0.4.0-alpha.1"
    assert value["distributionStatus"] == "not-authorized"
    assert [item["id"] for item in value["stages"]] == list(range(1, 17))
    assert len({item["name"] for item in value["stages"]}) == 16
    assert all(set(item) == {"id", "name", "implementation", "nativeEvidence", "evidence"} for item in value["stages"])
    assert all(item["implementation"] in {"complete", "in-progress"} for item in value["stages"])
    assert all(item["nativeEvidence"] in {
        "not-required", "candidate-required",
        "current-candidate-three-vendor",
    } for item in value["stages"])
    assert all(
        isinstance(item["evidence"], list)
        and len(item["evidence"]) >= 2
        and all(isinstance(path, str) and (ROOT / path).is_file() for path in item["evidence"])
        for item in value["stages"]
    )
    assert sum(item["nativeEvidence"] == "candidate-required" for item in value["stages"]) == 1
    assert sum(item["nativeEvidence"] == "current-candidate-three-vendor" for item in value["stages"]) == 14
    assert value["stopBoundaries"] and all(flag is False for flag in value["stopBoundaries"].values())
    print("Windows alpha stage ledger tests passed: 12 checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
