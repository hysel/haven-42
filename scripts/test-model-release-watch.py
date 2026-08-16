#!/usr/bin/env python3
"""Validate the candidate-only model release radar."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
WATCH = json.loads((ROOT / "config" / "model-release-watch.json").read_text(encoding="utf-8"))
SHA1 = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_HOSTS = {"huggingface.co", "ollama.com"}


class ModelReleaseWatchTests(unittest.TestCase):
    def test_watch_is_candidate_only_and_effect_free(self) -> None:
        self.assertEqual(WATCH["schemaVersion"], 1)
        self.assertEqual(WATCH["status"], "candidate-only-no-download-no-execution-no-promotion")
        rules = WATCH["rules"]
        self.assertTrue(rules["officialPrimaryReleaseSourceRequired"])
        self.assertTrue(rules["immutableRevisionRequiredBeforeTestPlanning"])
        self.assertTrue(rules["exactRuntimeAndArtifactRequiredBeforeExecution"])
        self.assertFalse(rules["newModelDownloadStarted"])
        self.assertFalse(rules["newSoakStarted"])
        self.assertFalse(rules["automaticDefaultChanged"])
        self.assertFalse(rules["supportLabelChanged"])

    def test_candidates_are_unique_public_and_explicit(self) -> None:
        ids = set()
        for item in WATCH["candidates"]:
            self.assertNotIn(item["id"], ids)
            ids.add(item["id"])
            parsed = urlparse(item["sourceUrl"])
            self.assertEqual(parsed.scheme, "https")
            self.assertIn(parsed.hostname, ALLOWED_HOSTS)
            if item["revision"] is not None:
                self.assertRegex(item["revision"], SHA1)
            self.assertGreater(item["repositorySizeGiBApprox"], 0)
            self.assertTrue(item["capabilityLanes"])
            self.assertIn(item["priority"], {"highest", "high", "medium", "low"})
            self.assertNotIn("192.168.", json.dumps(item))
        self.assertIn("qwen38-27b", ids)
        self.assertIn("gemma4-local-family", ids)
        self.assertIn("mage-vl-5b", ids)
        self.assertIn("riva-translate-4b-v2", ids)
        self.assertIn("north-micro-vision-instruct-24b", ids)
        self.assertIn("ornith-10-9b-q4", ids)

    def test_hardware_ineligible_releases_remain_visible(self) -> None:
        excluded = {item["id"]: item for item in WATCH["monitoredButNotCurrentLabCandidates"]}
        self.assertIn("qwen38-24t-a95b", excluded)
        self.assertIn("kimi-k3-28t", excluded)
        self.assertIn("laguna-s-21-118b-a8b", excluded)
        self.assertIn("deepseek-v4-flash-0731", excluded)
        self.assertIn("deepseek-v4-pro-0813", excluded)
        self.assertIn("glm5", excluded)
        for item in excluded.values():
            self.assertTrue(item["reason"])


if __name__ == "__main__":
    unittest.main()
