#!/usr/bin/env python3
"""Validate that newly discovered model evaluations remain fail closed."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WATCH_PATH = ROOT / "config" / "model-release-watch.json"
PLAN_PATH = ROOT / "config" / "model-release-evaluation-plan.json"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    watch = json.loads(WATCH_PATH.read_text(encoding="utf-8"))
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    checks = 0
    for key in ("downloadsAuthorizedByThisFile", "executionAuthorizedByThisFile", "hardwareChangesAuthorizedByThisFile", "promotionAuthorizedByThisFile"):
        check(plan["authority"][key] is False, f"{key} must remain false")
        checks += 1
    check(plan["authority"]["freshOwnerPromptRequiredToStart"] is True, "fresh start prompt must be required")
    checks += 1

    candidate_ids = {item["id"] for item in watch["candidates"]}
    planned_ids: set[str] = set()
    lane_ids: set[str] = set()
    for lane in plan["lanes"]:
        check(lane["id"] not in lane_ids, f"duplicate lane: {lane['id']}")
        lane_ids.add(lane["id"])
        check(len(lane["fixtures"]) >= 3, f"lane needs meaningful fixtures: {lane['id']}")
        check(bool(lane["requiredBeforeStart"]), f"lane needs pre-start gates: {lane['id']}")
        check(bool(lane["failClosedOn"]), f"lane needs fail-closed outcomes: {lane['id']}")
        checks += 4
        for candidate_id in lane["candidateIds"]:
            check(candidate_id in candidate_ids, f"unknown candidate in plan: {candidate_id}")
            check(candidate_id not in planned_ids, f"candidate appears in multiple lanes: {candidate_id}")
            planned_ids.add(candidate_id)
            checks += 2

    check(planned_ids == candidate_ids, "every runnable release-watch candidate must have exactly one evaluation lane")
    check(len(plan["commonGates"]) >= 8, "common evidence gates are incomplete")
    checks += 2
    print(f"Model release evaluation plan tests passed: {checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
