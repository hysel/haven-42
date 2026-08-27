#!/usr/bin/env python3
"""Assemble and verify an unsigned Linux Alpha 2 release-candidate packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.4.0-alpha.2"
PORTABLE_ARCHIVE = "haven42-linux-x86_64-unsigned-development.tar.gz"
ARCHIVE_NAME = f"haven42-{VERSION}-linux-x64-unsigned.tar.gz"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_EVIDENCE = {
    "APACHE-2.0.txt", "CPYTHON-3.14.6-LICENSE.txt", "LIBFFI-3.4.4-LICENSE.txt",
    "OLLAMA-MIT-LICENSE.txt",
    "THIRD-PARTY-NOTICES.txt", "build-provenance.json", "dependency-inventory.json",
    "haven42.cdx.json", "package-file-inventory.json", "runtime-component-inventory.json",
}
KNOWN_LIMITATIONS_NAME = "KNOWN-LIMITATIONS.md"
KNOWN_LIMITATIONS_SOURCE = ROOT / "docs" / "alpha-2-known-limitations.md"
CANDIDATE_EVIDENCE = REQUIRED_EVIDENCE | {KNOWN_LIMITATIONS_NAME}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def normalized_known_limitations() -> bytes:
    try:
        text = KNOWN_LIMITATIONS_SOURCE.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError("candidate-known-limitations-unreadable") from error
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def load_provenance(artifacts: Path) -> dict:
    try:
        value = json.loads(
            (artifacts / "build-provenance.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("candidate-provenance-unreadable") from error
    source = value.get("source", {})
    if (
        value.get("application") != {"name": "Haven 42", "version": VERSION}
        or value.get("environment", {}).get("operatingSystem") != "linux"
        or value.get("environment", {}).get("architecture") not in {"amd64", "x86_64"}
        or value.get("security", {}).get("signed") is not False
        or value.get("security", {}).get("releasePublished") is not False
        or not FULL_COMMIT.fullmatch(str(source.get("commit", "")))
        or source.get("commitIsExactSource") is not True
        or source.get("treeState") != "exact-commit"
    ):
        raise ValueError("candidate-provenance-mismatch")
    return value


def build(portable_root: Path, output: Path) -> dict:
    if platform.system() != "Linux" or platform.machine().casefold() not in {"amd64", "x86_64"}:
        raise ValueError("linux-x64-required")
    artifacts = portable_root / "artifacts"
    source_archive = artifacts / PORTABLE_ARCHIVE
    if not source_archive.is_file() or source_archive.is_symlink():
        raise ValueError("exact-portable-archive-required")
    missing = sorted(name for name in REQUIRED_EVIDENCE if not (artifacts / name).is_file())
    if missing:
        raise ValueError("candidate-evidence-incomplete")
    if not KNOWN_LIMITATIONS_SOURCE.is_file() or KNOWN_LIMITATIONS_SOURCE.is_symlink():
        raise ValueError("candidate-known-limitations-required")
    provenance = load_provenance(artifacts)
    output.mkdir(parents=True, exist_ok=True)
    candidate = output / ARCHIVE_NAME
    if candidate.exists():
        candidate.unlink()
    shutil.copy2(source_archive, candidate)
    for name in sorted(REQUIRED_EVIDENCE):
        shutil.copy2(artifacts / name, output / name)
    (output / KNOWN_LIMITATIONS_NAME).write_bytes(normalized_known_limitations())
    archive_digest = digest(candidate)
    limitations_digest = digest(output / KNOWN_LIMITATIONS_NAME)
    source = provenance["source"]
    manifest = {
        "schemaVersion": 1,
        "kind": "unsigned-linux-alpha2-release-candidate",
        "version": VERSION,
        "platform": "linux-x64",
        "archive": {
            "name": ARCHIVE_NAME,
            "sizeBytes": candidate.stat().st_size,
            "sha256": archive_digest,
        },
        "knownLimitations": {
            "name": KNOWN_LIMITATIONS_NAME,
            "sha256": limitations_digest,
        },
        "sourceCommit": source["commit"],
        "exactSourceCommit": source["commitIsExactSource"],
        "treeState": source["treeState"],
        "signed": False,
        "publicReleaseAllowed": False,
        "distributionAuthorized": False,
        "productionReady": False,
        "nativeValidationRequired": True,
        "alpha1AssetsMayBeModified": False,
    }
    (output / "candidate-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / f"{ARCHIVE_NAME}.sha256").write_text(
        f"{archive_digest}  {ARCHIVE_NAME}\n", encoding="ascii"
    )
    return verify(output)


def verify(output: Path) -> dict:
    try:
        manifest = json.loads(
            (output / "candidate-manifest.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid-candidate-manifest") from error
    required = {
        "schemaVersion", "kind", "version", "platform", "archive", "knownLimitations",
        "sourceCommit",
        "exactSourceCommit", "treeState", "signed", "publicReleaseAllowed",
        "distributionAuthorized", "productionReady", "nativeValidationRequired",
        "alpha1AssetsMayBeModified",
    }
    expected_files = CANDIDATE_EVIDENCE | {
        ARCHIVE_NAME,
        f"{ARCHIVE_NAME}.sha256",
        "candidate-manifest.json",
    }
    if (
        not output.is_dir()
        or any(path.is_symlink() or not path.is_file() for path in output.iterdir())
        or {path.name for path in output.iterdir() if path.is_file()} != expected_files
    ):
        raise ValueError("candidate-file-set-invalid")
    archive = manifest.get("archive", {})
    known_limitations = manifest.get("knownLimitations", {})
    if (
        set(manifest) != required
        or manifest.get("schemaVersion") != 1
        or manifest.get("kind") != "unsigned-linux-alpha2-release-candidate"
        or manifest.get("version") != VERSION
        or manifest.get("platform") != "linux-x64"
        or archive.get("name") != ARCHIVE_NAME
        or known_limitations.get("name") != KNOWN_LIMITATIONS_NAME
        or not SHA256.fullmatch(str(known_limitations.get("sha256", "")))
        or not FULL_COMMIT.fullmatch(str(manifest.get("sourceCommit", "")))
        or manifest.get("exactSourceCommit") is not True
        or manifest.get("treeState") != "exact-commit"
        or any(manifest.get(key) is not False for key in (
            "signed", "publicReleaseAllowed", "distributionAuthorized",
            "productionReady", "alpha1AssetsMayBeModified",
        ))
        or manifest.get("nativeValidationRequired") is not True
    ):
        raise ValueError("candidate-authority-invalid")
    candidate = output / ARCHIVE_NAME
    if (
        not candidate.is_file()
        or candidate.is_symlink()
        or candidate.stat().st_size != archive.get("sizeBytes")
        or not SHA256.fullmatch(str(archive.get("sha256", "")))
        or digest(candidate) != archive["sha256"]
    ):
        raise ValueError("candidate-archive-integrity-failed")
    if (output / f"{ARCHIVE_NAME}.sha256").read_text(encoding="ascii") != (
        f"{archive['sha256']}  {ARCHIVE_NAME}\n"
    ):
        raise ValueError("candidate-checksum-mismatch")
    limitations = output / KNOWN_LIMITATIONS_NAME
    if digest(limitations) != known_limitations["sha256"]:
        raise ValueError("candidate-known-limitations-integrity-failed")
    if any(not (output / name).is_file() for name in CANDIDATE_EVIDENCE):
        raise ValueError("candidate-evidence-incomplete")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portable-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    result = verify(output) if args.verify_only else build(
        Path(args.portable_root).resolve(), output
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
