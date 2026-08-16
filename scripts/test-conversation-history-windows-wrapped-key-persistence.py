#!/usr/bin/env python3
"""Hostile checks for temporary Windows wrapped-key persistence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "conversation-history-windows-wrapped-key-persistence.py"
SPEC = importlib.util.spec_from_file_location("history_wrapped_key_persistence", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def refused(callable_, code: str) -> None:
    try:
        callable_()
    except MODULE.WrappedKeyPersistenceError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"expected refusal: {code}")


def main() -> int:
    checks = 0
    contract = MODULE.load_contract()
    assert contract["storage"]["callerPathAllowed"] is False; checks += 1
    assert contract["storage"]["atomicNoReplaceRenameRequired"] is True; checks += 1
    assert contract["storage"]["productionAclAdmissionRequired"] is True; checks += 1
    assert contract["storage"]["productionAclAdmissionProven"] is False; checks += 1
    assert contract["recovery"]["automaticResetAllowed"] is False; checks += 1
    assert contract["recovery"]["plaintextFallbackAllowed"] is False; checks += 1
    assert contract["authority"]["persistentApplicationWriteAllowed"] is False; checks += 1
    assert contract["authority"]["packageAdmissionAllowed"] is False; checks += 1

    result = MODULE.validate_synthetic_temporary_persistence()
    assert result["status"] == "windows-synthetic-wrapped-key-temporary-persistence-passed"; checks += 1
    assert all(result["checks"].values()); checks += 1
    assert not any(value for name, value in result["authority"].items() if name != "syntheticTemporaryValidationAllowed"); checks += 1

    with tempfile.TemporaryDirectory() as temporary_name:
        directory = Path(temporary_name).resolve()
        refused(lambda: MODULE.write_wrapped_key_once(directory, b""), "invalid-wrapped-key"); checks += 1
        refused(lambda: MODULE.write_wrapped_key_once(directory, b"x" * 16_385), "invalid-wrapped-key"); checks += 1
        refused(lambda: MODULE.recover_wrapped_key(directory), "wrapped-key-missing"); checks += 1
        marker = directory / "keep.txt"
        marker.write_text("keep\n", encoding="utf-8")
        refused(lambda: MODULE.write_wrapped_key_once(directory, b"wrapped"), "unsafe-temporary-directory"); checks += 1
        assert marker.read_text(encoding="utf-8") == "keep\n"; checks += 1

    with tempfile.TemporaryDirectory() as temporary_name:
        directory = Path(temporary_name).resolve()
        def create_racing_destination(path: Path) -> None:
            path.write_bytes(b"preexisting")
        refused(
            lambda: MODULE.write_wrapped_key_once(
                directory, b"wrapped", _before_rename_for_test=create_racing_destination
            ),
            "wrapped-key-already-exists",
        ); checks += 1
        assert (directory / "history-key.dpapi").read_bytes() == b"preexisting"; checks += 1
        assert not (directory / "history-key.dpapi.tmp").exists(); checks += 1

    with tempfile.TemporaryDirectory() as temporary_name:
        altered = json.loads(MODULE.CONTRACT_PATH.read_text(encoding="utf-8"))
        altered["recovery"]["automaticResetAllowed"] = True
        path = Path(temporary_name) / "unsafe.json"
        path.write_text(json.dumps(altered), encoding="utf-8")
        refused(lambda: MODULE.load_contract(path), "unsafe-persistence-contract"); checks += 1

    source = SCRIPT.read_text(encoding="utf-8")
    assert '.open("xb")' in source and "os.fsync" in source and "os.rename" in source; checks += 1
    assert "os.replace" not in source; checks += 1
    package_spec = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert "conversation-history-windows-wrapped-key-persistence" not in package_spec; checks += 1
    print(f"Windows wrapped-key temporary persistence passed {checks} security checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
