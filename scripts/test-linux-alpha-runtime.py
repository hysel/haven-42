#!/usr/bin/env python3
"""Hostile tests for the link-free Linux Alpha runtime extractor."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
from unittest import mock

try:
    from compression import zstd as _stdlib_zstd
except ImportError:
    _stdlib_zstd = None


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "linux_alpha_runtime", ROOT / "scripts/linux_alpha_runtime.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


if _stdlib_zstd is None and os.name != "posix":
    class _TestArchiveCodec:
        """Exercise archive policy where no safe native zstd exists.

        Production extraction still fails closed without its reviewed zstd
        backend. This test-only passthrough keeps the platform-neutral archive
        traversal and link checks runnable on Windows CI.
        """

        @staticmethod
        def compress(value: bytes) -> bytes:
            return value

        @staticmethod
        def open(path: Path, mode: str):
            assert mode == "rb"
            return path.open(mode)

    _stdlib_zstd = _TestArchiveCodec()
    MODULE._stdlib_zstd = _stdlib_zstd


def make_archive(path: Path, members: list[tuple[str, str, bytes | str]]) -> dict:
    raw = io.BytesIO()
    expanded = files = directories = links = 0
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for kind, name, value in members:
            info = tarfile.TarInfo(name)
            if kind == "dir":
                info.type = tarfile.DIRTYPE
                info.mode = 0o755
                directories += 1
                archive.addfile(info)
            elif kind == "file":
                assert isinstance(value, bytes)
                info.size = len(value)
                info.mode = 0o755 if name == "bin/ollama" else 0o644
                files += 1
                expanded += len(value)
                archive.addfile(info, io.BytesIO(value))
            elif kind == "link":
                assert isinstance(value, str)
                info.type = tarfile.SYMTYPE
                info.linkname = value
                info.mode = 0o777
                links += 1
                archive.addfile(info)
            elif kind == "hardlink":
                assert isinstance(value, str)
                info.type = tarfile.LNKTYPE
                info.linkname = value
                archive.addfile(info)
            else:
                info.type = tarfile.FIFOTYPE
                archive.addfile(info)
    if _stdlib_zstd is not None:
        encoded = _stdlib_zstd.compress(raw.getvalue())
    else:
        executable = MODULE._trusted_zstd()
        encoded = subprocess.run(
            [str(executable), "--compress", "--stdout", "--quiet"],
            input=raw.getvalue(), capture_output=True, check=True,
            env={"PATH": "/usr/bin:/bin", "LANG": "C"},
        ).stdout
    path.write_bytes(encoded)
    return {
        "id": "ollama-linux-core",
        "byteLength": len(encoded),
        "expandedByteLength": expanded,
        "maximumArchiveMembers": 16,
        "expectedRegularFiles": files,
        "expectedDirectories": directories,
        "expectedInternalLinks": links,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "executableRelativePath": "bin/ollama",
    }


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.LinuxRuntimeError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError(f"Expected {code}")


def main() -> None:
    MODULE.load_registry()
    with tempfile.TemporaryDirectory() as directory:
        # macOS exposes /var through /private/var. Canonicalize the test root
        # so the Linux extractor's intentional ancestor-symlink rejection is
        # tested against the actual directory rather than that host alias.
        root = Path(directory).resolve()
        archive = root / "runtime.tar.zst"
        component = make_archive(
            archive,
            [
                ("dir", "bin", b""),
                ("file", "bin/ollama", b"runtime"),
                ("dir", "lib", b""),
                ("file", "lib/libreal.so.1", b"library"),
                ("link", "lib/libreal.so", "libreal.so.1"),
            ],
        )
        inspected = MODULE.inspect_registered_archive(archive, component)
        assert inspected["internalLinks"] == 1
        output = root / "runtime"
        result = MODULE.extract_registered_archive(archive, output, component)
        assert result["linkFree"] is True
        assert (output / "bin/ollama").read_bytes() == b"runtime"
        assert (output / "lib/libreal.so").read_bytes() == b"library"
        assert not any(path.is_symlink() for path in output.rglob("*"))
        if os.name == "posix":
            assert (output / "bin/ollama").stat().st_mode & 0o777 == 0o500
            assert (output / "lib/libreal.so").stat().st_mode & 0o777 == 0o400

        nested_output = root / "new-parent" / "nested" / "runtime"
        nested_result = MODULE.extract_registered_archive(
            archive, nested_output, component,
        )
        assert nested_result["linkFree"] is True
        assert (nested_output / "bin/ollama").read_bytes() == b"runtime"

        bad_hash = dict(component, sha256="0" * 64)
        refused(
            lambda: MODULE.inspect_registered_archive(archive, bad_hash),
            "component-archive-integrity-failed",
        )
        refused(
            lambda: MODULE.extract_registered_archive(archive, output, component),
            "runtime-destination-exists",
        )

        hostile_cases = [
            ([('file', '../escape', b'x'), ('file', 'bin/ollama', b'x')], "unsafe-archive-member-path"),
            ([('file', '/escape', b'x'), ('file', 'bin/ollama', b'x')], "unsafe-archive-member-path"),
            ([('file', 'bin/ollama', b'x'), ('hardlink', 'bin/other', 'bin/ollama')], "unsupported-archive-member-type"),
            ([('file', 'bin/ollama', b'x'), ('other', 'pipe', b'')], "unsupported-archive-member-type"),
            ([('file', 'bin/ollama', b'x'), ('link', 'lib/x', '../../escape')], "unsafe-archive-link-target"),
            ([('file', 'bin/ollama', b'x'), ('link', 'lib/x', 'missing')], "archive-link-target-missing"),
            ([('file', 'bin/ollama', b'x'), ('link', 'a', 'b'), ('link', 'b', 'a')], "archive-link-cycle"),
            ([('file', 'bin/ollama', b'x'), ('file', 'BIN/OLLAMA', b'y')], "archive-member-collision"),
        ]
        for number, (members, expected) in enumerate(hostile_cases):
            candidate = root / f"hostile-{number}.tar.zst"
            spec = make_archive(candidate, members)
            refused(lambda c=candidate, s=spec: MODULE.inspect_registered_archive(c, s), expected)
        registry_path = ROOT / "config/linux-alpha-component-registry.json"
        assert MODULE.registered_component("ollama-linux-core", registry_path)["id"] == "ollama-linux-core"
        refused(
            lambda: MODULE.registered_component("ollama-linux-amd-rocm", registry_path),
            "linux-component-not-managed",
        )
        refused(
            lambda: MODULE.registered_component("../bad", registry_path),
            "invalid-linux-component-id",
        )

        class ClosingStream:
            closed = False

            def close(self) -> None:
                self.closed = True

        stream = ClosingStream()
        decompressor = mock.Mock()
        decompressor.open.return_value = stream
        with (
            mock.patch.object(MODULE, "_stdlib_zstd", decompressor),
            mock.patch.object(MODULE.tarfile, "open", side_effect=tarfile.ReadError()),
        ):
            refused(
                lambda: MODULE._open_archive(root / "invalid.tar.zst"),
                "invalid-component-archive",
            )
        assert stream.closed is True
    print("Linux Alpha runtime extractor passed 23 safety and behavior checks.")


if __name__ == "__main__":
    main()
