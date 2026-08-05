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

from portable_runtime_components import ComponentClassificationError, classify


SHA256 = re.compile(r"^[0-9a-f]{64}$")
APP_VERSION = "0.4.0-alpha.1"
REQUIRED_EVIDENCE = {
    "APACHE-2.0.txt",
    "CPYTHON-3.14.6-LICENSE.txt",
    "LIBFFI-3.4.4-LICENSE.txt",
    "THIRD-PARTY-NOTICES.txt",
    "build-provenance.json",
    "dependency-inventory.json",
    "haven42.cdx.json",
    "package-file-inventory.json",
    "runtime-component-inventory.json",
}
EXPECTED_LICENSE_EVIDENCE = {
    "APACHE-2.0.txt": "69849221bfb90053de2134ef5e6d540287b4b98062326492f1f96f5da685524b",
    "CPYTHON-3.14.6-LICENSE.txt": "214919267ac05a769eed6c9e442432ab7cacf108774e4597b2d676c5dd12d020",
    "LIBFFI-3.4.4-LICENSE.txt": "2c9c2acb9743e6b007b91350475308aee44691d96aa20eacef8e199988c8c388",
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
EXPECTED_PYTHON_DISTRIBUTIONS = {
    "windows-amd64": {
        "repository": "actions/python-versions",
        "releaseTag": "3.14.6-27283001424",
        "releaseCommit": "25a990ef82051ebb9cba2b6ed6b79e61148a5bfb",
        "asset": "python-3.14.6-win32-x64.zip",
        "sha256": "dc722964ab28f81f6a0c753ee960871f045d363568f4fb7626cc02c1e0caa1e9",
        "verification": "pinned-setup-python-release-metadata",
    },
    "linux-x86_64": {
        "repository": "actions/python-versions",
        "releaseTag": "3.14.6-27283001424",
        "releaseCommit": "25a990ef82051ebb9cba2b6ed6b79e61148a5bfb",
        "asset": "python-3.14.6-linux-24.04-x64.tar.gz",
        "sha256": "29dc7f3887a430fe7a0005fee4732b00be1bbed5bf21aa1e43f8d947eb1b9f61",
        "verification": "pinned-setup-python-release-metadata",
    },
    "darwin-arm64": {
        "repository": "actions/python-versions",
        "releaseTag": "3.14.6-27283001424",
        "releaseCommit": "25a990ef82051ebb9cba2b6ed6b79e61148a5bfb",
        "asset": "python-3.14.6-darwin-arm64.tar.gz",
        "sha256": "7ed5b5c399a38b9b5b1bbb70a454c2ac8b0548cd0610871ea443c4747468e97c",
        "verification": "pinned-setup-python-release-metadata",
    },
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


def verify_sbom_document(
    sbom: dict, inventory: dict, runtime_inventory: dict, target: str
) -> None:
    expected_tools = [
        {"name": record["name"], "type": "application", "version": record["version"]}
        for record in inventory["buildDependencies"]
    ]
    if (
        set(sbom) != {"bomFormat", "specVersion", "version", "metadata", "components"}
        or sbom.get("bomFormat") != "CycloneDX"
        or sbom.get("specVersion") != "1.5"
        or sbom.get("version") != 1
        or sbom.get("metadata", {}).get("component") != {
            "type": "application",
            "name": "Haven 42",
            "version": APP_VERSION,
            "licenses": [{"expression": "MIT"}],
        }
        or sbom.get("metadata", {}).get("tools", {}).get("components") != expected_tools
        or sbom.get("metadata", {}).get("properties") != [
            {"name": "haven42:artifact-kind", "value": "unsigned-development"},
            {"name": "haven42:target", "value": target},
        ]
        or sbom.get("components") != [
            {
                "type": "framework" if item["id"] == "cpython" else "library",
                "name": item["name"],
                "version": item["version"],
                "scope": "required",
                "licenses": [{"expression": item["license"]}],
                "properties": [
                    {"name": "haven42:component-id", "value": item["id"]},
                    {"name": "haven42:review-status", "value": item["reviewStatus"]},
                    {"name": "haven42:file-count", "value": str(item["fileCount"])},
                    {"name": "haven42:signing-eligible", "value": "false"},
                ],
            }
            for item in runtime_inventory["runtimeComponents"]
        ]
    ):
        raise ArtifactVerificationError("invalid-sbom")


def verify_notice_text(notices: str, inventory: dict, runtime_inventory: dict) -> None:
    for record in inventory["buildDependencies"]:
        if f"{record['name']} {record['version']} — {record['license']}" not in notices:
            raise ArtifactVerificationError("third-party-notice-coverage-mismatch")
    if "RUNTIME REDISTRIBUTION IS NOT CLEARED FOR PRODUCTION PROMOTION." not in notices:
        raise ArtifactVerificationError("runtime-clearance-warning-missing")
    if (
        "CPYTHON-3.14.6-LICENSE.txt, APACHE-2.0.txt, and "
        "LIBFFI-3.4.4-LICENSE.txt are included as hash-verified license evidence."
        not in notices
    ):
        raise ArtifactVerificationError("license-evidence-notice-missing")
    for record in runtime_inventory["runtimeComponents"]:
        marker = (
            f"{record['name']} {record['version']} — {record['license']} — "
            f"{record['reviewStatus']} — {record['fileCount']} files"
        )
        if marker not in notices:
            raise ArtifactVerificationError("runtime-notice-coverage-mismatch")


def verify_evidence(directory: Path) -> None:
    for name, expected_digest in EXPECTED_LICENSE_EVIDENCE.items():
        path = directory / name
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected_digest:
            raise ArtifactVerificationError("license-evidence-mismatch")
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
        inventory.get("schemaVersion") != 3
        or set(inventory) != {
            "schemaVersion", "target", "runtimeComponents", "buildDependencies",
        }
        or not isinstance(inventory.get("runtimeComponents"), list)
        or not isinstance(inventory.get("buildDependencies"), list)
        or operating_system not in EXPECTED_PLATFORM_BUILD_DEPENDENCIES
        or architecture not in ALLOWED_ARCHITECTURES.get(str(operating_system), set())
        or target != f"{operating_system}-{architecture}"
    ):
        raise ArtifactVerificationError("invalid-dependency-inventory")
    commit = provenance.get("source", {}).get("commit", "")
    security = provenance.get("security", {})
    python_distribution = environment.get("pythonDistribution")
    expected_python_distribution = (
        EXPECTED_PYTHON_DISTRIBUTIONS.get(str(target))
        if builder.get("kind") == "github-actions"
        else {
            "repository": "local-build-environment",
            "releaseTag": "",
            "releaseCommit": "",
            "asset": "",
            "sha256": "",
            "verification": "local-unverified",
        }
    )
    if (
        set(provenance) != {
            "schemaVersion", "artifactKind", "application", "source",
            "builder", "environment", "security",
        }
        or provenance.get("schemaVersion") != 1
        or provenance.get("artifactKind") != "unsigned-development"
        or application != {"name": "Haven 42", "version": APP_VERSION}
        or source.get("repository") != "https://github.com/hysel/haven-42"
        or set(source) != {
            "repository", "commit", "treeState", "commitIsExactSource",
            "snapshotSha256",
        }
        or set(builder) != {"kind", "workflow", "runId"}
        or builder.get("kind") not in {"github-actions", "local"}
        or not all(isinstance(builder.get(field), str) and builder[field] for field in ("workflow", "runId"))
        or set(environment) != {
            "operatingSystem", "architecture", "pythonImplementation",
            "pythonVersion", "pythonDistribution", "pyinstallerVersion",
        }
        or environment.get("pythonImplementation") != "CPython"
        or environment.get("pyinstallerVersion") != "6.21.0"
        or python_distribution != expected_python_distribution
        or not all(
            isinstance(environment.get(field), str) and environment[field]
            for field in environment
            if field != "pythonDistribution"
        )
        or not re.fullmatch(r"[0-9a-f]{40}", str(commit))
        or source.get("treeState") not in {"exact-commit", "modified-uncommitted"}
        or source.get("commitIsExactSource")
            is not (source.get("treeState") == "exact-commit")
        or not isinstance(source.get("snapshotSha256"), str)
        or (
            source.get("snapshotSha256") != ""
            and not re.fullmatch(r"[0-9a-f]{64}", source["snapshotSha256"])
        )
        or (
            builder.get("kind") == "github-actions"
            and (
                source.get("treeState") != "exact-commit"
                or source.get("snapshotSha256") != ""
            )
        )
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
    runtime_inventory = load_json(directory / "runtime-component-inventory.json")
    package_inventory = load_json(directory / "package-file-inventory.json")
    expected_package_files(directory / "package-file-inventory.json")
    runtime_records = runtime_inventory.get("runtimeComponents")
    if not isinstance(runtime_records, list):
        raise ArtifactVerificationError("invalid-runtime-component-inventory")
    openssl_records = [
        item for item in runtime_records
        if isinstance(item, dict) and item.get("id") == "openssl"
    ]
    openssl_version = (
        str(openssl_records[0].get("version"))
        if len(openssl_records) == 1
        else "unresolved"
    )
    if not re.fullmatch(r"(?:unresolved|\d+\.\d+\.\d+)", openssl_version):
        raise ArtifactVerificationError("invalid-runtime-component-version")
    try:
        expected_runtime_inventory = classify(
            package_inventory.get("files"),
            str(target),
            str(environment.get("pythonVersion")),
            openssl_version,
        )
    except (ComponentClassificationError, TypeError) as error:
        raise ArtifactVerificationError("invalid-runtime-component-inventory") from error
    if runtime_inventory != expected_runtime_inventory:
        raise ArtifactVerificationError("runtime-component-inventory-mismatch")
    expected_runtime_summaries = [
        {
            key: item[key]
            for key in (
                "id", "name", "version", "license", "reviewStatus",
                "sourceProvenance", "fileCount",
            )
        }
        for item in runtime_inventory["runtimeComponents"]
    ]
    if inventory["runtimeComponents"] != expected_runtime_summaries:
        raise ArtifactVerificationError("dependency-runtime-component-mismatch")
    sbom = load_json(directory / "haven42.cdx.json")
    verify_sbom_document(sbom, inventory, runtime_inventory, str(target))
    try:
        notices = (directory / "THIRD-PARTY-NOTICES.txt").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ArtifactVerificationError("invalid-third-party-notices") from error
    verify_notice_text(notices, inventory, runtime_inventory)


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
        license_root = root / "licenses"
        license_root.mkdir()
        for name in EXPECTED_LICENSE_EVIDENCE:
            (license_root / name).write_bytes(b"substituted license\n")
        try:
            verify_evidence(license_root)
        except ArtifactVerificationError as error:
            if str(error) != "license-evidence-mismatch":
                raise AssertionError(f"expected license-evidence-mismatch, received {error}") from error
            hostile_cases += 1
        else:
            raise AssertionError("expected license-evidence-mismatch")

        inventory = {
            "buildDependencies": [{"name": "tool", "version": "1.0", "license": "MIT"}]
        }
        runtime_inventory = {
            "runtimeComponents": [{
                "id": "cpython",
                "name": "CPython embedded runtime",
                "version": "3.14.6",
                "license": "PSF-2.0",
                "reviewStatus": "review-required",
                "fileCount": 1,
            }]
        }
        valid_sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "component": {
                    "type": "application",
                    "name": "Haven 42",
                    "version": APP_VERSION,
                    "licenses": [{"expression": "MIT"}],
                },
                "tools": {"components": [{"name": "tool", "type": "application", "version": "1.0"}]},
                "properties": [
                    {"name": "haven42:artifact-kind", "value": "unsigned-development"},
                    {"name": "haven42:target", "value": "windows-amd64"},
                ],
            },
            "components": [],
        }
        try:
            verify_sbom_document(valid_sbom, inventory, runtime_inventory, "windows-amd64")
        except ArtifactVerificationError as error:
            if str(error) != "invalid-sbom":
                raise AssertionError(f"expected invalid-sbom, received {error}") from error
            hostile_cases += 1
        else:
            raise AssertionError("expected invalid-sbom")

        incomplete_notice = (
            "tool 1.0 — MIT\n"
            "RUNTIME REDISTRIBUTION IS NOT CLEARED FOR PRODUCTION PROMOTION.\n"
        )
        try:
            verify_notice_text(incomplete_notice, inventory, runtime_inventory)
        except ArtifactVerificationError as error:
            if str(error) != "license-evidence-notice-missing":
                raise AssertionError(
                    f"expected license-evidence-notice-missing, received {error}"
                ) from error
            hostile_cases += 1
        else:
            raise AssertionError("expected license-evidence-notice-missing")
    if hostile_cases != 7:
        raise AssertionError("hostile archive self-test failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-directory")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-only", action="store_true")
    args = parser.parse_args()
    if args.self_test_only and (args.self_test or args.artifact_directory):
        parser.error("--self-test-only cannot be combined with artifact verification")
    if not args.self_test_only and not args.artifact_directory:
        parser.error("--artifact-directory is required unless --self-test-only is used")
    try:
        if args.self_test or args.self_test_only:
            run_self_tests()
        if args.self_test_only:
            print("Portable verifier hostile self-tests passed 7 cases.")
            return 0
        verify(Path(args.artifact_directory).resolve())
    except ArtifactVerificationError as error:
        print(f"Portable artifact verification failed: {error}")
        return 2
    print("Portable artifact archive, evidence, and checksum verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
