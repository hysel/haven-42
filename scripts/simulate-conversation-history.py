#!/usr/bin/env python3
"""Validate conversation-history requests and return effect-free plans only."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config" / "conversation-history-contract.json"
SCHEMA_PATH = ROOT / "config" / "conversation-history-schema.json"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class HistoryFoundationError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HistoryFoundationError("configuration-unavailable") from error
    if not isinstance(value, dict):
        raise HistoryFoundationError("configuration-invalid")
    return value


def _bounded_id(value: Any) -> bool:
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def _utc(value: Any) -> datetime:
    if not isinstance(value, str) or UTC_TIMESTAMP.fullmatch(value) is None:
        raise HistoryFoundationError("invalid-timestamp")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise HistoryFoundationError("invalid-timestamp") from error
    return parsed


def _integer(value: Any, minimum: int, maximum: int, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise HistoryFoundationError(code)
    return value


def _exact(payload: Any, fields: set[str]) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != fields:
        raise HistoryFoundationError("invalid-payload-fields")
    return payload


def _forbidden_field_scan(
    value: Any,
    forbidden: set[str],
    maximum_depth: int,
    maximum_nodes: int,
) -> None:
    pending = [(value, 0)]
    visited = 0
    while pending:
        current, depth = pending.pop()
        if depth > maximum_depth:
            raise HistoryFoundationError("request-nesting-too-deep")
        if not isinstance(current, (dict, list)):
            continue
        visited += 1
        if visited > maximum_nodes:
            raise HistoryFoundationError("request-too-complex")
        if isinstance(current, dict):
            if any(key in forbidden for key in current):
                raise HistoryFoundationError("forbidden-request-authority")
            pending.extend((child, depth + 1) for child in current.values())
        else:
            pending.extend((child, depth + 1) for child in current)


def _base_plan(operation: str, request_id: str, contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "conversation-history-foundation-plan",
        "status": "planned",
        "operation": operation,
        "requestId": request_id,
        "runtimeAdmitted": False,
        "privateSessionDefault": True,
        "executionAllowed": False,
        "effects": dict(contract["effects"]),
    }


def _inspect_schema(payload: Any, schema: dict[str, Any]) -> dict[str, Any]:
    _exact(payload, set())
    return {
        "schemaVersion": schema["currentVersion"],
        "tableNames": [table["name"] for table in schema["tables"]],
        "executableSqlIncluded": False,
    }


def _plan_migration(payload: Any, schema: dict[str, Any]) -> dict[str, Any]:
    value = _exact(payload, {"currentVersion", "targetVersion", "condition"})
    current = _integer(value["currentVersion"], 0, 1000, "invalid-schema-version")
    target = _integer(value["targetVersion"], 1, 1000, "invalid-schema-version")
    if target < current:
        raise HistoryFoundationError("schema-downgrade-refused")
    if target != schema["currentVersion"] or current not in (0, target):
        raise HistoryFoundationError("unsupported-migration-edge")
    if value["condition"] not in ("clean", "interrupted-before-commit"):
        raise HistoryFoundationError("invalid-migration-condition")
    steps = ["validate-source-version", "begin-atomic-migration", "validate-target-schema"]
    if value["condition"] == "interrupted-before-commit":
        steps.append("plan-rollback-to-source-version")
    else:
        steps.append("plan-commit")
    return {
        "fromVersion": current,
        "toVersion": target,
        "steps": steps,
        "atomicRequired": True,
        "rollbackRequired": True,
        "databaseOpened": False,
    }


def _plan_retention(payload: Any, contract: dict[str, Any]) -> dict[str, Any]:
    value = _exact(
        payload,
        {"conversationId", "retentionPolicy", "nowUtc", "lastActivityUtc"},
    )
    if not _bounded_id(value["conversationId"]):
        raise HistoryFoundationError("invalid-conversation-id")
    policy = value["retentionPolicy"]
    if policy not in contract["retentionPolicies"]:
        raise HistoryFoundationError("invalid-retention-policy")
    now = _utc(value["nowUtc"])
    last_activity = _utc(value["lastActivityUtc"])
    if last_activity > now:
        raise HistoryFoundationError("future-last-activity")
    if policy == "private-session":
        disposition = "no-record-allowed"
    elif policy == "forever":
        disposition = "retain"
    else:
        days = int(policy.split("-", 1)[0])
        disposition = "eligible-for-explicit-delete" if (now - last_activity).days >= days else "retain"
    return {
        "conversationId": value["conversationId"],
        "retentionPolicy": policy,
        "disposition": disposition,
        "automaticDeleteExecuted": False,
    }


def _plan_context(payload: Any, contract: dict[str, Any]) -> dict[str, Any]:
    value = _exact(
        payload,
        {"conversationId", "tokenBudget", "messages", "summary"},
    )
    if not _bounded_id(value["conversationId"]):
        raise HistoryFoundationError("invalid-conversation-id")
    maximum_tokens = contract["bounds"]["maximumContextTokens"]
    budget = _integer(value["tokenBudget"], 1, maximum_tokens, "invalid-context-budget")
    messages = value["messages"]
    if not isinstance(messages, list) or len(messages) > contract["bounds"]["maximumContextMessages"]:
        raise HistoryFoundationError("invalid-context-message-count")
    allowed_roles = set(contract["context"]["allowedRoles"])
    seen: set[str] = set()
    previous_ordinal = 0
    validated: list[dict[str, Any]] = []
    for message in messages:
        item = _exact(
            message,
            {"messageId", "conversationId", "ordinal", "role", "characters", "estimatedTokens"},
        )
        if (
            not _bounded_id(item["messageId"])
            or item["messageId"] in seen
            or item["conversationId"] != value["conversationId"]
            or item["role"] not in allowed_roles
        ):
            raise HistoryFoundationError("invalid-context-message")
        ordinal = _integer(
            item["ordinal"],
            1,
            contract["bounds"]["maximumMessagesPerConversation"],
            "invalid-context-ordinal",
        )
        if ordinal <= previous_ordinal:
            raise HistoryFoundationError("invalid-context-order")
        _integer(
            item["characters"],
            0,
            contract["bounds"]["maximumMessageCharacters"],
            "invalid-message-size",
        )
        _integer(item["estimatedTokens"], 0, maximum_tokens, "invalid-token-estimate")
        seen.add(item["messageId"])
        previous_ordinal = ordinal
        validated.append(item)
    summary = value["summary"]
    if summary is not None:
        summary = _exact(
            summary,
            {"summaryId", "conversationId", "throughOrdinal", "characters", "estimatedTokens", "validationStatus"},
        )
        if (
            not _bounded_id(summary["summaryId"])
            or summary["conversationId"] != value["conversationId"]
            or summary["validationStatus"] != "validated-local"
        ):
            raise HistoryFoundationError("invalid-context-summary")
        _integer(summary["throughOrdinal"], 1, contract["bounds"]["maximumMessagesPerConversation"], "invalid-summary-ordinal")
        _integer(summary["characters"], 0, contract["bounds"]["maximumSummaryCharacters"], "invalid-summary-size")
        _integer(summary["estimatedTokens"], 0, maximum_tokens, "invalid-token-estimate")

    selected: list[str] = []
    used = 0
    for item in reversed(validated):
        estimate = item["estimatedTokens"]
        if used + estimate > budget:
            continue
        selected.append(item["messageId"])
        used += estimate
    selected.reverse()
    summary_selected = False
    if summary is not None and summary["estimatedTokens"] + used <= budget:
        summary_selected = True
        used += summary["estimatedTokens"]
    return {
        "conversationId": value["conversationId"],
        "selectedMessageIds": selected,
        "selectedSummaryId": summary["summaryId"] if summary_selected else None,
        "estimatedTokens": used,
        "contentIncludedInPlan": False,
        "providerInvocationAllowed": False,
    }


def _plan_deletion(payload: Any) -> dict[str, Any]:
    value = _exact(payload, {"scope", "conversationId", "includeBackups"})
    if value["scope"] not in ("conversation", "clear-all"):
        raise HistoryFoundationError("invalid-deletion-scope")
    if value["scope"] == "conversation" and not _bounded_id(value["conversationId"]):
        raise HistoryFoundationError("invalid-conversation-id")
    if value["scope"] == "clear-all" and value["conversationId"] is not None:
        raise HistoryFoundationError("invalid-clear-all-target")
    if not isinstance(value["includeBackups"], bool):
        raise HistoryFoundationError("invalid-backup-deletion-choice")
    return {
        "scope": value["scope"],
        "conversationId": value["conversationId"],
        "targets": ["messages", "summaries", "attachment-references", "indexes", "wal", "journal"]
        + (["backups"] if value["includeBackups"] else []),
        "explicitConfirmationRequired": True,
        "deletionExecuted": False,
    }


def _plan_recovery(payload: Any) -> dict[str, Any]:
    value = _exact(payload, {"condition", "schemaVersion", "integrityStatus"})
    conditions = {
        "busy-or-locked": ["bounded-retry-disallowed", "preserve-current-state", "report-retryable"],
        "interrupted-write": ["discard-uncommitted-transaction", "verify-integrity", "preserve-last-commit"],
        "corruption": ["stop-writes", "preserve-original", "require-verified-restore"],
        "disk-full": ["rollback-transaction", "remove-run-owned-temporary-data", "report-capacity-error"],
    }
    if value["condition"] not in conditions:
        raise HistoryFoundationError("invalid-recovery-condition")
    _integer(value["schemaVersion"], 1, 1000, "invalid-schema-version")
    if value["integrityStatus"] not in ("unknown", "ok", "failed"):
        raise HistoryFoundationError("invalid-integrity-status")
    return {
        "condition": value["condition"],
        "steps": conditions[value["condition"]],
        "automaticRestoreAllowed": False,
        "originalPreserved": True,
        "recoveryExecuted": False,
    }


def _plan_backup(payload: Any, contract: dict[str, Any]) -> dict[str, Any]:
    value = _exact(payload, {"recordCount", "includeAttachmentBytes", "destinationGrant"})
    count = _integer(value["recordCount"], 0, contract["bounds"]["maximumBackupRecords"], "invalid-backup-record-count")
    if value["includeAttachmentBytes"] is not False:
        raise HistoryFoundationError("attachment-bytes-not-admitted")
    if value["destinationGrant"] is not False:
        raise HistoryFoundationError("filesystem-grant-not-admitted")
    return {
        "recordCount": count,
        "manifestRequired": True,
        "integrityHashRequired": True,
        "destinationSelectionDeferred": True,
        "backupWritten": False,
    }


def _plan_restore(payload: Any, contract: dict[str, Any]) -> dict[str, Any]:
    value = _exact(payload, {"recordCount", "sourceSchemaVersion", "integrityStatus", "activeContentDetected"})
    count = _integer(value["recordCount"], 0, contract["bounds"]["maximumBackupRecords"], "invalid-restore-record-count")
    version = _integer(value["sourceSchemaVersion"], 1, 1000, "invalid-schema-version")
    if version != 1:
        raise HistoryFoundationError("unsupported-restore-schema")
    if value["integrityStatus"] != "verified":
        raise HistoryFoundationError("restore-integrity-not-verified")
    if value["activeContentDetected"] is not False:
        raise HistoryFoundationError("active-content-rejected")
    return {
        "recordCount": count,
        "sourceSchemaVersion": version,
        "stagingRequired": True,
        "restoreWritten": False,
    }


def plan_history(
    request: dict[str, Any],
    contract: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    if contract.get("status") != "simulation-only-not-runtime-admitted":
        raise HistoryFoundationError("foundation-not-in-simulation-mode")
    required = set(contract["request"]["requiredFields"])
    if not isinstance(request, dict) or set(request) != required:
        raise HistoryFoundationError("invalid-request-fields")
    serialized = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(serialized) > contract["request"]["maximumSerializedBytes"]:
        raise HistoryFoundationError("request-too-large")
    _forbidden_field_scan(
        request,
        set(contract["request"]["forbiddenFieldNames"]),
        contract["request"]["maximumNestingDepth"],
        contract["request"]["maximumContainerNodes"],
    )
    if request["schemaVersion"] != 1:
        raise HistoryFoundationError("unsupported-request-version")
    operation = request["operation"]
    if operation not in contract["request"]["operations"]:
        raise HistoryFoundationError("operation-not-admitted")
    if not _bounded_id(request["requestId"]):
        raise HistoryFoundationError("invalid-request-id")

    planners = {
        "inspect-schema": lambda value: _inspect_schema(value, schema),
        "plan-migration": lambda value: _plan_migration(value, schema),
        "plan-retention": lambda value: _plan_retention(value, contract),
        "plan-context": lambda value: _plan_context(value, contract),
        "plan-deletion": _plan_deletion,
        "plan-recovery": _plan_recovery,
        "plan-backup": lambda value: _plan_backup(value, contract),
        "plan-restore": lambda value: _plan_restore(value, contract),
    }
    result = _base_plan(operation, request["requestId"], contract)
    result["plan"] = planners[operation](request["payload"])
    if any(result["effects"].values()):
        raise HistoryFoundationError("foundation-effect-policy-invalid")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    try:
        request = load_json(Path(args.request))
        result = plan_history(request, load_json(CONTRACT_PATH), load_json(SCHEMA_PATH))
    except HistoryFoundationError as error:
        print(json.dumps({
            "schemaVersion": 1,
            "kind": "conversation-history-foundation-error",
            "status": "rejected",
            "error": str(error),
            "executionAllowed": False,
        }, separators=(",", ":")), file=sys.stderr)
        return 2
    assert result["executionAllowed"] is False and not any(result["effects"].values())
    print("Conversation-history request accepted in simulation-only mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
