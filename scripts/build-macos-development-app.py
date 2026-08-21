#!/usr/bin/env python3
"""Wrap an exact Haven 42 one-folder build in an unsigned macOS app bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import tarfile


ROOT = Path(__file__).resolve().parent.parent
BUNDLE_NAME = "Haven 42.app"
BUNDLE_IDENTIFIER = "org.haven42.desktop"
ALLOWED_VERSIONS = {"0.4.0-alpha.1", "0.4.0-alpha.2"}
BUNDLE_VERSIONS = {
    "0.4.0-alpha.1": {"short": "0.4.0", "build": "0.4.1"},
    "0.4.0-alpha.2": {"short": "0.4.0", "build": "0.4.2"},
}
ALLOWED_SOURCE_ENTRIES = {
    "haven42", "_internal", "DEVELOPMENT-BUILD.txt", "LICENSE.txt",
    "THIRD-PARTY-NOTICES.txt", "licenses",
}
ALLOWED_SOURCE_LINKS = {
    "_internal/Python": "Python.framework/Versions/3.14/Python",
    "_internal/Python.framework/Python": "Versions/Current/Python",
    "_internal/Python.framework/Resources": "Versions/Current/Resources",
    "_internal/Python.framework/Versions/Current": "3.14",
}


class AppBuildError(RuntimeError):
    """Raised when a development app cannot be built safely."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def safe_files(
    root: Path,
    allowed_links: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    resolved_root = root.resolve()
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            relative = path.relative_to(root).as_posix()
            try:
                target = path.readlink().as_posix()
                resolved = path.resolve(strict=True)
                resolved.relative_to(resolved_root)
            except (OSError, ValueError) as error:
                raise AppBuildError("bundle-link-escaped-root") from error
            if allowed_links is None or allowed_links.get(relative) != target:
                raise AppBuildError("unexpected-bundle-link")
            continue
        if not path.is_file():
            continue
        try:
            path.resolve(strict=True).relative_to(resolved_root)
        except (OSError, ValueError) as error:
            raise AppBuildError("bundle-file-escaped-root") from error
        records.append({
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256(path),
            "sizeBytes": path.stat().st_size,
        })
    return sorted(records, key=lambda item: str(item["path"]))


def validate_source_package(source: Path) -> None:
    if not source.is_dir() or source.is_symlink():
        raise AppBuildError("source-package-not-found")
    unexpected = {path.name for path in source.iterdir()} - ALLOWED_SOURCE_ENTRIES
    if unexpected:
        raise AppBuildError(f"unexpected-source-entry:{sorted(unexpected)}")
    executable = source / "haven42"
    required = (
        executable, source / "_internal", source / "DEVELOPMENT-BUILD.txt",
        source / "LICENSE.txt", source / "THIRD-PARTY-NOTICES.txt",
        source / "licenses",
    )
    if not all(path.exists() and not path.is_symlink() for path in required):
        raise AppBuildError("incomplete-source-package")
    if not executable.is_file() or (
        os.name != "nt" and not (executable.stat().st_mode & stat.S_IXUSR)
    ):
        raise AppBuildError("source-executable-is-not-executable")
    # PyInstaller's pinned macOS framework layout contains four conventional
    # internal links.  Admit only those exact link names and targets, prove
    # they resolve inside the package, then dereference them into the app.
    safe_files(source, ALLOWED_SOURCE_LINKS)


def resolve_output(value: str) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        requested = ROOT / requested
    output = requested.resolve()
    allowed = (ROOT / "dist").resolve()
    try:
        relative = output.relative_to(allowed)
    except ValueError as error:
        raise AppBuildError("output-must-stay-beneath-dist") from error
    if not relative.parts or output.is_symlink():
        raise AppBuildError("unsafe-output-directory")
    return output


