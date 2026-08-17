#!/usr/bin/env python3
"""Static fail-closed checks for Qwen 3.5 metadata activation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run-alpha2-rx5700xt-qwen35-metadata-activation.sh"


class MetadataActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = RUNNER.read_text(encoding="utf-8")

    def test_waits_for_power_and_uses_ready_marker_last(self) -> None:
        self.assertIn("rx5700xt-power-followup.complete", self.text)
        ready = self.text.index('touch "$EVIDENCE_ROOT/rx5700xt-qwen35-metadata.ready"')
        self.assertGreater(ready, self.text.index('mv "$STAGED_INVENTORY" "$INVENTORY"'))
        self.assertGreater(ready, self.text.index('mv "$STAGED_MATRIX" "$MATRIX"'))

    def test_binds_old_and_new_metadata_pairs(self) -> None:
        for digest in (
            "61f0c670f49304a20c7701c3c53fb503d90f1c0abfaac84307a57c710cdb5ac9",
            "6d45244100771b03d91fc4c9307d296ea2f18ef52441083fe8b8fba3dc6403bc",
            "76e01a821f1610bfed91e0fc6e8758b00aab4c6f5ea5715c5c572eec88309137",
            "ce61deccfc375383d48c7659e105255f7841aad1783f6960fa798354e649322d",
        ):
            self.assertIn(digest, self.text)

    def test_no_model_or_runtime_effect(self) -> None:
        for forbidden in ("ollama pull", "ollama run", "ollama rm", "/api/generate"):
            self.assertNotIn(forbidden, self.text)

    def test_no_private_lab_identity(self) -> None:
        for forbidden in ("192.168.", "root@", "haven42@", "known_hosts", "authorized_keys"):
            self.assertNotIn(forbidden, self.text)


if __name__ == "__main__":
    unittest.main()
