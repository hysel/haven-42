#!/usr/bin/env python3
"""Security and lifecycle tests for the synthetic conversation store."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("history_store", ROOT / "scripts/conversation-history-development-store.py")
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


def message(identifier: str = "msg-1", ordinal: int = 1, content: str = "Synthetic message.") -> dict:
    return {"messageId": identifier, "ordinal": ordinal, "role": "user", "content": content, "modelId": "model-one", "providerId": "provider-one", "createdAtUtc": "2026-01-01T00:00:01Z"}


def attachment() -> dict:
    return {"name": "synthetic.txt", "mediaType": "text/plain", "sizeBytes": 12, "sha256": "a" * 64, "availability": "available-at-send"}


def seed(store) -> None:
    store.create_conversation("conv-1", "Synthetic project", "2026-01-01T00:00:00Z", "30-days", "model-one", "provider-one")
    store.append_message("conv-1", message(), [attachment()])


def main() -> None:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-history-store-") as temporary:
        directory = Path(temporary).resolve(); store = MODULE.DevelopmentStore(directory)
        try:
            assert store.connection.execute("PRAGMA user_version").fetchone()[0] == 2
            assert store.connection.execute("PRAGMA secure_delete").fetchone()[0] == 1; checks += 1
            seed(store)
            store.rename_conversation("conv-1", "Renamed synthetic project", "2026-01-01T00:00:02Z")
            assert store.list_conversations()[0]["title"].startswith("Renamed"); checks += 1
            assert store.search_conversations("Renamed")[0]["conversation_id"] == "conv-1"
            assert store.search_conversations("%") == []; checks += 1
            messages = store.list_messages("conv-1")
            assert messages[0]["model_id"] == "model-one" and messages[0]["provider_id"] == "provider-one"
            assert set(messages[0]["attachments"][0]) == {"ordinal", "name", "media_type", "size_bytes", "sha256", "availability"}; checks += 1
            encoded = store.export_sanitized()
            assert b"databasePath" not in encoded and b"contentBase64" not in encoded; checks += 1
            manifest = store.backup(directory / "history-backup.sqlite3"); store.verify_backup(directory, manifest); checks += 1
            hostile = dict(manifest); hostile["sha256"] = "0" * 64
            try: store.verify_backup(directory, hostile); raise AssertionError("corrupt manifest accepted")
            except MODULE.StoreError: pass
            checks += 1
            store.delete_conversation("conv-1")
            assert store.list_conversations() == [] and store.connection.execute("SELECT count(*) FROM attachment_snapshots").fetchone()[0] == 0; checks += 1
            store.import_sanitized(encoded)
            assert len(store.list_messages("conv-1")) == 1; checks += 1
            store.clear_all(); assert store.list_conversations() == []; checks += 1

            hostile_export = json.loads(encoded)
            hostile_export["conversations"][0]["path"] = "forbidden"
            try: store.import_sanitized(json.dumps(hostile_export).encode()); raise AssertionError("path import accepted")
            except MODULE.StoreError: pass
            checks += 1

            # Parameterization: SQL syntax remains inert content.
            store.create_conversation("conv-2", "SQL inert", "2026-01-01T00:00:00Z", "forever", "model-one", "provider-one")
            store.append_message("conv-2", message("msg-2", 1, "'); DROP TABLE conversations; --"), [])
            assert store.connection.execute("SELECT count(*) FROM conversations").fetchone()[0] == 1; checks += 1

        finally:
            store.cleanup()
        assert list(directory.iterdir()) == []; checks += 1

    # Migration rollback leaves schema v1 and no added column.
    with tempfile.TemporaryDirectory(prefix="haven42-history-migration-") as temporary:
        directory = Path(temporary).resolve(); path = directory / "history.sqlite3"
        connection = MODULE._connect(path); connection.executescript(MODULE.SCHEMA_V1)
        dummy = object.__new__(MODULE.DevelopmentStore); dummy.connection = connection
        try:
            try: dummy.migrate_to_current(fail=True); raise AssertionError("failed migration committed")
            except MODULE.StoreError: pass
            assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
            assert "renamed_at_utc" not in {row[1] for row in connection.execute("PRAGMA table_info(conversations)")}; checks += 1
        finally: connection.close(); path.unlink()

    # Corrupt database fails without reset.
    with tempfile.TemporaryDirectory(prefix="haven42-history-corrupt-") as temporary:
        path = Path(temporary) / "corrupt.sqlite3"; path.write_bytes(b"not sqlite")
        try:
            MODULE._connect(path)
            raise AssertionError("corruption accepted")
        except sqlite3.DatabaseError: pass
        assert path.read_bytes() == b"not sqlite"; checks += 1

    # Locked database fails boundedly, and simulated disk-full writes nothing.
    with tempfile.TemporaryDirectory(prefix="haven42-history-busy-") as temporary:
        directory = Path(temporary).resolve(); store = MODULE.DevelopmentStore(directory)
        second = MODULE._connect(store.path, timeout=0.01)
        try:
            store.connection.execute("BEGIN EXCLUSIVE")
            try: second.execute("INSERT INTO metadata VALUES('x','y')"); raise AssertionError("locked write accepted")
            except sqlite3.OperationalError: pass
            store.connection.execute("ROLLBACK"); checks += 1
        finally: second.close(); store.cleanup()
    with tempfile.TemporaryDirectory(prefix="haven42-history-full-") as temporary:
        store = MODULE.DevelopmentStore(Path(temporary).resolve(), quota_check=lambda _size: False)
        try:
            store.create_conversation("conv-1", "Synthetic", "2026-01-01T00:00:00Z", "30-days", "model-one", "provider-one")
            try: store.append_message("conv-1", message(), []); raise AssertionError("disk-full write accepted")
            except MODULE.StoreError: pass
            assert store.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 0; checks += 1
        finally: store.cleanup()

    # Interrupted multi-row append rolls back the message.
    with tempfile.TemporaryDirectory(prefix="haven42-history-interrupt-") as temporary:
        def interrupted(): raise RuntimeError("injected interruption")
        store = MODULE.DevelopmentStore(Path(temporary).resolve(), failure_hook=interrupted)
        try:
            store.create_conversation("conv-1", "Synthetic", "2026-01-01T00:00:00Z", "30-days", "model-one", "provider-one")
            try: store.append_message("conv-1", message(), [attachment()]); raise AssertionError("interruption accepted")
            except RuntimeError: pass
            assert store.connection.execute("SELECT count(*) FROM messages").fetchone()[0] == 0; checks += 1
        finally: store.cleanup()

    contract = MODULE.CONTRACT
    assert contract["database"]["plaintextPromotionAllowed"] is False
    assert contract["encryption"]["admitted"] is False
    assert contract["encryption"]["unavailableDecision"] == "private-session-no-write"
    assert not any(contract["activation"].values()); checks += 1
    spec = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "conversation-history-development-store" not in spec and "conversation-history-store-contract" not in spec; checks += 1
    print(f"Conversation history synthetic store passed {checks} security and lifecycle checks.")


if __name__ == "__main__": main()
