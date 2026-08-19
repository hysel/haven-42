#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("freshness", ROOT / "scripts/alpha2-evidence-freshness.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EvidenceFreshnessTests(unittest.TestCase):
    def binding(self, digest: str, path: str = "config/input.json") -> dict:
        return {
            "schemaVersion": 1,
            "kind": "haven42-evidence-input-binding",
            "evidenceId": "fixture-evidence",
            "inputs": [{"role": "catalog", "path": path, "hashMode": "canonical-json", "sha256": digest}],
        }

    def test_exact_canonical_json_is_fresh_despite_formatting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            value = {"b": 2, "a": 1}
            (root / "config/input.json").write_text(json.dumps(value, indent=4), encoding="utf-8")
            result = MODULE.assess(self.binding(MODULE.canonical_json_sha256(value)), root)
            self.assertEqual(result["status"], "fresh")
            self.assertFalse(result["admissionAllowed"])

    def test_changed_and_missing_inputs_are_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            (root / "config/input.json").write_text('{"a":2}', encoding="utf-8")
            changed = MODULE.assess(self.binding(MODULE.canonical_json_sha256({"a": 1})), root)
            self.assertEqual(changed["checks"][0]["status"], "changed")
            missing = MODULE.assess(self.binding("0" * 64, "config/missing.json"), root)
            self.assertEqual(missing["checks"][0]["status"], "missing")

    def test_path_escape_duplicate_roles_and_bad_digest_fail_closed(self) -> None:
        with self.assertRaisesRegex(MODULE.FreshnessError, "invalid-repository-path"):
            MODULE.assess(self.binding("0" * 64, "../secret"), ROOT)
        duplicate = self.binding("0" * 64)
        duplicate["inputs"].append(dict(duplicate["inputs"][0]))
        with self.assertRaisesRegex(MODULE.FreshnessError, "invalid-input-role"):
            MODULE.validate_binding(duplicate)
        with self.assertRaisesRegex(MODULE.FreshnessError, "invalid-input-sha256"):
            MODULE.validate_binding(self.binding("ABC"))


if __name__ == "__main__":
    unittest.main()
