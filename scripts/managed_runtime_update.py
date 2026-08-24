#!/usr/bin/env python3
"""Approval-gated managed Ollama updates with a retained certified fallback."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
import shutil
import threading
import time
from typing import Any, Callable

from software_update_service import SoftwareUpdateError, download_official_asset


VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ACTIVE_RUNTIME_FILE = "active-runtime.json"
APPROVAL_TTL_SECONDS = 15 * 60


class ManagedRuntimeUpdateError(ValueError):
    """A managed runtime update or rollback failed closed."""


def read_runtime_selection(root: Path, certified: dict[str, Any]) -> dict[str, str]:
    """Read the bounded active-runtime marker or fail safely to certified."""
    fallback = {
        "version": str(certified["version"]),
        "certificationStatus": "certified",
        "sha256": str(certified["sha256"]),
    }
    try:
        path = root / ACTIVE_RUNTIME_FILE
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024:
            return fallback
        value = json.loads(path.read_text(encoding="ascii"))
        if (
            not isinstance(value, dict)
            or set(value) != {"schemaVersion", "version", "certificationStatus", "sha256"}
            or value.get("schemaVersion") != 1
            or not VERSION.fullmatch(str(value.get("version", "")))
            or value.get("certificationStatus") not in {"certified", "official-unverified"}
            or not HEX64.fullmatch(str(value.get("sha256", "")))
        ):
            return fallback
        return {
            "version": value["version"],
            "certificationStatus": value["certificationStatus"],
            "sha256": value["sha256"],
        }
    except (OSError, UnicodeError, json.JSONDecodeError):
        return fallback


class ManagedRuntimeUpdateCoordinator:
    """One memory-only approval flow around a persistent runtime selection."""

    def __init__(
        self, session_id: str, setup: Any,
        on_activated: Callable[[str], None] | None = None,
    ) -> None:
        if not isinstance(session_id, str) or len(session_id) < 16:
            raise ManagedRuntimeUpdateError("invalid-runtime-update-session")
        self.session_id = session_id
        self.setup = setup
        self.on_activated = on_activated
        self.lock = threading.Lock()
        self.cancel_event = threading.Event()
        self.pending: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, dict[str, Any]] = {}
        self.thread: threading.Thread | None = None
        self.value: dict[str, Any] = {
            "phase": "idle", "progressPercent": 0, "error": None,
            "targetVersion": None, "targetCertification": None,
            "rollbackPerformed": False,
        }

    @staticmethod
    def _certified_component() -> dict[str, Any]:
        if os.name == "nt":
            from windows_alpha import load_component_registry
            return dict(load_component_registry()["components"][0])
        from linux_alpha import load_registry
        return dict(load_registry()["components"][0])

    def _root(self, create: bool) -> Path:
        if os.name == "nt":
            from windows_alpha_setup import _owned_state_root
            return _owned_state_root(self.setup.root, create=create)
        from linux_alpha_setup import _owned_root
        return _owned_root(self.setup.root, create=create)

    def _selection_path(self, root: Path) -> Path:
        return root / ACTIVE_RUNTIME_FILE

    def _active_selection(self) -> dict[str, str]:
        try:
            root = self._root(False)
            return read_runtime_selection(root, self._certified_component())
        except Exception:
            component = self._certified_component()
            return {
                "version": str(component["version"]),
                "certificationStatus": "certified",
                "sha256": str(component["sha256"]),
            }

    def _write_selection(self, root: Path, value: dict[str, str]) -> None:
        path = self._selection_path(root)
        temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
        payload = {
            "schemaVersion": 1,
            "version": value["version"],
            "certificationStatus": value["certificationStatus"],
            "sha256": value["sha256"],
        }
        try:
            with temporary.open("x", encoding="ascii", newline="\n") as handle:
                json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
            temporary.replace(path)
        except OSError as error:
            temporary.unlink(missing_ok=True)
            raise ManagedRuntimeUpdateError("runtime-selection-write-failed") from error

    def public_status(self) -> dict[str, Any]:
        active = self._active_selection()
        certified = self._certified_component()
        with self.lock:
            value = dict(self.value)
            running = self.thread is not None and self.thread.is_alive()
        return {
            "schemaVersion": 1,
            "kind": "haven42-managed-runtime-update-status",
            "activeVersion": active["version"],
            "activeCertificationStatus": active["certificationStatus"],
            "certifiedVersion": certified["version"],
            "rollbackAvailable": active["version"] != certified["version"],
            "updateInProgress": running,
            **value,
        }

    def prepare(self, component: dict[str, Any], target: str) -> dict[str, Any]:
        if self.thread is not None and self.thread.is_alive():
            raise ManagedRuntimeUpdateError("runtime-update-already-running")
        if target not in {"latest-official", "certified"}:
            raise ManagedRuntimeUpdateError("invalid-runtime-update-target")
        certified = self._certified_component()
        if target == "latest-official":
            version = component.get("latestStableVersion")
            sha256 = component.get("sha256")
            certification = component.get("certificationStatus")
            download_bytes = component.get("downloadBytes")
            if (
                not VERSION.fullmatch(str(version or ""))
                or not HEX64.fullmatch(str(sha256 or ""))
                or certification not in {"certified", "official-unverified"}
                or type(download_bytes) is not int
                or not (
                    component.get("newerOfficialVersionAvailable") is True
                    or component.get("managedVersionIsLatest") is True
                )
            ):
                raise ManagedRuntimeUpdateError("invalid-runtime-update-component")
            retained = certified["version"]
        else:
            version = certified["version"]
            sha256 = certified["sha256"]
            certification = "certified"
            download_bytes = certified["byteLength"]
            retained = self._active_selection()["version"]
        effects = [
            "download-runtime-files" if target == "latest-official" else "select-certified-runtime",
            "stop-and-restart-owned-local-ai",
            "keep-models-and-user-data",
            "retain-certified-rollback",
        ]
        plan_id = secrets.token_urlsafe(18)
        internal = {
            "planId": plan_id, "target": target, "version": version,
            "sha256": sha256, "certificationStatus": certification,
            "downloadBytes": download_bytes, "effects": effects,
            "component": dict(component) if target == "latest-official" else None,
            "expires": time.monotonic() + APPROVAL_TTL_SECONDS,
        }
        with self.lock:
            self.pending = {plan_id: internal}
        return {
            "schemaVersion": 1,
            "kind": "haven42-managed-runtime-update-plan",
            "planId": plan_id,
            "target": target,
            "version": version,
            "certificationStatus": certification,
            "downloadBytes": download_bytes,
            "certifiedVersionRetained": retained,
            "modelsAndUserDataKept": True,
            "approvalRequired": True,
            "effects": effects,
            "warning": (
                "This official release has not yet been compatibility-tested by Haven 42."
                if certification == "official-unverified" else None
            ),
        }

    def approve(self, plan_id: object, effects: object) -> str:
        if not isinstance(plan_id, str) or not isinstance(effects, list):
            raise ManagedRuntimeUpdateError("runtime-update-approval-mismatch")
        with self.lock:
            plan = self.pending.pop(plan_id, None)
        if plan is None or plan["expires"] < time.monotonic() or effects != plan["effects"]:
            raise ManagedRuntimeUpdateError("runtime-update-approval-mismatch")
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.approvals[token] = {**plan, "expires": time.monotonic() + APPROVAL_TTL_SECONDS}
        return token

    def start(self, approval_token: object) -> dict[str, Any]:
        if not isinstance(approval_token, str):
            raise ManagedRuntimeUpdateError("invalid-runtime-update-approval")
        with self.lock:
            plan = self.approvals.pop(approval_token, None)
            if plan is None or plan["expires"] < time.monotonic():
                raise ManagedRuntimeUpdateError("invalid-runtime-update-approval")
            if self.thread is not None and self.thread.is_alive():
                raise ManagedRuntimeUpdateError("runtime-update-already-running")
            self.value = {
                "phase": "starting", "progressPercent": 0, "error": None,
                "targetVersion": plan["version"],
                "targetCertification": plan["certificationStatus"],
                "rollbackPerformed": False,
            }
            self.cancel_event.clear()
            self.thread = threading.Thread(target=self._run, args=(plan,), daemon=True)
            self.thread.start()
        return self.public_status()

    def _progress(self, phase: str, percent: int) -> None:
        with self.lock:
            self.value.update(phase=phase, progressPercent=max(0, min(100, percent)))

    def _plan(self) -> dict[str, Any]:
        plan = getattr(self.setup, "_plan", None)
        if plan is None:
            plan = getattr(self.setup, "plan", None)
        if not isinstance(plan, dict):
            raise ManagedRuntimeUpdateError("managed-setup-plan-required")
        return dict(plan)

    def _activate(self, version: str) -> None:
        plan = self._plan()
        root = self._root(False)
        runtime = root / "runtime" / version
        if os.name == "nt":
            from windows_alpha import load_model_catalog
            from windows_alpha_setup import (
                MANAGED_OLLAMA_HOST, MANAGED_OLLAMA_URL, _assert_safe_root,
                registered_model_present, validate_managed_inference,
                verify_authenticode, verify_runtime_integrity,
                wait_for_managed_provider,
            )
            verify_runtime_integrity(root, version, runtime)
            executables = [item for item in runtime.rglob("ollama.exe") if item.is_file()]
            if len(executables) != 1:
                raise ManagedRuntimeUpdateError("runtime-executable-missing")
            executable = executables[0]
            verify_authenticode(executable)
            models = root / "models"
            directories = {
                "HOME": root / "home", "USERPROFILE": root / "home",
                "LOCALAPPDATA": root / "appdata" / "local",
                "APPDATA": root / "appdata" / "roaming",
                "TEMP": root / "temp", "TMP": root / "temp",
            }
            for directory in {models, *directories.values()}:
                _assert_safe_root(directory, create=True)
            environment = {
                "OLLAMA_HOST": MANAGED_OLLAMA_HOST,
                "OLLAMA_MODELS": str(models.resolve()),
                "OLLAMA_ORIGINS": "http://127.0.0.1",
                "OLLAMA_NO_CLOUD": "1", "OLLAMA_NOHISTORY": "1",
                **{name: str(path.resolve()) for name, path in directories.items()},
            }
            if plan["backendMode"] == "vulkan":
                environment["OLLAMA_VULKAN"] = "1"
            elif plan["backendMode"] == "cpu":
                environment["OLLAMA_LLM_LIBRARY"] = "cpu"
            self.setup.process.start(executable, ("serve",), environment, plan["backendMode"])
            wait_for_managed_provider(version, process_running=self.setup.process.is_running)
            model = next(item for item in load_model_catalog()["models"] if item["id"] == plan["modelId"])
            if not registered_model_present(model):
                raise ManagedRuntimeUpdateError("registered-model-not-present")
            validate_managed_inference(model, plan["gpuAccelerationRequired"])
            return
        from linux_alpha import load_catalog
        from linux_alpha_setup import _model_record, _validate_inference, _verify_integrity, _wait_provider
        _verify_integrity(root, version, runtime)
        self.setup._start_runtime(root, runtime, plan["backendMode"])
        _wait_provider(version, self.setup.process, self.cancel_event)
        model = next(item for item in load_catalog()["models"] if item["id"] == plan["modelId"])
        if not _model_record(model):
            raise ManagedRuntimeUpdateError("managed-model-not-present")
        _validate_inference(model, plan["gpuAccelerationRequired"])

    def _install_official(self, plan: dict[str, Any], root: Path) -> None:
        component = plan["component"]
        version = plan["version"]
        runtime = root / "runtime" / version
        if runtime.exists():
            return
        downloads = root / "downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        archive = downloads / f"update-{version}-{component['artifactName']}"
        if archive.exists():
            archive.unlink()
        self._progress("downloading", 5)
        download_official_asset(
            component, archive, self.cancel_event,
            lambda done, total: self._progress("downloading", 5 + done * 55 // total),
        )
        staging = root / "staging" / f"runtime-update-{secrets.token_hex(8)}"
        self._progress("extracting", 65)
        try:
            if os.name == "nt":
                from windows_alpha_setup import extract_validated_zip, verify_authenticode, write_runtime_integrity
                extract_validated_zip(archive, staging)
                executables = [item for item in staging.rglob("ollama.exe") if item.is_file()]
                if len(executables) != 1:
                    raise ManagedRuntimeUpdateError("runtime-executable-missing")
                verify_authenticode(executables[0])
                runtime.parent.mkdir(parents=True, exist_ok=True)
                staging.replace(runtime)
                write_runtime_integrity(root, version, runtime)
            else:
                from linux_alpha_runtime import extract_official_update_archive
                from linux_alpha_setup import _write_integrity
                extract_official_update_archive(archive, staging, component)
                runtime.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                staging.replace(runtime)
                _write_integrity(root, version, runtime)
        finally:
            archive.unlink(missing_ok=True)
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    def _run(self, plan: dict[str, Any]) -> None:
        previous = self._active_selection()
        root: Path | None = None
        try:
            root = self._root(True)
            self.setup.process.stop()
            if plan["target"] == "latest-official":
                self._install_official(plan, root)
            self._progress("validating", 80)
            self._activate(plan["version"])
            if self.on_activated is not None:
                self.on_activated(plan["version"])
            self._write_selection(root, {
                "version": plan["version"],
                "certificationStatus": plan["certificationStatus"],
                "sha256": plan["sha256"],
            })
            self._progress("complete", 100)
        except Exception as error:
            rollback_performed = False
            try:
                self.setup.process.stop()
                self._activate(previous["version"])
                if self.on_activated is not None:
                    self.on_activated(previous["version"])
                rollback_performed = True
            except Exception:
                pass
            with self.lock:
                self.value.update(
                    phase="failed", error=(
                        str(error) if isinstance(error, (ManagedRuntimeUpdateError, SoftwareUpdateError))
                        else "runtime-update-failed"
                    ), rollbackPerformed=rollback_performed,
                )
