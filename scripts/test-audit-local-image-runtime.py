#!/usr/bin/env python3
"""Security and behavior tests for the offline image-runtime license audit."""

from __future__ import annotations

import importlib.util
import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


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

    def test_duplicate_contract_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            raw = CONTRACT.read_text(encoding="utf-8").replace(
                '"schemaVersion": 1,', '"schemaVersion": 1, "schemaVersion": 1,', 1
            )
            hostile = base / "contract.json"
            hostile.write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(MODULE.AuditError, "duplicate-contract-key"):
                MODULE.audit(Args(runtime, base / "report.json", contract=hostile))

    def test_ambiguous_distribution_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            add_dist(runtime, "sample", "1.0")
            metadata = runtime / "sample-1.0.dist-info" / "METADATA"
            metadata.write_text(
                "Name: sample\nName: substituted\nVersion: 1.0\nLicense-Expression: MIT\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(MODULE.AuditError, "ambiguous-distribution-metadata"):
                MODULE.audit(Args(runtime, base / "report.json"))

    def test_metadata_and_license_size_limits_are_enforced(self):
        for limit_name, expected in (
            ("maxMetadataBytes", "maximum-metadata-size-exceeded"),
            ("maxLicenseBytes", "maximum-license-size-exceeded"),
        ):
            with self.subTest(limit_name=limit_name), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                runtime = base / "runtime"
                runtime.mkdir()
                add_dist(runtime, "sample", "1.0")
                contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
                contract["limits"][limit_name] = 8
                hostile = base / "contract.json"
                hostile.write_text(json.dumps(contract), encoding="utf-8")
                with self.assertRaisesRegex(MODULE.AuditError, expected):
                    MODULE.audit(Args(runtime, base / "report.json", contract=hostile))

    def test_distribution_license_file_count_ceiling_is_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            dist = runtime / "sample-1.0.dist-info"
            licenses = dist / "licenses"
            licenses.mkdir(parents=True)
            (dist / "METADATA").write_text(
                "Name: sample\nVersion: 1.0\nLicense-Expression: MIT\n",
                encoding="utf-8",
            )
            for index in range(110):
                (licenses / f"LICENSE-{index:03}.txt").write_text(
                    "license\n", encoding="utf-8"
                )
            with self.assertRaisesRegex(
                MODULE.AuditError, "maximum-license-file-count-exceeded"
            ):
                MODULE.audit(Args(runtime, base / "report.json"))

    def test_depth_and_file_count_limits_are_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            (runtime / "one" / "two").mkdir(parents=True)
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["limits"]["maxDepth"] = 1
            hostile = base / "contract.json"
            hostile.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.AuditError, "maximum-depth-exceeded"):
                MODULE.audit(Args(runtime, base / "report.json", contract=hostile))
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            (runtime / "one.txt").write_text("one", encoding="utf-8")
            (runtime / "two.txt").write_text("two", encoding="utf-8")
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["limits"]["maxFiles"] = 1
            hostile = base / "contract.json"
            hostile.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.AuditError, "maximum-file-count-exceeded"):
                MODULE.audit(Args(runtime, base / "report.json", contract=hostile))

    @unittest.skipUnless(os.name == "nt", "Windows extended-length path behavior")
    def test_windows_extended_length_runtime_is_scanned(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            extended_runtime = MODULE.runtime_filesystem_root(runtime.resolve(strict=True))
            deep = extended_runtime / ("a" * 180) / ("b" * 80)
            deep.mkdir(parents=True)
            license_file = deep / "LICENSE.txt"
            license_file.write_text("long path license\n", encoding="utf-8")
            report = MODULE.audit(Args(runtime, base / "report.json"))
            self.assertEqual(report["scope"]["regularFileCount"], 1)
            self.assertEqual(len(report["globalLicenseEvidence"]), 1)
            self.assertEqual(
                report["globalLicenseEvidence"][0]["relativePath"],
                f'{"a" * 180}/{"b" * 80}/LICENSE.txt',
            )
            # Python's normal TemporaryDirectory cleanup can miss children over
            # MAX_PATH even when the audit correctly used Win32 extended paths.
            # Remove only the exact test-created entries through those same
            # extended paths so this native security regression stays reliable.
            license_file.unlink()
            deep.rmdir()
            deep.parent.rmdir()
            self.assertFalse(license_file.exists())

    def test_reparse_detection_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            marker = runtime / "marker.txt"
            marker.write_text("marker", encoding="utf-8")
            original = MODULE.is_link_or_reparse

            def flagged(path, info):
                return path.name == marker.name or original(path, info)

            with mock.patch.object(MODULE, "is_link_or_reparse", side_effect=flagged):
                with self.assertRaisesRegex(MODULE.AuditError, "link-entry-rejected"):
                    MODULE.audit(Args(runtime, base / "report.json"))

    def test_unsafe_and_reserved_names_are_redacted(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            self.assertTrue(MODULE.safe_relative(runtime / "safe.txt", runtime) == "safe.txt")
            for name in ("CON", "NUL.txt", "trailing.", "unicode-\N{SNOWMAN}.txt"):
                with self.subTest(name=name):
                    self.assertTrue(
                        MODULE.safe_relative(runtime / name, runtime).startswith("redacted-unsafe-name/")
                    )

    def test_embedded_runtime_ownership_accepts_only_admitted_root_shapes(self):
        accepted = (
            ("python_embeded", "python.exe"),
            ("python_embeded", "DLLs", "_ssl.pyd"),
            ("ComfyUI_windows_portable", "python_embeded", "python.exe"),
        )
        rejected = (
            ("python_embeded",),
            ("python-embedded", "python.exe"),
            ("other", "python_embeded", "python.exe"),
            ("ComfyUI_windows_portable", "python_embeded-malicious", "python.exe"),
            ("comfyui_windows_portable", "python_embeded", "python.exe"),
        )
        for parts in accepted:
            with self.subTest(parts=parts):
                self.assertTrue(MODULE.is_contracted_embedded_runtime_path(parts))
        for parts in rejected:
            with self.subTest(parts=parts):
                self.assertFalse(MODULE.is_contracted_embedded_runtime_path(parts))

    def test_duplicate_distributions_are_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            add_dist(runtime, "sample-pkg", "1.0")
            add_dist(runtime, "sample_pkg", "1.0")
            report = MODULE.audit(Args(runtime, base / "report.json"))
            self.assertTrue(all("duplicate-distribution" in item["blockers"] for item in report["distributions"]))

    def test_case_collisions_are_rejected_portably(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            with self.assertRaisesRegex(MODULE.AuditError, "case-collision-rejected"):
                MODULE.reject_case_collisions(
                    [runtime / "Case.txt", runtime / "case.txt"], runtime
                )

    def test_archive_substitution_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            archive = base / "runtime.zip"
            archive.write_bytes(b"expected")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["profiles"][PROFILE]["archiveSha256"] = digest
            local_contract = base / "contract.json"
            local_contract.write_text(json.dumps(contract), encoding="utf-8")
            archive.write_bytes(b"substituted")
            with self.assertRaisesRegex(MODULE.AuditError, "archive-digest-mismatch"):
                MODULE.audit(
                    Args(
                        runtime,
                        base / "report.json",
                        digest=digest,
                        archive=archive,
                        contract=local_contract,
                    )
                )

    def test_windows_record_backslashes_are_normalized_narrowly(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            add_dist(runtime, "sample", "1.0")
            native = runtime / "sample" / "native.dll"
            native.parent.mkdir()
            native.write_bytes(b"MZ windows record")
            digest = hashlib.sha256(native.read_bytes()).digest()
            encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
            (runtime / "sample-1.0.dist-info" / "RECORD").write_text(
                f"sample\\native.dll,sha256={encoded},{native.stat().st_size}\n",
                encoding="utf-8",
            )
            report = MODULE.audit(Args(runtime, base / "report.json"))
            owners = report["nativeArtifacts"][0]["owners"]
            self.assertEqual(owners[0]["distribution"], "sample")
            self.assertTrue(owners[0]["recordSha256Matches"])

    def test_hostile_windows_record_paths_are_rejected(self):
        hostile = (
            "mixed/path\\value.dll",
            "\\\\server\\share\\value.dll",
            "C:\\value.dll",
            "double\\\\value.dll",
            "parent\\..\\value.dll",
            "stream:alternate.dll",
            "control\\value\x01.dll",
        )
        for value in hostile:
            with self.subTest(value=value), self.assertRaisesRegex(
                MODULE.AuditError, "invalid-record-row"
            ):
                MODULE.record_path_parts(value, allow_windows_separators=True)
        with self.assertRaisesRegex(MODULE.AuditError, "invalid-record-row"):
            MODULE.record_path_parts(
                "windows\\value.dll", allow_windows_separators=False
            )

    def test_output_location_attacks_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runtime = base / "runtime"
            runtime.mkdir()
            with self.assertRaisesRegex(MODULE.AuditError, "output-inside-runtime-rejected"):
                MODULE.audit(Args(runtime, runtime / "report.json"))
            with self.assertRaisesRegex(MODULE.AuditError, "invalid-output-name"):
                MODULE.audit(Args(runtime, base / "CON"))
            redirected = base / "redirected"
            target = base / "target"
            target.mkdir()
            try:
                redirected.symlink_to(target, target_is_directory=True)
            except OSError:
                return
            with self.assertRaisesRegex(
                MODULE.AuditError, "output-parent-(?:link|redirect)-rejected"
            ):
                MODULE.audit(Args(runtime, redirected / "report.json"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"Local image runtime license audit passed {result.testsRun} fail-closed checks.")
