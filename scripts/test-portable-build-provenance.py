#!/usr/bin/env python3
"""Effect-free tests for portable Python distribution provenance."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "portable_builder",
    ROOT / "scripts" / "build-portable-development-package.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rejected(target: str, asset: str, digest: str, message: str) -> None:
    with patch.dict(
        "os.environ",
        {
            "GITHUB_ACTIONS": "true",
            "HAVEN42_PYTHON_SOURCE_ASSET": asset,
            "HAVEN42_PYTHON_SOURCE_SHA256": digest,
        },
        clear=False,
    ):
        try:
            MODULE.python_distribution_provenance(target)
        except SystemExit as error:
            assert str(error) == message, (str(error), message)
            return
    raise AssertionError(f"Python provenance unexpectedly accepted: {target}")


def main() -> int:
    with patch.dict("os.environ", {"GITHUB_ACTIONS": "false"}, clear=False):
        local = MODULE.python_distribution_provenance("windows-amd64")
    assert local == {
        "repository": "local-build-environment",
        "releaseTag": "",
        "releaseCommit": "",
        "asset": "",
        "sha256": "",
        "verification": "local-unverified",
    }
    passed = 1

    for target, expected in MODULE.PYTHON_DISTRIBUTIONS.items():
        with patch.dict(
            "os.environ",
            {
                "GITHUB_ACTIONS": "true",
                "HAVEN42_PYTHON_SOURCE_ASSET": expected["asset"],
                "HAVEN42_PYTHON_SOURCE_SHA256": expected["sha256"],
            },
            clear=False,
        ):
            result = MODULE.python_distribution_provenance(target)
        assert result == {
            "repository": "actions/python-versions",
            "releaseTag": "3.14.6-27283001424",
            "releaseCommit": "25a990ef82051ebb9cba2b6ed6b79e61148a5bfb",
            "asset": expected["asset"],
            "sha256": expected["sha256"],
            "verification": "pinned-setup-python-release-metadata",
        }
        passed += 1
        rejected(
            target,
            expected["asset"],
            "0" * 64,
            "GitHub Python distribution identity mismatch.",
        )
        passed += 1

    rejected(
        "linux-riscv64",
        "unknown.tar.gz",
        "0" * 64,
        "No admitted Python distribution for target: linux-riscv64",
    )
    passed += 1

    with (
        patch.object(MODULE.platform, "system", return_value="Windows"),
        patch.object(
            MODULE,
            "windows_system_root",
            return_value=MODULE.Path(r"C:\Windows"),
        ),
        patch.object(MODULE.Path, "is_dir", return_value=True),
        patch.dict(
            "os.environ",
            {
                "PATH": r"C:\hostile-jdk\bin;C:\unreviewed-tools",
                "PYTHONHOME": r"C:\hostile-python",
                "PYTHONPATH": r"C:\hostile-imports",
                "SystemRoot": r"C:\Windows",
            },
            clear=False,
        ),
    ):
        build_environment = MODULE.pyinstaller_environment()
    assert "hostile" not in build_environment["PATH"].casefold()
    assert "unreviewed" not in build_environment["PATH"].casefold()
    assert "PYTHONHOME" not in build_environment
    assert "PYTHONPATH" not in build_environment
    assert build_environment["PYTHONNOUSERSITE"] == "1"
    assert build_environment["PYTHONSAFEPATH"] == "1"
    assert str(MODULE.Path(sys.executable).resolve().parent) in build_environment["PATH"]
    passed += 1

    spec_text = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert 'startswith("api-ms-win-")' in spec_text
    assert '== "ucrtbase.dll"' in spec_text
    assert "VCRUNTIME" in spec_text
    assert MODULE.LICENSE_EVIDENCE["LIBFFI-3.4.4-LICENSE.txt"] == (
        "2c9c2acb9743e6b007b91350475308aee44691d96aa20eacef8e199988c8c388"
    )
    passed += 1

    print(f"Portable build provenance self-test passed: {passed} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
