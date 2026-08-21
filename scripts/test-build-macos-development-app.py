#!/usr/bin/env python3
"""Effect-free tests for the unsigned macOS development app builder."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import plistlib
import stat
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "macos_app_builder", ROOT / "scripts" / "build-macos-development-app.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixture(root: Path) -> Path:
    source = root / "source"
    source.mkdir(parents=True)
    executable = source / "haven42"
    executable.write_bytes(b"fixture executable")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    (source / "_internal").mkdir()
    (source / "_internal" / "app.js").write_text("fixture", encoding="utf-8")
    (source / "licenses").mkdir()
    (source / "licenses" / "MIT.txt").write_text("fixture", encoding="utf-8")
    for name in ("DEVELOPMENT-BUILD.txt", "LICENSE.txt", "THIRD-PARTY-NOTICES.txt"):
        (source / name).write_text("fixture", encoding="utf-8")
    return source


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="haven42-macos-app-test-") as temporary:
        root = Path(temporary)
        source = fixture(root)
        output = root / "output"
        result = MODULE.build_bundle(source, output, "0.4.0-alpha.2")
        app = output / "Haven 42.app"
        with (app / "Contents" / "Info.plist").open("rb") as stream:
            plist = plistlib.load(stream)
        assert plist["CFBundleIdentifier"] == "org.haven42.desktop"
        assert plist["CFBundleExecutable"] == "haven42"
        assert plist["CFBundleShortVersionString"] == "0.4.0"
        assert plist["CFBundleVersion"] == "0.4.2"
        assert plist["Haven42ReleaseVersion"] == "0.4.0-alpha.2"
        assert plist["LSMultipleInstancesProhibited"] is True
        assert plist["LSUIElement"] is True
        assert plist["NSLocalNetworkUsageDescription"] == (
            "Haven 42 connects only to an AI server you choose on your private "
            "network. It does not scan for nearby devices."
        )
        if os.name != "nt":
            assert (app / "Contents" / "MacOS" / "haven42").stat().st_mode & stat.S_IXUSR
        assert (app / "Contents" / "Frameworks" / "app.js").is_file()
        assert (
            app / "Contents" / "Resources" / "PortablePackage" / "licenses" / "MIT.txt"
        ).is_file()
        assert not (app / "Contents" / "MacOS" / "_internal").exists()
        assert result["runtime"]["globalPythonRequired"] is False
        assert result["platformTrust"] == {
            "developerIdSigned": False, "notarized": False,
            "gatekeeperAdmissionClaimed": False,
            "publicDistributionAllowed": False,
        }
        evidence = json.loads(
            (output / "macos-app-build-result.json").read_text(encoding="utf-8")
        )
        assert evidence == result
        assert evidence["inventory"]["fileCount"] >= 9
        assert (output / "haven42-darwin-arm64-unsigned-development-app.tar.gz").is_file()
        assert len((output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()) == 2
        try:
            MODULE.build_bundle(source, output, "0.4.0-alpha.2")
        except MODULE.AppBuildError as error:
            assert str(error) == "output-already-exists"
        else:
            raise AssertionError("Existing app output was overwritten.")

        unsafe = fixture(root / "unsafe")
        (unsafe / "unexpected.txt").write_text("fixture", encoding="utf-8")
        try:
            MODULE.build_bundle(unsafe, root / "unsafe-output", "0.4.0-alpha.2")
        except MODULE.AppBuildError as error:
            assert str(error).startswith("unexpected-source-entry:")
        else:
            raise AssertionError("Unexpected source entry was accepted.")

        try:
            MODULE.info_plist("0.4.0-alpha.3")
        except MODULE.AppBuildError as error:
            assert str(error) == "unsupported-app-version"
        else:
            raise AssertionError("Unsupported app version was accepted.")

        assert MODULE.ALLOWED_SOURCE_LINKS == {
            "_internal/Python": "Python.framework/Versions/3.14/Python",
            "_internal/Python.framework/Python": "Versions/Current/Python",
            "_internal/Python.framework/Resources": "Versions/Current/Resources",
            "_internal/Python.framework/Versions/Current": "3.14",
        }
    print("macOS development app builder tests: 3 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
