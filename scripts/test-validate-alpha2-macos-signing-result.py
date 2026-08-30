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


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate-alpha2-macos-signing-result.py"
SPEC = importlib.util.spec_from_file_location("validate_alpha2_macos_signing_result", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_directory(root: Path) -> tuple[Path, dict[str, object]]:
    root.mkdir()
    archive = root / MODULE.ARCHIVE_NAME
    archive.write_bytes(b"signed-notarized-stapled-archive")
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
