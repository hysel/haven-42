#!/usr/bin/env python3
"""Exercise hostile candidate-wheel shapes without importing or installing pypdf."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "pdf_parser_artifact_lock",
    ROOT / "scripts" / "test-pdf-parser-artifact-lock.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
BASE_LOCK = json.loads((ROOT / "config" / "pdf-parser-artifact-lock.json").read_text(encoding="utf-8"))


def build_wheel(path: Path, entries: list[tuple[str, bytes]]) -> dict:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as wheel:
        for name, content in entries:
            entry = zipfile.ZipInfo(name.replace("\\", "/"))
            entry.filename = name
            entry.orig_filename = name
            entry.compress_type = zipfile.ZIP_DEFLATED
            wheel.writestr(entry, content)
    with zipfile.ZipFile(path) as wheel:
        infos = wheel.infolist()
        lock = copy.deepcopy(BASE_LOCK)
        artifact = lock["artifact"]
        artifact["sizeBytes"] = path.stat().st_size
        artifact["sha256"] = MODULE.sha256_file(path)
        artifact["entryCount"] = len(infos)
        artifact["totalCompressedBytes"] = sum(info.compress_size for info in infos)
        artifact["totalUncompressedBytes"] = sum(info.file_size for info in infos)
        artifact["maximumEntryBytes"] = max(info.file_size for info in infos)
        metadata = wheel.read(lock["metadata"]["path"]) if lock["metadata"]["path"] in wheel.namelist() else b""
        license_text = wheel.read(lock["license"]["path"]) if lock["license"]["path"] in wheel.namelist() else b""
        lock["metadata"]["sha256"] = MODULE.sha256_bytes(metadata)
        lock["license"]["sha256"] = MODULE.sha256_bytes(license_text)
        return lock


def validate(path: Path, lock: dict) -> None:
    def require(condition: bool, label: str) -> None:
        if not condition:
            raise AssertionError(label)

    MODULE.validate_wheel(path, lock, require)


def main() -> int:
    metadata_path = BASE_LOCK["metadata"]["path"]
    license_path = BASE_LOCK["license"]["path"]
    base = [(metadata_path, b"Name: pypdf\nVersion: 6.14.2\n"), (license_path, b"BSD test fixture\n")]
    cases = 0

    with tempfile.TemporaryDirectory(prefix="haven42-pdf-artifact-") as temporary:
        wheel_path = Path(temporary) / BASE_LOCK["artifact"]["filename"]

        safe_lock = build_wheel(wheel_path, base + [("pypdf/__init__.py", b"__version__ = '6.14.2'\n")])
        validate(wheel_path, safe_lock)
        cases += 1

        hostile_entries = [
            ("parent traversal", base + [("../escape.py", b"x")]),
            ("absolute path", base + [("/absolute.py", b"x")]),
            ("drive path", base + [("C:/escape.py", b"x")]),
            ("native binary", base + [("pypdf/extension.dll", b"MZ")]),
            ("excessive entry", base + [("pypdf/large.py", b"x" * (MODULE.MAXIMUM_ENTRY_BYTES + 1))]),
            (
                "excessive entry count",
                base + [(f"pypdf/generated_{index}.py", b"x") for index in range(MODULE.MAXIMUM_WHEEL_ENTRIES)],
            ),
        ]
        for label, entries in hostile_entries:
            lock = build_wheel(wheel_path, entries)
            try:
                validate(wheel_path, lock)
            except AssertionError:
                cases += 1
            else:
                raise AssertionError(f"hostile wheel was accepted: {label}")

        if MODULE.suspicious_entry_names(["pypdf\\escape.py"]) != ["pypdf\\escape.py"]:
            raise AssertionError("backslash entry-name detector failed")
        cases += 1

        wrong_name = Path(temporary) / "renamed.whl"
        wrong_name.write_bytes(wheel_path.read_bytes())
        try:
            validate(wrong_name, lock)
        except AssertionError:
            cases += 1
        else:
            raise AssertionError("renamed wheel was accepted")

        tampered = build_wheel(wheel_path, base + [("pypdf/safe.py", b"safe")])
        tampered["artifact"]["sha256"] = "0" * 64
        try:
            validate(wheel_path, tampered)
        except AssertionError:
            cases += 1
        else:
            raise AssertionError("tampered wheel digest was accepted")

    print(f"PDF parser artifact hostile suite passed: {cases} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
