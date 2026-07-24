#!/usr/bin/env python3
"""Fail-closed verification for unsigned portable development artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import tempfile
import zipfile


SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_EVIDENCE = {
    "THIRD-PARTY-NOTICES.txt",
    "build-provenance.json",
    "dependency-inventory.json",
    "haven42.cdx.json",
    "package-file-inventory.json",
}
EXPECTED_COMMON_BUILD_DEPENDENCIES = {
    "altgraph": ("0.17.5", "MIT"),
    "packaging": ("26.2", "Apache-2.0 OR BSD-2-Clause"),
    "pyinstaller": ("6.21.0", "GPL-2.0-or-later WITH Bootloader-exception"),
    "pyinstaller-hooks-contrib": (
        "2026.6", "GPL-2.0-or-later WITH Bootloader-exception",
    ),
    "setuptools": ("83.0.0", "MIT"),
}
EXPECTED_PLATFORM_BUILD_DEPENDENCIES = {
    "windows": {
        "pefile": ("2024.8.26", "MIT"),
        "pywin32-ctypes": ("0.2.3", "BSD-3-Clause"),
    },
    "darwin": {"macholib": ("1.16.3", "MIT")},
    "linux": {},
}
ALLOWED_ARCHITECTURES = {
    "windows": {"amd64", "arm64", "x86_64"},
    "linux": {"aarch64", "arm64", "x86_64"},
    "darwin": {"arm64", "x86_64"},
}
MAX_ARCHIVE_FILES = 10_000
MAX_ARCHIVE_MEMBER_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_TOTAL_BYTES = 512 * 1024 * 1024


class ArtifactVerificationError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_member_name(value: str) -> str:
    if "\\" in value or "\x00" in value:
        raise ArtifactVerificationError("unsafe-archive-member")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or path.parts[0] != "haven42":
        raise ArtifactVerificationError("unsafe-archive-member")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ArtifactVerificationError("unsafe-archive-member")
    return path.as_posix()


def read_archive_files(path: Path) -> dict[str, tuple[int, str]]:
    files: dict[str, tuple[int, str]] = {}
    total_bytes = 0

    def add(name: str, data: bytes) -> None:
        nonlocal total_bytes
        if len(files) >= MAX_ARCHIVE_FILES:
            raise ArtifactVerificationError("archive-file-count-exceeded")
        if len(data) > MAX_ARCHIVE_MEMBER_BYTES:
            raise ArtifactVerificationError("archive-member-size-exceeded")
        total_bytes += len(data)
        if total_bytes > MAX_ARCHIVE_TOTAL_BYTES:
            raise ArtifactVerificationError("archive-total-size-exceeded")
        safe = safe_member_name(name)
        relative = PurePosixPath(safe).relative_to("haven42").as_posix()
        if not relative or relative.casefold() in {item.casefold() for item in files}:
            raise ArtifactVerificationError("duplicate-archive-member")
        files[relative] = (len(data), sha256_bytes(data))

    if path.name.endswith(".zip"):
        try:
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    unix_mode = (member.external_attr >> 16) & 0o170000
                    if member.flag_bits & 0x1:
                        raise ArtifactVerificationError("encrypted-archive-member")
                    if unix_mode == 0o120000:
                        raise ArtifactVerificationError("non-regular-archive-member")
                    if member.is_dir():
                        safe_member_name(member.filename.rstrip("/"))
                        continue
                    add(member.filename, archive.read(member))
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            raise ArtifactVerificationError("invalid-zip-archive") from error
    elif path.name.endswith(".tar.gz"):
        try:
            with tarfile.open(path, "r:gz") as archive:
                for member in archive.getmembers():
                    safe_member_name(member.name)
                    if member.isdir():
                        continue
                    if not member.isfile():
                        raise ArtifactVerificationError("non-regular-archive-member")
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise ArtifactVerificationError("unreadable-archive-member")
                    add(member.name, stream.read())
        except (OSError, tarfile.TarError) as error:
            raise ArtifactVerificationError("invalid-tar-archive") from error
    else:
        raise ArtifactVerificationError("unsupported-archive-format")
    if not files:
        raise ArtifactVerificationError("empty-archive")
    return files


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ArtifactVerificationError(f"invalid-json:{path.name}") from error
    if not isinstance(value, dict):
        raise ArtifactVerificationError(f"invalid-json:{path.name}")
    return value


def expected_package_files(path: Path) -> dict[str, tuple[int, str]]:
    value = load_json(path)
    if (
        set(value) != {"algorithm", "files", "packageRoot", "schemaVersion"}
        or value["schemaVersion"] != 1
        or value["algorithm"] != "sha256"
        or value["packageRoot"] != "haven42"
        or not isinstance(value["files"], list)
    ):
        raise ArtifactVerificationError("invalid-package-file-inventory")
    result: dict[str, tuple[int, str]] = {}
    folded_names: set[str] = set()
    for record in value["files"]:
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "sizeBytes"}:
            raise ArtifactVerificationError("invalid-package-file-record")
        name = str(record["path"])
        safe_member_name(f"haven42/{name}")
        digest = str(record["sha256"])
        size = record["sizeBytes"]
        if (
            name in result
            or name.casefold() in folded_names
            or not SHA256.fullmatch(digest)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
        ):
            raise ArtifactVerificationError("invalid-package-file-record")
        result[name] = (size, digest)
        folded_names.add(name.casefold())
    if not result:
        raise ArtifactVerificationError("empty-package-file-inventory")
    return result


def verify_checksums(directory: Path) -> None:
    checksum_path = directory / "SHA256SUMS"
    try:
        lines = checksum_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ArtifactVerificationError("missing-checksums") from error
    expected_names = {path.name for path in directory.iterdir() if path.is_file()} - {"SHA256SUMS"}
    seen: set[str] = set()
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._-]{0,199})", line)
        if not match or match.group(2) in seen:
            raise ArtifactVerificationError("invalid-checksum-record")
        digest, name = match.groups()
        target = directory / name
        if (
            name not in expected_names
            or not target.is_file()
            or target.is_symlink()
            or sha256_file(target) != digest
        ):
            raise ArtifactVerificationError("checksum-mismatch")
        seen.add(name)
    if seen != expected_names:
        raise ArtifactVerificationError("checksum-coverage-mismatch")


def verify_evidence(directory: Path) -> None:
    inventory = load_json(directory / "dependency-inventory.json")
    provenance = load_json(directory / "build-provenance.json")
    environment = provenance.get("environment", {})
    application = provenance.get("application", {})
    source = provenance.get("source", {})
    builder = provenance.get("builder", {})
    operating_system = environment.get("operatingSystem")
    architecture = environment.get("architecture")
    target = inventory.get("target")
    if (
        inventory.get("schemaVersion") != 2
        or set(inventory) != {
            "schemaVersion", "target", "runtimeComponents", "buildDependencies",
        }
        or not isinstance(inventory.get("runtimeComponents"), list)
        or not isinstance(inventory.get("buildDependencies"), list)
        or inventory["runtimeComponents"] != [{
            "name": "CPython",
            "scope": "embedded-runtime",
            "version": provenance.get("environment", {}).get("pythonVersion"),
        }]
        or operating_system not in EXPECTED_PLATFORM_BUILD_DEPENDENCIES
        or architecture not in ALLOWED_ARCHITECTURES.get(str(operating_system), set())
        or target != f"{operating_system}-{architecture}"
    ):
        raise ArtifactVerificationError("invalid-dependency-inventory")
    commit = provenance.get("source", {}).get("commit", "")
    security = provenance.get("security", {})
    if (
        set(provenance) != {
            "schemaVersion", "artifactKind", "application", "source",
            "builder", "environment", "security",
        }
        or provenance.get("schemaVersion") != 1
        or provenance.get("artifactKind") != "unsigned-development"
        or application != {"name": "Haven 42", "version": "0.3.0"}
        or source.get("repository") != "https://github.com/hysel/haven-42"
        or set(source) != {"repository", "commit"}
        or set(builder) != {"kind", "workflow", "runId"}
        or builder.get("kind") not in {"github-actions", "local"}
        or not all(isinstance(builder.get(field), str) and builder[field] for field in ("workflow", "runId"))
        or set(environment) != {
            "operatingSystem", "architecture", "pythonImplementation",
            "pythonVersion", "pyinstallerVersion",
        }
        or environment.get("pythonImplementation") != "CPython"
        or environment.get("pyinstallerVersion") != "6.21.0"
        or not all(
            isinstance(environment.get(field), str) and environment[field]
            for field in environment
        )
        or not re.fullmatch(r"[0-9a-f]{40}", str(commit))
        or security != {
            "attested": False,
            "dependencyHashesRequired": True,
            "notarized": False,
            "releasePublished": False,
            "resourceIntegrityManifestEmbedded": True,
            "signed": False,
        }
    ):
        raise ArtifactVerificationError("invalid-build-provenance")
    expected_build_dependencies = {
        **EXPECTED_COMMON_BUILD_DEPENDENCIES,
        **EXPECTED_PLATFORM_BUILD_DEPENDENCIES[str(operating_system)],
    }
    build_names: set[str] = set()
    for record in inventory["buildDependencies"]:
        if (
            not isinstance(record, dict)
            or set(record) != {"license", "name", "version"}
            or not all(isinstance(record[field], str) and record[field] for field in record)
            or record["name"] in build_names
            or expected_build_dependencies.get(record["name"]) != (
                record["version"], record["license"],
            )
        ):
            raise ArtifactVerificationError("invalid-build-dependency-record")
        build_names.add(record["name"])
    if build_names != set(expected_build_dependencies):
        raise ArtifactVerificationError("build-dependency-allowlist-mismatch")
    sbom = load_json(directory / "haven42.cdx.json")
    expected_tools = [
        {"name": record["name"], "type": "application", "version": record["version"]}
        for record in inventory["buildDependencies"]
    ]
    if (
        set(sbom) != {"bomFormat", "specVersion", "version", "metadata", "components"}
        or
        sbom.get("bomFormat") != "CycloneDX"
        or sbom.get("specVersion") != "1.5"
        or sbom.get("version") != 1
        or sbom.get("metadata", {}).get("component", {}).get("name") != "Haven 42"
        or sbom.get("metadata", {}).get("component") != {
            "type": "application", "name": "Haven 42", "version": "0.3.0",
        }
        or sbom.get("metadata", {}).get("tools", {}).get("components") != expected_tools
        or sbom.get("metadata", {}).get("properties") != [
            {"name": "haven42:artifact-kind", "value": "unsigned-development"},
            {"name": "haven42:target", "value": target},
        ]
        or sbom.get("components") != [{
            "name": "CPython",
            "scope": "required",
            "type": "framework",
            "version": inventory["runtimeComponents"][0]["version"],
        }]
    ):
        raise ArtifactVerificationError("invalid-sbom")
    try:
        notices = (directory / "THIRD-PARTY-NOTICES.txt").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ArtifactVerificationError("invalid-third-party-notices") from error
    for record in inventory["buildDependencies"]:
        if f"{record['name']} {record['version']} — {record['license']}" not in notices:
            raise ArtifactVerificationError("third-party-notice-coverage-mismatch")


def verify(directory: Path) -> None:
    if not directory.is_dir():
        raise ArtifactVerificationError("artifact-directory-not-found")
    if any(path.is_symlink() for path in directory.iterdir()):
        raise ArtifactVerificationError("artifact-symlink-rejected")
    archives = [
        path for path in directory.iterdir()
        if path.is_file() and (path.name.endswith(".zip") or path.name.endswith(".tar.gz"))
    ]
    if len(archives) != 1:
        raise ArtifactVerificationError("exactly-one-package-archive-required")
    present = {path.name for path in directory.iterdir() if path.is_file()}
    expected_artifacts = REQUIRED_EVIDENCE | {"SHA256SUMS", archives[0].name}
    if present != expected_artifacts:
        raise ArtifactVerificationError("required-evidence-missing")
    verify_checksums(directory)
    verify_evidence(directory)
    provenance = load_json(directory / "build-provenance.json")
    target = (
        f"{provenance['environment']['operatingSystem']}-"
        f"{provenance['environment']['architecture']}"
    )
    if archives[0].name != (
        f"haven42-{target}-unsigned-development.zip"
        if target.startswith("windows-")
        else f"haven42-{target}-unsigned-development.tar.gz"
    ):
        raise ArtifactVerificationError("archive-target-name-mismatch")
    actual = read_archive_files(archives[0])
    expected = expected_package_files(directory / "package-file-inventory.json")
    if actual != expected:
        raise ArtifactVerificationError("archive-inventory-mismatch")


def run_self_tests() -> None:
    accepted = safe_member_name("haven42/_internal/web/static/app.js")
    assert accepted == "haven42/_internal/web/static/app.js"
    denied = 0
    for value in (
        "../escape",
        "/haven42/file",
        "other/file",
        "haven42/../escape",
        "haven42\\file",
        "haven42/\x00file",
    ):
        try:
            safe_member_name(value)
        except ArtifactVerificationError:
            denied += 1
    if denied != 6:
        raise AssertionError("hostile member-name self-test failed")
    hostile_cases = 0
    with tempfile.TemporaryDirectory(prefix="haven42-artifact-verifier-") as temporary:
        root = Path(temporary)
        traversal = root / "traversal.zip"
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("haven42/../escape", b"unsafe")
        duplicate = root / "duplicate.zip"
        with zipfile.ZipFile(duplicate, "w") as archive:
            archive.writestr("haven42/File.txt", b"one")
            archive.writestr("haven42/file.txt", b"two")
        linked = root / "linked.tar.gz"
        with tarfile.open(linked, "w:gz") as archive:
            directory = tarfile.TarInfo("haven42")
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)
            link = tarfile.TarInfo("haven42/link")
            link.type = tarfile.SYMTYPE
            link.linkname = "../../escape"
            archive.addfile(link)
        for path, expected in (
            (traversal, "unsafe-archive-member"),
            (duplicate, "duplicate-archive-member"),
            (linked, "non-regular-archive-member"),
        ):
            try:
                read_archive_files(path)
            except ArtifactVerificationError as error:
                if str(error) != expected:
                    raise AssertionError(f"expected {expected}, received {error}") from error
                hostile_cases += 1
            else:
                raise AssertionError(f"expected {expected}")
        checksum_root = root / "checksums"
        checksum_root.mkdir()
        payload = checksum_root / "payload.bin"
        payload.write_bytes(b"expected")
        (checksum_root / "SHA256SUMS").write_text(
            f"{'0' * 64}  payload.bin\n",
            encoding="utf-8",
        )
        try:
            verify_checksums(checksum_root)
        except ArtifactVerificationError as error:
            if str(error) != "checksum-mismatch":
                raise AssertionError(f"expected checksum-mismatch, received {error}") from error
            hostile_cases += 1
        else:
            raise AssertionError("expected checksum-mismatch")
    if hostile_cases != 4:
        raise AssertionError("hostile archive self-test failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-directory", required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            run_self_tests()
        verify(Path(args.artifact_directory).resolve())
    except ArtifactVerificationError as error:
        print(f"Portable artifact verification failed: {error}")
        return 2
    print("Portable artifact archive, evidence, and checksum verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
