#!/usr/bin/env python3
"""Tests for sanitized exact-source native Apple M4 Full-test evidence."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUMMARY = load("native_test_summary", ROOT / "scripts/summarize-alpha2-macos-native-test-result.py")
VALIDATOR = load("native_test_validator", ROOT / "scripts/validate-alpha2-macos-native-test-result.py")
PLAN = json.loads((ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json").read_text(encoding="utf-8"))


def result() -> dict:
    return SUMMARY.build_report(
        PLAN,
        VALIDATOR.canonical_sha256(PLAN),
        {"platformFamily": "macos", "architecture": "arm64", "backend": "metal", "systemMemoryGiB": 16.0},
        "b" * 64,
        "a" * 40,
        {"groupsExecuted": 80, "groupsSkipped": 0, "durationSeconds": 900},
    )


class NativeTestResultTests(unittest.TestCase):
    def test_exact_pass_line_and_result_validate(self) -> None:
        measurements = SUMMARY.parse_pass(
            "PASS one\nTest run passed. Tier=full; 80 tests executed; 0 skipped; 900 seconds.\n"
        )
        self.assertEqual(measurements["groupsExecuted"], 80)
        VALIDATOR.validate(result(), PLAN)

    def test_failed_incomplete_or_nonfinal_logs_are_rejected(self) -> None:
        for text in (
            "FAIL one\nTest run passed. Tier=full; 80 tests executed; 0 skipped; 900 seconds.\n",
            "Test run passed. Tier=full; 79 tests executed; 0 skipped; 900 seconds.\n",
            "Test run passed. Tier=full; 80 tests executed; 1 skipped; 900 seconds.\n",
            "Test run failed. Tier=full; 80 tests executed; 0 skipped; 900 seconds.\n",
        ):
            with self.assertRaises(SUMMARY.NativeTestSummaryError):
                SUMMARY.parse_pass(text)

    def test_source_privacy_and_authority_fail_closed(self) -> None:
        mutations = (
            lambda value: value["source"].__setitem__("snapshotSha256", "bad"),
            lambda value: value["test"].__setitem__("groupsSkipped", 1),
            lambda value: value.__setitem__("privatePathsRetained", True),
            lambda value: value["source"].__setitem__("treeState", "/Users/private"),
            lambda value: value.__setitem__("releasePublicationAuthorized", True),
        )
        for mutation in mutations:
            value = copy.deepcopy(result())
            mutation(value)
            with self.assertRaises(VALIDATOR.NativeTestResultError):
                VALIDATOR.validate(value, PLAN)


if __name__ == "__main__":
    unittest.main()
