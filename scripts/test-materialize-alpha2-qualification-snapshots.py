#!/usr/bin/env python3
"""Checks for qualification campaign snapshot reconstruction."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize-alpha2-qualification-snapshots.py"
SPEC = importlib.util.spec_from_file_location("campaign_snapshots", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CampaignSnapshotTests(unittest.TestCase):
    def test_all_four_generations_materialize_with_exact_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "snapshots"
            values = MODULE.materialize(output)
            self.assertEqual(
                [value["id"] for value in values],
                [
                    "campaign-initial",
                    "campaign-release-expansion",
                    "campaign-pre-qwen35-rx-ladder",
                    "campaign-current",
                ],
            )
            self.assertTrue((output / "campaign-initial" / "inventory.json").is_file())
            self.assertTrue((output / "campaign-current" / "matrix.json").is_file())
            with self.assertRaisesRegex(MODULE.SnapshotError, "output-already-exists"):
                MODULE.materialize(output)


if __name__ == "__main__":
    unittest.main()
