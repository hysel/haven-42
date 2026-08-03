#!/usr/bin/env python3
"""Offline security tests for the native Linux parser-isolation probe."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/probe-linux-parser-isolation.py"
SPEC = importlib.util.spec_from_file_location("linux_isolation_probe", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def main() -> int:
    old_platform = MODULE.sys.platform
    MODULE.sys.platform = "linux"
    try:
        def run(arguments, timeout=10):
            if arguments == ["/usr/bin/systemd-detect-virt"]:
                return 0, "kvm\n"
            if "bwrap" in arguments[0]:
                return 0, "namespace-ok"
            if "setpriv" in arguments[0]:
                return 0, "nnp-ok"
            return 127, ""

        def which(name):
            return f"/usr/bin/{name}" if name in {"bwrap", "setpriv", "prlimit"} else None

        native = MODULE.collect(
            run=run,
            which=which,
            landlock_abi=lambda: 8,
            uname=lambda: SimpleNamespace(
                release="7.0.0-28-generic", version="#1 Ubuntu", machine="x86_64"
            ),
            status_text="Seccomp:\t0\n",
            cgroup_v2=True,
        )
        evidence = native["evidence"]
        assert evidence["environmentKind"] == "native"
        assert all(control["available"] for control in evidence["controls"])
        assert not any(control["implemented"] for control in evidence["controls"])
        assert not any(control["enforcementTestPassed"] for control in evidence["controls"])
        assert not any(control["hostileEscapeTestPassed"] for control in evidence["controls"])
        assert native["evaluation"]["isolationAdmissionPassed"] is False
        assert native["evaluation"]["runtimeAdmissionGranted"] is False
        assert native["evaluation"]["fallbackUsed"] is False
        assert native["evaluation"]["gateEvaluationPerformed"] is True
        serialized = json.dumps(native)
        assert "hostname" not in serialized.casefold() or '"hostnameRetained": false' in serialized
        assert "192" + ".168." not in serialized and "/home/" not in serialized

        wsl = MODULE.collect(
            run=run,
            which=which,
            landlock_abi=lambda: 8,
            uname=lambda: SimpleNamespace(
                release="6.6.87.2-microsoft-standard-WSL2",
                version="#1 SMP Microsoft", machine="x86_64"
            ),
            status_text="Seccomp:\t2\n",
            cgroup_v2=True,
        )
        assert wsl["evidence"]["environmentKind"] == "wsl2"
        assert wsl["evaluation"]["nativePlatformEvidence"] is False
        assert wsl["evaluation"]["isolationAdmissionPassed"] is False
        assert wsl["evaluation"]["environmentLimitations"] == [
            "wsl2-is-not-native-linux-evidence"
        ]
    finally:
        MODULE.sys.platform = old_platform
    source = PATH.read_text(encoding="utf-8")
    assert "sudo" not in source
    assert "apt " not in source and "dnf " not in source
    assert "os.open" not in source and "--output" not in source
    assert '"implemented": False' in source
    assert '"sourcePackageParityPassed": False' in source
    print("Linux parser-isolation probe passed 19 offline security checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
