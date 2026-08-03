#!/usr/bin/env python3
"""Security and parser tests for the cross-accelerator lab runner."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-cross-accelerator-model-matrix.py"
SPEC = importlib.util.spec_from_file_location("cross_accelerator_matrix", RUNNER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MatrixRunnerTests(unittest.TestCase):
    def test_repository_manifest_is_valid(self) -> None:
        manifest = MODULE.load_manifest(
            ROOT / "examples" / "cross-accelerator-model-matrix.json"
        )
        self.assertEqual(manifest["runtime"]["expectedBuildNumber"], 10088)
        self.assertEqual(len(manifest["models"]), 11)

    def test_manifest_rejects_parent_traversal(self) -> None:
        manifest = json.loads(
            (ROOT / "examples" / "cross-accelerator-model-matrix.json").read_text(
                encoding="utf-8"
            )
        )
        manifest["models"][0]["artifact"]["path"] = "../escape.gguf"
        with self.assertRaisesRegex(MODULE.MatrixError, "safe relative"):
            MODULE.validate_manifest(manifest)

    def test_manifest_rejects_duplicate_model_ids(self) -> None:
        manifest = json.loads(
            (ROOT / "examples" / "cross-accelerator-model-matrix.json").read_text(
                encoding="utf-8"
            )
        )
        manifest["models"][1]["id"] = manifest["models"][0]["id"]
        with self.assertRaisesRegex(MODULE.MatrixError, "Duplicate"):
            MODULE.validate_manifest(manifest)

    def test_manifest_rejects_security_policy_relaxation(self) -> None:
        manifest = json.loads(
            (ROOT / "examples" / "cross-accelerator-model-matrix.json").read_text(
                encoding="utf-8"
            )
        )
        manifest["security"]["networkUseDuringInference"] = True
        with self.assertRaisesRegex(MODULE.MatrixError, "security policy"):
            MODULE.validate_manifest(manifest)

    def test_manifest_rejects_unbounded_execution_and_unknown_tests(self) -> None:
        manifest = json.loads(
            (ROOT / "examples" / "cross-accelerator-model-matrix.json").read_text(
                encoding="utf-8"
            )
        )
        manifest["execution"]["timeoutSeconds"] = 999999
        with self.assertRaisesRegex(MODULE.MatrixError, "outside"):
            MODULE.validate_manifest(manifest)
        manifest["execution"]["timeoutSeconds"] = 300
        manifest["models"][0]["tests"].append("execute-host-command")
        with self.assertRaisesRegex(MODULE.MatrixError, "allowlist"):
            MODULE.validate_manifest(manifest)

    def test_resolve_beneath_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(strict=True)
            target = root / "target"
            target.write_bytes(b"safe")
            link = root / "link"
            try:
                link.symlink_to(target)
            except OSError:
                with self.assertRaisesRegex(MODULE.MatrixError, "outside"):
                    MODULE.resolve_beneath(root, "../escape", "artifact")
            else:
                with self.assertRaisesRegex(MODULE.MatrixError, "symlink"):
                    MODULE.resolve_beneath(root, "link", "artifact")

    def test_verify_artifact_checks_size_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(strict=True)
            artifact = root / "model.gguf"
            artifact.write_bytes(b"controlled")
            good = {
                "path": "model.gguf",
                "sizeBytes": 10,
                "sha256": MODULE.hashlib.sha256(b"controlled").hexdigest(),
            }
            self.assertEqual(MODULE.verify_artifact(root, good, "model"), artifact)
            bad = dict(good, sha256="0" * 64)
            with self.assertRaisesRegex(MODULE.MatrixError, "SHA-256"):
                MODULE.verify_artifact(root, bad, "model")

    def test_benchmark_parser_returns_only_sanitized_metrics(self) -> None:
        rows = [
            {
                "build_commit": "67b9b0e7f",
                "build_number": 10088,
                "backends": "HIP",
                "gpu_info": "AMD Radeon RX 7800 XT",
                "model_filename": "private/path/model.gguf",
                "model_type": "qwen 1B",
                "model_n_params": 10,
                "n_prompt": 128,
                "n_gen": 0,
                "n_gpu_layers": 99,
                "avg_ts": 100.5,
            },
            {
                "n_prompt": 0,
                "n_gen": 64,
                "avg_ts": 50.25,
            },
        ]
        result = MODULE.parse_benchmark(json.dumps(rows))
        self.assertNotIn("model_filename", result)
        self.assertEqual(result["generationTokensPerSecond"], 50.25)

    def test_full_offload_requires_all_layers(self) -> None:
        partial = MODULE.offload_result(
            "ROCm0 offloaded 20/21 layers to GPU", "hip"
        )
        full = MODULE.offload_result(
            "ROCm0 offloaded 21/21 layers to GPU", "hip"
        )
        self.assertFalse(partial["fullGpuOffload"])
        self.assertTrue(full["fullGpuOffload"])
        self.assertTrue(full["backendObserved"])

    def test_sycl_backend_requires_intel_runtime_evidence(self) -> None:
        full = MODULE.offload_result(
            "SYCL0 offloaded 41/41 layers to GPU; Intel(R) Arc(TM) B580",
            "sycl",
        )
        wrong = MODULE.offload_result(
            "CUDA0 offloaded 41/41 layers to GPU; NVIDIA",
            "sycl",
        )
        self.assertTrue(full["fullGpuOffload"])
        self.assertTrue(full["backendObserved"])
        self.assertTrue(wrong["fullGpuOffload"])
        self.assertFalse(wrong["backendObserved"])

    def test_exact_output_removes_bounded_thinking_block_only(self) -> None:
        self.assertTrue(
            MODULE.exact_output_passed(
                "<think>internal synthetic reasoning</think>\nHAVEN42_MATRIX_OK"
            )
        )
        self.assertFalse(MODULE.exact_output_passed("HAVEN42_MATRIX_OK extra"))

    def test_exact_output_extracts_cli_conversation_wrapper(self) -> None:
        wrapped = (
            "private runtime banner omitted\n"
            f"> {MODULE.EXACT_PROMPT}\n"
            " HAVEN42_MATRIX_OK\n\n"
            "[ Prompt: 100.0 t/s | Generation: 50.0 t/s ]\n"
            "Exiting...\n"
        )
        self.assertEqual(MODULE.extract_cli_response(wrapped), "HAVEN42_MATRIX_OK")
        self.assertTrue(MODULE.exact_output_passed(wrapped))

    def test_incomplete_thinking_is_not_exact_output(self) -> None:
        wrapped = (
            f"> {MODULE.EXACT_PROMPT}\n"
            "[Start thinking]\nThe answer should be the requested marker\n"
            "[ Prompt: 100.0 t/s | Generation: 50.0 t/s ]\n"
        )
        self.assertFalse(MODULE.exact_output_passed(wrapped))

    def test_runner_forces_noninteractive_single_turn(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('runtime_binary(runtime_root, "llama-completion")', source)
        self.assertNotIn('runtime_binary(runtime_root, "llama-cli")', source)
        self.assertIn('"--single-turn"', source)
        self.assertIn('"--simple-io"', source)
        self.assertIn('"--no-warmup"', source)
        self.assertIn('"--verbose"', source)
        self.assertGreaterEqual(source.count('"--offline"'), 2)
        self.assertIn("shell=False", source)

    def test_child_environment_excludes_home_and_user_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(strict=True)
            environment = MODULE.safe_environment(root, "hip", "0", [])
        self.assertNotIn("HOME", environment)
        self.assertNotIn("USERPROFILE", environment)
        self.assertEqual(environment["HIP_VISIBLE_DEVICES"], "0")

    def test_sycl_environment_disables_persistent_cache_and_scopes_device(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(strict=True)
            environment = MODULE.safe_environment(root, "sycl", "0", [])
        self.assertEqual(environment["ONEAPI_DEVICE_SELECTOR"], "level_zero:gpu:0")
        self.assertEqual(environment["SYCL_CACHE_PERSISTENT"], "0")
        self.assertEqual(environment["ZES_ENABLE_SYSMAN"], "1")
        self.assertEqual(environment["GGML_SYCL_ENABLE_LEVEL_ZERO"], "1")
        self.assertNotIn("HOME", environment)
        self.assertNotIn("USERPROFILE", environment)

    def test_wsl_dxg_environment_is_fixed_and_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(strict=True)
            original = MODULE.os.environ.get("HSA_ENABLE_DXG_DETECTION")
            MODULE.os.environ["HSA_ENABLE_DXG_DETECTION"] = "hostile"
            try:
                default = MODULE.safe_environment(root, "hip", None, [])
                enabled = MODULE.safe_environment(
                    root, "hip", None, [], wsl_dxg=True
                )
            finally:
                if original is None:
                    MODULE.os.environ.pop("HSA_ENABLE_DXG_DETECTION", None)
                else:
                    MODULE.os.environ["HSA_ENABLE_DXG_DETECTION"] = original
        self.assertNotIn("HSA_ENABLE_DXG_DETECTION", default)
        self.assertEqual(enabled["HSA_ENABLE_DXG_DETECTION"], "1")

    def test_wsl_dxg_rejects_wrong_backend_and_non_device(self) -> None:
        with self.assertRaisesRegex(MODULE.MatrixError, "HIP backend"):
            MODULE.validate_wsl_dxg("cuda", True, platform_name="posix")
        with tempfile.TemporaryDirectory() as temporary:
            fake_device = Path(temporary) / "dxg"
            fake_device.write_bytes(b"not a device")
            with self.assertRaisesRegex(MODULE.MatrixError, "character device"):
                MODULE.validate_wsl_dxg(
                    "hip",
                    True,
                    dxg_path=fake_device,
                    platform_name="posix",
                    os_release="microsoft-standard-WSL2",
                )

    def test_wsl_dxg_rejects_non_wsl_kernel(self) -> None:
        with self.assertRaisesRegex(MODULE.MatrixError, "verified WSL kernel"):
            MODULE.validate_wsl_dxg(
                "hip", True, platform_name="posix", os_release="generic-linux"
            )

    def test_summary_refuses_predictable_temporary_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(strict=True)
            output = root / "result.json"
            collision = root / f".{output.name}.{MODULE.os.getpid()}.tmp"
            collision.write_text("do not overwrite", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.MatrixError, "safely"):
                MODULE.write_summary(output, {"status": "pass"})
            self.assertEqual(collision.read_text(encoding="utf-8"), "do not overwrite")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
