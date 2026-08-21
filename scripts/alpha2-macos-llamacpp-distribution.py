#!/usr/bin/env python3
"""Validate one exact official llama.cpp macOS archive without granting admission."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import posixpath
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


KIND = "haven42-sanitized-macos-llamacpp-distribution-result"
PROJECT = "ggml-org/llama.cpp"
TAG = "b10520"
ARCHIVE_ROOT = "llama-b10520"
COMMIT = "cd644c39545aac3dca63261f99a9bfc35956cb25"
ASSET = "llama-b10520-bin-macos-arm64.tar.gz"
ASSET_BYTES = 11_089_815
ASSET_SHA256 = "c993962da4fec1cdccb5cb27ce06c8f7db0fb46f188bb156f0e6761233b7fa6d"
SERVER_SHA256 = "d0878274b8d6bd3c8ea26a78eb66cd1ffd943d007c62b9dff31c8aa99922d713"
RELEASE_URL = "https://github.com/ggml-org/llama.cpp/releases/tag/b10520"
ASSET_URL = f"https://github.com/{PROJECT}/releases/download/{TAG}/{ASSET}"
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024


class DistributionError(ValueError):
    """The artifact, host, extraction, runtime, or output failed closed."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise DistributionError(code)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_members(archive: tarfile.TarFile, expected_root: str = ARCHIVE_ROOT) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    require(0 < len(members) <= 512, "unsafe-archive-member-count")
    for member in members:
        path = PurePosixPath(member.name)
        require(
            not path.is_absolute()
            and path.parts
            and path.parts[0] == expected_root
            and all(part not in {"", ".", ".."} for part in path.parts),
            "unsafe-archive-path",
        )
        require(member.isdir() or member.isfile() or member.issym(), "unsafe-archive-member-type")
        if member.issym():
            target = PurePosixPath(member.linkname)
            require(not target.is_absolute(), "unsafe-archive-link")
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(member.name), member.linkname))
            require(resolved.startswith(expected_root + "/"), "unsafe-archive-link")
    return members


def run(arguments: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(cwd or Path("/tmp"))},
    )


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def inspect_archive(archive_path: Path, output: Path) -> dict[str, Any]:
    require(platform.system() == "Darwin" and platform.machine() == "arm64", "requires-macos-arm64")
    require(
        archive_path.is_file()
        and not archive_path.is_symlink()
        and archive_path.stat().st_size <= MAX_ARCHIVE_BYTES,
        "unsafe-archive-input",
    )
    require(archive_path.stat().st_size == ASSET_BYTES, "official-asset-size-mismatch")
    require(sha256_file(archive_path) == ASSET_SHA256, "official-asset-digest-mismatch")

    with tempfile.TemporaryDirectory(prefix="haven42-llamacpp-distribution-") as directory:
        root = Path(directory)
        with tarfile.open(archive_path, "r:gz") as archive:
            members = safe_members(archive)
            archive.extractall(root, filter="data")
        runtime = root / ARCHIVE_ROOT
        server = runtime / "llama-server"
        require(server.is_file() and not server.is_symlink() and os.access(server, os.X_OK), "server-missing")
        require(sha256_file(server) == SERVER_SHA256, "server-digest-mismatch")

        architecture = run(["/usr/bin/lipo", "-archs", str(server)], cwd=root)
        require(architecture.returncode == 0 and architecture.stdout.strip() == "arm64", "architecture-mismatch")
        version = run([str(server), "--version"], cwd=root)
        version_text = version.stdout + version.stderr
        require(
            version.returncode == 0 and "build 10520" in version_text and "commit cd644c395" in version_text,
            "runtime-version-mismatch",
        )

        signature = run(["/usr/bin/codesign", "-dv", "--verbose=4", str(server)], cwd=root)
        signature_text = signature.stdout + signature.stderr
        developer_id = "Authority=Developer ID" in signature_text
        adhoc = "Signature=adhoc" in signature_text
        gatekeeper = run(["/usr/sbin/spctl", "-a", "-t", "exec", str(server)], cwd=root)

        result = {
            "schemaVersion": 1,
            "kind": KIND,
            "status": "partial-pass",
            "profile": {"platformFamily": "macos", "architecture": "arm64", "hardware": "Apple M4", "memoryGiB": 16},
            "officialRelease": {
                "project": PROJECT,
                "tag": TAG,
                "commit": COMMIT,
                "releaseUrl": RELEASE_URL,
                "asset": ASSET,
                "assetUrl": ASSET_URL,
                "assetBytes": ASSET_BYTES,
                "assetSha256": ASSET_SHA256,
            },
            "archive": {
                "memberCount": len(members),
                "safePaths": True,
                "safeInternalSymlinks": True,
                "exactOfficialDigest": True,
            },
            "runtime": {
                "serverSha256": SERVER_SHA256,
                "nativeArchitecture": "arm64",
                "version": TAG,
                "commit": COMMIT,
                "relocatedLaunchPassed": True,
                "runtimeLaunchRequiresSystemPython": False,
                "runtimeLaunchRequiresPackageManager": False,
            },
            "platformTrust": {
                "adHocSigned": adhoc,
                "developerIdSigned": developer_id,
                "notarizationProven": False,
                "gatekeeperAdmitted": gatekeeper.returncode == 0,
                "publicDistributionTrusted": developer_id and gatekeeper.returncode == 0,
            },
            "open": [
                "developer-id-signing",
                "notarization",
                "gatekeeper-public-admission",
                "maintained-coding-surface",
            ],
            "privacy": {"privateIdentityRetained": False, "privatePathRetained": False, "rawToolOutputRetained": False},
            "authority": {"runtimeAdmissionGranted": False, "packageAdmissionGranted": False, "releasePromotionAllowed": False},
        }
        require(adhoc and not developer_id and gatekeeper.returncode != 0, "unexpected-platform-trust-state")
        atomic_write(output, result)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = inspect_archive(args.archive, args.output)
    except (DistributionError, OSError, tarfile.TarError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    print(json.dumps({"status": result["status"], "result": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
