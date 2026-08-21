#!/usr/bin/env python3
"""Run the review-only PDF worker against fixed synthetic fixtures."""

from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import Any
from ctypes import wintypes


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config" / "pdf-parser-worker-prototype-contract.json"
ARTIFACT_LOCK_PATH = ROOT / "config" / "pdf-parser-artifact-lock.json"
CORPUS_PATH = ROOT / "config" / "pdf-parser-hostile-corpus.json"
WORKER_PATH = ROOT / "scripts" / "restricted-pdf-worker.py"
DEFAULT_WHEEL = (
    ROOT
    / "dist"
    / "local-review"
    / "pdf-parser-candidate"
    / "pypdf-6.14.2-py3-none-any.whl"
)
FIXTURE_DIRECTORY = ROOT / "dist" / "local-review" / "pdf-parser-hostile-corpus"
REJECTION_REASONS = {
    "active-content-rejected",
    "artifact-digest-mismatch",
    "artifact-identity-mismatch",
    "embedded-content-rejected",
    "encrypted-content-rejected",
    "expansion-budget-exceeded",
    "external-reference-rejected",
    "input-size-rejected",
    "invalid-document-encoding",
    "invalid-object-reference",
    "invalid-page-tree",
    "invalid-pdf-signature",
    "invalid-request",
    "malformed-pdf-rejected",
    "nesting-budget-exceeded",
    "object-budget-exceeded",
    "object-graph-budget-exceeded",
    "output-budget-exceeded",
    "page-budget-exceeded",
    "parser-version-mismatch",
    "recursive-object-rejected",
    "request-too-large",
    "serialized-output-too-large",
    "stream-decode-rejected",
    "text-extraction-rejected",
    "worker-failure",
}


class WorkerHarnessError(RuntimeError):
    pass


if os.name == "nt":
    class _IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]


    class _BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]


    class _ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimitInformation),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]


def create_windows_job(contract: dict[str, Any]) -> int | None:
    if os.name != "nt":
        return None
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise WorkerHarnessError("windows-job-create-failed")
    limits = contract["limits"]
    information = _ExtendedLimitInformation()
    information.BasicLimitInformation.LimitFlags = (
        0x00000002
        | 0x00000008
        | 0x00000100
        | 0x00000200
        | 0x00002000
    )
    information.BasicLimitInformation.PerProcessUserTimeLimit = (
        limits["maximumCpuSeconds"] * 10_000_000
    )
    information.BasicLimitInformation.ActiveProcessLimit = 1
    information.ProcessMemoryLimit = limits["maximumMemoryBytes"]
    information.JobMemoryLimit = limits["maximumMemoryBytes"]
    if not kernel32.SetInformationJobObject(
        job,
        9,
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(job)
        raise WorkerHarnessError(f"windows-job-limit-failed-{error}")
    return int(job)


def assign_windows_job(job: int | None, process: subprocess.Popen[bytes]) -> None:
    if job is None:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    if not kernel32.AssignProcessToJobObject(job, int(process._handle)):
        error = ctypes.get_last_error()
        process.kill()
        process.wait(timeout=5)
        raise WorkerHarnessError(f"windows-job-assignment-failed-{error}")


def resume_windows_process(process: subprocess.Popen[bytes]) -> None:
    if os.name != "nt":
        return
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
    ntdll.NtResumeProcess.restype = ctypes.c_long
    status = ntdll.NtResumeProcess(int(process._handle))
    if status != 0:
        process.kill()
        process.wait(timeout=5)
        raise WorkerHarnessError(f"windows-process-resume-failed-{status & 0xffffffff:08x}")


def close_windows_job(job: int | None) -> None:
    if job is None:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle(job)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_wheel(wheel: Path, contract: dict[str, Any], artifact_lock: dict[str, Any]) -> Path:
    wheel = wheel.resolve(strict=True)
    artifact = contract["artifact"]
    locked = artifact_lock["artifact"]
    expected_parent = DEFAULT_WHEEL.parent.resolve()
    if wheel.parent != expected_parent or wheel.name != artifact["filename"]:
        raise WorkerHarnessError("artifact-path-rejected")
    if wheel.is_symlink() or not wheel.is_file():
        raise WorkerHarnessError("artifact-path-rejected")
    if (
        wheel.stat().st_size != locked["sizeBytes"]
        or sha256_file(wheel) != artifact["sha256"]
        or artifact["sha256"] != locked["sha256"]
    ):
        raise WorkerHarnessError("artifact-digest-mismatch")
    return wheel


def restricted_environment() -> dict[str, str]:
    environment = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
    }
    if os.name == "nt":
        for name in ("SystemRoot", "WINDIR"):
            if value := os.environ.get(name):
                environment[name] = value
    return environment


