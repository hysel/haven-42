#!/usr/bin/env python3
"""Validate the exact published Alpha record and its narrow authority."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "config" / "windows-alpha-release-record.json"
RELEASE_DOC = ROOT / "docs" / "windows-alpha-release.md"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ReleaseRecordError(ValueError):
    """Raised when the publication record drifts or broadens authority."""


def official_url(value: object, expected_path: str) -> None:
    if not isinstance(value, str):
        raise ReleaseRecordError("invalid-release-url")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.path != expected_path
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
        or parsed.port is not None
    ):
        raise ReleaseRecordError("invalid-release-url")


def validate(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {
        "schemaVersion", "recordId", "release", "candidate",
        "verification", "reporting", "authority",
    }:
        raise ReleaseRecordError("invalid-record-shape")
    if (
        value["schemaVersion"] != 1
        or value["recordId"] != "haven42.windows-alpha-release.0.4.0-alpha.1"
    ):
        raise ReleaseRecordError("invalid-record-identity")

    release = value["release"]
    if release != {
        "version": "0.4.0-alpha.1",
        "tag": "v0.4.0-alpha.1",
        "title": "Haven 42 0.4.0 Alpha 1",
        "repository": "hysel/haven-42",
        "url": "https://github.com/hysel/haven-42/releases/tag/v0.4.0-alpha.1",
        "publishedAtUtc": "2026-08-05T22:35:32Z",
        "channel": "github-public-prerelease",
        "prerelease": True,
        "invitedTestingBoundary": True,
    }:
        raise ReleaseRecordError("invalid-release-identity")
    official_url(release["url"], "/hysel/haven-42/releases/tag/v0.4.0-alpha.1")

    candidate = value["candidate"]
    if set(candidate) != {
        "sourceCommit", "operatingSystem", "architecture", "artifactName",
        "byteLength", "sha256",
    }:
        raise ReleaseRecordError("invalid-candidate-shape")
    if (
        not HEX40.fullmatch(str(candidate["sourceCommit"]))
        or candidate["sourceCommit"] != "6624dfb967a58c67d2d5a9a01437cf3213eee289"
        or candidate["operatingSystem"] != "windows"
        or candidate["architecture"] != "x64"
        or candidate["artifactName"] != "haven42-0.4.0-alpha.1-windows-x64-unsigned.zip"
        or candidate["byteLength"] != 9650721
        or not HEX64.fullmatch(str(candidate["sha256"]))
        or candidate["sha256"] != "d1648667807dde37c645beb2199503b8a4852a585a2f62eb4ebe2c0b90465106"
    ):
        raise ReleaseRecordError("invalid-candidate-identity")

    verification = value["verification"]
    expected_verification = {
        "validatePackRun": "https://github.com/hysel/haven-42/actions/runs/31050714006",
        "codeQlRun": "https://github.com/hysel/haven-42/actions/runs/31050714049",
        "exactSourceSecurityReviewPassed": True,
        "publicHistoryPrivacyPassed": True,
        "nativePackageSmokePassed": True,
        "crossPlatformHostedPackagePassed": True,
        "releaseAssetDigestVerified": True,
    }
    if verification != expected_verification:
        raise ReleaseRecordError("invalid-verification-evidence")
    official_url(verification["validatePackRun"], "/hysel/haven-42/actions/runs/31050714006")
    official_url(verification["codeQlRun"], "/hysel/haven-42/actions/runs/31050714049")

    reporting = value["reporting"]
    if reporting != {
        "issueChooser": "https://github.com/hysel/haven-42/issues/new/choose",
        "privateVulnerabilityReporting": "https://github.com/hysel/haven-42/security/advisories/new",
    }:
        raise ReleaseRecordError("invalid-reporting-boundary")
    official_url(reporting["issueChooser"], "/hysel/haven-42/issues/new/choose")
    official_url(reporting["privateVulnerabilityReporting"], "/hysel/haven-42/security/advisories/new")

    authority = value["authority"]
    if set(authority) != {
        "publicUnsignedAlphaDistributionRecorded", "platformSigningAllowed",
        "notarizationAllowed", "stableOrProductionPromotionAllowed",
        "installerActivationAllowed", "onlineCoreUpdaterAllowed",
        "driverServiceOrFirewallModificationAllowed", "tauriOrRustAdmitted",
        "externalSoftwareBundled",
    }:
        raise ReleaseRecordError("invalid-authority-shape")
    if authority["publicUnsignedAlphaDistributionRecorded"] is not True or any(
        authority[field] is not False
        for field in authority
        if field != "publicUnsignedAlphaDistributionRecorded"
    ):
        raise ReleaseRecordError("release-authority-broadened")


def rejected(value: object, code: str) -> None:
    try:
        validate(value)
    except ReleaseRecordError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"unsafe release record accepted: {code}")


def main() -> int:
    baseline = json.loads(RECORD.read_text(encoding="utf-8"))
    validate(copy.deepcopy(baseline))
    checks = 1

    release_doc = RELEASE_DOC.read_text(encoding="utf-8")
    for expected in (
        baseline["release"]["tag"],
        baseline["candidate"]["sourceCommit"],
        baseline["candidate"]["artifactName"],
        str(baseline["candidate"]["byteLength"]),
        baseline["candidate"]["sha256"],
    ):
        assert expected in release_doc, f"release documentation omitted {expected}"
        checks += 1
    assert "not a stable or production promotion" in release_doc
    checks += 1

    cases = (
        (lambda value: value.update(schemaVersion=2), "invalid-record-identity"),
        (lambda value: value["release"].update(tag="latest"), "invalid-release-identity"),
        (lambda value: value["release"].update(url="http://github.com/hysel/haven-42"), "invalid-release-identity"),
        (lambda value: value["candidate"].update(sourceCommit="a" * 40), "invalid-candidate-identity"),
        (lambda value: value["candidate"].update(sha256="0" * 64), "invalid-candidate-identity"),
        (lambda value: value["candidate"].update(byteLength=1), "invalid-candidate-identity"),
        (lambda value: value["verification"].update(nativePackageSmokePassed=False), "invalid-verification-evidence"),
        (lambda value: value["reporting"].update(issueChooser="https://example.com"), "invalid-reporting-boundary"),
        (lambda value: value["authority"].update(platformSigningAllowed=True), "release-authority-broadened"),
        (lambda value: value["authority"].update(onlineCoreUpdaterAllowed=True), "release-authority-broadened"),
        (lambda value: value["authority"].update(stableOrProductionPromotionAllowed=True), "release-authority-broadened"),
        (lambda value: value["authority"].update(externalSoftwareBundled=True), "release-authority-broadened"),
    )
    for mutate, code in cases:
        hostile = copy.deepcopy(baseline)
        mutate(hostile)
        rejected(hostile, code)
        checks += 1
    print(f"Windows Alpha release-record tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
