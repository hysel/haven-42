#!/usr/bin/env python3
"""Validate the committed physical-Mac portable-package evidence boundary."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "config" / "alpha-2-apple-m4-portable-package-result.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class AppleM4PackageResultTests(unittest.TestCase):
    def test_exact_evidence_boundary(self) -> None:
        value = json.loads(RESULT.read_text(encoding="utf-8"))
        self.assertEqual(value["schemaVersion"], 1)
        self.assertEqual(value["kind"], "haven42-sanitized-physical-macos-portable-package-result")
        self.assertEqual(value["release"], "0.4.0-alpha.2")
        self.assertEqual(value["status"], "partial-pass")
        datetime.strptime(value["observedAtUtc"], "%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(value["hardwareProfile"], {
            "platformFamily": "macos",
            "architecture": "arm64",
            "acceleratorFamily": "Apple M4",
            "systemMemoryGiB": 16,
        })
        self.assertTrue(HEX40.fullmatch(value["source"]["baseCommit"]))
        self.assertFalse(value["source"]["commitIsExactSource"])
        self.assertEqual(value["source"]["treeState"], "modified-uncommitted")
        self.assertTrue(HEX64.fullmatch(value["source"]["snapshotSha256"]))
        self.assertTrue(HEX64.fullmatch(value["artifact"]["sha256"]))
        self.assertEqual(value["artifact"]["kind"], "unsigned-development")
        self.assertTrue(value["artifact"]["nativeArchitectureVerified"])
        self.assertTrue(value["artifact"]["resourceIntegrityManifestEmbedded"])
        self.assertTrue(all(value["tests"].values()))
        self.assertTrue(value["platformTrust"]["codeSignatureStructureValid"])
        self.assertFalse(value["platformTrust"]["developerIdSigned"])
        self.assertFalse(value["platformTrust"]["notarized"])
        self.assertFalse(value["platformTrust"]["gatekeeperAdmitted"])
        self.assertEqual(value["platformTrust"]["gatekeeperExitCode"], 3)
        for key in (
            "privateIdentityRetained",
            "privatePathsRetained",
            "rawUserContentRetained",
            "releasePublicationAuthorized",
            "automaticUpdateAuthorized",
            "productionAdmissionGranted",
        ):
            self.assertFalse(value[key])

    def test_no_private_or_authority_fields(self) -> None:
        text = RESULT.read_text(encoding="utf-8")
        lowered = re.sub(r"[^a-z0-9]", "", text.lower())
        for prohibited in ("hostname", "username", "machineid", "serialnumber", "ipaddress", "rawprompt", "rawresponse"):
            self.assertNotIn(prohibited, lowered)
        self.assertNotRegex(text, r"(?<![0-9])(?:10|192\.168|172\.(?:1[6-9]|2[0-9]|3[01]))(?:\.[0-9]{1,3}){2}(?![0-9])")


if __name__ == "__main__":
    unittest.main()
