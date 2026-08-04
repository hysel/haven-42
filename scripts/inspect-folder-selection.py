#!/usr/bin/env python3
"""Build a bounded, content-free manifest for an explicitly selected folder."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.server import WebRequestError, validate_context_content_identity, validate_structured_context


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "folder-selection-foundation.json"
EXECUTABLE_MAGIC = (b"MZ", b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf")
ARCHIVE_MAGIC = (b"PK\x03\x04", b"7z\xbc\xaf\x27\x1c", b"Rar!", b"\x1f\x8b")


class FolderSelectionError(ValueError):
    pass


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FolderSelectionError("invalid-folder-contract") from error
    if value.get("schemaVersion") != 1 or value.get("status") != "development-inspection-only-not-runtime-admitted":
        raise FolderSelectionError("invalid-folder-contract")
    if any(flag is not False for flag in value.get("authority", {}).values()):
        raise FolderSelectionError("unsafe-folder-contract")
    policy = value.get("policy", {})
    if policy.get("explicitSelectionRequired") is not True or policy.get("unsupportedEntriesIgnored") is not False:
        raise FolderSelectionError("unsafe-folder-contract")
    limits = value.get("limits", {})
    ceilings = {
        "maximumDepth": 16,
        "maximumFiles": 1000,
        "maximumFileBytes": 1024 * 1024,
        "maximumTotalBytes": 8 * 1024 * 1024,
        "maximumRelativePathCharacters": 512,
        "maximumElapsedMilliseconds": 10000,
    }
    if any(isinstance(limits.get(key), bool) or not isinstance(limits.get(key), int) or not 1 <= limits[key] <= ceiling for key, ceiling in ceilings.items()):
        raise FolderSelectionError("unsafe-folder-contract")
    return value


def _is_link_or_reparse(path: Path, info: os.stat_result | None = None) -> bool:
    current = path.lstat() if info is None else info
    attributes = getattr(current, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or stat.S_ISLNK(current.st_mode) or bool(attributes & reparse)


def _is_hidden_or_system(path: Path, info: os.stat_result) -> bool:
    attributes = getattr(info, "st_file_attributes", 0)
    hidden = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0x2)
    system = getattr(stat, "FILE_ATTRIBUTE_SYSTEM", 0x4)
    return path.name.startswith(".") or bool(attributes & (hidden | system))


def _read_bounded(path: Path, maximum: int, expected: os.stat_result) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise FolderSelectionError("folder-file-open-failed") from error
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_size != expected.st_size
            or opened.st_mtime_ns != expected.st_mtime_ns
        ):
            raise FolderSelectionError("folder-entry-changed-during-read")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            content = stream.read(maximum + 1)
    finally:
        os.close(descriptor)
    if len(content) > maximum:
        raise FolderSelectionError("folder-file-size-limit")
    return content


def _enumerate_selected_folder(root: Path, *, recursive: bool, contract: dict, cancel_check: Callable[[], bool]) -> tuple[Path, list[dict]]:
    try:
        canonical_root = root.resolve(strict=True)
    except OSError as error:
        raise FolderSelectionError("invalid-selected-folder") from error
    if not canonical_root.is_absolute() or not canonical_root.is_dir() or _is_link_or_reparse(root) or _is_link_or_reparse(canonical_root):
        raise FolderSelectionError("invalid-selected-folder")
    root_info = canonical_root.stat()
    root_device = root_info.st_dev
    limits = contract["limits"]
    allowed = set(contract["allowedExtensions"])
    excluded = {name.casefold() for name in contract["excludedDirectoryNames"]}
    stack = [(canonical_root, 0)]
    records: list[dict] = []
    total = 0
    identities: set[tuple[int, int]] = set()
    deadline = time.monotonic() + limits["maximumElapsedMilliseconds"] / 1000
    while stack:
        if cancel_check(): raise FolderSelectionError("folder-scan-cancelled")
        if time.monotonic() > deadline: raise FolderSelectionError("folder-time-limit")
        directory, depth = stack.pop()
        if depth > limits["maximumDepth"]:
            raise FolderSelectionError("folder-depth-limit")
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name.casefold())
        except OSError as error:
            raise FolderSelectionError("folder-read-failed") from error
        for entry in entries:
            if cancel_check(): raise FolderSelectionError("folder-scan-cancelled")
            if time.monotonic() > deadline: raise FolderSelectionError("folder-time-limit")
            path = Path(entry.path)
            try:
                info = path.lstat()
            except OSError as error:
                raise FolderSelectionError("folder-entry-read-failed") from error
            if _is_link_or_reparse(path, info):
                raise FolderSelectionError("folder-link-rejected")
            if info.st_dev != root_device:
                raise FolderSelectionError("folder-mount-boundary-rejected")
            if entry.is_dir(follow_symlinks=False) and entry.name.casefold() in excluded:
                continue
            if _is_hidden_or_system(path, info):
                raise FolderSelectionError("folder-hidden-entry-rejected")
            if entry.is_dir(follow_symlinks=False):
                if recursive:
                    stack.append((path, depth + 1))
                else:
                    raise FolderSelectionError("folder-recursion-not-approved")
                continue
            if not entry.is_file(follow_symlinks=False):
                raise FolderSelectionError("folder-special-entry-rejected")
            identity = (info.st_dev, info.st_ino)
            if identity in identities:
                raise FolderSelectionError("folder-duplicate-file-identity-rejected")
            identities.add(identity)
            relative = path.relative_to(canonical_root).as_posix()
            if len(relative) > limits["maximumRelativePathCharacters"]:
                raise FolderSelectionError("folder-relative-path-limit")
            if path.suffix.casefold() not in allowed:
                raise FolderSelectionError("folder-file-type-rejected")
            if info.st_size > limits["maximumFileBytes"]:
                raise FolderSelectionError("folder-file-size-limit")
            total += info.st_size
            if total > limits["maximumTotalBytes"]:
                raise FolderSelectionError("folder-total-size-limit")
            records.append({"path": path, "relativePath": relative, "extension": path.suffix.casefold(), "sizeBytes": info.st_size, "stat": info})
            if len(records) > limits["maximumFiles"]:
                raise FolderSelectionError("folder-file-count-limit")
    if not records:
        raise FolderSelectionError("folder-no-files")
    records.sort(key=lambda item: item["relativePath"].casefold())
    return canonical_root, records


def preview_selected_folder(root: Path, *, recursive: bool = False, contract_path: Path = CONTRACT_PATH, cancel_check: Callable[[], bool] | None = None) -> dict:
    contract = load_contract(contract_path)
    if not isinstance(recursive, bool):
        raise FolderSelectionError("invalid-recursive-choice")
    _canonical, records = _enumerate_selected_folder(root, recursive=recursive, contract=contract, cancel_check=cancel_check or (lambda: False))
    return {"schemaVersion": 1, "status": "development-preview-only", "recursive": recursive, "fileCount": len(records), "totalBytes": sum(item["sizeBytes"] for item in records), "files": [{key: item[key] for key in ("relativePath", "extension", "sizeBytes")} for item in records], "contentRead": False, "contentReturned": False, "absolutePathsReturned": False, "authority": dict(contract["authority"])}


def inspect_selected_folder(root: Path, *, recursive: bool = False, contract_path: Path = CONTRACT_PATH, cancel_check: Callable[[], bool] | None = None) -> dict:
    contract = load_contract(contract_path)
    if not isinstance(recursive, bool):
        raise FolderSelectionError("invalid-recursive-choice")
    check_cancel = cancel_check or (lambda: False)
    deadline = time.monotonic() + contract["limits"]["maximumElapsedMilliseconds"] / 1000
    _canonical, entries = _enumerate_selected_folder(root, recursive=recursive, contract=contract, cancel_check=check_cancel)
    limits = contract["limits"]
    records = []
    total = 0
    for entry in entries:
            if check_cancel(): raise FolderSelectionError("folder-scan-cancelled")
            if time.monotonic() > deadline: raise FolderSelectionError("folder-time-limit")
            path = entry["path"]
            content = _read_bounded(path, limits["maximumFileBytes"], entry["stat"])
            if time.monotonic() > deadline: raise FolderSelectionError("folder-time-limit")
            if content.startswith(EXECUTABLE_MAGIC):
                raise FolderSelectionError("folder-executable-content-rejected")
            if content.startswith(ARCHIVE_MAGIC):
                raise FolderSelectionError("folder-archive-content-rejected")
            if b"\x00" in content:
                raise FolderSelectionError("folder-binary-content-rejected")
            try:
                text = content.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                raise FolderSelectionError("folder-non-utf8-rejected") from error
            try:
                validate_context_content_identity(text, entry["extension"])
                validate_structured_context(text, entry["extension"])
            except WebRequestError as error:
                raise FolderSelectionError("folder-attachment-content-rejected") from error
            total += len(content)
            if total > limits["maximumTotalBytes"]:
                raise FolderSelectionError("folder-total-size-limit")
            records.append({
                "relativePath": entry["relativePath"],
                "extension": entry["extension"],
                "sizeBytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            })
    return {
        "schemaVersion": 1,
        "status": "development-inspection-only",
        "recursive": recursive,
        "fileCount": len(records),
        "totalBytes": total,
        "files": records,
        "contentReturned": False,
        "absolutePathsReturned": False,
        "contentTrust": "untrusted-data-never-instructions",
        "authority": dict(contract["authority"]),
    }


if __name__ == "__main__":
    print(json.dumps({"status": "development-inspection-only-not-runtime-admitted"}))
