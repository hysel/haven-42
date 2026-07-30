#!/usr/bin/env python3
"""Exercise the offline restricted PDF worker against the synthetic corpus."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
HARNESS_PATH = ROOT / "scripts" / "run-restricted-pdf-worker.py"
SPEC = importlib.util.spec_from_file_location("restricted_pdf_harness", HARNESS_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


EXPECTED = {
    "associated-file.pdf": "embedded-content-rejected",
    "compressed-expansion.pdf": "expansion-budget-exceeded",
    "embedded-file.pdf": "embedded-content-rejected",
    "encrypted-standard.pdf": "encrypted-content-rejected",
    "excessive-page-count.pdf": "page-budget-exceeded",
    "external-uri.pdf": "external-reference-rejected",
    "javascript-name-tree.pdf": "active-content-rejected",
    "launch-action.pdf": "active-content-rejected",
    "malformed-xref.pdf": "malformed-pdf-rejected",
    "open-action.pdf": "active-content-rejected",
    "recursive-object.pdf": "recursive-object-rejected",
    "submit-form-action.pdf": "active-content-rejected",
    "truncated-eof.pdf": "malformed-pdf-rejected",
}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    contract = MODULE.load_json(MODULE.CONTRACT_PATH)
    checks = 0

    assert contract["status"] == "offline-security-prototype-not-runtime-admitted"
    assert contract["reviewAuthority"]["parserImportForReviewAllowed"] is True
    assert contract["reviewAuthority"]["workerProcessForReviewAllowed"] is True
    assert contract["reviewAuthority"]["runtimeRouteAllowed"] is False
    assert contract["reviewAuthority"]["uiControlAllowed"] is False
    assert contract["reviewAuthority"]["userDocumentAllowed"] is False
    assert contract["reviewAuthority"]["dependencyAdmissionGranted"] is False
    assert contract["containment"]["productionGradeIsolationClaimed"] is False
    assert contract["containment"]["windowsJobCpuMemoryProcessLimitsRequired"] is True
    assert contract["containment"]["windowsSuspendedAssignmentRequired"] is True
    assert contract["containment"]["windowsOsMemoryLimitImplemented"] is True
    assert contract["containment"]["parentStreamingOutputLimitsRequired"] is True
    assert contract["containment"]["boundedDirectResidueSnapshotRequired"] is True
    checks += 13

    safe = MODULE.run_worker(MODULE.fixture_bytes("safe-text-only.pdf"))
    assert safe["status"] == "candidate-output"
    assert safe["text"].strip() == "Haven 42 fixture"
    assert safe["pageCount"] == 1
    assert safe["objectCount"] == 5
    assert safe["expandedBytes"] > 0
    assert not any(safe["effects"].values())
    checks += 6

    for filename, expected_reason in EXPECTED.items():
        result = MODULE.run_worker(MODULE.fixture_bytes(filename))
        assert result == {
            "schemaVersion": 1,
            "status": "rejected",
            "reason": expected_reason,
            "runtimeAdmissionGranted": False,
        }, (filename, result)
        checks += 1

    timeout = MODULE.lifecycle_probe("--self-test-hang", 0.25)
    assert timeout["forcedTermination"] is True
    assert timeout["residueDetected"] is False
    assert timeout["stdoutBytes"] == 0
    assert timeout["stderrBytes"] == 0
    checks += 4

    crash = MODULE.lifecycle_probe("--self-test-crash", 2)
    assert crash["returncode"] == 23
    assert crash["forcedTermination"] is False
    assert crash["residueDetected"] is False
    assert crash["stdoutBytes"] == 0
    assert crash["stderrBytes"] == 0
    checks += 5

    for argument, reason in (
        ("--self-test-stdout-flood", "worker-stdout-too-large"),
        ("--self-test-stderr-flood", "worker-stderr-too-large"),
    ):
        try:
            MODULE.lifecycle_probe(argument, 2)
        except MODULE.WorkerHarnessError as error:
            assert str(error) == reason
            checks += 1
        else:
            raise AssertionError(f"{argument} was not bounded")

    effects = MODULE.effect_guard_probe()
    assert all(effects["denied"].values())
    assert effects["runtimeAdmissionGranted"] is False
    checks += 7

    try:
        MODULE.fixture_bytes("../safe-text-only.pdf")
    except MODULE.WorkerHarnessError as error:
        assert str(error) == "fixture-not-allowlisted"
        checks += 1
    else:
        raise AssertionError("arbitrary fixture path was accepted")

    try:
        MODULE.validate_wheel(ROOT / "README.md", contract, MODULE.load_json(MODULE.ARTIFACT_LOCK_PATH))
    except MODULE.WorkerHarnessError as error:
        assert str(error) == "artifact-path-rejected"
        checks += 1
    else:
        raise AssertionError("arbitrary artifact path was accepted")

    with tempfile.TemporaryDirectory(prefix="haven42-pdf-snapshot-") as temporary:
        snapshot_root = Path(temporary)
        (snapshot_root / "safe.txt").write_text("safe", encoding="utf-8")
        assert MODULE.directory_snapshot(snapshot_root) == {
            "safe.txt": (4, hashlib.sha256(b"safe").hexdigest())
        }
        checks += 1
        (snapshot_root / "nested").mkdir()
        try:
            MODULE.directory_snapshot(snapshot_root)
        except MODULE.WorkerHarnessError as error:
            assert str(error) == "snapshot-entry-rejected"
            checks += 1
        else:
            raise AssertionError("snapshot traversal entry was accepted")

    with tempfile.TemporaryDirectory(prefix="haven42-pdf-entry-budget-") as temporary:
        snapshot_root = Path(temporary)
        for index in range(65):
            (snapshot_root / f"{index:02d}.txt").write_text("", encoding="utf-8")
        try:
            MODULE.directory_snapshot(snapshot_root)
        except MODULE.WorkerHarnessError as error:
            assert str(error) == "snapshot-entry-budget-exceeded"
            checks += 1
        else:
            raise AssertionError("snapshot entry budget was not enforced")

    runtime_imports = set()
    for path in (ROOT / "web").rglob("*.py"):
        runtime_imports.update(imported_roots(path))
        content = path.read_text(encoding="utf-8")
        assert "restricted-pdf-worker" not in content
        assert "run-restricted-pdf-worker" not in content
    assert "pypdf" not in runtime_imports
    checks += 3

    artifact_lock = MODULE.load_json(MODULE.ARTIFACT_LOCK_PATH)
    assert artifact_lock["admission"]["dependencyAdmitted"] is False
    assert artifact_lock["admission"]["installAllowed"] is False
    assert artifact_lock["admission"]["runtimeRouteAllowed"] is False
    checks += 3

    print(f"Restricted PDF worker prototype passed {checks} security checks across 14 fixtures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
