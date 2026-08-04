#!/usr/bin/env python3
"""Synthetic temporary conversation store; not imported by Haven 42 runtime."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "config/conversation-history-store-contract.json").read_text(encoding="utf-8"))
IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
DIGEST = re.compile(r"[0-9a-f]{64}")
UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


class StoreError(ValueError):
    pass


SCHEMA_V1 = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE conversations (
  conversation_id TEXT PRIMARY KEY,
  title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 200),
  created_at_utc TEXT NOT NULL,
  retention_policy TEXT NOT NULL CHECK(retention_policy IN ('30-days','90-days','forever')),
  model_id TEXT NOT NULL,
  provider_id TEXT NOT NULL
);
CREATE TABLE messages (
  message_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  ordinal INTEGER NOT NULL CHECK(ordinal > 0),
  role TEXT NOT NULL CHECK(role IN ('system','user','assistant')),
  content TEXT NOT NULL CHECK(length(content) <= 200000),
  model_id TEXT NOT NULL,
  provider_id TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  UNIQUE(conversation_id, ordinal)
);
CREATE TABLE attachment_snapshots (
  message_id TEXT NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
  ordinal INTEGER NOT NULL,
  name TEXT NOT NULL,
  media_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
  sha256 TEXT NOT NULL,
  availability TEXT NOT NULL CHECK(availability IN ('available-at-send','unavailable-at-send')),
  PRIMARY KEY(message_id, ordinal)
);
PRAGMA user_version=1;
"""


def _connect(path: Path, *, timeout: float = 0.05) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=timeout, isolation_level=None)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.execute("PRAGMA secure_delete=ON")
        connection.enable_load_extension(False)
        return connection
    except Exception:
        connection.close()
        raise


