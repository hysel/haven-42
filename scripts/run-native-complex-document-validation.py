#!/usr/bin/env python3
"""Run fixed complex-document review suites with bounded native evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config/complex-document-native-validation-contract.json"
OUTPUT = ROOT / "dist/local-review/complex-document-native-validation"
PLATFORMS = {"windows": "Windows", "linux": "Linux", "macos": "Darwin"}
TESTS = (
    (
        "containerSecurity",
        "scripts/test-complex-document-container-review.py",
        "41 deterministic security checks across 16 fixtures",
    ),
    (
        "semanticSecurity",
        "scripts/test-complex-document-semantic-review.py",
        "44 checks across 12 fixtures",
    ),
)


def environment() -> dict[str, str]:
    result = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
    }
    if os.name == "nt":
        for name in ("SystemRoot", "WINDIR"):
            if value := os.environ.get(name):
                result[name] = value
    return result


def drain(stream, maximum: int, result: dict, name: str) -> None:
    value = bytearray()
    overflow = False
    while chunk := stream.read(64 * 1024):
        remaining = maximum - len(value)
        if remaining > 0:
            value.extend(chunk[:remaining])
        overflow = overflow or len(chunk) > max(remaining, 0)
    result[name] = bytes(value)
    result[f"{name}Overflow"] = overflow


def execute(command: list[str], limits: dict) -> tuple[int, bytes, bytes]:
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None and process.stderr is not None
    captured: dict[str, object] = {}
    threads = (
        threading.Thread(
            target=drain,
            args=(process.stdout, limits["maximumStdoutBytes"], captured, "stdout"),
            daemon=True,
        ),
        threading.Thread(
            target=drain,
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
    return returncode, captured.get("stdout", b""), captured.get("stderr", b"")


def normalized_machine() -> str:
    value = platform.machine().casefold()
    return {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}.get(value, value)


def run(expected: str) -> dict:
    if platform.system() != PLATFORMS[expected]:
        raise RuntimeError("platform-mismatch")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    checks = {}
    for identifier, relative, marker in TESTS:
        returncode, stdout_bytes, stderr = execute(
            [sys.executable, "-I", "-S", str(ROOT / relative)], contract["limits"]
        )
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        if returncode != 0 or stderr or marker not in stdout:
            raise RuntimeError(f"native-check-failed-{identifier}")
        checks[identifier] = contract["requiredChecks"][identifier]
    evidence = {
        "schemaVersion": 1,
        "status": "review-only-native-validation-passed",
        "platform": expected,
        "architecture": normalized_machine(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "checks": checks,
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.platform), indent=2))
