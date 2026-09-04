#!/usr/bin/env python3
"""Effect-free tests for sanitized physical macOS app evidence."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load("macos_app_builder_for_summary", "build-macos-development-app.py")
SUMMARY = load("macos_app_summary", "summarize-alpha2-macos-development-app.py")


def source_fixture(root: Path) -> Path:
    source = root / "source"
    source.mkdir()
    executable = source / "haven42"
    executable.write_bytes(b"fixture")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    internal = source / "_internal"
    internal.mkdir()
    (internal / "base_library.zip").write_bytes(b"fixture")
    for name in ("config", "examples", "package", "scripts", "web"):
        directory = internal / name
        directory.mkdir()
        (directory / "fixture.txt").write_text("fixture", encoding="utf-8")
    for name in ("libcrypto.3.dylib", "libssl.3.dylib", "libzstd.1.dylib"):
        (internal / name).write_bytes(b"fixture")
    runtime = internal / "python3.14" / "lib-dynload"
    runtime.mkdir(parents=True)
    (runtime / "fixture.so").write_bytes(b"fixture")
    framework_version = internal / "Python.framework" / "Versions" / "3.14"
    (framework_version / "Resources").mkdir(parents=True)
    (framework_version / "Python").write_bytes(b"fixture")
    (framework_version / "Resources" / "Info.plist").write_bytes(b"fixture")
    (internal / "Python").symlink_to("Python.framework/Versions/3.14/Python")
    (internal / "Python.framework" / "Python").symlink_to("Versions/Current/Python")
    (internal / "Python.framework" / "Resources").symlink_to("Versions/Current/Resources")
    (internal / "Python.framework" / "Versions" / "Current").symlink_to("3.14")
    (source / "licenses").mkdir()
    (source / "licenses" / "fixture.txt").write_text("fixture", encoding="utf-8")
    for name in ("DEVELOPMENT-BUILD.txt", "LICENSE.txt", "THIRD-PARTY-NOTICES.txt"):
        (source / name).write_text("fixture", encoding="utf-8")
    return source


def portable_fixture(path: Path, package_files: list[dict[str, object]]) -> None:
    path.mkdir()
    (path / "build-provenance.json").write_text(json.dumps({
        "application": {"name": "Haven 42", "version": "0.4.0-alpha.2"},
        "environment": {"operatingSystem": "darwin", "architecture": "arm64"},
        "source": {
            "repository": "https://github.com/hysel/haven-42",
            "commit": "a" * 40, "treeState": "modified-uncommitted",
            "commitIsExactSource": False, "snapshotSha256": "b" * 64,
        },
    }), encoding="utf-8")
    (path / "package-file-inventory.json").write_text(json.dumps({
        "files": package_files,
    }), encoding="utf-8")
    (path / "haven42-darwin-arm64-unsigned-development.tar.gz").write_bytes(b"archive")


def hardware_fixture(path: Path) -> None:
    path.write_text(json.dumps({
        "kind": "haven42-apple-silicon-model-qualification-result",
        "hardwareProfile": {
            "profileId": "apple-m4-16gib-macos26-metal",
            "platformFamily": "macos", "architecture": "arm64",
            "backend": "metal", "systemMemoryGiB": 16,
        },
    }), encoding="utf-8")


def main() -> int:
    if os.name == "nt":
        assert callable(SUMMARY.wrapped_package_records)
        assert len(SUMMARY.VALIDATOR.APP_LINKS) == 12
        print("macOS development app summary tests: 4 passed (Windows contract; native link tests run on macOS)")
        return 0
    with tempfile.TemporaryDirectory(prefix="haven42-macos-app-summary-") as temporary:
        root = Path(temporary)
        source = source_fixture(root)
        materialized = root / "materialized"
        shutil.copytree(source, materialized, symlinks=False)
        package_files = BUILDER.safe_files(materialized)
        artifacts = root / "artifacts"
        BUILDER.build_bundle(source, artifacts, "0.4.0-alpha.2")
        portable = root / "portable"
        portable_fixture(portable, package_files)
        hardware = root / "hardware.json"
        hardware_fixture(hardware)
        log = root / "package.log"
        log.write_text(SUMMARY.SUCCESS_MARKER + "\n", encoding="utf-8")
        side_effect = (
            subprocess.CompletedProcess([], 0, "Mach-O 64-bit executable arm64\n", ""),
            subprocess.CompletedProcess([], 1, "", "unsigned"),
            subprocess.CompletedProcess([], 3, "", "rejected"),
        )
        with (
            patch.object(SUMMARY.PORTABLE_VALIDATOR, "verify"),
            patch.object(SUMMARY, "tool", side_effect=side_effect),
        ):
            result = SUMMARY.summarize(artifacts, portable, hardware, log)
        assert result["status"] == "partial-pass"
        assert result["app"]["nativeArchitecture"] == "arm64"
        assert result["app"]["globalPythonRequired"] is False
        assert result["tests"]["packagedBrowserFlow"] is False
        assert result["tests"]["packagedBrowserChecks"] == 0
        assert result["tests"]["boundedAttachmentFlow"] is False
        assert result["tests"]["automatedAccessibilityFlow"] is False
        assert result["tests"]["localPrivacyBoundary"] is False
        assert all(
            value for key, value in result["tests"].items()
            if key not in {
                "packagedBrowserFlow", "packagedBrowserChecks",
                "boundedAttachmentFlow", "automatedAccessibilityFlow",
                "localPrivacyBoundary",
            }
        )
        assert "packaged-real-browser-flow" in result["open"]
        assert all(value is False for value in result["authority"].values())
        assert all(value is False for value in result["privacy"].values())
        assert result["platformTrust"]["codeSignatureStructureValid"] is False
        assert result["platformTrust"]["gatekeeperAdmittedOnTestHost"] is False

        browser_log = root / "browser.log"
        browser_log.write_text(
            SUMMARY.BROWSER_EVIDENCE
            + "\nHaven 42 headless browser flow passed: 622 checks.\n",
            encoding="utf-8",
        )
        with (
            patch.object(SUMMARY.PORTABLE_VALIDATOR, "verify"),
            patch.object(SUMMARY, "tool", side_effect=side_effect),
        ):
            browser_result = SUMMARY.summarize(
                artifacts, portable, hardware, log, browser_log,
            )
        assert browser_result["tests"]["packagedBrowserFlow"] is True
        assert browser_result["tests"]["packagedBrowserChecks"] == 622
        assert browser_result["tests"]["boundedAttachmentFlow"] is True
        assert browser_result["tests"]["automatedAccessibilityFlow"] is True
        assert browser_result["tests"]["localPrivacyBoundary"] is True
        assert "packaged-real-browser-flow" not in browser_result["open"]

        log.write_text("unexpected output\n", encoding="utf-8")
        try:
            with patch.object(SUMMARY.PORTABLE_VALIDATOR, "verify"):
                SUMMARY.summarize(artifacts, portable, hardware, log)
        except SUMMARY.SummaryError as error:
            assert str(error) == "package-test-marker-missing-or-ambiguous"
        else:
            raise AssertionError("Ambiguous package test log was accepted.")

        log.write_text(SUMMARY.SUCCESS_MARKER + "\n", encoding="utf-8")
        with (
            patch.object(SUMMARY.PORTABLE_VALIDATOR, "verify"),
            patch.object(SUMMARY, "tool", return_value=subprocess.CompletedProcess([], 0, "ELF x86-64\n", "")),
        ):
            try:
                SUMMARY.summarize(artifacts, portable, hardware, log)
            except SUMMARY.SummaryError as error:
                assert str(error) == "native-arm64-executable-not-proven"
            else:
                raise AssertionError("Wrong executable architecture was accepted.")
    print("macOS development app summary tests: 4 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
