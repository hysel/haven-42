#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load("coding_history", "scripts/model-coding-agent-history-audit.py")
TEMPLATE = load("coding_template", "scripts/model-coding-agent-cell-template.py")
SCREEN = TEMPLATE.SCREEN


class CodingAgentHistoryAuditTests(unittest.TestCase):
    @classmethod
    def legacy(cls) -> dict:
        return json.loads((ROOT / "config/model-coding-agent-qualification-result.json").read_text(encoding="utf-8"))

    def test_history_is_retained_without_current_recommendation(self) -> None:
        result = AUDIT.audit(self.legacy())
        self.assertEqual(result["modelCount"], 18)
        self.assertEqual(result["codingRecommendationCount"], 0)
        self.assertTrue(all(not row["currentCodingRecommendationEligible"] for row in result["models"]))

    def test_summary_drift_and_forbidden_authority_fail_closed(self) -> None:
        drift = copy.deepcopy(self.legacy())
        drift["workflowScreenPassed"] = []
        with self.assertRaisesRegex(ValueError, "summary does not match"):
            AUDIT.audit(drift)
        authority = copy.deepcopy(self.legacy())
        authority["automaticDefaultChangeAllowed"] = True
        with self.assertRaisesRegex(ValueError, "forbidden automatic authority"):
            AUDIT.audit(authority)

    def test_template_is_complete_not_run_and_validator_blocked(self) -> None:
        cell = TEMPLATE.build(
            "fixture-model", "1" * 64, "ollama", "fixture", "2" * 64,
            "fixture-gpu", "vscode-native-chat", "fixture",
        )
        result = SCREEN.evaluate(cell)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["codingRecommendationEligible"])
        self.assertTrue(all(gate["status"] == "not-run" for gate in cell["gates"].values()))


if __name__ == "__main__":
    unittest.main()
