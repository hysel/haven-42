#!/usr/bin/env python3
"""Offline, fail-closed policy engine for immutable Haven 42 core updates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


SHA256 = re.compile(r"^[0-9a-f]{64}$")
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
APPROVED_HOSTS = {"github.com", "objects.githubusercontent.com"}
ROOT = Path(__file__).resolve().parent.parent


class UpdatePolicyError(ValueError):
    pass


def _strict(value: dict, required: list[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != set(required):
        raise UpdatePolicyError(f"invalid-{label}-shape")


def _https(value: str, label: str) -> None:
    try:
        parsed = urlparse(value)
    except ValueError as error:
        raise UpdatePolicyError(f"invalid-{label}-url") from error
    if parsed.scheme != "https" or parsed.hostname not in APPROVED_HOSTS or parsed.username or parsed.password:
        raise UpdatePolicyError(f"unapproved-{label}-url")


def _version_tuple(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise UpdatePolicyError("invalid-version")
    core = value.split("-", 1)[0].split("+", 1)[0]
    return tuple(int(part) for part in core.split("."))


def evaluate(manifest: dict, host: dict, package_path: Path | None = None) -> dict:
    contract = json.loads((ROOT / "config/core-update-manifest-contract.json").read_text(encoding="utf-8"))
    _strict(manifest, contract["manifest"]["required"], "manifest")
    if manifest["schemaVersion"] != 1 or manifest["channel"] not in contract["manifest"]["channels"]:
        raise UpdatePolicyError("manifest-policy-rejected")
    if not isinstance(manifest["releaseTag"], str) or not manifest["releaseTag"].startswith("v"):
        raise UpdatePolicyError("invalid-release-tag")
    if not isinstance(manifest["releaseCommit"], str) or not FULL_SHA.fullmatch(manifest["releaseCommit"]):
        raise UpdatePolicyError("invalid-release-commit")
    if not isinstance(manifest["manifestSignature"], str) or not manifest["manifestSignature"].strip():
        raise UpdatePolicyError("manifest-signature-required")
    release_version = _version_tuple(manifest["releaseVersion"])
    current_version = _version_tuple(host["currentVersion"])
    updater_version = _version_tuple(host["updaterVersion"])
    if updater_version < _version_tuple(manifest["minimumUpdaterVersion"]):
        raise UpdatePolicyError("updater-too-old")
    if manifest["channel"] != host["channel"]:
        raise UpdatePolicyError("channel-mismatch")
    if release_version <= current_version:
        raise UpdatePolicyError("not-a-newer-release")

    compatibility = manifest["compatibility"]
    _strict(compatibility, contract["compatibility"]["required"], "compatibility")
    schema_checks = {
        "desktopIpcSchemaVersions": host["desktopIpcSchemaVersion"],
        "workflowEnvelopeSchemaVersions": host["workflowEnvelopeSchemaVersion"],
        "typedArtifactSchemaVersions": host["typedArtifactSchemaVersion"],
        "configurationSchemaVersions": host["configurationSchemaVersion"],
    }
    if compatibility["engineApiVersion"] != host["engineApiVersion"]:
        raise UpdatePolicyError("engine-api-incompatible")
    for field, value in schema_checks.items():
        if value not in compatibility[field]:
            raise UpdatePolicyError("schema-incompatible")

    matches = []
    for asset in manifest["assets"]:
        _strict(asset, contract["asset"]["required"], "asset")
        for field in ("downloadUrl", "signatureOrAttestation", "sbomUrl", "thirdPartyNoticesUrl"):
            _https(asset[field], field)
        if not isinstance(asset["sizeBytes"], int) or asset["sizeBytes"] <= 0:
            raise UpdatePolicyError("invalid-asset-size")
        if not isinstance(asset["sha256"], str) or not SHA256.fullmatch(asset["sha256"]):
            raise UpdatePolicyError("invalid-asset-sha256")
        if asset["os"] == host["os"] and asset["architecture"] == host["architecture"] and asset["targetTriple"] == host["targetTriple"]:
            matches.append(asset)
    if len(matches) != 1:
        raise UpdatePolicyError("exactly-one-host-asset-required")
    asset = matches[0]

    bytes_verified = False
    if package_path is not None:
        if not package_path.is_file() or package_path.stat().st_size != asset["sizeBytes"]:
            raise UpdatePolicyError("package-size-mismatch")
        digest = hashlib.sha256(package_path.read_bytes()).hexdigest()
        if digest != asset["sha256"]:
            raise UpdatePolicyError("package-hash-mismatch")
        bytes_verified = True

    return {
        "SchemaVersion": 1,
        "Kind": "core-update-policy",
        "Status": "verified-bytes-awaiting-cryptographic-attestation" if bytes_verified else "planned",
        "ReleaseVersion": manifest["releaseVersion"],
        "ReleaseTag": manifest["releaseTag"],
        "ReleaseCommit": manifest["releaseCommit"],
        "AssetId": asset["assetId"],
        "BytesVerified": bytes_verified,
        "CompatibilityPreflightComplete": False,
        "OperatingSystemCompatibilityVerified": False,
        "ManifestSignatureVerified": False,
        "AssetAttestationVerified": False,
        "ActivationAllowed": False,
        "NetworkUsed": False,
        "FilesWritten": False,
        "UserDataTouched": False,
        "NextGate": "trusted native verifier must verify manifest signature and asset attestation before staging",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or verify immutable core-update inputs without downloading, staging, or activating code.")
    parser.add_argument("--manifest-path", required=True)
    parser.add_argument("--package-path")
    parser.add_argument("--host-os", required=True, choices=["windows", "linux", "macos"])
    parser.add_argument("--host-architecture", required=True, choices=["x64", "arm64", "intel64"])
    parser.add_argument("--target-triple", required=True)
    parser.add_argument("--current-version", required=True)
    parser.add_argument("--updater-version", required=True)
    parser.add_argument("--channel", default="stable", choices=["stable", "beta"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    host = {
        "os": args.host_os, "architecture": args.host_architecture, "targetTriple": args.target_triple,
        "currentVersion": args.current_version, "updaterVersion": args.updater_version, "channel": args.channel,
        "engineApiVersion": 1, "desktopIpcSchemaVersion": 1, "workflowEnvelopeSchemaVersion": 1,
        "typedArtifactSchemaVersion": 1, "configurationSchemaVersion": 1,
    }
    try:
        manifest = json.loads(Path(args.manifest_path).read_text(encoding="utf-8"))
        result = evaluate(manifest, host, Path(args.package_path) if args.package_path else None)
    except (OSError, json.JSONDecodeError, UpdatePolicyError) as error:
        print(f"Core update policy rejected input: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Status: {result['Status']}\nRelease: {result['ReleaseVersion']}\nActivation allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
