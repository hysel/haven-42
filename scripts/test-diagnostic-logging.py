#!/usr/bin/env python3
"""Hostile, privacy, lifecycle, and bounds tests for local diagnostics."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("diagnostic_logging", ROOT / "scripts/diagnostic_logging.py")
assert SPEC and SPEC.loader
LOGS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOGS)


def log_root(parent: Path) -> Path:
    return parent / "Haven42-Logs"


def assert_private(summary: dict) -> None:
    assert summary["storageDirectoryName"] == "Haven42-Logs"
    assert summary["storageScope"] == "inside-extracted-folder"
    assert summary["privacy"] and all(value is False for value in summary["privacy"].values())
    assert len(summary["events"]) <= 100
    expected = {"schemaVersion", "timestamp", "eventId", "category", "code", "outcome", "appVersion"}
    assert all(set(event) == expected for event in summary["events"])


def main() -> int:
    checks = 0
    secret = "PROMPT_SECRET_ENDPOINT_PATH_TOKEN"
    with tempfile.TemporaryDirectory(prefix="haven42-diagnostics-") as raw:
        parent = Path(raw)
        logger = LOGS.DiagnosticLogger("0.4-alpha-1", log_root(parent))
        summary = logger.summary()
        assert summary["available"] is True and summary["removedForSession"] is False
        assert_private(summary)
        checks += 3

        assert logger.record("setup", "READINESS_SCAN_COMPLETED", "completed") is True
        assert logger.record(
            "setup",
            "SETUP_COMPONENT_OLLAMA_WINDOWS_AMD_ROCM_0_32_5_ROCM_7_1_SELECTED",
            "observed",
        ) is True
        assert logger.record("storage", "SETUP_STORAGE_WRITE_FAILED", "failed") is True
        assert logger.record("invalid", "READINESS_SCAN_COMPLETED", "completed") is False
        assert logger.record("setup", "bad-code", "completed") is False
        try:
            logger.record("setup", "VALID_CODE", "completed", secret)
            raise AssertionError("arbitrary diagnostic details were accepted")
        except TypeError:
            pass
        serialized = "\n".join(
            item.read_text(encoding="utf-8")
            for item in log_root(parent).iterdir()
            if item.is_file()
        )
        assert secret not in serialized
        checks += 7

        real_open = os.open
        def deny_event_write(path, flags, mode=0o777):
            if Path(path).name == LOGS.EVENT_FILE_NAME and flags & os.O_WRONLY:
                raise OSError("simulated bounded storage failure")
            return real_open(path, flags, mode)
        with patch.object(LOGS.os, "open", side_effect=deny_event_write):
            assert logger.record("storage", "DIAGNOSTIC_WRITE_PROBE", "observed") is False
        assert logger.summary()["available"] is False
        assert logger.record("storage", "DIAGNOSTIC_WRITE_RECOVERED", "completed") is True
        assert logger.summary()["available"] is True
        checks += 4

        old_limit = LOGS.MAX_EVENT_FILE_BYTES
        LOGS.MAX_EVENT_FILE_BYTES = 900
        try:
            for _ in range(30):
                assert logger.record("text", "TEXT_GENERATION_COMPLETED", "completed")
        finally:
            LOGS.MAX_EVENT_FILE_BYTES = old_limit
        assert (log_root(parent) / LOGS.ROTATED_EVENT_FILE_NAME).is_file()
        assert len(logger.summary()["events"]) <= 100
        checks += 2

        answer = logger.save_answer_report(
            "incorrect",
            "general.chat",
            "qwen3.5:9b",
            "a" * 64,
            "0.32.5",
            "The date appears wrong; no chat content included.",
        )
        assert answer["saved"] is True and answer["automaticUpload"] is False
        answer_path = log_root(parent) / LOGS.REPORT_DIRECTORY_NAME / answer["fileName"]
        answer_payload = json.loads(answer_path.read_text(encoding="utf-8"))
        assert answer_payload["eventReference"] == answer["eventReference"]
        assert answer_payload["containsPrompt"] is False and answer_payload["containsResponse"] is False
        assert answer_payload["containsAttachments"] is False and answer_payload["automaticUpload"] is False
        try:
            logger.save_answer_report(
                "incorrect", "general.chat", "qwen3.5:9b", "a" * 64, "0.32.5", "x" * 301,
            )
            raise AssertionError("oversized answer-report note was accepted")
        except LOGS.DiagnosticLogError as error:
            assert str(error) == "invalid-answer-report"
        report = logger.save_support_report()
        assert report["saved"] is True and LOGS.REPORT_NAME.fullmatch(report["fileName"])
        report_path = log_root(parent) / LOGS.REPORT_DIRECTORY_NAME / report["fileName"]
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        assert payload["automaticUpload"] is False and payload["containsUserContent"] is False
        assert secret not in report_path.read_text(encoding="utf-8")
        for _ in range(LOGS.MAX_REPORT_FILES - 2):
            logger.save_support_report()
        try:
            logger.save_support_report()
            raise AssertionError("support report count was unbounded")
        except LOGS.DiagnosticLogError as error:
            assert str(error) == "diagnostic-report-limit-reached"
        logger.clear_events()
        assert report_path.is_file() and logger.summary()["eventCount"] == 0
        checks += 12

        removal = logger.remove_all()
        assert removal == {"removed": True, "directoryName": "Haven42-Logs"}
        assert not log_root(parent).exists()
        removed = logger.summary()
        assert removed["removedForSession"] is True and removed["available"] is False
        assert logger.record("application", "SHOULD_NOT_RECREATE", "observed") is False
        logger.close()
        assert not log_root(parent).exists()
        checks += 5

    with tempfile.TemporaryDirectory(prefix="haven42-diagnostics-unowned-") as raw:
        root = log_root(Path(raw))
        root.mkdir()
        (root / "unrelated.txt").write_text("leave me", encoding="utf-8")
        logger = LOGS.DiagnosticLogger("0.4-alpha-1", root)
        assert logger.summary()["available"] is False
        assert (root / "unrelated.txt").read_text(encoding="utf-8") == "leave me"
        checks += 2

    with tempfile.TemporaryDirectory(prefix="haven42-diagnostics-corrupt-") as raw:
        root = log_root(Path(raw))
        logger = LOGS.DiagnosticLogger("0.4-alpha-1", root)
        (root / LOGS.EVENT_FILE_NAME).write_text('{"unsafe":"content"}\n', encoding="utf-8")
        summary = logger.summary()
        assert summary["available"] is False and summary["events"] == []
        logger.close()
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-diagnostics-session-") as raw:
        root = log_root(Path(raw))
        first = LOGS.DiagnosticLogger("0.4-alpha-1", root)
        second = LOGS.DiagnosticLogger("0.4-alpha-1", root)
        assert any(event["code"] == "PREVIOUS_SESSION_UNCLEAN" for event in second.summary()["events"])
        second.close()
        first.close()
        checks += 1

    print(f"Diagnostic logging security tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
