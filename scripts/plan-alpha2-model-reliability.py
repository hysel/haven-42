#!/usr/bin/env python3
"""Prepare a content-free Alpha 2 reliability plan without executing it."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config/alpha-2-model-reliability-contract.json"
MAX_INPUT_BYTES = 2 * 1024 * 1024
SAFE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,99}")
SAFE_DIGEST = re.compile(r"[0-9a-f]{64}")
SAFE_TEXT = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._()+:/-]{0,199}")
SAFE_NARRATIVE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .,;:'()/_+-]{0,499}")


class ReliabilityPlanError(ValueError):
    """The reliability preparation request or contract was unsafe."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_INPUT_BYTES:
            raise ReliabilityPlanError("unsafe-reliability-input")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReliabilityPlanError("invalid-reliability-input") from error
    if not isinstance(value, dict):
        raise ReliabilityPlanError("invalid-reliability-input")
    return value


def canonical_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def safe_text(value: Any) -> str:
    if not isinstance(value, str) or not SAFE_TEXT.fullmatch(value):
        raise ReliabilityPlanError("unsafe-reliability-text")
    return value


def safe_narrative(value: Any) -> str:
    if not isinstance(value, str) or not SAFE_NARRATIVE.fullmatch(value):
        raise ReliabilityPlanError("unsafe-reliability-narrative")
    return value


def finite(value: Any, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not 0 <= float(value) <= maximum:
        raise ReliabilityPlanError("invalid-reliability-capacity")
    return float(value)


def validate_contract(contract: dict[str, Any]) -> list[dict[str, Any]]:
    required = {
        "schemaVersion", "contractId", "release", "status", "evidenceLabelsAllowed",
        "globalSafety", "scenarios", "universalStopConditions",
    }
    safety = contract.get("globalSafety")
    scenarios = contract.get("scenarios")
    if (
        set(contract) != required
        or contract.get("schemaVersion") != 1
        or contract.get("contractId") != "haven42.alpha2.model-reliability"
        or contract.get("release") != "0.4.0-alpha.2"
        or contract.get("status") != "preparation-only-explicit-execution-approval-required"
        or not isinstance(safety, dict)
        or set(safety.values()) - {True, False}
        or safety.get("freshExecutionApprovalRequired") is not True
        or safety.get("activeCampaignIsolationRequired") is not True
        or safety.get("automaticPromotionAllowed") is not False
        or safety.get("automaticDefaultChangeAllowed") is not False
        or safety.get("realDiskFillAllowed") is not False
        or safety.get("unboundedMemoryPressureAllowed") is not False
        or safety.get("wildcardProcessTerminationAllowed") is not False
        or not isinstance(scenarios, list)
        or len(scenarios) != 8
        or not isinstance(contract.get("universalStopConditions"), list)
        or not contract["universalStopConditions"]
    ):
        raise ReliabilityPlanError("invalid-reliability-contract")
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict) or set(scenario) != {
            "id", "name", "authority", "minimumAttempts", "maximumMinutes",
            "procedure", "passCriteria",
        }:
            raise ReliabilityPlanError("invalid-reliability-contract")
        scenario_id = scenario["id"]
        if (
            not isinstance(scenario_id, str) or not SAFE_ID.fullmatch(scenario_id)
            or scenario_id in seen
            or not isinstance(scenario["minimumAttempts"], int) or isinstance(scenario["minimumAttempts"], bool)
            or not 1 <= scenario["minimumAttempts"] <= 10
            or not isinstance(scenario["maximumMinutes"], int) or isinstance(scenario["maximumMinutes"], bool)
            or not 5 <= scenario["maximumMinutes"] <= 120
            or not isinstance(scenario["procedure"], list) or not scenario["procedure"]
            or not isinstance(scenario["passCriteria"], list) or not scenario["passCriteria"]
        ):
            raise ReliabilityPlanError("invalid-reliability-contract")
        safe_text(scenario["name"])
        safe_text(scenario["authority"])
        for text in scenario["procedure"] + scenario["passCriteria"]:
            safe_narrative(text)
        seen.add(scenario_id)
    return scenarios


