#!/usr/bin/env python3
"""Hostile tests for the effect-free saved-history readiness policy."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "history_activation_readiness",
    ROOT / "scripts" / "conversation-history-activation-readiness.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
POLICY = json.loads(
    (ROOT / "config" / "conversation-history-activation-readiness.json").read_text(encoding="utf-8")
)


def refused(value, code, root=ROOT):
    try:
        MODULE.validate_policy(value, root)
    except MODULE.ReadinessError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"unsafe readiness policy admitted: {code}")


def mutate(path, value):
    result = copy.deepcopy(POLICY)
    cursor = result
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    return result


def main() -> int:
    report = MODULE.evaluate(POLICY)
    assert report["status"] == "blocked"
    assert report["effectiveMode"] == "private-session"
    assert report["activationAllowed"] is False
    assert report["openGateCount"] == 8
    assert report["openGates"] == list(MODULE.EXPECTED_GATES)
    assert not any(report["effects"].values())

    refused({**POLICY, "approval": True}, "invalid-policy-fields")
    refused(mutate(["schemaVersion"], 2), "invalid-policy-identity")
    refused(mutate(["policyId"], "other"), "invalid-policy-identity")
    refused(mutate(["defaultMode"], "saved-history"), "invalid-policy-identity")
    refused(mutate(["requiredPlatforms"], ["windows"]), "invalid-policy-identity")
    refused(mutate(["effects", "filesystemWrite"], True), "effect-authority-present")
    refused(mutate(["effects", "shell"], False), "invalid-effect-fields")
    refused(mutate(["requiredGates"], POLICY["requiredGates"][:-1]), "invalid-gate-count")
    refused(mutate(["requiredGates", 0, "status"], "waived"), "invalid-gate-status")
    refused(mutate(["requiredGates", 0, "id"], "UPPER"), "invalid-gate-id")
    refused(mutate(["requiredGates", 0, "evidence"], "../../secret"), "invalid-evidence-path")
    refused(mutate(["requiredGates", 0, "evidence"], "docs/missing.md"), "evidence-unavailable")
    with patch.object(Path, "is_symlink", return_value=True):
        refused(POLICY, "evidence-link-refused")
    refused(mutate(["requiredGates", 0, "reason"], "short"), "invalid-gate-reason")
    refused(mutate(["requiredGates", 0, "extra"], False), "invalid-gate-fields")

    reversed_gates = copy.deepcopy(POLICY)
    reversed_gates["requiredGates"].reverse()
    refused(reversed_gates, "invalid-gate-order")

    overstated = copy.deepcopy(POLICY)
    overstated["activationAllowed"] = True
    refused(overstated, "readiness-overstated")
    overstated = copy.deepcopy(POLICY)
    overstated["status"] = "candidate-ready-not-activated"
    refused(overstated, "readiness-overstated")

    passed = copy.deepcopy(POLICY)
    passed["status"] = "candidate-ready-not-activated"
    for gate in passed["requiredGates"]:
        gate["status"] = "passed"
    passed_but_blocked = copy.deepcopy(passed)
    passed_but_blocked["status"] = "blocked-private-session-only"
    refused(passed_but_blocked, "readiness-overstated")
    activated = copy.deepcopy(passed)
    activated["activationAllowed"] = True
    refused(activated, "readiness-overstated")
    ready = MODULE.evaluate(passed)
    assert ready["status"] == "candidate-ready-not-activated"
    assert ready["activationAllowed"] is False
    assert ready["effectiveMode"] == "private-session"
    assert ready["openGateCount"] == 0
    assert not any(ready["effects"].values())

    assert MODULE.load_policy() == POLICY
    try:
        MODULE.load_policy(ROOT / "config" / "conversation-history-contract.json")
    except MODULE.ReadinessError as error:
        assert str(error) == "caller-policy-path-refused"
    else:
        raise AssertionError("caller policy path unexpectedly accepted")

    spec_text = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert "conversation-history-activation-readiness" not in spec_text
    source = (ROOT / "scripts" / "conversation-history-activation-readiness.py").read_text(encoding="utf-8")
    for forbidden in ("subprocess", "socket", "urllib", "requests", "sqlite3", "ctypes"):
        assert forbidden not in source

    print("Conversation-history activation readiness passed 31 fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
