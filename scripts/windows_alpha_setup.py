#!/usr/bin/env python3
"""Constrained current-user setup primitives for the Windows private alpha.

No operation runs merely by importing this module. Network, extraction, and
process effects require a short-lived, single-use approval issued for an exact
plan. The web renderer never supplies paths, commands, URLs, or environment.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import ctypes
from ctypes import wintypes
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Callable

from windows_alpha import (
    load_component_registry,
    load_contract,
    load_model_catalog,
    required_setup_storage_bytes,
    setup_backend,
)
from alpha_release import ALPHA_1_VERSION, application_version
from windows_user_paths import WindowsUserPathError, portable_data_root, windows_local_app_data


HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_ARCHIVE_MEMBERS = 4096
MAX_EXPANDED_BYTES = 4 * 1024 * 1024 * 1024
MAX_REDIRECTS = 3
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
APPROVAL_TTL_SECONDS = 15 * 60
JOURNAL_NAME = "setup-transaction.json"
MANAGED_OLLAMA_HOST = "127.0.0.1:11435"
MANAGED_OLLAMA_URL = "http://127.0.0.1:11435"
MAX_PROVIDER_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_RUNTIME_FILES = 8192
MANAGED_PROVIDER_START_TIMEOUT_SECONDS = 120
MODEL_PULL_SOCKET_TIMEOUT_SECONDS = 120
RUNTIME_INTEGRITY_PREFIX = "runtime-integrity-"
BACKEND_MODES = {"cpu", "cuda", "rocm", "vulkan"}
COMPONENT_PROGRESS_STATES = {
    "pending", "present", "downloading", "verifying", "installing", "ready",
    "validating", "complete", "failed", "cancelled",
}
COMPONENT_DECISION_CODES = {
    "ollama-windows-core": "SETUP_COMPONENT_OLLAMA_WINDOWS_CORE_0_32_14_SELECTED",
    "ollama-windows-amd-rocm": (
        "SETUP_COMPONENT_OLLAMA_WINDOWS_AMD_ROCM_0_32_14_ROCM_7_1_SELECTED"
    ),
}
MODEL_DECISION_CODES = {
    "qwen35-08b-q8": "SETUP_MODEL_QWEN35_08B_Q8_SELECTED",
    "qwen35-2b-q8": "SETUP_MODEL_QWEN35_2B_Q8_SELECTED",
    "qwen35-4b-q4": "SETUP_MODEL_QWEN35_4B_Q4_SELECTED",
    "qwen35-9b-q4": "SETUP_MODEL_QWEN35_9B_Q4_SELECTED",
    "qwen35-27b-q4": "SETUP_MODEL_QWEN35_27B_Q4_SELECTED",
    "qwen35-35b-q4": "SETUP_MODEL_QWEN35_35B_Q4_SELECTED",
}
SETUP_FAILURE_DIAGNOSTIC_CODES = {
    "managed-provider-start-timeout": "MANAGED_PROVIDER_START_TIMEOUT",
    "managed-provider-exited-before-ready": "MANAGED_PROVIDER_EXITED_EARLY",
    "managed-provider-exited-during-validation": "MANAGED_PROVIDER_EXITED_DURING_VALIDATION",
    "model-download-failed": "MODEL_DOWNLOAD_INTERRUPTED",
    "managed-inference-request-failed": "MANAGED_INFERENCE_REQUEST_FAILED",
    "managed-inference-request-rejected": "MANAGED_INFERENCE_REQUEST_REJECTED",
    "managed-inference-response-invalid": "MANAGED_INFERENCE_RESPONSE_INVALID",
    "managed-model-status-request-failed": "MANAGED_MODEL_STATUS_REQUEST_FAILED",
    "managed-model-status-request-rejected": "MANAGED_MODEL_STATUS_REQUEST_REJECTED",
    "managed-model-status-response-invalid": "MANAGED_MODEL_STATUS_RESPONSE_INVALID",
    "managed-inference-validation-failed": "MANAGED_INFERENCE_VALIDATION_FAILED",
    "managed-model-not-loaded": "MANAGED_MODEL_NOT_LOADED",
    "managed-accelerator-not-active": "MANAGED_ACCELERATOR_NOT_ACTIVE",
}
STALE_JOURNAL_TEMP = re.compile(r"^\.setup-transaction\.json\.[0-9a-f]{16}\.tmp$")
SAFE_PLAN_ID = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
OWNER_MARKER_NAME = ".haven42-managed-data.json"
OWNER_MARKER = {
    "schemaVersion": 1,
    "kind": "haven42-managed-portable-data",
    "owner": "Haven 42",
    "layoutVersion": 1,
}
MAX_MANAGED_TREE_ENTRIES = 32768
LEGACY_DIRECTORIES = {"appdata", "downloads", "home", "models", "runtime", "staging", "temp"}
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
WAIT_TIMEOUT = 0x00000102
CREATE_SUSPENDED = 0x00000004
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000


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


class SetupError(ValueError):
    """Raised when a setup request or artifact fails closed."""


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _is_reparse_point(path: Path) -> bool:
    """Recognize Windows reparse points without breaking non-Windows CI."""
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _assert_safe_root(path: Path, *, create: bool = False) -> Path:
    lexical = path.absolute()
    cursor = lexical
    while True:
        if os.path.lexists(cursor) and (cursor.is_symlink() or _is_reparse_point(cursor)):
            raise SetupError("unsafe-reparse-root")
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    resolved = lexical.resolve(strict=False)
    if create:
        resolved.mkdir(parents=True, exist_ok=True)
    cursor = resolved
    while True:
        if os.path.lexists(cursor) and (cursor.is_symlink() or _is_reparse_point(cursor)):
            raise SetupError("unsafe-reparse-root")
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    return resolved


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(DOWNLOAD_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_state_root() -> Path:
    try:
        return portable_data_root()
    except WindowsUserPathError as error:
        raise SetupError("portable-data-root-unavailable") from error


def legacy_state_root() -> Path | None:
    if os.name != "nt":
        return None
    try:
        return windows_local_app_data() / "Haven42" / "alpha"
    except WindowsUserPathError:
        return None


def _owned_state_root(path: Path, *, create: bool) -> Path:
    """Validate or initialize the exact marker-owned portable data root."""
    existed = path.exists()
    root = _assert_safe_root(path, create=create)
    marker = root / OWNER_MARKER_NAME
    if not existed and create:
        try:
            with marker.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(OWNER_MARKER, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as error:
            raise SetupError("portable-data-marker-write-failed") from error
    if not root.exists():
        raise SetupError("portable-data-not-present")
    try:
        if marker.is_symlink() or _is_reparse_point(marker) or not marker.is_file():
            raise SetupError("unowned-portable-data-root")
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SetupError("unowned-portable-data-root") from error
    if value != OWNER_MARKER:
        raise SetupError("unowned-portable-data-root")
    return root


def _audit_removal_tree(root: Path) -> int:
    """Reject links, reparse points, special files, and unbounded deletion trees."""
    pending = [root]
    entries = 0
    while pending:
        directory = pending.pop()
        try:
            children = list(os.scandir(directory))
        except OSError as error:
            raise SetupError("portable-data-removal-audit-failed") from error
        for child in children:
            entries += 1
            if entries > MAX_MANAGED_TREE_ENTRIES:
                raise SetupError("portable-data-entry-limit")
            path = Path(child.path)
            if child.is_symlink() or _is_reparse_point(path):
                raise SetupError("unsafe-portable-data-entry")
            if child.is_dir(follow_symlinks=False):
                pending.append(path)
            elif not child.is_file(follow_symlinks=False):
                raise SetupError("unsafe-portable-data-entry")
    return entries


def _stop_windows_processes_beneath(roots: list[Path]) -> list[int]:
    """Stop only processes whose executable resolves inside an owned root."""
    if os.name != "nt" or not roots:
        return []
    canonical_roots = [root.resolve(strict=True) for root in roots]
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    psapi.EnumProcesses.argtypes = [
        ctypes.POINTER(wintypes.DWORD),
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    psapi.EnumProcesses.restype = wintypes.BOOL

    capacity = 65536
    identifiers = (wintypes.DWORD * capacity)()
    needed = wintypes.DWORD()
    if not psapi.EnumProcesses(
        identifiers, ctypes.sizeof(identifiers), ctypes.byref(needed),
    ):
        raise SetupError("managed-process-enumeration-failed")
    count = needed.value // ctypes.sizeof(wintypes.DWORD)
    if count >= capacity:
        raise SetupError("managed-process-enumeration-limit")

    stopped: list[int] = []
    for process_id in identifiers[:count]:
        if process_id in {0, os.getpid()}:
            continue
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_TERMINATE | SYNCHRONIZE,
            False,
            process_id,
        )
        if not handle:
            continue
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buffer))
            if not kernel32.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(size),
            ):
                continue
            try:
                executable = Path(buffer.value).resolve(strict=True)
            except OSError:
                continue
            if not any(_is_relative_to(executable, root) for root in canonical_roots):
                continue
            if not kernel32.TerminateProcess(handle, 1):
                raise SetupError("managed-process-stop-failed")
            if kernel32.WaitForSingleObject(handle, 5000) == WAIT_TIMEOUT:
                raise SetupError("managed-process-stop-failed")
            stopped.append(int(process_id))
        finally:
            kernel32.CloseHandle(handle)
    return stopped


def _legacy_owned_state_root(path: Path) -> Path:
    """Recognize only the exact receipt-bearing layout written by older Alpha builds."""
    root = _assert_safe_root(path, create=False)
    if not root.is_dir():
        raise SetupError("legacy-portable-data-not-present")
    journal = root / JOURNAL_NAME
    try:
        if journal.is_symlink() or _is_reparse_point(journal) or not journal.is_file():
            raise SetupError("unrecognized-legacy-data-root")
        receipt = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SetupError("unrecognized-legacy-data-root") from error
    expected_keys = {
        "schemaVersion", "transactionId", "planId", "version", "phase",
        "componentIds", "modelId",
    }
    registered_components = {item["id"] for item in load_component_registry()["components"]}
    registered_models = {item["id"] for item in load_model_catalog()["models"]}
    if (
        not isinstance(receipt, dict)
        or set(receipt) != expected_keys
        or receipt.get("schemaVersion") != 1
        or receipt.get("version") not in {ALPHA_1_VERSION, load_contract()["version"]}
        or not isinstance(receipt.get("transactionId"), str)
        or not SAFE_PLAN_ID.fullmatch(receipt["transactionId"])
        or not isinstance(receipt.get("planId"), str)
        or not SAFE_PLAN_ID.fullmatch(receipt["planId"])
        or receipt.get("phase") not in SetupCoordinator.PHASES - {"idle"}
        or not isinstance(receipt.get("componentIds"), list)
        or not receipt["componentIds"]
        or len(set(receipt["componentIds"])) != len(receipt["componentIds"])
        or any(item not in registered_components for item in receipt["componentIds"])
        or receipt.get("modelId") not in registered_models
    ):
        raise SetupError("unrecognized-legacy-data-root")
    for child in root.iterdir():
        if child.name in LEGACY_DIRECTORIES and child.is_dir():
            continue
        if child.name == JOURNAL_NAME and child.is_file():
            continue
        if re.fullmatch(r"runtime-integrity-[0-9]+(?:\.[0-9]+){1,3}\.json", child.name) and child.is_file():
            continue
        raise SetupError("unrecognized-legacy-data-root")
    return root


def clean_stale_journal_temps(state_root: Path) -> int:
    """Remove only bounded, engine-named remnants of interrupted atomic writes."""
    root = _assert_safe_root(state_root, create=True)
    removed = 0
    for entry in list(root.iterdir())[:64]:
        if not STALE_JOURNAL_TEMP.fullmatch(entry.name):
            continue
        if entry.is_symlink() or _is_reparse_point(entry) or not entry.is_file():
            raise SetupError("unsafe-stale-journal-entry")
        entry.unlink()
        removed += 1
        if removed > 32:
            raise SetupError("stale-journal-entry-limit")
    return removed


def build_plan(snapshot: dict[str, Any], selected_model: dict[str, Any]) -> dict[str, Any]:
    """Create a renderer-safe plan containing only registry identifiers."""
    contract = load_contract()
    registry = load_component_registry()
    catalog = load_model_catalog()
    if selected_model not in catalog["models"]:
        raise SetupError("unregistered-model")
    if not isinstance(snapshot, dict):
        raise SetupError("invalid-hardware-snapshot")
    try:
        backend = setup_backend(snapshot)
    except ValueError as error:
        raise SetupError("invalid-hardware-snapshot") from error
    backend_mode = backend["backendMode"]
    components = backend["components"]
    registered = {item["id"] for item in registry["components"]}
    if any(component not in registered for component in components):
        raise SetupError("unregistered-component")
    plan = {
        "schemaVersion": 1,
        "kind": "windows-alpha-setup-plan",
        "planId": secrets.token_urlsafe(24),
        "version": contract["version"],
        "components": components,
        "modelId": selected_model["id"],
        "backendMode": backend_mode,
        "gpuAccelerationRequired": backend_mode != "cpu",
        "requiredStorageBytes": required_setup_storage_bytes(
            selected_model, components, contract=contract, catalog=catalog, registry=registry,
        ),
        "effects": [
            "network-download", "portable-folder-files", "owned-process",
            "local-model-validation",
        ],
        "forbiddenEffects": list(contract["forbiddenEffects"]),
        "approvalRequired": True,
        "rememberApprovalAllowed": False,
        "driverAutomationAllowed": False,
    }
    validate_setup_plan(plan)
    return plan


def validate_setup_plan(plan: object) -> dict[str, Any]:
    """Reject any plan that is not exactly derivable from committed registries."""
    required = {
        "schemaVersion", "kind", "planId", "version", "components", "modelId",
        "backendMode", "gpuAccelerationRequired", "requiredStorageBytes", "effects",
        "forbiddenEffects", "approvalRequired", "rememberApprovalAllowed",
        "driverAutomationAllowed",
    }
    if not isinstance(plan, dict) or set(plan) != required:
        raise SetupError("invalid-setup-plan")
    contract = load_contract()
    catalog = load_model_catalog()
    registry = load_component_registry()
    models = [item for item in catalog["models"] if item["id"] == plan.get("modelId")]
    components = plan.get("components")
    backend = plan.get("backendMode")
    expected_components = (
        ["ollama-windows-core", "ollama-windows-amd-rocm"]
        if backend == "rocm" else ["ollama-windows-core"]
    )
    try:
        expected_storage = required_setup_storage_bytes(
            models[0], components, contract=contract, catalog=catalog, registry=registry,
        ) if len(models) == 1 and isinstance(components, list) else -1
    except ValueError:
        expected_storage = -1
    if (
        plan.get("schemaVersion") != 1
        or plan.get("kind") != "windows-alpha-setup-plan"
        or plan.get("version") != contract["version"]
        or not isinstance(plan.get("planId"), str)
        or not SAFE_PLAN_ID.fullmatch(plan["planId"])
        or backend not in BACKEND_MODES
        or components != expected_components
        or plan.get("gpuAccelerationRequired") is not (backend != "cpu")
        or isinstance(plan.get("requiredStorageBytes"), bool)
        or plan.get("requiredStorageBytes") != expected_storage
        or plan.get("effects") != [
            "network-download", "portable-folder-files", "owned-process",
            "local-model-validation",
        ]
        or plan.get("forbiddenEffects") != contract["forbiddenEffects"]
        or plan.get("approvalRequired") is not True
        or plan.get("rememberApprovalAllowed") is not False
        or plan.get("driverAutomationAllowed") is not False
    ):
        raise SetupError("invalid-setup-plan")
    return dict(plan)


class ApprovalStore:
    """Memory-only, session-bound, effect-bound, single-use approvals."""

    def __init__(self, session_id: str) -> None:
        if not isinstance(session_id, str) or len(session_id) < 16:
            raise SetupError("invalid-session")
        self._session_id = session_id
        self._values: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def issue(self, plan: dict[str, Any]) -> str:
        try:
            validate_setup_plan(plan)
        except SetupError as error:
            raise SetupError("invalid-approval-plan") from error
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._values[token] = {
                "sessionId": self._session_id,
                "planId": plan["planId"],
                "effects": tuple(plan["effects"]),
                "expires": time.monotonic() + APPROVAL_TTL_SECONDS,
            }
        return token

    def consume(self, token: str, plan: dict[str, Any]) -> None:
        with self._lock:
            value = self._values.pop(token, None)
        if (
            value is None
            or value["sessionId"] != self._session_id
            or value["planId"] != plan.get("planId")
            or value["effects"] != tuple(plan.get("effects", ()))
            or value["expires"] < time.monotonic()
        ):
            raise SetupError("invalid-or-expired-approval")


class FixedOriginRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: set[str]) -> None:
        self.allowed_hosts = allowed_hosts
        self.redirects = 0

    def redirect_request(self, request, fp, code, msg, headers, new_url):
        self.redirects += 1
        parsed = urllib.parse.urlsplit(new_url)
        if (
            self.redirects > MAX_REDIRECTS
            or parsed.scheme != "https"
            or parsed.hostname not in self.allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in {None, 443}
        ):
            raise SetupError("unsafe-download-redirect")
        return super().redirect_request(request, fp, code, msg, headers, new_url)


def download_registered_component(
    component: dict[str, Any],
    destination: Path,
    cancel: threading.Event | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Download one exact registry artifact to a newly created local file."""
    registry = load_component_registry()
    if component not in registry["components"]:
        raise SetupError("unregistered-component")
    parsed = urllib.parse.urlsplit(component["sourceUrl"])
    allowed_hosts = {"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise SetupError("unsafe-download-origin")
    destination = destination.resolve(strict=False)
    parent = _assert_safe_root(destination.parent, create=True)
    if destination.parent != parent:
        raise SetupError("unsafe-download-destination")
    if destination.exists():
        raise SetupError("download-destination-exists")
    opener = urllib.request.build_opener(FixedOriginRedirectHandler(allowed_hosts))
    request = urllib.request.Request(component["sourceUrl"], headers={"User-Agent": f"Haven42/{application_version()}"})
    digest = hashlib.sha256()
    written = 0
    try:
        with opener.open(request, timeout=30) as response, destination.open("xb") as output:
            while True:
                if cancel is not None and cancel.is_set():
                    raise SetupError("setup-cancelled")
                chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                written += len(chunk)
                if written > component["byteLength"]:
                    raise SetupError("component-size-mismatch")
                digest.update(chunk)
                output.write(chunk)
                if progress is not None:
                    progress(written, component["byteLength"])
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    if written != component["byteLength"] or digest.hexdigest() != component["sha256"]:
        destination.unlink(missing_ok=True)
        raise SetupError("component-integrity-mismatch")
    return {"byteLength": written, "sha256": digest.hexdigest(), "networkUsed": True}


def validate_zip(archive: Path) -> list[zipfile.ZipInfo]:
    """Reject traversal, links, case collisions, devices, and zip bombs."""
    try:
        handle = zipfile.ZipFile(archive)
    except (OSError, zipfile.BadZipFile) as error:
        raise SetupError("invalid-component-archive") from error
    with handle:
        members = handle.infolist()
        if not members or len(members) > MAX_ARCHIVE_MEMBERS:
            raise SetupError("unsafe-archive-member-count")
        total = 0
        names: set[str] = set()
        for member in members:
            path = PurePosixPath(member.filename.replace("\\", "/"))
            normalized = path.as_posix()
            mode = member.external_attr >> 16
            if (
                path.is_absolute()
                or not path.parts
                or any(part in {"", ".", ".."} for part in path.parts)
                or ":" in path.parts[0]
                or normalized.casefold() in names
                or stat.S_ISLNK(mode)
                or (mode and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)))
                or member.file_size < 0
            ):
                raise SetupError("unsafe-archive-member")
            names.add(normalized.casefold())
            total += member.file_size
            if total > MAX_EXPANDED_BYTES:
                raise SetupError("unsafe-archive-expanded-size")
        return members


