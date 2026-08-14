#!/usr/bin/env python3
"""Deterministic checks for reliability evidence validation."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
PLANNER_SCRIPT = ROOT / "scripts/plan-alpha2-model-reliability.py"
VALIDATOR_SCRIPT = ROOT / "scripts/validate-alpha2-model-reliability-evidence.py"
CONTRACT = ROOT / "config/alpha-2-model-reliability-contract.json"
FIXTURE = ROOT / "examples/fixtures/alpha-2-model-reliability-request.json"


def load_module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
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


def metrics(attempts: int) -> dict:
    return {
        "checksPassed": attempts,
        "checksFailed": 0,
        "firstTokenLatencyMs": [250.0] * attempts,
        "tokensPerSecond": [42.0] * attempts,
        "peakSystemMemoryMiB": 8192.0,
        "peakAcceleratorMemoryMiB": 4096.0,
        "acceleratorUseObserved": True,
        "modelUnloadPasses": attempts,
        "listenerCleanupPasses": attempts,
        "processCleanupPasses": attempts,
        "boundedErrorCodes": [],
    }


def main() -> int:
    planner = load_module("alpha2_reliability_planner_for_validation", PLANNER_SCRIPT)
    validator = load_module("alpha2_reliability_evidence", VALIDATOR_SCRIPT)
    plan = planner.build_plan(planner.load_json(CONTRACT), planner.load_json(FIXTURE))
    evidence = {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-model-reliability-evidence",
        "planBinding": {"canonicalSha256": validator.canonical_sha256(plan)},
        "campaignId": plan["campaignId"],
        "identity": plan["identity"],
        "environment": plan["environment"],
        "executionApprovalReference": "approvals/current-reliability-run.md",
        "startedAtUtc": "2026-08-12T15:00:00Z",
        "completedAtUtc": "2026-08-12T18:00:00Z",
        "scenarios": [
            {
                "scenarioId": action["scenarioId"],
                "outcome": "passed",
                "attempts": action["minimumAttempts"],
                "metrics": metrics(action["minimumAttempts"]),
            }
            for action in plan["actions"]
        ],
        "evidence": {
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
            "containsProviderEndpoint": False,
            "automaticPromotionAllowed": False,
            "automaticDefaultChangeAllowed": False,
        },
    }
    result = validator.validate(plan, evidence)
    assert result["outcome"] == "passed"
    assert result["scenarioCounts"] == {"passed": 8, "failed": 0, "not-supported": 0}
    assert result["automaticPromotionAllowed"] is False

    incomplete_cleanup = copy.deepcopy(evidence)
    incomplete_cleanup["scenarios"][0]["metrics"]["processCleanupPasses"] = 0
    refused(lambda: validator.validate(plan, incomplete_cleanup), "passing-reliability-evidence-incomplete")

    bad_binding = copy.deepcopy(evidence)
    bad_binding["planBinding"]["canonicalSha256"] = "0" * 64
    refused(lambda: validator.validate(plan, bad_binding), "reliability-plan-binding-mismatch")

    unsafe = copy.deepcopy(evidence)
    unsafe["evidence"]["containsRawPromptsOrResponses"] = True
    refused(lambda: validator.validate(plan, unsafe), "unsafe-reliability-disclosure")

    stale_approval = copy.deepcopy(evidence)
    stale_approval["executionApprovalReference"] = "../old-approval.md"
    refused(lambda: validator.validate(plan, stale_approval), "invalid-execution-approval-reference")

    failed = copy.deepcopy(evidence)
    failed["scenarios"][0]["outcome"] = "failed"
    failed["scenarios"][0]["metrics"]["checksFailed"] = 1
    failed_result = validator.validate(plan, failed)
    assert failed_result["outcome"] == "failed-needs-retest"

    source = VALIDATOR_SCRIPT.read_text(encoding="utf-8")
    assert "subprocess" not in source and "urlopen" not in source
    assert '"automaticPromotionAllowed": False' in source
    print("alpha2 model reliability evidence checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
