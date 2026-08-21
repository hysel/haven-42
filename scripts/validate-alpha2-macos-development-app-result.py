#!/usr/bin/env python3
"""Validate sanitized physical-Mac development-app evidence fail closed."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SHA256 = re.compile(r"[0-9a-f]{64}")
REQUIRED_TESTS = {
    "bundleStructure", "infoPlistIdentity", "exactFileInventory", "archiveParity",
    "archiveChecksums", "nativeArm64Executable", "sourcePackageParity", "relocation",
    "readOnlyStartup", "abruptExitRecovery", "repeatedLifecycle", "occupiedPortRefusal",
    "shutdownAuthority", "hostileEnvironment", "resourceIntegrity", "packagedBrowserFlow",
    "packagedBrowserChecks", "boundedAttachmentFlow", "automatedAccessibilityFlow",
    "localPrivacyBoundary",
}
REQUIRED_OPEN = {
    "developer-id-signing", "notarization", "gatekeeper-public-admission",
    "clean-machine-beginner-review", "manual-screen-reader", "manual-keyboard",
    "manual-zoom", "manual-reduced-motion",
}


class ResultError(ValueError):
    pass


def validate(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {
        "schemaVersion", "kind", "release", "observedAtUtc", "status", "hardwareProfile",
        "source", "app", "tests", "platformTrust", "open", "authority", "privacy",
    }:
        raise ResultError("result-shape-invalid")
    if (
        value["schemaVersion"] != 1
        or value["kind"] != "haven42-sanitized-physical-macos-development-app-result"
        or value["release"] != "0.4.0-alpha.2"
        or value["status"] != "partial-pass"
        or not isinstance(value["observedAtUtc"], str)
        or not value["observedAtUtc"].endswith("Z")
    ):
        raise ResultError("result-identity-invalid")
    hardware = value["hardwareProfile"]
    if hardware != {
        "profileId": "apple-m4-16gib-macos26-metal",
        "platformFamily": "macos",
        "architecture": "arm64",
        "backend": "metal",
        "systemMemoryGiB": 16,
    }:
        raise ResultError("hardware-profile-invalid")
    source = value["source"]
    if not isinstance(source, dict) or set(source) != {"repository", "commit", "treeState", "commitIsExactSource", "snapshotSha256"}:
        raise ResultError("source-identity-invalid")
    exact_source = (
        source["treeState"] == "exact-commit"
        and source["commitIsExactSource"] is True
        and source["snapshotSha256"] == ""
    )
    modified_source = (
        source["treeState"] == "modified-uncommitted"
        and source["commitIsExactSource"] is False
        and SHA256.fullmatch(str(source["snapshotSha256"])) is not None
    )
    if (
        source["repository"] != "https://github.com/hysel/haven-42"
        or re.fullmatch(r"[0-9a-f]{40}", str(source["commit"])) is None
        or not (exact_source or modified_source)
    ):
        raise ResultError("source-identity-invalid")
    app = value["app"]
    if not isinstance(app, dict) or set(app) != {
        "bundleIdentifier", "bundleShortVersion", "bundleVersion", "minimumSystemVersion",
        "archiveSha256", "portablePackageArchiveSha256", "portableBuildProvenanceSha256",
        "inventoryCanonicalSha256", "fileCount", "nativeArchitecture", "globalPythonRequired",
    }:
        raise ResultError("app-identity-invalid")
    if (
        app["bundleIdentifier"] != "org.haven42.desktop"
        or app["bundleShortVersion"] != "0.4.0"
        or app["bundleVersion"] != "0.4.2"
        or app["minimumSystemVersion"] != "13.0"
        or app["nativeArchitecture"] != "arm64"
        or app["globalPythonRequired"] is not False
        or not isinstance(app["fileCount"], int)
        or app["fileCount"] < 1
    ):
        raise ResultError("app-identity-invalid")
    if any(SHA256.fullmatch(str(app[key])) is None for key in ("archiveSha256", "portablePackageArchiveSha256", "portableBuildProvenanceSha256", "inventoryCanonicalSha256")):
        raise ResultError("artifact-digest-invalid")
    tests = value["tests"]
    if not isinstance(tests, dict) or set(tests) != REQUIRED_TESTS:
        raise ResultError("test-coverage-invalid")
    if any(tests[key] is not True for key in REQUIRED_TESTS - {"packagedBrowserChecks"}) or not isinstance(tests["packagedBrowserChecks"], int) or tests["packagedBrowserChecks"] < 1:
        raise ResultError("test-failure-visible")
    trust = value["platformTrust"]
    if not isinstance(trust, dict) or set(trust) != {"codeSignatureStructureValid", "developerIdSigned", "notarized", "gatekeeperAdmittedOnTestHost", "publicDistributionAllowed"}:
        raise ResultError("platform-trust-invalid")
    if type(trust["codeSignatureStructureValid"]) is not bool or type(trust["gatekeeperAdmittedOnTestHost"]) is not bool or any(trust[key] is not False for key in ("developerIdSigned", "notarized", "publicDistributionAllowed")):
        raise ResultError("platform-trust-overstated")
    if not isinstance(value["open"], list) or set(value["open"]) != REQUIRED_OPEN:
        raise ResultError("open-gates-invalid")
    if value["authority"] != {"releasePublicationAllowed": False, "automaticUpdateAllowed": False, "productionAdmissionGranted": False}:
        raise ResultError("authority-invalid")
    if value["privacy"] != {"privateIdentityRetained": False, "privatePathsRetained": False, "rawUserContentRetained": False, "rawToolOutputRetained": False}:
        raise ResultError("privacy-invalid")
    serialized = json.dumps(value, sort_keys=True)
    private_pattern = r"(?:" + re.escape("/" + "Users/") + r"|192\.168\.|BEGIN [A-Z ]+KEY)"
    if re.search(private_pattern, serialized, re.IGNORECASE):
        raise ResultError("private-data-detected")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        validate(json.loads(args.result.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, ResultError) as error:
        parser.error(str(error))
    print("Apple M4 development-app result validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
