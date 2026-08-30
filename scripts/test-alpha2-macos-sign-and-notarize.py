#!/usr/bin/env python3
"""Tests for the fail-closed macOS signing and notarization runner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "alpha2-macos-sign-and-notarize.py"
SPEC = importlib.util.spec_from_file_location("alpha2_macos_sign_and_notarize", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
IDENTITY = "A" * 40


def completed(command: list[str], code: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(command, code, stdout, stderr)


def source_app(root: Path) -> Path:
    app = root / "Haven 42.app"
    executable = app / "Contents" / "MacOS" / "haven42"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"synthetic-mach-o")
    with (app / "Contents" / "Info.plist").open("wb") as stream:
        plistlib.dump({
            "CFBundleIdentifier": "org.haven42.desktop",
            "CFBundleExecutable": "haven42",
            "Haven42ReleaseVersion": "0.4.0-alpha.2",
        }, stream)
    return app


def source_binding() -> dict[str, str]:
    return {
        "unsignedArtifactSha256": "1" * 64,
        "buildEvidenceSha256": "2" * 64,
        "appInventoryCanonicalSha256": "3" * 64,
    }


class FakeRunner:
    def __init__(self, *, accepted: bool = True) -> None:
        self.accepted = accepted
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str], **_: object) -> subprocess.CompletedProcess:
        self.commands.append(command)
        executable = Path(command[0]).name
        if executable == "security":
            return completed(command, stdout=(
                f'  1) {IDENTITY} "Developer ID Application: Haven 42 Test (ABCDE12345)"\n'
                "     1 valid identities found\n"
            ).encode())
        if executable == "file":
            output = b"Mach-O 64-bit executable arm64\n" if command[-1].endswith("haven42") else b"XML document text\n"
            return completed(command, stdout=output)
        if executable == "codesign" and "-dv" in command:
            return completed(command, stderr=(
                b"Authority=Developer ID Application: Haven 42 Test (ABCDE12345)\n"
                b"TeamIdentifier=ABCDE12345\nflags=0x10000(runtime)\n"
            ))
        if executable == "ditto":
            Path(command[-1]).write_bytes(b"synthetic-notarization-archive")
            return completed(command)
        if executable == "xcrun" and "notarytool" in command:
            status = "Accepted" if self.accepted else "Invalid"
            return completed(command, 0 if self.accepted else 1, json.dumps({"status": status}).encode())
        return completed(command)


class SigningTests(unittest.TestCase):
    def test_framework_macho_files_are_signed_as_one_framework_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            app = source_app(Path(temporary))
            standalone = app / "Contents" / "Frameworks" / "libssl.3.dylib"
            framework = app / "Contents" / "Frameworks" / "Python.framework"
            framework_binary = framework / "Versions" / "3.14" / "Python"
            standalone.parent.mkdir(parents=True, exist_ok=True)
            standalone.write_bytes(b"synthetic-mach-o")
            framework_binary.parent.mkdir(parents=True)
            framework_binary.write_bytes(b"synthetic-mach-o")

            def macho(command: list[str], **_: object) -> subprocess.CompletedProcess:
                return completed(command, stdout=b"Mach-O 64-bit executable arm64\n")

            files, frameworks = MODULE.code_targets(app, runner=macho)
            self.assertIn(standalone, files)
            self.assertNotIn(app / "Contents" / "MacOS" / "haven42", files)
            self.assertNotIn(framework_binary, files)
            self.assertEqual(frameworks, [framework])

    def test_signed_notarized_result_is_sanitized_and_stapled_archive_is_repacked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = source_app(root / "source")
            output = root / "result"
            runner = FakeRunner()
            with mock.patch.object(MODULE, "require_tool", return_value=None), mock.patch.object(
                MODULE, "validate_source_directory",
                return_value=(app, "0.4.0-alpha.2", source_binding()),
            ):
                result = MODULE.execute(
                    app.parent, output, IDENTITY, "haven42-notary",
                    runner=runner, platform_name="darwin",
                )
            self.assertEqual(result["status"], "passed")
            self.assertTrue(result["platformTrust"]["developerIdSigned"])
            self.assertTrue(result["platformTrust"]["hardenedRuntime"])
            self.assertTrue(result["platformTrust"]["notarized"])
            self.assertTrue(result["platformTrust"]["ticketStapled"])
            self.assertEqual(result["source"], source_binding())
            encoded = (output / "macos-signing-notarization-result.json").read_text(encoding="utf-8")
            self.assertNotIn(IDENTITY, encoded)
            self.assertNotIn("haven42-notary", encoded)
            ditto_commands = [command for command in runner.commands if Path(command[0]).name == "ditto"]
            self.assertEqual(len(ditto_commands), 2)
            self.assertTrue((output / "haven42-darwin-arm64-developer-id-notarized.zip").is_file())
            self.assertTrue((output / "SHA256SUMS").is_file())

    def test_rejected_notarization_cleans_temporary_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = source_app(root / "source")
            runner = FakeRunner(accepted=False)
            with mock.patch.object(MODULE, "require_tool", return_value=None), mock.patch.object(
                MODULE, "validate_source_directory",
                return_value=(app, "0.4.0-alpha.2", source_binding()),
            ):
                with self.assertRaisesRegex(MODULE.SigningError, "notarization-not-accepted"):
                    MODULE.execute(
                        app.parent, root / "result", IDENTITY, "haven42-notary",
                        runner=runner, platform_name="darwin",
                    )
            self.assertFalse((root / "result").exists())
            leftovers = list(root.glob("haven42-macos-signing-*"))
            self.assertEqual(leftovers, [])

    def test_only_developer_id_application_identity_is_accepted(self) -> None:
        def wrong_identity(command: list[str], **_: object) -> subprocess.CompletedProcess:
            return completed(command, stdout=f'1) {IDENTITY} "Apple Development: Test"\n'.encode())

        with self.assertRaisesRegex(MODULE.SigningError, "developer-id-application-required"):
            MODULE.validate_identity(IDENTITY, runner=wrong_identity)

    def test_profile_and_platform_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            app = source_app(Path(temporary) / "source")
            with self.assertRaisesRegex(MODULE.SigningError, "physical-macos-required"):
                MODULE.execute(app.parent, Path(temporary) / "out", IDENTITY, "valid", platform_name="win32")
            with self.assertRaisesRegex(MODULE.SigningError, "notary-profile-name-invalid"):
                MODULE.execute(app.parent, Path(temporary) / "out", IDENTITY, "bad profile", platform_name="darwin")

    def test_source_directory_must_pass_existing_unsigned_app_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(MODULE.SigningError, "unsigned-source-validation-failed"):
                MODULE.validate_source_directory(root)


if __name__ == "__main__":
    unittest.main()
