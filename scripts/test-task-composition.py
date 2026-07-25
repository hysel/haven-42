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


def request(steps, cancel=False, attempt=0, retry_of=None, mode=None):
    return {
        "schemaVersion": 1,
        "compositionId": "review-project",
        "steps": steps,
        "cancelRequested": cancel,
        "lifecycle": {
            "attempt": attempt,
            "retryOf": retry_of,
            "mode": mode or ("cancel" if cancel else "fresh"),
        },
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
    assert result["steps"][0]["artifact"] == {
        "schemaVersion": 1,
        "artifactType": "workflow-plan-reference",
        "status": "planned",
        "workflowName": "Profile Local Hardware",
        "sourceStepId": "profile",
        "consumerStepIds": ["recommend"],
        "classification": "metadata-only",
        "contentIncluded": False,
        "validationStatus": "contract-validated",
    }
    assert all(
        item["approval"] == {
            "required": False,
            "authority": "engine-owned",
            "rendererGrantAccepted": False,
        }
        for item in result["steps"]
    )

    cancelled = MODULE.plan_composition(request(steps, True), CONTRACT, REGISTRY)
    assert cancelled["state"] == "cancelled" and cancelled["steps"] == []
    retried = MODULE.plan_composition(
        request(steps, attempt=1, retry_of="previous-review", mode="retry"),
        CONTRACT,
        REGISTRY,
    )
    assert retried["attempt"] == 1 and retried["retryOf"] == "previous-review"
    assert [event["type"] for event in retried["events"]][1] == "retry-planned"

    rejected({**request(steps), "arguments": []}, "invalid-request-fields")
    rejected({**request(steps), "approvalGrant": "renderer-value"}, "invalid-request-fields")
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
    rejected(request(steps, attempt=3, retry_of="older", mode="retry"), "invalid-lifecycle-attempt")
    rejected(request(steps, attempt=1, mode="retry"), "invalid-retry-identity")
    rejected(request(steps, attempt=1, retry_of="review-project", mode="retry"), "invalid-retry-identity")
    rejected(request(steps, attempt=1, retry_of="older", mode="fresh"), "invalid-fresh-lifecycle")
    rejected(request(steps, mode="cancel"), "invalid-cancel-lifecycle")
    rejected(request(steps, cancel=True, mode="fresh"), "cancellation-lifecycle-mismatch")
    hostile_lifecycle = request(steps)
    hostile_lifecycle["lifecycle"]["resumeToken"] = "renderer-value"
    rejected(hostile_lifecycle, "invalid-lifecycle-fields")
    print("Task composition planner passed 19 bounded, effect-free checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
