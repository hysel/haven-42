#!/usr/bin/env python3
"""Fail-closed verifier for an unsigned Haven 42 macOS development app."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import plistlib
import re
import tarfile


APP_NAME = "Haven 42.app"
ARCHIVE_NAME = "haven42-darwin-arm64-unsigned-development-app.tar.gz"
EXPECTED_FILES = {APP_NAME, ARCHIVE_NAME, "macos-app-build-result.json", "SHA256SUMS"}
RESOURCE_RUNTIME_ENTRIES = {
    "base_library.zip", "config", "package", "scripts", "web",
}
APP_LINKS = {
    "Contents/Frameworks/Python": "Python.framework/Versions/3.14/Python",
    "Contents/Frameworks/Python.framework/Python": "Versions/Current/Python",
    "Contents/Frameworks/Python.framework/Resources": "Versions/Current/Resources",
    "Contents/Frameworks/Python.framework/Versions/Current": "3.14",
    **{
        f"Contents/Frameworks/{name}": f"../Resources/Runtime/{name}"
        for name in RESOURCE_RUNTIME_ENTRIES
    },
    "Contents/Frameworks/python3.14": "python3__dot__14",
    "Contents/Resources/python3.14": "../Frameworks/python3__dot__14",
}
EXPECTED_FRAMEWORK_ENTRIES = (
    RESOURCE_RUNTIME_ENTRIES
    | {
        "Python", "Python.framework", "libcrypto.3.dylib", "libssl.3.dylib",
        "libzstd.1.dylib", "python3.14", "python3__dot__14",
    }
)
EXPECTED_RESOURCE_ENTRIES = {
    "PortablePackage", "README.txt", "Runtime", "python3.14",
}


class ValidationError(RuntimeError):
    """Raised when the app bundle or evidence is unsafe or inconsistent."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return sha256_bytes(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8"))


def app_inventory(
    app: Path,
) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    if not app.is_dir() or app.is_symlink():
        raise ValidationError("app-bundle-missing")
    records: list[dict[str, object]] = []
    links: list[dict[str, str]] = []
    resolved_app = app.resolve()
    for path in sorted(app.rglob("*")):
        if path.is_symlink():
            relative = path.relative_to(app).as_posix()
            try:
                target = path.readlink().as_posix()
                path.resolve(strict=True).relative_to(resolved_app)
            except (OSError, ValueError) as error:
                raise ValidationError("app-bundle-link-escaped-root") from error
            if APP_LINKS.get(relative) != target:
                raise ValidationError("unexpected-app-bundle-link")
            links.append({"path": relative, "target": target})
            continue
        if path.is_file():
            records.append({
                "path": path.relative_to(app).as_posix(),
                "sha256": sha256(path),
                "sizeBytes": path.stat().st_size,
            })
    if {item["path"] for item in links} != set(APP_LINKS):
        raise ValidationError("required-app-bundle-link-missing")
    return (
        sorted(records, key=lambda item: str(item["path"])),
        sorted(links, key=lambda item: item["path"]),
    )


def safe_member(name: str) -> str:
    if not name or "\\" in name or "\x00" in name or name.startswith("/"):
        raise ValidationError("unsafe-archive-member")
    path = PurePosixPath(name)
    if path.parts[0] != APP_NAME or any(part in {"", ".", ".."} for part in path.parts):
        raise ValidationError("unsafe-archive-member")
    return path.as_posix()


def archive_inventory(
    archive: Path,
) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    records: list[dict[str, object]] = []
    links: list[dict[str, str]] = []
    names: set[str] = set()
    folded: set[str] = set()
    try:
        stream = tarfile.open(archive, "r:gz")
    except (OSError, tarfile.TarError) as error:
        raise ValidationError("invalid-app-archive") from error
    with stream:
        for member in stream.getmembers():
            name = safe_member(member.name)
            folded_name = name.casefold()
            if name in names or folded_name in folded:
                raise ValidationError("duplicate-archive-member")
            names.add(name)
            folded.add(folded_name)
            if member.isdir():
                continue
            relative = PurePosixPath(name).relative_to(APP_NAME).as_posix()
            if member.issym():
                if APP_LINKS.get(relative) != member.linkname or member.size != 0:
                    raise ValidationError("unexpected-archive-link")
                links.append({"path": relative, "target": member.linkname})
                continue
            if not member.isfile() or member.size > 134_217_728:
                raise ValidationError("non-regular-archive-member")
            extracted = stream.extractfile(member)
            if extracted is None:
                raise ValidationError("invalid-app-archive")
            data = extracted.read(134_217_729)
            if len(data) != member.size:
                raise ValidationError("invalid-app-archive")
            records.append({
                "path": relative,
                "sha256": sha256_bytes(data),
                "sizeBytes": len(data),
            })
    if {item["path"] for item in links} != set(APP_LINKS):
        raise ValidationError("required-archive-link-missing")
    return (
        sorted(records, key=lambda item: str(item["path"])),
        sorted(links, key=lambda item: item["path"]),
    )


