#!/usr/bin/env python3
"""Fail-closed portable runtime primitives for Haven 42 Alpha 2 on Linux.

Importing this module has no process, network, or filesystem effects. Archive
inspection and extraction require an exact registry record supplied by the
trusted engine; renderer input never supplies paths, URLs, commands, or modes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
from typing import Any
import unicodedata

try:
    from compression import zstd as _stdlib_zstd
except ImportError:  # Python before 3.14 uses the fixed system-tool fallback.
    _stdlib_zstd = None


SOURCE_ROOT = Path(__file__).resolve().parent.parent
ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
REGISTRY_PATH = ROOT / "config" / "linux-alpha-component-registry.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_COMPONENT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_METADATA_BYTES = 2 * 1024 * 1024
COPY_CHUNK_BYTES = 1024 * 1024
MAX_PATH_BYTES = 512
MAX_LINK_DEPTH = 16
ZSTD_CANDIDATES = (Path("/usr/bin/zstd"), Path("/bin/zstd"))


class LinuxRuntimeError(ValueError):
    """A portable Linux runtime operation failed closed."""


def _read_json(path: Path, label: str) -> Any:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_METADATA_BYTES:
            raise LinuxRuntimeError(f"unsafe-{label}")
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LinuxRuntimeError(f"invalid-{label}") from error


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    value = _read_json(path, "linux-component-registry")
    if (
        not isinstance(value, dict)
        or set(value) != {
            "schemaVersion", "registryId", "defaultDecision", "runtimeAdmission",
            "components", "driverPolicy",
        }
        or value.get("schemaVersion") != 1
        or value.get("registryId") != "haven42.linux-alpha.components"
        or value.get("defaultDecision") != "deny"
        or not isinstance(value.get("components"), list)
        or len(value["components"]) != 2
    ):
        raise LinuxRuntimeError("invalid-linux-component-registry")
    identifiers: set[str] = set()
    for component in value["components"]:
        if (
            not isinstance(component, dict)
            or not SAFE_COMPONENT_ID.fullmatch(str(component.get("id", "")))
            or component["id"] in identifiers
            or not HEX64.fullmatch(str(component.get("sha256", "")))
            or not isinstance(component.get("byteLength"), int)
            or isinstance(component.get("byteLength"), bool)
            or not 1 <= component["byteLength"] <= 4 * 1024**3
            or component.get("archiveFormat") != "tar.zst"
            or not str(component.get("sourceUrl", "")).startswith(
                "https://github.com/ollama/ollama/releases/download/v0.32.5/"
            )
        ):
            raise LinuxRuntimeError("invalid-linux-component-record")
        identifiers.add(component["id"])
    core = next(item for item in value["components"] if item["id"] == "ollama-linux-core")
    required_core = {
        "expandedByteLength", "maximumArchiveMembers", "expectedRegularFiles",
        "expectedDirectories", "expectedInternalLinks", "executableRelativePath",
        "archiveLinkPolicy",
    }
    if (
        not required_core.issubset(core)
        or core.get("managedInstallationAllowed") is not True
        or core.get("archiveLinkPolicy")
        != "materialize-validated-relative-file-targets"
        or core.get("executableRelativePath") != "bin/ollama"
    ):
        raise LinuxRuntimeError("invalid-linux-core-record")
    rocm = next(item for item in value["components"] if item["id"] == "ollama-linux-amd-rocm")
    if rocm.get("managedInstallationAllowed") is not False:
        raise LinuxRuntimeError("unreviewed-rocm-component-admitted")
    return value


def component_record(component_id: str, path: Path = REGISTRY_PATH) -> dict[str, Any]:
    if not isinstance(component_id, str) or not SAFE_COMPONENT_ID.fullmatch(component_id):
        raise LinuxRuntimeError("invalid-component-id")
    matches = [item for item in load_registry(path)["components"] if item["id"] == component_id]
    if len(matches) != 1:
        raise LinuxRuntimeError("unregistered-component")
    return matches[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        if path.is_symlink() or not path.is_file():
            raise LinuxRuntimeError("unsafe-component-archive")
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(COPY_CHUNK_BYTES), b""):
                digest.update(block)
    except OSError as error:
        raise LinuxRuntimeError("component-archive-read-failed") from error
    return digest.hexdigest()


def verify_registered_archive(archive: Path, component: dict[str, Any]) -> dict[str, Any]:
    try:
        size = archive.stat().st_size
    except OSError as error:
        raise LinuxRuntimeError("component-archive-read-failed") from error
    if (
        archive.is_symlink()
        or not archive.is_file()
        or size != component["byteLength"]
        or sha256_file(archive) != component["sha256"]
    ):
        raise LinuxRuntimeError("component-archive-integrity-failed")
    return {"sizeBytes": size, "sha256": component["sha256"], "verified": True}


def _member_name(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise LinuxRuntimeError("invalid-archive-member-name")
    if len(value.encode("utf-8")) > MAX_PATH_BYTES:
        raise LinuxRuntimeError("archive-member-name-too-long")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise LinuxRuntimeError("unsafe-archive-member-path")
    normalized = "/".join(path.parts)
    if unicodedata.normalize("NFC", normalized) != normalized:
        raise LinuxRuntimeError("noncanonical-archive-member-name")
    return normalized


def _resolved_link_name(name: str, target: str) -> str:
    if not isinstance(target, str) or not target or "\x00" in target:
        raise LinuxRuntimeError("invalid-archive-link-target")
    link = PurePosixPath(target)
    if link.is_absolute():
        raise LinuxRuntimeError("unsafe-archive-link-target")
    combined = PurePosixPath(name).parent / link
    parts: list[str] = []
    for part in combined.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                raise LinuxRuntimeError("unsafe-archive-link-target")
            parts.pop()
        else:
            parts.append(part)
    if not parts:
        raise LinuxRuntimeError("unsafe-archive-link-target")
    return _member_name("/".join(parts))


class _ProcessStream:
    """Minimal read stream that verifies its fixed decompressor on close."""

    def __init__(self, process: subprocess.Popen[bytes]):
        if process.stdout is None:
            raise LinuxRuntimeError("zstd-process-stream-unavailable")
        self.process = process
        self.stdout = process.stdout

    def read(self, size: int = -1) -> bytes:
        return self.stdout.read(size)

    def close(self) -> None:
        self.stdout.close()
        try:
            result = self.process.wait(timeout=10)
        except subprocess.TimeoutExpired as error:
            self.process.kill()
            self.process.wait(timeout=5)
            raise LinuxRuntimeError("zstd-process-timeout") from error
        if result != 0:
            raise LinuxRuntimeError("zstd-process-failed")


def _trusted_zstd() -> Path:
    for candidate in ZSTD_CANDIDATES:
        try:
            details = candidate.lstat()
        except OSError:
            continue
        if (
            stat.S_ISREG(details.st_mode)
            and not candidate.is_symlink()
            and details.st_uid == 0
            and details.st_mode & 0o022 == 0
            and details.st_mode & 0o111 != 0
        ):
            return candidate
    raise LinuxRuntimeError("trusted-zstd-unavailable")


def _open_archive(archive: Path):
    stream = None
    try:
        if _stdlib_zstd is not None:
            stream = _stdlib_zstd.open(archive, "rb")
        else:
            executable = _trusted_zstd()
            process = subprocess.Popen(
                [str(executable), "--decompress", "--stdout", "--quiet", "--", str(archive)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                shell=False,
                close_fds=True,
                env={"PATH": "/usr/bin:/bin", "LANG": "C"},
            )
            stream = _ProcessStream(process)
        value = tarfile.open(fileobj=stream, mode="r|")
    except (OSError, subprocess.SubprocessError, tarfile.TarError) as error:
        if stream is not None:
            try:
                stream.close()
            except (OSError, LinuxRuntimeError):
                pass
        raise LinuxRuntimeError("invalid-component-archive") from error
    return stream, value


def inspect_registered_archive(
    archive: Path, component: dict[str, Any]
) -> dict[str, Any]:
    verify_registered_archive(archive, component)
    records: dict[str, dict[str, Any]] = {}
    folded: set[str] = set()
    regular_files = directories = internal_links = expanded = 0
    stream, bundle = _open_archive(archive)
    try:
        for index, member in enumerate(bundle, start=1):
            if index > component["maximumArchiveMembers"]:
                raise LinuxRuntimeError("archive-member-limit")
            name = _member_name(member.name)
            collision = unicodedata.normalize("NFC", name).casefold()
            if name in records or collision in folded:
                raise LinuxRuntimeError("archive-member-collision")
            folded.add(collision)
            if member.isdir():
                directories += 1
                record = {"kind": "directory", "size": 0, "mode": member.mode}
            elif member.isfile():
                if member.size < 0:
                    raise LinuxRuntimeError("invalid-archive-member-size")
                expanded += member.size
                if expanded > component["expandedByteLength"]:
                    raise LinuxRuntimeError("archive-expansion-limit")
                regular_files += 1
                record = {"kind": "file", "size": member.size, "mode": member.mode}
            elif member.issym():
                internal_links += 1
                record = {
                    "kind": "internal-link", "size": 0, "mode": member.mode,
                    "target": _resolved_link_name(name, member.linkname),
                }
            else:
                raise LinuxRuntimeError("unsupported-archive-member-type")
            records[name] = record
    except (OSError, tarfile.TarError) as error:
        raise LinuxRuntimeError("invalid-component-archive") from error
    finally:
        bundle.close()
        stream.close()
    expected = (
        regular_files == component["expectedRegularFiles"]
        and directories == component["expectedDirectories"]
        and internal_links == component["expectedInternalLinks"]
        and expanded == component["expandedByteLength"]
    )
    if not expected:
        raise LinuxRuntimeError("archive-inventory-mismatch")
    for name, record in records.items():
        if record["kind"] != "internal-link":
            continue
        visited = {name}
        target = record["target"]
        for _ in range(MAX_LINK_DEPTH):
            target_record = records.get(target)
            if target_record is None or target_record["kind"] == "directory":
                raise LinuxRuntimeError("archive-link-target-missing")
            if target_record["kind"] == "file":
                break
            if target in visited:
                raise LinuxRuntimeError("archive-link-cycle")
            visited.add(target)
            target = target_record["target"]
        else:
            raise LinuxRuntimeError("archive-link-depth-limit")
        record["resolvedTarget"] = target
    executable = records.get(component["executableRelativePath"])
    if executable is None or executable["kind"] != "file" or not executable["mode"] & 0o111:
        raise LinuxRuntimeError("runtime-executable-missing")
    return {
        "records": records,
        "regularFiles": regular_files,
        "directories": directories,
        "internalLinks": internal_links,
        "expandedBytes": expanded,
    }


def _assert_destination(destination: Path) -> Path:
    absolute = destination.absolute()
    if absolute.exists() or absolute.is_symlink():
        raise LinuxRuntimeError("runtime-destination-exists")
    cursor = absolute.parent
    while True:
        if cursor.is_symlink():
            raise LinuxRuntimeError("unsafe-runtime-destination")
        if cursor.exists():
            if not cursor.is_dir():
                raise LinuxRuntimeError("unsafe-runtime-destination")
            break
        if cursor.parent == cursor:
            raise LinuxRuntimeError("runtime-parent-missing")
        cursor = cursor.parent
    return absolute


def _safe_output(root: Path, name: str) -> Path:
    path = root.joinpath(*PurePosixPath(name).parts)
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise LinuxRuntimeError("archive-output-escaped") from error
    return path


def extract_registered_archive(
    archive: Path, destination: Path, component: dict[str, Any]
) -> dict[str, Any]:
    inventory = inspect_registered_archive(archive, component)
    destination = _assert_destination(destination)
    staging = destination.with_name(f".{destination.name}.extracting")
    if staging.exists() or staging.is_symlink():
        raise LinuxRuntimeError("runtime-staging-exists")
    staging.mkdir(mode=0o700)
    try:
        records = inventory["records"]
        for name, record in sorted(records.items()):
            if record["kind"] == "directory":
                _safe_output(staging, name).mkdir(parents=True, exist_ok=False, mode=0o700)
        stream, bundle = _open_archive(archive)
        try:
            for member in bundle:
                name = _member_name(member.name)
                record = records[name]
                if record["kind"] != "file":
                    continue
                output = _safe_output(staging, name)
                output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                source = bundle.extractfile(member)
                if source is None:
                    raise LinuxRuntimeError("archive-member-read-failed")
                written = 0
                with output.open("xb") as handle:
                    while True:
                        block = source.read(COPY_CHUNK_BYTES)
                        if not block:
                            break
                        written += len(block)
                        if written > record["size"]:
                            raise LinuxRuntimeError("archive-member-size-mismatch")
                        handle.write(block)
                if written != record["size"]:
                    raise LinuxRuntimeError("archive-member-size-mismatch")
                output.chmod(0o500 if record["mode"] & 0o111 else 0o400)
        finally:
            bundle.close()
            stream.close()
        for name, record in sorted(records.items()):
            if record["kind"] != "internal-link":
                continue
            target = _safe_output(staging, record["resolvedTarget"])
            output = _safe_output(staging, name)
            if not target.is_file() or target.is_symlink():
                raise LinuxRuntimeError("archive-link-target-missing")
            output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with target.open("rb") as source, output.open("xb") as handle:
                shutil.copyfileobj(source, handle, COPY_CHUNK_BYTES)
            output.chmod(stat.S_IMODE(target.stat().st_mode))
        for path in staging.rglob("*"):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise LinuxRuntimeError("unsafe-extracted-runtime-entry")
        staging.rename(destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "componentId": component["id"],
        "destination": destination,
        "regularFiles": inventory["regularFiles"] + inventory["internalLinks"],
        "directories": inventory["directories"],
        "linkFree": True,
    }


def registered_component(component_id: str, path: Path = REGISTRY_PATH) -> dict[str, Any]:
    """Return one exact managed component or fail closed."""
    if not SAFE_COMPONENT_ID.fullmatch(component_id):
        raise LinuxRuntimeError("invalid-linux-component-id")
    registry = load_registry(path)
    matches = [item for item in registry["components"] if item["id"] == component_id]
    if len(matches) != 1 or matches[0].get("managedInstallationAllowed") is not True:
        raise LinuxRuntimeError("linux-component-not-managed")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component-id", required=True)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = extract_registered_archive(
            args.archive,
            args.destination,
            registered_component(args.component_id),
        )
        # Local paths stay out of stdout so captured setup logs remain portable.
        result.pop("destination", None)
        print(json.dumps(result, indent=2, sort_keys=True))
    except LinuxRuntimeError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
