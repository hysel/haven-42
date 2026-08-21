#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("summary", ROOT / "scripts/summarize-alpha2-macos-model-qualification.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MacQualificationSummaryTests(unittest.TestCase):
    def test_compact_summary_retains_only_outcomes_and_metrics(self) -> None:
        result = {"status": "completed", "testContract": {"version": 2}, "modelsPulled": 1, "cleanup": [{"model": "model:test", "removed": True}], "results": [{"modelId": "one", "model": "model:test", "status": "failed", "checks": {"generalChat": {"status": "passed"}, "structuredCode": {"status": "failed"}}, "metrics": {"generalChat": {"tokensPerSecond": 10}, "structuredCode": {"tokensPerSecond": 20}}, "codingSurfaceStatus": "not-run", "codingRecommendationEligible": False}]}
        summary = MODULE.summarize(result)
        self.assertEqual(summary["passed"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["results"][0]["averageTokensPerSecond"], 15.0)
        self.assertNotIn("metrics", summary["results"][0])
        self.assertFalse(summary["rawPromptsOrResponsesRetained"])


if __name__ == "__main__":
    unittest.main()
