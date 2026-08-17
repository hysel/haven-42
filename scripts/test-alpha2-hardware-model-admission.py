#!/usr/bin/env python3
"""Tests for deterministic hardware-model admission evidence."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "alpha2-hardware-model-admission.py"
SPEC = importlib.util.spec_from_file_location("hardware_model_admission", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HardwareModelAdmissionTests(unittest.TestCase):
    def test_reviewed_oversized_models_are_refused_without_execution(self) -> None:
        for model_id in ("qwen35-9b-q4", "gemma3-12b-q4", "gemma4-12b-qat"):
            with self.subTest(model_id=model_id):
                result = MODULE.evaluate(model_id)
                self.assertEqual(result["tier"], "oversized-refusal")
                self.assertEqual(result["decision"], "refused-before-download")
                self.assertEqual(result["outcome"], "passed")
                self.assertFalse(result["downloadPerformed"])
                self.assertFalse(result["executionPerformed"])
                self.assertFalse(result["automaticPromotionAllowed"])

    def test_small_model_is_not_certified_by_size_alone(self) -> None:
        result = MODULE.evaluate("gemma3-1b-q4")
        self.assertEqual(result["tier"], "expected-fit")
        self.assertEqual(result["outcome"], "inconclusive")
        self.assertEqual(result["decision"], "requires-runtime-headroom-measurement")

    def test_unreviewed_model_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            MODULE.AdmissionError, "unreviewed-hardware-cell"
        ):
            MODULE.evaluate("qwen38-27b-q4")


if __name__ == "__main__":
    unittest.main()