def info_plist(version: str) -> dict[str, object]:
    if version not in ALLOWED_VERSIONS:
        raise AppBuildError("unsupported-app-version")
    bundle_version = BUNDLE_VERSIONS[version]
    return {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleDisplayName": "Haven 42",
        "CFBundleExecutable": "haven42",
        "CFBundleIdentifier": BUNDLE_IDENTIFIER,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "Haven 42",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": bundle_version["short"],
        "CFBundleVersion": bundle_version["build"],
        "Haven42ReleaseVersion": version,
        "LSApplicationCategoryType": "public.app-category.utilities",
        "LSMinimumSystemVersion": "13.0",
        "LSMultipleInstancesProhibited": True,
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "Copyright Haven 42 contributors",
        "NSLocalNetworkUsageDescription": (
            "Haven 42 connects only to an AI server you choose on your private "
            "network. It does not scan for nearby devices."
        ),
    }


def build_bundle(source: Path, output: Path, version: str) -> dict[str, object]:
    validate_source_package(source)
    if output.exists():
        raise AppBuildError("output-already-exists")
    output.mkdir(parents=True)
    app = output / BUNDLE_NAME
    contents = app / "Contents"
    macos = contents / "MacOS"
    frameworks = contents / "Frameworks"
    resources = contents / "Resources"
    portable_resources = resources / "PortablePackage"
    macos.mkdir(parents=True)
    frameworks.mkdir()
    resources.mkdir()
    portable_resources.mkdir()

    shutil.copy2(source / "haven42", macos / "haven42")
    for path in sorted((source / "_internal").iterdir()):
        destination = frameworks / path.name
        if path.is_dir():
            shutil.copytree(path, destination, symlinks=False)
        else:
            shutil.copy2(path, destination, follow_symlinks=True)
    for name in (
        "DEVELOPMENT-BUILD.txt", "LICENSE.txt", "THIRD-PARTY-NOTICES.txt",
    ):
        shutil.copy2(source / name, portable_resources / name)
    shutil.copytree(
        source / "licenses", portable_resources / "licenses", symlinks=False,
    )
    plist = info_plist(version)
    with (contents / "Info.plist").open("wb") as stream:
        plistlib.dump(plist, stream, sort_keys=True)
    (contents / "PkgInfo").write_bytes(b"APPL????")
    (resources / "README.txt").write_text(
        "Haven 42 unsigned development app.\n"
        "Double-clicking starts a private loopback server and opens the UI.\n"
        "This build is not Developer ID signed or notarized and is not a public release.\n",
        encoding="utf-8",
    )

    records = safe_files(app)
    result: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "haven42-unsigned-macos-development-app-build",
        "status": "development-only",
        "application": {
            "name": "Haven 42", "version": version,
            "bundleIdentifier": BUNDLE_IDENTIFIER,
            "bundleShortVersion": BUNDLE_VERSIONS[version]["short"],
            "bundleVersion": BUNDLE_VERSIONS[version]["build"],
            "minimumSystemVersion": "13.0",
        },
        "runtime": {
            "globalPythonRequired": False,
            "entryPoint": "Haven 42.app/Contents/MacOS/haven42",
            "browserUi": True,
        },
        "platformTrust": {
            "developerIdSigned": False, "notarized": False,
            "gatekeeperAdmissionClaimed": False,
            "publicDistributionAllowed": False,
        },
        "inventory": {
            "algorithm": "sha256",
            "canonicalSha256": canonical_sha256(records),
            "fileCount": len(records), "files": records,
        },
    }
    evidence = output / "macos-app-build-result.json"
    evidence.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    archive = output / "haven42-darwin-arm64-unsigned-development-app.tar.gz"
    with tarfile.open(archive, "w:gz", dereference=True) as stream:
        stream.add(app, arcname=BUNDLE_NAME, recursive=True)
    (output / "SHA256SUMS").write_text(
        f"{sha256(archive)}  {archive.name}\n"
        f"{sha256(evidence)}  {evidence.name}\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-package", required=True)
    parser.add_argument("--output", default="dist/macos-development-app")
    parser.add_argument("--version", default="0.4.0-alpha.2")
    args = parser.parse_args()
    try:
        output = resolve_output(args.output)
        build_bundle(Path(args.source_package).expanduser().resolve(), output, args.version)
    except AppBuildError as error:
        parser.error(str(error))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
