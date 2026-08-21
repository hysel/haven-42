#!/usr/bin/env python3
"""Summarize an exact-source native macOS Full-test receipt without raw logs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"
PASS_LINE = re.compile(
    r"^Test run passed\. Tier=full; ([1-9][0-9]*) tests executed; "
    r"(0|[1-9][0-9]*) skipped; ([1-9][0-9]*) seconds\.$"
)
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class NativeTestSummaryError(ValueError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise NativeTestSummaryError("module-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_pass(log_text: str) -> dict[str, int]:
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    if not lines or any(line.startswith("FAIL ") for line in lines):
        raise NativeTestSummaryError("native-test-log-not-passed")
    match = PASS_LINE.fullmatch(lines[-1])
    if not match:
        raise NativeTestSummaryError("native-test-pass-receipt-missing")
    executed, skipped, duration = (int(value) for value in match.groups())
    if executed < 80 or skipped != 0:
        raise NativeTestSummaryError("native-test-coverage-incomplete")
    return {"groupsExecuted": executed, "groupsSkipped": skipped, "durationSeconds": duration}


def build_report(
    plan: dict[str, Any], plan_sha256: str, host: dict[str, Any], source_sha256: str,
    base_commit: str, measurements: dict[str, int],
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-native-test-result",
        "release": plan["release"],
        "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "passed",
        "planCanonicalSha256": plan_sha256,
        "hardwareProfile": host | {"profileId": plan["hardwareProfile"]["id"]},
        "source": {
            "baseCommit": base_commit,
            "treeState": "modified-uncommitted",
            "commitIsExactSource": False,
            "snapshotSha256": source_sha256,
        },
        "test": {"tier": "full", "runner": "native-shell", **measurements},
        "rawLogRetained": False,
        "privateIdentityRetained": False,
        "privatePathsRetained": False,
        "releasePublicationAuthorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--source-archive", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runner = load_module("mac_qualification_runner", RUNNER_PATH)
    try:
        if not COMMIT.fullmatch(args.base_commit):
            raise NativeTestSummaryError("invalid-base-commit")
        for path in (args.log, args.source_archive):
            if not path.is_file() or path.is_symlink():
                raise NativeTestSummaryError("required-input-unavailable")
        plan = runner.load_json(args.plan)
        runner.validate_plan(plan, ROOT)
        host = runner.host_preflight(plan)
        measurements = parse_pass(args.log.read_text(encoding="utf-8"))
        report = build_report(
            plan, runner.canonical_sha256(plan), host,
            sha256_file(args.source_archive), args.base_commit, measurements,
        )
        encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name + ".tmp")
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, args.output)
        print("Native macOS Full-test result summarized.")
        return 0
    except (NativeTestSummaryError, runner.QualificationError, OSError, UnicodeError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
