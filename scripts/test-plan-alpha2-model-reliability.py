#!/usr/bin/env python3
"""Deterministic safety checks for Alpha 2 reliability preparation."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/plan-alpha2-model-reliability.py"
CONTRACT = ROOT / "config/alpha-2-model-reliability-contract.json"
FIXTURE = ROOT / "examples/fixtures/alpha-2-model-reliability-request.json"


def load_module():
    specification = importlib.util.spec_from_file_location("alpha2_reliability_plan", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def refused(callback, message: str) -> None:
    try:
        callback()
    except Exception as error:
        assert str(error) == message, (str(error), message)
    else:
        raise AssertionError(f"expected refusal: {message}")


def main() -> int:
    module = load_module()
    contract = module.load_json(CONTRACT)
    request = module.load_json(FIXTURE)
    plan = module.build_plan(contract, request)
    assert plan["kind"] == "haven42-alpha2-model-reliability-plan"
    assert len(plan["actions"]) == 8
    assert all(item["status"] == "blocked-awaiting-explicit-execution-approval" for item in plan["actions"])
    assert all(value is False for value in plan["effects"].values())
    assert plan["evidence"] == {
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "containsProviderEndpoint": False,
        "automaticPromotionAllowed": False,
        "automaticDefaultChangeAllowed": False,
    }
    sleep = next(item for item in plan["actions"] if item["scenarioId"] == "sleep-and-wake-recovery")
    assert sleep["requiredPreflight"]["operatorPresentForPowerTransition"] is False
    assert all(value is False or value is None for value in sleep["requiredPreflight"].values())

    unsupported = copy.deepcopy(request)
    decision = next(item for item in unsupported["scenarioDecisions"] if item["id"] == "sleep-and-wake-recovery")
    decision.update({"decision": "not-supported", "reason": "Sleep is unavailable on this test profile."})
    unsupported_plan = module.build_plan(contract, unsupported)
    unsupported_sleep = next(item for item in unsupported_plan["actions"] if item["scenarioId"] == "sleep-and-wake-recovery")
    assert unsupported_sleep["status"] == "not-supported"

    incomplete = copy.deepcopy(request)
    incomplete["scenarioDecisions"].pop()
    refused(lambda: module.build_plan(contract, incomplete), "incomplete-scenario-decisions")

    preapproved = copy.deepcopy(request)
    preapproved["executionApprovalReference"] = "approvals/old-approval.md"
    refused(lambda: module.build_plan(contract, preapproved), "execution-approval-cannot-be-prebound")

    cpu = copy.deepcopy(request)
    cpu["environment"]["backend"] = "cpu"
    refused(lambda: module.build_plan(contract, cpu), "cpu-backend-gpu-memory-mismatch")

    unsafe_contract = copy.deepcopy(contract)
    unsafe_contract["globalSafety"]["realDiskFillAllowed"] = True
    refused(lambda: module.build_plan(unsafe_contract, request), "invalid-reliability-contract")

    source = SCRIPT.read_text(encoding="utf-8")
    assert "subprocess" not in source and "urlopen" not in source and "sleep(" not in source
    assert '"modelExecuted": False' in source
    assert '"powerStateChanged": False' in source
    print("alpha2 model reliability preparation checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
