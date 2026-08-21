#!/usr/bin/env python3
"""Build the fail-closed Apple M4 qualification ledger from validated evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


class SummaryError(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SummaryError(f"invalid-json:{path.name}") from error
    if not isinstance(value, dict):
        raise SummaryError(f"invalid-object:{path.name}")
    return value


def run_validator(*arguments: str) -> None:
    process = subprocess.run(
        [sys.executable, *arguments], capture_output=True, text=True,
        cwd=ROOT, timeout=120, shell=False,
    )
    if process.returncode != 0:
        raise SummaryError(f"evidence-validation-failed:{Path(arguments[0]).name}")


def relative_binding(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise SummaryError("evidence-outside-repository") from error
    return {
        "path": relative.as_posix(),
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
    }


def count(records: object, status: str) -> int:
    if not isinstance(records, list):
        raise SummaryError("result-records-invalid")
    return sum(isinstance(record, dict) and record.get("status") == status for record in records)


def build_status(values: dict[str, dict[str, Any]], bindings: list[dict[str, str]]) -> dict[str, Any]:
    core, soak, coding = values["core"], values["soak"], values["coding"]
    addendum_core = values.get("addendum_core")
    addendum_soak = values.get("addendum_soak")
    addendum_coding = values.get("addendum_coding")
    addendum_present = all(value is not None for value in (addendum_core, addendum_soak, addendum_coding))
    package, keychain = values["package"], values["keychain"]
    native_tests = values["native_tests"]
    power = [
        values[name]
        for name in ("idle_power", "small_power", "medium_power", "large_power")
    ]
    if native_tests.get("status") != "passed":
        raise SummaryError("native-tests-not-passed")
    native_receipt = native_tests.get("test")
    if not isinstance(native_receipt, dict) or native_receipt.get("tier") != "full" or native_receipt.get("runner") != "native-shell" or not isinstance(native_receipt.get("groupsExecuted"), int) or native_receipt["groupsExecuted"] < 80 or native_receipt.get("groupsSkipped") != 0:
        raise SummaryError("native-test-receipt-invalid")
    if count(core.get("results"), "passed") + count(core.get("results"), "failed") != 16:
        raise SummaryError("core-result-count-invalid")
    if count(soak.get("results"), "passed") + count(soak.get("results"), "failed") != 9:
        raise SummaryError("soak-result-count-invalid")
    if count(coding.get("results"), "passed") + count(coding.get("results"), "failed") != 16:
        raise SummaryError("coding-result-count-invalid")
    if addendum_present:
        if count(addendum_core.get("results"), "passed") + count(addendum_core.get("results"), "failed") != 1:
            raise SummaryError("addendum-core-result-count-invalid")
        expected_addendum_soaks = count(addendum_core.get("results"), "passed")
        if count(addendum_soak.get("results"), "passed") + count(addendum_soak.get("results"), "failed") != expected_addendum_soaks:
            raise SummaryError("addendum-soak-result-count-invalid")
        if count(addendum_coding.get("results"), "passed") + count(addendum_coding.get("results"), "failed") != 1:
            raise SummaryError("addendum-coding-result-count-invalid")
    if any(value.get("status") != "passed" for value in power):
        raise SummaryError("power-cell-not-passed")
    tests = package.get("tests", {})
    if (
        tests.get("packagedBrowserFlow") is not True
        or tests.get("boundedAttachmentFlow") is not True
        or tests.get("automatedAccessibilityFlow") is not True
        or tests.get("localPrivacyBoundary") is not True
        or not isinstance(tests.get("packagedBrowserChecks"), int)
        or tests["packagedBrowserChecks"] < 1
    ):
        raise SummaryError("packaged-browser-evidence-invalid")
    coding_records = coding["results"]
    all_coding_records = coding_records + (addendum_coding["results"] if addendum_present else [])
    eligible = sum(record.get("codingRecommendationEligible") is True for record in all_coding_records)
    core_candidates = 16 + (1 if addendum_present else 0)
    core_passed = count(core["results"], "passed") + (count(addendum_core["results"], "passed") if addendum_present else 0)
    core_failed = count(core["results"], "failed") + (count(addendum_core["results"], "failed") if addendum_present else 0)
    soak_candidates = 9 + (len(addendum_soak["results"]) if addendum_present else 0)
    soak_passed = count(soak["results"], "passed") + (count(addendum_soak["results"], "passed") if addendum_present else 0)
    soak_failed = count(soak["results"], "failed") + (count(addendum_soak["results"], "failed") if addendum_present else 0)
    coding_candidates = 16 + (1 if addendum_present else 0)
    coding_passed = count(coding_records, "passed") + (count(addendum_coding["results"], "passed") if addendum_present else 0)
    coding_failed = count(coding_records, "failed") + (count(addendum_coding["results"], "failed") if addendum_present else 0)
    return {
        "schemaVersion": 1,
        "kind": "haven42-apple-m4-qualification-status",
        "release": "0.4.0-alpha.2",
        "profileId": "apple-m4-16gib-macos26-metal",
        "status": "in-progress",
        "complete": False,
        "evidenceBindings": bindings,
        "gates": {
            "nativeRepositoryTests": {"status": "passed", "scope": "exact source snapshot full test tier", "checksPassed": native_receipt["groupsExecuted"], "sourceSnapshotSha256": native_tests["source"]["snapshotSha256"]},
            "noviceSelfContainedPackage": {
                "status": "partial-pass",
                "passed": ["native-arm64", "embedded-python", "source-package-parity", "relocation", "read-only-startup", "abrupt-exit-recovery", "repeated-lifecycle", "occupied-port-refusal", "shutdown-authority", "hostile-environment", "resource-integrity", "packaged-real-browser-flow"],
                "open": list(package["open"]),
            },
            "ollamaLifecycle": {"status": "passed", "runtimeVersion": core["runtime"]["version"], "transport": core["runtime"]["transport"], "boundary": "model qualification, bounded lifecycle, and long-run reliability"},
            "llamaCppLifecycle": {"status": "partial-pass", "runtimeVersion": values["llamacpp"]["runtime"]["commit"], "passed": ["native-arm64", "metal-full-offload", "authenticated-loopback", "bounded-inference", "timeout-recovery", "restart", "listener-cleanup"], "open": ["trusted-distribution", "self-contained-package", "maintained-coding-surface"]},
            "mlxLifecycle": {"status": "partial-pass", "runtimeVersion": values["mlx"]["runtime"]["packages"]["mlx-lm"], "passed": ["pinned-offline-runtime", "native-metal-generation", "timeout-recovery", "process-cleanup"], "open": ["production-suitable-server", "authenticated-boundary", "self-contained-package", "maintained-coding-surface"]},
            "modelCoreQualification": {"status": "partial-pass", "candidates": core_candidates, "passed": core_passed, "failed": core_failed},
            "longRunReliability": {"status": "completed", "eligibleCandidates": soak_candidates, "passed": soak_passed, "failed": soak_failed, "minutesPerCandidate": 30},
            "codingAgentQualification": {"status": "completed", "surface": "opencode-cli", "surfaceVersion": coding["surface"]["version"], "candidates": coding_candidates, "passed": coding_passed, "failed": coding_failed, "eligibleForHumanReview": eligible, "continueEvidenceAccepted": False},
            "powerAndThermals": {"status": "partial-pass", "passed": ["idle-baseline", "representative-small-model", "representative-medium-model", "representative-large-model", "gpu-and-ane-estimates", "thermal-pressure"], "open": ["whole-system-wall-power"]},
            "uiAccessibilityAndAttachments": {"status": "partial-pass", "passed": ["automated-source-package-parity", "packaged-real-browser-flow", "bounded-attachment-flow", "automated-accessibility-flow", "local-privacy-boundary"], "packagedBrowserChecks": tests["packagedBrowserChecks"], "open": ["manual-screen-reader", "manual-keyboard", "manual-zoom", "manual-reduced-motion", "physical-clipboard"]},
            "keychain": {"status": keychain["status"], "passed": [] if keychain["status"] != "passed" else ["synthetic-item-lifecycle"], "blocked": [keychain["errorCode"]] if keychain["status"] == "blocked" else [], "open": ["interactive-packaged-item-lifecycle", "locked-denied-recovery", "encrypted-history-integration"]},
            "updateRollbackAndUninstall": {"status": "blocked", "passed": ["offline-policy-and-lifecycle-simulation"], "open": ["signed-native-install", "side-by-side-update", "health-gated-activation", "automatic-rollback", "marker-owned-uninstall", "user-data-preservation"], "reason": "The physical artifact is an unsigned development archive; simulations do not prove a native package transition."},
        },
        "authority": {"automaticDefaultChangeAllowed": False, "automaticSelectionAllowed": False, "supportLabelChangeAllowed": False, "runtimePromotionAllowed": False, "releasePromotionAllowed": False, "automaticUpdateActivationAllowed": False},
        "privacy": {"privateIdentityRetained": False, "privateInfrastructureRetained": False, "rawPromptsOrResponsesRetained": False, "rawTelemetryRetained": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "core", "soak", "coding", "coding-policy", "native-tests", "idle-power", "small-power", "medium-power", "large-power", "package", "keychain", "mlx", "llamacpp"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("addendum-plan", "addendum-core", "addendum-soak", "addendum-coding"):
        parser.add_argument(f"--{name}", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    paths = {name.replace("-", "_"): getattr(args, name.replace("-", "_")) for name in ("plan", "core", "soak", "coding", "coding-policy", "native-tests", "idle-power", "small-power", "medium-power", "large-power", "package", "keychain", "mlx", "llamacpp")}
    addendum_paths = {
        name.replace("-", "_"): getattr(args, name.replace("-", "_"))
        for name in ("addendum-plan", "addendum-core", "addendum-soak", "addendum-coding")
    }
    if any(addendum_paths.values()) and not all(addendum_paths.values()):
        parser.error("addendum-evidence-must-be-complete")
    if all(addendum_paths.values()):
        paths.update(addendum_paths)
    for path in paths.values():
        if not path.is_file() or path.is_symlink():
            parser.error("evidence-file-unavailable")
    validators = ROOT / "scripts"
    run_validator(str(validators / "validate-alpha2-macos-model-qualification-result.py"), str(paths["core"]), "--plan", str(paths["plan"]))
    run_validator(str(validators / "validate-alpha2-macos-model-soak-result.py"), str(paths["soak"]), "--qualification-result", str(paths["core"]), "--plan", str(paths["plan"]))
    run_validator(str(validators / "validate-alpha2-macos-opencode-coding-result.py"), str(paths["coding"]), "--qualification-result", str(paths["core"]), "--plan", str(paths["plan"]), "--policy", str(paths["coding_policy"]))
    if "addendum_plan" in paths:
        run_validator(str(validators / "validate-alpha2-macos-model-qualification-result.py"), str(paths["addendum_core"]), "--plan", str(paths["addendum_plan"]))
        run_validator(str(validators / "validate-alpha2-macos-model-soak-result.py"), str(paths["addendum_soak"]), "--qualification-result", str(paths["addendum_core"]), "--plan", str(paths["addendum_plan"]))
        run_validator(str(validators / "validate-alpha2-macos-opencode-coding-result.py"), str(paths["addendum_coding"]), "--qualification-result", str(paths["addendum_core"]), "--plan", str(paths["addendum_plan"]), "--policy", str(paths["coding_policy"]))
    run_validator(str(validators / "validate-alpha2-macos-native-test-result.py"), str(paths["native_tests"]), "--plan", str(paths["plan"]))
    for name in ("idle_power", "small_power", "medium_power", "large_power"):
        run_validator(str(validators / "validate-alpha2-macos-power-result.py"), str(paths[name]), "--plan", str(paths["plan"]))
    run_validator(str(validators / "validate-alpha2-macos-development-app-result.py"), str(paths["package"]))
    run_validator(str(validators / "validate-alpha2-macos-keychain-lifecycle-result.py"), str(paths["keychain"]))
    run_validator(str(validators / "validate-alpha2-macos-mlx-lifecycle-result.py"), str(paths["mlx"]))
    run_validator(str(validators / "validate-alpha2-macos-llamacpp-lifecycle-result.py"), str(paths["llamacpp"]))
    values = {name: load(path) for name, path in paths.items() if name not in {"plan", "addendum_plan", "coding_policy"}}
    bindings = [relative_binding(path) for path in paths.values()]
    status = build_status(values, bindings)
    encoded = json.dumps(status, indent=2, sort_keys=True) + "\n"
    private_pattern = r"(?:" + re.escape("/" + "Users/") + r"|192\.168\.|BEGIN [A-Z ]+KEY)"
    if re.search(private_pattern, encoded, re.IGNORECASE):
        parser.error("private-data-detected")
    output = args.output.resolve()
    if output.exists() and not args.replace:
        parser.error("output-exists-use-replace")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, output)
    print(f"Apple M4 qualification ledger written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
