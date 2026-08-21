#!/usr/bin/env python3
"""Hostile tests for the synthetic temporary conversation database."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest import mock
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-conversation-history-development.py"
SPEC = importlib.util.spec_from_file_location("history_development", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT = ROOT / "config" / "conversation-history-development-contract.json"


class DevelopmentHistoryTests(unittest.TestCase):
    def test_synthetic_database_is_verified_and_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            result = MODULE.validate_in_temporary_directory(directory)
            self.assertEqual(result["status"], "synthetic-temporary-validation-passed")
            self.assertTrue(result["checks"]["residueFree"])
            self.assertFalse(any(result["authority"].values()))
            self.assertEqual(list(directory.iterdir()), [])

    def test_preexisting_content_is_rejected_without_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            marker = directory / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.DevelopmentHistoryError, "temporary-directory-not-empty"):
                MODULE.validate_in_temporary_directory(directory)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

    def test_relative_directory_is_rejected(self):
        with self.assertRaisesRegex(MODULE.DevelopmentHistoryError, "invalid-temporary-directory"):
            MODULE.validate_in_temporary_directory(Path("relative"))

    def test_runtime_authority_cannot_be_enabled(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["authority"]["runtimeRouteAllowed"] = True
            path = directory / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            work = directory / "work"
            work.mkdir()
            with self.assertRaisesRegex(MODULE.DevelopmentHistoryError, "unsafe-development-contract"):
                MODULE.validate_in_temporary_directory(work.resolve(), path)

    def test_preexisting_database_permission_cannot_be_enabled(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["database"]["preexistingDatabaseAllowed"] = True
            path = directory / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.DevelopmentHistoryError, "unsafe-development-contract"):
                MODULE.load_contract(path)

    def test_contract_has_no_user_or_persistence_authority(self):
        contract = MODULE.load_contract()
        self.assertFalse(contract["authority"]["userContentAllowed"])
        self.assertFalse(contract["authority"]["persistentDatabaseAllowed"])
        self.assertFalse(contract["database"]["callerPathAllowed"])

    def test_missing_extension_api_is_treated_as_fail_closed(self):
        class ConnectionWithoutExtensionApi:
            def __init__(self):
                self.statements = []

            def execute(self, statement):
                self.statements.append(statement)
                return self

        connection = ConnectionWithoutExtensionApi()
        with mock.patch.object(MODULE.sqlite3, "connect", return_value=connection):
            self.assertIs(MODULE._connect(Path("unused.sqlite3")), connection)
        self.assertIn("PRAGMA trusted_schema=OFF", connection.statements)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DevelopmentHistoryTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"Conversation history development database passed {result.testsRun} security checks.")
