#!/usr/bin/env python3
"""Hostile tests for the effect-free offline installer lifecycle model."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "simulate-offline-installer-lifecycle.py"
SPEC = importlib.util.spec_from_file_location("offline_installer", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASE = json.loads(
    (ROOT / "examples/fixtures/offline-installer-lifecycle-request.json").read_text(encoding="utf-8")
)


def rejected(mutator, expected: str) -> None:
    value = copy.deepcopy(BASE)
    mutator(value)
    try:
        MODULE.evaluate(value)
    except MODULE.InstallerLifecycleError as error:
        if expected not in str(error):
            raise AssertionError(f"expected {expected}, received {error}") from error
    else:
        raise AssertionError(f"unsafe request accepted: {expected}")


def uninstall_request() -> dict:
    value = copy.deepcopy(BASE)
    value["operation"] = "uninstall"
    value["artifact"]["version"] = "0.2.0-development"
    value["uninstallFiles"] = [{
        "relativeSegments": ["versions", "0.2.0-development", "haven42.exe"],
        "sha256": "c" * 64,
        "ownedByTransaction": True,
    }]
    return value


def main() -> int:
    checks = 0
    result = MODULE.evaluate(copy.deepcopy(BASE))
    if (
        result["status"] != "update-plan"
        or result["runtimeAdmitted"]
        or result["executionAllowed"]
        or any(result["machineEffects"].values())
        or result["artifactRegistryDecision"] != "deny"
    ):
        raise AssertionError("valid simulation granted authority or reported wrong state")
    checks += 1

    install = copy.deepcopy(BASE)
    install["operation"] = "install"
    install["currentState"]["installedVersions"] = []
    install["currentState"]["activeVersion"] = None
    if MODULE.evaluate(install)["status"] != "install-plan":
        raise AssertionError("valid install was not planned")
    checks += 1

    rollback = copy.deepcopy(BASE)
    rollback["operation"] = "rollback"
    rollback["artifact"]["version"] = "0.2.0-development"
    if MODULE.evaluate(rollback)["status"] != "rollback-plan":
        raise AssertionError("valid rollback was not planned")
    checks += 1

    cleanup = copy.deepcopy(BASE)
    cleanup["operation"] = "cleanup"
    cleanup["artifact"]["version"] = "0.2.0-development"
    if MODULE.evaluate(cleanup)["status"] != "cleanup-plan":
        raise AssertionError("valid cleanup was not planned")
    checks += 1

    delete_choice = uninstall_request()
    delete_choice["userDataChoice"] = "delete"
    delete_result = MODULE.evaluate(delete_choice)
    if delete_result["machineEffects"]["userDataDeleted"]:
        raise AssertionError("explicit simulated delete performed an effect")
    checks += 1

    for phase in (
        "preflight", "staging", "verifying", "activating", "health-check",
        "committing", "cleaning",
    ):
        value = copy.deepcopy(BASE)
        value["interruption"] = phase
        interrupted = MODULE.evaluate(value)
        if not interrupted["recoveryRequired"] or interrupted["nextOperation"] != "recover":
            raise AssertionError(f"interruption was not recoverable: {phase}")
        checks += 1

    uninstall = MODULE.evaluate(uninstall_request())
    if uninstall["exactUninstallFileCount"] != 1 or uninstall["wouldRetainVersions"]:
        raise AssertionError("exact-file uninstall plan was incorrect")
    checks += 1

    cases = (
        (lambda value: value.update(extra=True), "invalid-request-shape"),
        (lambda value: value.update(transactionId="bad"), "invalid-transaction-id"),
        (lambda value: value["currentState"]["completedTransactionIds"].append(value["transactionId"]), "transaction-replay"),
        (lambda value: value["artifact"].update(version="0.1.0-development"), "downgrade-rejected"),
        (lambda value: value["artifact"].update(sha256="short"), "invalid-artifact-digest"),
        (lambda value: value["artifact"].update(licenseReviewed=False), "artifact-not-verified"),
        (lambda value: value["artifact"].update(platform="linux"), "artifact-platform-mismatch"),
        (lambda value: value["storage"].update(destinationAvailableBytes=1), "destination-space-insufficient"),
        (lambda value: value["storage"].update(temporaryAvailableBytes=1), "temporary-space-insufficient"),
        (lambda value: value["destination"].update(ownedByCurrentUser=False), "destination-permission-preflight-failed"),
        (lambda value: value["destination"]["relativeSegments"].__setitem__(0, ".."), "unsafe-path-segment"),
        (lambda value: value["destination"]["relativeSegments"].__setitem__(0, "NUL.txt"), "unsafe-path-segment"),
        (lambda value: value["destination"]["pathProof"].update(canonical=False), "path-not-canonical-or-contained"),
        (lambda value: value["destination"]["pathProof"].update(symlink=True), "unsafe-path-proof"),
        (lambda value: value["destination"]["pathProof"].update(junction=True), "unsafe-path-proof"),
        (lambda value: value["destination"]["pathProof"].update(reparsePoint=True), "unsafe-path-proof"),
        (lambda value: value["destination"]["pathProof"].update(mountEscape=True), "unsafe-path-proof"),
        (lambda value: value["destination"]["pathProof"].update(overlapsRepositoryRoot=True), "unsafe-path-proof"),
        (
            lambda value: value["currentState"]["installedVersions"].extend(
                ["0.1.0-development", "0.4.0-development"]
            ),
            "invalid-retained-versions",
        ),
        (lambda value: value.update(userDataChoice="delete"), "user-data-delete-outside-uninstall"),
        (lambda value: value.update(operation="recover"), "recover-requires-partial-state"),
    )
    for mutator, expected in cases:
        rejected(mutator, expected)
        checks += 1

    value = uninstall_request()
    value["uninstallFiles"] = []
    try:
        MODULE.evaluate(value)
    except MODULE.InstallerLifecycleError as error:
        if str(error) != "exact-uninstall-files-required":
            raise AssertionError(f"unexpected uninstall rejection: {error}") from error
        checks += 1
    else:
        raise AssertionError("broad empty uninstall was accepted")

    value = uninstall_request()
    value["uninstallFiles"][0]["ownedByTransaction"] = False
    try:
        MODULE.evaluate(value)
    except MODULE.InstallerLifecycleError as error:
        if str(error) != "unowned-uninstall-file":
            raise AssertionError(f"unexpected ownership rejection: {error}") from error
        checks += 1
    else:
        raise AssertionError("unowned uninstall file was accepted")

    entry = MODULE.append_journal(BASE["transactionId"], ["preflight"], "0" * 64, 1)[0]
    value = copy.deepcopy(BASE)
    value["journal"] = [entry]
    value["journal"][0]["previousDigest"] = "d" * 64
    try:
        MODULE.evaluate(value)
    except MODULE.InstallerLifecycleError as error:
        if str(error) != "journal-chain-broken":
            raise AssertionError(f"unexpected journal rejection: {error}") from error
        checks += 1
    else:
        raise AssertionError("broken journal was accepted")

    valid_entry = MODULE.append_journal(BASE["transactionId"], ["preflight"], "0" * 64, 1)[0]
    recovery = copy.deepcopy(BASE)
    recovery["operation"] = "recover"
    recovery["currentState"]["partialTransactionId"] = BASE["transactionId"]
    recovery["journal"] = [valid_entry]
    recovered = MODULE.evaluate(recovery)
    if recovered["status"] != "recover-plan":
        raise AssertionError("valid partial-state recovery was not planned")
    checks += 1

    if checks != 38:
        raise AssertionError(f"expected 38 checks, ran {checks}")
    print("Offline installer lifecycle hostile tests passed: 38 checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
