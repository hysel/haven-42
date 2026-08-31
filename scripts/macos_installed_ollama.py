#!/usr/bin/env python3
"""Approval-gated startup for an already-installed official macOS Ollama app."""

from __future__ import annotations

import hashlib
import json
import os
import plistlib
import re
import secrets
import signal
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable


OLLAMA_APP = Path("/Applications/Ollama.app")
OLLAMA_BINARY_RELATIVE = Path("Contents/Resources/ollama")
OLLAMA_INFO_RELATIVE = Path("Contents/Info.plist")
OLLAMA_BUNDLE_ID = "com.electron.ollama"
OLLAMA_TEAM_ID = "3MU9H2V9Y9"
OLLAMA_HOST = "127.0.0.1:11435"
OLLAMA_URL = f"http://{OLLAMA_HOST}"
MAX_COMMAND_OUTPUT = 64 * 1024
SAFE_VERSION = re.compile(r"^[0-9][0-9A-Za-z._+-]{0,63}$")
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{16,160}$")


class MacOSInstalledOllamaError(ValueError):
    """The installed app or requested lifecycle action failed closed."""


def _registered_child(root: Path, relative: Path) -> Path:
    try:
        if root.is_symlink() or not root.is_dir():
            raise MacOSInstalledOllamaError("macos-ollama-app-not-detected")
        resolved_root = root.resolve(strict=True)
        candidate = root / relative
        if candidate.is_symlink():
            raise MacOSInstalledOllamaError("macos-ollama-layout-unverified")
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
        if not resolved.is_file():
            raise MacOSInstalledOllamaError("macos-ollama-layout-unverified")
        return resolved
    except (OSError, ValueError) as error:
        if isinstance(error, MacOSInstalledOllamaError):
            raise
        raise MacOSInstalledOllamaError("macos-ollama-layout-unverified") from error


def _read_identity(app_path: Path) -> dict[str, str]:
    info = _registered_child(app_path, OLLAMA_INFO_RELATIVE)
    try:
        if info.stat().st_size > 1024 * 1024:
            raise MacOSInstalledOllamaError("macos-ollama-identity-unverified")
        value = plistlib.loads(info.read_bytes())
    except (OSError, plistlib.InvalidFileException) as error:
        raise MacOSInstalledOllamaError("macos-ollama-identity-unverified") from error
    if not isinstance(value, dict) or value.get("CFBundleIdentifier") != OLLAMA_BUNDLE_ID:
        raise MacOSInstalledOllamaError("macos-ollama-identity-unverified")
    version = str(value.get("CFBundleShortVersionString", ""))
    if not SAFE_VERSION.fullmatch(version):
        raise MacOSInstalledOllamaError("macos-ollama-version-unverified")
    return {"bundleId": OLLAMA_BUNDLE_ID, "version": version}


