#!/usr/bin/env python3
"""Validate and plan a bounded workflow composition without executing anything."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config" / "task-composition-contract.json"
WORKFLOWS_PATH = ROOT / "config" / "workflows.json"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


class CompositionError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CompositionError("configuration-unavailable") from error
    if not isinstance(value, dict):
        raise CompositionError("configuration-invalid")
    return value


def trusted_workflows(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = registry.get("workflows")
    if registry.get("schemaVersion") != 1 or not isinstance(records, list):
        raise CompositionError("workflow-registry-invalid")
    trusted: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise CompositionError("workflow-registry-invalid")
        workflow_id = record.get("id")
        if (
            isinstance(workflow_id, str)
            and record.get("uiReady") is True
            and record.get("safetyLevel") == "read-only"
        ):
            trusted[workflow_id] = record
    return trusted


def plan_composition(
    request: dict[str, Any],
    contract: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    request_contract = contract.get("request", {})
    required = set(request_contract.get("requiredFields", []))
    if set(request) != required:
        raise CompositionError("invalid-request-fields")
    if request.get("schemaVersion") != 1:
        raise CompositionError("unsupported-request-version")
    composition_id = request.get("compositionId")
    if not isinstance(composition_id, str) or not IDENTIFIER.fullmatch(composition_id):
        raise CompositionError("invalid-composition-id")
    if not isinstance(request.get("cancelRequested"), bool):
        raise CompositionError("invalid-cancellation-state")
    steps = request.get("steps")
    maximum = contract.get("maximumSteps")
    if (
        not isinstance(steps, list)
        or not steps
        or isinstance(maximum, bool)
        or not isinstance(maximum, int)
        or len(steps) > maximum
    ):
        raise CompositionError("invalid-step-count")

    trusted = trusted_workflows(registry)
    expected_step_fields = set(request_contract.get("stepFields", []))
    by_id: dict[str, dict[str, Any]] = {}
    for step in steps:
        if not isinstance(step, dict) or set(step) != expected_step_fields:
            raise CompositionError("invalid-step-fields")
        step_id = step.get("stepId")
        workflow_id = step.get("workflowId")
        dependencies = step.get("dependsOn")
        if (
            not isinstance(step_id, str)
            or not IDENTIFIER.fullmatch(step_id)
            or step_id in by_id
        ):
            raise CompositionError("invalid-or-duplicate-step-id")
        if not isinstance(workflow_id, str) or workflow_id not in trusted:
            raise CompositionError("workflow-not-admitted-for-composition")
        if (
            not isinstance(dependencies, list)
            or len(dependencies) > contract.get("maximumDependenciesPerStep", 0)
            or len(dependencies) != len(set(dependencies))
            or not all(isinstance(item, str) and IDENTIFIER.fullmatch(item) for item in dependencies)
        ):
            raise CompositionError("invalid-step-dependencies")
        by_id[step_id] = step

    if any(
        dependency not in by_id or dependency == step_id
        for step_id, step in by_id.items()
        for dependency in step["dependsOn"]
    ):
        raise CompositionError("unknown-or-self-dependency")

    pending = dict(by_id)
    ordered: list[dict[str, Any]] = []
    completed: set[str] = set()
    while pending:
        ready = [
            step for step in pending.values()
            if set(step["dependsOn"]).issubset(completed)
        ]
        if not ready:
            raise CompositionError("cyclic-composition")
        for step in sorted(ready, key=lambda value: value["stepId"]):
            ordered.append(step)
            completed.add(step["stepId"])
            del pending[step["stepId"]]

    events: list[dict[str, Any]] = [{
        "sequence": 1,
        "type": "accepted",
        "code": "COMPOSITION_PLAN_ACCEPTED",
    }]
    if request["cancelRequested"]:
        events.append({
            "sequence": 2,
            "type": "cancelled",
            "code": "COMPOSITION_CANCELLED_BEFORE_EXECUTION",
        })
        state = "cancelled"
        planned_steps: list[dict[str, Any]] = []
    else:
        planned_steps = []
        for step in ordered:
            workflow = trusted[step["workflowId"]]
            planned_steps.append({
                "stepId": step["stepId"],
                "workflowId": step["workflowId"],
                "dependsOn": list(step["dependsOn"]),
                "artifact": {
                    "artifactType": "workflow-plan-reference",
                    "status": "planned",
                    "workflowName": workflow["name"],
                },
            })
            events.append({
                "sequence": len(events) + 1,
                "type": "step-planned",
                "code": "COMPOSITION_STEP_PLANNED",
                "stepId": step["stepId"],
            })
        events.append({
            "sequence": len(events) + 1,
            "type": "result",
            "code": "COMPOSITION_PLAN_READY",
        })
        state = "planned"

    return {
        "schemaVersion": 1,
        "kind": "task-composition-plan",
        "compositionId": composition_id,
        "state": state,
        "executionAllowed": False,
        "steps": planned_steps,
        "events": events,
        "effects": {
            "processCreation": False,
            "filesystemAccess": False,
            "networkAccess": False,
            "machineModification": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    try:
        request = load_json(Path(args.request))
        result = plan_composition(
            request,
            load_json(CONTRACT_PATH),
            load_json(WORKFLOWS_PATH),
        )
    except CompositionError as error:
        print(json.dumps({
            "schemaVersion": 1,
            "kind": "task-composition-error",
            "state": "rejected",
            "error": str(error),
            "executionAllowed": False,
        }, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
