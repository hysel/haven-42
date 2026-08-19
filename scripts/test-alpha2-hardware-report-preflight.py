#!/usr/bin/env python3
from __future__ import annotations

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


NORMALIZE = load("normalize_fixture", "scripts/alpha2-hardware-result-normalizer.py")
PREFLIGHT = load("preflight_fixture", "scripts/alpha2-hardware-report-preflight.py")


class HardwareReportPreflightTests(unittest.TestCase):
    @classmethod
    def legacy(cls) -> dict:
        return json.loads((ROOT / "config/alpha-2-nvidia-rtx3060-qualification-result.json").read_text(encoding="utf-8"))

    def test_legacy_normalization_never_upgrades_completion(self) -> None:
        result = NORMALIZE.normalize(self.legacy())
        self.assertEqual(result["status"], "in-progress-local-review-only")
        self.assertIsNone(result["sourceBindings"]["inputFreshness"])
        self.assertIn("cannot-be-promoted-to-complete-by-normalization", result["legacyLimitations"])

    def test_legacy_pair_is_previewable_but_not_publishable(self) -> None:
        first = NORMALIZE.normalize(self.legacy())
        second = json.loads(json.dumps(first))
        second["environment"]["operatingSystem"] = "Linux fixture"
        result = PREFLIGHT.preflight(first, second)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["publicationAllowed"])
        self.assertIn("first-cell-input-bindings-not-fresh", result["blockers"])

    def test_two_fresh_complete_cells_are_ready(self) -> None:
        value = NORMALIZE.normalize(self.legacy())
        value["status"] = "exact-profile-engineering-evidence-complete"
        value["sourceBindings"]["inputFreshness"] = {
            "evidenceId": "fixture", "status": "fresh", "roles": ["fixture"], "sha256": {"fixture": "a" * 64}
        }
        other = json.loads(json.dumps(value))
        other["environment"]["operatingSystem"] = "Linux fixture"
        other["sourceBindings"]["inputFreshness"]["evidenceId"] = "fixture-linux"
        result = PREFLIGHT.preflight(value, other)
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["publicationAllowed"])


if __name__ == "__main__":
    unittest.main()
