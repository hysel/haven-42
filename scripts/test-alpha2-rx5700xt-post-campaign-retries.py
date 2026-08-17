#!/usr/bin/env python3
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PostCampaignRetryTests(unittest.TestCase):
    def test_power_retry_is_ordered_and_immutable(self) -> None:
        text = (ROOT / 'scripts/run-alpha2-rx5700xt-power-retry.sh').read_text(encoding='utf-8')
        self.assertIn('rx5700xt-stability-followup.complete', text)
        self.assertIn('rx5700xt-llama32-3b-q4-power-retry.json', text)
        self.assertIn('a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72', text)
        self.assertIn('original power record missing', text)
        self.assertNotIn('rm -f', text)

    def test_minicpm_retry_preserves_base_failure_and_waits_for_power(self) -> None:
        text = (ROOT / 'scripts/run-alpha2-rx5700xt-minicpm-extended-retry.sh').read_text(encoding='utf-8')
        self.assertIn('rx5700xt-power-retry.complete', text)
        self.assertIn('task-general.chat.json', text)
        self.assertIn('vision failure-recovery', text)
        self.assertIn('alpha2-ollama-full-residency-monitor.py', text)
        self.assertIn('--origin "$ORIGIN"', text)
        self.assertIn('--profile-id "$PROFILE"', text)
        self.assertNotIn('--qualification-profile-id', text)
        self.assertEqual(text.count('--backend vulkan'), 1)
        self.assertNotIn('rm -f', text)

    def test_no_private_lab_data(self) -> None:
        combined = ''.join((ROOT / f).read_text(encoding='utf-8') for f in (
            'scripts/run-alpha2-rx5700xt-power-retry.sh',
            'scripts/run-alpha2-rx5700xt-minicpm-extended-retry.sh',
        ))
        for forbidden in ('192.168.', 'root@', 'haven42@', 'known_hosts', 'authorized_keys'):
            self.assertNotIn(forbidden, combined)


if __name__ == '__main__':
    unittest.main()