def extract_validated_zip(archive: Path, destination: Path) -> dict[str, Any]:
    members = validate_zip(archive)
    root = _assert_safe_root(destination, create=True)
    written = 0
    with zipfile.ZipFile(archive) as handle:
        for member in members:
            target = (root / PurePosixPath(member.filename.replace("\\", "/"))).resolve(strict=False)
            if not _is_relative_to(target, root):
                raise SetupError("unsafe-archive-target")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with handle.open(member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output, DOWNLOAD_CHUNK_BYTES)
            written += member.file_size
    return {"memberCount": len(members), "expandedBytes": written, "filesWritten": True}


def write_journal(root: Path, transaction: dict[str, Any]) -> Path:
    """Persist only bounded recovery state; never URLs, paths, user content, or tokens."""
    allowed = {"schemaVersion", "transactionId", "planId", "version", "phase", "componentIds", "modelId"}
    if set(transaction) != allowed or transaction.get("schemaVersion") != 1:
        raise SetupError("invalid-transaction-journal")
    if transaction["phase"] not in {"approved", "downloading", "verifying", "extracting", "validating", "complete", "failed"}:
        raise SetupError("invalid-transaction-journal")
    for key in ("transactionId", "planId", "version", "phase", "modelId"):
        if not isinstance(transaction[key], str) or len(transaction[key]) > 128:
            raise SetupError("invalid-transaction-journal")
    if not isinstance(transaction["componentIds"], list) or any(not SAFE_ID.fullmatch(value) for value in transaction["componentIds"]):
        raise SetupError("invalid-transaction-journal")
    root = _assert_safe_root(root, create=True)
    target = root / JOURNAL_NAME
    temporary = root / f".{JOURNAL_NAME}.{secrets.token_hex(8)}.tmp"
    data = json.dumps(transaction, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if len(data) > 4096:
        raise SetupError("invalid-transaction-journal")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise SetupError("portable-data-journal-write-failed") from error
    return target


def completed_setup_components(state_root: Path, plan: dict[str, Any]) -> set[str]:
    """Identify receipt-backed portable files that can be verified and reused."""
    validated = validate_setup_plan(plan)
    if not state_root.exists():
        return set()
    root = _owned_state_root(state_root, create=False)
    journal = root / JOURNAL_NAME
    if not journal.exists():
        return set()
    if journal.is_symlink() or _is_reparse_point(journal) or not journal.is_file():
        raise SetupError("managed-setup-receipt-invalid")
    try:
        if journal.stat().st_size > 4096:
            raise SetupError("managed-setup-receipt-invalid")
        receipt = json.loads(journal.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SetupError("managed-setup-receipt-invalid") from error
    expected_keys = {
        "schemaVersion", "transactionId", "planId", "version", "phase",
        "componentIds", "modelId",
    }
    if (
        not isinstance(receipt, dict)
        or set(receipt) != expected_keys
        or receipt.get("schemaVersion") != 1
        or receipt.get("phase") != "complete"
        or receipt.get("version") != validated["version"]
        or receipt.get("componentIds") != validated["components"]
        or receipt.get("modelId") != validated["modelId"]
    ):
        return set()
    registry = load_component_registry()
    runtime_version = registry["components"][0]["version"]
    present: set[str] = set()
    if (
        (root / "runtime" / runtime_version).is_dir()
        and (root / f"{RUNTIME_INTEGRITY_PREFIX}{runtime_version}.json").is_file()
    ):
        present.update(validated["components"])
    if (root / "models").is_dir():
        present.add(validated["modelId"])
    return present


def _runtime_records(runtime: Path) -> list[dict[str, Any]]:
    root = _assert_safe_root(runtime, create=False).resolve(strict=True)
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().casefold()):
        if path.is_symlink() or _is_reparse_point(path):
            raise SetupError("unsafe-managed-runtime-entry")
        if path.is_dir():
            continue
        if not path.is_file():
            raise SetupError("unsafe-managed-runtime-entry")
        relative = path.relative_to(root).as_posix()
        if not relative or any(part in {"", ".", ".."} for part in PurePosixPath(relative).parts):
            raise SetupError("unsafe-managed-runtime-entry")
        records.append({"path": relative, "sizeBytes": path.stat().st_size, "sha256": _sha256_file(path)})
        if len(records) > MAX_RUNTIME_FILES:
            raise SetupError("managed-runtime-file-limit")
    if not records:
        raise SetupError("managed-runtime-empty")
    return records


def write_runtime_integrity(state_root: Path, version: str, runtime: Path) -> Path:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}(?:-[0-9A-Za-z.-]+)?", version):
        raise SetupError("invalid-runtime-version")
    root = _assert_safe_root(state_root, create=True)
    value = {
        "schemaVersion": 1,
        "kind": "haven42-managed-runtime-integrity",
        "version": version,
        "files": _runtime_records(runtime),
    }
    target = root / f"{RUNTIME_INTEGRITY_PREFIX}{version}.json"
    temporary = root / f".{target.name}.{secrets.token_hex(8)}.tmp"
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return target


