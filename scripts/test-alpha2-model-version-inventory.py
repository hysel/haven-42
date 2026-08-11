#!/usr/bin/env python3
"""Validate the Alpha 2 model-family version inventory."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "config" / "alpha-2-model-version-inventory.json"
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
READY_DOWNLOAD_IDS = {
    "gemma3-1b-q4",
    "gemma3-4b-q4",
    "gemma4-e2b-qat",
    "gemma4-e4b-qat",
    "gemma4-12b-qat",
    "granite41-3b-q4",
    "granite41-8b-q4",
    "phi4-mini-38b-q4",
    "llama32-3b-q4",
    "ministral3-3b-q4",
    "ministral3-8b-q4",
}
ALLOWED_SOURCE_HOSTS = {
    "ai.google.dev",
    "github.com",
    "huggingface.co",
    "ollama.com",
    "www.ibm.com",
    "qwen.ai",
}


class ModelVersionInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    def test_inventory_is_fail_closed_and_not_selection_policy(self) -> None:
        self.assertEqual(self.inventory["schemaVersion"], 1)
        self.assertEqual(
            self.inventory["status"],
            "qualification-inventory-not-selection-policy",
        )
        rules = self.inventory["rules"]
        self.assertTrue(rules["officialPrimarySourcesOnly"])
        self.assertTrue(rules["exactManifestDigestRequiredBeforeExecution"])
        self.assertTrue(rules["downloadsRequireExplicitApply"])
        self.assertFalse(rules["mutableLatestTagsAllowed"])
        self.assertFalse(rules["automaticPromotionAllowed"])
        self.assertFalse(rules["rawPromptsOrResponsesAllowed"])
        self.assertTrue(rules["unloadAfterEverySampleRequired"])
        self.assertEqual(
            self.inventory["qualificationProvider"],
            {
                "name": "ollama",
                "exactVersion": "0.32.5",
                "transport": "ipv4-loopback-only",
            },
        )

    def test_qwen_versions_are_explicitly_complete_for_current_scope(self) -> None:
        qwen = next(item for item in self.inventory["families"] if item["family"] == "Qwen")
        self.assertEqual(
            [version["version"] for version in qwen["versions"]],
            ["3.5", "3.6", "3.7", "3.8"],
        )

    def test_gemma_four_local_candidates_are_exact(self) -> None:
        gemma = next(
            item for item in self.inventory["families"] if item["family"] == "Gemma"
        )
        gemma_four = next(
            item for item in gemma["versions"] if item["version"] == "4"
        )
        self.assertEqual(gemma_four["artifactStatus"], "local-artifacts-verified")
        self.assertEqual(gemma_four["license"], "Apache-2.0")
        self.assertEqual(
            {
                candidate["id"]: candidate["manifestDigest"]
                for candidate in gemma_four["candidates"]
            },
            {
                "gemma4-e2b-qat": "07ea59a474013479c8b6b802bef095c40e964a1d776ba02f264c0e30e1aede0c",
                "gemma4-e4b-qat": "ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f",
                "gemma4-12b-qat": "38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3",
            },
        )

    def test_added_cross_family_candidates_are_exact(self) -> None:
        expected = {
            "phi4-mini-38b-q4": "78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753",
            "llama32-3b-q4": "a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72",
            "ministral3-3b-q4": "f04aa1c738f64e13c625b82ae92504fc0260fa6723b509ed1ece0fa188179b1d",
            "ministral3-8b-q4": "1922accd5827ebe6829e536369195db25eaf664528dc66206d646ea3bb386b71",
        }
        actual = {
            candidate["id"]: candidate["manifestDigest"]
            for family in self.inventory["families"]
            for version in family["versions"]
            for candidate in version.get("candidates", [])
            if candidate["id"] in expected
        }
        self.assertEqual(actual, expected)

    def test_candidates_are_exact_unique_and_never_latest(self) -> None:
        ids: set[str] = set()
        models: set[str] = set()
        for family in self.inventory["families"]:
            for version in family["versions"]:
                candidates = version.get("candidates", [])
                if version["artifactStatus"] == "official-local-artifact-not-found":
                    self.assertEqual(candidates, [])
                for candidate in candidates:
                    self.assertNotIn(candidate["id"], ids)
                    self.assertNotIn(candidate["model"], models)
                    ids.add(candidate["id"])
                    models.add(candidate["model"])
                    self.assertNotRegex(candidate["model"], r"(^|:)latest$")
                    self.assertRegex(candidate["manifestDigest"], HEX_64)
                    if "modelLayerDigest" in candidate:
                        self.assertRegex(candidate["modelLayerDigest"], HEX_64)
                    self.assertIsInstance(candidate["modelBytes"], int)
                    self.assertGreater(candidate["modelBytes"], 0)
                    if candidate["id"] in READY_DOWNLOAD_IDS:
                        download_bytes = candidate["downloadBytes"]
                        self.assertIsInstance(download_bytes, int)
                        self.assertGreaterEqual(download_bytes, candidate["modelBytes"])

    def test_sources_are_https_and_from_reviewed_primary_hosts(self) -> None:
        for family in self.inventory["families"]:
            urls = [family["licenseSource"]]
            urls.extend(version["officialSource"] for version in family["versions"])
            urls.extend(
                version["licenseSource"]
                for version in family["versions"]
                if "licenseSource" in version
            )
            for source in urls:
                parsed = urlparse(source)
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(parsed.hostname, ALLOWED_SOURCE_HOSTS)

    def test_evidence_references_are_repository_relative_and_exist(self) -> None:
        for family in self.inventory["families"]:
            for version in family["versions"]:
                reference = version.get("evidenceReference")
                if reference is None:
                    continue
                self.assertFalse(Path(reference).is_absolute())
                self.assertTrue((ROOT / reference).is_file(), reference)


if __name__ == "__main__":
    unittest.main()
