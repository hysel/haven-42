#!/usr/bin/env python3
"""Exercise the candidate updater without network access or model downloads."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "discover-online-model-candidates.py"


class ModelCandidateUpdaterTests(unittest.TestCase):
    def test_inventory_comparison_previous_delta_and_fail_closed_effects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            fixture = work / "ollama.html"
            output = work / "report.json"
            markdown = work / "report.md"
            previous = work / "previous.json"
            fixture.write_text(
                """
                <a href="/library/nemotron-3.5-lightning:30b-a3b-q4_K_M">tracked</a>
                <a href="/library/nemotron-3.5-lightning:30b-a3b-q6_K">new tag</a>
                <a href="/library/example-new-model:7b-q4_K_M">new family</a>
                <a href="/library/example-new-model:latest">mutable</a>
                """,
                encoding="utf-8",
            )
            previous.write_text(
                json.dumps(
                    {
                        "Candidates": [
                            {
                                "SourceId": "ollama",
                                "ArtifactId": "nemotron-3.5-lightning:30b-a3b-q6_K",
                                "Revision": None,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-config",
                    str(ROOT / "config" / "model-discovery-sources.json"),
                    "--contract-path",
                    str(ROOT / "config" / "model-discovery-contract.json"),
                    "--sources",
                    "ollama",
                    "--queries",
                    "nemotron-3.5-lightning",
                    "--queries",
                    "example-new-model",
                    "--ollama-html-fixture",
                    str(fixture),
                    "--inventory-path",
                    str(ROOT / "config" / "alpha-2-model-version-inventory.json"),
                    "--previous-report-path",
                    str(previous),
                    "--output-path",
                    str(output),
                    "--markdown-output-path",
                    str(markdown),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            candidates = {item["Model"]: item for item in report["Candidates"]}
            self.assertEqual(
                candidates["nemotron-3.5-lightning:30b-a3b-q4_K_M"]["InventoryStatus"],
                "already-tracked-exact-artifact",
            )
            self.assertEqual(
                candidates["nemotron-3.5-lightning:30b-a3b-q6_K"]["InventoryStatus"],
                "new-artifact-in-tracked-model-repository",
            )
            self.assertTrue(
                candidates["nemotron-3.5-lightning:30b-a3b-q6_K"]["SeenInPreviousReport"]
            )
            self.assertEqual(
                candidates["example-new-model:latest"]["TestQueueStatus"],
                "blocked-mutable-tag-requires-version-pinned-artifact",
            )
            self.assertEqual(report["UpdateSummary"]["DiscoveredCount"], 4)
            self.assertEqual(report["UpdateSummary"]["AlreadyTrackedExactCount"], 1)
            self.assertEqual(report["UpdateSummary"]["UntrackedCandidateCount"], 3)
            self.assertEqual(report["UpdateSummary"]["NewSincePreviousReportCount"], 2)
            self.assertFalse(report["PullsModels"])
            self.assertFalse(report["WritesCertificationInventory"])
            self.assertFalse(report["StartsTests"])
            self.assertFalse(report["ChangesAutomaticModelSelection"])
            human = markdown.read_text(encoding="utf-8")
            self.assertIn("This is a review queue", human)
            self.assertIn("example-new-model:7b-q4_K_M", human)


if __name__ == "__main__":
    unittest.main()
