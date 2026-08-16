#!/usr/bin/env python3
"""Windows current-user DPAPI proof for synthetic conversation-history keys."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "conversation-history-windows-key-protection.json"
CRYPTPROTECT_UI_FORBIDDEN = 0x1


class KeyProtectionError(ValueError):
    pass


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise KeyProtectionError("invalid-key-protection-contract") from error
    mechanism = value.get("mechanism", {})
    memory = value.get("memory", {})
    authority = value.get("authority", {})
    if (
        value.get("schemaVersion") != 1
        or value.get("status") != "development-synthetic-key-only"
        or value.get("platform") != "windows"
        or mechanism != {
            "provider": "windows-dpapi-current-user",
            "cryptProtectLocalMachineAllowed": False,
            "uiAllowed": False,
            "optionalEntropyRequired": True,
            "entropyContext": "haven42.conversation-history.database-key.v1",
            "databaseKeyBytes": 32,
            "plaintextFallbackAllowed": False,
            "automaticResetOnFailureAllowed": False,
        }
        or memory != {
            "mutablePlaintextBuffersRequired": True,
            "plaintextBufferWipeRequired": True,
            "nativeOutputBufferWipeRequired": True,
        }
        or authority.get("syntheticDevelopmentValidationAllowed") is not True
        or any(
            authority.get(name) is not False
            for name in (
                "runtimeRouteAllowed", "uiControlAllowed", "userContentAllowed",
                "databaseOpenAllowed", "databaseCreateAllowed",
                "persistentKeyWriteAllowed", "packageAdmissionAllowed",
                "productionUseAllowed",
            )
        )
    ):
        raise KeyProtectionError("unsafe-key-protection-contract")
    return value


def wipe(value: bytearray) -> None:
    if not isinstance(value, bytearray):
        raise KeyProtectionError("mutable-buffer-required")
    if value:
        ctypes.memset((ctypes.c_ubyte * len(value)).from_buffer(value), 0, len(value))


def _blob(value: bytearray) -> tuple[DATA_BLOB, object]:
    if not isinstance(value, bytearray) or not value:
        raise KeyProtectionError("mutable-buffer-required")
    buffer = (ctypes.c_ubyte * len(value)).from_buffer(value)
    return DATA_BLOB(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


def _libraries():
    if sys.platform != "win32":
        raise KeyProtectionError("windows-dpapi-unavailable")
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), wintypes.LPCWSTR, ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(DATA_BLOB), ctypes.c_void_p, ctypes.c_void_p,
        wintypes.DWORD, ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    return crypt32, kernel32


def _entropy(contract: dict) -> bytearray:
    return bytearray(contract["mechanism"]["entropyContext"].encode("utf-8"))


def _copy_and_free(output: DATA_BLOB, kernel32, *, mutable: bool) -> bytes | bytearray:
    if not output.pbData or output.cbData <= 0:
        raise KeyProtectionError("dpapi-empty-output")
    try:
        if mutable:
            result = bytearray(output.cbData)
            target = (ctypes.c_ubyte * len(result)).from_buffer(result)
            ctypes.memmove(target, output.pbData, output.cbData)
            return result
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.memset(output.pbData, 0, output.cbData)
        kernel32.LocalFree(output.pbData)


def protect_key(key: bytearray, contract_path: Path = CONTRACT_PATH) -> bytes:
    contract = load_contract(contract_path)
    if not isinstance(key, bytearray) or len(key) != contract["mechanism"]["databaseKeyBytes"]:
        raise KeyProtectionError("invalid-database-key")
    entropy = _entropy(contract)
    try:
        crypt32, kernel32 = _libraries()
        source, source_buffer = _blob(key)
        entropy_blob, entropy_buffer = _blob(entropy)
        output = DATA_BLOB()
        if not crypt32.CryptProtectData(
            ctypes.byref(source), "Haven 42 conversation history key",
            ctypes.byref(entropy_blob), None, None, CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(output),
        ):
            raise KeyProtectionError(f"dpapi-protect-failed-{ctypes.get_last_error()}")
        del source_buffer, entropy_buffer
        return _copy_and_free(output, kernel32, mutable=False)
    finally:
        wipe(key)
        wipe(entropy)


def unprotect_key(wrapped: bytes, contract_path: Path = CONTRACT_PATH) -> bytearray:
    contract = load_contract(contract_path)
    if not isinstance(wrapped, bytes) or not wrapped or len(wrapped) > 16_384:
        raise KeyProtectionError("invalid-wrapped-key")
    wrapped_buffer = bytearray(wrapped)
    entropy = _entropy(contract)
    try:
        crypt32, kernel32 = _libraries()
        source, source_buffer = _blob(wrapped_buffer)
        entropy_blob, entropy_buffer = _blob(entropy)
        output = DATA_BLOB()
        if not crypt32.CryptUnprotectData(
            ctypes.byref(source), None, ctypes.byref(entropy_blob), None, None,
            CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(output),
        ):
            raise KeyProtectionError(f"dpapi-unprotect-failed-{ctypes.get_last_error()}")
        del source_buffer, entropy_buffer
        plaintext = _copy_and_free(output, kernel32, mutable=True)
        if not isinstance(plaintext, bytearray):
            raise KeyProtectionError("mutable-plaintext-copy-required")
        if len(plaintext) != contract["mechanism"]["databaseKeyBytes"]:
            wipe(plaintext)
            raise KeyProtectionError("invalid-unwrapped-key")
        return plaintext
    finally:
        wipe(wrapped_buffer)
        wipe(entropy)


def validate_synthetic_round_trip() -> dict:
    key = bytearray(os.urandom(load_contract()["mechanism"]["databaseKeyBytes"]))
    expected_digest = hashlib.sha256(key).digest()
    wrapped = protect_key(key)
    if any(key):
        raise KeyProtectionError("key-wipe-or-wrapping-failed")
    recovered = unprotect_key(wrapped)
    try:
        if hashlib.sha256(recovered).digest() != expected_digest:
            raise KeyProtectionError("key-round-trip-failed")
    finally:
        wipe(recovered)
    return {
        "schemaVersion": 1,
        "status": "windows-current-user-dpapi-synthetic-round-trip-passed",
        "keyBytes": load_contract()["mechanism"]["databaseKeyBytes"],
        "wrappedBytes": len(wrapped),
        "plaintextKeyReturned": False,
        "persistentWritePerformed": False,
        "runtimeAdmissionGranted": False,
        "packageAdmissionGranted": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(validate_synthetic_round_trip(), sort_keys=True))
    except KeyProtectionError as error:
        print(json.dumps({"status": "refused", "code": str(error)}, sort_keys=True))
        raise SystemExit(1)
