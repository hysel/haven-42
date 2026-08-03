#!/usr/bin/env python3
"""Read-only native Linux availability probe for the inactive parser worker gate."""

from __future__ import annotations

import argparse
import ctypes
import importlib.util
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = ROOT / "scripts/evaluate-pdf-os-isolation.py"
CONTROL_IDS = (
    "user-mount-pid-network-namespaces",
    "no-new-privileges",
    "seccomp-system-call-allowlist",
    "landlock-or-equivalent-filesystem-allowlist",
    "cgroup-or-rlimit-resource-limits",
)


def _load_evaluator():
    spec = importlib.util.spec_from_file_location("haven42_pdf_isolation", EVALUATOR_PATH)
    if not spec or not spec.loader:
        raise RuntimeError("isolation-evaluator-unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run(arguments: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        result = subprocess.run(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return result.returncode, result.stdout[:4096]


def _landlock_abi() -> int:
    # landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)
    if platform.machine().casefold() not in {"x86_64", "amd64", "aarch64", "arm64"}:
        return 0
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        result = int(libc.syscall(444, None, 0, 1))
    except (AttributeError, OSError, TypeError, ValueError):
        return 0
    return max(result, 0)


def _environment_kind(os_release: str, version: str) -> str:
    marker = (os_release + " " + version).casefold()
    return "wsl2" if "microsoft" in marker or "wsl" in marker else "native"


def collect(
    run=_run,
    which=shutil.which,
    landlock_abi=_landlock_abi,
    uname=platform.uname,
    status_text: str | None = None,
    cgroup_v2: bool | None = None,
) -> dict[str, object]:
    if sys.platform != "linux":
        raise RuntimeError("linux-only-probe")
    release = uname()
    environment_kind = _environment_kind(release.release, release.version)
    return_code, virtual = run(["/usr/bin/systemd-detect-virt"])
    virtual_class = virtual.strip().casefold() if return_code == 0 else "physical"
    if not re.fullmatch(r"[a-z0-9_-]{1,32}", virtual_class):
        virtual_class = "unknown"
    kernel = ".".join(re.findall(r"\d+", release.release)[:2]) or "unknown"
    machine = re.sub(r"[^a-z0-9_-]", "-", release.machine.casefold())[:32] or "unknown"
    identity = f"linux-{kernel}-{machine}-{virtual_class}"

    bwrap = which("bwrap")
    namespace_available = False
    if bwrap:
        code, output = run([
            bwrap, "--unshare-user", "--unshare-pid", "--unshare-net",
            "--ro-bind", "/", "/", "--proc", "/proc", "--dev", "/dev",
            "/usr/bin/printf", "namespace-ok",
        ])
        namespace_available = code == 0 and output == "namespace-ok"

    setpriv = which("setpriv")
    no_new_privileges = False
    if setpriv:
        code, output = run([
            setpriv, "--no-new-privs", "/bin/sh", "-c",
            "grep -q '^NoNewPrivs:[[:space:]]*1$' /proc/self/status && printf nnp-ok",
        ])
        no_new_privileges = code == 0 and output == "nnp-ok"

    if status_text is None:
        try:
            status = Path("/proc/self/status").read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            status = ""
    else:
        status = status_text
    seccomp_available = re.search(r"^Seccomp:\s*[0-2]$", status, re.MULTILINE) is not None
    cgroup_available = (
        Path("/sys/fs/cgroup/cgroup.controllers").is_file()
        if cgroup_v2 is None else cgroup_v2
    )
    resource_available = bool(which("prlimit")) and cgroup_available
    availability = {
        "user-mount-pid-network-namespaces": namespace_available,
        "no-new-privileges": no_new_privileges,
        "seccomp-system-call-allowlist": seccomp_available,
        "landlock-or-equivalent-filesystem-allowlist": landlock_abi() > 0,
        "cgroup-or-rlimit-resource-limits": resource_available,
    }
    evidence = {
        "schemaVersion": 2,
        "platform": "linux",
        "platformIdentity": identity,
        "environmentKind": environment_kind,
        "controls": [{
            "id": identifier,
            "available": availability[identifier],
            "implemented": False,
            "enforcementTestPassed": False,
            "hostileEscapeTestPassed": False,
        } for identifier in CONTROL_IDS],
        "sourcePackageParityPassed": False,
    }
    try:
        evaluator = _load_evaluator()
    except (RuntimeError, OSError, ImportError):
        evaluation = {
            "gateEvaluationPerformed": False,
            "isolationAdmissionPassed": False,
            "runtimeAdmissionGranted": False,
            "reason": "formal-evaluator-unavailable",
        }
    else:
        evaluation = evaluator.evaluate(evidence)
        evaluation["gateEvaluationPerformed"] = True
    return {
        "schemaVersion": 1,
        "evidenceType": "read-only-linux-isolation-capability-probe",
        "evidence": evidence,
        "evaluation": evaluation,
        "hostnameRetained": False,
        "networkIdentityRetained": False,
        "filesystemPathsRetained": False,
        "systemDependencyBundled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    result = collect()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
