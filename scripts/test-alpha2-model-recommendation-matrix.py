#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("matrix", ROOT / "scripts/alpha2-model-recommendation-matrix.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RecommendationMatrixTests(unittest.TestCase):
    def test_all_pinned_profiles_preserve_expected_decisions(self) -> None:
        fixtures = json.loads((ROOT / "examples/fixtures/alpha-2-model-selection-cases.json").read_text(encoding="utf-8"))
        result = MODULE.build_matrix(fixtures)
        self.assertEqual(result["caseCount"], len(fixtures["cases"]))
        self.assertTrue(all(row["selectedModelId"] == row["expectedModelId"] for row in result["cases"]))
        self.assertFalse(result["productAdmission"])
        self.assertFalse(result["downloadsPerformed"])

    def test_fixture_cannot_claim_product_admission(self) -> None:
        fixtures = json.loads((ROOT / "examples/fixtures/alpha-2-model-selection-cases.json").read_text(encoding="utf-8"))
        fixtures["productAdmission"] = True
        with self.assertRaisesRegex(ValueError, "non-product synthetic"):
            MODULE.build_matrix(fixtures)


if __name__ == "__main__":
    unittest.main()
