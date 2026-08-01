#!/usr/bin/env python3
"""Lifecycle security tests for the live provider-conformance harness."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "test-provider-conformance.py"
SPEC = importlib.util.spec_from_file_location("provider_conformance", TARGET)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProviderConformanceSecurityTests(unittest.TestCase):
    def test_best_effort_unload_uses_zero_keep_alive(self) -> None:
        with mock.patch.object(MODULE, "request_json", return_value=({}, 0)) as request:
            self.assertTrue(MODULE.best_effort_unload("http://loopback.invalid", "fixture"))
        request.assert_called_once_with(
            "http://loopback.invalid",
            "/api/generate",
            {"model": "fixture", "keep_alive": 0},
            timeout=30,
        )

    def test_best_effort_unload_does_not_mask_original_failure(self) -> None:
        with mock.patch.object(MODULE, "request_json", side_effect=TimeoutError):
            self.assertFalse(MODULE.best_effort_unload("http://loopback.invalid", "fixture"))

    def test_main_has_finally_cleanup(self) -> None:
        source = TARGET.read_text(encoding="utf-8")
        self.assertIn("finally:\n        if args.unload:", source)
        self.assertIn("best_effort_unload(args.base_url, args.model)", source)


if __name__ == "__main__":
    unittest.main()
