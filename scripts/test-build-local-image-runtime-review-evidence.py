#!/usr/bin/env python3
"""Hostile tests for candidate image-runtime review evidence."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "build-local-image-runtime-review-evidence.py"
SPEC = importlib.util.spec_from_file_location("image_review_evidence", TARGET)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
SHA = "a" * 64


def report() -> dict:
    return {
        "schemaVersion": 1,
        "status": "review-required",
        "profile": {
            "id": "windows-amd-comfyui-0.30.0",
            "operatingSystem": "windows",
            "accelerator": "amd-rocm",
            "provider": "ComfyUI",
            "providerVersion": "0.30.0",
            "archiveSha256": SHA,
        },
        "artifact": {"sha256": SHA, "archiveIndependentlyVerified": True},
        "distributions": [{
            "name": "sample",
            "normalizedName": "sample",
            "version": "1.0",
            "installationScope": "top-level",
            "licenseExpression": "MIT",
            "reviewedLicenseExpression": None,
            "legacyLicense": None,
            "licenseClassifiers": [],
            "licenseEvidence": [{"name": "LICENSE", "bytes": 10, "sha256": SHA}],
            "blockers": [],
        }],
        "globalLicenseEvidence": [{"relativePath": "sample/LICENSE", "bytes": 10, "sha256": SHA}],
        "nativeArtifacts": [{"relativePath": "sample/native.dll", "bytes": 20, "sha256": SHA}],
        "blockers": ["native-components-require-exact-review"],
        "decision": {
            "installationAllowed": False,
            "redistributionAllowed": False,
            "packagingAllowed": False,
            "providerPromoted": False,
        },
        "privacy": {
            "absolutePathsRecorded": False,
            "hostnamesRecorded": False,
            "usernamesRecorded": False,
            "endpointsRecorded": False,
        },
    }


class EvidenceTests(unittest.TestCase):
    def test_build_is_deterministic_and_non_admitting(self):
        first = MODULE.build(report())
        second = MODULE.build(report())
        self.assertEqual(first, second)
        summary = json.loads(first["review-summary.json"])
        self.assertFalse(summary["redistributionAllowed"])
        self.assertIn(b"not a shipping notice", first["THIRD-PARTY-NOTICES-CANDIDATE.txt"])

    def test_unverified_archive_is_rejected(self):
        value = report()
        value["artifact"]["archiveIndependentlyVerified"] = False
        with self.assertRaisesRegex(MODULE.EvidenceError, "archive-not-independently-verified"):
            MODULE.build(value)

    def test_authority_escalation_is_rejected(self):
        value = report()
        value["decision"]["packagingAllowed"] = True
        with self.assertRaisesRegex(MODULE.EvidenceError, "authority-must-remain-false"):
            MODULE.build(value)

    def test_absolute_or_traversal_native_path_is_rejected(self):
        for hostile in ("C:/secret.dll", "../secret.dll", "/secret.dll", "safe/../../secret.dll"):
            with self.subTest(hostile=hostile):
                value = report()
                value["nativeArtifacts"][0]["relativePath"] = hostile
                with self.assertRaises(MODULE.EvidenceError):
                    MODULE.build(value)

    def test_malformed_hash_is_rejected(self):
        value = report()
        value["nativeArtifacts"][0]["sha256"] = "not-a-hash"
        with self.assertRaisesRegex(MODULE.EvidenceError, "invalid-sha256"):
            MODULE.build(value)

    def test_existing_output_is_not_modified(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.EvidenceError, "output-already-exists"):
                MODULE.write_exclusive(output, MODULE.build(report()))
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

    def test_input_object_is_not_mutated(self):
        value = report()
        original = copy.deepcopy(value)
        MODULE.build(value)
        self.assertEqual(value, original)

    def test_inventory_sbom_notice_and_checksum_parity(self):
        files = MODULE.build(report())
        summary = json.loads(files["review-summary.json"])
        inventory = json.loads(files["dependency-license-inventory.json"])
        native = json.loads(files["native-file-inventory.json"])
        sbom = json.loads(files["image-runtime.cdx.json"])
        checksummed = {item["name"]: item for item in summary["files"]}
        self.assertEqual(set(checksummed), set(files) - {"review-summary.json"})
        for name, item in checksummed.items():
            self.assertEqual(item["bytes"], len(files[name]))
            self.assertEqual(item["sha256"], hashlib.sha256(files[name]).hexdigest())
        self.assertEqual(summary["distributionCount"], len(inventory["distributions"]))
        self.assertEqual(summary["nativeFileCount"], len(native["artifacts"]))
        self.assertEqual(
            len(sbom["components"]),
            summary["distributionCount"] + summary["nativeFileCount"],
        )
        notice = files["THIRD-PARTY-NOTICES-CANDIDATE.txt"].decode("utf-8")
        self.assertIn(
            f"Native files requiring exact origin/license review: {summary['nativeFileCount']}",
            notice,
        )

    def test_duplicate_report_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.json"
            path.write_text('{"schemaVersion":1,"schemaVersion":1}', encoding="utf-8")
            with self.assertRaisesRegex(MODULE.EvidenceError, "duplicate-audit-report-key"):
                MODULE.load_report(path)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"Local image runtime review evidence passed {result.testsRun} hostile checks.")
