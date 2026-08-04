#!/usr/bin/env python3
"""Security and behavior tests for the offline image-runtime license audit."""

from __future__ import annotations

import importlib.util
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit-local-image-runtime.py"
SPEC = importlib.util.spec_from_file_location("image_runtime_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT = ROOT / "config" / "local-image-runtime-license-contract.json"
PROFILE = "windows-amd-comfyui-0.30.0"
DIGEST = "0f3816fa1149e5a739e4d095d7733bc4ea28b02c8872fadeb8f73b933b141568"


class Args:
    def __init__(self, runtime: Path, output: Path, *, digest: str = DIGEST, archive: Path | None = None, contract: Path = CONTRACT):
        self.runtime = runtime
        self.output = output
        self.profile = PROFILE
        self.artifact_sha256 = digest
        self.archive = archive
        self.contract = contract


def add_dist(root: Path, name: str, version: str, license_expression: str | None = "MIT") -> None:
    dist = root / f"{name}-{version}.dist-info"
    (dist / "licenses").mkdir(parents=True)
    lines = [f"Name: {name}", f"Version: {version}"]
    if license_expression is not None:
        lines.append(f"License-Expression: {license_expression}")
    (dist / "METADATA").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (dist / "licenses" / "LICENSE.txt").write_text("sample license\n", encoding="utf-8")


class AuditTests(unittest.TestCase):
    def test_inventory_is_fail_closed_and_path_free(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            add_dist(runtime, "sample", "1.0")
            (runtime / "native.dll").write_bytes(b"MZ sample")
            digest = hashlib.sha256(b"MZ sample").digest()
            encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
            (runtime / "sample-1.0.dist-info" / "RECORD").write_text(
                f"native.dll,sha256={encoded},9\n", encoding="utf-8"
            )
            output = base / "report.json"
            report = MODULE.audit(Args(runtime, output))
            self.assertEqual(report["status"], "review-required")
            self.assertIn("archive-not-independently-verified", report["blockers"])
            self.assertIn("native-components-require-exact-review", report["blockers"])
            self.assertEqual(report["nativeArtifacts"][0]["sha256"], "3539755a2d5519b82829cab55517a070e15d31ecb0a98f8d58091d7e44399e54")
            self.assertEqual(report["nativeArtifacts"][0]["owners"][0]["distribution"], "sample")
            self.assertTrue(report["nativeArtifacts"][0]["owners"][0]["recordSha256Matches"])
            serialized = output.read_text(encoding="utf-8")
            self.assertNotIn(str(runtime), serialized)
            self.assertEqual(json.loads(serialized)["decision"]["redistributionAllowed"], False)

    def test_missing_license_metadata_is_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            add_dist(runtime, "sample", "1.0", None)
            report = MODULE.audit(Args(runtime, base / "report.json"))
            self.assertIn("license-metadata-missing", report["blockers"])

    def test_empty_distribution_inventory_is_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            report = MODULE.audit(Args(runtime, base / "report.json"))
            self.assertIn("distribution-inventory-empty", report["blockers"])

    def test_dist_info_without_metadata_is_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            (runtime / "broken-1.0.dist-info").mkdir(parents=True)
            report = MODULE.audit(Args(runtime, base / "report.json"))
            self.assertIn("distribution-metadata-missing", report["blockers"])

    def test_wrong_digest_is_rejected_before_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            with self.assertRaisesRegex(MODULE.AuditError, "artifact-digest-not-contracted"):
                MODULE.audit(Args(runtime, base / "report.json", digest="0" * 64))

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            output = base / "report.json"
            output.write_text("keep\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.AuditError, "output-already-exists"):
                MODULE.audit(Args(runtime, output))
            self.assertEqual(output.read_text(encoding="utf-8"), "keep\n")

    def test_link_entry_is_rejected_when_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            target = base / "outside.txt"
            target.write_text("outside\n", encoding="utf-8")
            link = runtime / "linked.txt"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("link creation is unavailable on this host")
            with self.assertRaisesRegex(MODULE.AuditError, "link-entry-rejected"):
                MODULE.audit(Args(runtime, base / "report.json"))

    def test_hostile_contract_cannot_disable_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["limits"]["maxFiles"] = 10**12
            hostile = base / "contract.json"
            hostile.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.AuditError, "invalid-contract-limits"):
                MODULE.audit(Args(runtime, base / "report.json", contract=hostile))

    def test_malformed_reviewed_license_override_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["reviewedDistributionLicenses"]["unsafe identity"] = {
                "licenseExpression": "MIT",
                "packagedLicenseSha256": "0" * 64,
                "reviewStatus": "reviewed",
            }
            hostile = base / "contract.json"
            hostile.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.AuditError, "invalid-license-overrides"):
                MODULE.audit(Args(runtime, base / "report.json", contract=hostile))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"Local image runtime license audit passed {result.testsRun} fail-closed checks.")
