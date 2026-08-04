#!/usr/bin/env python3
"""Evaluate quantized-artifact lifecycle requests without effects."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "config/quantized-artifact-lifecycle-contract.json").read_text(encoding="utf-8"))
DIGEST = re.compile(r"[0-9a-f]{64}")
REVISION = re.compile(r"[0-9a-f]{40}")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+:/-]{0,127}")


class LifecycleError(ValueError):
    pass


def strict(value: Any, fields: list[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != set(fields):
        raise LifecycleError(f"invalid-{label}-shape")
    return value


def scan(value: Any) -> None:
    if isinstance(value, dict):
        if set(value) & set(CONTRACT["forbiddenFields"]):
            raise LifecycleError("forbidden-authority")
        for child in value.values(): scan(child)
    elif isinstance(value, list):
        for child in value: scan(child)


def evaluate(request: dict) -> dict:
    if CONTRACT["status"] != "simulation-only-inactive" or any(CONTRACT["effects"].values()):
        raise LifecycleError("unsafe-contract")
    scan(request)
    strict(request, CONTRACT["requiredFields"], "request")
    if request["schemaVersion"] != 1 or request["operation"] not in CONTRACT["operations"]:
        raise LifecycleError("unsupported-request")
    source = strict(request["source"], CONTRACT["sourceFields"], "source")
    derivative = strict(request["derivative"], CONTRACT["derivativeFields"], "derivative")
    recipe = strict(request["recipe"], CONTRACT["recipeFields"], "recipe")
    compatibility = strict(request["compatibility"], CONTRACT["compatibilityFields"], "compatibility")
    storage = strict(request["storage"], CONTRACT["storageFields"], "storage")
    validation = strict(request["validation"], CONTRACT["validationFields"], "validation")
    state = strict(request["state"], CONTRACT["stateFields"], "state")
    if (not IDENTIFIER.fullmatch(source["repository"]) or ".." in source["repository"] or source["repository"].startswith(("/", "\\")) or not REVISION.fullmatch(source["revision"])):
        raise LifecycleError("moving-or-invalid-source")
    if not DIGEST.fullmatch(source["sha256"]) or not DIGEST.fullmatch(derivative["sha256"]):
        raise LifecycleError("invalid-digest")
    if source["sha256"] == derivative["sha256"]:
        raise LifecycleError("source-derivative-replay")
    if source["derivativeAllowed"] is not True or not source["license"] or source["license"] != derivative["license"]:
        raise LifecycleError("license-rejected")
    if derivative["provenanceComplete"] is not True or derivative["sizeBytes"] <= 0:
        raise LifecycleError("provenance-incomplete")
    if recipe["bits"] not in {2, 3, 4, 5, 6, 8} or not all(recipe[key] for key in ("tool", "toolVersion", "method")):
        raise LifecycleError("invalid-recipe")
    if not all(compatibility[key] for key in ("runtime", "runtimeVersion", "operatingSystem", "architecture", "accelerator", "driver")):
        raise LifecycleError("compatibility-incomplete")
    if compatibility["contextTokens"] <= 0 or compatibility["fullOffloadRequired"] is not True:
        raise LifecycleError("compatibility-rejected")
    if any(type(storage[key]) is not int or storage[key] < 0 for key in storage):
        raise LifecycleError("invalid-storage")
    if storage["finalBytes"] != derivative["sizeBytes"] or storage["availableBytes"] < storage["finalBytes"] + storage["temporaryBytes"] + storage["reserveBytes"]:
        raise LifecycleError("storage-insufficient")
    if any(type(value) is not bool for value in validation.values()):
        raise LifecycleError("invalid-validation")
    if validation["silentFallbackObserved"]:
        raise LifecycleError("silent-fallback-rejected")
    if state["phase"] not in CONTRACT["statePhases"]:
        raise LifecycleError("invalid-state")

    operation = request["operation"]
    transitions = ["identity-verified", "license-verified", "recipe-verified", "compatibility-verified", "storage-verified"]
    if operation == "inspect":
        status = "exact-cell-eligible" if all(value for key, value in validation.items() if key != "silentFallbackObserved") else "validation-incomplete"
    elif operation == "plan-activation":
        if state["phase"] != "staged" or not all(value for key, value in validation.items() if key != "silentFallbackObserved"):
            raise LifecycleError("activation-preconditions-failed")
        status = "activation-plan-only"; transitions += ["atomic-selection-planned", "post-health-planned", "automatic-rollback-planned"]
    elif operation == "plan-rollback":
        if state["phase"] != "rollback-required" or not state["previousArtifactId"] or not validation["rollbackPassed"]:
            raise LifecycleError("rollback-preconditions-failed")
        status = "rollback-plan-only"; transitions += ["known-good-restore-planned"]
    elif operation == "recover-interrupted":
        if state["phase"] not in {"converting", "activating", "rollback-required"}:
            raise LifecycleError("no-interrupted-operation")
        status = "recovery-plan-only"; transitions += ["stop-before-new-effects", "preserve-known-good", "exact-partial-cleanup-planned"]
    else:
        if state["phase"] != "partial-cleanup" or not state["partialArtifactId"]:
            raise LifecycleError("partial-cleanup-preconditions-failed")
        status = "partial-cleanup-plan-only"; transitions += ["exact-partial-artifact-removal-planned"]
    return {"schemaVersion": 1, "status": status, "operation": operation, "transitions": transitions, "catalogAdmissionAllowed": status == "exact-cell-eligible", "effects": copy.deepcopy(CONTRACT["effects"])}


if __name__ == "__main__":
    fixture = json.loads((ROOT / "examples/fixtures/quantized-artifact-lifecycle-request.json").read_text(encoding="utf-8"))
    print(json.dumps(evaluate(fixture), indent=2, sort_keys=True))