def verify_runtime_integrity(state_root: Path, version: str, runtime: Path) -> dict[str, Any]:
    root = _assert_safe_root(state_root, create=False)
    manifest = root / f"{RUNTIME_INTEGRITY_PREFIX}{version}.json"
    if not manifest.is_file() or manifest.is_symlink() or _is_reparse_point(manifest):
        raise SetupError("managed-runtime-integrity-missing")
    try:
        value = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SetupError("managed-runtime-integrity-invalid") from error
    expected_keys = {"schemaVersion", "kind", "version", "files"}
    if (
        not isinstance(value, dict)
        or set(value) != expected_keys
        or value.get("schemaVersion") != 1
        or value.get("kind") != "haven42-managed-runtime-integrity"
        or value.get("version") != version
        or not isinstance(value.get("files"), list)
    ):
        raise SetupError("managed-runtime-integrity-invalid")
    try:
        actual = _runtime_records(runtime)
    except OSError as error:
        raise SetupError("managed-runtime-integrity-unreadable") from error
    if value["files"] != actual:
        raise SetupError("managed-runtime-integrity-mismatch")
    return {"verified": True, "fileCount": len(actual), "version": version}


def _create_windows_kill_job() -> int | None:
    """Create a non-inheritable job whose process tree dies with this process."""
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
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise SetupError("managed-job-create-failed")
    information = _ExtendedLimitInformation()
    information.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not kernel32.SetInformationJobObject(
        job, 9, ctypes.byref(information), ctypes.sizeof(information),
    ):
        kernel32.CloseHandle(job)
        raise SetupError("managed-job-policy-failed")
    return int(job)


