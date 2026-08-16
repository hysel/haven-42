#!/usr/bin/env python3
"""Test fail-closed Alpha 2 model/runtime resolution."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alpha2_runtime_compatibility",
    ROOT / "scripts" / "alpha2_runtime_compatibility.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RuntimeCompatibilityTests(unittest.TestCase):
    @staticmethod
    def model_requirements() -> dict:
        return json.loads(
            (ROOT / "config" / "alpha-2-model-runtime-requirements.json").read_text(
                encoding="utf-8"
            )
        )

    @staticmethod
    def windows_registry() -> dict:
        return json.loads(
            (ROOT / "config" / "windows-alpha-component-registry.json").read_text(
                encoding="utf-8"
            )
        )

    def test_active_alpha2_qwen_ladder_is_bound_to_admitted_ollama(self) -> None:
        expected = {
            "qwen35-08b-q8": "qwen3.5:0.8b",
            "qwen35-2b-q8": "qwen3.5:2b",
            "qwen35-4b-q4": "qwen3.5:4b",
            "qwen35-9b-q4": "qwen3.5:9b",
            "qwen35-27b-q4": "qwen3.5:27b",
            "qwen35-35b-q4": "qwen3.5:35b",
        }
        for model_id, tag in expected.items():
            with self.subTest(model_id=model_id):
                result = MODULE.resolve(model_id, "linux-x64", "core")
                self.assertEqual(result["decision"], "install")
                self.assertEqual(result["engine"], "ollama")
                self.assertEqual(result["selectedRuntimeVersion"], "0.32.5")
                self.assertEqual(result["modelArtifact"]["exactTag"], tag)
                self.assertEqual(result["installationRoot"], "Haven42-Data")

    def test_active_qwen_has_no_unreviewed_llamacpp_fallback(self) -> None:
        with self.assertRaisesRegex(MODULE.CompatibilityError, "no-model-runtime-route"):
            MODULE.resolve(
                "qwen35-4b-q4", "windows-x64", "cuda-12.4", engine="llama.cpp"
            )

    def test_managed_plan_matches_exact_resolved_artifact(self) -> None:
        resolution = MODULE.resolve("qwen35-4b-q4", "windows-x64", "core")
        result = MODULE.validate_managed_setup_binding(
            resolution,
            {
                "kind": "windows-alpha-setup-plan",
                "planId": "plan-1",
                "modelId": "qwen35-4b-q4",
                "backendMode": "cuda",
                "components": ["ollama-windows-core"],
            },
            self.windows_registry(),
        )
        self.assertEqual(result["runtimeVersion"], "0.32.5")
        self.assertEqual(result["backend"], "core")
        self.assertEqual(
            result["artifactSha256"],
            ["7c941ae084569d298062d29f8139163a3187c76dbca0479c70d085e78fd8c7bb"],
        )

    def test_managed_rocm_plan_requires_both_exact_artifacts(self) -> None:
        resolution = MODULE.resolve("qwen35-4b-q4", "windows-x64", "rocm")
        result = MODULE.validate_managed_setup_binding(
            resolution,
            {
                "kind": "windows-alpha-setup-plan",
                "planId": "plan-2",
                "modelId": "qwen35-4b-q4",
                "backendMode": "rocm",
                "components": ["ollama-windows-core", "ollama-windows-amd-rocm"],
            },
            self.windows_registry(),
        )
        self.assertEqual(len(result["artifactSha256"]), 2)

    def test_managed_plan_rejects_component_registry_drift(self) -> None:
        resolution = MODULE.resolve("qwen35-4b-q4", "windows-x64", "core")
        registry = copy.deepcopy(self.windows_registry())
        registry["components"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            MODULE.CompatibilityError, "managed-component-runtime-artifact-mismatch"
        ):
            MODULE.validate_managed_setup_binding(
                resolution,
                {
                    "kind": "windows-alpha-setup-plan",
                    "planId": "plan-3",
                    "modelId": "qwen35-4b-q4",
                    "backendMode": "cpu",
                    "components": ["ollama-windows-core"],
                },
                registry,
            )

    def test_managed_plan_rejects_cross_backend_binding(self) -> None:
        resolution = MODULE.resolve("qwen35-4b-q4", "windows-x64", "core")
        with self.assertRaisesRegex(
            MODULE.CompatibilityError, "managed-plan-runtime-route-mismatch"
        ):
            MODULE.validate_managed_setup_binding(
                resolution,
                {
                    "kind": "windows-alpha-setup-plan",
                    "planId": "plan-4",
                    "modelId": "qwen35-4b-q4",
                    "backendMode": "rocm",
                    "components": ["ollama-windows-core", "ollama-windows-amd-rocm"],
                },
                self.windows_registry(),
            )

    def test_product_resolution_denies_unadmitted_runtime(self) -> None:
        with self.assertRaisesRegex(
            MODULE.CompatibilityError, "no-admitted-compatible-runtime"
        ):
            MODULE.resolve(
                "nemotron35-lightning-30b-a3b-q4",
                "linux-x64",
                "core",
            )

    def test_planning_resolution_selects_newest_exact_candidate_artifact(self) -> None:
        result = MODULE.resolve(
            "nemotron35-lightning-30b-a3b-q4",
            "linux-x64",
            "core",
            include_candidate=True,
        )
        self.assertEqual(result["decision"], "candidate")
        self.assertEqual(result["minimumOllamaVersion"], "0.32.9")
        self.assertEqual(result["selectedOllamaVersion"], "0.32.13")
        self.assertEqual(result["installationRoot"], "Haven42-Data")
        self.assertFalse(result["systemRuntimeModificationAllowed"])
        self.assertEqual(
            [artifact["name"] for artifact in result["artifacts"]],
            ["ollama-linux-amd64.tar.zst"],
        )
        self.assertEqual(
            result["artifacts"][0]["sha256"],
            "0fd1dece38a1c6242e8013ce20b597345c5de072ae6b320160edb0e729ef1de1",
        )

    def test_nemotron_routes_record_partial_evidence_without_admission(self) -> None:
        requirements = {
            item["modelId"]: item
            for item in self.model_requirements()["models"]
        }
        for model_id in (
            "nemotron35-lightning-30b-a3b-q4",
            "nemotron35-lightning-30b-a3b-q8",
        ):
            ollama = next(
                route for route in requirements[model_id]["routes"]
                if route["engine"] == "ollama"
            )
            self.assertEqual(
                ollama["admissionState"],
                "candidate-qualification-partial-remaining-gates",
            )
            self.assertEqual(
                ollama["evidenceReferences"],
                ["examples/nvidia-v100-nemotron-validation.md"],
            )

    def test_llamacpp_profile_evidence_stays_fail_closed(self) -> None:
        registry = json.loads(
            (ROOT / "config" / "alpha-2-runtime-compatibility.json").read_text(
                encoding="utf-8"
            )
        )
        runtime = next(
            item for item in registry["llamaCppRuntimes"]
            if item["version"] == "b10375"
        )
        profiles = {
            (item["platform"], item["backend"]): item
            for item in runtime["profileEvidence"]
        }
        self.assertEqual(
            profiles[("linux-x64", "sycl-fp16")]["outcome"], "partial-pass"
        )
        wsl = profiles[("wsl2-ubuntu-x64", "hip-dxg")]
        self.assertEqual(wsl["decision"], "deny-this-runtime-on-this-profile")
        self.assertEqual(wsl["lastPassingRuntime"], "b10088")
        self.assertEqual(
            wsl["lastPassingCommit"],
            "67b9b0e7f6ce45d929a4411907d3c48ec719e81c",
        )
        self.assertTrue(
            all(
                not item["automaticAdmissionAllowed"]
                for item in profiles.values()
            )
        )

    def test_rocm_resolution_requires_core_and_rocm_artifacts(self) -> None:
        result = MODULE.resolve(
            "nemotron35-lightning-30b-a3b-q8",
            "windows-x64",
            "rocm",
            include_candidate=True,
        )
        self.assertEqual(
            {artifact["backend"] for artifact in result["artifacts"]},
            {"core", "rocm"},
        )

    def test_unregistered_model_fails_closed(self) -> None:
        with self.assertRaisesRegex(MODULE.CompatibilityError, "model-not-registered"):
            MODULE.resolve("unknown-model", "windows-x64", "core", include_candidate=True)

    def test_muse_glimmer_ollama_route_remains_blocked_after_task_failure(self) -> None:
        with self.assertRaisesRegex(
            MODULE.CompatibilityError, "no-admitted-compatible-runtime"
        ):
            MODULE.resolve(
                "muse-glimmer-30b-q4",
                "windows-x64",
                "rocm",
                include_candidate=True,
            )

    def test_llamacpp_product_resolution_denies_candidate_runtime(self) -> None:
        with self.assertRaisesRegex(
            MODULE.CompatibilityError, "no-admitted-compatible-runtime"
        ):
            MODULE.resolve(
                "muse-glimmer-30b-q4",
                "windows-x64",
                "cuda-12.4",
                engine="llama.cpp",
            )

    def test_llamacpp_planning_selects_exact_runtime_and_model(self) -> None:
        result = MODULE.resolve(
            "muse-glimmer-30b-q4",
            "windows-x64",
            "cuda-12.4",
            engine="llama.cpp",
            include_candidate=True,
        )
        self.assertEqual(result["decision"], "candidate")
        self.assertEqual(result["minimumRuntimeVersion"], "b10353")
        self.assertEqual(result["selectedRuntimeVersion"], "b10375")
        self.assertEqual(
            {artifact["role"] for artifact in result["runtimeArtifacts"]},
            {"runtime", "runtime-support"},
        )
        self.assertEqual(
            result["modelArtifact"]["revision"],
            "a0532f7263ee67f1e0a5f5c5fdcd50dd62fc9aa4",
        )
        self.assertEqual(
            [item["role"] for item in result["modelArtifact"]["selectedComponents"]],
            ["text-model"],
        )
        self.assertFalse(result["silentEngineFallbackAllowed"])

    def test_llamacpp_vision_adds_exact_projector(self) -> None:
        result = MODULE.resolve(
            "muse-glimmer-30b-q4",
            "windows-x64",
            "vulkan",
            engine="llama.cpp",
            capability="vision",
            include_candidate=True,
        )
        self.assertEqual(
            [item["role"] for item in result["modelArtifact"]["selectedComponents"]],
            ["text-model", "vision-projector"],
        )

    def test_llamacpp_nemotron_selects_conservative_pinned_release(self) -> None:
        result = MODULE.resolve(
            "nemotron35-lightning-30b-a3b-q4",
            "windows-x64",
            "rocm",
            engine="llama.cpp",
            include_candidate=True,
        )
        self.assertEqual(result["minimumRuntimeVersion"], "b10375")
        self.assertEqual(result["selectedRuntimeVersion"], "b10375")
        component = result["modelArtifact"]["selectedComponents"][0]
        self.assertEqual(
            component["sha256"],
            "6110e2e2e6cd324e6ee69ddced5a6b34fad6c94ca9827222a1e420fb92e3c90b",
        )

    def test_llamacpp_linux_cuda_fails_without_official_managed_artifact(self) -> None:
        with self.assertRaisesRegex(
            MODULE.CompatibilityError, "no-admitted-compatible-runtime"
        ):
            MODULE.resolve(
                "nemotron35-lightning-30b-a3b-q4",
                "linux-x64",
                "cuda",
                engine="llama.cpp",
                include_candidate=True,
            )

    def test_engine_fallback_is_never_inferred(self) -> None:
        with self.assertRaisesRegex(MODULE.CompatibilityError, "invalid-runtime-request"):
            MODULE.resolve(
                "muse-glimmer-30b-q4",
                "windows-x64",
                "cuda",
                engine="unknown",
                include_candidate=True,
            )


if __name__ == "__main__":
    unittest.main()
