#!/usr/bin/env python3
"""Static safety checks for the RX host-stability follow-up runner."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run-alpha2-rx5700xt-stability-followup.sh"


class StabilityFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = RUNNER.read_text(encoding="utf-8")

    def test_waits_for_last_model_followup(self) -> None:
        self.assertIn("rx5700xt-qwen35-followup.complete", self.text)

    def test_cpu_smoke_is_bounded_and_after_model_queue(self) -> None:
        self.assertIn("--duration-seconds 600 --workers 4", self.text)
        self.assertLess(self.text.index('while [[ ! -f "$PREREQUISITE" ]]'), self.text.index("--duration-seconds 600"))

    def test_refusals_do_not_download_or_execute_models(self) -> None:
        for model_id in ("qwen35-9b-q4", "gemma3-12b-q4", "gemma4-12b-qat"):
            self.assertIn(model_id, self.text)
        self.assertNotRegex(self.text, re.compile(r"\bollama\s+(pull|run|rm)\b"))
        self.assertNotIn("/api/generate", self.text)

    def test_no_private_lab_identity(self) -> None:
        for forbidden in ("192.168.", "root@", "haven42@", "known_hosts", "authorized_keys"):
            self.assertNotIn(forbidden, self.text)


if __name__ == "__main__":
    unittest.main()