def checksums(directory: Path) -> dict[str, str]:
    lines = (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    parsed: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9._-]+)", line)
        if not match or match.group(2) in parsed:
            raise ValidationError("invalid-checksum-file")
        parsed[match.group(2)] = match.group(1)
    return parsed


def validate(directory: Path) -> dict[str, object]:
    if not directory.is_dir() or directory.is_symlink():
        raise ValidationError("app-output-not-found")
    if {path.name for path in directory.iterdir()} != EXPECTED_FILES:
        raise ValidationError("unexpected-app-output-entry")
    app = directory / APP_NAME
    contents = app / "Contents"
    if (
        {path.name for path in contents.iterdir()}
        != {"Frameworks", "Info.plist", "MacOS", "PkgInfo", "Resources"}
        or {path.name for path in (contents / "MacOS").iterdir()} != {"haven42"}
        or {path.name for path in (contents / "Frameworks").iterdir()}
        != EXPECTED_FRAMEWORK_ENTRIES
        or {path.name for path in (contents / "Resources").iterdir()}
        != EXPECTED_RESOURCE_ENTRIES
    ):
        raise ValidationError("unexpected-app-bundle-layout")
    archive = directory / ARCHIVE_NAME
    evidence_path = directory / "macos-app-build-result.json"
    expected_checksums = {
        ARCHIVE_NAME: sha256(archive),
        evidence_path.name: sha256(evidence_path),
    }
    if checksums(directory) != expected_checksums:
        raise ValidationError("app-output-checksum-mismatch")
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("invalid-app-build-result") from error
    if (
        evidence.get("schemaVersion") != 1
        or evidence.get("kind") != "haven42-unsigned-macos-development-app-build"
        or evidence.get("status") != "development-only"
        or evidence.get("application", {}).get("bundleIdentifier") != "org.haven42.desktop"
        or evidence.get("application", {}).get("version") not in {"0.4.0-alpha.1", "0.4.0-alpha.2"}
        or evidence.get("runtime") != {
            "browserUi": True,
            "entryPoint": "Haven 42.app/Contents/MacOS/haven42",
            "globalPythonRequired": False,
        }
        or evidence.get("platformTrust") != {
            "developerIdSigned": False,
            "gatekeeperAdmissionClaimed": False,
            "notarized": False,
            "publicDistributionAllowed": False,
        }
    ):
        raise ValidationError("invalid-app-build-result")
    records, links = app_inventory(app)
    inventory = evidence.get("inventory")
    if inventory != {
        "algorithm": "sha256",
        "canonicalSha256": canonical_sha256({"files": records, "links": links}),
        "fileCount": len(records),
        "linkCount": len(links),
        "files": records,
        "links": links,
    }:
        raise ValidationError("app-inventory-mismatch")
    if archive_inventory(archive) != (records, links):
        raise ValidationError("app-archive-inventory-mismatch")
    try:
        with (app / "Contents" / "Info.plist").open("rb") as stream:
            plist = plistlib.load(stream)
    except (OSError, plistlib.InvalidFileException) as error:
        raise ValidationError("invalid-app-info-plist") from error
    application = evidence["application"]
    if (
        plist.get("CFBundleIdentifier") != application["bundleIdentifier"]
        or plist.get("CFBundleShortVersionString") != application["bundleShortVersion"]
        or plist.get("CFBundleVersion") != application["bundleVersion"]
        or plist.get("Haven42ReleaseVersion") != application["version"]
        or plist.get("CFBundleExecutable") != "haven42"
        or plist.get("CFBundlePackageType") != "APPL"
        or plist.get("LSMinimumSystemVersion") != application["minimumSystemVersion"]
        or plist.get("LSMultipleInstancesProhibited") is not True
        or plist.get("LSUIElement") is not True
    ):
        raise ValidationError("app-info-plist-mismatch")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_directory")
    args = parser.parse_args()
    try:
        result = validate(Path(args.artifact_directory).resolve())
    except ValidationError as error:
        parser.error(str(error))
    print(json.dumps({
        "status": "passed",
        "kind": result["kind"],
        "version": result["application"]["version"],
        "fileCount": result["inventory"]["fileCount"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
