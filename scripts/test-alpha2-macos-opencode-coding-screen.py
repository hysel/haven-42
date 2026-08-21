#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_opencode_screen", ROOT / "scripts/alpha2-macos-opencode-coding-screen.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MacOpenCodeCodingScreenTests(unittest.TestCase):
    def test_gate_is_fail_closed(self):
        self.assertEqual(MODULE.gate({"one": "passed", "two": "passed"})["status"], "passed")
        self.assertEqual(MODULE.gate({"one": "passed", "two": "not-run"})["status"], "not-run")
        self.assertEqual(MODULE.gate({"one": "blocked", "two": "failed"})["status"], "failed")

    def test_event_stream_extracts_text_without_retaining_it_in_a_report(self):
        text, events = MODULE.parse_event_stream('\n'.join((
            json.dumps({"type": "text", "part": {"text": "README.md"}}),
            json.dumps({"type": "tool", "part": {"tool": "read", "input": {"path": "README.md"}}}),
            "not-json",
        )))
        self.assertIn("README.md", text)
        self.assertEqual(MODULE.event_tool_names(events), ["read"])

    def test_surface_config_is_loopback_and_exact_model(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            MODULE.write_surface_config(path, "model:exact", "http://127.0.0.1:11434")
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(value["model"], "ollama/model:exact")
            self.assertEqual(value["provider"]["ollama"]["options"]["baseURL"], "http://127.0.0.1:11434/v1")
            self.assertEqual(set(value["provider"]["ollama"]["models"]), {"model:exact"})

    def test_disposable_copy_drops_source_git_and_local_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / "source", root / "copy"
            source.mkdir()
            (source / "README.md").write_text("fixture\n", encoding="utf-8")
            (source / ".opencode.local.json").write_text("{}\n", encoding="utf-8")
            (source / ".git").mkdir()
            (source / ".git" / "private").write_text("do not copy\n", encoding="utf-8")
            MODULE.prepare_repository(source, destination)
            self.assertTrue((destination / "README.md").is_file())
            self.assertFalse((destination / ".opencode.local.json").exists())
            self.assertFalse((destination / ".git" / "private").exists())
            self.assertEqual(MODULE.git_output(destination, "status", "--short"), "")

    def test_resume_checkpoint_requires_exact_prefix_and_bindings(self):
        expected = {"schemaVersion": 1, "kind": "kind", "release": "release", "planCanonicalSha256": "a", "qualificationCanonicalSha256": "b", "policyCanonicalSha256": "c", "runtime": {}, "hardwareProfile": {}, "surface": {}, "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False, "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False}
        value = expected | {"status": "running", "results": [{"modelId": "one", "status": "failed"}]}
        self.assertEqual(len(MODULE.validate_resume_checkpoint(value, expected, ["one", "two"])), 1)
        value["results"][0]["modelId"] = "two"
        with self.assertRaisesRegex(MODULE.CodingScreenError, "stale-or-invalid"):
            MODULE.validate_resume_checkpoint(value, expected, ["one", "two"])


if __name__ == "__main__":
    unittest.main()
