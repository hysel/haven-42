#!/usr/bin/env python3
"""Build an unsigned, one-folder Haven 42 development package and evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parent.parent
APP_VERSION = "0.3.0"
RESOURCE_PATHS = (
    "web/static/index.html",
    "web/static/app.js",
    "web/static/styles.css",
    "config/text-capability-model-recommendations.json",
    "config/evidence-catalog.tsv",
    "config/install-component-registry.json",
    "config/workflows.json",
)
ALLOWED_PACKAGE_ENTRIES = {"haven42", "haven42.exe", "_internal", "DEVELOPMENT-BUILD.txt"}
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_resource_manifest() -> None:
    resources = []
    for relative in RESOURCE_PATHS:
        path = ROOT / relative
        resources.append({
            "path": relative,
            "sha256": sha256(path),
            "sizeBytes": path.stat().st_size,
        })
    write_json(ROOT / "package/resource-integrity.json", {
        "schemaVersion": 1,
        "algorithm": "sha256",
        "resources": resources,
    })


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


def commit_identity() -> str:
    value = os.environ.get("HAVEN42_SOURCE_COMMIT", "")
    if re.fullmatch(r"[0-9a-f]{40}", value):
        return value
    value = os.environ.get("GITHUB_SHA", "")
    if re.fullmatch(r"[0-9a-f]{40}", value):
        return value
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise SystemExit("Could not resolve an exact build commit.")
    return value


def package_file_records(package_dir: Path) -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(package_dir).as_posix(),
            "sha256": sha256(path),
            "sizeBytes": path.stat().st_size,
        }
        for path in sorted(package_dir.rglob("*"))
        if path.is_file()
    ]


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "dist" / "portable"))
    parser.add_argument("--skip-pyinstaller", action="store_true")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    work = output / "work"
    artifact_dir = output / "artifacts"
    target = f"{platform.system().lower()}-{platform.machine().lower()}"
    build_resource_manifest()
    if not args.skip_pyinstaller:
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean",
            "--distpath", str(output / "bundle"),
            "--workpath", str(work),
            str(ROOT / "package/haven42.spec"),
        ], cwd=ROOT, check=True)
    package_dir = output / "bundle" / "haven42"
    if not package_dir.is_dir():
        raise SystemExit("PyInstaller one-folder output was not found.")
    unexpected = {path.name for path in package_dir.iterdir()} - ALLOWED_PACKAGE_ENTRIES
    if unexpected:
        raise SystemExit(f"Unexpected top-level package entries: {sorted(unexpected)}")
    (package_dir / "DEVELOPMENT-BUILD.txt").write_text(
        "Haven 42 unsigned development build.\n"
        "No installer, signing, notarization, updater activation, or production-readiness claim.\n",
        encoding="utf-8",
    )
    dependencies = dependency_records()
    evidence = output / "evidence"
    write_json(evidence / "dependency-inventory.json", {
        "schemaVersion": 2,
        "target": target,
        "runtimeComponents": [{
            "name": "CPython",
            "version": platform.python_version(),
            "scope": "embedded-runtime",
        }],
        "buildDependencies": dependencies,
    })
    archive_staging = tempfile.TemporaryDirectory(
        prefix="haven42-archive-staging-",
        dir=output,
    )
    staged_package_dir = Path(archive_staging.name) / "haven42"
    shutil.copytree(package_dir, staged_package_dir, symlinks=False)
    package_files = package_file_records(staged_package_dir)
    write_json(evidence / "package-file-inventory.json", {
        "schemaVersion": 1,
        "algorithm": "sha256",
        "packageRoot": "haven42",
        "files": package_files,
    })
    write_json(evidence / "build-provenance.json", {
        "schemaVersion": 1,
        "artifactKind": "unsigned-development",
        "application": {"name": "Haven 42", "version": APP_VERSION},
        "source": {
            "repository": "https://github.com/hysel/haven-42",
            "commit": commit_identity(),
        },
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
            "component": {"type": "application", "name": "Haven 42", "version": APP_VERSION},
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
                "type": "framework",
                "name": "CPython",
                "version": platform.python_version(),
                "scope": "required",
            }
        ],
    })
    notices = [
        "THIRD-PARTY NOTICES — unsigned development package",
        "",
        "Build-tool versions and license expressions are an explicit reviewed allowlist.",
        "These tools influence the generated package but are not imported application dependencies.",
        "",
    ]
    notices.extend(f"{item['name']} {item['version']} — {item['license']}" for item in dependencies)
    (evidence / "THIRD-PARTY-NOTICES.txt").write_text("\n".join(notices) + "\n", encoding="utf-8")
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
