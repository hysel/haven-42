#!/usr/bin/env python3
"""Build the nonvisual Haven 42 UI model from committed contracts.

The output is renderer-safe presentation state. It cannot execute an operation,
mint an approval, select an executable, or turn an unavailable capability into
an available one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PLATFORMS = {"windows", "linux", "macos"}
BLOCKED_STATES = {"unavailable", "blocked", "failed"}


class UiModelError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise UiModelError(f"JSON root must be an object: {path}")
    return value


def availability_overrides(report: dict[str, Any] | None) -> dict[str, str]:
    if report is None:
        return {}
    if report.get("SchemaVersion") != 1 or report.get("Kind") != "capability-availability":
        raise UiModelError("Availability report must be a schema-v1 capability-availability report.")
    result: dict[str, str] = {}
    for item in report.get("Items", []):
        capability_id = item.get("CapabilityId")
        state = item.get("EffectiveAvailability")
        if not isinstance(capability_id, str) or state not in {"available", "configuration-required", "unavailable", "blocked", "failed"}:
            raise UiModelError("Availability report contains an invalid capability item.")
        result[capability_id] = state
    return result


def validate_onboarding(onboarding: dict[str, Any]) -> None:
    if onboarding.get("schemaVersion") != 1 or onboarding.get("runtimeAdmitted") is not False:
        raise UiModelError("Progressive onboarding must be schema v1 and runtime-admission false.")
    choices = {item.get("id"): item for item in onboarding.get("choices", [])}
    if set(choices) != {"guided-setup", "existing-setup", "not-now"}:
        raise UiModelError("Progressive onboarding must define the three product-wide choices.")
    if choices["guided-setup"].get("advancedSettingsAvailable") is not True or choices["existing-setup"].get("advancedSettingsAvailable") is not True:
        raise UiModelError("Guided and existing-setup paths must both expose advanced settings.")
    if choices["not-now"].get("advancedSettingsAvailable") is not False or choices["not-now"].get("createsMachineEffects") is not False:
        raise UiModelError("Not-now must be effect-free and must not expose advanced settings.")
    states = {item.get("id") for item in onboarding.get("configurationStates", [])}
    if states != {"validated", "customized", "unverified", "blocked"}:
        raise UiModelError("Progressive onboarding configuration states are incomplete.")
    derivation = onboarding.get("stateDerivation", {})
    if derivation.get("derivedByEnginePolicy") is not True or derivation.get("rendererMaySelectState") is not False:
        raise UiModelError("Configuration evidence state must be derived outside the renderer.")
    if onboarding.get("advancedSettings", {}).get("rawArbitraryCommandOrFlagEntryAllowed") is not False:
        raise UiModelError("Advanced onboarding cannot expose arbitrary commands or flags.")


def validate_contracts(ui: dict[str, Any], onboarding: dict[str, Any], capabilities: dict[str, Any], workflows: dict[str, Any]) -> None:
    if ui.get("schemaVersion") != 1 or ui.get("runtimeAdmitted") is not False:
        raise UiModelError("UI contract must be schema v1 and runtime-admission false.")
    capability_ids = {item["id"] for item in capabilities.get("capabilities", [])}
    workflow_by_id = {item["id"]: item for item in workflows.get("workflows", [])}
    route_ids = {item["id"] for item in ui.get("routes", [])}
    if len(route_ids) != len(ui.get("routes", [])):
        raise UiModelError("UI route ids must be unique.")
    if ui.get("firstRun", {}).get("networkProbeByDefault") is not False:
        raise UiModelError("First run cannot probe the network by default.")
    if ui.get("principles", {}).get("rendererIsExecutionAuthority") is not False:
        raise UiModelError("Renderer cannot be execution authority.")
    validate_onboarding(onboarding)
    experience = ui.get("onboardingExperience", {})
    if experience.get("choiceIds") != ["guided-setup", "existing-setup", "not-now"]:
        raise UiModelError("UI onboarding choices must preserve the shared contract order.")
    if experience.get("advancedSettingsChoiceIds") != ["guided-setup", "existing-setup"]:
        raise UiModelError("UI advanced settings must be available on both active setup paths.")
    if experience.get("rendererMayDeriveConfigurationState") is not False:
        raise UiModelError("Renderer cannot derive onboarding configuration state.")
    for action in ui.get("homeActions", []):
        if action.get("routeId") not in route_ids:
            raise UiModelError(f"Home action references unknown route: {action.get('routeId')}")
        operation_id = action.get("operationId")
        if action.get("operationKind") == "capability" and operation_id not in capability_ids:
            raise UiModelError(f"Home action references unknown capability: {operation_id}")
        if action.get("operationKind") == "workflow":
            workflow = workflow_by_id.get(operation_id)
            if workflow is None or workflow.get("uiReady") is not True:
                raise UiModelError(f"Home action references non-UI-ready workflow: {operation_id}")
    for route_id, ids in ui.get("routeWorkflows", {}).items():
        if route_id not in route_ids:
            raise UiModelError(f"Workflow group references unknown route: {route_id}")
        for workflow_id in ids:
            workflow = workflow_by_id.get(workflow_id)
            if workflow is None or workflow.get("uiReady") is not True:
                raise UiModelError(f"Route references non-UI-ready workflow: {workflow_id}")


def build(platform: str, first_run_complete: bool, availability: dict[str, Any] | None = None) -> dict[str, Any]:
    if platform not in PLATFORMS:
        raise UiModelError(f"Unsupported platform: {platform}")
    ui = load_json(ROOT / "config/ui-navigation-contract.json")
    onboarding = load_json(ROOT / "config/progressive-onboarding-contract.json")
    capabilities = load_json(ROOT / "config/capabilities.json")
    workflows = load_json(ROOT / "config/workflows.json")
    providers = load_json(ROOT / "config/providers.json")
    validate_contracts(ui, onboarding, capabilities, workflows)

    capability_by_id = {item["id"]: item for item in capabilities["capabilities"]}
    workflow_by_id = {item["id"]: item for item in workflows["workflows"]}
    provider_by_capability: dict[str, list[dict[str, Any]]] = {}
    for provider in providers["providers"]:
        for capability_id in provider["capabilityIds"]:
            provider_by_capability.setdefault(capability_id, []).append({
                "id": provider["id"],
                "name": provider["name"],
                "kind": provider["kind"],
                "validationStatus": provider["validationStatus"],
                "availability": provider["defaultAvailability"],
            })
    overrides = availability_overrides(availability)

    actions = []
    for definition in ui["homeActions"]:
        item = dict(definition)
        if definition["operationKind"] == "capability":
            capability = capability_by_id[definition["operationId"]]
            state = overrides.get(capability["id"], capability["availability"]["state"])
            item.update({
                "availability": state,
                "enabled": state not in BLOCKED_STATES,
                "requiresConfiguration": state == "configuration-required",
                "policy": capability["policy"],
                "providers": provider_by_capability.get(capability["id"], []),
                "outputArtifactTypes": capability["outputArtifactTypes"],
            })
        else:
            workflow = workflow_by_id[definition["operationId"]]
            item.update({
                "availability": "available",
                "enabled": True,
                "requiresConfiguration": False,
                "policy": {"safetyLevel": workflow["safetyLevel"]},
                "providers": [],
                "outputArtifactTypes": workflow["outputs"],
            })
        actions.append(item)

    route_workflows = {}
    for route_id, workflow_ids in ui["routeWorkflows"].items():
        route_workflows[route_id] = [{
            "id": workflow_id,
            "name": workflow_by_id[workflow_id]["name"],
            "purpose": workflow_by_id[workflow_id]["purpose"],
            "safetyLevel": workflow_by_id[workflow_id]["safetyLevel"],
            "inputs": workflow_by_id[workflow_id]["inputs"],
            "outputs": workflow_by_id[workflow_id]["outputs"],
        } for workflow_id in workflow_ids]

    return {
        "schemaVersion": 1,
        "kind": "ui-view-model",
        "platform": platform,
        "initialRouteId": "home" if first_run_complete else "welcome",
        "firstRunComplete": first_run_complete,
        "runtimeAdmitted": False,
        "executionEnabled": False,
        "navigation": ui["shell"]["primaryNavigation"] if first_run_complete else ["welcome", "privacy", "readiness"],
        "routes": ui["routes"],
        "onboarding": {
            "choices": onboarding["choices"],
            "advancedSettings": onboarding["advancedSettings"],
            "configurationStates": onboarding["configurationStates"],
            "presentation": onboarding["presentation"],
        },
        "homeActions": actions,
        "routeWorkflows": route_workflows,
        "taskStateMachine": ui["taskStateMachine"],
        "approvalReview": ui["approvalReview"],
        "resultPresentation": ui["resultPresentation"],
        "privacy": {
            "endpointPersisted": False,
            "promptOrArtifactContentPersisted": False,
            "rawPathsReturned": False,
            "networkProbeUsed": availability is not None and bool(availability.get("ProbeUsed")),
        },
        "sources": ui["sourceContracts"],
    }


def self_test() -> None:
    model = build("windows", False)
    assert model["initialRouteId"] == "welcome"
    assert model["executionEnabled"] is False
    assert [item["id"] for item in model["onboarding"]["choices"]] == ["guided-setup", "existing-setup", "not-now"]
    assert all("entryPoints" not in json.dumps(item) for item in model["homeActions"])
    ready = build("linux", True, {
        "SchemaVersion": 1,
        "Kind": "capability-availability",
        "ProbeUsed": True,
        "Items": [{"CapabilityId": "general.chat", "EffectiveAvailability": "available"}],
    })
    chat = next(item for item in ready["homeActions"] if item["operationId"] == "general.chat")
    assert ready["initialRouteId"] == "home" and chat["enabled"] is True
    hostile = json.loads(json.dumps(load_json(ROOT / "config/ui-navigation-contract.json")))
    hostile["homeActions"][0]["operationId"] = "arbitrary.command"
    try:
        validate_contracts(hostile, load_json(ROOT / "config/progressive-onboarding-contract.json"), load_json(ROOT / "config/capabilities.json"), load_json(ROOT / "config/workflows.json"))
    except UiModelError:
        pass
    else:
        raise AssertionError("Unknown operations must fail closed.")
    hostile_onboarding = json.loads(json.dumps(load_json(ROOT / "config/progressive-onboarding-contract.json")))
    hostile_onboarding["stateDerivation"]["rendererMaySelectState"] = True
    try:
        validate_onboarding(hostile_onboarding)
    except UiModelError:
        pass
    else:
        raise AssertionError("Renderer-selected evidence state must fail closed.")
    print("UI view-model self-test passed: 4 cases")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a renderer-safe Haven 42 UI view model.")
    parser.add_argument("--platform", choices=sorted(PLATFORMS), default="windows")
    parser.add_argument("--first-run-complete", action="store_true")
    parser.add_argument("--availability-path")
    parser.add_argument("--output-path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        availability = load_json(Path(args.availability_path)) if args.availability_path else None
        result = build(args.platform, args.first_run_complete, availability)
        rendered = json.dumps(result, indent=2) + "\n"
        if args.output_path:
            output = Path(args.output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, json.JSONDecodeError, UiModelError) as error:
        print(f"ui-view-model-error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
