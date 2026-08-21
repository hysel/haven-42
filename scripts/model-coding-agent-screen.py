#!/usr/bin/env python3
"""Validate one sanitized, surface-specific coding-agent evidence cell."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/model-coding-agent-qualification-policy.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


class ScreenError(ValueError):
    pass


def _exact_dict(value: Any, keys: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ScreenError(code)
    return value


def load_policy(path: Path = POLICY) -> dict[str, Any]:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ScreenError("policy-unavailable") from error
    validate_policy(policy)
    return policy


def validate_policy(policy: Any) -> None:
    if not isinstance(policy, dict) or policy.get("schemaVersion") != 1 or policy.get("kind") != "haven42-model-coding-agent-qualification-policy":
        raise ScreenError("policy-identity-invalid")
    gates = policy.get("requiredGates")
    if not isinstance(gates, list) or not gates:
        raise ScreenError("policy-gates-invalid")
    gate_ids: set[str] = set()
    for gate in gates:
        _exact_dict(gate, {"id", "checks"}, "policy-gate-shape-invalid")
        if not isinstance(gate["id"], str) or gate["id"] in gate_ids:
            raise ScreenError("policy-gate-id-invalid")
        gate_ids.add(gate["id"])
        if not isinstance(gate["checks"], list) or not gate["checks"] or len(set(gate["checks"])) != len(gate["checks"]):
            raise ScreenError("policy-gate-checks-invalid")


def evaluate(cell: Any, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_policy()
    _exact_dict(cell, {
        "schemaVersion", "kind", "modelId", "manifestDigest", "runtime",
        "hardwareProfileId", "surface", "gates",
        "rawPromptsOrResponsesRetained", "privateIdentityRetained",
    }, "cell-shape-invalid")
    if cell["schemaVersion"] != 1 or cell["kind"] != "haven42-coding-agent-evidence-cell":
        raise ScreenError("cell-identity-invalid")
    if not isinstance(cell["modelId"], str) or not ID.fullmatch(cell["modelId"]):
        raise ScreenError("model-id-invalid")
    if not isinstance(cell["manifestDigest"], str) or not SHA256.fullmatch(cell["manifestDigest"]):
        raise ScreenError("manifest-digest-invalid")
    runtime = _exact_dict(cell["runtime"], {"engine", "version", "artifactDigest"}, "runtime-shape-invalid")
    if not all(isinstance(runtime[key], str) and runtime[key] for key in ("engine", "version")):
        raise ScreenError("runtime-value-invalid")
    if not isinstance(runtime["artifactDigest"], str) or not SHA256.fullmatch(runtime["artifactDigest"]):
        raise ScreenError("runtime-digest-invalid")
    surface = _exact_dict(cell["surface"], {"id", "version"}, "surface-shape-invalid")
    if not all(isinstance(surface[key], str) and surface[key] for key in surface):
        raise ScreenError("surface-value-invalid")
    if not isinstance(cell["hardwareProfileId"], str) or not ID.fullmatch(cell["hardwareProfileId"]):
        raise ScreenError("hardware-profile-invalid")
    if cell["rawPromptsOrResponsesRetained"] is not False or cell["privateIdentityRetained"] is not False:
        raise ScreenError("evidence-hygiene-invalid")

    allowed = set(policy["scope"]["allowedStatuses"])
    expected = {gate["id"]: set(gate["checks"]) for gate in policy["requiredGates"]}
    gates = cell["gates"]
    if not isinstance(gates, dict) or set(gates) != set(expected):
        raise ScreenError("required-gates-incomplete")
    gate_results: list[dict[str, str]] = []
    all_gates_passed = True
    for gate_id, check_ids in expected.items():
        gate = _exact_dict(gates[gate_id], {"status", "checks"}, "gate-shape-invalid")
        checks = gate["checks"]
        if gate["status"] not in allowed or not isinstance(checks, dict) or set(checks) != check_ids:
            raise ScreenError("gate-status-or-checks-invalid")
        if any(status not in allowed for status in checks.values()):
            raise ScreenError("check-status-invalid")
        derived = "passed" if all(status == "passed" for status in checks.values()) else next(
            status for status in ("failed", "blocked", "not-run") if status in checks.values()
        )
        if gate["status"] != derived:
            raise ScreenError("gate-summary-inconsistent")
        gate_results.append({"gateId": gate_id, "status": derived})
        all_gates_passed = all_gates_passed and derived == "passed"

    legacy_surfaces = set(policy["surfaceAdmission"].get("legacyEvidenceOnlySurfaces", []))
    legacy_surface = surface["id"] in legacy_surfaces
    eligible = all_gates_passed and not legacy_surface
    return {
        "schemaVersion": 1,
        "kind": "haven42-coding-agent-screen-result",
        "modelId": cell["modelId"],
        "surface": surface,
        "status": "passed" if eligible else "blocked",
        "codingRecommendationEligible": eligible,
        "automaticDefaultChangeAllowed": False,
        "gateResults": gate_results,
        "legacyEvidenceOnlySurface": legacy_surface,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a coding-agent evidence cell.")
    parser.add_argument("--cell", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=POLICY)
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.cell.read_text(encoding="utf-8")), load_policy(args.policy))
    except (OSError, json.JSONDecodeError, ScreenError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["codingRecommendationEligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
