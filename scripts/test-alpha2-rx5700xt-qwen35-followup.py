#!/usr/bin/env python3
"""Static safety checks for the RX Qwen 3.5 follow-up."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-alpha2-rx5700xt-qwen35-followup.sh"


class Qwen35FollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_exact_three_model_ladder_is_pinned(self) -> None:
        for model_id in ("qwen35-08b-q8", "qwen35-2b-q8", "qwen35-4b-q4"):
            self.assertIn(model_id, self.source)
        for digest in ("f3817196d142eaf7", "324d162be6ca5629", "2a654d98e6fba55d"):
            self.assertIn(digest, self.source)

    def test_waits_for_power_and_verified_metadata(self) -> None:
        self.assertIn("rx5700xt-power-followup.complete", self.source)
        self.assertIn("rx5700xt-qwen35-metadata.ready", self.source)
        self.assertIn("EXPECTED_INVENTORY_SHA", self.source)

    def test_uses_fail_closed_vulkan_qualification_and_soak(self) -> None:
        self.assertIn("alpha2-model-task-qualification.py", self.source)
        self.assertIn("alpha2-linux-soak.py", self.source)
        self.assertIn("--backend vulkan", self.source)
        self.assertIn("qualificationInventoryCanonicalSha256", self.source)

    def test_scope_excludes_infrastructure_and_policy_changes(self) -> None:
        self.assertNotIn("qm ", self.source)
        self.assertNotIn("pct ", self.source)
        self.assertNotIn("hostpci", self.source)
        self.assertNotIn("automaticPromotionAllowed\":true", self.source)


if __name__ == "__main__":
    unittest.main()
