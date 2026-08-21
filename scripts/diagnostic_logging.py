#!/usr/bin/env python3
"""Bounded, sanitized, portable diagnostic events for Haven 42 Alpha."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import threading
from typing import Any

from windows_user_paths import portable_install_root


LOG_DIRECTORY_NAME = "Haven42-Logs"
MARKER_NAME = ".haven42-logs.json"
EVENT_FILE_NAME = "events.jsonl"
ROTATED_EVENT_FILE_NAME = "events.1.jsonl"
SESSION_MARKER_NAME = ".session-active"
REPORT_DIRECTORY_NAME = "Reports"
MAX_EVENT_FILE_BYTES = 256 * 1024
MAX_VISIBLE_EVENTS = 100
MAX_REPORT_FILES = 5
MAX_REPORT_FILE_BYTES = 128 * 1024
MAX_EVENT_CODE_LENGTH = 80
ALLOWED_CATEGORIES = {"application", "provider", "setup", "text", "storage", "security"}
ALLOWED_OUTCOMES = {"started", "completed", "cancelled", "failed", "warning", "observed"}
EVENT_CODE = re.compile(r"[A-Z][A-Z0-9_]{2,79}")
REPORT_NAME = re.compile(r"(?:support|answer)-report-[a-f0-9]{16}\.json")
EVENT_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
ANSWER_REPORT_CATEGORIES = {"incorrect", "unsafe", "unclear", "formatting", "other"}
ANSWER_REPORT_CAPABILITIES = {"general.chat", "content.write", "content.summarize"}
MODEL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}")
MODEL_DIGEST = re.compile(r"[a-f0-9]{64}")
RUNTIME_VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}")
MAX_TESTER_NOTE_CHARACTERS = 300
MARKER = {
    "schemaVersion": 1,
    "kind": "haven42-sanitized-diagnostic-root",
    "directoryName": LOG_DIRECTORY_NAME,
}


class DiagnosticLogError(ValueError):
    pass


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class DiagnosticLogger:
    """Write only fixed-schema metadata; arbitrary caller details are impossible."""

    def __init__(self, app_version: str, root: Path | None = None):
        if not re.fullmatch(r"[0-9A-Za-z.-]{1,40}", app_version):
            raise DiagnosticLogError("invalid-diagnostic-app-version")
        self.app_version = app_version
        self.root = (root if root is not None else portable_install_root() / LOG_DIRECTORY_NAME).absolute()
        self._lock = threading.Lock()
        self._available = False
        self._error: str | None = None
        self._closed = False
        self._removed_for_session = False
        try:
            self._ensure_root()
            session_marker = self.root / SESSION_MARKER_NAME
            previous_unclean = session_marker.exists()
            if previous_unclean and _is_link_or_reparse(session_marker):
                raise DiagnosticLogError("diagnostic-session-link-rejected")
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(session_marker, flags, 0o600)
            with os.fdopen(descriptor, "w", encoding="ascii") as handle:
                handle.write("active\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._available = True
            if previous_unclean:
                self.record("application", "PREVIOUS_SESSION_UNCLEAN", "warning")
            self.record("application", "APPLICATION_STARTED", "started")
        except (OSError, DiagnosticLogError) as error:
            self._error = str(error) or "diagnostic-root-unavailable"

    def _ensure_root(self) -> None:
        if self.root.name != LOG_DIRECTORY_NAME or not self.root.is_absolute():
            raise DiagnosticLogError("invalid-diagnostic-root")
        if self.root.exists() and _is_link_or_reparse(self.root):
            raise DiagnosticLogError("diagnostic-root-link-rejected")
        self.root.mkdir(mode=0o700, parents=False, exist_ok=True)
        marker = self.root / MARKER_NAME
        if marker.exists():
            if _is_link_or_reparse(marker):
                raise DiagnosticLogError("diagnostic-marker-link-rejected")
            try:
                value = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise DiagnosticLogError("invalid-diagnostic-marker") from error
            if value != MARKER:
                raise DiagnosticLogError("invalid-diagnostic-marker")
        else:
            unexpected = [item for item in self.root.iterdir() if item.name != SESSION_MARKER_NAME]
            if unexpected:
                raise DiagnosticLogError("unowned-diagnostic-root")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(marker, flags, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(MARKER, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def _event(self, category: str, code: str, outcome: str) -> dict[str, Any]:
        if category not in ALLOWED_CATEGORIES or outcome not in ALLOWED_OUTCOMES:
            raise DiagnosticLogError("invalid-diagnostic-event")
        if not isinstance(code, str) or not EVENT_CODE.fullmatch(code):
            raise DiagnosticLogError("invalid-diagnostic-event-code")
        return {
            "schemaVersion": 1,
            "timestamp": _timestamp(),
            "eventId": secrets.token_hex(8),
            "category": category,
            "code": code,
            "outcome": outcome,
            "appVersion": self.app_version,
        }

    def _rotate_if_needed(self, incoming_bytes: int) -> None:
        current = self.root / EVENT_FILE_NAME
        if current.exists() and _is_link_or_reparse(current):
            raise DiagnosticLogError("diagnostic-event-link-rejected")
        if current.exists() and current.stat().st_size + incoming_bytes > MAX_EVENT_FILE_BYTES:
            rotated = self.root / ROTATED_EVENT_FILE_NAME
            if rotated.exists():
                if _is_link_or_reparse(rotated):
                    raise DiagnosticLogError("diagnostic-event-link-rejected")
                rotated.unlink()
            os.replace(current, rotated)

    def record(self, category: str, code: str, outcome: str) -> bool:
        try:
            event = self._event(category, code, outcome)
        except DiagnosticLogError:
            return False
        data = (json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
        with self._lock:
            if self._closed or self._removed_for_session:
                return False
            try:
                self._write_event(data)
                self._available = True
                self._error = None
                return True
            except (OSError, DiagnosticLogError) as error:
                self._available = False
                self._error = str(error) or "diagnostic-write-failed"
                return False

    def _write_event(self, data: bytes) -> None:
        self._ensure_root()
        self._rotate_if_needed(len(data))
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.root / EVENT_FILE_NAME, flags, 0o600)
        with os.fdopen(descriptor, "ab", buffering=0) as handle:
            handle.write(data)
            os.fsync(handle.fileno())

    def _read_events(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for name in (ROTATED_EVENT_FILE_NAME, EVENT_FILE_NAME):
            path = self.root / name
            if not path.exists():
                continue
            if _is_link_or_reparse(path) or path.stat().st_size > MAX_EVENT_FILE_BYTES:
                raise DiagnosticLogError("unsafe-diagnostic-event-file")
            for line in path.read_text(encoding="utf-8").splitlines():
                value = json.loads(line)
                if (
                    not isinstance(value, dict)
                    or set(value) != {"schemaVersion", "timestamp", "eventId", "category", "code", "outcome", "appVersion"}
                    or value.get("schemaVersion") != 1
                    or value.get("category") not in ALLOWED_CATEGORIES
                    or value.get("outcome") not in ALLOWED_OUTCOMES
                    or not isinstance(value.get("code"), str)
                    or not EVENT_CODE.fullmatch(value["code"])
                    or not isinstance(value.get("eventId"), str)
                    or not re.fullmatch(r"[a-f0-9]{16}", value["eventId"])
                    or not isinstance(value.get("timestamp"), str)
                    or not EVENT_TIMESTAMP.fullmatch(value["timestamp"])
                    or value.get("appVersion") != self.app_version
                ):
                    raise DiagnosticLogError("invalid-diagnostic-event-file")
                events.append(value)
        return events[-MAX_VISIBLE_EVENTS:]

    def summary(self) -> dict[str, Any]:
        with self._lock:
            if self._removed_for_session:
                events = []
                available = False
                error = None
            else:
                try:
                    self._ensure_root()
                    events = self._read_events()
                    available = self._available
                    error = None if available else "diagnostic-data-unavailable"
                except (OSError, UnicodeDecodeError, json.JSONDecodeError, DiagnosticLogError):
                    events = []
                    available = False
                    error = "diagnostic-data-unavailable"
            return {
                "schemaVersion": 1,
                "kind": "haven42-sanitized-diagnostics",
                "available": available,
                "error": error,
                "removedForSession": self._removed_for_session,
                "storageScope": "inside-extracted-folder",
                "storageDirectoryName": LOG_DIRECTORY_NAME,
                "eventCount": len(events),
                "events": events,
                "privacy": {
                    "promptsRecorded": False,
                    "responsesRecorded": False,
                    "attachmentDataRecorded": False,
                    "credentialsRecorded": False,
                    "endpointsRecorded": False,
                    "identityRecorded": False,
                    "pathsRecorded": False,
                    "commandsRecorded": False,
                    "rawChildOutputRecorded": False,
                    "automaticUpload": False,
                },
            }

    def save_support_report(self) -> dict[str, Any]:
        with self._lock:
            if self._removed_for_session:
                raise DiagnosticLogError("diagnostics-removed-for-session")
            self._ensure_root()
            events = self._read_events()
            reports = self.root / REPORT_DIRECTORY_NAME
            if reports.exists() and _is_link_or_reparse(reports):
                raise DiagnosticLogError("diagnostic-report-link-rejected")
            reports.mkdir(mode=0o700, exist_ok=True)
            existing_reports = list(reports.iterdir())
            if any(
                not item.is_file()
                or _is_link_or_reparse(item)
                or not REPORT_NAME.fullmatch(item.name)
                or item.stat().st_size > MAX_REPORT_FILE_BYTES
                for item in existing_reports
            ):
                raise DiagnosticLogError("unsafe-diagnostic-report-entry")
            if len(existing_reports) >= MAX_REPORT_FILES:
                raise DiagnosticLogError("diagnostic-report-limit-reached")
            name = f"support-report-{secrets.token_hex(8)}.json"
            report = {
                "schemaVersion": 1,
                "kind": "haven42-sanitized-support-report",
                "createdAt": _timestamp(),
                "appVersion": self.app_version,
                "events": events,
                "containsUserContent": False,
                "automaticUpload": False,
            }
            target = reports / name
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            descriptor = os.open(target, flags, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if target.stat().st_size > MAX_REPORT_FILE_BYTES:
                target.unlink(missing_ok=True)
                raise DiagnosticLogError("diagnostic-report-too-large")
            return {"saved": True, "fileName": name, "directoryName": LOG_DIRECTORY_NAME}

    def save_answer_report(
        self,
        category: str,
        capability_id: str,
        model: str,
        model_digest: str,
        runtime_version: str,
        tester_note: str,
    ) -> dict[str, Any]:
        if (
            category not in ANSWER_REPORT_CATEGORIES
            or capability_id not in ANSWER_REPORT_CAPABILITIES
            or not isinstance(model, str) or not MODEL_NAME.fullmatch(model)
            or not isinstance(model_digest, str) or not MODEL_DIGEST.fullmatch(model_digest)
            or not isinstance(runtime_version, str) or not RUNTIME_VERSION.fullmatch(runtime_version)
            or not isinstance(tester_note, str)
            or len(tester_note) > MAX_TESTER_NOTE_CHARACTERS
            or any(ord(character) < 32 and character not in "\n\t" for character in tester_note)
        ):
            raise DiagnosticLogError("invalid-answer-report")
        with self._lock:
            if self._removed_for_session:
                raise DiagnosticLogError("diagnostics-removed-for-session")
            reports = self.root / REPORT_DIRECTORY_NAME
            if reports.exists() and _is_link_or_reparse(reports):
                raise DiagnosticLogError("diagnostic-report-link-rejected")
            reports.mkdir(mode=0o700, exist_ok=True)
            existing_reports = list(reports.iterdir())
            if any(
                not item.is_file()
                or _is_link_or_reparse(item)
                or not REPORT_NAME.fullmatch(item.name)
                or item.stat().st_size > MAX_REPORT_FILE_BYTES
                for item in existing_reports
            ):
                raise DiagnosticLogError("unsafe-diagnostic-report-entry")
            if len(existing_reports) >= MAX_REPORT_FILES:
                raise DiagnosticLogError("diagnostic-report-limit-reached")
            event = self._event("text", "ANSWER_REPORT_REQUESTED", "observed")
            event_data = (json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
            self._write_event(event_data)
            name = f"answer-report-{secrets.token_hex(8)}.json"
            report = {
                "schemaVersion": 1,
                "kind": "haven42-sanitized-answer-report",
                "createdAt": _timestamp(),
                "appVersion": self.app_version,
                "eventReference": event["eventId"],
                "category": category,
                "capabilityId": capability_id,
                "model": model,
                "modelDigest": model_digest,
                "runtimeVersion": runtime_version,
                "testerNote": tester_note or None,
                "containsPrompt": False,
                "containsResponse": False,
                "containsAttachments": False,
                "automaticUpload": False,
            }
            target = reports / name
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(target, flags, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if target.stat().st_size > MAX_REPORT_FILE_BYTES:
                target.unlink(missing_ok=True)
                raise DiagnosticLogError("diagnostic-report-too-large")
            self._available = True
            self._error = None
            return {
                "saved": True,
                "fileName": name,
                "directoryName": LOG_DIRECTORY_NAME,
                "eventReference": event["eventId"],
                "automaticUpload": False,
            }

    def clear_events(self) -> dict[str, Any]:
        with self._lock:
            if self._removed_for_session:
                raise DiagnosticLogError("diagnostics-removed-for-session")
            self._ensure_root()
            for name in (EVENT_FILE_NAME, ROTATED_EVENT_FILE_NAME):
                path = self.root / name
                if path.exists():
                    if _is_link_or_reparse(path):
                        raise DiagnosticLogError("diagnostic-event-link-rejected")
                    path.unlink()
            return {"cleared": True, "reportsPreserved": True, "directoryName": LOG_DIRECTORY_NAME}

    def remove_all(self) -> dict[str, Any]:
        with self._lock:
            self._ensure_root()
            allowed = {MARKER_NAME, EVENT_FILE_NAME, ROTATED_EVENT_FILE_NAME, SESSION_MARKER_NAME, REPORT_DIRECTORY_NAME}
            for item in self.root.iterdir():
                if item.name not in allowed or _is_link_or_reparse(item):
                    raise DiagnosticLogError("unsafe-diagnostic-root-entry")
                if item.name == REPORT_DIRECTORY_NAME:
                    if not item.is_dir():
                        raise DiagnosticLogError("unsafe-diagnostic-root-entry")
                    for report in item.iterdir():
                        if not report.is_file() or _is_link_or_reparse(report) or not REPORT_NAME.fullmatch(report.name):
                            raise DiagnosticLogError("unsafe-diagnostic-report-entry")
            if _is_link_or_reparse(self.root):
                raise DiagnosticLogError("diagnostic-root-link-rejected")
            shutil.rmtree(self.root)
            self._available = False
            self._removed_for_session = True
            return {"removed": True, "directoryName": LOG_DIRECTORY_NAME}

    def close(self) -> None:
        with self._lock:
            if self._closed or self._removed_for_session:
                self._closed = True
                return
        self.record("application", "APPLICATION_STOPPED", "completed")
        with self._lock:
            marker = self.root / SESSION_MARKER_NAME
            try:
                if marker.exists() and not _is_link_or_reparse(marker):
                    marker.unlink()
            except OSError:
                pass
            self._closed = True
