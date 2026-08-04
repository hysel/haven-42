#!/usr/bin/env python3
"""Security tests for bounded explicit folder inspection."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "inspect-folder-selection.py"
SPEC = importlib.util.spec_from_file_location("folder_selection", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT = ROOT / "config" / "folder-selection-foundation.json"


class FolderSelectionTests(unittest.TestCase):
    def test_manifest_is_relative_content_free_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "notes.txt").write_text("hello\n", encoding="utf-8")
            (root / "data.json").write_text('{"safe": true}\n', encoding="utf-8")
            result = MODULE.inspect_selected_folder(root)
            self.assertEqual([item["relativePath"] for item in result["files"]], ["data.json", "notes.txt"])
            self.assertNotIn(str(root), json.dumps(result))
            self.assertNotIn("hello", json.dumps(result))
            self.assertFalse(any(result["authority"].values()))

    def test_recursion_requires_explicit_choice(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "sub").mkdir()
            (root / "sub" / "safe.md").write_text("safe\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.FolderSelectionError, "folder-recursion-not-approved"):
                MODULE.inspect_selected_folder(root)
            self.assertEqual(MODULE.inspect_selected_folder(root, recursive=True)["fileCount"], 1)

    def test_disguised_executable_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "malware.txt").write_bytes(b"MZ\x90\x00")
            with self.assertRaisesRegex(MODULE.FolderSelectionError, "folder-executable-content-rejected"):
                MODULE.inspect_selected_folder(root)

    def test_disguised_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "archive.txt").write_bytes(b"PK\x03\x04data")
            with self.assertRaisesRegex(MODULE.FolderSelectionError, "folder-archive-content-rejected"):
                MODULE.inspect_selected_folder(root)

    def test_unsupported_extension_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "document.pdf").write_bytes(b"%PDF-1.7")
            with self.assertRaisesRegex(MODULE.FolderSelectionError, "folder-file-type-rejected"):
                MODULE.inspect_selected_folder(root)

    def test_hidden_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / ".env").write_text("SECRET=value\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.FolderSelectionError, "folder-hidden-entry-rejected"):
                MODULE.inspect_selected_folder(root)

    def test_link_is_rejected_when_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target = root / "target.txt"
            target.write_text("safe\n", encoding="utf-8")
            try:
                (root / "link.txt").symlink_to(target)
            except OSError:
                self.skipTest("link creation unavailable")
            with self.assertRaisesRegex(MODULE.FolderSelectionError, "folder-link-rejected"):
                MODULE.inspect_selected_folder(root)

    def test_contract_cannot_enable_runtime_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["authority"]["runtimeRouteAllowed"] = True
            path = root / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.FolderSelectionError, "unsafe-folder-contract"):
                MODULE.load_contract(path)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FolderSelectionTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"Folder selection foundation passed {result.testsRun} security checks.")
