#!/usr/bin/env python3
"""Effect-free tests for portable Python distribution provenance."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
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
    package_doc = (ROOT / "docs" / "portable-development-package.md").read_text(
        encoding="utf-8"
    )
    assert "python3.14 -m venv --copies .venv-build" in package_doc
    normalized_package_doc = " ".join(package_doc.split())
    assert "People running the packaged Haven 42 app do not install" in normalized_package_doc
    passed = 1

    assert MODULE.resolve_app_version("platform-default", "Darwin") == MODULE.ALPHA_1_VERSION
    assert MODULE.resolve_app_version("alpha2", "Darwin") == MODULE.ALPHA_2_VERSION
    assert MODULE.resolve_app_version("platform-default", "Linux") == MODULE.ALPHA_2_VERSION
    assert MODULE.resolve_app_version("platform-default", "Windows") == MODULE.ALPHA_1_VERSION
    try:
        MODULE.resolve_app_version("alpha2", "Unsupported")
    except SystemExit as error:
        assert "Windows, Linux, or macOS" in str(error)
    else:
        raise AssertionError("Unsupported Alpha 2 build platform was accepted.")
    passed += 1

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
    passed += 1

    with (
        patch.object(
            MODULE,
            "installed_pyinstaller_version",
            return_value=MODULE.REQUIRED_PYINSTALLER_VERSION,
        ),
        patch.object(MODULE.subprocess, "run") as run,
    ):
        assert MODULE.delegate_to_repository_build_environment() is None
        run.assert_not_called()
    passed += 1

    with (
        patch.object(MODULE, "installed_pyinstaller_version", return_value=None),
        patch.object(MODULE, "repository_build_python", return_value=None),
    ):
        try:
            MODULE.delegate_to_repository_build_environment()
        except SystemExit as error:
            assert ".venv-build is missing" in str(error)
        else:
            raise AssertionError("Missing repository build environment was accepted.")
    passed += 1

    delegated_python = ROOT / ".venv-build" / "Scripts" / "python.exe"
    probe_result = MODULE.subprocess.CompletedProcess(
        args=[], returncode=0, stdout="3.14.6\n6.21.0\n", stderr=""
    )
    delegated_result = MODULE.subprocess.CompletedProcess(args=[], returncode=23)
    with (
        patch.object(MODULE, "installed_pyinstaller_version", return_value=None),
        patch.object(
            MODULE,
            "repository_build_python",
            return_value=delegated_python,
        ),
        patch.object(
            MODULE.subprocess,
            "run",
            side_effect=(probe_result, delegated_result),
        ) as run,
    ):
        assert MODULE.delegate_to_repository_build_environment() == 23
        assert run.call_count == 2
        assert run.call_args_list[0].args[0][0] == str(delegated_python)
        assert run.call_args_list[0].args[0][1] == "-I"
        assert run.call_args_list[1].args[0][0] == str(delegated_python)
        assert run.call_args_list[1].args[0][1] == "-I"
    passed += 1

    wrong_probe = MODULE.subprocess.CompletedProcess(
        args=[], returncode=0, stdout="3.14.6\n6.20.0\n", stderr=""
    )
    with (
        patch.object(MODULE, "installed_pyinstaller_version", return_value=None),
        patch.object(
            MODULE,
            "repository_build_python",
            return_value=delegated_python,
        ),
        patch.object(MODULE.subprocess, "run", return_value=wrong_probe) as run,
    ):
        try:
            MODULE.delegate_to_repository_build_environment()
        except SystemExit as error:
            assert "PyInstaller 6.21.0" in str(error)
        else:
            raise AssertionError("Wrong repository PyInstaller version was accepted.")
        assert run.call_count == 1
    passed += 1

    wrong_python_probe = MODULE.subprocess.CompletedProcess(
        args=[], returncode=0, stdout="3.13.0\n6.21.0\n", stderr=""
    )
    with (
        patch.object(MODULE, "installed_pyinstaller_version", return_value=None),
        patch.object(
            MODULE,
            "repository_build_python",
            return_value=delegated_python,
        ),
        patch.object(
            MODULE.subprocess,
            "run",
            return_value=wrong_python_probe,
        ),
    ):
        try:
            MODULE.delegate_to_repository_build_environment()
        except SystemExit as error:
            assert "Python 3.14.6" in str(error)
        else:
            raise AssertionError("Wrong repository Python version was accepted.")
    passed += 1

    with patch.dict(
        "os.environ",
        {
            "PYTHONHOME": r"C:\hostile-python",
            "PYTHONPATH": r"C:\hostile-imports",
        },
        clear=False,
    ):
        isolated_environment = MODULE.isolated_python_environment()
    assert "PYTHONHOME" not in isolated_environment
    assert "PYTHONPATH" not in isolated_environment
    assert isolated_environment["PYTHONNOUSERSITE"] == "1"
    assert isolated_environment["PYTHONSAFEPATH"] == "1"
    passed += 1

    with tempfile.TemporaryDirectory(prefix="haven42-build-environment-") as temporary:
        root = Path(temporary)
        scripts = root / ".venv-build" / "Scripts"
        scripts.mkdir(parents=True)
        executable = scripts / "python.exe"
        executable.write_bytes(b"fixture")
        with patch.object(MODULE.platform, "system", return_value="Windows"):
            assert MODULE.repository_build_python(root) == executable.resolve()
    passed += 1

    commit = "1" * 40
    snapshot = "2" * 64
    with patch.dict(
        "os.environ",
        {
            "HAVEN42_SOURCE_COMMIT": commit,
            "HAVEN42_SOURCE_TREE_STATE": "modified-uncommitted",
            "HAVEN42_SOURCE_SNAPSHOT_SHA256": snapshot,
        },
        clear=False,
    ):
        source = MODULE.source_provenance()
    assert source == {
        "repository": "https://github.com/hysel/haven-42",
        "commit": commit,
        "treeState": "modified-uncommitted",
        "commitIsExactSource": False,
        "snapshotSha256": snapshot,
    }
    passed += 1

    for environment, message in (
        (
            {"HAVEN42_SOURCE_COMMIT": commit, "HAVEN42_SOURCE_TREE_STATE": "modified-uncommitted", "HAVEN42_SOURCE_SNAPSHOT_SHA256": ""},
            "Modified source exports require HAVEN42_SOURCE_SNAPSHOT_SHA256.",
        ),
        (
            {"HAVEN42_SOURCE_COMMIT": commit, "HAVEN42_SOURCE_TREE_STATE": "unknown", "HAVEN42_SOURCE_SNAPSHOT_SHA256": snapshot},
            "Invalid HAVEN42_SOURCE_TREE_STATE.",
        ),
        (
            {"HAVEN42_SOURCE_COMMIT": commit, "HAVEN42_SOURCE_TREE_STATE": "exact-commit", "HAVEN42_SOURCE_SNAPSHOT_SHA256": "bad"},
            "Invalid HAVEN42_SOURCE_SNAPSHOT_SHA256.",
        ),
    ):
        with patch.dict("os.environ", environment, clear=False):
            try:
                MODULE.source_provenance()
            except SystemExit as error:
                assert str(error) == message
            else:
                raise AssertionError("Unsafe source provenance was accepted.")
        passed += 1

    with patch.dict(
        "os.environ",
        {
            "HAVEN42_SOURCE_COMMIT": commit,
            "HAVEN42_SOURCE_TREE_STATE": "exact-commit",
            "HAVEN42_SOURCE_SNAPSHOT_SHA256": "",
        },
        clear=False,
    ):
        exact_source = MODULE.source_provenance()
    assert exact_source["commitIsExactSource"] is True
    assert exact_source["treeState"] == "exact-commit"
    passed += 1

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
                "PYINSTALLER_CONFIG_DIR": r"C:\hostile-cache",
                "SystemRoot": r"C:\Windows",
            },
            clear=False,
        ),
    ):
        expected_config = MODULE.Path(r"E:\safe-output\config").resolve()
        build_environment = MODULE.pyinstaller_environment(expected_config)
    assert "hostile" not in build_environment["PATH"].casefold()
    assert "unreviewed" not in build_environment["PATH"].casefold()
    assert "PYTHONHOME" not in build_environment
    assert "PYTHONPATH" not in build_environment
    assert build_environment["PYTHONNOUSERSITE"] == "1"
    assert build_environment["PYTHONSAFEPATH"] == "1"
    assert build_environment["PYINSTALLER_CONFIG_DIR"] == str(expected_config)
    assert str(MODULE.Path(sys.executable).resolve().parent) in build_environment["PATH"]
    passed += 1

    safe_output = MODULE.resolve_build_output("dist/provenance-test-output")
    assert safe_output == (ROOT / "dist/provenance-test-output").resolve()
    try:
        MODULE.resolve_build_output(str(ROOT.parent / "escaped-output"))
    except SystemExit as error:
        assert "must stay beneath" in str(error)
    else:
        raise AssertionError("Escaped portable build output was accepted.")
    passed += 1

    test_output = ROOT / "dist"
    test_output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="haven42-package-link-", dir=test_output
    ) as raw:
        package = Path(raw) / "package"
        package.mkdir()
        inside = package / "inside.txt"
        inside.write_text("inside\n", encoding="utf-8")
        outside = Path(raw) / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        link = package / "escape.txt"
        try:
            link.symlink_to(outside)
        except OSError:
            pass
        else:
            try:
                MODULE.package_file_records(package)
            except SystemExit as error:
                assert "escapes the bundle" in str(error)
            else:
                raise AssertionError("Escaping package link was accepted.")
    passed += 1

    spec_text = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert 'startswith("api-ms-win-")' in spec_text
    assert '== "ucrtbase.dll"' in spec_text
    assert "VCRUNTIME" in spec_text
    attributes_text = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "LICENSE text eol=lf" in attributes_text.splitlines()
    for relative in MODULE.RESOURCE_PATHS:
        assert f'("{relative}",' in spec_text, (
            f"protected resource is missing from the PyInstaller data list: {relative}"
        )
        if relative.startswith("web/static/"):
            assert f"{relative} text eol=lf" in attributes_text.splitlines(), (
                f"protected static resource lacks an LF checkout rule: {relative}"
            )
    qualified_catalog = json.loads(
        (ROOT / "config" / "hardware-qualified-chat-models.json").read_text(
            encoding="utf-8"
        )
    )
    qualified_evidence = {
        profile["evidence"] for profile in qualified_catalog["profiles"]
    }
    assert qualified_evidence <= set(MODULE.RESOURCE_PATHS), (
        "every packaged hardware-qualified profile must include its reviewed evidence"
    )
    build_text = (ROOT / "scripts/build-portable-development-package.py").read_text(
        encoding="utf-8"
    )
    assert build_text.index("shutil.copytree(package_dir, staged_package_dir") < (
        build_text.index("preliminary_inventory = classify")
    )
    assert 'write_package_text(staged_package_dir / "THIRD-PARTY-NOTICES.txt"' in (
        build_text
    )
    assert MODULE.LICENSE_EVIDENCE["LIBFFI-3.4.4-LICENSE.txt"] == (
        "2c9c2acb9743e6b007b91350475308aee44691d96aa20eacef8e199988c8c388"
    )
    assert MODULE.LICENSE_EVIDENCE["OLLAMA-MIT-LICENSE.txt"] == (
        "5934ed2ce0d15154bcdb9c85203210abac0da4314af34081e36df4599f90b226"
    )
    passed += 1

    # Exercise the checked-out manifest, not only synthetic fixtures. This is
    # the fast local preflight that prevents a reviewed protected-resource
    # change from reaching the slower hosted package matrix with stale hashes.
    MODULE.verify_resource_manifest(ROOT)
    passed += 1

    with tempfile.TemporaryDirectory(prefix="haven42-resource-manifest-") as temporary:
        fixture_root = Path(temporary)
        for index, relative in enumerate(MODULE.RESOURCE_PATHS):
            path = fixture_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"resource-{index}\n".encode("utf-8"))
        MODULE.update_resource_manifest(fixture_root)
        MODULE.verify_resource_manifest(fixture_root)
        manifest_path = fixture_root / "package/resource-integrity.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest == MODULE.expected_resource_manifest(fixture_root)
        passed += 1

        protected = fixture_root / MODULE.RESOURCE_PATHS[0]
        protected.write_bytes(protected.read_bytes() + b"unreviewed-change\n")
        try:
            MODULE.verify_resource_manifest(fixture_root)
        except SystemExit as error:
            assert "does not match" in str(error)
        else:
            raise AssertionError("Unreviewed protected-resource change was accepted.")
        passed += 1

        MODULE.update_resource_manifest(fixture_root)
        MODULE.verify_resource_manifest(fixture_root)
        passed += 1

        protected.write_bytes(b"resource\r\n")
        try:
            MODULE.update_resource_manifest(fixture_root)
        except SystemExit as error:
            assert "repository-enforced LF" in str(error)
        else:
            raise AssertionError("CRLF protected resource was accepted.")
        protected.write_bytes(b"resource\n")
        passed += 1

        manifest["unexpected"] = True
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        try:
            MODULE.verify_resource_manifest(fixture_root)
        except SystemExit as error:
            assert "does not match" in str(error)
        else:
            raise AssertionError("Unexpected manifest field was accepted.")
        passed += 1

        manifest_path.write_text("{", encoding="utf-8")
        try:
            MODULE.verify_resource_manifest(fixture_root)
        except SystemExit as error:
            assert "unreadable" in str(error)
        else:
            raise AssertionError("Malformed resource manifest was accepted.")
        passed += 1

    print(f"Portable build provenance self-test passed: {passed} cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
