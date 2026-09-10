"""Validate the bounded P4000 records and fail-closed summarizer."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('summary', ROOT/'scripts/summarize-p4000-qualification.py')
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


class EvidenceTests(unittest.TestCase):
    def test_published_counts_and_digests(self):
        inventory = json.loads((ROOT/'config/alpha-2-model-version-inventory.json').read_text())
        candidates = {c['id']: c for f in inventory['families'] for v in f['versions'] for c in v.get('candidates', [])}
        for platform, count in [('windows', 699), ('ubuntu', 735)]:
            r = json.loads((ROOT/f'config/p4000-{platform}-inference-result.json').read_text())
            self.assertEqual(r['samplesPassed'], count)
            self.assertEqual(r['samplesFailed'], 0)
            self.assertEqual(r['finalUnload'], 'verified')
            self.assertEqual({m['modelId'] for m in r['models']}, set(summary.IDS))
            self.assertEqual(sum(m['coreSamplesPassed']+m['soakSamplesPassed'] for m in r['models']), count)
            for m in r['models']:
                self.assertEqual(m['manifestDigest'], candidates[m['modelId']]['manifestDigest'])
                self.assertEqual(m['coreSamplesPassed'], 9)
                self.assertGreaterEqual(m['elapsedSoakSeconds'], 1800)
            self.assertEqual(r['codingAgent'], 'not-run')
            self.assertEqual(r['nativePackageReview'], 'not-run')
            self.assertFalse(r['automaticDefaultChangeAllowed'])
            self.assertFalse(r['automaticSupportChangeAllowed'])

    def test_incomplete_run_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path/'status.json').write_text(json.dumps({'status': 'stopped', 'finalUnload': 'verified'}))
            with self.assertRaisesRegex(ValueError, 'incomplete-run'):
                summary.summarize(path, 'windows')

    def test_unexpected_models_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path/'status.json').write_text(json.dumps({'status': 'completed', 'finalUnload': 'verified', 'models': {}}))
            with self.assertRaisesRegex(ValueError, 'unexpected-model-set'):
                summary.summarize(path, 'windows')


if __name__ == '__main__':
    unittest.main()
