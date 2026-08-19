#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("report", ROOT / "scripts/alpha2-model-recommendation-report.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RecommendationReportTests(unittest.TestCase):
    def profile(self) -> dict:
        return {
            "platformFamily": "linux", "operatingSystemId": "ubuntu-26-04",
            "architecture": "x64", "backendMode": "cuda", "systemMemoryGiB": 32,
            "usableGpuMemoryGiB": 12,
            "storageAdmittedModelIds": [
                "qwen35-08b-q8", "qwen35-2b-q8", "qwen35-4b-q4", "qwen35-9b-q4",
                "qwen35-27b-q4", "qwen35-35b-q4",
            ],
            "requestedCapabilities": ["general.chat", "content.write", "content.summarize"],
            "provider": "ollama", "providerVersion": "0.32.5",
        }

    def evidence(self, model: dict, policy_digest: str) -> dict:
        return {
            "evidenceId": f'evidence-{model["id"]}', "modelId": model["id"],
            "manifestDigest": model["manifestDigest"], "platformFamily": "linux",
            "operatingSystemId": "ubuntu-26-04", "architecture": "x64",
            "backendMode": "cuda", "provider": "ollama", "providerVersion": "0.32.5",
            "minimumTestedSystemMemoryGiB": 16,
            "minimumTestedUsableGpuMemoryGiB": 6,
            "capabilities": ["general.chat", "content.write", "content.summarize"],
            "status": "passed", "selectorPolicyCanonicalSha256": policy_digest,
        }

    def test_report_matches_selector_and_explains_larger_rejections(self) -> None:
        policy, catalog = MODULE.SELECTOR.load_policy()
        digest = MODULE.SELECTOR.canonical_sha256(policy)
        by_id = {model["id"]: model for model in catalog["models"]}
        evidence = [self.evidence(by_id["qwen35-4b-q4"], digest)]
        result = MODULE.explain(self.profile(), evidence)
        self.assertEqual(result["selectorDecision"]["selectedModelId"], "qwen35-4b-q4")
        self.assertEqual(result["runtimeRoute"]["status"], "admitted-route-found")
        rows = {row["modelId"]: row for row in result["candidates"]}
        self.assertIn("no-model-evidence", rows["qwen35-9b-q4"]["reasons"])
        self.assertIn("insufficient-system-memory", rows["qwen35-27b-q4"]["reasons"])
        self.assertFalse(result["policyChanged"])
        self.assertFalse(result["downloadsPerformed"])

    def test_exact_profile_mismatch_is_explained_by_field(self) -> None:
        policy, catalog = MODULE.SELECTOR.load_policy()
        digest = MODULE.SELECTOR.canonical_sha256(policy)
        by_id = {model["id"]: model for model in catalog["models"]}
        record = self.evidence(by_id["qwen35-4b-q4"], digest)
        record["providerVersion"] = "0.32.6"
        result = MODULE.explain(self.profile(), [record])
        row = next(item for item in result["candidates"] if item["modelId"] == "qwen35-4b-q4")
        self.assertIn("no-evidence-for-providerVersion", row["reasons"])
        self.assertIsNone(result["selectorDecision"]["selectedModelId"])


if __name__ == "__main__":
    unittest.main()
