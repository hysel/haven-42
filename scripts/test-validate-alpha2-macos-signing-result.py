#!/usr/bin/env python3
"""Hostile tests for the sanitized macOS signing-result validator."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate-alpha2-macos-signing-result.py"
RECORDED_RESULT = ROOT / "config" / "alpha-2-apple-m4-signing-notarization-result.json"
SPEC = importlib.util.spec_from_file_location("validate_alpha2_macos_signing_result", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_directory(root: Path) -> tuple[Path, dict[str, object]]:
    root.mkdir()
    archive = root / MODULE.ARCHIVE_NAME
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        output.writestr("Haven42/", b"")
        output.writestr("Haven42/Haven 42.app/", b"")
        output.writestr("Haven42/Haven 42.app/Contents/Info.plist", b"signed-notarized-stapled-app")
        output.writestr("Haven42/Haven42-Data/", b"")
        output.writestr("Haven42/Haven42-Logs/", b"")
    value: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-macos-developer-id-notarization-result",
        "release": "0.4.0-alpha.2",
        "observedAtUtc": "2026-08-30T03:00:00Z",
        "status": "passed",
        "source": {
            "unsignedArtifactSha256": "1" * 64,
            "buildEvidenceSha256": "2" * 64,
            "appInventoryCanonicalSha256": "3" * 64,
        },
        "artifact": {
            "name": MODULE.ARCHIVE_NAME,
            "sha256": sha256(archive),
            "sizeBytes": archive.stat().st_size,
        },
        "platformTrust": {
            "developerIdSigned": True,
            "hardenedRuntime": True,
            "notarized": True,
            "ticketStapled": True,
            "gatekeeperAdmittedOnTestHost": True,
        },
        "privacy": {
            "certificateIdentityRetained": False,
            "teamIdentifierRetained": False,
            "notaryProfileRetained": False,
            "notaryCredentialRetained": False,
            "rawToolOutputRetained": False,
        },
        "authority": {
            "automaticUpdateActivationGranted": False,
            "releasePublicationGranted": False,
        },
    }
    write(root, value)
    return root, value


def write(root: Path, value: dict[str, object]) -> None:
    evidence = root / MODULE.EVIDENCE_NAME
    evidence.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    archive = root / MODULE.ARCHIVE_NAME
    (root / "SHA256SUMS").write_text(
        f"{sha256(archive)}  {archive.name}\n{sha256(evidence)}  {evidence.name}\n",
        encoding="ascii",
    )


class ValidatorTests(unittest.TestCase):
    def test_recorded_physical_result_is_sanitized_and_non_authorizing(self) -> None:
        encoded = RECORDED_RESULT.read_text(encoding="utf-8")
        value = json.loads(encoded)
        self.assertEqual(value["kind"], "haven42-sanitized-macos-developer-id-notarization-result")
        self.assertEqual(value["release"], "0.4.0-alpha.2")
        self.assertEqual(value["status"], "passed")
        self.assertEqual(value["platformTrust"], {
            "developerIdSigned": True,
            "gatekeeperAdmittedOnTestHost": True,
            "hardenedRuntime": True,
            "notarized": True,
            "ticketStapled": True,
        })
        self.assertEqual(value["privacy"], {
            "certificateIdentityRetained": False,
            "notaryCredentialRetained": False,
            "notaryProfileRetained": False,
            "rawToolOutputRetained": False,
            "teamIdentifierRetained": False,
        })
        self.assertEqual(value["authority"], {
            "automaticUpdateActivationGranted": False,
            "releasePublicationGranted": False,
        })
        for forbidden in ("/Users/", "Developer ID Application:", "haven42-alpha2-notary", "192.168."):
            self.assertNotIn(forbidden, encoded)

    def test_exact_sanitized_result_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, value = result_directory(Path(temporary) / "result")
            self.assertEqual(MODULE.validate(root), value)

    def test_artifact_tampering_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = result_directory(Path(temporary) / "result")
            (root / MODULE.ARCHIVE_NAME).write_bytes(b"changed")
            with self.assertRaisesRegex(MODULE.ValidationError, "artifact-record-mismatch"):
                MODULE.validate(root)

    def test_archive_requires_one_visible_haven42_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, value = result_directory(Path(temporary) / "result")
            archive = root / MODULE.ARCHIVE_NAME
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                output.writestr("Haven42-0.4.0-alpha.2/Haven 42.app/", b"")
                output.writestr(
                    "Haven42-0.4.0-alpha.2/Haven 42.app/Contents/Info.plist",
                    b"wrapped-app",
                )
            value["artifact"]["sha256"] = sha256(archive)
            value["artifact"]["sizeBytes"] = archive.stat().st_size
            write(root, value)
            with self.assertRaisesRegex(
                MODULE.ValidationError, "artifact-visible-layout-invalid",
            ):
                MODULE.validate(root)

    def test_privacy_or_authority_overstatement_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, original = result_directory(Path(temporary) / "result")
            value = copy.deepcopy(original)
            value["privacy"]["notaryProfileRetained"] = True
            write(root, value)
            with self.assertRaisesRegex(MODULE.ValidationError, "privacy-boundary-invalid"):
                MODULE.validate(root)
            value = copy.deepcopy(original)
            value["authority"]["releasePublicationGranted"] = True
            write(root, value)
            with self.assertRaisesRegex(MODULE.ValidationError, "authority-overstated"):
                MODULE.validate(root)

    def test_extra_file_or_checksum_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = result_directory(Path(temporary) / "result")
            (root / "raw-notary-output.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "unexpected-result-entry"):
                MODULE.validate(root)
            (root / "raw-notary-output.json").unlink()
            (root / "SHA256SUMS").write_text("0" * 64 + f"  {MODULE.ARCHIVE_NAME}\n", encoding="ascii")
            with self.assertRaisesRegex(MODULE.ValidationError, "checksum-manifest-mismatch"):
                MODULE.validate(root)


if __name__ == "__main__":
    unittest.main()
