#!/usr/bin/env python3
"""Explicit, bounded checks for managed software releases.

No request is made when this module is imported. Callers must invoke
``check_for_updates`` from a user-approved action.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
import hashlib
import threading
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
MAX_RESPONSE_BYTES = 512 * 1024
OFFICIAL_RELEASE_API = "https://api.github.com/repos/ollama/ollama/releases/latest"
VERSION = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class SoftwareUpdateError(ValueError):
    """Raised when release metadata cannot be verified safely."""


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, new_url):
        raise SoftwareUpdateError("software-update-redirect-refused")


class _ReleaseRedirects(urllib.request.HTTPRedirectHandler):
    """Permit only GitHub's fixed release-asset delivery hosts."""

    def __init__(self) -> None:
        self.count = 0

    def redirect_request(self, request, fp, code, msg, headers, new_url):
        self.count += 1
        parsed = urllib.parse.urlsplit(new_url)
        if (
            self.count > 3
            or parsed.scheme != "https"
            or parsed.hostname not in {
                "github.com", "objects.githubusercontent.com",
                "release-assets.githubusercontent.com",
            }
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in {None, 443}
        ):
            raise SoftwareUpdateError("software-update-redirect-refused")
        return super().redirect_request(request, fp, code, msg, headers, new_url)