def _run_fixed(arguments: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise MacOSInstalledOllamaError("macos-ollama-signature-check-failed") from error
    if len(completed.stdout) > MAX_COMMAND_OUTPUT:
        raise MacOSInstalledOllamaError("macos-ollama-signature-output-too-large")
    return completed.returncode, completed.stdout.decode("utf-8", errors="replace")


def inspect_installed_ollama(
    app_path: Path = OLLAMA_APP,
    command_runner: Callable[[list[str], int], tuple[int, str]] = _run_fixed,
) -> dict[str, Any]:
    """Verify only the fixed official app identity; return no private paths."""
    identity = _read_identity(app_path)
    binary = _registered_child(app_path, OLLAMA_BINARY_RELATIVE)
    app = str(app_path.resolve(strict=True))
    verify_code, _ = command_runner(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=2", app],
        15,
    )
    detail_code, detail = command_runner(
        ["/usr/bin/codesign", "-d", "--verbose=4", app],
        15,
    )
    assess_code, assess = command_runner(
        ["/usr/sbin/spctl", "--assess", "--type", "execute", "--verbose=4", app],
        15,
    )
    if verify_code != 0 or detail_code != 0 or assess_code != 0:
        raise MacOSInstalledOllamaError("macos-ollama-signature-unverified")
    if f"Identifier={OLLAMA_BUNDLE_ID}" not in detail or f"TeamIdentifier={OLLAMA_TEAM_ID}" not in detail:
        raise MacOSInstalledOllamaError("macos-ollama-publisher-unverified")
    if "accepted" not in assess.casefold():
        raise MacOSInstalledOllamaError("macos-ollama-gatekeeper-unverified")
    return {
        "schemaVersion": 1,
        "kind": "macos-installed-ollama",
        "status": "verified",
        "bundleId": identity["bundleId"],
        "teamId": OLLAMA_TEAM_ID,
        "version": identity["version"],
        "binary": binary,
        "signatureVerified": True,
        "gatekeeperAccepted": True,
        "privatePathsReturned": False,
    }


def readiness_item(app_path: Path = OLLAMA_APP) -> dict[str, Any]:
    """Return a sanitized readiness item without performing signature commands."""
    try:
        identity = _read_identity(app_path)
        _registered_child(app_path, OLLAMA_BINARY_RELATIVE)
    except MacOSInstalledOllamaError:
        return {
            "componentId": "ollama", "state": "not-detected", "version": None,
            "source": "registered-app-bundle-probe", "confidence": "high",
        }
    return {
        "componentId": "ollama", "state": "installed-unverified",
        "version": identity["version"], "source": "registered-app-bundle-probe",
        "confidence": "medium",
    }


class _ApprovalStore:
    def __init__(self, session_id: str) -> None:
        self.session_hash = hashlib.sha256(session_id.encode("ascii")).hexdigest()
        self.values: dict[str, tuple[str, float]] = {}
        self.lock = threading.Lock()

    def issue(self, plan: dict[str, Any]) -> str:
        token = secrets.token_urlsafe(32)
        plan_hash = hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        with self.lock:
            self.values[token] = (plan_hash, time.monotonic() + 300)
        return token

    def consume(self, token: str, plan: dict[str, Any]) -> None:
        if not isinstance(token, str) or not SAFE_TOKEN.fullmatch(token):
            raise MacOSInstalledOllamaError("invalid-macos-ollama-approval")
        expected = hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        with self.lock:
            value = self.values.pop(token, None)
        if value is None or value[1] < time.monotonic() or not secrets.compare_digest(value[0], expected):
            raise MacOSInstalledOllamaError("invalid-macos-ollama-approval")


class MacOSInstalledOllamaCoordinator:
    """Own one explicitly approved Ollama child process for this app session."""

    EFFECTS = [
        "Verify the installed Ollama app's code signature and Gatekeeper approval.",
        "Start its local AI engine on this computer for this Haven 42 session only.",
        "Use the current macOS user's existing Ollama model storage; do not download a model yet.",
    ]

    def __init__(
        self,
        session_id: str,
        app_path: Path = OLLAMA_APP,
        inspector: Callable[[Path], dict[str, Any]] = inspect_installed_ollama,
        process_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    ) -> None:
        self.app_path = app_path
        self.inspector = inspector
        self.process_factory = process_factory
        self.approvals = _ApprovalStore(session_id)
        self.plan: dict[str, Any] | None = None
        self.process: subprocess.Popen[bytes] | None = None
        self.lock = threading.Lock()

    def register_plan(self) -> dict[str, Any]:
        verified = self.inspector(self.app_path)
        plan = {
            "schemaVersion": 1,
            "kind": "macos-installed-ollama-start-plan",
            "planId": secrets.token_urlsafe(18),
            "version": verified["version"],
            "effects": list(self.EFFECTS),
            "approvalRequired": True,
            "endpoint": OLLAMA_URL,
            "downloadPerformed": False,
            "installationPerformed": False,
            "appBundleChanged": False,
            "elevationRequested": False,
            "serviceChanged": False,
            "modelDownloadPerformed": False,
        }
        with self.lock:
            self.plan = plan
        return dict(plan)

    def approve(self, plan_id: str, effects: list[str]) -> str:
        with self.lock:
            plan = self.plan
        if plan is None or plan_id != plan["planId"] or effects != plan["effects"]:
            raise MacOSInstalledOllamaError("macos-ollama-approval-does-not-match-plan")
        return self.approvals.issue(plan)

    @staticmethod
    def _port_available() -> bool:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind(("127.0.0.1", 11435))
            return True
        except OSError:
            return False
        finally:
            probe.close()

    @staticmethod
    def _trusted_user_environment() -> dict[str, str]:
        try:
            import pwd

            record = pwd.getpwuid(os.getuid())
        except (ImportError, KeyError, OSError) as error:
            raise MacOSInstalledOllamaError("macos-user-identity-unverified") from error
        home = Path(record.pw_dir)
        try:
            if not home.is_absolute() or home.is_symlink() or not home.is_dir():
                raise MacOSInstalledOllamaError("macos-user-home-unverified")
            resolved_home = home.resolve(strict=True)
        except OSError as error:
            raise MacOSInstalledOllamaError("macos-user-home-unverified") from error
        return {
            "HOME": str(resolved_home),
            "USER": record.pw_name,
            "LOGNAME": record.pw_name,
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "TMPDIR": "/tmp",
            "OLLAMA_HOST": OLLAMA_HOST,
            "OLLAMA_ORIGINS": "http://127.0.0.1",
            "OLLAMA_NO_CLOUD": "1",
            "OLLAMA_NOHISTORY": "1",
        }

    @staticmethod
    def _wait_ready(process: subprocess.Popen[bytes], timeout: int = 20) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise MacOSInstalledOllamaError("macos-ollama-process-exited")
            try:
                with urllib.request.urlopen(f"{OLLAMA_URL}/api/version", timeout=1) as response:
                    if response.status != 200:
                        raise OSError("unexpected-status")
                    body = response.read(4097)
                if len(body) > 4096:
                    raise MacOSInstalledOllamaError("macos-ollama-version-response-too-large")
                value = json.loads(body.decode("utf-8"))
                version = str(value.get("version", "")) if isinstance(value, dict) else ""
                if SAFE_VERSION.fullmatch(version):
                    return version
            except (OSError, UnicodeError, json.JSONDecodeError):
                time.sleep(0.2)
        raise MacOSInstalledOllamaError("macos-ollama-start-timeout")

    def start(self, approval_token: str) -> dict[str, Any]:
        with self.lock:
            plan = self.plan
            running = self.process is not None and self.process.poll() is None
        if plan is None:
            raise MacOSInstalledOllamaError("macos-ollama-plan-required")
        if running:
            raise MacOSInstalledOllamaError("macos-ollama-already-running")
        self.approvals.consume(approval_token, plan)
        verified = self.inspector(self.app_path)
        if verified["version"] != plan["version"]:
            raise MacOSInstalledOllamaError("macos-ollama-version-changed-after-approval")
        if not self._port_available():
            raise MacOSInstalledOllamaError("macos-ollama-private-port-unavailable")
        process = self.process_factory(
            [str(verified["binary"]), "serve"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            env=self._trusted_user_environment(),
            start_new_session=True,
        )
        with self.lock:
            self.process = process
        try:
            runtime_version = self._wait_ready(process)
        except Exception:
            self.close()
            raise
        return {
            "schemaVersion": 1,
            "kind": "macos-installed-ollama-start-result",
            "status": "started",
            "endpoint": OLLAMA_URL,
            "appVersion": verified["version"],
            "runtimeVersion": runtime_version,
            "signatureVerified": True,
            "gatekeeperAccepted": True,
            "ownedProcess": True,
            "downloadPerformed": False,
            "installationPerformed": False,
            "appBundleChanged": False,
            "modelDownloadPerformed": False,
            "approvalConsumed": True,
            "persisted": False,
        }

    def close(self) -> bool:
        with self.lock:
            process = self.process
            self.process = None
        if process is None or process.poll() is not None:
            return True
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                return False
        return process.poll() is not None
