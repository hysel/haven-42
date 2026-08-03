#!/usr/bin/env python3
"""Hostile tests for the pure PDF OS-isolation evidence gate."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/evaluate-pdf-os-isolation.py"
SPEC = importlib.util.spec_from_file_location("pdf_isolation", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def rejects(value: object, reason: str) -> None:
    try:
        MODULE.evaluate(value)
    except MODULE.IsolationRejected as exc:
        assert str(exc) == reason, (str(exc), reason)
    else:
        raise AssertionError(f"accepted hostile evidence: {reason}")


def main() -> int:
    checks = 0
    for platform in ("windows", "linux", "macos"):
        value = MODULE.template(platform, f"{platform}-fixture")
        result = MODULE.evaluate(value)
        assert result["isolationAdmissionPassed"] is False
        assert result["runtimeAdmissionGranted"] is False
        assert result["nativePlatformEvidence"] is True
        assert len(result["missingControls"]) == 5
        checks += 3

        passing = copy.deepcopy(value)
        for control in passing["controls"]:
            for field in (
                "available",
                "implemented",
                "enforcementTestPassed",
                "hostileEscapeTestPassed",
            ):
                control[field] = True
        passing["sourcePackageParityPassed"] = True
        passed = MODULE.evaluate(passing)
        assert passed["isolationAdmissionPassed"] is True
        assert passed["runtimeAdmissionGranted"] is False
        checks += 2

        missing = copy.deepcopy(passing)
        missing["controls"].pop()
        rejects(missing, "controls-count")
        duplicate = copy.deepcopy(passing)
        duplicate["controls"][-1]["id"] = duplicate["controls"][0]["id"]
        rejects(duplicate, "control-duplicate")
        forged = copy.deepcopy(passing)
        forged["controls"][0]["implemented"] = "true"
        rejects(forged, "control-boolean")
        no_parity = copy.deepcopy(passing)
        no_parity["sourcePackageParityPassed"] = False
        assert MODULE.evaluate(no_parity)["isolationAdmissionPassed"] is False
        checks += 4

    rejects({}, "evidence-shape")
    wrong = MODULE.template("windows", "fixture")
    wrong["schemaVersion"] = 1
    rejects(wrong, "evidence-schema")
    wrong = MODULE.template("windows", "fixture")
    wrong["platform"] = "other"
    rejects(wrong, "platform-unsupported")
    wsl = MODULE.template("linux", "wsl2-fixture", "wsl2")
    for control in wsl["controls"]:
        for field in (
            "available", "implemented", "enforcementTestPassed",
            "hostileEscapeTestPassed",
        ):
            control[field] = True
    wsl["sourcePackageParityPassed"] = True
    wsl_result = MODULE.evaluate(wsl)
    assert wsl_result["isolationAdmissionPassed"] is False
    assert wsl_result["nativePlatformEvidence"] is False
    assert wsl_result["environmentLimitations"] == [
        "wsl2-is-not-native-linux-evidence"
    ]
    wrong_kind = MODULE.template("windows", "fixture")
    wrong_kind["environmentKind"] = "wsl2"
    rejects(wrong_kind, "environment-kind")
    checks += 7

    contract = MODULE.CONTRACT
    assert contract["fallbackAllowed"] is False
    assert not any(contract["authority"].values())
    assert contract["evidenceRequirements"]["nativeEnvironmentRequired"] is True
    checks += 3
    print(f"PDF OS-isolation gate passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
