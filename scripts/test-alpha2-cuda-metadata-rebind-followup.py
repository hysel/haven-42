#!/usr/bin/env python3
"""Static safety checks for the CUDA metadata-rebind handoff."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-alpha2-cuda-metadata-rebind-followup.sh"


class MetadataRebindFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_waits_for_primary_campaign_and_pins_identity(self) -> None:
        self.assertIn("cuda-new-model-campaign.complete", self.source)
        self.assertIn("qwen3.6:35b-a3b-q4_K_M", self.source)
        self.assertIn("07d35212591fc27746", self.source)
        self.assertIn("EXPECTED_INVENTORY_SHA", self.source)

    def test_preserves_prior_evidence_and_uses_atomic_replacement(self) -> None:
        self.assertIn("metadata-history/qwen36-35b-release-expansion", self.source)
        self.assertIn("cp --preserve=mode,timestamps", self.source)
        self.assertIn('mv -- "$temporary_root/$capability.json" "$destination"', self.source)

    def test_does_not_download_or_remove_a_model(self) -> None:
        self.assertNotIn("ollama pull", self.source)
        self.assertNotIn("ollama rm", self.source)
        self.assertNotIn("qm ", self.source)
        self.assertNotIn("pct ", self.source)

    def test_hands_off_only_after_privacy_and_hash_checks(self) -> None:
        self.assertIn("containsPrivateMachineIdentity", self.source)
        self.assertIn("containsRawPromptsOrResponses", self.source)
        self.assertIn('exec bash "$NEXT_SCRIPT" "$BASE"', self.source)


if __name__ == "__main__":
    unittest.main()
