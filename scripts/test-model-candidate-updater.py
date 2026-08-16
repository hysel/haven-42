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
    def test_newest_registry_index_finds_family_without_seed_query(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            fixture = work / "newest.html"
            output = work / "report.json"
            fixture.write_text(
                '''
                <a href="/library/surprise-local-family">new release</a>
                <a href="/library/cloud-only-family">hosted release</a>
                surprise-local-family:7b-q4_K_M
                cloud-only-family:cloud
                ''',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--source-config", str(ROOT / "config" / "model-discovery-sources.json"),
                    "--contract-path", str(ROOT / "config" / "model-discovery-contract.json"),
                    "--sources", "ollama-newest",
                    "--ollama-newest-html-fixture", str(fixture),
                    "--output-path", str(output),
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["QueriesBySource"]["ollama-newest"], [
                "surprise-local-family", "cloud-only-family"
            ])
            self.assertEqual(len(report["Candidates"]), 1)
            candidate = report["Candidates"][0]
            self.assertEqual(candidate["Model"], "surprise-local-family:7b-q4_K_M")
            self.assertTrue(candidate["DiscoveredWithoutSeedQuery"])
            self.assertEqual(candidate["SourceId"], "ollama-newest")
            self.assertEqual(len(report["SkippedCandidates"]), 1)
            self.assertEqual(report["SkippedCandidates"][0]["FailureSignal"], "MODEL_SKIPPED_FOR_PLATFORM")

    def test_official_publisher_feed_finds_unranked_release_by_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            fixture = work / "publisher-feed.json"
            output = work / "report.json"
            fixture.write_text(
                json.dumps([
                    {
                        "id": "Qwen/Qwen3.8-27B",
                        "author": "Qwen",
                        "sha": "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0",
                        "lastModified": "2026-08-14T15:00:01Z",
                        "pipeline_tag": "image-text-to-text",
                        "tags": ["transformers", "safetensors", "license:apache-2.0", "27b"],
                        "siblings": [{"rfilename": "model-00001-of-00018.safetensors"}],
                    },
                    {
                        "id": "Qwen/robotics-release",
                        "author": "Qwen",
                        "sha": "2" * 40,
                        "lastModified": "2026-08-15T00:00:00Z",
                        "pipeline_tag": "robotics",
                        "tags": ["license:apache-2.0"],
                    },
                    {
                        "id": "google/gemma-4-E4B-it",
                        "author": "google",
                        "sha": "ee0ef6023621cff504d758262d4e04895a5af4a2",
                        "lastModified": "2026-07-20T12:00:00Z",
                        "pipeline_tag": "image-text-to-text",
                        "tags": ["transformers", "safetensors", "license:apache-2.0", "4b"],
                        "siblings": [{"rfilename": "model-00001-of-00007.safetensors"}],
                    },
                ]),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-config", str(ROOT / "config" / "model-discovery-sources.json"),
                    "--contract-path", str(ROOT / "config" / "model-discovery-contract.json"),
                    "--sources", "official-publishers",
                    "--publisher-feed-json-fixture", str(fixture),
                    "--publisher-since-utc", "2026-08-01T00:00:00Z",
                    "--discovery-now-utc", "2026-08-16T00:00:00Z",
                    "--inventory-path", str(ROOT / "config" / "alpha-2-model-version-inventory.json"),
                    "--output-path", str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["PublisherFeedSinceUtc"], "2026-07-02T00:00:00Z")
            self.assertEqual(len(report["Candidates"]), 2)
            candidates = {item["Model"]: item for item in report["Candidates"]}
            candidate = candidates["Qwen/Qwen3.8-27B"]
            self.assertEqual(candidate["Model"], "Qwen/Qwen3.8-27B")
            self.assertEqual(candidate["Revision"], "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0")
            self.assertEqual(candidate["PublisherIdentityStatus"], "configured-publisher-namespace")
            self.assertIn("safetensors", candidate["Formats"])
            self.assertEqual(
                candidates["google/gemma-4-E4B-it"]["Revision"],
                "ee0ef6023621cff504d758262d4e04895a5af4a2",
            )
            self.assertEqual(len(report["SkippedCandidates"]), 1)
            self.assertFalse(report["PullsModels"])
            self.assertFalse(report["StartsTests"])

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
