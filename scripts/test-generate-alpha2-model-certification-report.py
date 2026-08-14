#!/usr/bin/env python3
"""Checks for ordered Alpha 2 model certification reporting."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/generate-alpha2-model-certification-report.py"


def load_module():
    specification = importlib.util.spec_from_file_location("alpha2_certification", SCRIPT)
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


def fixture(module, highest: str = "soakPassed") -> dict:
    passed = True
    gates = {}
    for name, _ in module.GATES:
        gates[name] = {"passed": passed, "evidence": [f"evidence/{name}.json"] if passed else []}
        if name == highest:
            passed = False
    gates[module.FAILURE_GATE] = {"passed": False, "evidence": []}
    return {
        "modelId": "fixture-3b-q4",
        "identity": {
            "provider": "ollama", "runtimeVersion": "0.32.8",
            "model": "fixture:3b-q4", "manifestDigest": "a" * 64,
        },
        "environment": {
            "operatingSystem": "Windows 11", "acceleratorVendor": "AMD",
            "acceleratorModel": "Fixture GPU", "driverVersion": "1.2.3",
        },
        "assessment": {
            "campaignScope": "shared-baseline", "fitStatus": "comfortable",
            "executionMode": "full-accelerator",
            "tasks": {"chat": "passed", "writing": "passed", "summarization": "passed"},
            "recommendationStatus": "candidate", "recommendationRole": "Balanced text candidate",
            "limitations": ["Comparative review remains open"],
            "measurements": {
                "averageTokensPerSecond": 42.5, "acceleratorMemoryGiB": 3.5,
                "systemMemoryGiB": 16, "averagePowerWatts": None,
            },
        },
        "gates": gates,
        "ownerApprovalReference": None,
    }


def main() -> int:
    module = load_module()
    record = fixture(module)
    normalized = module.normalize_record(record)
    assert normalized["label"] == "Soak passed"
    assert normalized["nextGate"] == "Hardware verified"
    assert normalized["automaticPromotionAllowed"] is False

    out_of_order = fixture(module, "taskQualified")
    out_of_order["gates"]["hardwareVerified"] = {"passed": True, "evidence": ["evidence/hardware.json"]}
    refused(lambda: module.normalize_record(out_of_order), "certification-gates-out-of-order")

    default = fixture(module, "defaultCandidate")
    default["assessment"]["recommendationStatus"] = "recommended"
    refused(lambda: module.normalize_record(default), "unsafe-evidence-reference")
    default["ownerApprovalReference"] = "approvals/owner-default-decision.md"
    default_record = module.normalize_record(default)
    assert default_record["label"] == "Default candidate"
    assert default_record["automaticPromotionAllowed"] is False

    failed = fixture(module)
    failed["gates"][module.FAILURE_GATE] = {"passed": True, "evidence": ["evidence/failure.json"]}
    assert module.normalize_record(failed)["label"] == "Failed or needs retest"

    unsafe_fit = fixture(module, "recommended")
    unsafe_fit["assessment"]["recommendationStatus"] = "recommended"
    unsafe_fit["assessment"]["fitStatus"] = "borderline"
    refused(lambda: module.normalize_record(unsafe_fit), "unsafe-recommendation-fit")

    unsafe = fixture(module)
    unsafe["gates"]["discovered"]["evidence"] = ["../private-lab.json"]
    refused(lambda: module.normalize_record(unsafe), "unsafe-evidence-reference")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "manifest.json"
        path.write_text(json.dumps({"schemaVersion": 1, "records": [record]}), encoding="utf-8")
        report = module.build_report(module.load_manifest(path))
        assert report["labelCounts"]["Soak passed"] == 1
        assert report["disclosures"] == {
            "automaticPromotionPerformed": False, "defaultSelectionChanged": False,
            "privateMachineIdentityRetained": False, "providerEndpointRetained": False,
        }
        rendered = module.markdown(report)
        assert "**Soak passed**" in rendered
        assert "Hardware verified" in rendered
        assert "shared-baseline" in rendered
        assert "chat: passed" in rendered
        assert "No automatic promotion" in rendered

    source = SCRIPT.read_text(encoding="utf-8")
    assert "defaultSelectionChanged\": False" in source
    assert "providerEndpointRetained\": False" in source
    assert "urlopen" not in source and "subprocess" not in source
    print("alpha2 model certification report checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
