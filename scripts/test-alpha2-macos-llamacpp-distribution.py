#!/usr/bin/env python3
"""Hostile archive and sanitized-result tests for Apple llama.cpp provenance."""

from __future__ import annotations

import importlib.util
import io
import json
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


runner = module("llamacpp_distribution", ROOT / "scripts/alpha2-macos-llamacpp-distribution.py")
validator = module("llamacpp_distribution_validator", ROOT / "scripts/validate-alpha2-macos-llamacpp-distribution-result.py")
checks = 0


def expect_error(builder, code: str) -> None:
    global checks
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "fixture.tar.gz"
        with tarfile.open(path, "w:gz") as archive:
            builder(archive)
        with tarfile.open(path, "r:gz") as archive:
            try:
                runner.safe_members(archive)
            except runner.DistributionError as error:
                assert str(error) == code
            else:
                raise AssertionError(f"expected {code}")
    checks += 1


def regular(archive: tarfile.TarFile, name: str = "llama-b10520/llama-server") -> None:
    info = tarfile.TarInfo(name)
    payload = b"fixture"
    info.size = len(payload)
    archive.addfile(info, io.BytesIO(payload))


expect_error(lambda archive: regular(archive, "../escape"), "unsafe-archive-path")
expect_error(lambda archive: regular(archive, "/absolute"), "unsafe-archive-path")


def hardlink(archive: tarfile.TarFile) -> None:
    info = tarfile.TarInfo("llama-b10520/link")
    info.type = tarfile.LNKTYPE
    info.linkname = "llama-b10520/llama-server"
    archive.addfile(info)


expect_error(hardlink, "unsafe-archive-member-type")


def escaping_symlink(archive: tarfile.TarFile) -> None:
    info = tarfile.TarInfo("llama-b10520/libunsafe.dylib")
    info.type = tarfile.SYMTYPE
    info.linkname = "../../outside"
    archive.addfile(info)


expect_error(escaping_symlink, "unsafe-archive-link")

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "safe.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        regular(archive)
        info = tarfile.TarInfo("llama-b10520/libsafe.dylib")
        info.type = tarfile.SYMTYPE
        info.linkname = "libsafe.1.dylib"
        archive.addfile(info)
    with tarfile.open(path, "r:gz") as archive:
        assert len(runner.safe_members(archive)) == 2
    checks += 1

valid = {
    "schemaVersion": 1,
    "kind": runner.KIND,
    "status": "partial-pass",
    "profile": {"platformFamily": "macos", "architecture": "arm64", "hardware": "Apple M4", "memoryGiB": 16},
    "officialRelease": {"project": runner.PROJECT, "tag": runner.TAG, "commit": runner.COMMIT, "releaseUrl": runner.RELEASE_URL, "asset": runner.ASSET, "assetUrl": runner.ASSET_URL, "assetBytes": runner.ASSET_BYTES, "assetSha256": runner.ASSET_SHA256},
    "archive": {"memberCount": 62, "safePaths": True, "safeInternalSymlinks": True, "exactOfficialDigest": True},
    "runtime": {"serverSha256": runner.SERVER_SHA256, "nativeArchitecture": "arm64", "version": runner.TAG, "commit": runner.COMMIT, "relocatedLaunchPassed": True, "runtimeLaunchRequiresSystemPython": False, "runtimeLaunchRequiresPackageManager": False},
    "platformTrust": {"adHocSigned": True, "developerIdSigned": False, "notarizationProven": False, "gatekeeperAdmitted": False, "publicDistributionTrusted": False},
    "open": ["developer-id-signing", "notarization", "gatekeeper-public-admission", "maintained-coding-surface"],
    "privacy": {"privateIdentityRetained": False, "privatePathRetained": False, "rawToolOutputRetained": False},
    "authority": {"runtimeAdmissionGranted": False, "packageAdmissionGranted": False, "releasePromotionAllowed": False},
}
validator.validate(valid, runner)
checks += 1

for mutation, code in (
    (("officialRelease", "assetSha256", "0" * 64), "official-release-mismatch"),
    (("runtime", "relocatedLaunchPassed", False), "relocation-not-proven"),
    (("platformTrust", "gatekeeperAdmitted", True), "trust-overstated"),
    (("authority", "runtimeAdmissionGranted", True), "authority-overstated"),
):
    candidate = json.loads(json.dumps(valid))
    candidate[mutation[0]][mutation[1]] = mutation[2]
    try:
        validator.validate(candidate, runner)
    except validator.ResultError as error:
        assert str(error) == code
    else:
        raise AssertionError(f"expected {code}")
    checks += 1

assert checks == 10
print("Apple llama.cpp distribution hostile tests passed: 10 checks.")