def _assign_windows_kill_job(
    job: int | None, process: subprocess.Popen[bytes],
) -> None:
    if job is None:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    if not kernel32.AssignProcessToJobObject(job, int(process._handle)):
        raise SetupError("managed-job-assignment-failed")


def _resume_windows_process(process: subprocess.Popen[bytes]) -> None:
    if os.name != "nt":
        return
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
    ntdll.NtResumeProcess.restype = ctypes.c_long
    if ntdll.NtResumeProcess(int(process._handle)) != 0:
        raise SetupError("managed-process-resume-failed")


def _close_windows_job(job: int | None) -> None:
    if job is None:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle(job)


class OwnedProcess:
    """Exact-process lifecycle; refuses PIDs not created by this instance."""

    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._job: int | None = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(
        self,
        executable: Path,
        arguments: tuple[str, ...],
        environment: dict[str, str],
        backend_mode: str,
    ) -> int:
        if self._process is not None:
            raise SetupError("owned-process-already-started")
        executable = executable.resolve(strict=True)
        if executable.name.casefold() != "ollama.exe" or executable.is_symlink():
            raise SetupError("invalid-runtime-executable")
        if arguments != ("serve",):
            raise SetupError("invalid-runtime-arguments")
        if backend_mode not in BACKEND_MODES:
            raise SetupError("invalid-runtime-backend")
        required_environment = {
            "OLLAMA_HOST", "OLLAMA_MODELS", "OLLAMA_ORIGINS", "OLLAMA_NO_CLOUD",
            "OLLAMA_NOHISTORY", "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA",
            "TEMP", "TMP",
        }
        expected_environment = set(required_environment)
        if backend_mode == "vulkan":
            expected_environment.add("OLLAMA_VULKAN")
        elif backend_mode == "cpu":
            expected_environment.add("OLLAMA_LLM_LIBRARY")
        models_path = Path(environment.get("OLLAMA_MODELS", "")).resolve(strict=False)
        managed_root = models_path.parent
        expected_paths = {
            "HOME": managed_root / "home",
            "USERPROFILE": managed_root / "home",
            "LOCALAPPDATA": managed_root / "appdata" / "local",
            "APPDATA": managed_root / "appdata" / "roaming",
            "TEMP": managed_root / "temp",
            "TMP": managed_root / "temp",
        }
        if (
            set(environment) != expected_environment
            or environment["OLLAMA_HOST"] != MANAGED_OLLAMA_HOST
            or environment.get("OLLAMA_NO_CLOUD") != "1"
            or environment.get("OLLAMA_NOHISTORY") != "1"
            or any(
                Path(environment.get(name, "")).resolve(strict=False) != expected.resolve(strict=False)
                for name, expected in expected_paths.items()
            )
            or (backend_mode == "vulkan" and environment.get("OLLAMA_VULKAN") != "1")
            or (backend_mode == "cpu" and environment.get("OLLAMA_LLM_LIBRARY") != "cpu")
        ):
            raise SetupError("invalid-runtime-environment")
        child_environment = {"PATH": str(executable.parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"), **environment}
        job = _create_windows_kill_job()
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if job is not None:
            creation_flags |= CREATE_SUSPENDED
        try:
            self._process = subprocess.Popen(
                [str(executable), "serve"], stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=str(executable.parent), env=child_environment,
                creationflags=creation_flags, shell=False,
            )
            _assign_windows_kill_job(job, self._process)
            _resume_windows_process(self._process)
            self._job = job
        except Exception as error:
            _close_windows_job(job)
            if self._process is not None and self._process.poll() is None:
                self._process.kill()
                self._process.wait(timeout=5)
            self._process = None
            if isinstance(error, SetupError):
                raise
            raise SetupError("managed-process-start-failed") from error
        return self._process.pid

    def stop(self, timeout_seconds: float = 10) -> bool:
        process = self._process
        if process is None:
            _close_windows_job(self._job)
            self._job = None
            return True
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=timeout_seconds)
            return process.poll() is not None
        finally:
            _close_windows_job(self._job)
            self._job = None
            self._process = None


def verify_authenticode(executable: Path) -> dict[str, str]:
    """Verify the extracted executable with Windows' Authenticode policy."""
    if os.name != "nt":
        raise SetupError("authenticode-windows-only")
    executable = executable.resolve(strict=True)
    if executable.name.casefold() != "ollama.exe" or executable.is_symlink():
        raise SetupError("invalid-runtime-executable")
    powershell = Path(os.environ.get("SYSTEMROOT", "C:\\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    script = (
        "$ErrorActionPreference='Stop';"
        "$s=Get-AuthenticodeSignature -LiteralPath $env:HAVEN42_AUTHENTICODE_TARGET;"
        "[pscustomobject]@{Status=[string]$s.Status;Subject=[string]$s.SignerCertificate.Subject;"
        "Thumbprint=[string]$s.SignerCertificate.Thumbprint}|ConvertTo-Json -Compress"
    )
    try:
        process = subprocess.run(
            [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=30, check=False, shell=False,
            env={
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "PATH": str(powershell.parent),
                "PSModulePath": str(
                    Path(os.environ.get("SYSTEMROOT", "C:\\Windows"))
                    / "System32" / "WindowsPowerShell" / "v1.0" / "Modules"
                ),
                "HAVEN42_AUTHENTICODE_TARGET": str(executable),
            },
        )
        if process.returncode != 0 or len(process.stdout) > 8192:
            raise SetupError("authenticode-verification-failed")
        value = json.loads(process.stdout.decode("utf-8-sig"))
    except (OSError, subprocess.TimeoutExpired, UnicodeError, json.JSONDecodeError) as error:
        raise SetupError("authenticode-verification-failed") from error
    if (
        not isinstance(value, dict)
        or value.get("Status") != "Valid"
        or not isinstance(value.get("Subject"), str)
        or "Ollama" not in value["Subject"]
        or not re.fullmatch(r"[0-9A-Fa-f]{40,64}", str(value.get("Thumbprint", "")))
    ):
        raise SetupError("untrusted-runtime-signature")
    return {
        "status": "Valid", "publisher": value["Subject"][:256],
        "certificateThumbprint": value["Thumbprint"].upper(),
    }


def _provider_json(path: str, body: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    if path not in {"/api/version", "/api/tags", "/api/ps", "/api/pull", "/api/generate"}:
        raise SetupError("invalid-managed-provider-route")
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        MANAGED_OLLAMA_URL + path, data=data,
        headers={"Content-Type": "application/json", "User-Agent": f"Haven42/{application_version()}"},
        method="GET" if data is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        if not 400 <= error.code <= 599:
            raise SetupError("managed-provider-request-failed") from error
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


def wait_for_managed_provider(
    expected_version: str,
    timeout_seconds: float = MANAGED_PROVIDER_START_TIMEOUT_SECONDS,
    process_running: Callable[[], bool] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if cancelled is not None and cancelled():
            raise SetupError("setup-cancelled")
        if process_running is not None and not process_running():
            raise SetupError("managed-provider-exited-before-ready")
        try:
            value = _provider_json("/api/version", timeout=2)
            if value.get("version") == expected_version:
                return
        except SetupError:
            pass
        time.sleep(0.25)
    raise SetupError("managed-provider-start-timeout")


def pull_registered_model(
    model: dict[str, Any],
    cancel: threading.Event | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    catalog = load_model_catalog()
    if model not in catalog["models"]:
        raise SetupError("unregistered-model")
    request = urllib.request.Request(
        MANAGED_OLLAMA_URL + "/api/pull",
        data=json.dumps({"model": model["name"], "stream": True}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": f"Haven42/{application_version()}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=MODEL_PULL_SOCKET_TIMEOUT_SECONDS) as response:
            total = 0
            value: dict[str, Any] | None = None
            layer_progress: dict[str, int] = {}
            while True:
                if cancel is not None and cancel.is_set():
                    raise SetupError("setup-cancelled")
                raw = response.readline(65537)
                if not raw:
                    break
                if len(raw) > 65536:
                    raise SetupError("managed-provider-response-too-large")
                total += len(raw)
                if total > 16 * 1024 * 1024:
                    raise SetupError("managed-provider-response-too-large")
                try:
                    current = json.loads(raw.decode("utf-8"))
                except (UnicodeError, json.JSONDecodeError) as error:
                    raise SetupError("invalid-managed-provider-response") from error
                if not isinstance(current, dict) or current.get("error"):
                    raise SetupError("model-download-failed")
                completed = current.get("completed")
                expected = current.get("total")
                digest_name = current.get("digest")
                if (
                    progress is not None
                    and isinstance(completed, int) and not isinstance(completed, bool)
                    and isinstance(expected, int) and not isinstance(expected, bool)
                    and 0 <= completed <= expected <= model["modelBytes"]
                    and isinstance(digest_name, str)
                    and re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", digest_name)
                ):
                    prior = layer_progress.get(digest_name, 0)
                    if completed >= prior:
                        layer_progress[digest_name] = completed
                        aggregate = min(sum(layer_progress.values()), model["modelBytes"])
                        progress(aggregate, model["modelBytes"])
                value = current
    except SetupError:
        raise
    except (OSError, urllib.error.URLError) as error:
        if cancel is not None and cancel.is_set():
            raise SetupError("setup-cancelled") from error
        raise SetupError("model-download-failed") from error
    if not isinstance(value, dict) or value.get("status") != "success":
        raise SetupError("model-download-failed")
    tags = _provider_json("/api/tags")
    records = tags.get("models", [])
    if not isinstance(records, list):
        raise SetupError("invalid-managed-provider-response")
    verify_registered_model_record(model, records)
    return {"model": model["name"], "manifestDigest": model["manifestDigest"], "downloaded": True}


def verify_registered_model_record(model: dict[str, Any], records: list[object]) -> dict[str, Any]:
    """Compare one Ollama tag record to the immutable catalog digest."""
    catalog = load_model_catalog()
    if model not in catalog["models"] or not isinstance(records, list):
        raise SetupError("invalid-managed-model-record")
    matching = [item for item in records if isinstance(item, dict) and item.get("name") == model["name"]]
    if len(matching) != 1:
        raise SetupError("model-manifest-digest-mismatch")
    actual = matching[0].get("digest")
    if not isinstance(actual, str):
        raise SetupError("model-manifest-digest-mismatch")
    if actual.startswith("sha256:"):
        actual = actual[7:]
    if not HEX64.fullmatch(actual) or actual != model["manifestDigest"]:
        raise SetupError("model-manifest-digest-mismatch")
    return {"name": model["name"], "manifestDigest": actual, "verified": True}


def registered_model_present(model: dict[str, Any]) -> bool:
    """Report whether the managed provider already has the exact registered tag."""
    tags = _provider_json("/api/tags")
    records = tags.get("models")
    try:
        verify_registered_model_record(model, records)
        return True
    except SetupError as error:
        if str(error) != "model-manifest-digest-mismatch":
            raise
    return False


def validate_managed_inference(model: dict[str, Any], gpu_required: bool) -> dict[str, Any]:
    """Run fixed synthetic inference and prove GPU residency when required."""
    catalog = load_model_catalog()
    if model not in catalog["models"] or not isinstance(gpu_required, bool):
        raise SetupError("invalid-managed-validation-request")
    try:
        generated = _provider_json(
            "/api/generate",
            {
                "model": model["name"],
                "prompt": "Reply with only the word ready.",
                "stream": False,
                "keep_alive": "5m",
                "options": {"temperature": 0, "seed": 42, "num_predict": 8},
            },
            timeout=300,
        )
    except SetupError as error:
        code = str(error)
        if code == "managed-provider-request-rejected":
            raise SetupError("managed-inference-request-rejected") from error
        if code == "managed-provider-request-failed":
            raise SetupError("managed-inference-request-failed") from error
        if code in {
            "invalid-managed-provider-response",
            "managed-provider-response-too-large",
        }:
            raise SetupError("managed-inference-response-invalid") from error
        raise
    response_text = generated.get("response")
    thinking_text = generated.get("thinking", "")
    if (
        generated.get("done") is not True
        or not isinstance(response_text, str)
        or not isinstance(thinking_text, str)
        or not (response_text.strip() or thinking_text.strip())
        or isinstance(generated.get("eval_count"), bool)
        or not isinstance(generated.get("eval_count"), int)
        or not 1 <= generated["eval_count"] <= 64
    ):
        raise SetupError("managed-inference-validation-failed")
    try:
        processes = _provider_json("/api/ps")
    except SetupError as error:
        code = str(error)
        if code == "managed-provider-request-rejected":
            raise SetupError("managed-model-status-request-rejected") from error
        if code == "managed-provider-request-failed":
            raise SetupError("managed-model-status-request-failed") from error
        if code in {
            "invalid-managed-provider-response",
            "managed-provider-response-too-large",
        }:
            raise SetupError("managed-model-status-response-invalid") from error
        raise
    records = processes.get("models")
    if not isinstance(records, list):
        raise SetupError("managed-model-status-response-invalid")
    matches = [
        item for item in records
        if isinstance(item, dict) and item.get("name") == model["name"]
    ]
    if len(matches) != 1:
        raise SetupError("managed-model-not-loaded")
    size_vram = matches[0].get("size_vram")
    if (
        isinstance(size_vram, bool)
        or not isinstance(size_vram, int)
        or size_vram < 0
        or size_vram > MAX_EXPANDED_BYTES * 16
    ):
        raise SetupError("managed-model-status-response-invalid")
    if gpu_required and size_vram <= 0:
        raise SetupError("managed-accelerator-not-active")
    return {
        "modelValidated": True,
        "gpuAccelerationRequired": gpu_required,
        "gpuAccelerationVerified": size_vram > 0,
    }


def setup_progress_components(
    plan: dict[str, Any], present_component_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return bounded renderer-safe descriptions for one validated setup plan."""
    validated = validate_setup_plan(plan)
    registry = load_component_registry()
    catalog = load_model_catalog()
    components = {item["id"]: item for item in registry["components"]}
    model = next(item for item in catalog["models"] if item["id"] == validated["modelId"])
    present = present_component_ids or set()
    result = [
        {
            "componentId": component_id,
            "kind": "runtime",
            "displayName": components[component_id]["displayName"],
            "version": components[component_id]["version"],
            "technologyName": components[component_id].get("technologyName"),
            "technologyVersion": components[component_id].get("technologyVersion"),
            "purpose": components[component_id]["purpose"],
            "sizeBytes": components[component_id]["byteLength"],
            "state": "present" if component_id in present else "pending",
            "progressPercent": 100 if component_id in present else 0,
            "downloadedBytes": components[component_id]["byteLength"] if component_id in present else 0,
            "bytesPerSecond": 0,
            "etaSeconds": 0 if component_id in present else None,
            "progressActive": False,
        }
        for component_id in validated["components"]
    ]
    result.append({
        "componentId": model["id"],
        "kind": "model",
        "displayName": model["name"],
        "version": model["quantization"],
        "technologyName": None,
        "technologyVersion": None,
        "purpose": "Provides the private local chat capability selected for this device.",
        "sizeBytes": model["modelBytes"],
        "state": "present" if model["id"] in present else "pending",
        "progressPercent": 100 if model["id"] in present else 0,
        "downloadedBytes": model["modelBytes"] if model["id"] in present else 0,
        "bytesPerSecond": 0,
        "etaSeconds": 0 if model["id"] in present else None,
        "progressActive": False,
    })
    return result


class SetupCoordinator:
    """One active setup transaction with bounded, renderer-safe progress."""

    PHASES = {"idle", "approved", "downloading", "verifying", "extracting", "starting", "model-download", "validating", "complete", "failed", "cancelled"}

    def __init__(
        self,
        session_id: str,
        state_root: Path | None = None,
        event_sink: Callable[[str, str, str], bool] | None = None,
    ) -> None:
        self.approvals = ApprovalStore(session_id)
        self.root = state_root or default_state_root()
        self.legacy_root = legacy_state_root() if state_root is None else None
        self.process = OwnedProcess()
        self._lock = threading.Lock()
        self._status: dict[str, Any] = {
            "phase": "idle", "progressPercent": 0, "error": None,
            "components": [],
        }
        self._active_component_id: str | None = None
        self._download_samples: dict[str, tuple[int, float]] = {}
        self._plan: dict[str, Any] | None = None
        self._cancel = threading.Event()
        self._thread: threading.Thread | None = None
        self._event_sink = event_sink

    def _emit(self, category: str, code: str, outcome: str) -> None:
        """Best-effort fixed-code evidence must never alter setup behavior."""
        if self._event_sink is None:
            return
        try:
            self._event_sink(category, code, outcome)
        except Exception:
            pass

    def register_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        if self._thread is not None and self._thread.is_alive():
            raise SetupError("setup-already-running")
        with self._lock:
            self._plan = validate_setup_plan(plan)
            present = completed_setup_components(self.root, self._plan)
            self._status = {
                "phase": "idle", "progressPercent": 0, "error": None,
                "components": setup_progress_components(self._plan, present),
            }
            self._active_component_id = None
            self._download_samples = {}
        self._emit(
            "setup",
            f"SETUP_BACKEND_{self._plan['backendMode'].upper()}_SELECTED",
            "observed",
        )
        for component_id in self._plan["components"]:
            self._emit("setup", COMPONENT_DECISION_CODES[component_id], "observed")
        self._emit("setup", MODEL_DECISION_CODES[self._plan["modelId"]], "observed")
        return self.status()

    def approve(self, plan_id: str, acknowledged_effects: list[str]) -> str:
        with self._lock:
            plan = self._plan
        if plan is None or plan.get("planId") != plan_id or acknowledged_effects != plan.get("effects"):
            raise SetupError("approval-does-not-match-plan")
        return self.approvals.issue(plan)

    def start(self, approval_token: str) -> None:
        with self._lock:
            plan = self._plan
        if plan is None:
            raise SetupError("setup-plan-required")
        self.approvals.consume(approval_token, plan)
        self._cancel.clear()
        self._thread = threading.Thread(target=self._run, args=(plan,), daemon=True)
        self._thread.start()

    def resume_completed(self) -> dict[str, Any]:
        """Start a previously approved, receipt-backed setup without downloading.

        Every launch revalidates the receipt, runtime inventory, Authenticode
        publisher, exact registered model, paths, and loopback endpoint. A
        missing or changed component fails closed and returns to guided setup.
        """
        if self._thread is not None and self._thread.is_alive():
            raise SetupError("setup-already-running")
        with self._lock:
            plan = dict(self._plan) if self._plan is not None else None
        if plan is None:
            raise SetupError("setup-plan-required")
        validated = validate_setup_plan(plan)
        expected = set(validated["components"]) | {validated["modelId"]}
        if completed_setup_components(self.root, validated) != expected:
            raise SetupError("managed-setup-not-complete")
        registry = load_component_registry()
        catalog = load_model_catalog()
        runtime_version = registry["components"][0]["version"]
        root = _owned_state_root(self.root, create=False)
        runtime = root / "runtime" / runtime_version
        models = root / "models"
        verify_runtime_integrity(root, runtime_version, runtime)
        try:
            executable = next(path for path in runtime.rglob("ollama.exe") if path.is_file())
        except StopIteration as error:
            raise SetupError("runtime-executable-missing") from error
        verify_authenticode(executable)
        managed_directories = {
            "HOME": root / "home",
            "USERPROFILE": root / "home",
            "LOCALAPPDATA": root / "appdata" / "local",
            "APPDATA": root / "appdata" / "roaming",
            "TEMP": root / "temp",
            "TMP": root / "temp",
        }
        for directory in {models, *managed_directories.values()}:
            if not directory.is_dir():
                raise SetupError("managed-runtime-directory-missing")
            _assert_safe_root(directory, create=False)
        environment = {
            "OLLAMA_HOST": MANAGED_OLLAMA_HOST,
            "OLLAMA_MODELS": str(models.resolve()),
            "OLLAMA_ORIGINS": "http://127.0.0.1",
            "OLLAMA_NO_CLOUD": "1",
            "OLLAMA_NOHISTORY": "1",
            **{name: str(path.resolve()) for name, path in managed_directories.items()},
        }
        if validated["backendMode"] == "vulkan":
            environment["OLLAMA_VULKAN"] = "1"
        elif validated["backendMode"] == "cpu":
            environment["OLLAMA_LLM_LIBRARY"] = "cpu"
        if not self.process.is_running():
            try:
                self.process.start(executable, ("serve",), environment, validated["backendMode"])
                wait_for_managed_provider(
                    runtime_version,
                    process_running=self.process.is_running,
                )
            except Exception:
                self.process.stop()
                raise
        model = next(item for item in catalog["models"] if item["id"] == validated["modelId"])
        if not registered_model_present(model):
            self.process.stop()
            raise SetupError("registered-model-not-present")
        with self._lock:
            self._status = {
                "phase": "complete", "progressPercent": 100, "error": None,
                "components": setup_progress_components(validated, expected),
            }
        return {
            "schemaVersion": 1,
            "kind": "windows-alpha-managed-provider-resume",
            "endpoint": MANAGED_OLLAMA_URL,
            "runtimeVersion": runtime_version,
            "model": model["name"],
            "backendMode": validated["backendMode"],
            "downloadPerformed": False,
            "installationPerformed": False,
            "integrityVerified": True,
            "publisherVerified": True,
            "receiptVerified": True,
        }

    def _set(self, phase: str, progress: int, error: str | None = None) -> None:
        if phase not in self.PHASES or not 0 <= progress <= 100:
            raise SetupError("invalid-setup-progress")
        with self._lock:
            self._status.update({
                "phase": phase, "progressPercent": progress, "error": error,
            })

    def _set_component(self, component_id: str, state: str, progress: int) -> None:
        if state not in COMPONENT_PROGRESS_STATES or not 0 <= progress <= 100:
            raise SetupError("invalid-component-progress")
        with self._lock:
            matches = [
                item for item in self._status["components"]
                if item["componentId"] == component_id
            ]
            if len(matches) != 1:
                raise SetupError("invalid-component-progress")
            matches[0]["state"] = state
            matches[0]["progressPercent"] = progress
            matches[0]["progressActive"] = state == "downloading"
            if state in {"present", "ready", "complete"}:
                matches[0]["downloadedBytes"] = matches[0]["sizeBytes"]
                matches[0]["bytesPerSecond"] = 0
                matches[0]["etaSeconds"] = 0
            elif state in {"failed", "cancelled"}:
                matches[0]["bytesPerSecond"] = 0
                matches[0]["etaSeconds"] = None
                matches[0]["progressActive"] = False
            if state in {"downloading", "verifying", "installing", "validating"}:
                self._active_component_id = component_id
            elif self._active_component_id == component_id:
                self._active_component_id = None

    def _download_progress(self, component_id: str, completed: int, total: int) -> None:
        if (
            isinstance(completed, bool) or not isinstance(completed, int)
            or isinstance(total, bool) or not isinstance(total, int)
            or total <= 0 or not 0 <= completed <= total
        ):
            raise SetupError("invalid-component-progress")
        component_progress = min(75, completed * 75 // total)
        self._set_component(component_id, "downloading", component_progress)
        with self._lock:
            components = self._status["components"]
            current = next(item for item in components if item["componentId"] == component_id)
            now = time.monotonic()
            previous = self._download_samples.get(component_id)
            bytes_per_second = current["bytesPerSecond"]
            if previous is not None and completed >= previous[0] and now > previous[1]:
                elapsed = now - previous[1]
                if elapsed >= 0.05:
                    bytes_per_second = min(
                        int((completed - previous[0]) / elapsed),
                        current["sizeBytes"] * 10,
                    )
            self._download_samples[component_id] = (completed, now)
            current["downloadedBytes"] = min(completed, current["sizeBytes"])
            current["bytesPerSecond"] = max(0, bytes_per_second)
            current["etaSeconds"] = (
                min(
                    7 * 24 * 60 * 60,
                    (current["sizeBytes"] - current["downloadedBytes"] + bytes_per_second - 1)
                    // bytes_per_second,
                )
                if bytes_per_second > 0 else None
            )
            current["progressActive"] = True
            if current["kind"] == "model" and self._status["phase"] == "model-download":
                calculated = 65 + component_progress * 30 // 75
                self._status["progressPercent"] = max(
                    self._status["progressPercent"], calculated,
                )
            elif current["kind"] == "runtime" and self._status["phase"] == "downloading":
                runtime_ids = [
                    item["componentId"] for item in components if item["kind"] == "runtime"
                ]
                index = runtime_ids.index(component_id)
                calculated = 5 + index * 20 + component_progress * 10 // 75
                self._status["progressPercent"] = max(
                    self._status["progressPercent"], calculated,
                )

    def status(self) -> dict[str, Any]:
        with self._lock:
            value = {
                **self._status,
                "components": [dict(item) for item in self._status["components"]],
            }
            plan_id = self._plan.get("planId") if self._plan else None
        storage = self.storage_status()
        return {
            "schemaVersion": 1, "kind": "windows-alpha-setup-progress",
            "planId": plan_id, **value, "persisted": False,
            "completedSetupCandidate": self.completed_setup_candidate(),
            "driverChanges": False, "serviceChanges": False,
            "firewallChanges": False, "elevationRequested": False,
            **storage,
        }

    def storage_status(self) -> dict[str, Any]:
        portable_state = "empty"
        if not self.root.exists():
            portable_state = "empty"
        else:
            try:
                _owned_state_root(self.root, create=False)
                portable_state = "managed"
            except SetupError:
                portable_state = "blocked-unrecognized"
        legacy_state = "empty"
        if self.legacy_root is not None and self.legacy_root.exists():
            try:
                _legacy_owned_state_root(self.legacy_root)
                legacy_state = "managed"
            except SetupError:
                legacy_state = "blocked-unrecognized"
        if "blocked-unrecognized" in {portable_state, legacy_state}:
            state = "blocked-unrecognized"
        elif portable_state == "managed" and legacy_state == "managed":
            state = "managed-with-legacy"
        elif portable_state == "managed":
            state = "managed"
        elif legacy_state == "managed":
            state = "legacy-managed"
        else:
            state = "empty"
        return {
            "storageScope": "inside-extracted-folder",
            "storageDirectoryName": "Haven42-Data",
            "managedComponentsState": state,
            "managedComponentsPresent": state in {"managed", "legacy-managed", "managed-with-legacy"},
            "legacyManagedComponentsPresent": legacy_state == "managed",
        }

    def completed_setup_identity(self) -> dict[str, Any] | None:
        """Return registered receipt identifiers, never paths or caller data."""
        try:
            root = _owned_state_root(self.root, create=False)
            journal = root / JOURNAL_NAME
            if (
                journal.is_symlink() or _is_reparse_point(journal)
                or not journal.is_file() or journal.stat().st_size > 4096
            ):
                return False
            receipt = json.loads(journal.read_text(encoding="ascii"))
            registry = load_component_registry()
            catalog = load_model_catalog()
            component_ids = {item["id"] for item in registry["components"]}
            model_ids = {item["id"] for item in catalog["models"]}
            valid = (
                isinstance(receipt, dict)
                and set(receipt) == {
                    "schemaVersion", "transactionId", "planId", "version",
                    "phase", "componentIds", "modelId",
                }
                and receipt.get("schemaVersion") == 1
                and receipt.get("version") == load_contract()["version"]
                and receipt.get("phase") == "complete"
                and isinstance(receipt.get("componentIds"), list)
                and bool(receipt["componentIds"])
                and len(receipt["componentIds"]) == len(set(receipt["componentIds"]))
                and all(item in component_ids for item in receipt["componentIds"])
                and receipt.get("modelId") in model_ids
                and isinstance(receipt.get("transactionId"), str)
                and SAFE_PLAN_ID.fullmatch(receipt["transactionId"]) is not None
                and isinstance(receipt.get("planId"), str)
                and SAFE_PLAN_ID.fullmatch(receipt["planId"]) is not None
            )
            if not valid:
                return None
            return {
                "version": receipt["version"],
                "componentIds": list(receipt["componentIds"]),
                "modelId": receipt["modelId"],
            }
        except (OSError, UnicodeError, json.JSONDecodeError, SetupError, ValueError):
            return None

    def completed_setup_candidate(self) -> bool:
        """Return only whether a bounded completion receipt is eligible for resume."""
        return self.completed_setup_identity() is not None

    def cancel(self) -> None:
        self._cancel.set()
        try:
            self.process.stop(timeout_seconds=2)
        except Exception:
            # The worker observes the cancellation flag even if Windows does
            # not let this request close the owned process immediately.
            pass

    def _run(self, plan: dict[str, Any]) -> None:
        state_root: Path | None = None
        staging: Path | None = None
        journal: dict[str, Any] | None = None
        try:
            transaction_id = secrets.token_urlsafe(18)
            catalog = load_model_catalog()
            registry = load_component_registry()
            components = {item["id"]: item for item in registry["components"]}
            model = next(item for item in catalog["models"] if item["id"] == plan["modelId"])
            state_root = _owned_state_root(self.root, create=True)
            if clean_stale_journal_temps(state_root):
                self._emit("storage", "SETUP_INTERRUPTED_WRITE_RECOVERED", "warning")
            staging = state_root / "staging" / transaction_id
            downloads = state_root / "downloads"
            runtime_version = registry["components"][0]["version"]
            runtime = state_root / "runtime" / runtime_version
            models = state_root / "models"
            journal = {
                "schemaVersion": 1, "transactionId": transaction_id,
                "planId": plan["planId"], "version": plan["version"],
                "phase": "approved", "componentIds": list(plan["components"]),
                "modelId": plan["modelId"],
            }
            self._set("approved", 1)
            write_journal(state_root, journal)
            if not runtime.exists():
                if shutil.disk_usage(state_root).free < plan["requiredStorageBytes"]:
                    raise SetupError("insufficient-managed-storage")
                downloaded_archives: list[Path] = []
                for index, component_id in enumerate(plan["components"]):
                    if self._cancel.is_set():
                        raise SetupError("setup-cancelled")
                    component = components[component_id]
                    self._set("downloading", 5 + index * 20)
                    self._set_component(component_id, "downloading", 0)
                    journal["phase"] = "downloading"; write_journal(state_root, journal)
                    archive = downloads / component["artifactName"]
                    if archive.exists():
                        if archive.is_symlink() or _is_reparse_point(archive):
                            raise SetupError("unsafe-download-cache-entry")
                        if archive.stat().st_size != component["byteLength"] or _sha256_file(archive) != component["sha256"]:
                            archive.unlink()
                    if not archive.exists():
                        download_registered_component(
                            component,
                            archive,
                            self._cancel,
                            lambda completed, total, current_id=component_id: self._download_progress(
                                current_id, completed, total,
                            ),
                        )
                    downloaded_archives.append(archive)
                    self._set("verifying", 15 + index * 20)
                    self._set_component(component_id, "verifying", 80)
                    journal["phase"] = "verifying"; write_journal(state_root, journal)
                    self._set("extracting", 20 + index * 20)
                    self._set_component(component_id, "installing", 90)
                    journal["phase"] = "extracting"; write_journal(state_root, journal)
                    extract_validated_zip(archive, staging)
                executable = next((path for path in staging.rglob("ollama.exe") if path.is_file()), None)
                if executable is None:
                    raise SetupError("runtime-executable-missing")
                self._set("verifying", 45)
                verify_authenticode(executable)
                runtime.parent.mkdir(parents=True, exist_ok=True)
                staging.replace(runtime)
                write_runtime_integrity(state_root, runtime_version, runtime)
                for archive in downloaded_archives:
                    archive.unlink(missing_ok=True)
            verify_runtime_integrity(state_root, runtime_version, runtime)
            executable = next(path for path in runtime.rglob("ollama.exe") if path.is_file())
            verify_authenticode(executable)
            for component_id in plan["components"]:
                self._set_component(component_id, "ready", 100)
            models.mkdir(parents=True, exist_ok=True)
            managed_directories = {
                "HOME": state_root / "home",
                "USERPROFILE": state_root / "home",
                "LOCALAPPDATA": state_root / "appdata" / "local",
                "APPDATA": state_root / "appdata" / "roaming",
                "TEMP": state_root / "temp",
                "TMP": state_root / "temp",
            }
            for directory in set(managed_directories.values()):
                _assert_safe_root(directory, create=True)
            self._set("starting", 55)
            environment = {
                "OLLAMA_HOST": MANAGED_OLLAMA_HOST,
                "OLLAMA_MODELS": str(models.resolve()),
                "OLLAMA_ORIGINS": "http://127.0.0.1",
                "OLLAMA_NO_CLOUD": "1",
                "OLLAMA_NOHISTORY": "1",
                **{name: str(path.resolve()) for name, path in managed_directories.items()},
            }
            if plan["backendMode"] == "vulkan":
                environment["OLLAMA_VULKAN"] = "1"
            elif plan["backendMode"] == "cpu":
                environment["OLLAMA_LLM_LIBRARY"] = "cpu"
            self.process.start(executable, ("serve",), environment, plan["backendMode"])
            wait_for_managed_provider(
                components["ollama-windows-core"]["version"],
                process_running=self.process.is_running,
                cancelled=self._cancel.is_set,
            )
            self._set("model-download", 65)
            if registered_model_present(model):
                self._set_component(model["id"], "ready", 100)
            else:
                if shutil.disk_usage(state_root).free < plan["requiredStorageBytes"]:
                    raise SetupError("insufficient-managed-storage")
                self._set_component(model["id"], "downloading", 0)
                pull_registered_model(
                    model,
                    self._cancel,
                    lambda completed, total: self._download_progress(
                        model["id"], completed, total,
                    ),
                )
            self._set("validating", 95)
            self._set_component(model["id"], "validating", 95)
            journal["phase"] = "validating"; write_journal(state_root, journal)
            try:
                validate_managed_inference(model, plan["gpuAccelerationRequired"])
            except SetupError as error:
                if not self.process.is_running():
                    raise SetupError("managed-provider-exited-during-validation") from error
                raise
            self._set_component(model["id"], "complete", 100)
            self._set("complete", 100)
            journal["phase"] = "complete"; write_journal(state_root, journal)
            self._emit("setup", "MANAGED_SETUP_COMPLETED", "completed")
        except Exception as error:
            with self._lock:
                preserved_progress = self._status["progressPercent"]
                active_component_id = self._active_component_id
                active_component = next((
                    dict(item) for item in self._status["components"]
                    if item["componentId"] == active_component_id
                ), None)
            code = str(error) if isinstance(error, SetupError) else "setup-internal-failure"
            if code == "insufficient-managed-storage":
                self._emit("storage", "SETUP_STORAGE_INSUFFICIENT", "failed")
            elif code in {
                "portable-data-marker-write-failed",
                "portable-data-journal-write-failed",
                "portable-data-root-unavailable",
            }:
                self._emit("storage", "SETUP_STORAGE_WRITE_FAILED", "failed")
            diagnostic_code = SETUP_FAILURE_DIAGNOSTIC_CODES.get(code)
            if diagnostic_code is not None:
                self._emit("setup", diagnostic_code, "failed")
            self._emit("setup", "MANAGED_SETUP_FAILED", "failed")
            if active_component is not None:
                self._set_component(
                    active_component["componentId"],
                    "cancelled" if code == "setup-cancelled" else "failed",
                    active_component["progressPercent"],
                )
            try:
                self.process.stop()
            except Exception:
                pass
            if (
                staging is not None
                and state_root is not None
                and staging.exists()
                and _is_relative_to(staging.resolve(strict=False), state_root.resolve(strict=False))
            ):
                shutil.rmtree(staging, ignore_errors=True)
            self._set(
                "cancelled" if code == "setup-cancelled" else "failed",
                preserved_progress,
                code,
            )
            if journal is not None and state_root is not None:
                journal["phase"] = "failed"
                try:
                    write_journal(state_root, journal)
                except Exception:
                    # Status remains observable in memory even if a full or
                    # failing user volume prevents the recovery receipt.
                    pass

    def close(self) -> bool:
        self._cancel.set()
        return self.process.stop()

    def remove_managed_components(self) -> dict[str, Any]:
        """Stop only the owned runtime and remove only marker-owned portable data."""
        if self._thread is not None and self._thread.is_alive():
            raise SetupError("setup-already-running")
        self._cancel.set()
        if not self.process.stop():
            raise SetupError("managed-process-stop-failed")
        roots: list[tuple[str, Path]] = []
        if self.root.exists():
            roots.append(("portable", _owned_state_root(self.root, create=False)))
        if self.legacy_root is not None and self.legacy_root.exists():
            roots.append(("legacy", _legacy_owned_state_root(self.legacy_root)))
        if not roots:
            return {
                "removed": False,
                "managedComponentsPresent": False,
                "legacyManagedComponentsRemoved": False,
                "storageScope": "inside-extracted-folder",
            }
        for _kind, root in roots:
            _audit_removal_tree(root)
        _stop_windows_processes_beneath([root for _kind, root in roots])
        for _kind, root in roots:
            _audit_removal_tree(root)
        for _kind, root in roots:
            try:
                shutil.rmtree(root)
            except OSError as error:
                self._emit("storage", "SETUP_STORAGE_REMOVAL_FAILED", "failed")
                raise SetupError("portable-data-removal-failed") from error
            if root.exists():
                self._emit("storage", "SETUP_STORAGE_REMOVAL_FAILED", "failed")
                raise SetupError("portable-data-removal-failed")
        with self._lock:
            self._plan = None
            self._status = {
                "phase": "idle", "progressPercent": 0, "error": None,
                "components": [],
            }
            self._active_component_id = None
        return {
            "removed": True,
            "managedComponentsPresent": False,
            "legacyManagedComponentsRemoved": any(kind == "legacy" for kind, _root in roots),
            "storageScope": "inside-extracted-folder",
        }
