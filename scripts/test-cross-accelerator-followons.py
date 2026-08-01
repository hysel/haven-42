#!/usr/bin/env python3
"""Security and parser tests for cross-accelerator follow-on cells."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-cross-accelerator-followons.py"
SPEC = importlib.util.spec_from_file_location("cross_accelerator_followons", RUNNER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FollowOnTests(unittest.TestCase):
    def test_safe_exact_patch(self) -> None:
        patch = """--- a/flag.py
+++ b/flag.py
@@ -1,2 +1,2 @@
 def enabled():
-    return False
+    return True
"""
        self.assertTrue(MODULE.patch_is_safe_and_exact(patch))

    def test_patch_rejects_traversal_and_extra_change(self) -> None:
        traversal = """--- a/../flag.py
+++ b/../flag.py
@@ -1,2 +1,2 @@
 def enabled():
-    return False
+    return True
"""
        extra = """--- a/flag.py
+++ b/flag.py
@@ -1,2 +1,2 @@
-def enabled():
-    return False
+def unsafe():
+    return True
"""
        self.assertFalse(MODULE.patch_is_safe_and_exact(traversal))
        self.assertFalse(MODULE.patch_is_safe_and_exact(extra))

    def test_context_contains_three_exact_markers(self) -> None:
        prompt = MODULE.build_context_prompt(11_000)
        self.assertGreaterEqual(len(prompt), 11_000)
        self.assertEqual(prompt.count("ALPHA-314159"), 1)
        self.assertEqual(prompt.count("BETA-271828"), 1)
        self.assertEqual(prompt.count("GAMMA-161803"), 1)

    def test_marker_line_is_exact_and_unique(self) -> None:
        self.assertTrue(MODULE.marker_line_detected("runtime banner\nHAVEN42_OK\n", "HAVEN42_OK"))
        self.assertFalse(MODULE.marker_line_detected("HAVEN42_OK extra", "HAVEN42_OK"))
        self.assertFalse(MODULE.marker_line_detected("HAVEN42_OK\nHAVEN42_OK", "HAVEN42_OK"))

    def test_ordered_markers_are_bounded_exact_and_unique(self) -> None:
        markers = ("ALPHA-314159", "BETA-271828", "GAMMA-161803")
        self.assertTrue(
            MODULE.ordered_markers_detected(
                "BEGIN ALPHA-314159; MIDDLE BETA-271828; END GAMMA-161803",
                markers,
            )
        )
        self.assertFalse(
            MODULE.ordered_markers_detected(
                "GAMMA-161803 BETA-271828 ALPHA-314159",
                markers,
            )
        )
        self.assertFalse(
            MODULE.ordered_markers_detected(
                "ALPHA-314159 BETA-271828 GAMMA-161803 ALPHA-314159",
                markers,
            )
        )

    def test_generated_png_has_expected_signature_and_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.png"
            MODULE.write_test_png(path)
            payload = path.read_bytes()
        self.assertEqual(payload[:8], b"\x89PNG\r\n\x1a\n")
        self.assertLess(len(payload), 4096)

    def test_command_forces_offline_noninteractive_execution(self) -> None:
        command = MODULE.cli_command(
            Path("llama-cli"),
            Path("model.gguf"),
            {"gpuLayers": 99},
            4096,
            Path("prompt.txt"),
            None,
        )
        self.assertIn("--offline", command)
        self.assertIn("--single-turn", command)
        self.assertIn("--simple-io", command)
        self.assertIn("--reasoning-budget", command)
        self.assertNotIn("--url", command)

    def test_source_has_no_listener_or_shell_execution(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("llama-server", source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib", source)
        self.assertNotIn('"stdout":', source)
        self.assertNotIn('"stderr":', source)
        self.assertIn('"boundedMarkerPromotesQuality": False', source)


if __name__ == "__main__":
    unittest.main()
