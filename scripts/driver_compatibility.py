#!/usr/bin/env python3
"""Effect-free driver compatibility advisory for the reviewed Alpha 2 catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "config" / "alpha-2-driver-compatibility-catalog.json"
SAFE_TOKEN = re.compile(r"[a-z0-9][a-z0-9.-]{0,63}")
SAFE_PCI = re.compile(r"[0-9a-f]{4}")
SAFE_VERSION = re.compile(r"[0-9]{1,4}(?:\.[0-9]{1,4}){0,3}")


class DriverAdvisoryError(ValueError):
    """Raised for malformed or unbound advisory input."""


def _load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 512 * 1024:
            raise DriverAdvisoryError("Unsafe driver catalog file.")
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DriverAdvisoryError("Cannot read driver catalog.") from error
    if (
        not isinstance(catalog, dict)
        or catalog.get("schemaVersion") != 1
        or catalog.get("status") != "initial-reviewed-subset-advisory-only"
        or catalog.get("authority", {}).get("installsOrUpdatesDrivers") is not False
        or catalog.get("authority", {}).get("changesAutomaticModelSelection") is not False
    ):
        raise DriverAdvisoryError("Invalid driver catalog authority boundary.")
    return catalog


def _version(value: str) -> tuple[int, ...]:
    if not isinstance(value, str) or not SAFE_VERSION.fullmatch(value):
        raise DriverAdvisoryError("Invalid driver version.")
    return tuple(int(part) for part in value.split("."))


def _token(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if not SAFE_TOKEN.fullmatch(normalized):
        raise DriverAdvisoryError(f"Invalid {label}.")
    return normalized


def _outcome(catalog: dict[str, Any], status: str, **details: Any) -> dict[str, Any]:
    result = {"status": status, **catalog["outcomes"][status], **details}
    result["advisoryOnly"] = True
    result["driverMutationAllowed"] = False
    result["modelDefaultChangeAllowed"] = False
    return result


def evaluate(
    *,
    platform: str,
    distribution: str,
    os_version: str,
    vendor_id: str,
    device_id: str,
    driver_version: str | None,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a bounded advisory without changing the machine or product policy."""
    catalog = catalog or _load_catalog()
    platform = _token(platform, "platform")
    distribution = _token(distribution, "distribution")
    os_version = _token(os_version, "OS version")
    vendor_id = vendor_id.strip().lower()
    device_id = device_id.strip().lower()
    if not SAFE_PCI.fullmatch(vendor_id) or not SAFE_PCI.fullmatch(device_id):
        raise DriverAdvisoryError("Invalid PCI identity.")
    installed = _version(driver_version) if driver_version is not None else None

    device = next(
        (
            item
            for item in catalog["devices"]
            if item["vendorId"] == vendor_id and item["deviceId"] == device_id
        ),
        None,
    )
    if device is None or installed is None:
        return _outcome(catalog, "unknown", reason="unreviewed-device-or-driver")

    branch = installed[0]
    if device["supportClass"] == "legacy-390":
        if branch == device["maximumReviewedBranch"]:
            return _outcome(
                catalog,
                "legacy-unvalidated",
                reason="legacy-driver-requires-manual-risk-acceptance",
                device=device["name"],
            )
        return _outcome(
            catalog,
            "known-incompatible",
            reason="driver-branch-does-not-match-reviewed-legacy-device",
            device=device["name"],
        )

    if branch < device["minimumReviewedBranch"]:
        return _outcome(
            catalog,
            "known-incompatible",
            reason="driver-branch-predates-reviewed-device-support-floor",
            device=device["name"],
        )

    profile = next(
        (
            item
            for item in catalog["profiles"]
            if item["platform"] == platform
            and item["distribution"] == distribution
            and item["version"] == os_version
            and item["device"] == device["id"]
        ),
        None,
    )
    if profile is None:
        return _outcome(
            catalog,
            "unknown",
            reason="exact-os-profile-not-reviewed",
            device=device["name"],
        )

    installed_text = driver_version
    recommended = _version(profile["recommendedExactVersion"])
    if installed_text in profile["validatedExactVersions"]:
        return _outcome(
            catalog,
            "validated-current",
            device=device["name"],
            recommendedVersion=profile["recommendedExactVersion"],
        )
    if installed > recommended:
        return _outcome(
            catalog,
            "newer-than-tested",
            reason="installed-driver-is-newer-than-exact-haven42-evidence",
            device=device["name"],
            recommendedVersion=profile["recommendedExactVersion"],
        )
    return _outcome(
        catalog,
        "supported-update-available",
        reason="newer-reviewed-distribution-version-available",
        device=device["name"],
        recommendedVersion=profile["recommendedExactVersion"],
        warning="Continuing uses an older supported driver at your own risk.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--distribution", required=True)
    parser.add_argument("--os-version", required=True)
    parser.add_argument("--vendor-id", required=True)
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--driver-version")
    args = parser.parse_args()
    try:
        result = evaluate(
            platform=args.platform,
            distribution=args.distribution,
            os_version=args.os_version,
            vendor_id=args.vendor_id,
            device_id=args.device_id,
            driver_version=args.driver_version,
        )
    except DriverAdvisoryError as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
