#!/usr/bin/env python3
"""Offline hostile tests for explicit managed-software release checks."""

from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import software_update_service as service  # noqa: E402


def release(version: str = "0.32.14") -> dict:
    artifact = service._asset_name()
    return {
        "tag_name": f"v{version}",
        "html_url": f"https://github.com/ollama/ollama/releases/tag/v{version}",
        "draft": False,
        "prerelease": False,
        "assets": [{
            "name": artifact,
            "size": 123456,
            "digest": "sha256:" + "a" * 64,
            "browser_download_url": f"https://github.com/ollama/ollama/releases/download/v{version}/{artifact}",
        }],
    }


def refused(value: dict) -> bool:
    try:
        service.check_for_updates(lambda: value)
    except service.SoftwareUpdateError:
        return True
    return False


def main() -> int:
    result = service.check_for_updates(release)
    assert result["checkedBecauseUserRequested"] is True
    assert result["automaticChecksEnabled"] is False
    assert result["configurationPersisted"] is False
    assert result["userContentSent"] is False
    component = result["components"][0]
    assert component["managedVersion"] == "0.32.14"
    assert component["latestStableVersion"] == "0.32.14"
    assert component["managedVersionIsLatest"] is True
    assert component["availableForManagedSetup"] is True

    newer = service.check_for_updates(lambda: release("0.32.15"))["components"][0]
    assert newer["newerOfficialVersionAvailable"] is True
    assert newer["availableForManagedSetup"] is False

    hostile = []
    for mutation in (
        lambda value: value.update(draft=True),
        lambda value: value.update(prerelease=True),
        lambda value: value.update(tag_name="latest"),
        lambda value: value.update(html_url="https://example.invalid/release"),
        lambda value: value["assets"][0].update(digest="sha256:bad"),
        lambda value: value["assets"][0].update(browser_download_url="https://example.invalid/file"),
        lambda value: value["assets"][0].update(size=0),
        lambda value: value.update(assets=[]),
    ):
        candidate = copy.deepcopy(release())
        mutation(candidate)
        hostile.append(candidate)
    assert all(refused(candidate) for candidate in hostile)
    print(f"Software update service passed {9 + len(hostile)} policy and hostile checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