def _read_official_release() -> dict[str, Any]:
    request = urllib.request.Request(
        OFFICIAL_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Haven42/0.4.0-alpha.2",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.build_opener(_NoRedirects()).open(request, timeout=15) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/json":
                raise SoftwareUpdateError("software-update-response-invalid")
            data = response.read(MAX_RESPONSE_BYTES + 1)
    except SoftwareUpdateError:
        raise
    except Exception as error:
        raise SoftwareUpdateError("software-update-check-unavailable") from error
    if len(data) > MAX_RESPONSE_BYTES:
        raise SoftwareUpdateError("software-update-response-too-large")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SoftwareUpdateError("software-update-response-invalid") from error
    if not isinstance(value, dict):
        raise SoftwareUpdateError("software-update-response-invalid")
    return value


def _managed_component() -> dict[str, Any]:
    name = "linux-alpha-component-registry.json" if sys.platform.startswith("linux") else "windows-alpha-component-registry.json"
    try:
        registry = json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))
        component = registry["components"][0]
    except (OSError, KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise SoftwareUpdateError("managed-software-registry-invalid") from error
    return component


def _version(value: object) -> tuple[int, int, int]:
    match = VERSION.fullmatch(str(value))
    if match is None:
        raise SoftwareUpdateError("software-update-version-invalid")
    return tuple(int(part) for part in match.groups())


def _asset_name() -> str:
    return "ollama-linux-amd64.tar.zst" if sys.platform.startswith("linux") else "ollama-windows-amd64.zip"


def check_for_updates(
    release_provider: Callable[[], dict[str, Any]] = _read_official_release,
) -> dict[str, Any]:
    """Return sanitized release information after an explicit user action."""
    release = release_provider()
    managed = _managed_component()
    tag = release.get("tag_name")
    latest_tuple = _version(tag)
    managed_tuple = _version(managed.get("version"))
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise SoftwareUpdateError("software-update-release-not-stable")
    expected_release_url = f"https://github.com/ollama/ollama/releases/tag/v{'.'.join(map(str, latest_tuple))}"
    if release.get("html_url") != expected_release_url:
        raise SoftwareUpdateError("software-update-release-url-invalid")
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise SoftwareUpdateError("software-update-assets-invalid")
    wanted = [item for item in assets if isinstance(item, dict) and item.get("name") == _asset_name()]
    if len(wanted) != 1:
        raise SoftwareUpdateError("software-update-asset-missing")
    asset = wanted[0]
    digest = str(asset.get("digest", ""))
    if not digest.startswith("sha256:") or not HEX64.fullmatch(digest[7:]):
        raise SoftwareUpdateError("software-update-asset-digest-invalid")
    download = str(asset.get("browser_download_url", ""))
    parsed = urllib.parse.urlsplit(download)
    expected_prefix = f"/ollama/ollama/releases/download/v{'.'.join(map(str, latest_tuple))}/"
    if (
        parsed.scheme != "https" or parsed.hostname != "github.com"
        or parsed.path != expected_prefix + _asset_name()
        or parsed.query or parsed.fragment or parsed.username or parsed.password
        or parsed.port not in {None, 443}
        or not isinstance(asset.get("size"), int) or not 1 <= asset["size"] <= 4 * 1024**3
    ):
        raise SoftwareUpdateError("software-update-asset-invalid")
    latest = ".".join(map(str, latest_tuple))
    managed_version = ".".join(map(str, managed_tuple))
    return {
        "schemaVersion": 1,
        "kind": "haven42-managed-software-update-check",
        "checkedBecauseUserRequested": True,
        "automaticChecksEnabled": False,
        "configurationPersisted": False,
        "userContentSent": False,
        "components": [{
            "id": "ollama-runtime",
            "displayName": "Ollama local AI engine",
            "managedVersion": managed_version,
            "latestStableVersion": latest,
            "newerOfficialVersionAvailable": latest_tuple > managed_tuple,
            "managedVersionIsLatest": latest_tuple == managed_tuple,
            "availableForManagedSetup": latest_tuple == managed_tuple,
            "certificationStatus": "certified" if latest_tuple == managed_tuple else "official-unverified",
            "releaseUrl": expected_release_url,
            "downloadUrl": download,
            "artifactName": _asset_name(),
            "downloadBytes": asset["size"],
            "sha256": digest[7:],
        }],
    }


def download_official_asset(
    component: dict[str, Any],
    destination: Path,
    cancel: threading.Event,
    progress: Callable[[int, int], None],
) -> None:
    """Download the exact asset selected from a validated official release."""
    required = {
        "id", "displayName", "managedVersion", "latestStableVersion",
        "newerOfficialVersionAvailable", "managedVersionIsLatest",
        "availableForManagedSetup", "certificationStatus", "releaseUrl",
        "downloadUrl", "artifactName", "downloadBytes", "sha256",
    }
    if (
        not isinstance(component, dict) or set(component) != required
        or component.get("id") != "ollama-runtime"
        or component.get("certificationStatus") not in {"certified", "official-unverified"}
        or not VERSION.fullmatch(str(component.get("latestStableVersion", "")))
        or not HEX64.fullmatch(str(component.get("sha256", "")))
        or type(component.get("downloadBytes")) is not int
        or not 1 <= component["downloadBytes"] <= 4 * 1024**3
    ):
        raise SoftwareUpdateError("software-update-component-invalid")
    parsed = urllib.parse.urlsplit(str(component.get("downloadUrl", "")))
    expected_path = (
        f"/ollama/ollama/releases/download/v{component['latestStableVersion']}/"
        f"{component['artifactName']}"
    )
    if (
        parsed.scheme != "https" or parsed.hostname != "github.com"
        or parsed.path != expected_path or parsed.query or parsed.fragment
        or parsed.username or parsed.password or parsed.port not in {None, 443}
    ):
        raise SoftwareUpdateError("software-update-download-url-invalid")
    destination = destination.resolve(strict=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise SoftwareUpdateError("software-update-download-destination-exists")
    digest = hashlib.sha256()
    written = 0
    request = urllib.request.Request(
        component["downloadUrl"], headers={"User-Agent": "Haven42/0.4.0-alpha.2"},
    )
    try:
        with urllib.request.build_opener(_ReleaseRedirects()).open(request, timeout=30) as response, destination.open("xb") as output:
            while True:
                if cancel.is_set():
                    raise SoftwareUpdateError("software-update-cancelled")
                block = response.read(1024 * 1024)
                if not block:
                    break
                written += len(block)
                if written > component["downloadBytes"]:
                    raise SoftwareUpdateError("software-update-size-mismatch")
                digest.update(block)
                output.write(block)
                progress(written, component["downloadBytes"])
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    if written != component["downloadBytes"] or digest.hexdigest() != component["sha256"]:
        destination.unlink(missing_ok=True)
        raise SoftwareUpdateError("software-update-integrity-mismatch")
