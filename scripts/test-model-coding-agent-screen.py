#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("coding_screen", ROOT / "scripts/model-coding-agent-screen.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CodingAgentScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = MODULE.load_policy()

    def cell(self) -> dict:
        gates = {}
        for gate in self.policy["requiredGates"]:
            gates[gate["id"]] = {
                "status": "passed",
                "checks": {check: "passed" for check in gate["checks"]},
            }
        return {
            "schemaVersion": 1,
            "kind": "haven42-coding-agent-evidence-cell",
            "modelId": "fixture-model-q4",
            "manifestDigest": "1" * 64,
            "runtime": {"engine": "ollama", "version": "0.0.0-fixture", "artifactDigest": "2" * 64},
            "hardwareProfileId": "fixture-gpu-8g",
            "surface": {"id": "vscode-native-chat", "version": "fixture"},
            "gates": gates,
            "rawPromptsOrResponsesRetained": False,
            "privateIdentityRetained": False,
        }

    def test_complete_exact_cell_is_eligible_but_changes_no_default(self) -> None:
        result = MODULE.evaluate(self.cell(), self.policy)
        self.assertTrue(result["codingRecommendationEligible"])
        self.assertFalse(result["automaticDefaultChangeAllowed"])

    def test_missing_failed_or_inconsistent_gate_fails_closed(self) -> None:
        missing = self.cell()
        del missing["gates"]["reliability"]
        with self.assertRaisesRegex(MODULE.ScreenError, "required-gates-incomplete"):
            MODULE.evaluate(missing, self.policy)
        failed = self.cell()
        failed["gates"]["scoped-edit"]["checks"]["no-unintended-writes"] = "failed"
        failed["gates"]["scoped-edit"]["status"] = "failed"
        self.assertFalse(MODULE.evaluate(failed, self.policy)["codingRecommendationEligible"])
        inconsistent = self.cell()
        inconsistent["gates"]["tool-contract"]["checks"]["unknown-tool-refusal"] = "failed"
        with self.assertRaisesRegex(MODULE.ScreenError, "gate-summary-inconsistent"):
            MODULE.evaluate(inconsistent, self.policy)

    def test_legacy_continue_surface_is_evidence_only(self) -> None:
        cell = self.cell()
        cell["surface"] = {"id": "continue-cli", "version": "historical-fixture"}
        result = MODULE.evaluate(cell, self.policy)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["legacyEvidenceOnlySurface"])

    def test_unknown_fields_private_data_and_bad_digests_are_rejected(self) -> None:
        extra = self.cell()
        extra["endpoint"] = "private"
        with self.assertRaisesRegex(MODULE.ScreenError, "cell-shape-invalid"):
            MODULE.evaluate(extra, self.policy)
        private = self.cell()
        private["privateIdentityRetained"] = True
        with self.assertRaisesRegex(MODULE.ScreenError, "evidence-hygiene-invalid"):
            MODULE.evaluate(private, self.policy)
        digest = self.cell()
        digest["manifestDigest"] = "latest"
        with self.assertRaisesRegex(MODULE.ScreenError, "manifest-digest-invalid"):
            MODULE.evaluate(digest, self.policy)

    def test_mutated_policy_with_duplicate_gate_is_rejected(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["requiredGates"].append(copy.deepcopy(policy["requiredGates"][0]))
        with self.assertRaisesRegex(MODULE.ScreenError, "policy-gate-id-invalid"):
            MODULE.validate_policy(policy)


if __name__ == "__main__":
    unittest.main()
