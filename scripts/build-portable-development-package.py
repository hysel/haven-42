#!/usr/bin/env python3
"""Build an unsigned, one-folder Haven 42 development package and evidence."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import zipfile

from portable_runtime_components import classify
from alpha_release import ALPHA_1_VERSION, ALPHA_2_VERSION


ROOT = Path(__file__).resolve().parent.parent
APP_VERSION = ALPHA_2_VERSION if platform.system() == "Linux" else ALPHA_1_VERSION
REQUIRED_PYTHON_VERSION = "3.14.6"
REQUIRED_PYINSTALLER_VERSION = "6.21.0"
LOCAL_BUILD_ENVIRONMENT = ".venv-build"
RESOURCE_PATHS = (
    "web/static/index.html",
    "web/static/accessibility.html",
    "web/static/app.js",
    "web/static/styles.css",
    "config/text-capability-model-recommendations.json",
    "config/evidence-catalog.tsv",
    "config/agent-surface-capabilities.json",
    "config/agent-surface-solutions.json",
    "config/install-component-registry.json",
    "config/workflows.json",
    "config/windows-alpha-contract.json",
    "config/windows-alpha-2-contract.json",
    "config/windows-alpha-model-catalog.json",
    "config/windows-alpha-component-registry.json",
    "config/windows-alpha-resource-monitor-contract.json",
    "config/windows-alpha-quantization-contract.json",
    "config/linux-alpha-contract.json",
    "config/linux-alpha-component-registry.json",
    "config/alpha-2-model-catalog.json",
    "config/alpha-2-model-selection-evidence.json",
    "config/alpha-2-model-selection-policy.json",
    "config/alpha-2-model-version-inventory.json",
    "config/alpha-2-model-runtime-requirements.json",
    "config/alpha-2-runtime-compatibility.json",
    "config/linux-runtime-artifact-review.json",
    "config/linux-model-artifact-review.json",
    "config/web-research-query-adapter.json",
    "config/web-research-native-query-transport.json",
    "config/web-research-native-page-transport.json",
    "config/web-research-page-foundation.json",
    "scripts/validate-web-research-query-adapter.py",
)
ALLOWED_PACKAGE_ENTRIES = {
    "haven42",
    "haven42.exe",
    "_internal",
    "DEVELOPMENT-BUILD.txt",
    "LICENSE.txt",
    "THIRD-PARTY-NOTICES.txt",
    "licenses",
}
COMMON_BUILD_DISTRIBUTIONS = {
    "altgraph": ("0.17.5", "MIT"),
    "packaging": ("26.2", "Apache-2.0 OR BSD-2-Clause"),
    "pyinstaller": ("6.21.0", "GPL-2.0-or-later WITH Bootloader-exception"),
    "pyinstaller-hooks-contrib": ("2026.6", "GPL-2.0-or-later WITH Bootloader-exception"),
    "setuptools": ("83.0.0", "MIT"),
}
PLATFORM_BUILD_DISTRIBUTIONS = {
    "Windows": {
        "pefile": ("2024.8.26", "MIT"),
        "pywin32-ctypes": ("0.2.3", "BSD-3-Clause"),
    },
    "Darwin": {"macholib": ("1.16.3", "MIT")},
    "Linux": {},
}
LICENSE_EVIDENCE = {
    "APACHE-2.0.txt": "69849221bfb90053de2134ef5e6d540287b4b98062326492f1f96f5da685524b",
    "CPYTHON-3.14.6-LICENSE.txt": "214919267ac05a769eed6c9e442432ab7cacf108774e4597b2d676c5dd12d020",
    "LIBFFI-3.4.4-LICENSE.txt": "2c9c2acb9743e6b007b91350475308aee44691d96aa20eacef8e199988c8c388",
    "OLLAMA-MIT-LICENSE.txt": "5934ed2ce0d15154bcdb9c85203210abac0da4314af34081e36df4599f90b226",
}
PYTHON_DISTRIBUTIONS = {
    "windows-amd64": {
        "asset": "python-3.14.6-win32-x64.zip",
        "sha256": "dc722964ab28f81f6a0c753ee960871f045d363568f4fb7626cc02c1e0caa1e9",
    },
    "linux-x86_64": {
        "asset": "python-3.14.6-linux-24.04-x64.tar.gz",
        "sha256": "29dc7f3887a430fe7a0005fee4732b00be1bbed5bf21aa1e43f8d947eb1b9f61",
    },
    "darwin-arm64": {
        "asset": "python-3.14.6-darwin-arm64.tar.gz",
        "sha256": "7ed5b5c399a38b9b5b1bbb70a454c2ac8b0548cd0610871ea443c4747468e97c",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def isolated_python_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONSAFEPATH"] = "1"
    return environment


def isolated_pyinstaller_version(executable: Path) -> str | None:
    probe = subprocess.run(
        [
            str(executable),
            "-I",
            "-c",
            "import importlib.metadata as m,platform; "
            "print(platform.python_version()); print(m.version('pyinstaller'))",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=isolated_python_environment(),
    )
    if probe.returncode != 0:
        return None
    versions = probe.stdout.splitlines()
    if len(versions) != 2 or versions[0].strip() != REQUIRED_PYTHON_VERSION:
        return None
    version = versions[1].strip()
    return version or None


def installed_pyinstaller_version() -> str | None:
    return isolated_pyinstaller_version(Path(sys.executable).resolve())


def repository_build_python(root: Path = ROOT) -> Path | None:
    environment = root / LOCAL_BUILD_ENVIRONMENT
    executable = environment / (
        "Scripts/python.exe" if platform.system() == "Windows" else "bin/python"
    )
    for path in (environment, executable.parent, executable):
        if path.is_symlink():
            remediation = (
                " On macOS, recreate it with Python 3.14.6 using "
                "'python3.14 -m venv --copies .venv-build'."
                if platform.system() == "Darwin"
                else ""
            )
            raise SystemExit(
                "The repository-local portable build environment is unsafe because "
                "it contains a symbolic link. Recreate .venv-build before building."
                + remediation
            )
    if not executable.is_file():
        return None
    resolved_root = root.resolve()
    resolved_environment = environment.resolve()
    resolved_executable = executable.resolve()
    try:
        resolved_environment.relative_to(resolved_root)
        resolved_executable.relative_to(resolved_environment)
    except ValueError as error:
        raise SystemExit(
            "The repository-local portable build Python escapes .venv-build."
        ) from error
    return resolved_executable


def delegate_to_repository_build_environment() -> int | None:
    current = installed_pyinstaller_version()
    if current == REQUIRED_PYINSTALLER_VERSION:
        return None
    executable = repository_build_python()
    if executable is None:
        found = current or "not installed"
        raise SystemExit(
            f"Portable packaging requires PyInstaller "
            f"{REQUIRED_PYINSTALLER_VERSION} on Python {REQUIRED_PYTHON_VERSION}; "
            f"the current isolated Python has {found}, and .venv-build is missing. "
            f"Create .venv-build with Python {REQUIRED_PYTHON_VERSION} and "
            "install package/requirements-build.txt with --require-hashes."
        )
    local_version = isolated_pyinstaller_version(executable)
    if local_version != REQUIRED_PYINSTALLER_VERSION:
        raise SystemExit(
            f"The repository-local build environment must contain exact "
            f"Python {REQUIRED_PYTHON_VERSION} and PyInstaller "
            f"{REQUIRED_PYINSTALLER_VERSION}. Recreate .venv-build "
            "from package/requirements-build.txt with --require-hashes."
        )
    print(
        f"Using repository-local .venv-build with Python "
        f"{REQUIRED_PYTHON_VERSION} and PyInstaller {REQUIRED_PYINSTALLER_VERSION}."
    )
    script = Path(__file__).resolve()
    bootstrap = (
        "import runpy,sys;"
        f"sys.path.insert(0,{str(script.parent)!r});"
        f"sys.argv=[{str(script)!r},*sys.argv[1:]];"
        f"runpy.run_path({str(script)!r},run_name='__main__')"
    )
    completed = subprocess.run(
        [str(executable), "-I", "-c", bootstrap, *sys.argv[1:]],
        cwd=ROOT,
        check=False,
        env=isolated_python_environment(),
    )
    return completed.returncode


def resolve_build_output(value: str) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        requested = ROOT / requested
    output = requested.resolve()
    allowed = (ROOT / "dist").resolve()
    try:
        relative = output.relative_to(allowed)
    except ValueError as error:
        raise SystemExit("Portable build output must stay beneath repository dist.") from error
    if not relative.parts or output.is_symlink() or (output.exists() and not output.is_dir()):
        raise SystemExit("Portable build output is unsafe.")
    return output


def windows_system_root() -> Path:
    buffer = ctypes.create_unicode_buffer(32_768)
    length = ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer))
    if length <= 0 or length >= len(buffer):
        raise SystemExit("Could not resolve the trusted Windows directory.")
    return Path(buffer.value).resolve()


def pyinstaller_environment(config_dir: Path, app_version: str = APP_VERSION) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONSAFEPATH"] = "1"
    environment["PYINSTALLER_CONFIG_DIR"] = str(config_dir.resolve())
    if app_version not in {ALPHA_1_VERSION, ALPHA_2_VERSION}:
        raise SystemExit("Invalid portable build release identity.")
    environment["HAVEN42_BUILD_VERSION"] = app_version
    if platform.system() == "Windows":
        system_root = windows_system_root()
        admitted = (
            Path(sys.executable).resolve().parent,
            Path(sys.base_prefix).resolve(),
            system_root / "System32",
            system_root,
        )
        environment["PATH"] = os.pathsep.join(
            str(path)
            for index, path in enumerate(admitted)
            if path.is_dir() and path not in admitted[:index]
        )
    return environment


def resolve_app_version(release_line: str, system: str) -> str:
    if release_line == "alpha2":
        if system not in {"Windows", "Linux", "Darwin"}:
            raise SystemExit(
                "--release-line alpha2 requires Windows, Linux, or macOS."
            )
        return ALPHA_2_VERSION
    if release_line != "platform-default":
        raise SystemExit("Invalid portable build release line.")
    return ALPHA_2_VERSION if system == "Linux" else ALPHA_1_VERSION


def expected_resource_manifest(root: Path = ROOT) -> dict[str, object]:
    resources = []
    for relative in RESOURCE_PATHS:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise SystemExit(f"Protected package resource is missing or unsafe: {relative}")
        content = path.read_bytes()
        if b"\r" in content:
            raise SystemExit(
                f"Protected package resource must use repository-enforced LF "
                f"bytes: {relative}"
            )
        resources.append({
            "path": relative,
            "sha256": hashlib.sha256(content).hexdigest(),
            "sizeBytes": len(content),
        })
    return {
        "schemaVersion": 1,
        "algorithm": "sha256",
        "resources": resources,
    }


def update_resource_manifest(root: Path = ROOT) -> None:
    write_json(
        root / "package/resource-integrity.json",
        expected_resource_manifest(root),
    )


def verify_resource_manifest(root: Path = ROOT) -> None:
    manifest_path = root / "package/resource-integrity.json"
    try:
        committed = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit(
            f"Committed resource integrity manifest is unreadable: {error}"
        ) from error
    if committed != expected_resource_manifest(root):
        raise SystemExit(
            "Committed resource integrity manifest does not match the protected "
            "package resources. Review the resource changes, then run "
            "'python scripts/build-portable-development-package.py "
            "--update-resource-integrity' explicitly."
        )


def copy_license_evidence(evidence: Path) -> None:
    for name, expected_digest in sorted(LICENSE_EVIDENCE.items()):
        source = ROOT / "package" / "licenses" / name
        if not source.is_file() or sha256(source) != expected_digest:
            raise SystemExit(f"License evidence mismatch: {name}")
        shutil.copy2(source, evidence / name)


def copy_package_license_evidence(package_dir: Path) -> None:
    project_license = ROOT / "LICENSE"
    expected_project_digest = (
        "da343e362fb1cc2b46c07e179936040dcfe8e92de4aa6d61f2bd4a43486f3ccc"
    )
    if (
        not project_license.is_file()
        or project_license.is_symlink()
        or sha256(project_license) != expected_project_digest
    ):
        raise SystemExit("Haven 42 license evidence mismatch.")
    project_destination = package_dir / "LICENSE.txt"
    reject_unsafe_write_destination(project_destination)
    shutil.copy2(project_license, project_destination)
    license_dir = package_dir / "licenses"
    if license_dir.exists():
        if not license_dir.is_dir() or license_dir.is_symlink():
            raise SystemExit("Package license directory is unsafe.")
    else:
        license_dir.mkdir()
    for name, expected_digest in sorted(LICENSE_EVIDENCE.items()):
        source = ROOT / "package" / "licenses" / name
        if (
            not source.is_file()
            or source.is_symlink()
            or sha256(source) != expected_digest
        ):
            raise SystemExit(f"License evidence mismatch: {name}")
        destination = license_dir / name
        reject_unsafe_write_destination(destination)
        shutil.copy2(source, destination)


def reject_unsafe_write_destination(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise SystemExit(f"Package evidence destination is unsafe: {path.name}")


def write_package_text(path: Path, content: str) -> None:
    reject_unsafe_write_destination(path)
    path.write_text(content, encoding="utf-8")


def third_party_notice(
    dependencies: list[dict[str, str]],
    runtime_inventory: dict[str, object],
) -> str:
    notices = [
        "THIRD-PARTY NOTICES — unsigned development package",
        "",
        "Build-tool versions and license expressions are an explicit reviewed allowlist.",
        "These tools influence the generated package but are not imported application dependencies.",
        "",
    ]
    notices.extend(
        f"{item['name']} {item['version']} — {item['license']}"
        for item in dependencies
    )
    notices.extend([
        "",
        "Embedded runtime component inventory",
        "RUNTIME REDISTRIBUTION IS NOT CLEARED FOR PRODUCTION PROMOTION.",
        "Every runtime component below is excluded from Haven 42 signing scope.",
        "CPYTHON-3.14.6-LICENSE.txt, APACHE-2.0.txt, "
        "LIBFFI-3.4.4-LICENSE.txt, and OLLAMA-MIT-LICENSE.txt are included "
        "in the extracted package and "
        "artifact evidence as hash-verified license evidence.",
        "",
    ])
    notices.extend(
        f"{item['name']} {item['version']} — {item['license']} — "
        f"{item['reviewStatus']} — {item['fileCount']} files"
        for item in runtime_inventory["runtimeComponents"]
    )
    return "\n".join(notices) + "\n"


def dependency_records() -> list[dict[str, str]]:
    expected = {
        **COMMON_BUILD_DISTRIBUTIONS,
        **PLATFORM_BUILD_DISTRIBUTIONS.get(platform.system(), {}),
    }
    records = []
    for name, (version, reviewed_license) in sorted(expected.items()):
        try:
            distribution = importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise SystemExit(f"Required build distribution is missing: {name}") from error
        if distribution.version != version:
            raise SystemExit(
                f"Build distribution version mismatch for {name}: "
                f"expected {version}, received {distribution.version}"
            )
        records.append({
            "name": name,
            "version": version,
            "license": reviewed_license,
        })
    return sorted(records, key=lambda item: item["name"].lower())


def validate_windows_executable_metadata(package_dir: Path) -> None:
    if platform.system() != "Windows":
        return
    try:
        import pefile
    except ImportError as error:
        raise SystemExit("pefile is required to verify Windows executable metadata.") from error
    executable = package_dir / "haven42.exe"
    try:
        pe = pefile.PE(str(executable), fast_load=True)
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
        )
        metadata: dict[str, str] = {}
        for file_info in getattr(pe, "FileInfo", []):
            for entry in file_info:
                if getattr(entry, "Key", b"") != b"StringFileInfo":
                    continue
                for table in entry.StringTable:
                    metadata.update({
                        key.decode("utf-8"): value.decode("utf-8")
                        for key, value in table.entries.items()
                    })
    except (OSError, pefile.PEFormatError, UnicodeDecodeError) as error:
        raise SystemExit("Could not verify Windows executable metadata.") from error
    finally:
        if "pe" in locals():
            pe.close()
    expected = {
        "FileDescription": "Haven 42",
        "FileVersion": APP_VERSION,
        "OriginalFilename": "haven42.exe",
        "ProductName": "Haven 42",
        "ProductVersion": APP_VERSION,
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise SystemExit(
            "Windows executable metadata mismatch: "
            + ", ".join(
                f"{key}={metadata.get(key)!r} (expected {value!r})"
                for key, value in expected.items()
                if metadata.get(key) != value
            )
        )


def commit_identity() -> str:
    value = os.environ.get("HAVEN42_SOURCE_COMMIT", "")
    if re.fullmatch(r"[0-9a-f]{40}", value):
        return value
    value = os.environ.get("GITHUB_SHA", "")
    if re.fullmatch(r"[0-9a-f]{40}", value):
        return value
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise SystemExit(
            "Could not resolve an exact build commit. Source exports must set "
            "HAVEN42_SOURCE_COMMIT and HAVEN42_SOURCE_TREE_STATE."
        ) from error
    value = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise SystemExit("Could not resolve an exact build commit.")
    return value


def source_provenance() -> dict[str, object]:
    commit = commit_identity()
    state = os.environ.get("HAVEN42_SOURCE_TREE_STATE", "")
    snapshot = os.environ.get("HAVEN42_SOURCE_SNAPSHOT_SHA256", "")
    if state:
        if state not in {"exact-commit", "modified-uncommitted"}:
            raise SystemExit("Invalid HAVEN42_SOURCE_TREE_STATE.")
        if state == "modified-uncommitted" and not re.fullmatch(r"[0-9a-f]{64}", snapshot):
            raise SystemExit(
                "Modified source exports require HAVEN42_SOURCE_SNAPSHOT_SHA256."
            )
        if snapshot and not re.fullmatch(r"[0-9a-f]{64}", snapshot):
            raise SystemExit("Invalid HAVEN42_SOURCE_SNAPSHOT_SHA256.")
    else:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=normal"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as error:
            raise SystemExit(
                "Could not determine source tree state. Source exports must set "
                "HAVEN42_SOURCE_TREE_STATE and, when modified, "
                "HAVEN42_SOURCE_SNAPSHOT_SHA256."
            ) from error
        state = "modified-uncommitted" if result.stdout.strip() else "exact-commit"
    return {
        "repository": "https://github.com/hysel/haven-42",
        "commit": commit,
        "treeState": state,
        "commitIsExactSource": state == "exact-commit",
        "snapshotSha256": snapshot,
    }


def package_file_records(package_dir: Path) -> list[dict[str, object]]:
    package_root = package_dir.resolve()
    for path in package_dir.rglob("*"):
        if path.is_symlink():
            try:
                path.resolve(strict=True).relative_to(package_root)
            except (OSError, ValueError) as error:
                raise SystemExit("Package link escapes the bundle.") from error
    return [
        {
            "path": path.relative_to(package_dir).as_posix(),
            "sha256": sha256(path),
            "sizeBytes": path.stat().st_size,
        }
        for path in sorted(package_dir.rglob("*"))
        if path.is_file()
    ]


def openssl_runtime_version() -> str:
    match = re.match(r"^OpenSSL\s+([0-9]+\.[0-9]+\.[0-9]+)", ssl.OPENSSL_VERSION)
    return match.group(1) if match else "unresolved"


def python_distribution_provenance(target: str) -> dict[str, str]:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return {
            "repository": "local-build-environment",
            "releaseTag": "",
            "releaseCommit": "",
            "asset": "",
            "sha256": "",
            "verification": "local-unverified",
        }
    expected = PYTHON_DISTRIBUTIONS.get(target)
    if expected is None:
        raise SystemExit(f"No admitted Python distribution for target: {target}")
    asset = os.environ.get("HAVEN42_PYTHON_SOURCE_ASSET", "")
    digest = os.environ.get("HAVEN42_PYTHON_SOURCE_SHA256", "")
    if asset != expected["asset"] or digest != expected["sha256"]:
        raise SystemExit("GitHub Python distribution identity mismatch.")
    return {
        "repository": "actions/python-versions",
        "releaseTag": "3.14.6-27283001424",
        "releaseCommit": "25a990ef82051ebb9cba2b6ed6b79e61148a5bfb",
        "asset": asset,
        "sha256": digest,
        "verification": "pinned-setup-python-release-metadata",
    }


def create_archive(package_dir: Path, artifact_dir: Path, target: str) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        archive = artifact_dir / f"haven42-{target}-unsigned-development.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
            for path in sorted(package_dir.rglob("*")):
                if path.is_file():
                    output.write(path, Path("haven42") / path.relative_to(package_dir))
        return archive
    archive = artifact_dir / f"haven42-{target}-unsigned-development.tar.gz"
    # PyInstaller uses platform-native symlinks on macOS. Portable archives
    # materialize their targets so extraction never creates archive-owned links.
    with tarfile.open(archive, "w:gz", dereference=True) as output:
        output.add(package_dir, arcname="haven42", recursive=True)
    return archive


def main() -> int:
    global APP_VERSION
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "dist" / "portable"))
    parser.add_argument("--skip-pyinstaller", action="store_true")
    parser.add_argument(
        "--release-line",
        choices=("platform-default", "alpha2"),
        default="platform-default",
        help=(
            "Use the existing platform default, or explicitly build Alpha 2. "
            "The explicit Alpha 2 option is supported on Windows, Linux, and macOS."
        ),
    )
    parser.add_argument(
        "--update-resource-integrity",
        action="store_true",
        help="Update only the tracked protected-resource manifest for review.",
    )
    args = parser.parse_args()
    try:
        APP_VERSION = resolve_app_version(args.release_line, platform.system())
    except SystemExit as error:
        parser.error(str(error))
    if args.update_resource_integrity:
        if args.skip_pyinstaller:
            parser.error(
                "--update-resource-integrity cannot be combined with "
                "--skip-pyinstaller."
            )
        update_resource_manifest()
        print(ROOT / "package/resource-integrity.json")
        return 0
    delegated = delegate_to_repository_build_environment()
    if delegated is not None:
        return delegated
    output = resolve_build_output(args.output)
    work = output / "work"
    artifact_dir = output / "artifacts"
    bundle_dir = output / "bundle"
    if bundle_dir.is_symlink():
        raise SystemExit("PyInstaller bundle directory is unsafe.")
    target = f"{platform.system().lower()}-{platform.machine().lower()}"
    verify_resource_manifest()
    if not args.skip_pyinstaller:
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean",
            "--distpath", str(bundle_dir),
            "--workpath", str(work),
            str(ROOT / "package/haven42.spec"),
        ], cwd=ROOT, check=True, env=pyinstaller_environment(work / "config", APP_VERSION))
    package_dir = bundle_dir / "haven42"
    if not package_dir.is_dir() or package_dir.is_symlink():
        raise SystemExit("PyInstaller one-folder output was not found.")
    validate_windows_executable_metadata(package_dir)
    unexpected = {path.name for path in package_dir.iterdir()} - ALLOWED_PACKAGE_ENTRIES
    if unexpected:
        raise SystemExit(f"Unexpected top-level package entries: {sorted(unexpected)}")
    write_package_text(
        package_dir / "DEVELOPMENT-BUILD.txt",
        "Haven 42 unsigned development build.\n"
        "No installer, signing, notarization, updater activation, or production-readiness claim.\n",
    )
    dependencies = dependency_records()
    copy_package_license_evidence(package_dir)
    evidence = output / "evidence"
    archive_staging = tempfile.TemporaryDirectory(
        prefix="haven42-archive-staging-",
        dir=output,
    )
    staged_package_dir = Path(archive_staging.name) / "haven42"
    shutil.copytree(package_dir, staged_package_dir, symlinks=False)
    preliminary_inventory = classify(
        package_file_records(staged_package_dir),
        target,
        platform.python_version(),
        openssl_runtime_version(),
    )
    notices = third_party_notice(dependencies, preliminary_inventory)
    write_package_text(package_dir / "THIRD-PARTY-NOTICES.txt", notices)
    write_package_text(staged_package_dir / "THIRD-PARTY-NOTICES.txt", notices)
    package_files = package_file_records(staged_package_dir)
    runtime_inventory = classify(
        package_files,
        target,
        platform.python_version(),
        openssl_runtime_version(),
    )
    write_json(evidence / "package-file-inventory.json", {
        "schemaVersion": 1,
        "algorithm": "sha256",
        "packageRoot": "haven42",
        "files": package_files,
    })
    write_json(evidence / "runtime-component-inventory.json", runtime_inventory)
    write_json(evidence / "dependency-inventory.json", {
        "schemaVersion": 3,
        "target": target,
        "runtimeComponents": [
            {
                key: item[key]
                for key in (
                    "id", "name", "version", "license", "reviewStatus",
                    "sourceProvenance", "fileCount",
                )
            }
            for item in runtime_inventory["runtimeComponents"]
        ],
        "buildDependencies": dependencies,
    })
    write_json(evidence / "build-provenance.json", {
        "schemaVersion": 1,
        "artifactKind": "unsigned-development",
        "application": {"name": "Haven 42", "version": APP_VERSION},
        "source": source_provenance(),
        "builder": {
            "kind": "github-actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "local",
            "workflow": os.environ.get("GITHUB_WORKFLOW", "local"),
            "runId": os.environ.get("GITHUB_RUN_ID", "local"),
        },
        "environment": {
            "operatingSystem": platform.system().lower(),
            "architecture": platform.machine().lower(),
            "pythonImplementation": platform.python_implementation(),
            "pythonVersion": platform.python_version(),
            "pythonDistribution": python_distribution_provenance(target),
            "pyinstallerVersion": importlib.metadata.version("pyinstaller"),
        },
        "security": {
            "dependencyHashesRequired": True,
            "resourceIntegrityManifestEmbedded": True,
            "signed": False,
            "notarized": False,
            "attested": False,
            "releasePublished": False,
        },
    })
    write_json(evidence / "haven42.cdx.json", {
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
            "tools": {
                "components": [
                    {"type": "application", "name": item["name"], "version": item["version"]}
                    for item in dependencies
                ]
            },
            "properties": [
                {"name": "haven42:artifact-kind", "value": "unsigned-development"},
                {"name": "haven42:target", "value": target},
            ],
        },
        "components": [
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
        ],
    })
    (evidence / "THIRD-PARTY-NOTICES.txt").write_text(notices, encoding="utf-8")
    copy_license_evidence(evidence)
    archive = create_archive(staged_package_dir, artifact_dir, target)
    archive_staging.cleanup()
    for path in sorted(evidence.iterdir()):
        shutil.copy2(path, artifact_dir)
    checksum_targets = [
        archive,
        *sorted(
            path
            for path in artifact_dir.iterdir()
            if path.name not in {"SHA256SUMS", archive.name}
        ),
    ]
    (artifact_dir / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_targets),
        encoding="utf-8",
    )
    print(artifact_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
