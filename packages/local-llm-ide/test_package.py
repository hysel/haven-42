#!/usr/bin/env python3
"""Hostile and packaging tests for the standalone IDE tools package."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SOURCE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load("haven42_ide_builder", PACKAGE_SOURCE / "build.py")


def rejected(function, message: str) -> None:
    try:
        function()
    except (Exception, SystemExit) as error:
        assert message in str(error), (message, str(error))
        return
    raise AssertionError(f"Expected rejection containing: {message}")


def main() -> int:
    passed = 0
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="haven42-ide-test-", dir=dist) as raw:
        output = Path(raw) / "package"
        archive, checksum, manifest_path = BUILDER.build(str(output))
        assert archive.is_file() and checksum.is_file() and manifest_path.is_file()
        passed += 1

        expected = hashlib.sha256(archive.read_bytes()).hexdigest()
        assert checksum.read_text(encoding="ascii") == f"{expected}  {archive.name}\n"
        passed += 1

        first_archive = archive.read_bytes()
        BUILDER.build(str(output))
        assert archive.read_bytes() == first_archive
        passed += 1

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["thirdPartySoftwareBundled"] is False
        assert manifest["version"] == BUILDER.VERSION
        assert len(manifest["files"]) > 40
        passed += 1

        with zipfile.ZipFile(archive) as package:
            names = package.namelist()
            assert all("../" not in name and not name.startswith("/") for name in names)
            assert any(name.endswith("/haven42_ide.py") for name in names)
            assert any("/assets/continue/config.yaml" in name for name in names)
            assert not any("/scripts/" in name or "/web/" in name or "/tests/" in name for name in names)
            extraction = Path(raw) / "extracted"
            package.extractall(extraction)
        passed += 1

        package_root = extraction / BUILDER.PACKAGE_NAME
        TOOL = load("haven42_ide_tool", package_root / "haven42_ide.py")
        with patch.object(TOOL, "PACKAGE_ROOT", package_root):
            TOOL.verify_package(package_root)
            assert TOOL.main(["status"]) == 0
        passed += 2

        if sys.platform == "win32":
            wrapper = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(package_root / "setup.ps1"), "status"],
                capture_output=True,
                check=False,
                text=True,
            )
        else:
            shell = shutil.which("bash") or shutil.which("sh")
            assert shell is not None
            wrapper = subprocess.run(
                [shell, str(package_root / "setup.sh"), "status"],
                capture_output=True,
                check=False,
                text=True,
            )
        assert wrapper.returncode == 0 and "Haven 42 Local LLM IDE Tools" in wrapper.stdout
        passed += 1

        with tempfile.TemporaryDirectory(prefix="haven42-ide-target-", dir=dist) as target_raw:
            target = Path(target_raw)
            with patch.object(TOOL, "PACKAGE_ROOT", package_root):
                assert TOOL.safe_target(str(target)) == target.resolve()
                actions = TOOL.install_continue(target, apply=False, replace=False)
                assert actions and not (target / ".continue").exists()
                passed += 1

                TOOL.install_continue(target, apply=True, replace=False)
                assert (target / ".continue/config.yaml").is_file()
                assert not (target / ".continue.haven42-backup").exists()
                passed += 1

                rejected(
                    lambda: TOOL.install_continue(target, apply=False, replace=False),
                    "already has Continue settings",
                )
                passed += 1

                (target / ".continue/user-note.txt").write_text("keep me\n", encoding="utf-8")
                TOOL.install_continue(target, apply=True, replace=True)
                assert (target / ".continue.haven42-backup/config.yaml").is_file()
                assert (target / ".continue.haven42-backup/user-note.txt").is_file()
                assert not (target / ".continue/user-note.txt").exists()
                passed += 1

            assert TOOL.safe_model("qwen3.5:9b") == "qwen3.5:9b"
            rejected(lambda: TOOL.safe_model("bad model; stop"), "unsupported characters")
            passed += 2

            assert TOOL.safe_ollama_url("http://127.0.0.1:11434/") == "http://127.0.0.1:11434"
            private_host = ".".join(str(part) for part in (192, 168, 1, 20))
            private_url = f"https://{private_host}:11434"
            assert TOOL.safe_ollama_url(private_url) == private_url
            rejected(lambda: TOOL.safe_ollama_url("https://8.8.8.8:11434"), "Public Ollama")
            rejected(lambda: TOOL.safe_ollama_url("https://192.0.2.20:11434"), "Public Ollama")
            credential_url = "http://" + "user" + ":" + "pass" + "@127.0.0.1:11434"
            rejected(lambda: TOOL.safe_ollama_url(credential_url), "without a password")
            rejected(lambda: TOOL.safe_ollama_url("http://ollama.example.test:11434"), "private-network IP")
            passed += 6

            actions = TOOL.configure_tool(
                "aider", target, "qwen3.5:9b", "http://127.0.0.1:11434", False, False
            )
            assert actions and not (target / ".aider.conf.local.yml").exists()
            passed += 1

            TOOL.configure_tool(
                "aider", target, "qwen3.5:9b", "http://127.0.0.1:11434", True, False
            )
            aider = target / ".aider.conf.local.yml"
            assert "auto-commits: false" in aider.read_text(encoding="utf-8")
            passed += 1

            rejected(
                lambda: TOOL.configure_tool(
                    "aider", target, "qwen3.5:9b", "http://127.0.0.1:11434", False, False
                ),
                "already exists",
            )
            TOOL.configure_tool(
                "aider", target, "qwen3.5:9b", "http://127.0.0.1:11434", True, True
            )
            assert (target / ".aider.conf.local.yml.haven42-backup").is_file()
            passed += 2

            TOOL.configure_tool(
                "opencode", target, "qwen3.5:9b", "http://127.0.0.1:11434", True, False
            )
            opencode = json.loads((target / ".opencode.local.json").read_text(encoding="utf-8"))
            assert opencode["provider"]["ollama"]["options"]["baseURL"].endswith("/v1")
            passed += 1

            link = target / ".linked-config"
            try:
                link.symlink_to(target / "missing")
            except OSError:
                pass
            else:
                rejected(lambda: TOOL.ensure_safe_destination(link, target), "symbolic link")
                passed += 1

        with patch.object(TOOL, "PACKAGE_ROOT", package_root):
            rejected(lambda: TOOL.safe_target(str(package_root.parent)), "not the IDE tools package")
        passed += 1

        damaged = package_root / "README.md"
        original = damaged.read_bytes()
        damaged.write_bytes(original + b"damaged\n")
        rejected(lambda: TOOL.verify_package(package_root), "integrity check failed")
        damaged.write_bytes(original)
        TOOL.verify_package(package_root)
        passed += 2

        rejected(lambda: BUILDER.safe_output(str(ROOT / "outside-ide-package")), "inside dist")
        passed += 1

    print(f"Local LLM IDE package tests passed: {passed} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
