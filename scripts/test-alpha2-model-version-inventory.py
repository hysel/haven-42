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
RUNTIME_REQUIREMENTS_PATH = ROOT / "config" / "alpha-2-model-runtime-requirements.json"
ALPHA2_CATALOG_PATH = ROOT / "config" / "alpha-2-model-catalog.json"
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
        cls.runtime_requirements = json.loads(
            RUNTIME_REQUIREMENTS_PATH.read_text(encoding="utf-8")
        )
        cls.alpha2_catalog = json.loads(
            ALPHA2_CATALOG_PATH.read_text(encoding="utf-8")
        )

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
                "exactVersion": "0.32.14",
                "transport": "ipv4-loopback-only",
            },
        )

    def test_qwen_versions_are_explicitly_complete_for_current_scope(self) -> None:
        qwen = next(item for item in self.inventory["families"] if item["family"] == "Qwen")
        self.assertEqual(
            [version["version"] for version in qwen["versions"]],
            ["3.5", "3.6", "3.7", "3.8"],
        )
        qwen38 = next(item for item in qwen["versions"] if item["version"] == "3.8")
        self.assertEqual(qwen38["artifactStatus"], "local-artifact-verified")
        self.assertEqual(
            qwen38["candidates"],
            [
                {
                    "id": "qwen38-27b-q4",
                    "model": "qwen3.8:27b",
                    "manifestDigest": "22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643",
                    "modelLayerDigest": "f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d",
                    "projectorLayerDigest": "ac3714bfdddeca31351f2752bf1a63f266f4df87c0b68c895e44945ca704448e",
                    "modelBytes": 16810714464,
                    "downloadBytes": 17741871939,
                    "quantization": "Q4_K_M",
                    "hardwareClass": "high-memory",
                    "minimumOllamaVersion": "0.32.12",
                    "runtimeRequirementReference": "config/alpha-2-model-runtime-requirements.json#qwen38-27b-q4",
                }
            ],
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

    def test_new_release_candidates_are_exact_and_runtime_pinned(self) -> None:
        expected = {
            "ornith-10-9b-q4": (
                "ornith:9b",
                "a75697c145891910e312c95e4a9fc1ccb8653e5ef543b23b0403a4665b82fd91",
                "0.30.11",
                5629110020,
            ),
            "north-mini-code-10-30b-a3b-q4": (
                "north-mini-code-1.0:q4_K_M",
                "d8b269ad5c7c7144ce104b83ce93bc3efb85e0f74e01be6be5f5d6f7ca90b60f",
                "0.30.10",
                18593966525,
            ),
            "lfm25-8b-a1b-q4": (
                "lfm2.5:8b",
                "9cf756159fc2f3b9128c6a3f544ec90c5e9b8afdbb4179a57b8aea9de589cfb2",
                "0.30.0",
                5156075045,
            ),
            "granite41-30b-q4": (
                "granite4.1:30b",
                "3f3e5df8a021439fd6f867a0e526bdc303cac79c811201cb6bac193298cb9fcd",
                "0.32.13",
                17490258936,
            ),
            "minicpm-v46-1b-q4": (
                "minicpm-v4.6:1b",
                "e95583acac773b45d95469c069db44808c87295f924183f4c942d52616b2d132",
                "0.30.0",
                1637848448,
            ),
            "nemotron3-nano-omni-33b-q4": (
                "nemotron3:33b",
                "f6d8b7ff496ccc53429cc480ad53971d522b443ee4a5aa58a6da49e57acf42cf",
                "0.32.13",
                27638631216,
            ),
        }
        actual = {
            candidate["id"]: (
                candidate["model"],
                candidate["manifestDigest"],
                candidate["minimumOllamaVersion"],
                candidate["downloadBytes"],
            )
            for family in self.inventory["families"]
            for version in family["versions"]
            for candidate in version.get("candidates", [])
            if candidate["id"] in expected
        }
        self.assertEqual(actual, expected)

    def test_muse_glimmer_candidates_are_exact_and_runtime_gated(self) -> None:
        muse = next(
            item for item in self.inventory["families"]
            if item["family"] == "Muse Glimmer"
        )
        self.assertEqual(muse["license"], "Apache-2.0")
        version = muse["versions"][0]
        self.assertEqual(version["version"], "30B")
        self.assertEqual(
            version["qualificationState"],
            "ollama-0.32.9-task-contract-failed-other-routes-untested",
        )
        candidates = {item["id"]: item for item in version["candidates"]}
        self.assertEqual(
            {
                model_id: (
                    candidate["model"],
                    candidate["manifestDigest"],
                    candidate["minimumOllamaVersion"],
                )
                for model_id, candidate in candidates.items()
            },
            {
                "muse-glimmer-30b-q4": (
                    "muse-glimmer:30b",
                    "de878ce33ad81d060001db1469a02eebe4d86f0ad58cfe52dc062fdcbe4464c1",
                    "0.32.8",
                ),
                "muse-glimmer-30b-mlx-nvfp4": (
                    "muse-glimmer:30b-mlx",
                    "ef32a55b4976faa955cbab0462d09bd081351ef5b87d73d8fcd299bf17c111d7",
                    "0.32.7",
                ),
            },
        )
        self.assertEqual(
            candidates["muse-glimmer-30b-q4"]["projectorLayerDigest"],
            "f48b452316f9b213758e8659444029b961a24a07f99a1abb2a9f88b06f7c00c6",
        )
        self.assertEqual(
            candidates["muse-glimmer-30b-mlx-nvfp4"]["configDigest"],
            "751aed2d7eee5bdf40f0d4138aa7fe57f0e54e96a430902dc9fa08fba3ae5f6a",
        )

    def test_nemotron_lightning_candidates_are_exact_and_not_promoted(self) -> None:
        family = next(
            item for item in self.inventory["families"]
            if item["family"] == "NVIDIA Nemotron"
        )
        self.assertEqual(family["license"], "NVIDIA-Nemotron-Open-Model-License")
        version = family["versions"][0]
        self.assertEqual(version["version"], "3.5 Lightning")
        self.assertEqual(
            version["qualificationState"],
            "planned-awaiting-explicit-owner-start",
        )
        self.assertEqual(
            version["architecture"],
            {
                "type": "mixture-of-experts",
                "totalParameters": "30B",
                "activeParameters": "3B",
            },
        )
        candidates = {item["id"]: item for item in version["candidates"]}
        self.assertEqual(
            candidates["nemotron35-lightning-30b-a3b-q4"]["minimumOllamaVersion"],
            "0.32.9",
        )
        self.assertEqual(
            candidates["nemotron35-lightning-30b-a3b-q8"]["minimumOllamaVersion"],
            "0.32.9",
        )
        self.assertEqual(
            {
                model_id: (candidate["model"], candidate["manifestDigest"])
                for model_id, candidate in candidates.items()
            },
            {
                "nemotron35-lightning-30b-a3b-q4": (
                    "nemotron-3.5-lightning:30b-a3b-q4_K_M",
                    "e7a64ff15fb174c42b4f463e5c888c4f2c7b9cabf9e8d65a1c0874405426c1b2",
                ),
                "nemotron35-lightning-30b-a3b-q8": (
                    "nemotron-3.5-lightning:30b-a3b-q8_0",
                    "9983b24ee511395c8d58ce1f92e0e8c11c4e2fb43029d1718c1d6694e8187117",
                ),
                "nemotron35-lightning-30b-a3b-bf16": (
                    "nemotron-3.5-lightning:30b-a3b-bf16",
                    "721c64cd61aca9b6dad20ef642d3e41ca16f0054099a3e3f42c9375aae649f39",
                ),
                "nemotron35-lightning-30b-a3b-mlx-nvfp4": (
                    "nemotron-3.5-lightning:30b-a3b-mlx",
                    "8b1474be6e54dc19eb7aa08bebfb9bda147c4b9ef9796a726131ad29ad15645a",
                ),
                "nemotron35-lightning-30b-a3b-mlx-mxfp8": (
                    "nemotron-3.5-lightning:30b-a3b-mxfp8",
                    "906068bad076d14ef66bb8d7245879ee2c1c5a70188f5baa37166b83c69f5d6d",
                ),
                "nemotron35-lightning-30b-a3b-mlx-bf16": (
                    "nemotron-3.5-lightning:30b-a3b-mlx-bf16",
                    "7bf11b5991edd861896d66dfefb55f3fa837b139f7070edba980d982a56a25d6",
                ),
            },
        )
        self.assertEqual(candidates["nemotron35-lightning-30b-a3b-q4"]["contextWindowTokens"], 1048576)
        self.assertEqual(candidates["nemotron35-lightning-30b-a3b-mlx-nvfp4"]["contextWindowTokens"], 262144)

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
                    if "projectorLayerDigest" in candidate:
                        self.assertRegex(candidate["projectorLayerDigest"], HEX_64)
                    if "configDigest" in candidate:
                        self.assertRegex(candidate["configDigest"], HEX_64)
                    self.assertIsInstance(candidate["modelBytes"], int)
                    self.assertGreater(candidate["modelBytes"], 0)
                    if candidate["id"] in READY_DOWNLOAD_IDS:
                        download_bytes = candidate["downloadBytes"]
                        self.assertIsInstance(download_bytes, int)
                        self.assertGreaterEqual(download_bytes, candidate["modelBytes"])

    def test_runtime_requirement_references_match_exact_model_routes(self) -> None:
        requirements = {
            item["modelId"]: item for item in self.runtime_requirements["models"]
        }
        referenced_ids: set[str] = set()

        for family in self.inventory["families"]:
            for version in family["versions"]:
                for candidate in version.get("candidates", []):
                    minimum = candidate.get("minimumOllamaVersion")
                    reference = candidate.get("runtimeRequirementReference")
                    if minimum is None and reference is None:
                        continue

                    self.assertIsNotNone(minimum, candidate["id"])
                    self.assertEqual(
                        reference,
                        f"config/alpha-2-model-runtime-requirements.json#{candidate['id']}",
                    )
                    requirement = requirements[candidate["id"]]
                    referenced_ids.add(candidate["id"])
                    ollama_route = next(
                        route
                        for route in requirement["routes"]
                        if route["engine"] == "ollama"
                    )
                    self.assertEqual(ollama_route["minimumRuntimeVersion"], minimum)
                    self.assertEqual(
                        ollama_route["modelArtifact"]["exactTag"], candidate["model"]
                    )
                    self.assertEqual(
                        ollama_route["modelArtifact"]["manifestSha256"],
                        candidate["manifestDigest"],
                    )

        for candidate in self.alpha2_catalog["models"]:
            requirement = requirements[candidate["id"]]
            referenced_ids.add(candidate["id"])
            self.assertEqual(len(requirement["routes"]), 1)
            ollama_route = requirement["routes"][0]
            self.assertEqual(ollama_route["engine"], "ollama")
            self.assertEqual(ollama_route["admissionState"], "admitted")
            self.assertEqual(ollama_route["minimumRuntimeVersion"], "0.32.5")
            self.assertEqual(
                ollama_route["modelArtifact"]["exactTag"], candidate["name"]
            )
            self.assertEqual(
                ollama_route["modelArtifact"]["manifestSha256"],
                candidate["manifestDigest"],
            )

        self.assertEqual(referenced_ids, set(requirements))

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
