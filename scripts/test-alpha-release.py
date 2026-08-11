#!/usr/bin/env python3
"""Verify source defaults and packaged Alpha identities remain isolated."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import alpha_release as release
import windows_alpha


def refused(call, expected: str) -> None:
    try:
        call()
    except release.AlphaReleaseError as error:
        assert str(error) == expected
    else:
        raise AssertionError(f"Release identity unexpectedly accepted: {expected}")


def main() -> int:
    checks = 0
    with patch.object(release.sys, "platform", "win32"):
        assert release.platform_default_version() == release.ALPHA_1_VERSION
    checks += 1
    with patch.object(release.sys, "platform", "linux"):
        assert release.platform_default_version() == release.ALPHA_2_VERSION
    checks += 1
    with (
        patch.object(release.sys, "platform", "win32"),
        patch.object(release.sys, "frozen", False, create=True),
        patch.dict(os.environ, {release.PACKAGED_VERSION_ENVIRONMENT: release.ALPHA_2_VERSION}),
    ):
        assert release.application_version() == release.ALPHA_1_VERSION
    checks += 1
    for version in (release.ALPHA_1_VERSION, release.ALPHA_2_VERSION):
        with (
            patch.object(release.sys, "platform", "win32"),
            patch.object(release.sys, "frozen", True, create=True),
            patch.dict(os.environ, {release.PACKAGED_VERSION_ENVIRONMENT: version}),
        ):
            assert release.application_version() == version
        checks += 1
    with (
        patch.object(release.sys, "platform", "linux"),
        patch.object(release.sys, "frozen", True, create=True),
        patch.dict(
            os.environ,
            {release.PACKAGED_VERSION_ENVIRONMENT: release.ALPHA_1_VERSION},
        ),
    ):
        refused(release.application_version, "invalid-packaged-release-identity")
    checks += 1
    with (
        patch.object(release.sys, "platform", "win32"),
        patch.object(release.sys, "frozen", True, create=True),
        patch.dict(os.environ, {release.PACKAGED_VERSION_ENVIRONMENT: "invalid"}),
    ):
        refused(release.application_version, "invalid-packaged-release-identity")
    checks += 1
    assert release.display_version(release.ALPHA_1_VERSION).endswith("Alpha 1")
    assert release.display_version(release.ALPHA_2_VERSION).endswith("Alpha 2")
    checks += 2
    refused(lambda: release.display_version("0.4.0"), "invalid-release-version")
    checks += 1
    with patch.object(
        windows_alpha, "application_version", return_value=release.ALPHA_2_VERSION,
    ):
        contract = windows_alpha.load_contract()
    assert contract["version"] == release.ALPHA_2_VERSION
    assert contract["displayVersion"] == "Haven 42 0.4 Alpha 2"
    assert contract["publicationAuthorized"] is False
    checks += 3
    print(f"Alpha release identity isolation passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
