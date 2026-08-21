#!/usr/bin/env python3
"""Hostile tests for the unsigned macOS development app verifier."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import stat
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load("macos_app_builder_for_validation", "build-macos-development-app.py")
VALIDATOR = load("macos_app_validator", "validate-macos-development-app.py")


def source_fixture(root: Path) -> Path:
    source = root / "source"
    source.mkdir()
    binary = source / "haven42"
    binary.write_bytes(b"fixture executable")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    for directory in ("_internal", "licenses"):
        (source / directory).mkdir()
        (source / directory / "fixture.txt").write_text("fixture", encoding="utf-8")
    for name in ("DEVELOPMENT-BUILD.txt", "LICENSE.txt", "THIRD-PARTY-NOTICES.txt"):
        (source / name).write_text("fixture", encoding="utf-8")
    return source


def expect(directory: Path, code: str) -> None:
    try:
        VALIDATOR.validate(directory)
    except VALIDATOR.ValidationError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"Unsafe app output accepted: {code}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="haven42-macos-app-validator-") as temporary:
        root = Path(temporary)
        accepted = root / "accepted"
        BUILDER.build_bundle(source_fixture(root), accepted, "0.4.0-alpha.2")
        result = VALIDATOR.validate(accepted)
        assert result["status"] == "development-only"

        tampered = root / "tampered"
        shutil.copytree(accepted, tampered)
        (tampered / "Haven 42.app" / "Contents" / "Resources" / "README.txt").write_text(
            "tampered", encoding="utf-8",
        )
        expect(tampered, "app-inventory-mismatch")

        extra = root / "extra"
        shutil.copytree(accepted, extra)
        (extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        expect(extra, "unexpected-app-output-entry")

        linked = root / "linked"
        shutil.copytree(accepted, linked)
        archive = linked / VALIDATOR.ARCHIVE_NAME
        with tarfile.open(archive, "w:gz") as stream:
            item = tarfile.TarInfo("Haven 42.app/link")
            item.type = tarfile.SYMTYPE
            item.linkname = "../../escape"
            stream.addfile(item)
        sums = linked / "SHA256SUMS"
        sums.write_text(
            f"{VALIDATOR.sha256(archive)}  {archive.name}\n"
            f"{VALIDATOR.sha256(linked / 'macos-app-build-result.json')}  macos-app-build-result.json\n",
            encoding="utf-8",
        )
        expect(linked, "non-regular-archive-member")
    print("macOS development app validator tests: 4 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
