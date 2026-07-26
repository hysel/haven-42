#!/usr/bin/env python3
"""Happy-path and hostile tests for the effect-free history foundation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "conversation_history_foundation",
    ROOT / "scripts" / "simulate-conversation-history.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CONTRACT = json.loads((ROOT / "config/conversation-history-contract.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "config/conversation-history-schema.json").read_text(encoding="utf-8"))
HOSTILE = json.loads(
    (ROOT / "examples/fixtures/conversation-history-hostile-cases.json").read_text(encoding="utf-8")
)


def request(operation, payload, request_id="foundation-check"):
    return {
        "schemaVersion": 1,
        "operation": operation,
        "requestId": request_id,
        "payload": payload,
    }


def rejected(value, code):
    try:
        MODULE.plan_history(value, CONTRACT, SCHEMA)
    except MODULE.HistoryFoundationError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"history request unexpectedly admitted: {code}")


def assert_effect_free(result):
    assert result["status"] == "planned"
    assert result["runtimeAdmitted"] is False
    assert result["executionAllowed"] is False
    assert result["privateSessionDefault"] is True
    assert not any(result["effects"].values())


def main() -> int:
    schema = MODULE.plan_history(request("inspect-schema", {}), CONTRACT, SCHEMA)
    assert_effect_free(schema)
    assert schema["plan"]["schemaVersion"] == 1
    assert schema["plan"]["executableSqlIncluded"] is False
    assert schema["plan"]["tableNames"] == [
        "conversations",
        "messages",
        "contextSummaries",
        "attachmentReferences",
    ]

    migration = MODULE.plan_history(
        request("plan-migration", {
            "currentVersion": 0,
            "targetVersion": 1,
            "condition": "interrupted-before-commit",
        }),
        CONTRACT,
        SCHEMA,
    )
    assert_effect_free(migration)
    assert migration["plan"]["rollbackRequired"] is True
    assert "plan-rollback-to-source-version" in migration["plan"]["steps"]
    assert migration["plan"]["databaseOpened"] is False

    private_retention = MODULE.plan_history(
        request("plan-retention", {
            "conversationId": "conversation-one",
            "retentionPolicy": "private-session",
            "nowUtc": "2026-07-26T12:00:00Z",
            "lastActivityUtc": "2026-07-26T11:00:00Z",
        }),
        CONTRACT,
        SCHEMA,
    )
    assert_effect_free(private_retention)
    assert private_retention["plan"]["disposition"] == "no-record-allowed"

    expired = MODULE.plan_history(
        request("plan-retention", {
            "conversationId": "conversation-one",
            "retentionPolicy": "30-days",
            "nowUtc": "2026-07-26T12:00:00Z",
            "lastActivityUtc": "2026-06-01T12:00:00Z",
        }),
        CONTRACT,
        SCHEMA,
    )
    assert expired["plan"]["disposition"] == "eligible-for-explicit-delete"
    assert expired["plan"]["automaticDeleteExecuted"] is False

    context = MODULE.plan_history(
        request("plan-context", {
            "conversationId": "conversation-one",
            "tokenBudget": 100,
            "messages": [
                {"messageId": "message-one", "conversationId": "conversation-one", "ordinal": 1, "role": "user", "characters": 160, "estimatedTokens": 40},
                {"messageId": "message-two", "conversationId": "conversation-one", "ordinal": 2, "role": "assistant", "characters": 240, "estimatedTokens": 60},
                {"messageId": "message-three", "conversationId": "conversation-one", "ordinal": 3, "role": "user", "characters": 80, "estimatedTokens": 20}
            ],
            "summary": {
                "summaryId": "summary-one",
                "conversationId": "conversation-one",
                "throughOrdinal": 1,
                "characters": 80,
                "estimatedTokens": 20,
                "validationStatus": "validated-local"
            },
        }),
        CONTRACT,
        SCHEMA,
    )
    assert_effect_free(context)
    assert context["plan"]["selectedMessageIds"] == ["message-two", "message-three"]
    assert context["plan"]["selectedSummaryId"] == "summary-one"
    assert context["plan"]["estimatedTokens"] == 100
    assert context["plan"]["contentIncludedInPlan"] is False

    deletion = MODULE.plan_history(
        request("plan-deletion", {
            "scope": "conversation",
            "conversationId": "conversation-one",
            "includeBackups": True,
        }),
        CONTRACT,
        SCHEMA,
    )
    assert_effect_free(deletion)
    assert deletion["plan"]["deletionExecuted"] is False
    assert set(("wal", "journal", "indexes", "backups")).issubset(deletion["plan"]["targets"])

    for condition in ("busy-or-locked", "interrupted-write", "corruption", "disk-full"):
        recovery = MODULE.plan_history(
            request("plan-recovery", {
                "condition": condition,
                "schemaVersion": 1,
                "integrityStatus": "failed" if condition == "corruption" else "unknown",
            }, f"recovery-{condition}"),
            CONTRACT,
            SCHEMA,
        )
        assert_effect_free(recovery)
        assert recovery["plan"]["automaticRestoreAllowed"] is False
        assert recovery["plan"]["originalPreserved"] is True
        assert recovery["plan"]["recoveryExecuted"] is False

    backup = MODULE.plan_history(
        request("plan-backup", {
            "recordCount": 20,
            "includeAttachmentBytes": False,
            "destinationGrant": False,
        }),
        CONTRACT,
        SCHEMA,
    )
    assert_effect_free(backup)
    assert backup["plan"]["backupWritten"] is False
    assert backup["plan"]["destinationSelectionDeferred"] is True

    restore = MODULE.plan_history(
        request("plan-restore", {
            "recordCount": 20,
            "sourceSchemaVersion": 1,
            "integrityStatus": "verified",
            "activeContentDetected": False,
        }),
        CONTRACT,
        SCHEMA,
    )
    assert_effect_free(restore)
    assert restore["plan"]["restoreWritten"] is False
    assert restore["plan"]["stagingRequired"] is True

    assert len(HOSTILE["cases"]) == 16
    for case in HOSTILE["cases"]:
        rejected(case["request"], case["expectedError"])

    rejected({**request("inspect-schema", {}), "approval": True}, "invalid-request-fields")
    rejected(request("inspect-schema", {}, "UPPERCASE"), "invalid-request-id")
    rejected(request("plan-context", {
        "conversationId": "conversation-one",
        "tokenBudget": 131073,
        "messages": [],
        "summary": None,
    }), "invalid-context-budget")
    rejected(request("plan-backup", {
        "recordCount": 1,
        "includeAttachmentBytes": False,
        "destinationGrant": True,
    }), "filesystem-grant-not-admitted")
    nested = {}
    cursor = nested
    for _ in range(10):
        cursor["nested"] = {}
        cursor = cursor["nested"]
    rejected(request("inspect-schema", nested), "request-nesting-too-deep")

    assert CONTRACT["activation"]["databaseOpenAllowed"] is False
    assert CONTRACT["activation"]["filesystemWriteAllowed"] is False
    assert CONTRACT["storage"]["encryptionAtRestAdmitted"] is False
    assert CONTRACT["lifecycle"]["privateSessionWriteFree"] is True
    assert SCHEMA["executableSqlIncluded"] is False
    print("Conversation-history foundation passed 39 bounded, effect-free checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
