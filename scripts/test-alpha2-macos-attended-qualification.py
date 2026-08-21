#!/usr/bin/env python3
"""Tests for the attended macOS qualification collector."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("attended", ROOT / "scripts/alpha2-macos-attended-qualification.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
PLAN_PATH = ROOT / "config/alpha-2-macos-attended-qualification-plan.json"


class AttendedQualificationTests(unittest.TestCase):
    def test_all_pass_is_sanitized_and_passed(self) -> None:
        plan = MODULE.load_plan(PLAN_PATH)
        answers = iter(["p"] * len(plan["gates"]))
        with patch.object(sys, "platform", "darwin"):
            result = MODULE.collect(
                plan,
                artifact_sha256="a" * 64,
                source_commit="b" * 40,
                input_fn=lambda _prompt: next(answers),
                output_fn=lambda _message: None,
            )
        self.assertEqual(result["status"], "passed")
        self.assertTrue(all(gate == {"status": "passed", "reasonCode": "verified-as-instructed"} for gate in result["gates"].values()))
        self.assertNotIn("instruction", json.dumps(result))
        self.assertFalse(any(result["privacy"].values()))
        self.assertFalse(any(result["authority"].values()))

    def test_nonpass_remains_visible(self) -> None:
        plan = MODULE.load_plan(PLAN_PATH)
        answers = iter(["x", "f", "b", "n"] + ["p"] * (len(plan["gates"]) - 3))
        with patch.object(sys, "platform", "darwin"):
            result = MODULE.collect(
                plan,
                artifact_sha256="c" * 64,
                source_commit="d" * 40,
                input_fn=lambda _prompt: next(answers),
                output_fn=lambda _message: None,
            )
        self.assertEqual(result["status"], "failed")
        statuses = [gate["status"] for gate in result["gates"].values()]
        self.assertEqual(statuses[:3], ["failed", "blocked", "not-run"])

    def test_refuses_non_macos_and_bad_bindings(self) -> None:
        plan = MODULE.load_plan(PLAN_PATH)
        with patch.object(sys, "platform", "win32"):
            with self.assertRaisesRegex(MODULE.AttendedQualificationError, "physical-macos-required"):
                MODULE.collect(plan, artifact_sha256="a" * 64, source_commit="b" * 40)
        with patch.object(sys, "platform", "darwin"):
            with self.assertRaisesRegex(MODULE.AttendedQualificationError, "evidence-binding-invalid"):
                MODULE.collect(plan, artifact_sha256="bad", source_commit="bad")

    def test_atomic_writer_leaves_only_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            MODULE.write_atomic(output, {"safe": True})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"safe": True})
            self.assertFalse(output.with_name("result.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
