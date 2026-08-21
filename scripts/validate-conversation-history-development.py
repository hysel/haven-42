#!/usr/bin/env python3
"""Exercise a synthetic temporary SQLite history database, then remove it."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "conversation-history-development-contract.json"
DATABASE_NAMES = ("history.sqlite3", "history-backup.sqlite3")
SIDE_SUFFIXES = ("", "-journal", "-shm", "-wal")
DDL = """
CREATE TABLE conversations (
  conversation_id TEXT PRIMARY KEY CHECK(length(conversation_id) BETWEEN 1 AND 64),
  title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 200),
  created_at_utc TEXT NOT NULL
);
CREATE TABLE messages (
  message_id TEXT PRIMARY KEY CHECK(length(message_id) BETWEEN 1 AND 64),
  conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  ordinal INTEGER NOT NULL CHECK(ordinal > 0),
  role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant')),
  content TEXT NOT NULL CHECK(length(content) <= 200000),
  UNIQUE(conversation_id, ordinal)
);
"""


class DevelopmentHistoryError(ValueError):
    pass


def _is_link_or_reparse(path: Path) -> bool:
    info = path.lstat()
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or stat.S_ISLNK(info.st_mode) or bool(attributes & reparse)


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DevelopmentHistoryError("invalid-development-contract") from error
    if contract.get("schemaVersion") != 1 or contract.get("status") != "synthetic-temporary-validation-only":
        raise DevelopmentHistoryError("invalid-development-contract")
    database = contract.get("database")
    authority = contract.get("authority")
    if not isinstance(database, dict) or not isinstance(authority, dict):
        raise DevelopmentHistoryError("invalid-development-contract")
    required_true = {
        "temporaryDirectoryOnly", "foreignKeysRequired", "parameterizedValuesRequired",
        "syntheticContentOnly", "cleanupRequired",
    }
    if any(database.get(name) is not True for name in required_true):
        raise DevelopmentHistoryError("unsafe-development-contract")
    if any(value is not False for value in authority.values()):
        raise DevelopmentHistoryError("unsafe-development-contract")
    if database.get("callerPathAllowed") is not False or database.get("preexistingDatabaseAllowed") is not False:
        raise DevelopmentHistoryError("unsafe-development-contract")
    return contract


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA trusted_schema=OFF")
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.execute("PRAGMA temp_store=MEMORY")
    # Some vendor Python builds, including Apple's signed arm64 build, compile
    # SQLite without loadable-extension support and therefore omit this method.
    # That is already the safer state.  Where the API exists, disable extension
    # loading explicitly before the connection is returned.
    disable_extensions = getattr(connection, "enable_load_extension", None)
    if disable_extensions is not None:
        disable_extensions(False)
    return connection


def validate_in_temporary_directory(directory: Path, contract_path: Path = CONTRACT_PATH) -> dict:
    contract = load_contract(contract_path)
    if not directory.is_absolute() or not directory.is_dir() or _is_link_or_reparse(directory):
        raise DevelopmentHistoryError("invalid-temporary-directory")
    if any(directory.iterdir()):
        raise DevelopmentHistoryError("temporary-directory-not-empty")
    database_path = directory / DATABASE_NAMES[0]
    backup_path = directory / DATABASE_NAMES[1]
    connection: sqlite3.Connection | None = None
    restored: sqlite3.Connection | None = None
    try:
        connection = _connect(database_path)
        try:
            os.chmod(database_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError as error:
            raise DevelopmentHistoryError("database-permission-hardening-failed") from error
        connection.executescript(DDL)
        synthetic = (
            ("m-1", "c-1", 1, "user", "Synthetic development prompt."),
            ("m-2", "c-1", 2, "assistant", "Synthetic development response."),
        )
        if len(synthetic) > contract["validation"]["maximumSyntheticMessages"]:
            raise DevelopmentHistoryError("synthetic-message-limit")
        if sum(len(item[4]) for item in synthetic) > contract["validation"]["maximumSyntheticCharacters"]:
            raise DevelopmentHistoryError("synthetic-character-limit")
        with connection:
            connection.execute(
                "INSERT INTO conversations VALUES (?, ?, ?)",
                ("c-1", "Synthetic validation", "2026-01-01T00:00:00Z"),
            )
            connection.executemany("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", synthetic)
        if connection.execute("SELECT count(*) FROM messages").fetchone()[0] != 2:
            raise DevelopmentHistoryError("synthetic-write-verification-failed")
        backup = sqlite3.connect(backup_path)
        try:
            connection.backup(backup)
        finally:
            backup.close()
        restored = sqlite3.connect(f"{backup_path.resolve().as_uri()}?mode=ro", uri=True)
        if restored.execute("SELECT count(*) FROM messages").fetchone()[0] != 2:
            raise DevelopmentHistoryError("backup-restore-verification-failed")
        restored.close()
        restored = None
        with connection:
            connection.execute("DELETE FROM conversations WHERE conversation_id = ?", ("c-1",))
        if connection.execute("SELECT count(*) FROM messages").fetchone()[0] != 0:
            raise DevelopmentHistoryError("cascade-delete-verification-failed")
    finally:
        if restored is not None:
            restored.close()
        if connection is not None:
            connection.close()
        for name in DATABASE_NAMES:
            for suffix in SIDE_SUFFIXES:
                candidate = directory / f"{name}{suffix}"
                if candidate.exists() and not candidate.is_symlink():
                    candidate.unlink()
    if any(directory.iterdir()):
        raise DevelopmentHistoryError("database-residue-detected")
    return {
        "schemaVersion": 1,
        "status": "synthetic-temporary-validation-passed",
        "checks": {
            "fixedSchema": True,
            "parameterizedValues": True,
            "backupRestore": True,
            "cascadeDeletion": True,
            "residueFree": True,
        },
        "authority": dict(contract["authority"]),
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="haven42-history-validation-") as temporary:
        result = validate_in_temporary_directory(Path(temporary).resolve())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
