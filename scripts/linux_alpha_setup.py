#!/usr/bin/env python3
"""Consent-gated, user-local managed setup for Haven 42 Linux Alpha 2.

Importing this module has no process, network, or filesystem effects. Every
effect is derived from committed registries and requires a short-lived,
single-use approval for the exact plan shown to the user.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from linux_alpha import load_catalog, load_contract, load_registry
from linux_alpha_runtime import LinuxRuntimeError, extract_registered_archive


MANAGED_OLLAMA_HOST = "127.0.0.1:11435"
MANAGED_OLLAMA_URL = "http://127.0.0.1:11435"
JOURNAL_NAME = "setup-transaction.json"
OWNER_MARKER_NAME = ".haven42-managed-data.json"
OWNER_MARKER = {
    "schemaVersion": 1,
    "kind": "haven42-managed-portable-data",
    "owner": "Haven 42",
    "layoutVersion": 1,
}
APPROVAL_TTL_SECONDS = 15 * 60
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
MAX_REDIRECTS = 3
MAX_PROVIDER_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_RUNTIME_FILES = 8192
MAX_MANAGED_TREE_ENTRIES = 32768
MODEL_PULL_SOCKET_TIMEOUT_SECONDS = 120
MANAGED_PROVIDER_START_TIMEOUT_SECONDS = 120
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
COMPONENT_DECISION_CODES = {
    "ollama-linux-core": "SETUP_COMPONENT_OLLAMA_LINUX_CORE_0_32_14_SELECTED",
}
MODEL_DECISION_CODES = {
    "qwen35-08b-q8": "SETUP_MODEL_QWEN35_08B_Q8_SELECTED",
    "qwen35-2b-q8": "SETUP_MODEL_QWEN35_2B_Q8_SELECTED",
    "qwen35-4b-q4": "SETUP_MODEL_QWEN35_4B_Q4_SELECTED",
    "qwen35-9b-q4": "SETUP_MODEL_QWEN35_9B_Q4_SELECTED",
    "qwen35-27b-q4": "SETUP_MODEL_QWEN35_27B_Q4_SELECTED",
    "qwen35-35b-q4": "SETUP_MODEL_QWEN35_35B_Q4_SELECTED",
}


class SetupError(ValueError):
    """A Linux managed-setup operation failed closed."""


def _install_root() -> Path:
    candidate = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
    try:
        root = candidate.resolve(strict=True)
    except OSError as error:
        raise SetupError("portable-install-root-unavailable") from error
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise SetupError("portable-install-root-unavailable")
    return root


def default_state_root() -> Path:
    return _install_root() / "Haven42-Data"


def _safe_root(path: Path, *, create: bool = False) -> Path:
    lexical = path.absolute()
    cursor = lexical
    while True:
        if os.path.lexists(cursor) and cursor.is_symlink():
            raise SetupError("unsafe-portable-data-root")
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    resolved = lexical.resolve(strict=False)
    if create:
        resolved.mkdir(parents=True, exist_ok=True, mode=0o700)
    if resolved.exists() and (not resolved.is_dir() or resolved.is_symlink()):
        raise SetupError("unsafe-portable-data-root")
    return resolved


def _owned_root(path: Path, *, create: bool) -> Path:
    existed = path.exists()
    root = _safe_root(path, create=create)
    marker = root / OWNER_MARKER_NAME
    if create and not existed:
        try:
            with marker.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(OWNER_MARKER, handle, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            marker.chmod(0o600)
        except OSError as error:
            raise SetupError("portable-data-marker-write-failed") from error
    try:
        if marker.is_symlink() or not marker.is_file() or marker.stat().st_size > 1024:
            raise SetupError("unowned-portable-data-root")
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SetupError("unowned-portable-data-root") from error
    if value != OWNER_MARKER:
        raise SetupError("unowned-portable-data-root")
    return root


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        if path.is_symlink() or not path.is_file():
            raise SetupError("unsafe-managed-file")
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(DOWNLOAD_CHUNK_BYTES), b""):
                digest.update(block)
    except OSError as error:
        raise SetupError("managed-file-read-failed") from error
    return digest.hexdigest()


def _runtime_records(runtime: Path) -> list[dict[str, Any]]:
    root = _safe_root(runtime).resolve(strict=True)
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise SetupError("unsafe-managed-runtime-entry")
        if path.is_file():
            records.append({
                "path": path.relative_to(root).as_posix(),
                "sizeBytes": path.stat().st_size,
                "sha256": _sha256(path),
            })
        if len(records) > MAX_RUNTIME_FILES:
            raise SetupError("managed-runtime-file-limit")
    if not records:
        raise SetupError("managed-runtime-empty")
    return records


def _integrity_path(root: Path, version: str) -> Path:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}", version):
        raise SetupError("invalid-runtime-version")
    return root / f"runtime-integrity-{version}.json"


def _write_integrity(root: Path, version: str, runtime: Path) -> None:
    target = _integrity_path(root, version)
    value = {
        "schemaVersion": 1,
        "kind": "haven42-managed-runtime-integrity",
        "version": version,
        "files": _runtime_records(runtime),
    }
    _atomic_json(target, value, 4 * 1024 * 1024)


def _verify_integrity(root: Path, version: str, runtime: Path) -> None:
    target = _integrity_path(root, version)
    try:
        if target.is_symlink() or not target.is_file() or target.stat().st_size > 4 * 1024 * 1024:
            raise SetupError("managed-runtime-integrity-invalid")
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SetupError("managed-runtime-integrity-invalid") from error
    if value != {
        "schemaVersion": 1,
        "kind": "haven42-managed-runtime-integrity",
        "version": version,
        "files": _runtime_records(runtime),
    }:
        raise SetupError("managed-runtime-integrity-mismatch")


def _atomic_json(target: Path, value: dict[str, Any], maximum: int = 4096) -> None:
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    if len(data) > maximum:
        raise SetupError("managed-metadata-too-large")
    temporary = target.with_name(f".{target.name}.{secrets.token_hex(8)}.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, target)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise SetupError("portable-data-journal-write-failed") from error


def _journal(root: Path, transaction: dict[str, Any]) -> None:
    required = {"schemaVersion", "transactionId", "planId", "version", "phase", "componentIds", "modelId"}
    if (
        set(transaction) != required
        or transaction.get("schemaVersion") != 1
        or transaction.get("phase") not in {"approved", "downloading", "verifying", "extracting", "validating", "complete", "failed"}
        or any(not isinstance(transaction.get(key), str) or len(transaction[key]) > 128 for key in ("transactionId", "planId", "version", "phase", "modelId"))
        or not isinstance(transaction.get("componentIds"), list)
        or any(not SAFE_ID.fullmatch(item) for item in transaction["componentIds"])
    ):
        raise SetupError("invalid-transaction-journal")
    _atomic_json(root / JOURNAL_NAME, transaction)


def _required_storage(model: dict[str, Any], component: dict[str, Any]) -> int:
    return component["byteLength"] + component["expandedByteLength"] + model["modelBytes"] + 2 * 1024**3


def validate_setup_plan(plan: object) -> dict[str, Any]:
    required = {
        "schemaVersion", "kind", "planId", "version", "components", "modelId",
        "backendMode", "gpuAccelerationRequired", "requiredStorageBytes", "effects",
        "forbiddenEffects", "approvalRequired", "rememberApprovalAllowed",
        "driverAutomationAllowed",
    }
    catalog = load_catalog()
    registry = load_registry()
    models = [item for item in catalog["models"] if item["id"] == plan.get("modelId")] if isinstance(plan, dict) else []
    core = registry["components"][0]
    if (
        not isinstance(plan, dict) or set(plan) != required
        or plan.get("schemaVersion") != 1
        or plan.get("kind") != "linux-alpha-setup-plan"
        or plan.get("version") != load_contract()["version"]
        or not isinstance(plan.get("planId"), str) or not SAFE_TOKEN.fullmatch(plan["planId"])
        or len(models) != 1
        or plan.get("components") != ["ollama-linux-core"]
        or plan.get("backendMode") not in {"cpu", "cuda"}
        or plan.get("gpuAccelerationRequired") is not (plan.get("backendMode") == "cuda")
        or plan.get("requiredStorageBytes") != _required_storage(models[0], core)
        or plan.get("effects") != ["network-download", "portable-folder-files", "owned-process", "local-model-validation"]
        or plan.get("forbiddenEffects") != load_contract()["forbiddenEffects"]
        or plan.get("approvalRequired") is not True
        or plan.get("rememberApprovalAllowed") is not False
        or plan.get("driverAutomationAllowed") is not False
    ):
        raise SetupError("invalid-setup-plan")
    return dict(plan)


class _ApprovalStore:
    def __init__(self, session_id: str) -> None:
        if not isinstance(session_id, str) or len(session_id) < 16:
            raise SetupError("invalid-session")
        self.session_id = session_id
        self.values: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def issue(self, plan: dict[str, Any]) -> str:
        validate_setup_plan(plan)
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.values[token] = {
                "planId": plan["planId"], "effects": tuple(plan["effects"]),
                "expires": time.monotonic() + APPROVAL_TTL_SECONDS,
            }
        return token

    def consume(self, token: str, plan: dict[str, Any]) -> None:
        with self.lock:
            value = self.values.pop(token, None)
        if (
            value is None or value["planId"] != plan.get("planId")
            or value["effects"] != tuple(plan.get("effects", ()))
            or value["expires"] < time.monotonic()
        ):
            raise SetupError("invalid-or-expired-approval")


class _Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        self.count = 0
        self.allowed = {"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}

    def redirect_request(self, request, fp, code, msg, headers, new_url):
        self.count += 1
        parsed = urllib.parse.urlsplit(new_url)
        if (
            self.count > MAX_REDIRECTS or parsed.scheme != "https"
            or parsed.hostname not in self.allowed or parsed.username is not None
            or parsed.password is not None or parsed.port not in {None, 443}
        ):
            raise SetupError("unsafe-download-redirect")
        return super().redirect_request(request, fp, code, msg, headers, new_url)


def _download(component: dict[str, Any], destination: Path, cancel: threading.Event, progress: Callable[[int, int], None]) -> None:
    if component not in load_registry()["components"] or component.get("managedInstallationAllowed") is not True:
        raise SetupError("unregistered-component")
    parsed = urllib.parse.urlsplit(component["sourceUrl"])
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise SetupError("unsafe-download-origin")
    parent = _safe_root(destination.parent, create=True)
    if destination.parent.resolve(strict=False) != parent or destination.exists() or destination.is_symlink():
        raise SetupError("unsafe-download-destination")
    request = urllib.request.Request(component["sourceUrl"], headers={"User-Agent": "Haven42/0.4.0-alpha.2"})
    digest = hashlib.sha256()
    written = 0
    try:
        with urllib.request.build_opener(_Redirects()).open(request, timeout=30) as response, destination.open("xb") as output:
            while True:
                if cancel.is_set():
                    raise SetupError("setup-cancelled")
                block = response.read(DOWNLOAD_CHUNK_BYTES)
                if not block:
                    break
                written += len(block)
                if written > component["byteLength"]:
                    raise SetupError("component-size-mismatch")
                digest.update(block)
                output.write(block)
                progress(written, component["byteLength"])
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    if written != component["byteLength"] or digest.hexdigest() != component["sha256"]:
        destination.unlink(missing_ok=True)
        raise SetupError("component-integrity-mismatch")


def _provider_json(path: str, body: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    if path not in {"/api/version", "/api/tags", "/api/ps", "/api/pull", "/api/generate"}:
        raise SetupError("invalid-managed-provider-route")
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        MANAGED_OLLAMA_URL + path, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Haven42/0.4.0-alpha.2"},
        method="GET" if data is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        raise SetupError("managed-provider-request-rejected") from error
    except (OSError, urllib.error.URLError) as error:
        raise SetupError("managed-provider-request-failed") from error
    if len(raw) > MAX_PROVIDER_RESPONSE_BYTES:
        raise SetupError("managed-provider-response-too-large")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SetupError("invalid-managed-provider-response") from error
    if not isinstance(value, dict):
        raise SetupError("invalid-managed-provider-response")
    return value


def _model_record(model: dict[str, Any]) -> bool:
    records = _provider_json("/api/tags").get("models")
    if not isinstance(records, list):
        raise SetupError("invalid-managed-provider-response")
    matches = [item for item in records if isinstance(item, dict) and item.get("name") == model["name"]]
    if not matches:
        return False
    if len(matches) != 1:
        raise SetupError("model-manifest-digest-mismatch")
    digest = str(matches[0].get("digest", "")).removeprefix("sha256:")
    if not HEX64.fullmatch(digest) or digest != model["manifestDigest"]:
        raise SetupError("model-manifest-digest-mismatch")
    return True


def _pull_model(model: dict[str, Any], cancel: threading.Event, progress: Callable[[int, int], None]) -> None:
    request = urllib.request.Request(
        MANAGED_OLLAMA_URL + "/api/pull",
        data=json.dumps({"model": model["name"], "stream": True}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Haven42/0.4.0-alpha.2"},
        method="POST",
    )
    final: dict[str, Any] | None = None
    layers: dict[str, int] = {}
    total_response = 0
    try:
        with urllib.request.urlopen(request, timeout=MODEL_PULL_SOCKET_TIMEOUT_SECONDS) as response:
            while True:
                if cancel.is_set():
                    raise SetupError("setup-cancelled")
                raw = response.readline(65537)
                if not raw:
                    break
                total_response += len(raw)
                if len(raw) > 65536 or total_response > 16 * 1024 * 1024:
                    raise SetupError("managed-provider-response-too-large")
                current = json.loads(raw.decode("utf-8"))
                if not isinstance(current, dict) or current.get("error"):
                    raise SetupError("model-download-failed")
                completed, expected, digest = current.get("completed"), current.get("total"), current.get("digest")
                if (
                    isinstance(completed, int) and not isinstance(completed, bool)
                    and isinstance(expected, int) and not isinstance(expected, bool)
                    and 0 <= completed <= expected <= model["modelBytes"]
                    and isinstance(digest, str) and re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", digest)
                ):
                    layers[digest] = max(layers.get(digest, 0), completed)
                    progress(min(sum(layers.values()), model["modelBytes"]), model["modelBytes"])
                final = current
    except SetupError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, urllib.error.URLError) as error:
        raise SetupError("model-download-failed") from error
    if not isinstance(final, dict) or final.get("status") != "success" or not _model_record(model):
        raise SetupError("model-manifest-digest-mismatch")


class _OwnedProcess:
    def __init__(self) -> None:
        self.process: subprocess.Popen[bytes] | None = None

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def start(self, executable: Path, environment: dict[str, str], backend: str) -> int:
        if self.process is not None:
            raise SetupError("owned-process-already-started")
        try:
            executable = executable.resolve(strict=True)
        except OSError as error:
            raise SetupError("invalid-runtime-executable") from error
        if executable.name != "ollama" or executable.is_symlink() or not executable.is_file():
            raise SetupError("invalid-runtime-executable")
        if backend not in {"cpu", "cuda"}:
            raise SetupError("invalid-runtime-backend")
        required = {"OLLAMA_HOST", "OLLAMA_MODELS", "OLLAMA_ORIGINS", "OLLAMA_NO_CLOUD", "OLLAMA_NOHISTORY", "HOME", "TMPDIR"}
        expected = set(required)
        if backend == "cpu":
            expected.update({"OLLAMA_LLM_LIBRARY", "CUDA_VISIBLE_DEVICES"})
        managed_root = executable.parents[3]
        expected_paths = {
            "OLLAMA_MODELS": managed_root / "models",
            "HOME": managed_root / "home",
            "TMPDIR": managed_root / "temp",
        }
        paths_match = False
        if set(environment) == expected:
            try:
                paths_match = all(
                    Path(environment[name]).resolve(strict=True) == path.resolve(strict=True)
                    and not Path(environment[name]).is_symlink()
                    and Path(environment[name]).is_dir()
                    for name, path in expected_paths.items()
                )
            except OSError:
                paths_match = False
        if (
            set(environment) != expected
            or environment["OLLAMA_HOST"] != MANAGED_OLLAMA_HOST
            or environment["OLLAMA_ORIGINS"] != "http://127.0.0.1"
            or environment["OLLAMA_NO_CLOUD"] != "1"
            or environment["OLLAMA_NOHISTORY"] != "1"
            or not paths_match
            or backend == "cpu" and (
                environment["OLLAMA_LLM_LIBRARY"] != "cpu"
                or environment["CUDA_VISIBLE_DEVICES"] != "-1"
            )
        ):
            raise SetupError("invalid-runtime-environment")
        try:
            self.process = subprocess.Popen(
                [str(executable), "serve"], stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=str(executable.parent), env={"PATH": str(executable.parent), "LANG": "C.UTF-8", **environment},
                start_new_session=True, close_fds=True, shell=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            self.process = None
            raise SetupError("managed-process-start-failed") from error
        return self.process.pid

    def stop(self, timeout_seconds: float = 10) -> bool:
        process = self.process
        if process is None:
            return True
        try:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=timeout_seconds)
            return process.poll() is not None
        except (OSError, subprocess.SubprocessError) as error:
            raise SetupError("managed-process-stop-failed") from error
        finally:
            self.process = None


def _wait_provider(version: str, process: _OwnedProcess, cancel: threading.Event) -> None:
    deadline = time.monotonic() + MANAGED_PROVIDER_START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if cancel.is_set():
            raise SetupError("setup-cancelled")
        if not process.is_running():
            raise SetupError("managed-provider-exited-before-ready")
        try:
            if _provider_json("/api/version", timeout=2).get("version") == version:
                return
        except SetupError:
            pass
        time.sleep(0.25)
    raise SetupError("managed-provider-start-timeout")


def _validate_inference(model: dict[str, Any], gpu_required: bool) -> None:
    result = _provider_json("/api/generate", {
        "model": model["name"], "prompt": "Reply with only the word ready.",
        "stream": False, "keep_alive": "5m",
        "options": {"temperature": 0, "seed": 42, "num_predict": 8},
    }, timeout=300)
    if result.get("done") is not True or not (str(result.get("response", "")).strip() or str(result.get("thinking", "")).strip()):
        raise SetupError("managed-inference-validation-failed")
    records = _provider_json("/api/ps").get("models")
    matches = [item for item in records if isinstance(item, dict) and item.get("name") == model["name"]] if isinstance(records, list) else []
    if len(matches) != 1 or not isinstance(matches[0].get("size_vram"), int):
        raise SetupError("managed-model-not-loaded")
    if gpu_required and matches[0]["size_vram"] <= 0:
        raise SetupError("managed-accelerator-not-active")


def _progress_components(plan: dict[str, Any], present: set[str]) -> list[dict[str, Any]]:
    registry = {item["id"]: item for item in load_registry()["components"]}
    model = next(item for item in load_catalog()["models"] if item["id"] == plan["modelId"])
    result = []
    for component_id in plan["components"]:
        item = registry[component_id]
        result.append({
            "componentId": component_id, "kind": "runtime", "displayName": item["displayName"],
            "version": item["version"], "technologyName": None, "technologyVersion": None,
            "purpose": item["purpose"], "sizeBytes": item["byteLength"],
            "state": "present" if component_id in present else "pending",
            "progressPercent": 100 if component_id in present else 0,
            "downloadedBytes": item["byteLength"] if component_id in present else 0,
            "bytesPerSecond": 0, "etaSeconds": 0 if component_id in present else None,
            "progressActive": False,
        })
    result.append({
        "componentId": model["id"], "kind": "model", "displayName": model["name"],
        "version": model["quantization"], "technologyName": None, "technologyVersion": None,
        "purpose": "Provides private local chat, writing, and summaries on this computer.",
        "sizeBytes": model["modelBytes"], "state": "present" if model["id"] in present else "pending",
        "progressPercent": 100 if model["id"] in present else 0,
        "downloadedBytes": model["modelBytes"] if model["id"] in present else 0,
        "bytesPerSecond": 0, "etaSeconds": 0 if model["id"] in present else None,
        "progressActive": False,
    })
    return result


class SetupCoordinator:
    PHASES = {"idle", "approved", "downloading", "verifying", "extracting", "starting", "model-download", "validating", "complete", "failed", "cancelled"}

    def __init__(self, session_id: str, state_root: Path | None = None, event_sink: Callable[[str, str, str], bool] | None = None) -> None:
        self.approvals = _ApprovalStore(session_id)
        self.root = state_root or default_state_root()
        self.process = _OwnedProcess()
        self.lock = threading.Lock()
        self.status_value: dict[str, Any] = {"phase": "idle", "progressPercent": 0, "error": None, "components": []}
        self.plan: dict[str, Any] | None = None
        self.cancel_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.event_sink = event_sink
        self.download_samples: dict[str, tuple[int, float]] = {}

    def _emit(self, category: str, code: str, outcome: str) -> None:
        if self.event_sink is not None:
            try:
                self.event_sink(category, code, outcome)
            except Exception:
                pass

    def _set(self, phase: str, percent: int, error: str | None = None) -> None:
        with self.lock:
            self.status_value.update(phase=phase, progressPercent=max(0, min(100, percent)), error=error)

    def _component(self, identifier: str, state: str, percent: int) -> None:
        with self.lock:
            item = next(value for value in self.status_value["components"] if value["componentId"] == identifier)
            item.update(state=state, progressPercent=max(0, min(100, percent)), progressActive=state in {"downloading", "verifying", "installing", "validating"})

    def _download_progress(self, identifier: str, completed: int, total: int) -> None:
        percent = min(75, completed * 75 // max(total, 1))
        self._component(identifier, "downloading", percent)
        with self.lock:
            item = next(value for value in self.status_value["components"] if value["componentId"] == identifier)
            now = time.monotonic()
            prior = self.download_samples.get(identifier)
            speed = item["bytesPerSecond"]
            if prior and completed >= prior[0] and now - prior[1] >= 0.05:
                speed = int((completed - prior[0]) / (now - prior[1]))
            self.download_samples[identifier] = (completed, now)
            item.update(downloadedBytes=min(completed, item["sizeBytes"]), bytesPerSecond=max(0, speed))
            item["etaSeconds"] = (item["sizeBytes"] - item["downloadedBytes"] + speed - 1) // speed if speed > 0 else None

    def _present(self, plan: dict[str, Any]) -> set[str]:
        identity = self.completed_setup_identity()
        if identity is None or identity["componentIds"] != plan["components"] or identity["modelId"] != plan["modelId"]:
            return set()
        root = _owned_root(self.root, create=False)
        component = load_registry()["components"][0]
        from managed_runtime_update import read_runtime_selection
        version = read_runtime_selection(root, component)["version"]
        present = set()
        if (root / "runtime" / version).is_dir() and _integrity_path(root, version).is_file():
            present.update(plan["components"])
        if (root / "models").is_dir():
            present.add(plan["modelId"])
        return present

    def register_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        if self.thread is not None and self.thread.is_alive():
            raise SetupError("setup-already-running")
        validated = validate_setup_plan(plan)
        present = self._present(validated)
        with self.lock:
            self.plan = validated
            self.status_value = {"phase": "idle", "progressPercent": 0, "error": None, "components": _progress_components(validated, present)}
            self.download_samples = {}
        self._emit("setup", f"SETUP_BACKEND_{validated['backendMode'].upper()}_SELECTED", "observed")
        for identifier in validated["components"]:
            self._emit("setup", COMPONENT_DECISION_CODES[identifier], "observed")
        self._emit("setup", MODEL_DECISION_CODES[validated["modelId"]], "observed")
        return self.status()

    def approve(self, plan_id: str, acknowledged_effects: list[str]) -> str:
        with self.lock:
            plan = self.plan
        if plan is None or plan["planId"] != plan_id or acknowledged_effects != plan["effects"]:
            raise SetupError("approval-does-not-match-plan")
        return self.approvals.issue(plan)

    def start(self, approval_token: str) -> None:
        with self.lock:
            plan = self.plan
        if plan is None or self.thread is not None and self.thread.is_alive():
            raise SetupError("setup-plan-required" if plan is None else "setup-already-running")
        self.approvals.consume(approval_token, plan)
        self.cancel_event.clear()
        self.thread = threading.Thread(target=self._run, args=(dict(plan),), daemon=True)
        self.thread.start()

    def status(self) -> dict[str, Any]:
        with self.lock:
            value = {**self.status_value, "components": [dict(item) for item in self.status_value["components"]]}
            plan_id = self.plan["planId"] if self.plan else None
        return {
            "schemaVersion": 1, "kind": "linux-alpha-setup-progress", "planId": plan_id,
            **value, "persisted": False, "completedSetupCandidate": self.completed_setup_candidate(),
            "driverChanges": False, "serviceChanges": False, "firewallChanges": False,
            "elevationRequested": False, **self.storage_status(),
        }

    def storage_status(self) -> dict[str, Any]:
        state = "empty"
        if self.root.exists():
            try:
                _owned_root(self.root, create=False)
                state = "managed"
            except SetupError:
                state = "blocked-unrecognized"
        return {
            "storageScope": "inside-extracted-folder", "storageDirectoryName": "Haven42-Data",
            "managedComponentsState": state, "managedComponentsPresent": state == "managed",
            "legacyManagedComponentsPresent": False,
        }

    def completed_setup_identity(self) -> dict[str, Any] | None:
        try:
            root = _owned_root(self.root, create=False)
            receipt = root / JOURNAL_NAME
            if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size > 4096:
                return None
            value = json.loads(receipt.read_text(encoding="ascii"))
            registered_models = {item["id"] for item in load_catalog()["models"]}
            if (
                not isinstance(value, dict) or value.get("schemaVersion") != 1
                or value.get("version") != load_contract()["version"] or value.get("phase") != "complete"
                or value.get("componentIds") != ["ollama-linux-core"]
                or value.get("modelId") not in registered_models
                or not SAFE_TOKEN.fullmatch(str(value.get("transactionId", "")))
                or not SAFE_TOKEN.fullmatch(str(value.get("planId", "")))
            ):
                return None
            return {"version": value["version"], "componentIds": list(value["componentIds"]), "modelId": value["modelId"]}
        except (OSError, UnicodeError, json.JSONDecodeError, SetupError):
            return None

    def completed_setup_candidate(self) -> bool:
        return self.completed_setup_identity() is not None

    def resume_completed(self) -> dict[str, Any]:
        with self.lock:
            plan = self.plan
        identity = self.completed_setup_identity()
        if (
            plan is None
            or identity is None
            or identity["componentIds"] != plan["components"]
            or identity["modelId"] != plan["modelId"]
        ):
            raise SetupError("managed-setup-not-complete")
        root = _owned_root(self.root, create=False)
        version = load_registry()["components"][0]["version"]
        runtime = root / "runtime" / version
        _verify_integrity(root, version, runtime)
        self.cancel_event.clear()
        self._start_runtime(root, runtime, plan["backendMode"])
        _wait_provider(version, self.process, self.cancel_event)
        model = next(item for item in load_catalog()["models"] if item["id"] == plan["modelId"])
        if not _model_record(model):
            self.process.stop()
            raise SetupError("managed-model-not-present")
        return {"resumed": True, "modelId": model["id"], "backendMode": plan["backendMode"]}

    def _start_runtime(self, root: Path, runtime: Path, backend: str) -> None:
        for directory in (root / "home", root / "models", root / "temp"):
            _safe_root(directory, create=True)
        environment = {
            "OLLAMA_HOST": MANAGED_OLLAMA_HOST, "OLLAMA_MODELS": str((root / "models").resolve()),
            "OLLAMA_ORIGINS": "http://127.0.0.1", "OLLAMA_NO_CLOUD": "1", "OLLAMA_NOHISTORY": "1",
            "HOME": str((root / "home").resolve()), "TMPDIR": str((root / "temp").resolve()),
        }
        if backend == "cpu":
            environment.update(OLLAMA_LLM_LIBRARY="cpu", CUDA_VISIBLE_DEVICES="-1")
        self.process.start(runtime / "bin" / "ollama", environment, backend)

    def _run(self, plan: dict[str, Any]) -> None:
        staging: Path | None = None
        journal: dict[str, Any] | None = None
        root: Path | None = None
        try:
            transaction = secrets.token_urlsafe(18)
            component = load_registry()["components"][0]
            model = next(item for item in load_catalog()["models"] if item["id"] == plan["modelId"])
            root = _owned_root(self.root, create=True)
            runtime = root / "runtime" / component["version"]
            staging = root / "staging" / transaction
            archive = root / "downloads" / component["artifactName"]
            journal = {"schemaVersion": 1, "transactionId": transaction, "planId": plan["planId"], "version": plan["version"], "phase": "approved", "componentIds": list(plan["components"]), "modelId": plan["modelId"]}
            _journal(root, journal)
            self._set("approved", 1)
            if not runtime.exists():
                if shutil.disk_usage(root).free < plan["requiredStorageBytes"]:
                    raise SetupError("insufficient-managed-storage")
                if archive.exists() and (archive.is_symlink() or archive.stat().st_size != component["byteLength"] or _sha256(archive) != component["sha256"]):
                    archive.unlink()
                if not archive.exists():
                    self._set("downloading", 5)
                    self._component(component["id"], "downloading", 0)
                    journal["phase"] = "downloading"; _journal(root, journal)
                    _download(component, archive, self.cancel_event, lambda done, total: self._download_progress(component["id"], done, total))
                self._set("verifying", 25)
                self._component(component["id"], "verifying", 80)
                journal["phase"] = "verifying"; _journal(root, journal)
                self._set("extracting", 35)
                self._component(component["id"], "installing", 90)
                journal["phase"] = "extracting"; _journal(root, journal)
                try:
                    extract_registered_archive(archive, staging, component)
                except LinuxRuntimeError as error:
                    raise SetupError(str(error)) from error
                runtime.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                staging.replace(runtime)
                _write_integrity(root, component["version"], runtime)
                archive.unlink(missing_ok=True)
            _verify_integrity(root, component["version"], runtime)
            self._component(component["id"], "ready", 100)
            self._set("starting", 55)
            self._start_runtime(root, runtime, plan["backendMode"])
            _wait_provider(component["version"], self.process, self.cancel_event)
            self._set("model-download", 65)
            if not _model_record(model):
                self._component(model["id"], "downloading", 0)
                _pull_model(model, self.cancel_event, lambda done, total: self._download_progress(model["id"], done, total))
            self._set("validating", 95)
            self._component(model["id"], "validating", 95)
            journal["phase"] = "validating"; _journal(root, journal)
            _validate_inference(model, plan["gpuAccelerationRequired"])
            self._component(model["id"], "complete", 100)
            journal["phase"] = "complete"; _journal(root, journal)
            # Publish completion only after its durable receipt is visible.
            # Otherwise a fast caller can observe 100% and reject the setup
            # while the receipt still says "validating".
            self._set("complete", 100)
            self._emit("setup", "MANAGED_SETUP_COMPLETED", "completed")
        except Exception as error:
            code = str(error) if isinstance(error, SetupError) else "setup-internal-failure"
            self._emit("setup", "MANAGED_SETUP_FAILED", "failed")
            try:
                self.process.stop()
            except SetupError:
                pass
            if staging is not None and root is not None and staging.exists():
                try:
                    if staging.resolve(strict=False).is_relative_to(root.resolve(strict=False)):
                        shutil.rmtree(staging)
                except OSError:
                    pass
            with self.lock:
                progress_percent = self.status_value["progressPercent"]
            self._set("cancelled" if code == "setup-cancelled" else "failed", progress_percent, code)
            if journal is not None and root is not None:
                journal["phase"] = "failed"
                try:
                    _journal(root, journal)
                except SetupError:
                    pass

    def cancel(self) -> None:
        self.cancel_event.set()
        self.process.stop(timeout_seconds=2)

    def close(self) -> bool:
        self.cancel_event.set()
        return self.process.stop()

    def remove_managed_components(self) -> dict[str, Any]:
        if self.thread is not None and self.thread.is_alive():
            raise SetupError("setup-already-running")
        self.cancel_event.set()
        self.process.stop()
        if not self.root.exists():
            return {"removed": False, "managedComponentsPresent": False, "legacyManagedComponentsRemoved": False, "storageScope": "inside-extracted-folder"}
        root = _owned_root(self.root, create=False)
        entries = 0
        for path in root.rglob("*"):
            entries += 1
            if entries > MAX_MANAGED_TREE_ENTRIES or path.is_symlink() or (not path.is_file() and not path.is_dir()):
                raise SetupError("unsafe-portable-data-entry")
        try:
            shutil.rmtree(root)
        except OSError as error:
            raise SetupError("portable-data-removal-failed") from error
        with self.lock:
            self.plan = None
            self.status_value = {"phase": "idle", "progressPercent": 0, "error": None, "components": []}
        return {"removed": True, "managedComponentsPresent": False, "legacyManagedComponentsRemoved": False, "storageScope": "inside-extracted-folder"}
