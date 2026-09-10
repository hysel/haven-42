"""Check published hardware evidence without inferring untested capabilities."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EvidenceTests(unittest.TestCase):
    def test_all_model_digests_and_counts(self):
        inventory = json.loads((ROOT/'config/alpha-2-model-version-inventory.json').read_text())
        expected = {c['id']: c['manifestDigest'] for f in inventory['families'] for v in f['versions'] for c in v.get('candidates', [])}
        for gpu, totals in [('p4000', (699, 735)), ('rtx4060', (717, 717))]:
            for os, total in zip(('windows', 'ubuntu'), totals):
                r = json.loads((ROOT/f'config/{gpu}-{os}-inference-result.json').read_text())
                self.assertEqual(r['samplesPassed'], total)
                self.assertEqual(r['samplesFailed'], 0)
                self.assertEqual(r['finalUnload'], 'verified')
                self.assertEqual(sum(m['coreSamplesPassed']+m['soakSamplesPassed'] for m in r['models']), total)
                self.assertEqual(len(r['models']), 5)
                for model in r['models']:
                    self.assertEqual(model['manifestDigest'], expected[model['modelId']])
                    self.assertEqual(model['coreSamplesPassed'], 9)
                    self.assertGreaterEqual(model['elapsedSoakSeconds'], 1800)
                self.assertEqual(r['codingAgent'], 'not-run')
                self.assertEqual(r['nativePackageReview'], 'not-run')
                if gpu == 'rtx4060':
                    self.assertEqual(r['telemetry']['powerW']['samples'], 0)
                    self.assertIsNone(r['telemetry']['powerW']['arithmeticMean'])

    def test_5050_limitations_and_source_bindings(self):
        r = json.loads((ROOT/'config/rtx5050-inference-result.json').read_text())
        self.assertEqual(r['windowsFirstController']['finalUnload'], 'unverified')
        self.assertEqual(r['profiles'][0]['finalUnload'], 'verified-resumed-controller-only')
        self.assertEqual(r['ubuntuPackage']['managedSetup'], 'not-completed')
        self.assertEqual(r['ubuntuPackage']['packagedInference'], 'not-run')
        self.assertEqual(r['codingAgent'], 'not-run')
        self.assertFalse(r['automaticPromotionAllowed'])
        for profile, total in zip(r['profiles'], (720, 738)):
            self.assertEqual(profile['coreSamplesPassed']+profile['soakSamplesPassed'], total)
            for m in profile['models']:
                self.assertEqual(m['coreSamplesPassed'], m['coreUnloadProofs'])
                self.assertEqual(m['soakSamplesPassed'], m['soakUnloadProofs'])
        first = r['profiles'][0]['models'][0]
        self.assertEqual(first['recordedLastSampleElapsedSeconds'], 1783.88)
        self.assertAlmostEqual(first['reconstructedProbeIntervalSeconds'], 1800.003349)
        self.assertNotIn('soakSeconds', first)

    def test_summarizers_reject_stopped_runs(self):
        for gpu in ('p4000', 'rtx4060'):
            spec = importlib.util.spec_from_file_location(gpu, ROOT/f'scripts/summarize-{gpu}-qualification.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root/'status.json').write_text('{"status":"stopped","finalUnload":"verified"}')
                with self.assertRaisesRegex(ValueError, 'incomplete-run'):
                    mod.summarize(root, 'windows')


if __name__ == '__main__':
    unittest.main()