def directory_snapshot(directory: Path) -> dict[str, tuple[int, str]]:
    resolved = directory.resolve(strict=True)
    if directory.is_symlink() or (
        hasattr(directory, "is_junction") and directory.is_junction()
    ):
        raise WorkerHarnessError("snapshot-directory-rejected")
    with os.scandir(resolved) as iterator:
        entries = sorted(iterator, key=lambda entry: entry.name)
    if len(entries) > 64:
        raise WorkerHarnessError("snapshot-entry-budget-exceeded")
    snapshot: dict[str, tuple[int, str]] = {}
    total_bytes = 0
    for entry in entries:
        path = Path(entry.path)
        if (
            entry.is_symlink()
            or not entry.is_file(follow_symlinks=False)
            or (hasattr(path, "is_junction") and path.is_junction())
        ):
            raise WorkerHarnessError("snapshot-entry-rejected")
        size = os.lstat(entry.path).st_size
        total_bytes += size
        if total_bytes > 33_554_432:
            raise WorkerHarnessError("snapshot-byte-budget-exceeded")
        snapshot[entry.name] = (size, sha256_file(path))
    return snapshot


def bounded_process_io(
    process: subprocess.Popen[bytes],
    request: bytes,
    timeout_seconds: float,
    maximum_stdout: int,
    maximum_stderr: int,
) -> tuple[bytes, bytes, bool]:
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    overflow = threading.Event()

    def write_request() -> None:
        try:
            assert process.stdin is not None
            process.stdin.write(request)
            process.stdin.close()
        except (BrokenPipeError, OSError, ValueError):
            pass

    def read_bounded(stream: Any, output: bytearray, limit: int) -> None:
        try:
            while chunk := stream.read(64 * 1024):
                remaining = limit + 1 - len(output)
                if remaining > 0:
                    output.extend(chunk[:remaining])
                if len(output) > limit or len(chunk) > remaining:
                    overflow.set()
                    return
        finally:
            stream.close()

    assert process.stdout is not None and process.stderr is not None
    threads = [
        threading.Thread(target=write_request, daemon=True),
        threading.Thread(
            target=read_bounded,
            args=(process.stdout, stdout_buffer, maximum_stdout),
            daemon=True,
        ),
        threading.Thread(
            target=read_bounded,
            args=(process.stderr, stderr_buffer, maximum_stderr),
            daemon=True,
        ),
    ]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout_seconds
    forced = False
    while process.poll() is None:
        if overflow.is_set() or time.monotonic() >= deadline:
            forced = True
            process.kill()
            break
        time.sleep(0.01)
    process.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=5)
    if any(thread.is_alive() for thread in threads):
        raise WorkerHarnessError("worker-io-thread-failed")
    return bytes(stdout_buffer), bytes(stderr_buffer), forced


