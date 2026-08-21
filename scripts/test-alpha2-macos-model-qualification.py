#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADDENDUM_PLAN = ROOT / "config/alpha-2-apple-silicon-16gib-gemma4-12b-addendum-plan.json"
SPEC = importlib.util.spec_from_file_location(
    "mac_model_qualification", ROOT / "scripts/alpha2-macos-model-qualification.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MacModelQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = json.loads(MODULE.PLAN_PATH.read_text(encoding="utf-8"))

    def test_reviewed_plan_is_bound_to_inventory(self) -> None:
        candidates = MODULE.validate_plan(self.plan)
        self.assertEqual(len(candidates), 16)
        self.assertEqual(candidates["qwen35-4b-q4"]["model"], "qwen3.5:4b")

    def test_late_candidate_addendum_is_independently_bound(self) -> None:
        addendum = json.loads(ADDENDUM_PLAN.read_text(encoding="utf-8"))
        candidates = MODULE.validate_plan(addendum)
        self.assertEqual(list(candidates), ["gemma4-12b-qat"])
        self.assertEqual(candidates["gemma4-12b-qat"]["model"], "gemma4:12b-it-qat")

    def test_plan_drift_and_authority_fail_closed(self) -> None:
        drift = copy.deepcopy(self.plan)
        drift["candidates"][0]["manifestDigest"] = "0" * 64
        with self.assertRaisesRegex(MODULE.QualificationError, "inventory-mismatch"):
            MODULE.validate_plan(drift)
        authority = copy.deepcopy(self.plan)
        authority["rules"]["automaticDefaultChangeAllowed"] = True
        with self.assertRaisesRegex(MODULE.QualificationError, "invalid-plan-rules"):
            MODULE.validate_plan(authority)

    def test_only_ipv4_loopback_origin_is_admitted(self) -> None:
        self.assertEqual(MODULE.validate_origin("http://127.0.0.1:11434"), "http://127.0.0.1:11434")
        for unsafe in ("http://localhost:11434", "http://192.0.2.1:11434", "https://127.0.0.1:11434", "http://user@127.0.0.1:11434"):
            with self.assertRaisesRegex(MODULE.QualificationError, "invalid-loopback-origin"):
                MODULE.validate_origin(unsafe)

    def test_response_checks_are_strict_and_do_not_retain_content(self) -> None:
        self.assertTrue(MODULE.check_exact("MAC_CHAT_OK", "MAC_CHAT_OK"))
        self.assertFalse(MODULE.check_exact("MAC_CHAT_OK.", "MAC_CHAT_OK"))
        self.assertTrue(MODULE.check_write("Careful testing prevents small defects from becoming costly production failures.", ""))
        self.assertFalse(MODULE.check_write("Testing helps. Testing works.", ""))
        self.assertTrue(MODULE.check_summary("RUNTIME_LOCAL and MODEL_LOCAL stay beside the app for CLEAR_REMOVAL.", ""))
        self.assertFalse(MODULE.check_summary("The runtime and model stay beside the app for clear removal.", ""))

    def test_structured_json_parser_rejects_fences_and_arrays(self) -> None:
        self.assertEqual(MODULE.parse_json_object('{"path":"app/main.py","code":"pass"}')["path"], "app/main.py")
        self.assertIsNone(MODULE.parse_json_object('```json\n{"path":"app/main.py"}\n```'))
        self.assertIsNone(MODULE.parse_json_object("[]"))


if __name__ == "__main__":
    unittest.main()
