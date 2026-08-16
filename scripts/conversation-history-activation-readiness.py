#!/usr/bin/env python3
"""Evaluate the checked-in saved-history admission state without side effects."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "config" / "conversation-history-activation-readiness.json"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
RELATIVE_EVIDENCE = re.compile(r"^(?:config|docs|examples)/[A-Za-z0-9._/-]{1,180}$")
EXPECTED_EFFECTS = {
    "databaseOpened",
    "databaseCreated",
    "filesystemRead",
    "filesystemWrite",
    "credentialStoreAccessed",
    "browserStorageUsed",
    "runtimeRouteEnabled",
    "uiControlEnabled",
    "providerInvoked",
    "networkAccessed",
}
EXPECTED_GATES = (
    "encrypted-database-dependency",
    "credential-store-lifecycle",
    "per-user-storage-permissions",
    "atomic-database-and-key-lifecycle",
    "encrypted-backup-restore-and-delete",
    "native-source-package-parity",
    "accessible-opt-in-and-recovery-ui",
    "privacy-and-data-flow-review",
)


class ReadinessError(ValueError):
    """The policy cannot safely support a readiness decision."""


def _exact(value: Any, fields: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ReadinessError(code)
    return value


def validate_policy(value: Any, root: Path = ROOT) -> dict[str, Any]:
    policy = _exact(
        value,
        {
            "schemaVersion",
            "policyId",
            "status",
            "defaultMode",
            "activationAllowed",
            "requiredPlatforms",
            "requiredGates",
            "effects",
        },
        "invalid-policy-fields",
    )
    if (
        policy["schemaVersion"] != 1
        or policy["policyId"] != "haven42.conversation-history.activation-readiness"
        or policy["status"] not in {"blocked-private-session-only", "candidate-ready-not-activated"}
        or policy["defaultMode"] != "private-session"
        or not isinstance(policy["activationAllowed"], bool)
        or policy["requiredPlatforms"] != ["windows", "linux", "macos"]
    ):
        raise ReadinessError("invalid-policy-identity")
    effects = _exact(policy["effects"], EXPECTED_EFFECTS, "invalid-effect-fields")
    if any(item is not False for item in effects.values()):
        raise ReadinessError("effect-authority-present")
    gates = policy["requiredGates"]
    if not isinstance(gates, list) or len(gates) != len(EXPECTED_GATES):
        raise ReadinessError("invalid-gate-count")
    observed: list[str] = []
    for gate in gates:
        item = _exact(gate, {"id", "status", "evidence", "reason"}, "invalid-gate-fields")
        if not isinstance(item["id"], str) or IDENTIFIER.fullmatch(item["id"]) is None:
            raise ReadinessError("invalid-gate-id")
        if item["status"] not in {"open", "passed"}:
            raise ReadinessError("invalid-gate-status")
        if (
            not isinstance(item["evidence"], str)
            or RELATIVE_EVIDENCE.fullmatch(item["evidence"]) is None
            or ".." in Path(item["evidence"]).parts
        ):
            raise ReadinessError("invalid-evidence-path")
        unresolved_evidence_path = root / item["evidence"]
        if unresolved_evidence_path.is_symlink():
            raise ReadinessError("evidence-link-refused")
        evidence_path = unresolved_evidence_path.resolve()
        try:
            evidence_path.relative_to(root.resolve())
        except ValueError as error:
            raise ReadinessError("evidence-path-escaped") from error
        if not evidence_path.is_file():
            raise ReadinessError("evidence-unavailable")
        if not isinstance(item["reason"], str) or not 20 <= len(item["reason"]) <= 300:
            raise ReadinessError("invalid-gate-reason")
        observed.append(item["id"])
    if tuple(observed) != EXPECTED_GATES:
        raise ReadinessError("invalid-gate-order")
    all_passed = all(item["status"] == "passed" for item in gates)
    expected_status = "candidate-ready-not-activated" if all_passed else "blocked-private-session-only"
    if policy["activationAllowed"] is not False or policy["status"] != expected_status:
        raise ReadinessError("readiness-overstated")
    return policy


def evaluate(policy: dict[str, Any]) -> dict[str, Any]:
    validated = validate_policy(policy)
    open_gates = [item["id"] for item in validated["requiredGates"] if item["status"] != "passed"]
    return {
        "schemaVersion": 1,
        "kind": "conversation-history-activation-readiness",
        "status": "blocked" if open_gates else "candidate-ready-not-activated",
        "effectiveMode": "private-session",
        "activationAllowed": False,
        "openGateCount": len(open_gates),
        "openGates": open_gates,
        "effects": dict(validated["effects"]),
    }


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    if path != POLICY_PATH:
        raise ReadinessError("caller-policy-path-refused")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReadinessError("policy-unavailable") from error
    if not isinstance(value, dict):
        raise ReadinessError("invalid-policy-fields")
    return value


def main() -> int:
    print(json.dumps(evaluate(load_policy()), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
