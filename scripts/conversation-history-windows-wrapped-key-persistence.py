#!/usr/bin/env python3
"""Temporary synthetic wrapped-key persistence proof for Windows only."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "conversation-history-windows-wrapped-key-persistence.json"
KEY_PROTECTION_PATH = ROOT / "scripts" / "conversation-history-windows-key-protection.py"


class WrappedKeyPersistenceError(ValueError):
    pass


def _load_key_protection():
    spec = importlib.util.spec_from_file_location("history_dpapi_for_persistence", KEY_PROTECTION_PATH)
    if spec is None or spec.loader is None:
        raise WrappedKeyPersistenceError("key-protection-module-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


KEY_PROTECTION = _load_key_protection()


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise WrappedKeyPersistenceError("invalid-persistence-contract") from error
    storage = value.get("storage", {})
    recovery = value.get("recovery", {})
    authority = value.get("authority", {})
    if (
        value.get("schemaVersion") != 1
        or value.get("status") != "development-synthetic-temporary-only"
        or value.get("platform") != "windows"
        or storage != {
            "testOwnedTemporaryDirectoryOnly": True,
            "callerPathAllowed": False,
            "directoryMustStartEmpty": True,
            "symlinksOrReparsePointsAllowed": False,
            "wrappedKeyFilename": "history-key.dpapi",
            "temporaryFilename": "history-key.dpapi.tmp",
            "maximumWrappedKeyBytes": 16_384,
            "exclusiveTemporaryCreateRequired": True,
            "flushBeforeRenameRequired": True,
            "atomicNoReplaceRenameRequired": True,
            "productionAclAdmissionRequired": True,
            "productionAclAdmissionProven": False,
            "cleanupRequired": True,
        }
        or set(recovery) != {
            "missingKeyFailsClosed", "emptyKeyFailsClosed", "oversizedKeyFailsClosed",
            "tamperedKeyFailsClosed", "preexistingKeyNeverOverwritten",
            "automaticResetAllowed", "plaintextFallbackAllowed",
        }
        or any(recovery[name] is not True for name in (
            "missingKeyFailsClosed", "emptyKeyFailsClosed", "oversizedKeyFailsClosed",
            "tamperedKeyFailsClosed", "preexistingKeyNeverOverwritten",
        ))
        or recovery.get("automaticResetAllowed") is not False
        or recovery.get("plaintextFallbackAllowed") is not False
        or authority.get("syntheticTemporaryValidationAllowed") is not True
        or any(value is not False for name, value in authority.items() if name != "syntheticTemporaryValidationAllowed")
    ):
        raise WrappedKeyPersistenceError("unsafe-persistence-contract")
    return value


def _is_link_or_reparse(path: Path) -> bool:
    info = path.lstat()
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or stat.S_ISLNK(info.st_mode) or bool(attributes & reparse)


def _validate_empty_directory(directory: Path) -> None:
    if (
        sys.platform != "win32"
        or not directory.is_absolute()
        or not directory.is_dir()
        or _is_link_or_reparse(directory)
        or any(directory.iterdir())
    ):
        raise WrappedKeyPersistenceError("unsafe-temporary-directory")


def _paths(directory: Path, contract: dict) -> tuple[Path, Path]:
    return (
        directory / contract["storage"]["wrappedKeyFilename"],
        directory / contract["storage"]["temporaryFilename"],
    )


def write_wrapped_key_once(
    directory: Path,
    wrapped: bytes,
    contract_path: Path = CONTRACT_PATH,
    *,
    _before_rename_for_test=None,
) -> Path:
    contract = load_contract(contract_path)
    _validate_empty_directory(directory)
    maximum = contract["storage"]["maximumWrappedKeyBytes"]
    if not isinstance(wrapped, bytes) or not 0 < len(wrapped) <= maximum:
        raise WrappedKeyPersistenceError("invalid-wrapped-key")
    destination, temporary = _paths(directory, contract)
    if destination.exists() or temporary.exists():
        raise WrappedKeyPersistenceError("wrapped-key-already-exists")
    created = False
    try:
        with temporary.open("xb") as stream:
            created = True
            stream.write(wrapped)
            stream.flush()
            os.fsync(stream.fileno())
        if _before_rename_for_test is not None:
            _before_rename_for_test(destination)
        # On Windows os.rename does not replace an existing destination. This
        # preserves the fail-closed no-overwrite contract without a check/use
        # replacement race.
        os.rename(temporary, destination)
        created = False
        return destination
    except FileExistsError as error:
        raise WrappedKeyPersistenceError("wrapped-key-already-exists") from error
    except OSError as error:
        raise WrappedKeyPersistenceError("wrapped-key-atomic-write-failed") from error
    finally:
        if created and temporary.exists() and not _is_link_or_reparse(temporary):
            temporary.unlink()


def recover_wrapped_key(directory: Path, contract_path: Path = CONTRACT_PATH) -> bytearray:
    contract = load_contract(contract_path)
    if sys.platform != "win32" or not directory.is_absolute() or not directory.is_dir() or _is_link_or_reparse(directory):
        raise WrappedKeyPersistenceError("unsafe-temporary-directory")
    destination, temporary = _paths(directory, contract)
    if temporary.exists():
        raise WrappedKeyPersistenceError("interrupted-wrapped-key-write")
    if not destination.exists():
        raise WrappedKeyPersistenceError("wrapped-key-missing")
    if _is_link_or_reparse(destination) or not destination.is_file():
        raise WrappedKeyPersistenceError("unsafe-wrapped-key-file")
    size = destination.stat().st_size
    if not 0 < size <= contract["storage"]["maximumWrappedKeyBytes"]:
        raise WrappedKeyPersistenceError("invalid-wrapped-key-file")
    try:
        wrapped = destination.read_bytes()
    except OSError as error:
        raise WrappedKeyPersistenceError("wrapped-key-read-failed") from error
    try:
        return KEY_PROTECTION.unprotect_key(wrapped)
    except KEY_PROTECTION.KeyProtectionError as error:
        raise WrappedKeyPersistenceError("wrapped-key-recovery-failed") from error


def _remove_test_file(path: Path) -> None:
    if path.exists():
        if _is_link_or_reparse(path) or not path.is_file():
            raise WrappedKeyPersistenceError("unsafe-test-cleanup-target")
        path.unlink()


def validate_synthetic_temporary_persistence() -> dict:
    contract = load_contract()
    temporary_path: Path | None = None
    wrapped_size = 0
    with tempfile.TemporaryDirectory(prefix="haven42-history-wrapped-key-") as temporary_name:
        directory = Path(temporary_name).resolve()
        temporary_path = directory
        _validate_empty_directory(directory)
        key = bytearray(os.urandom(32))
        expected_digest = hashlib.sha256(key).digest()
        wrapped = KEY_PROTECTION.protect_key(key)
        if any(key):
            raise WrappedKeyPersistenceError("plaintext-key-not-wiped")
        wrapped_size = len(wrapped)
        destination = write_wrapped_key_once(directory, wrapped)
        original_digest = hashlib.sha256(destination.read_bytes()).digest()
        recovered = recover_wrapped_key(directory)
        try:
            if hashlib.sha256(recovered).digest() != expected_digest:
                raise WrappedKeyPersistenceError("recovered-key-mismatch")
        finally:
            KEY_PROTECTION.wipe(recovered)
        try:
            write_wrapped_key_once(directory, wrapped)
        except WrappedKeyPersistenceError as error:
            if str(error) != "unsafe-temporary-directory":
                raise
        else:
            raise WrappedKeyPersistenceError("preexisting-key-was-overwritten")
        if hashlib.sha256(destination.read_bytes()).digest() != original_digest:
            raise WrappedKeyPersistenceError("preexisting-key-was-modified")

        tampered = bytearray(destination.read_bytes())
        tampered[-1] ^= 1
        destination.write_bytes(tampered)
        tampered_digest = hashlib.sha256(destination.read_bytes()).digest()
        try:
            recover_wrapped_key(directory)
        except WrappedKeyPersistenceError as error:
            if str(error) != "wrapped-key-recovery-failed":
                raise
        else:
            raise WrappedKeyPersistenceError("tampered-key-was-accepted")
        if hashlib.sha256(destination.read_bytes()).digest() != tampered_digest:
            raise WrappedKeyPersistenceError("tampered-key-was-reset")
        _remove_test_file(destination)
        try:
            recover_wrapped_key(directory)
        except WrappedKeyPersistenceError as error:
            if str(error) != "wrapped-key-missing":
                raise
        else:
            raise WrappedKeyPersistenceError("missing-key-was-regenerated")
        if any(directory.iterdir()):
            raise WrappedKeyPersistenceError("temporary-residue-detected")
    if temporary_path is None or temporary_path.exists():
        raise WrappedKeyPersistenceError("temporary-directory-cleanup-failed")
    return {
        "schemaVersion": 1,
        "status": "windows-synthetic-wrapped-key-temporary-persistence-passed",
        "wrappedBytes": wrapped_size,
        "checks": {
            "atomicNoReplaceWrite": True,
            "recoverable": True,
            "tamperFailsClosed": True,
            "missingKeyFailsClosed": True,
            "automaticResetAbsent": True,
            "residueFree": True,
        },
        "authority": dict(contract["authority"]),
    }


if __name__ == "__main__":
    try:
        print(json.dumps(validate_synthetic_temporary_persistence(), sort_keys=True))
    except WrappedKeyPersistenceError as error:
        print(json.dumps({"status": "refused", "code": str(error)}, sort_keys=True))
        raise SystemExit(1)
