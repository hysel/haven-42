#!/usr/bin/env python3
"""Hostile and happy-path tests for the effect-free composition planner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "task_composition",
    ROOT / "scripts" / "simulate-task-composition.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT = json.loads((ROOT / "config/task-composition-contract.json").read_text())
REGISTRY = json.loads((ROOT / "config/workflows.json").read_text())


def request(steps, cancel=False):
    return {
        "schemaVersion": 1,
        "compositionId": "review-project",
        "steps": steps,
        "cancelRequested": cancel,
    }


def rejected(value, code):
    try:
        MODULE.plan_composition(value, CONTRACT, REGISTRY)
    except MODULE.CompositionError as error:
        assert str(error) == code
        return
    raise AssertionError(f"composition unexpectedly admitted: {code}")


def main() -> int:
    steps = [
        {"stepId": "profile", "workflowId": "profile-local-hardware", "dependsOn": []},
        {"stepId": "recommend", "workflowId": "recommend-agent-config", "dependsOn": ["profile"]},
        {"stepId": "health", "workflowId": "test-local-agent-health", "dependsOn": ["recommend"]},
    ]
    result = MODULE.plan_composition(request(steps), CONTRACT, REGISTRY)
    assert result["state"] == "planned"
    assert [item["stepId"] for item in result["steps"]] == ["profile", "recommend", "health"]
    assert result["executionAllowed"] is False
    assert not any(result["effects"].values())
    assert all(item["artifact"]["status"] == "planned" for item in result["steps"])

    cancelled = MODULE.plan_composition(request(steps, True), CONTRACT, REGISTRY)
    assert cancelled["state"] == "cancelled" and cancelled["steps"] == []

    rejected({**request(steps), "arguments": []}, "invalid-request-fields")
    rejected(request([]), "invalid-step-count")
    rejected(request(steps + steps + [steps[0]]), "invalid-step-count")
    rejected(request([
        {"stepId": "write", "workflowId": "apply-agent-config", "dependsOn": []},
    ]), "workflow-not-admitted-for-composition")
    rejected(request([
        {"stepId": "one", "workflowId": "profile-local-hardware", "dependsOn": ["two"]},
        {"stepId": "two", "workflowId": "test-local-agent-health", "dependsOn": ["one"]},
    ]), "cyclic-composition")
    rejected(request([
        {"stepId": "one", "workflowId": "profile-local-hardware", "dependsOn": ["missing"]},
    ]), "unknown-or-self-dependency")
    rejected(request([
        {
            "stepId": "one",
            "workflowId": "profile-local-hardware",
            "dependsOn": [],
            "arguments": ["--hostile"],
        },
    ]), "invalid-step-fields")
    print("Task composition planner passed 10 bounded, effect-free checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
