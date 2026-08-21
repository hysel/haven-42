#!/usr/bin/env python3
"""Validate the Apple M4 qualification status ledger and its evidence bindings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "config" / "alpha-2-apple-m4-qualification-status.json"


class AppleM4QualificationStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = json.loads(STATUS.read_text(encoding="utf-8"))

    def test_evidence_bindings_and_open_gates(self) -> None:
        self.assertEqual(self.value["schemaVersion"], 1)
        self.assertEqual(self.value["kind"], "haven42-apple-m4-qualification-status")
        self.assertEqual(self.value["status"], "in-progress")
        self.assertFalse(self.value["complete"])
        binding_count = len(self.value["evidenceBindings"])
        self.assertIn(binding_count, {5, 14, 18})
        self.assertEqual(
            len({binding["path"] for binding in self.value["evidenceBindings"]}),
            len(self.value["evidenceBindings"]),
        )
        for binding in self.value["evidenceBindings"]:
            path = ROOT / binding["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), binding["sha256"])
        gates = self.value["gates"]
        if binding_count == 5:
            # The checked-in bootstrap ledger deliberately remains valid while
            # physical evidence is being collected. The final summarizer and
            # validator still require the expanded evidence set before this
            # qualification can be reported as complete.
            self.assertEqual(gates["longRunReliability"]["status"], "not-run")
            self.assertEqual(gates["codingAgentQualification"]["status"], "not-run")
            self.assertIn("signed-native-install", gates["updateRollbackAndUninstall"]["open"])
            return
        self.assertEqual(gates["nativeRepositoryTests"]["status"], "passed")
        self.assertGreaterEqual(gates["nativeRepositoryTests"]["checksPassed"], 80)
        self.assertRegex(gates["nativeRepositoryTests"]["sourceSnapshotSha256"], r"^[0-9a-f]{64}$")
        self.assertIn(
            "packaged-real-browser-flow",
            gates["noviceSelfContainedPackage"]["passed"],
        )
        self.assertIn(
            "bounded-attachment-flow",
            gates["uiAccessibilityAndAttachments"]["passed"],
        )
        self.assertEqual(gates["llamaCppLifecycle"]["status"], "partial-pass")
        self.assertEqual(gates["mlxLifecycle"]["status"], "partial-pass")
        self.assertIn(gates["modelCoreQualification"]["candidates"], {16, 17})
        self.assertEqual(
            gates["modelCoreQualification"]["passed"]
            + gates["modelCoreQualification"]["failed"],
            gates["modelCoreQualification"]["candidates"],
        )
        reliability = gates["longRunReliability"]
        self.assertEqual(reliability["status"], "completed")
        self.assertGreaterEqual(reliability["eligibleCandidates"], 9)
        self.assertEqual(
            reliability["passed"] + reliability["failed"],
            reliability["eligibleCandidates"],
        )
        self.assertEqual(reliability["minutesPerCandidate"], 30)
        coding = gates["codingAgentQualification"]
        self.assertEqual(coding["status"], "completed")
        self.assertEqual(coding["surface"], "opencode-cli")
        self.assertEqual(
            coding["candidates"], gates["modelCoreQualification"]["candidates"]
        )
        self.assertEqual(
            coding["passed"] + coding["failed"], coding["candidates"]
        )
        self.assertGreaterEqual(coding["eligibleForHumanReview"], 0)
        self.assertLessEqual(coding["eligibleForHumanReview"], coding["candidates"])
        self.assertFalse(gates["codingAgentQualification"]["continueEvidenceAccepted"])
        self.assertIn("synthetic-item-create-denied", gates["keychain"]["blocked"])
        self.assertEqual(gates["updateRollbackAndUninstall"]["status"], "blocked")
        self.assertIn("signed-native-install", gates["updateRollbackAndUninstall"]["open"])
        self.assertIn("partial-pass", {gate["status"] for gate in gates.values()})

    def test_no_implicit_authority_or_private_data(self) -> None:
        self.assertTrue(all(value is False for value in self.value["authority"].values()))
        self.assertTrue(all(value is False for value in self.value["privacy"].values()))
        text = STATUS.read_text(encoding="utf-8")
        compact = re.sub(r"[^a-z0-9]", "", text.lower())
        for prohibited in ("hostname", "username", "machineid", "serialnumber", "ipaddress"):
            self.assertNotIn(prohibited, compact)
        self.assertNotRegex(text, r"(?<![0-9])(?:10|192\.168|172\.(?:1[6-9]|2[0-9]|3[01]))(?:\.[0-9]{1,3}){2}(?![0-9])")


if __name__ == "__main__":
    unittest.main()
