#!/usr/bin/env python3
"""Offline and native checks for the Windows per-user ACL proof."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "conversation-history-windows-per-user-acl.json"
SCRIPT = ROOT / "scripts" / "conversation-history-windows-per-user-acl.ps1"


def main() -> int:
    checks = 0
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schemaVersion"] == 1; checks += 1
    assert contract["status"] == "development-synthetic-temporary-only"; checks += 1
    assert contract["acl"]["callerPathAllowed"] is False; checks += 1
    assert contract["acl"]["inheritanceMustBeProtected"] is True; checks += 1
    assert contract["acl"]["allowedPrincipalSids"] == ["current-user", "S-1-5-18"]; checks += 1
    assert contract["acl"]["unexpectedPrincipalFailsClosed"] is True; checks += 1
    assert contract["acl"]["productionApplicationDirectoryProven"] is False; checks += 1
    assert contract["authority"]["syntheticTemporaryValidationAllowed"] is True; checks += 1
    assert not any(
        value for name, value in contract["authority"].items()
        if name != "syntheticTemporaryValidationAllowed"
    ); checks += 1

    source = SCRIPT.read_text(encoding="utf-8")
    for required in (
        "SetAccessRuleProtection($true, $false)",
        "S-1-5-18",
        "S-1-5-32-545",
        "Assert-ExactAcl",
        "unexpected-principal-was-accepted",
        "FileMode]::CreateNew",
        "Flush($true)",
        "temporary-residue-detected",
    ):
        assert required in source, required
        checks += 1
    assert "param(" not in source.lower(); checks += 1
    assert "Invoke-Expression" not in source; checks += 1
    package_spec = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert "conversation-history-windows-per-user-acl" not in package_spec; checks += 1

    if sys.platform == "win32":
        completed = subprocess.run(
            ["pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(SCRIPT)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        result = json.loads(completed.stdout)
        assert result["status"] == "windows-synthetic-per-user-acl-passed"; checks += 1
        assert all(value is True for name, value in result["checks"].items() if name != "productionApplicationDirectoryProven"); checks += 1
        assert result["checks"]["productionApplicationDirectoryProven"] is False; checks += 1
        assert not any(
            value for name, value in result["authority"].items()
            if name != "syntheticTemporaryValidationAllowed"
        ); checks += 1

    print(f"Windows per-user ACL proof passed {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
