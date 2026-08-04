#!/usr/bin/env python3
"""Static safety tests for approved public-repository candidates."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-public-repository-candidate.py"
SPEC = importlib.util.spec_from_file_location("public_candidate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CATALOG = ROOT / "config" / "public-repository-validation-candidates.json"


class PublicCandidateTests(unittest.TestCase):
    def test_catalog_is_exact_and_non_authorizing(self):
        catalog = MODULE.load_catalog()
        self.assertEqual(len(catalog["candidates"]), 3)
        self.assertFalse(any(catalog["execution"].values()))
        self.assertFalse(any(catalog["authority"].values()))

    def test_catalog_rejects_network_or_execution_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            contract = json.loads(CATALOG.read_text(encoding="utf-8"))
            contract["execution"]["targetCodeExecutionAllowed"] = True
            path = Path(temporary) / "catalog.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.PublicRepositoryError, "unsafe-public-repository-catalog"):
                MODULE.load_catalog(path)

    def test_catalog_rejects_mutable_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            contract = json.loads(CATALOG.read_text(encoding="utf-8"))
            contract["candidates"][0]["commit"] = "main"
            path = Path(temporary) / "catalog.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.PublicRepositoryError, "invalid-public-repository-identity"):
                MODULE.load_catalog(path)

    def test_repository_outside_ignored_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve()
            with self.assertRaisesRegex(MODULE.PublicRepositoryError, "repository-outside-review-root"):
                MODULE._safe_repository(path)

    def test_bare_config_include_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").write_text("[include]\npath = outside\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.PublicRepositoryError, "bare-repository-config-rejected"):
                MODULE._validate_bare_control(root)

    def test_object_alternate_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "objects" / "info").mkdir(parents=True)
            (root / "objects" / "info" / "alternates").write_text("outside\n", encoding="utf-8")
            (root / "config").write_text("[core]\nbare = true\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.PublicRepositoryError, "bare-repository-alternate-rejected"):
                MODULE._validate_bare_control(root)

    def test_exact_origin_tag_object_type_and_commit_are_required(self):
        candidate = MODULE.load_catalog()["candidates"][0]
        values = [
            (candidate["repository"] + "\n").encode(),
            (candidate["tagObject"] + "\n").encode(),
            b"tag\n",
            (candidate["commit"] + "\n").encode(),
        ]
        with patch.object(MODULE, "_git", side_effect=values):
            self.assertEqual(MODULE._validate_identity(candidate, Path("unused")), candidate["commit"])

    def test_mutable_or_wrong_origin_identity_is_rejected(self):
        candidate = MODULE.load_catalog()["candidates"][0]
        values = [
            b"https://attacker.example/repository.git\n",
            (candidate["tagObject"] + "\n").encode(),
            b"tag\n",
            (candidate["commit"] + "\n").encode(),
        ]
        with patch.object(MODULE, "_git", side_effect=values):
            with self.assertRaisesRegex(MODULE.PublicRepositoryError, "public-repository-identity-mismatch"):
                MODULE._validate_identity(candidate, Path("unused"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PublicCandidateTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"Public repository candidates passed {result.testsRun} fail-closed checks.")
