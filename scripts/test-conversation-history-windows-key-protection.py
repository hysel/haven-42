#!/usr/bin/env python3
"""Hostile checks for the Windows conversation-history DPAPI proof."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "conversation-history-windows-key-protection.py"
SPEC = importlib.util.spec_from_file_location("history_dpapi", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def refused(callable_, code_prefix: str) -> None:
    try:
        callable_()
    except MODULE.KeyProtectionError as error:
        assert str(error).startswith(code_prefix), (str(error), code_prefix)
        return
    raise AssertionError(f"expected refusal: {code_prefix}")


def main() -> int:
    checks = 0
    contract = MODULE.load_contract()
    assert contract["mechanism"]["cryptProtectLocalMachineAllowed"] is False; checks += 1
    assert contract["mechanism"]["plaintextFallbackAllowed"] is False; checks += 1
    assert contract["authority"]["runtimeRouteAllowed"] is False; checks += 1
    assert contract["authority"]["persistentKeyWriteAllowed"] is False; checks += 1
    refused(lambda: MODULE.wipe(b"immutable"), "mutable-buffer-required"); checks += 1
    refused(lambda: MODULE.protect_key(bytearray(31)), "invalid-database-key"); checks += 1

    result = MODULE.validate_synthetic_round_trip()
    assert result["status"] == "windows-current-user-dpapi-synthetic-round-trip-passed"; checks += 1
    assert result["plaintextKeyReturned"] is False and result["persistentWritePerformed"] is False; checks += 1

    key = bytearray(range(32))
    expected_digest = hashlib.sha256(key).digest()
    wrapped = MODULE.protect_key(key)
    assert not any(key); checks += 1
    recovered = MODULE.unprotect_key(wrapped)
    try:
        assert hashlib.sha256(recovered).digest() == expected_digest; checks += 1
    finally:
        MODULE.wipe(recovered)
    tampered = wrapped[:-1] + bytes([wrapped[-1] ^ 1])
    refused(lambda: MODULE.unprotect_key(tampered), "dpapi-unprotect-failed-"); checks += 1

    with tempfile.TemporaryDirectory() as temporary:
        altered = json.loads(MODULE.CONTRACT_PATH.read_text(encoding="utf-8"))
        altered["mechanism"]["cryptProtectLocalMachineAllowed"] = True
        path = Path(temporary) / "unsafe.json"
        path.write_text(json.dumps(altered), encoding="utf-8")
        refused(lambda: MODULE.load_contract(path), "unsafe-key-protection-contract"); checks += 1

    source = SCRIPT.read_text(encoding="utf-8")
    assert "CRYPTPROTECT_LOCAL_MACHINE" not in source; checks += 1
    assert "CRYPTPROTECT_UI_FORBIDDEN" in source; checks += 1
    assert "mutable=True" in source and "ctypes.memmove" in source; checks += 1
    package_spec = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert "conversation-history-windows-key-protection" not in package_spec; checks += 1
    print(f"Windows conversation-history key protection passed {checks} security checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
