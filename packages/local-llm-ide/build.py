#!/usr/bin/env python3
"""Build the standalone Haven 42 Local LLM IDE Tools ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
VERSION = "0.1.0-development"
PACKAGE_NAME = "haven42-local-llm-ide-tools"
SOURCE_FILES = ("README.md", "haven42_ide.py", "setup.ps1", "setup.sh")
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_output(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    allowed = (ROOT / "dist").resolve()
    try:
        relative = resolved.relative_to(allowed)
    except ValueError as error:
        raise SystemExit("The IDE package output must stay inside dist.") from error
    if not relative.parts or resolved.is_symlink():
        raise SystemExit("The IDE package output folder is unsafe.")
    return resolved


def source_entries() -> list[tuple[Path, Path]]:
    entries: list[tuple[Path, Path]] = []
    for name in SOURCE_FILES:
        source = SOURCE / name
        if not source.is_file() or source.is_symlink():
            raise SystemExit(f"IDE package source is missing or unsafe: {name}")
        entries.append((source, Path(name)))
    license_file = ROOT / "LICENSE"
    if not license_file.is_file() or license_file.is_symlink():
        raise SystemExit("Project license is missing or unsafe.")
    entries.append((license_file, Path("LICENSE.txt")))
    continue_root = ROOT / ".continue"
    for source in sorted(continue_root.rglob("*")):
        if source.is_symlink():
            raise SystemExit("The Continue source bundle contains an unsafe link.")
        if source.is_file() and not source.name.startswith("config.local"):
            entries.append((source, Path("assets/continue") / source.relative_to(continue_root)))
    if len(entries) <= len(SOURCE_FILES) + 1:
        raise SystemExit("No Continue assets were selected.")
    if any(source.stat().st_size > MAX_FILE_BYTES for source, _ in entries):
        raise SystemExit("An IDE package source file is unexpectedly large.")
    if sum(source.stat().st_size for source, _ in entries) > MAX_TOTAL_BYTES:
        raise SystemExit("The IDE package sources are unexpectedly large.")
    return entries


def add_zip_file(package: zipfile.ZipFile, source: Path, archive_name: Path) -> None:
    info = zipfile.ZipInfo(archive_name.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    mode = 0o755 if source.name == "setup.sh" else 0o644
    info.external_attr = (mode | 0o100000) << 16
    package.writestr(info, source.read_bytes())


def build(output_value: str) -> tuple[Path, Path, Path]:
    output = safe_output(output_value)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{PACKAGE_NAME}-{VERSION}.zip"
    checksum = output / f"{archive.name}.sha256"
    outside_manifest = output / f"{PACKAGE_NAME}-{VERSION}.manifest.json"
    with tempfile.TemporaryDirectory(prefix="haven42-ide-package-", dir=output) as raw:
        staging = Path(raw) / PACKAGE_NAME
        staging.mkdir()
        for source, relative in source_entries():
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        records = [
            {
                "path": path.relative_to(staging).as_posix(),
                "sha256": digest(path),
                "sizeBytes": path.stat().st_size,
            }
            for path in sorted(staging.rglob("*"))
            if path.is_file()
        ]
        manifest = {
            "schemaVersion": 1,
            "name": "Haven 42 Local LLM IDE Tools",
            "version": VERSION,
            "thirdPartySoftwareBundled": False,
            "files": records,
        }
        manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        (staging / "MANIFEST.json").write_text(manifest_text, encoding="utf-8", newline="\n")
        outside_manifest.write_text(manifest_text, encoding="utf-8", newline="\n")
        if archive.exists():
            archive.unlink()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    add_zip_file(package, path, Path(PACKAGE_NAME) / path.relative_to(staging))
    checksum.write_text(f"{digest(archive)}  {archive.name}\n", encoding="ascii", newline="\n")
    return archive, checksum, outside_manifest


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--output", default="dist/local-llm-ide")
    options = arguments.parse_args()
    for path in build(options.output):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
