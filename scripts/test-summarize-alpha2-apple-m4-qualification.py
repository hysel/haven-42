#!/usr/bin/env python3
"""Tests for deterministic Apple M4 qualification ledger aggregation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "summarize-alpha2-apple-m4-qualification.py"
SPEC = importlib.util.spec_from_file_location("m4_status", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def records(passed: int, failed: int, *, coding: bool = False) -> list[dict]:
    values = [{"status": "passed"} for _ in range(passed)] + [{"status": "failed"} for _ in range(failed)]
    if coding:
        for index, value in enumerate(values):
            value["codingRecommendationEligible"] = value["status"] == "passed" and index != 0
    return values


def fixture() -> dict:
    tests = {
        "packagedBrowserFlow": True,
        "boundedAttachmentFlow": True,
        "automatedAccessibilityFlow": True,
        "localPrivacyBoundary": True,
        "packagedBrowserChecks": 61,
    }
    return {
        "core": {"runtime": {"version": "0.32.15", "transport": "ipv4-loopback-only"}, "results": records(9, 7)},
        "soak": {"results": records(9, 0)},
        "coding": {"surface": {"version": "1.18.19"}, "results": records(5, 11, coding=True)},
        "native_tests": {"status": "passed", "source": {"snapshotSha256": "c" * 64}, "test": {"tier": "full", "runner": "native-shell", "groupsExecuted": 80, "groupsSkipped": 0}},
        "idle_power": {"status": "passed"},
        "small_power": {"status": "passed"},
        "medium_power": {"status": "passed"},
        "large_power": {"status": "passed"},
        "package": {"tests": tests, "open": ["developer-id-signing", "notarization", "gatekeeper-public-admission", "clean-machine-beginner-review", "manual-screen-reader", "manual-keyboard", "manual-zoom", "manual-reduced-motion"]},
        "keychain": {"status": "blocked", "errorCode": "interactive-authorization-required"},
        "mlx": {"runtime": {"packages": {"mlx-lm": "0.31.3"}}},
        "llamacpp": {"runtime": {"commit": "cd644c395"}},
        "development_update": {
            "status": "partial-pass",
            "operations": {
                operation: True
                for operation in MODULE.DEVELOPMENT_UPDATE_OPERATIONS
            },
            "platformTrust": {
                "developerIdSigned": False,
                "notarized": False,
                "gatekeeperPublicAdmission": False,
            },
            "authority": {
                "productionUpdaterAdmissionGranted": False,
                "automaticUpdateAdmissionGranted": False,
                "releasePromotionGranted": False,
            },
        },
    }


def main() -> int:
    checks = 0
    status = MODULE.build_status(fixture(), [{"path": "config/example.json", "sha256": "a" * 64}])
    assert status["status"] == "in-progress" and status["complete"] is False
    assert status["gates"]["longRunReliability"]["passed"] == 9
    assert status["gates"]["codingAgentQualification"]["eligibleForHumanReview"] == 4
    assert status["gates"]["uiAccessibilityAndAttachments"]["packagedBrowserChecks"] == 61
    assert status["gates"]["keychain"]["status"] == "blocked"
    assert status["gates"]["updateRollbackAndUninstall"]["status"] == "partial-pass"
    assert "production-updater-integration" in status["gates"]["updateRollbackAndUninstall"]["open"]
    assert all(value is False for value in status["authority"].values())
    checks += 8
    addendum = fixture()
    addendum["addendum_core"] = {"results": records(1, 0)}
    addendum["addendum_soak"] = {"results": records(1, 0)}
    addendum["addendum_coding"] = {"results": records(1, 0, coding=True)}
    expanded = MODULE.build_status(addendum, [])
    assert expanded["gates"]["modelCoreQualification"] == {
        "status": "partial-pass", "candidates": 17, "passed": 10, "failed": 7,
    }
    assert expanded["gates"]["longRunReliability"]["eligibleCandidates"] == 10
    assert expanded["gates"]["codingAgentQualification"]["candidates"] == 17
    checks += 3
    for mutation in (
        lambda value: value["soak"].__setitem__("results", records(8, 0)),
        lambda value: value["coding"].__setitem__("results", records(5, 10, coding=True)),
        lambda value: value["native_tests"]["test"].__setitem__("groupsSkipped", 1),
        lambda value: value["small_power"].__setitem__("status", "failed"),
        lambda value: value["medium_power"].__setitem__("status", "failed"),
        lambda value: value["package"]["tests"].__setitem__("packagedBrowserFlow", False),
        lambda value: value["development_update"]["operations"].__setitem__("automatic-baseline-rollback", False),
        lambda value: value["development_update"]["authority"].__setitem__("productionUpdaterAdmissionGranted", True),
    ):
        candidate = fixture()
        mutation(candidate)
        try:
            MODULE.build_status(candidate, [])
        except MODULE.SummaryError:
            checks += 1
        else:
            raise AssertionError("Incomplete M4 evidence was summarized as usable.")
    print(f"Apple M4 qualification ledger summary tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
