#!/usr/bin/env python3
"""Prove that Windows closes a Haven-managed process tree with its job."""

from __future__ import annotations

import ctypes
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "windows_alpha_setup", ROOT / "scripts/windows_alpha_setup.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def main() -> int:
    if os.name != "nt":
        print("Windows Alpha job lifecycle test skipped: non-Windows host.")
        return 0

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    job = None
    parent = None
    child_handle = None
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-job-test-") as directory:
        pid_file = Path(directory) / "child.pid"
        parent_code = (
            "import pathlib,subprocess,sys,time;"
            "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
            "pathlib.Path(sys.argv[1]).write_text(str(child.pid),encoding='ascii');"
            "time.sleep(60)"
        )
        try:
            job = MODULE._create_windows_kill_job()
            assert job is not None
            parent = subprocess.Popen(
                [sys.executable, "-c", parent_code, str(pid_file)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW | MODULE.CREATE_SUSPENDED,
                shell=False,
            )
            MODULE._assign_windows_kill_job(job, parent)
            MODULE._resume_windows_process(parent)
            deadline = time.monotonic() + 10
            while not pid_file.is_file() and time.monotonic() < deadline:
                if parent.poll() is not None:
                    raise AssertionError("managed parent exited before creating its child")
                time.sleep(0.05)
            assert pid_file.is_file()
            child_pid = int(pid_file.read_text(encoding="ascii"))
            child_handle = kernel32.OpenProcess(
                MODULE.PROCESS_TERMINATE | MODULE.SYNCHRONIZE,
                False,
                child_pid,
            )
            assert child_handle
            checks += 4

            MODULE._close_windows_job(job)
            job = None
            parent.wait(timeout=5)
            assert parent.poll() is not None
            assert kernel32.WaitForSingleObject(child_handle, 5000) != MODULE.WAIT_TIMEOUT
            checks += 2
        finally:
            MODULE._close_windows_job(job)
            if parent is not None and parent.poll() is None:
                parent.kill()
                parent.wait(timeout=5)
            if child_handle:
                if kernel32.WaitForSingleObject(child_handle, 0) == MODULE.WAIT_TIMEOUT:
                    kernel32.TerminateProcess(child_handle, 1)
                    kernel32.WaitForSingleObject(child_handle, 5000)
                kernel32.CloseHandle(child_handle)

    print(f"Windows Alpha job lifecycle test passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
