#!/usr/bin/env python3
"""Run the exact review-only PDF worker suite and write sanitized native evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading


ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "config/pdf-parser-native-validation-contract.json"
WHEEL = ROOT / "dist/local-review/pdf-parser-candidate/pypdf-6.14.2-py3-none-any.whl"
OUTPUT = ROOT / "dist/local-review/pdf-native-validation"
PLATFORMS = {"windows": "Windows", "linux": "Linux", "macos": "Darwin"}
TESTS = (
    ("artifactLock", "scripts/test-pdf-parser-artifact-lock.py", "33 fail-closed checks"),
    ("fixtureCorpus", "scripts/test-pdf-parser-review-fixtures.py", "78 checks and created 14 inert files"),
    ("workerSecurity", "scripts/test-restricted-pdf-worker.py", "61 security checks across 14 fixtures"),
    ("staticContract", "scripts/test-pdf-worker-prototype-contract.py", "64 fail-closed checks"),
    ("boundaryParityAndExclusion", "scripts/test-pdf-worker-review-boundary.py", "40 contract-parity and exclusion checks"),
    ("prospectiveEvidence", "scripts/test-pdf-prospective-package-evidence.py", "10 deterministic, non-admission checks"),
)


def load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(64 * 1024):
            value.update(chunk)
    return value.hexdigest()


def normalized_machine() -> str:
    value = platform.machine().casefold()
    return {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}.get(value, value)


def safe_environment() -> dict[str, str]:
    value = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
    }
    if os.name == "nt":
        for name in ("SystemRoot", "WINDIR"):
            if current := os.environ.get(name):
                value[name] = current
    return value


def validate_preflight(expected: str, contract: dict) -> None:
    if platform.system() != PLATFORMS[expected]:
        raise RuntimeError("platform-mismatch")
    if WHEEL.is_symlink() or not WHEEL.is_file():
        raise RuntimeError("exact-ignored-wheel-required")
    if WHEEL.stat().st_size != contract["exactArtifactSizeBytes"]:
        raise RuntimeError("artifact-size-mismatch")
    if sha256_file(WHEEL) != contract["exactArtifactSha256"]:
        raise RuntimeError("artifact-digest-mismatch")
    if expected in {"linux", "macos"}:
        import resource
        for name in ("RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_FSIZE", "RLIMIT_NOFILE", "RLIMIT_NPROC"):
            if not hasattr(resource, name):
                raise RuntimeError("posix-resource-limit-unavailable")


def drain_bounded(stream, limit: int, result: dict, name: str) -> None:
    captured = bytearray()
    overflow = False
    while chunk := stream.read(64 * 1024):
        remaining = limit - len(captured)
        if remaining > 0:
            captured.extend(chunk[:remaining])
        if len(chunk) > max(remaining, 0):
            overflow = True
    result[name] = bytes(captured)
    result[f"{name}Overflow"] = overflow


def run_check(command: list[str], limits: dict) -> tuple[int, bytes, bytes]:
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=safe_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None and process.stderr is not None
    captured: dict[str, bytes | bool] = {}
    threads = (
        threading.Thread(
            target=drain_bounded,
            args=(process.stdout, limits["maximumStdoutBytes"], captured, "stdout"),
            daemon=True,
        ),
        threading.Thread(
            target=drain_bounded,
            args=(process.stderr, limits["maximumStderrBytes"], captured, "stderr"),
            daemon=True,
        ),
    )
    for thread in threads:
        thread.start()
    try:
        returncode = process.wait(timeout=limits["maximumCheckSeconds"])
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise RuntimeError("native-check-timeout") from None
    finally:
        for thread in threads:
            thread.join(timeout=5)
        process.stdout.close()
        process.stderr.close()
    if any(thread.is_alive() for thread in threads):
        raise RuntimeError("native-check-output-drain-failed")
    if captured.get("stdoutOverflow") or captured.get("stderrOverflow"):
        raise RuntimeError("native-check-output-limit-exceeded")
    return (
        returncode,
        captured.get("stdout", b""),
        captured.get("stderr", b""),
    )


def run(expected: str) -> dict:
    contract = load()
    validate_preflight(expected, contract)
    results = {}
    for identifier, relative, marker in TESTS:
        returncode, stdout_bytes, stderr = run_check(
            [sys.executable, "-I", "-S", str(ROOT / relative)],
            contract["validationLimits"],
        )
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        if returncode != 0 or stderr or marker not in stdout:
            raise RuntimeError(f"native-check-failed-{identifier}")
        results[identifier] = contract["requiredChecks"][identifier]
    evidence = {
        "schemaVersion": 1,
        "status": "review-only-native-validation-passed",
        "platform": expected,
        "architecture": normalized_machine(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "artifactSha256": contract["exactArtifactSha256"],
        "checks": results,
        "packageTested": False,
        "runtimeAdmissionGranted": False,
        "sanitization": {
            "hostnameRecorded": False,
            "usernameRecorded": False,
            "networkAddressRecorded": False,
            "absolutePathRecorded": False,
            "rawDocumentContentRecorded": False,
        },
    }
    if OUTPUT.exists() and (
        OUTPUT.is_symlink()
        or (hasattr(OUTPUT, "is_junction") and OUTPUT.is_junction())
        or not OUTPUT.is_dir()
    ):
        raise RuntimeError("unsafe-evidence-directory")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / f"{expected}-{normalized_machine()}.json"
    if destination.exists() and (destination.is_symlink() or not destination.is_file()):
        raise RuntimeError("unsafe-evidence-file")
    destination.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def describe(expected: str) -> dict:
    contract = load()
    return {
        "schemaVersion": 1,
        "status": "review-only-native-validation-plan",
        "platform": expected,
        "requiredChecks": contract["requiredChecks"],
        "networkUsed": False,
        "dependencyInstalled": False,
        "packageTested": False,
        "runtimeAdmissionGranted": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    parser.add_argument("--describe", action="store_true")
    arguments = parser.parse_args()
    result = describe(arguments.platform) if arguments.describe else run(arguments.platform)
    print(json.dumps(result, indent=2))
