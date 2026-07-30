#!/usr/bin/env python3
"""Validate the pypdf candidate artifact lock without installing the wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "config" / "pdf-parser-artifact-lock.json"
REVIEW_PATH = ROOT / "config" / "pdf-parser-candidate-review.json"
WORKER_PATH = ROOT / "config" / "restricted-parser-worker-contract.json"
MAXIMUM_WHEEL_BYTES = 500_000
MAXIMUM_WHEEL_ENTRIES = 100
MAXIMUM_TOTAL_UNCOMPRESSED_BYTES = 2_000_000
MAXIMUM_ENTRY_BYTES = 500_000


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def suspicious_entry_names(names: list[str]) -> list[str]:
    return [
        name
        for name in names
        if name.startswith("/")
        or "\\" in name
        or re.match(r"^[A-Za-z]:", name)
        or ".." in PurePosixPath(name).parts
    ]


def validate_wheel(path: Path, lock: dict, require) -> None:
    artifact = lock["artifact"]
    require(path.name == artifact["filename"], "wheel filename")
    require(path.is_file() and not path.is_symlink(), "wheel is a regular non-symlink file")
    require(path.stat().st_size <= MAXIMUM_WHEEL_BYTES, "wheel fixed byte ceiling")
    require(path.stat().st_size == artifact["sizeBytes"], "wheel byte count")
    require(sha256_file(path) == artifact["sha256"], "wheel SHA-256")
    with zipfile.ZipFile(path) as wheel:
        entries = wheel.infolist()
        names = [entry.filename for entry in entries]
        require(len(entries) <= MAXIMUM_WHEEL_ENTRIES, "wheel fixed entry ceiling")
        require(len(entries) == artifact["entryCount"], "wheel entry count")
        require(sum(entry.file_size for entry in entries) <= MAXIMUM_TOTAL_UNCOMPRESSED_BYTES, "wheel fixed expansion ceiling")
        require(sum(entry.compress_size for entry in entries) == artifact["totalCompressedBytes"], "compressed byte total")
        require(sum(entry.file_size for entry in entries) == artifact["totalUncompressedBytes"], "uncompressed byte total")
        require(max(entry.file_size for entry in entries) <= MAXIMUM_ENTRY_BYTES, "wheel fixed per-entry ceiling")
        require(max(entry.file_size for entry in entries) == artifact["maximumEntryBytes"], "maximum entry size")
        suspicious = suspicious_entry_names(names)
        require(suspicious == [], "no absolute, traversal, drive, or backslash entries")
        native_suffixes = (".dll", ".dylib", ".exe", ".pyd", ".so")
        require(not any(name.lower().endswith(native_suffixes) for name in names), "no native binary entries")
        require(sha256_bytes(wheel.read(lock["metadata"]["path"])) == lock["metadata"]["sha256"], "metadata SHA-256")
        require(sha256_bytes(wheel.read(lock["license"]["path"])) == lock["license"]["sha256"], "license SHA-256")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, help="Optional exact wheel to verify without installing.")
    args = parser.parse_args()

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    worker = json.loads(WORKER_PATH.read_text(encoding="utf-8"))
    checks: list[str] = []

    def require(condition: bool, label: str) -> None:
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    require(lock["schemaVersion"] == 1, "versioned lock")
    require(lock["status"] == "artifact-verified-dependency-not-admitted", "artifact-only status")
    require(lock["verifiedDate"] == "2026-07-30", "verification date")
    require(lock["package"] == review["preferredCandidate"]["package"] == "pypdf", "candidate package parity")
    require(lock["version"] == review["preferredCandidate"]["version"] == "6.14.2", "candidate version parity")

    artifact = lock["artifact"]
    require(artifact["filename"] == "pypdf-6.14.2-py3-none-any.whl", "exact wheel filename")
    require(artifact["wheelTag"] == "py3-none-any", "universal wheel tag")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])), "wheel digest shape")
    require(artifact["sizeBytes"] == 349514, "wheel size")
    require(0 < artifact["totalCompressedBytes"] <= artifact["sizeBytes"], "bounded compressed bytes")
    require(artifact["totalUncompressedBytes"] <= 2_000_000, "bounded uncompressed bytes")
    require(artifact["maximumEntryBytes"] <= 500_000, "bounded entry bytes")
    require(artifact["suspiciousEntryNames"] == 0, "recorded safe entry names")
    require(artifact["nativeBinaryEntries"] == 0, "recorded no native binaries")
    artifact_url = urlparse(artifact["url"])
    require(artifact_url.scheme == "https" and artifact_url.hostname == "files.pythonhosted.org", "artifact source allowlist")
    require(not artifact_url.username and not artifact_url.password, "artifact URL has no credentials")

    metadata = lock["metadata"]
    license_info = lock["license"]
    require(metadata["name"] == lock["package"] and metadata["version"] == lock["version"], "metadata identity")
    require(metadata["licenseExpression"] == license_info["expression"] == "BSD-3-Clause", "license parity")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", metadata["sha256"])), "metadata digest shape")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", license_info["sha256"])), "license digest shape")
    require(metadata["path"].startswith("pypdf-6.14.2.dist-info/"), "metadata path boundary")
    require(license_info["path"].startswith("pypdf-6.14.2.dist-info/licenses/"), "license path boundary")

    dependencies = lock["dependencyReview"]
    require(dependencies["packagingPython"] == "3.14.6", "packaging Python identity")
    require(dependencies["mandatoryForPackagingPython"] == [], "no mandatory packaging dependency")
    require(dependencies["extrasSelected"] == [], "no extras selected")
    require(set(dependencies["excludedOptionalFamilies"]) == {
        "crypto", "cryptodome", "dev", "docs", "fonts", "full", "image"
    }, "all optional families excluded")
    require(dependencies["conditionalForPython39And310"] == ["typing_extensions>=4.0"], "older-Python conditional recorded")

    require(all(urlparse(source).scheme == "https" for source in lock["sources"]), "HTTPS evidence sources")
    require({urlparse(source).hostname for source in lock["sources"]} <= {"pypi.org", "github.com"}, "evidence host allowlist")
    require(all(value is False for value in lock["admission"].values()), "all admission authority denied")
    require(all(value is False for value in lock["effects"].values()), "all effects denied")
    require(worker["parserDependenciesAdmitted"] == [], "worker dependency list empty")
    require(worker["workerProcessAllowed"] is False and worker["runtimeRouteAllowed"] is False, "worker and route denied")

    if args.wheel is not None:
        validate_wheel(args.wheel.resolve(), lock, require)

    suffix = " including the supplied wheel" if args.wheel is not None else ""
    print(f"PDF parser artifact lock passed {len(checks)} fail-closed checks{suffix}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