def validate_request(request: dict[str, Any], scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    required = {
        "schemaVersion", "campaignId", "identity", "environment",
        "scenarioDecisions", "executionApprovalReference",
    }
    if set(request) != required or request.get("schemaVersion") != 1:
        raise ReliabilityPlanError("invalid-reliability-request")
    campaign_id = request["campaignId"]
    if not isinstance(campaign_id, str) or not SAFE_ID.fullmatch(campaign_id):
        raise ReliabilityPlanError("invalid-reliability-request")
    identity = request["identity"]
    environment = request["environment"]
    if not isinstance(identity, dict) or set(identity) != {"provider", "runtimeVersion", "modelId", "model", "manifestDigest"}:
        raise ReliabilityPlanError("invalid-reliability-request")
    if not isinstance(environment, dict) or set(environment) != {
        "platformFamily", "operatingSystem", "backend", "acceleratorVendor",
        "acceleratorModel", "driverVersion", "systemMemoryGiB", "usableGpuMemoryGiB",
    }:
        raise ReliabilityPlanError("invalid-reliability-request")
    if not isinstance(identity["modelId"], str) or not SAFE_ID.fullmatch(identity["modelId"]):
        raise ReliabilityPlanError("invalid-reliability-request")
    if not isinstance(identity["manifestDigest"], str) or not SAFE_DIGEST.fullmatch(identity["manifestDigest"]):
        raise ReliabilityPlanError("invalid-reliability-request")
    for value in (identity[name] for name in ("provider", "runtimeVersion", "model")):
        safe_text(value)
    for name in ("platformFamily", "operatingSystem", "backend", "acceleratorVendor", "acceleratorModel", "driverVersion"):
        safe_text(environment[name])
    system_memory = finite(environment["systemMemoryGiB"], 2048)
    gpu_memory = finite(environment["usableGpuMemoryGiB"], 256)
    if environment["backend"].lower() == "cpu" and gpu_memory != 0:
        raise ReliabilityPlanError("cpu-backend-gpu-memory-mismatch")
    decisions = request["scenarioDecisions"]
    if not isinstance(decisions, list) or len(decisions) != len(scenarios):
        raise ReliabilityPlanError("incomplete-scenario-decisions")
    normalized: dict[str, dict[str, Any]] = {}
    expected = {item["id"] for item in scenarios}
    for decision in decisions:
        if not isinstance(decision, dict) or set(decision) != {"id", "decision", "reason"}:
            raise ReliabilityPlanError("invalid-scenario-decision")
        scenario_id = decision["id"]
        status = decision["decision"]
        reason = decision["reason"]
        if scenario_id not in expected or scenario_id in normalized or status not in {"prepare", "not-supported"}:
            raise ReliabilityPlanError("invalid-scenario-decision")
        if status == "prepare" and reason is not None:
            raise ReliabilityPlanError("unexpected-scenario-reason")
        if status == "not-supported":
            reason = safe_narrative(reason)
        normalized[scenario_id] = {"decision": status, "reason": reason}
    if set(normalized) != expected:
        raise ReliabilityPlanError("incomplete-scenario-decisions")
    if request["executionApprovalReference"] is not None:
        raise ReliabilityPlanError("execution-approval-cannot-be-prebound")
    return {
        "campaignId": campaign_id,
        "identity": {**identity, "manifestDigest": identity["manifestDigest"]},
        "environment": {**environment, "systemMemoryGiB": system_memory, "usableGpuMemoryGiB": gpu_memory},
        "decisions": normalized,
    }


def build_plan(contract: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    scenarios = validate_contract(contract)
    normalized = validate_request(request, scenarios)
    actions = []
    for scenario in scenarios:
        decision = normalized["decisions"][scenario["id"]]
        actions.append({
            "scenarioId": scenario["id"], "name": scenario["name"],
            "status": "blocked-awaiting-explicit-execution-approval" if decision["decision"] == "prepare" else "not-supported",
            "notSupportedReason": decision["reason"], "authority": scenario["authority"],
            "minimumAttempts": scenario["minimumAttempts"], "maximumMinutes": scenario["maximumMinutes"],
            "procedure": scenario["procedure"], "passCriteria": scenario["passCriteria"],
            "requiredPreflight": {
                "freshExecutionApproval": False,
                "noActiveCampaignOnTarget": False,
                "exactArtifactAndRuntimeVerified": False,
                "hostSafetyHeadroomVerified": False,
                "appOwnedProcessReceiptReady": False,
                "operatorPresentForPowerTransition": False if scenario["authority"] == "system-power-transition" else None,
            },
        })
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-model-reliability-plan",
        "generatedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "contract": {"path": "config/alpha-2-model-reliability-contract.json", "canonicalSha256": canonical_sha256(contract)},
        "campaignId": normalized["campaignId"], "identity": normalized["identity"],
        "environment": normalized["environment"], "actions": actions,
        "universalStopConditions": contract["universalStopConditions"],
        "effects": {
            "modelExecuted": False, "networkContacted": False, "processSignaled": False,
            "powerStateChanged": False, "resourcePressureApplied": False, "machineModified": False,
        },
        "evidence": {
            "containsRawPromptsOrResponses": False, "containsPrivateMachineIdentity": False,
            "containsProviderEndpoint": False, "automaticPromotionAllowed": False,
            "automaticDefaultChangeAllowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("output already exists or is unsafe")
    try:
        plan = build_plan(load_json(CONTRACT_PATH), load_json(args.request))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ReliabilityPlanError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({
        "campaignId": plan["campaignId"],
        "prepared": sum(item["status"].startswith("blocked") for item in plan["actions"]),
        "executed": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
