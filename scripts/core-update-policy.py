#!/usr/bin/env python3
"""Offline, fail-closed policy engine for immutable Haven 42 core updates."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
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


def evaluate_release_metadata(metadata: dict, manifest: dict) -> dict:
    contract = json.loads((ROOT / "config/core-update-check-contract.json").read_text(encoding="utf-8"))
    _strict(metadata, contract["requiredReleaseFields"], "release-metadata")
    if metadata["schemaVersion"] != 1 or metadata["repository"] != contract["stablePolicy"]["repository"]:
        raise UpdatePolicyError("release-source-rejected")
    if metadata["draft"] is not False or metadata["prerelease"] is not False or metadata["immutable"] is not True:
        raise UpdatePolicyError("release-not-immutable-stable")
    _https(metadata["releaseUrl"], "release")
    if metadata["tagName"] != manifest.get("releaseTag"):
        raise UpdatePolicyError("release-tag-manifest-mismatch")
    expected_release_url = f"https://github.com/{contract['stablePolicy']['repository']}/releases/tag/{metadata['tagName']}"
    if metadata["releaseUrl"] != expected_release_url:
        raise UpdatePolicyError("release-url-identity-mismatch")
    assets = metadata["assets"]
    if not isinstance(assets, list) or len(assets) > contract["maximumAssets"]:
        raise UpdatePolicyError("invalid-release-assets")
    manifest_assets = []
    for asset in assets:
        _strict(asset, contract["requiredAssetFields"], "release-asset")
        _https(asset["url"], "release-asset")
        if isinstance(asset["sizeBytes"], bool) or not isinstance(asset["sizeBytes"], int) or asset["sizeBytes"] <= 0:
            raise UpdatePolicyError("invalid-release-asset-size")
        if asset["name"] == contract["stablePolicy"]["manifestAssetName"]:
            manifest_assets.append(asset)
    if len(manifest_assets) != 1:
        raise UpdatePolicyError("exactly-one-update-manifest-required")
    expected_manifest_url = (
        f"https://github.com/{contract['stablePolicy']['repository']}/releases/download/"
        f"{metadata['tagName']}/{contract['stablePolicy']['manifestAssetName']}"
    )
    if manifest_assets[0]["url"] != expected_manifest_url:
        raise UpdatePolicyError("manifest-url-identity-mismatch")
    return {
        "SchemaVersion": 1,
        "Kind": "offline-core-update-check",
        "Status": "candidate-verified-offline",
        "ReleaseTag": metadata["tagName"],
        "ReleaseVersion": manifest["releaseVersion"],
        "ManifestAsset": manifest_assets[0]["name"],
        "NetworkUsed": False,
        "DownloadAllowed": False,
        "FilesWritten": False,
        "ActivationAllowed": False,
        "NextGate": "explicit network consent and trusted signature verification are required",
    }


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


def run_self_tests() -> int:
    """Exercise hostile manifests without network, staging, or activation."""
    manifest = json.loads((ROOT / "examples/fixtures/core-update-manifest.json").read_text(encoding="utf-8"))
    release_metadata = json.loads((ROOT / "examples/fixtures/github-release-candidate.json").read_text(encoding="utf-8"))
    package_path = ROOT / "examples/fixtures/core-update-package.bin"
    host = {
        "os": "windows", "architecture": "x64", "targetTriple": "x86_64-pc-windows-msvc",
        "currentVersion": "0.3.0", "updaterVersion": "0.3.0", "channel": "stable",
        "engineApiVersion": 1, "desktopIpcSchemaVersion": 1, "workflowEnvelopeSchemaVersion": 1,
        "typedArtifactSchemaVersion": 1, "configurationSchemaVersion": 1,
    }
    passed = 0

    def allow(candidate: dict, package: Path | None = None) -> None:
        nonlocal passed
        result = evaluate(candidate, copy.deepcopy(host), package)
        assert result["ActivationAllowed"] is False
        passed += 1

    def deny(mutator, expected: str, host_override: dict | None = None, package: Path | None = None) -> None:
        nonlocal passed
        candidate = copy.deepcopy(manifest)
        mutator(candidate)
        target_host = copy.deepcopy(host)
        if host_override:
            target_host.update(host_override)
        try:
            evaluate(candidate, target_host, package)
        except UpdatePolicyError as error:
            if str(error) != expected:
                raise AssertionError(f"expected {expected}, received {error}") from error
            passed += 1
            return
        raise AssertionError(f"expected {expected}")

    allow(copy.deepcopy(manifest))
    allow(copy.deepcopy(manifest), package_path)
    release_result = evaluate_release_metadata(copy.deepcopy(release_metadata), copy.deepcopy(manifest))
    assert release_result["NetworkUsed"] is False and release_result["DownloadAllowed"] is False
    passed += 1
    deny(lambda value: value.update(releaseVersion="0.3.0"), "not-a-newer-release")
    deny(lambda value: value["assets"].append(copy.deepcopy(value["assets"][0])), "exactly-one-host-asset-required")
    deny(lambda value: value.update(releaseCommit="main"), "invalid-release-commit")
    deny(lambda value: value.update(unexpected=True), "invalid-manifest-shape")
    deny(lambda value: value["assets"][0].update(downloadUrl="http://github.com/file"), "unapproved-downloadUrl-url")
    deny(lambda value: value["assets"][0].update(sha256="ABC"), "invalid-asset-sha256")
    deny(lambda value: value["assets"][0].update(sizeBytes=0), "invalid-asset-size")
    deny(lambda value: value.update(manifestSignature=""), "manifest-signature-required")
    deny(lambda value: value.update(schemaVersion=2), "manifest-policy-rejected")
    deny(lambda value: None, "channel-mismatch", {"channel": "beta"})
    deny(lambda value: value.update(minimumUpdaterVersion="9.0.0"), "updater-too-old")
    deny(lambda value: value["compatibility"].update(engineApiVersion=2), "engine-api-incompatible")
    deny(lambda value: value["compatibility"].update(desktopIpcSchemaVersions=[2]), "schema-incompatible")
    deny(lambda value: value["assets"][0].update(targetTriple="x86_64-unknown-linux-gnu"), "exactly-one-host-asset-required")
    deny(lambda value: value["assets"][0].update(sha256="0" * 64), "package-hash-mismatch", package=package_path)
    with tempfile.TemporaryDirectory(prefix="haven42-corrupt-update-") as directory:
        original = package_path.read_bytes()
        same_size = Path(directory) / "same-size-corrupt.bin"
        same_size.write_bytes(bytes([original[0] ^ 0xFF]) + original[1:])
        deny(lambda value: None, "package-hash-mismatch", package=same_size)
        truncated = Path(directory) / "truncated.bin"
        truncated.write_bytes(original[:-1])
        deny(lambda value: None, "package-size-mismatch", package=truncated)
    for mutator, expected in (
        (lambda value: value.update(draft=True), "release-not-immutable-stable"),
        (lambda value: value.update(immutable=False), "release-not-immutable-stable"),
        (lambda value: value.update(repository="someone/fork"), "release-source-rejected"),
        (lambda value: value.update(tagName="v9.9.9"), "release-tag-manifest-mismatch"),
        (lambda value: value.update(assets=[]), "exactly-one-update-manifest-required"),
        (lambda value: value.update(releaseUrl="https://github.com/someone/fork/releases/tag/v0.4.0"), "release-url-identity-mismatch"),
        (lambda value: value["assets"][0].update(url="https://github.com/someone/fork/releases/download/v0.4.0/haven-42-core-update-manifest.json"), "manifest-url-identity-mismatch"),
        (lambda value: value["assets"][0].update(sizeBytes=True), "invalid-release-asset-size"),
    ):
        candidate = copy.deepcopy(release_metadata)
        mutator(candidate)
        try:
            evaluate_release_metadata(candidate, copy.deepcopy(manifest))
        except UpdatePolicyError as error:
            if str(error) != expected:
                raise AssertionError(f"expected {expected}, received {error}") from error
            passed += 1
        else:
            raise AssertionError(f"expected {expected}")
    print(f"Core update hostile self-test passed: {passed} cases.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or verify immutable core-update inputs without downloading, staging, or activating code.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--manifest-path")
    parser.add_argument("--release-metadata-path")
    parser.add_argument("--package-path")
    parser.add_argument("--host-os", choices=["windows", "linux", "macos"])
    parser.add_argument("--host-architecture", choices=["x64", "arm64", "intel64"])
    parser.add_argument("--target-triple")
    parser.add_argument("--current-version")
    parser.add_argument("--updater-version")
    parser.add_argument("--channel", default="stable", choices=["stable", "beta"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return run_self_tests()
    if args.manifest_path is None:
        parser.error("manifest is required unless --self-test is used")
    host_required = (args.host_os, args.host_architecture, args.target_triple, args.current_version, args.updater_version)
    if not args.release_metadata_path and any(value is None for value in host_required):
        parser.error("host arguments are required for asset policy evaluation")
    host = {
        "os": args.host_os, "architecture": args.host_architecture, "targetTriple": args.target_triple,
        "currentVersion": args.current_version, "updaterVersion": args.updater_version, "channel": args.channel,
        "engineApiVersion": 1, "desktopIpcSchemaVersion": 1, "workflowEnvelopeSchemaVersion": 1,
        "typedArtifactSchemaVersion": 1, "configurationSchemaVersion": 1,
    }
    try:
        manifest = json.loads(Path(args.manifest_path).read_text(encoding="utf-8"))
        result = (
            evaluate_release_metadata(
                json.loads(Path(args.release_metadata_path).read_text(encoding="utf-8")),
                manifest,
            )
            if args.release_metadata_path
            else evaluate(manifest, host, Path(args.package_path) if args.package_path else None)
        )
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
