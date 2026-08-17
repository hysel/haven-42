#!/usr/bin/env python3
"""Tests for sanitized extended model capability qualification."""

from __future__ import annotations

import base64
import argparse
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "alpha2-model-extended-qualification.py"
SPEC = importlib.util.spec_from_file_location("extended_qualification", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExtendedQualificationTests(unittest.TestCase):
    def test_png_fixture_is_a_real_small_png(self) -> None:
        raw = base64.b64decode(MODULE._png(48, 48, (255, 0, 0)))
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        self.assertLess(len(raw), 2048)

    def test_tool_contract_accepts_one_exact_call(self) -> None:
        response = {"message": {"content": "", "tool_calls": [{
            "function": {"name": "lookup_status", "arguments": {"item": "alpha"}}
        }]}}
        with patch.object(MODULE, "_request", return_value=response):
            self.assertEqual(
                MODULE._run_capability("http://127.0.0.1:11434", "x:1", "tools"),
                {"toolCallCount": 1, "toolArgumentsValidated": True},
            )

    def test_tool_contract_rejects_extra_argument(self) -> None:
        response = {"message": {"content": "", "tool_calls": [{
            "function": {
                "name": "lookup_status",
                "arguments": {"item": "alpha", "extra": True},
            }
        }]}}
        with patch.object(MODULE, "_request", return_value=response):
            with self.assertRaisesRegex(
                MODULE.ExtendedQualificationError, "tool-call-contract-failed"
            ):
                MODULE._run_capability(
                    "http://127.0.0.1:11434", "x:1", "tools"
                )

    def test_vision_requires_two_grounded_answers(self) -> None:
        responses = [
            {"message": {"content": "RED"}},
            {"message": {"content": "BLUE"}},
        ]
        with patch.object(MODULE, "_request", side_effect=responses):
            self.assertEqual(
                MODULE._run_capability("http://127.0.0.1:11434", "x:1", "vision"),
                {"syntheticImages": 2, "groundedAnswers": 2},
            )

    def test_coding_contract_is_structural(self) -> None:
        response = {"message": {"content": (
            '{"language":"python","code":"def add(a, b):\\n    return a + b"}'
        )}}
        with patch.object(MODULE, "_request", return_value=response):
            self.assertEqual(
                MODULE._run_capability("http://127.0.0.1:11434", "x:1", "coding"),
                {"structuredOutput": True},
            )

    def test_long_context_requires_exact_three_sentinel_recall(self) -> None:
        response = {
            "response": "HAVEN42_BEGIN|HAVEN42_MIDDLE|HAVEN42_END"
        }
        with patch.object(MODULE, "_request", return_value=response) as request:
            result = MODULE._run_capability(
                "http://127.0.0.1:11434", "x:1", "long-context"
            )
        self.assertEqual(result["sentinelsRecalled"], 3)
        self.assertEqual(result["contextWindowRequested"], 16384)
        self.assertGreater(result["inputCharacters"], 30000)
        self.assertEqual(
            request.call_args.args[2]["options"]["num_ctx"], 16384
        )

    def test_review_rejects_unlisted_capability(self) -> None:
        with self.assertRaisesRegex(
            MODULE.ExtendedQualificationError, "unreviewed-capability-cell"
        ):
            MODULE._review_cell(
                "granite41-3b-q4",
                "vulkan-8gib-system-16gib",
                "vision",
            )

    def test_failed_result_keeps_sanitized_reviewed_binding(self) -> None:
        args = argparse.Namespace(
            model_id="granite41-30b-q4",
            capability="coding",
            profile_id="cuda-32gib-system-64gib",
            operating_system_id="test-linux",
            platform_family="linux",
            system_memory_gib=128.0,
            usable_gpu_memory_gib=64.0,
        )
        result = MODULE._failed_result(args, "coding-contract-failed")
        self.assertTrue(result["bindingComplete"])
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["backend"], "cuda")
        self.assertEqual(result["provider"], "ollama")
        self.assertFalse(result["containsRawPromptsOrResponses"])
        self.assertFalse(result["containsPrivateMachineIdentity"])
        self.assertFalse(result["automaticPromotionAllowed"])


if __name__ == "__main__":
    unittest.main()
