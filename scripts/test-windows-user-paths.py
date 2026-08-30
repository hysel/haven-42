#!/usr/bin/env python3
"""Tests for platform-correct portable storage-root resolution."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "windows_user_paths.py"
SPEC = importlib.util.spec_from_file_location("windows_user_paths_under_test", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PortableRootTests(unittest.TestCase):
    def test_frozen_windows_and_linux_use_executable_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "portable" / "haven42"
            executable.parent.mkdir()
            executable.write_bytes(b"fixture")
            for platform_name in ("win32", "linux"):
                with mock.patch.object(MODULE.sys, "frozen", True, create=True), mock.patch.object(
                    MODULE.sys, "executable", str(executable),
                ), mock.patch.object(MODULE.sys, "platform", platform_name):
                    self.assertEqual(MODULE.portable_install_root(), executable.parent.resolve())

    def test_frozen_macos_app_uses_directory_beside_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            install = Path(temporary) / "install"
            executable = install / "Haven 42.app" / "Contents" / "MacOS" / "haven42"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"fixture")
            with mock.patch.object(MODULE.sys, "frozen", True, create=True), mock.patch.object(
                MODULE.sys, "executable", str(executable),
            ), mock.patch.object(MODULE.sys, "platform", "darwin"):
                self.assertEqual(MODULE.portable_install_root(), install.resolve())
                self.assertEqual(MODULE.portable_data_root(), install.resolve() / "Haven42-Data")

    def test_macos_non_bundle_executable_does_not_escape_its_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "bin" / "haven42"
            executable.parent.mkdir()
            executable.write_bytes(b"fixture")
            with mock.patch.object(MODULE.sys, "frozen", True, create=True), mock.patch.object(
                MODULE.sys, "executable", str(executable),
            ), mock.patch.object(MODULE.sys, "platform", "darwin"):
                self.assertEqual(MODULE.portable_install_root(), executable.parent.resolve())


if __name__ == "__main__":
    unittest.main()