def _validate_text(value: Any, maximum: int, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise StoreError(f"invalid-{label}")
    return value


def _validate_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        raise StoreError(f"invalid-{label}")
    return value


def _scan_forbidden(value: Any) -> None:
    if isinstance(value, dict):
        if set(value) & set(CONTRACT["forbiddenImportFields"]):
            raise StoreError("forbidden-import-field")
        for child in value.values(): _scan_forbidden(child)
    elif isinstance(value, list):
        for child in value: _scan_forbidden(child)


class DevelopmentStore:
    def __init__(self, directory: Path, *, quota_check: Callable[[int], bool] | None = None, failure_hook: Callable[[], None] | None = None):
        if CONTRACT["status"] != "synthetic-temporary-development-only" or any(CONTRACT["activation"].values()):
            raise StoreError("unsafe-contract")
        if not directory.is_absolute() or not directory.is_dir() or directory.is_symlink() or any(directory.iterdir()):
            raise StoreError("unsafe-development-directory")
        self.directory = directory
        self.path = directory / "history.sqlite3"
        self.connection = _connect(self.path)
        self.quota_check = quota_check or (lambda _size: True)
        self.failure_hook = failure_hook or (lambda: None)
        self.connection.executescript(SCHEMA_V1)
        self.migrate_to_current()

    def close(self) -> None:
        self.connection.close()

    def cleanup(self) -> None:
        self.close()
        for name in ("history.sqlite3", "history-backup.sqlite3"):
            for suffix in ("", "-journal", "-shm", "-wal"):
                candidate = self.directory / f"{name}{suffix}"
                if candidate.exists() and not candidate.is_symlink(): candidate.unlink()

    def migrate_to_current(self, *, fail: bool = False) -> None:
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version > CONTRACT["database"]["currentSchemaVersion"]:
            raise StoreError("downgrade-rejected")
        if version == 1:
            try:
                self.connection.execute("BEGIN IMMEDIATE")
                self.connection.execute("ALTER TABLE conversations ADD COLUMN renamed_at_utc TEXT")
                if fail: raise StoreError("injected-migration-failure")
                self.connection.execute("PRAGMA user_version=2")
                self.connection.execute("COMMIT")
            except Exception:
                self.connection.execute("ROLLBACK")
                raise
        if self.connection.execute("PRAGMA user_version").fetchone()[0] != 2:
            raise StoreError("schema-version-mismatch")

    def create_conversation(self, conversation_id: str, title: str, created: str, retention: str, model: str, provider: str) -> None:
        _validate_id(conversation_id, "conversation-id"); _validate_text(title, 200, "title")
        if UTC.fullmatch(created) is None or retention not in {"30-days", "90-days", "forever"}: raise StoreError("invalid-conversation-metadata")
        _validate_id(model, "model-id"); _validate_id(provider, "provider-id")
        self.connection.execute("INSERT INTO conversations(conversation_id,title,created_at_utc,retention_policy,model_id,provider_id) VALUES(?,?,?,?,?,?)", (conversation_id, title, created, retention, model, provider))

    def rename_conversation(self, conversation_id: str, title: str, renamed: str) -> None:
        _validate_id(conversation_id, "conversation-id"); _validate_text(title, 200, "title")
        if UTC.fullmatch(renamed) is None: raise StoreError("invalid-renamed-time")
        cursor = self.connection.execute("UPDATE conversations SET title=?,renamed_at_utc=? WHERE conversation_id=?", (title, renamed, conversation_id))
        if cursor.rowcount != 1: raise StoreError("conversation-not-found")

    def list_conversations(self) -> list[dict]:
        return [dict(row) for row in self.connection.execute("SELECT conversation_id,title,created_at_utc,retention_policy,model_id,provider_id,renamed_at_utc FROM conversations ORDER BY created_at_utc,conversation_id")]

    def search_conversations(self, term: str) -> list[dict]:
        term = _validate_text(term, CONTRACT["limits"]["searchCharacters"], "search")
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return [dict(row) for row in self.connection.execute("SELECT conversation_id,title FROM conversations WHERE title LIKE ? ESCAPE '\\' ORDER BY title,conversation_id", (f"%{escaped}%",))]

    def append_message(self, conversation_id: str, message: dict, attachments: list[dict]) -> None:
        _validate_id(conversation_id, "conversation-id")
        expected = {"messageId", "ordinal", "role", "content", "modelId", "providerId", "createdAtUtc"}
        if set(message) != expected: raise StoreError("invalid-message-shape")
        _validate_id(message["messageId"], "message-id"); _validate_text(message["content"], 200000, "content")
        _validate_id(message["modelId"], "model-id"); _validate_id(message["providerId"], "provider-id")
        if type(message["ordinal"]) is not int or message["ordinal"] <= 0 or message["role"] not in {"system", "user", "assistant"} or UTC.fullmatch(message["createdAtUtc"]) is None: raise StoreError("invalid-message-metadata")
        if not isinstance(attachments, list) or len(attachments) > CONTRACT["limits"]["attachmentSnapshotsPerMessage"]: raise StoreError("invalid-attachments")
        checked = []
        fields = set(CONTRACT["attachmentSnapshotFields"])
        for ordinal, item in enumerate(attachments, 1):
            if not isinstance(item, dict) or set(item) != fields: raise StoreError("invalid-attachment-shape")
            _validate_text(item["name"], 255, "attachment-name"); _validate_text(item["mediaType"], 100, "media-type")
            if type(item["sizeBytes"]) is not int or item["sizeBytes"] < 0 or DIGEST.fullmatch(item["sha256"]) is None or item["availability"] not in {"available-at-send", "unavailable-at-send"}: raise StoreError("invalid-attachment-metadata")
            checked.append((message["messageId"], ordinal, item["name"], item["mediaType"], item["sizeBytes"], item["sha256"], item["availability"]))
        if not self.quota_check(len(message["content"].encode("utf-8"))): raise StoreError("storage-unavailable")
        own_transaction = not self.connection.in_transaction
        try:
            if own_transaction: self.connection.execute("BEGIN IMMEDIATE")
            self.connection.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?)", (message["messageId"], conversation_id, message["ordinal"], message["role"], message["content"], message["modelId"], message["providerId"], message["createdAtUtc"]))
            self.failure_hook()
            self.connection.executemany("INSERT INTO attachment_snapshots VALUES(?,?,?,?,?,?,?)", checked)
            if own_transaction: self.connection.execute("COMMIT")
        except Exception:
            if own_transaction and self.connection.in_transaction: self.connection.execute("ROLLBACK")
            raise

    def list_messages(self, conversation_id: str) -> list[dict]:
        _validate_id(conversation_id, "conversation-id")
        messages = []
        for row in self.connection.execute("SELECT message_id,ordinal,role,content,model_id,provider_id,created_at_utc FROM messages WHERE conversation_id=? ORDER BY ordinal", (conversation_id,)):
            item = dict(row)
            item["attachments"] = [dict(value) for value in self.connection.execute("SELECT ordinal,name,media_type,size_bytes,sha256,availability FROM attachment_snapshots WHERE message_id=? ORDER BY ordinal", (row["message_id"],))]
            messages.append(item)
        return messages

    def delete_conversation(self, conversation_id: str) -> None:
        _validate_id(conversation_id, "conversation-id")
        self.connection.execute("DELETE FROM conversations WHERE conversation_id=?", (conversation_id,))

    def clear_all(self) -> None:
        self.connection.execute("DELETE FROM conversations")

    def export_sanitized(self) -> bytes:
        payload = {"schemaVersion": 1, "conversations": []}
        for conversation in self.list_conversations():
            item = dict(conversation); item["messages"] = self.list_messages(conversation["conversation_id"]); payload["conversations"].append(item)
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(encoded) > CONTRACT["limits"]["exportBytes"]: raise StoreError("export-too-large")
        return encoded

    def import_sanitized(self, data: bytes) -> None:
        if not isinstance(data, bytes) or len(data) > CONTRACT["limits"]["exportBytes"]: raise StoreError("invalid-import-size")
        try: payload = json.loads(data.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error: raise StoreError("invalid-import") from error
        _scan_forbidden(payload)
        if not isinstance(payload, dict) or set(payload) != {"schemaVersion", "conversations"} or payload["schemaVersion"] != 1 or not isinstance(payload["conversations"], list) or len(payload["conversations"]) > CONTRACT["limits"]["importRecords"]: raise StoreError("invalid-import-shape")
        if self.list_conversations(): raise StoreError("import-target-not-empty")
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            for item in payload["conversations"]:
                expected = {"conversation_id", "title", "created_at_utc", "retention_policy", "model_id", "provider_id", "renamed_at_utc", "messages"}
                if not isinstance(item, dict) or set(item) != expected: raise StoreError("invalid-import-conversation")
                self.create_conversation(item["conversation_id"], item["title"], item["created_at_utc"], item["retention_policy"], item["model_id"], item["provider_id"])
                for message in item["messages"]:
                    mapped = {"messageId": message["message_id"], "ordinal": message["ordinal"], "role": message["role"], "content": message["content"], "modelId": message["model_id"], "providerId": message["provider_id"], "createdAtUtc": message["created_at_utc"]}
                    attachments = [{"name": a["name"], "mediaType": a["media_type"], "sizeBytes": a["size_bytes"], "sha256": a["sha256"], "availability": a["availability"]} for a in message["attachments"]]
                    self.append_message(item["conversation_id"], mapped, attachments)
            self.connection.execute("COMMIT")
        except Exception:
            if self.connection.in_transaction: self.connection.execute("ROLLBACK")
            raise

    def backup(self, destination: Path) -> dict:
        if destination.parent != self.directory or destination.exists() or destination.name != "history-backup.sqlite3": raise StoreError("unsafe-backup-destination")
        backup = sqlite3.connect(destination)
        try: self.connection.backup(backup)
        finally: backup.close()
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        return {"schemaVersion": 1, "name": destination.name, "sizeBytes": destination.stat().st_size, "sha256": digest}

    @staticmethod
    def verify_backup(directory: Path, manifest: dict) -> None:
        if not isinstance(manifest, dict) or set(manifest) != {"schemaVersion", "name", "sizeBytes", "sha256"} or manifest["schemaVersion"] != 1 or manifest["name"] != "history-backup.sqlite3" or type(manifest["sizeBytes"]) is not int or DIGEST.fullmatch(manifest["sha256"]) is None: raise StoreError("invalid-backup-manifest")
        candidate = directory / manifest["name"]
        if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size != manifest["sizeBytes"] or hashlib.sha256(candidate.read_bytes()).hexdigest() != manifest["sha256"]: raise StoreError("backup-verification-failed")