def launch(
    arguments: list[str],
    request: bytes,
    timeout_seconds: float,
    contract: dict[str, Any],
) -> tuple[int | None, bytes, bytes, bool]:
    creation_flags = (
        subprocess.CREATE_NO_WINDOW | 0x00000004
        if os.name == "nt"
        else 0
    )
    job = create_windows_job(contract)
    try:
        process = subprocess.Popen(
            [sys.executable, "-I", "-S", str(WORKER_PATH), *arguments],
            cwd=FIXTURE_DIRECTORY,
            env=restricted_environment(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creation_flags,
        )
        assign_windows_job(job, process)
        resume_windows_process(process)
        limits = contract["limits"]
        stdout, stderr, forced = bounded_process_io(
            process,
            request,
            timeout_seconds,
            limits["maximumStdoutBytes"],
            limits["maximumStderrBytes"],
        )
    finally:
        close_windows_job(job)
    if len(stdout) > limits["maximumStdoutBytes"]:
        raise WorkerHarnessError("worker-stdout-too-large")
    if len(stderr) > limits["maximumStderrBytes"]:
        raise WorkerHarnessError("worker-stderr-too-large")
    return process.returncode, stdout, stderr, forced


def validate_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise WorkerHarnessError("invalid-worker-result")
    if value.get("status") == "candidate-output":
        if set(value) != {
            "effects",
            "expandedBytes",
            "objectCount",
            "pageCount",
            "parser",
            "schemaVersion",
            "status",
            "text",
        }:
            raise WorkerHarnessError("invalid-worker-result")
        if value["parser"] != {"package": "pypdf", "version": "6.14.2"}:
            raise WorkerHarnessError("invalid-worker-result")
        if not isinstance(value["text"], str):
            raise WorkerHarnessError("invalid-worker-result")
        if not isinstance(value["pageCount"], int) or not isinstance(value["objectCount"], int):
            raise WorkerHarnessError("invalid-worker-result")
        if not isinstance(value["expandedBytes"], int):
            raise WorkerHarnessError("invalid-worker-result")
        if value["effects"] != {
            "networkUsed": False,
            "filesystemReadAfterImport": False,
            "filesystemWritePerformed": False,
            "temporaryFileWritten": False,
            "childProcessStarted": False,
            "runtimeAdmissionGranted": False,
        }:
            raise WorkerHarnessError("unsafe-worker-effects")
        return value
    if value.get("status") in {"rejected", "error"}:
        if set(value) != {"reason", "runtimeAdmissionGranted", "schemaVersion", "status"}:
            raise WorkerHarnessError("invalid-worker-result")
        if value["reason"] not in REJECTION_REASONS or value["runtimeAdmissionGranted"] is not False:
            raise WorkerHarnessError("invalid-worker-result")
        return value
    raise WorkerHarnessError("invalid-worker-result")


def run_worker(document: bytes, wheel: Path = DEFAULT_WHEEL) -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    artifact_lock = load_json(ARTIFACT_LOCK_PATH)
    wheel = validate_wheel(wheel, contract, artifact_lock)
    limits = contract["limits"]
    if not 1 <= len(document) <= limits["maximumInputBytes"]:
        raise WorkerHarnessError("input-size-rejected")
    request = json.dumps({
        "schemaVersion": 1,
        "operation": "extract-text",
        "documentBase64": base64.b64encode(document).decode("ascii"),
    }, separators=(",", ":")).encode("ascii")
    if len(request) > limits["maximumSerializedRequestBytes"]:
        raise WorkerHarnessError("request-too-large")
    before = directory_snapshot(FIXTURE_DIRECTORY)
    worker_wheel_reference = os.path.relpath(wheel, FIXTURE_DIRECTORY)
    returncode, stdout, stderr, forced = launch(
        ["--wheel", worker_wheel_reference],
        request,
        limits["maximumWallSeconds"],
        contract,
    )
    after = directory_snapshot(FIXTURE_DIRECTORY)
    if before != after:
        raise WorkerHarnessError("worker-residue-detected")
    if forced:
        raise WorkerHarnessError("worker-timeout")
    if returncode != 0 or stderr:
        raise WorkerHarnessError("worker-process-failed")
    try:
        return validate_result(json.loads(stdout))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkerHarnessError("invalid-worker-json") from error


def fixture_bytes(filename: str) -> bytes:
    corpus = load_json(CORPUS_PATH)
    allowed = {item["filename"] for item in corpus["cases"]}
    if filename not in allowed:
        raise WorkerHarnessError("fixture-not-allowlisted")
    path = FIXTURE_DIRECTORY / filename
    if path.is_symlink() or not path.is_file() or path.parent.resolve() != FIXTURE_DIRECTORY.resolve():
        raise WorkerHarnessError("fixture-path-rejected")
    expected = next(item for item in corpus["cases"] if item["filename"] == filename)
    if path.stat().st_size != expected["sizeBytes"] or sha256_file(path) != expected["sha256"]:
        raise WorkerHarnessError("fixture-digest-mismatch")
    return path.read_bytes()


def lifecycle_probe(argument: str, timeout_seconds: float) -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    before = directory_snapshot(FIXTURE_DIRECTORY)
    returncode, stdout, stderr, forced = launch(
        [argument],
        b"",
        timeout_seconds,
        contract,
    )
    after = directory_snapshot(FIXTURE_DIRECTORY)
    if before != after:
        raise WorkerHarnessError("worker-residue-detected")
    return {
        "returncode": returncode,
        "forcedTermination": forced,
        "stdoutBytes": len(stdout),
        "stderrBytes": len(stderr),
        "residueDetected": False,
    }


def effect_guard_probe(wheel: Path = DEFAULT_WHEEL) -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    wheel = validate_wheel(wheel, contract, load_json(ARTIFACT_LOCK_PATH))
    before = directory_snapshot(FIXTURE_DIRECTORY)
    worker_wheel_reference = os.path.relpath(wheel, FIXTURE_DIRECTORY)
    returncode, stdout, stderr, forced = launch(
        ["--wheel", worker_wheel_reference, "--self-test-effects"],
        b"",
        5,
        contract,
    )
    after = directory_snapshot(FIXTURE_DIRECTORY)
    if (
        before != after
        or forced
        or returncode != 0
        or stderr
    ):
        raise WorkerHarnessError("effect-guard-probe-failed")
    try:
        result = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkerHarnessError("effect-guard-probe-failed") from error
    if (
        not isinstance(result, dict)
        or set(result) != {"denied", "runtimeAdmissionGranted", "schemaVersion", "status"}
        or result["schemaVersion"] != 1
        or result["status"] != "effect-guard-probe"
        or result["runtimeAdmissionGranted"] is not False
        or set(result["denied"]) != {
            "network",
            "filesystemBuiltins",
            "filesystemOs",
            "temporaryFile",
            "childProcess",
            "shell",
        }
        or not all(result["denied"].values())
    ):
        raise WorkerHarnessError("effect-guard-probe-failed")
    return result


def main() -> int:
    corpus = load_json(CORPUS_PATH)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixture",
        choices=[item["filename"] for item in corpus["cases"]],
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.fixture:
        parser.error("--fixture is required")
    result = run_worker(fixture_bytes(args.fixture))
    print(json.dumps(result, indent=2) if args.json else result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
