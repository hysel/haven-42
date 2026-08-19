#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("binding", ROOT / "scripts/alpha2-evidence-binding.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EvidenceBindingTests(unittest.TestCase):
    def test_generated_binding_immediately_passes_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            (root / "scripts").mkdir()
            (root / "config/catalog.json").write_text('{"b":2,"a":1}', encoding="utf-8")
            (root / "scripts/check.py").write_bytes(b"print('ok')\n")
            binding = MODULE.build_binding("fixture", [
                "catalog=canonical-json=config/catalog.json",
                "validator=file-bytes=scripts/check.py",
            ], root)
            result = MODULE.FRESHNESS.assess(binding, root)
            self.assertEqual(result["status"], "fresh")
            self.assertEqual([item["role"] for item in binding["inputs"]], ["catalog", "validator"])

    def test_duplicate_roles_path_escape_bad_mode_and_invalid_json_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "file.txt").write_text("text", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.FRESHNESS.FreshnessError, "invalid-input-role"):
                MODULE.build_binding("fixture", [
                    "same=file-bytes=file.txt", "same=file-bytes=file.txt",
                ], root)
            with self.assertRaisesRegex(MODULE.FRESHNESS.FreshnessError, "invalid-repository-path"):
                MODULE.build_binding("fixture", ["item=file-bytes=../file.txt"], root)
            with self.assertRaisesRegex(MODULE.BindingError, "unsupported hash mode"):
                MODULE.build_binding("fixture", ["item=latest=file.txt"], root)
            with self.assertRaisesRegex(MODULE.BindingError, "not valid UTF-8 JSON"):
                MODULE.build_binding("fixture", ["item=canonical-json=file.txt"], root)


if __name__ == "__main__":
    unittest.main()
