#!/usr/bin/env python3
"""Validate a sanitized Apple M4 OpenCode coding-agent qualification result."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
POLICY_PATH = ROOT / "config/model-coding-agent-qualification-policy.json"
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"
QUALIFICATION_VALIDATOR_PATH = ROOT / "scripts/validate-alpha2-macos-model-qualification-result.py"
ALLOWED_STATUSES = {"passed", "failed", "blocked", "not-run"}


class CodingResultError(ValueError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise CodingResultError("validator-dependency-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_dict(value: Any, keys: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CodingResultError(code)
    return value


def derived_status(checks: dict[str, str]) -> str:
    for status in ("failed", "blocked", "not-run"):
        if status in checks.values():
            return status
    return "passed"


def validate_result(value: Any, plan: dict[str, Any], qualification: dict[str, Any], policy: dict[str, Any], runner: Any) -> None:
    exact_dict(value, {
        "schemaVersion", "kind", "release", "status", "planCanonicalSha256",
        "qualificationCanonicalSha256", "policyCanonicalSha256", "runtime",
        "hardwareProfile", "surface", "results", "observedAtUtc",
        "rawPromptsOrResponsesRetained", "privateIdentityRetained",
        "automaticDefaultChangeAllowed", "automaticSelectionEvidenceAllowed",
        "automaticSupportChangeAllowed",
    }, "result-shape-invalid")
    if value["schemaVersion"] != 1 or value["kind"] != "haven42-apple-silicon-coding-agent-qualification-result" or value["status"] != "completed":
        raise CodingResultError("result-identity-invalid")
    if value["release"] != plan["release"]:
        raise CodingResultError("release-mismatch")
    bindings = (value["planCanonicalSha256"], value["qualificationCanonicalSha256"], value["policyCanonicalSha256"])
    expected_bindings = (runner.canonical_sha256(plan), runner.canonical_sha256(qualification), runner.canonical_sha256(policy))
    if bindings != expected_bindings:
        raise CodingResultError("evidence-binding-mismatch")
    expected_runtime = {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")}
    if value["runtime"] != expected_runtime:
        raise CodingResultError("runtime-mismatch")
    hardware = exact_dict(value["hardwareProfile"], {"architecture", "backend", "platformFamily", "profileId", "systemMemoryGiB"}, "hardware-shape-invalid")
    if hardware["profileId"] != plan["hardwareProfile"]["id"] or hardware["platformFamily"] != "macos" or hardware["architecture"] != "arm64" or hardware["backend"] != "metal":
        raise CodingResultError("hardware-mismatch")
    surface = exact_dict(value["surface"], {"id", "version", "binarySha256", "archiveSha256"}, "surface-shape-invalid")
    if surface["id"] != "opencode-cli" or surface["version"] != "1.18.19" or any(not runner.SHA256.fullmatch(str(surface[key])) for key in ("binarySha256", "archiveSha256")):
        raise CodingResultError("surface-mismatch")
    if value["rawPromptsOrResponsesRetained"] is not False or value["privateIdentityRetained"] is not False:
        raise CodingResultError("privacy-boundary-invalid")
    if any(value[key] is not False for key in ("automaticDefaultChangeAllowed", "automaticSelectionEvidenceAllowed", "automaticSupportChangeAllowed")):
        raise CodingResultError("promotion-authority-invalid")
    if not isinstance(value["observedAtUtc"], str) or not value["observedAtUtc"].endswith("Z"):
        raise CodingResultError("observation-time-invalid")
    expected_gates = {gate["id"]: set(gate["checks"]) for gate in policy["requiredGates"]}
    expected_candidates = plan["candidates"]
    results = value["results"]
    if not isinstance(results, list) or [record.get("modelId") for record in results if isinstance(record, dict)] != [item["modelId"] for item in expected_candidates]:
        raise CodingResultError("result-coverage-invalid")
    candidates = {item["modelId"]: item for item in expected_candidates}
    for record in results:
        required = {"modelId", "model", "manifestDigest", "status", "gates", "surfaceToolObservations", "surfaceMetrics", "temporaryModelPulled", "temporaryModelRemoved", "responseRetained", "codingRecommendationEligible", "promotionBlock"}
        if not isinstance(record, dict) or set(record) not in (required, required | {"errorCode"}):
            raise CodingResultError("model-result-shape-invalid")
        candidate = candidates[record["modelId"]]
        if record["model"] != candidate["model"] or record["manifestDigest"] != candidate["manifestDigest"] or record["promotionBlock"] != candidate.get("promotionBlock"):
            raise CodingResultError("model-binding-mismatch")
        if record["status"] not in {"passed", "failed"} or record["responseRetained"] is not False:
            raise CodingResultError("model-result-status-invalid")
        gates = record["gates"]
        if not isinstance(gates, dict) or set(gates) != set(expected_gates):
            raise CodingResultError("required-gates-incomplete")
        all_passed = True
        for gate_id, check_ids in expected_gates.items():
            gate = exact_dict(gates[gate_id], {"status", "checks"}, "gate-shape-invalid")
            checks = gate["checks"]
            if not isinstance(checks, dict) or set(checks) != check_ids or any(status not in ALLOWED_STATUSES for status in checks.values()):
                raise CodingResultError("gate-checks-invalid")
            if gate["status"] != derived_status(checks):
                raise CodingResultError("gate-summary-inconsistent")
            all_passed = all_passed and gate["status"] == "passed"
        cleanup_ok = record["temporaryModelPulled"] is not True or record["temporaryModelRemoved"] is True
        expected_status = "passed" if all_passed and cleanup_ok and "errorCode" not in record else "failed"
        if record["status"] != expected_status:
            raise CodingResultError("model-summary-inconsistent")
        eligible = expected_status == "passed" and record["promotionBlock"] is None
        if record["codingRecommendationEligible"] is not eligible:
            raise CodingResultError("coding-eligibility-inconsistent")
        observations = record["surfaceToolObservations"]
        metrics = record["surfaceMetrics"]
        if "errorCode" in record and (not isinstance(record["errorCode"], str) or not record["errorCode"]):
            raise CodingResultError("failed-record-invalid")
        if observations == {} and metrics == {}:
            if "errorCode" not in record:
                raise CodingResultError("failed-record-invalid")
        else:
            exact_dict(observations, {"read-tool-observed", "write-tool-observed"}, "surface-observations-invalid")
            if any(status not in ALLOWED_STATUSES for status in observations.values()):
                raise CodingResultError("surface-observation-status-invalid")
            exact_dict(metrics, {"readDurationSeconds", "editDurationSeconds", "readErrorCode", "editErrorCode", "readUnloadPassed", "editUnloadPassed", "rawEventsRetained", "forcedTimeoutDurationSeconds", "recoveryDurationSeconds"}, "surface-metrics-invalid")
            if metrics["rawEventsRetained"] is not False or any(not isinstance(metrics[key], (int, float)) or metrics[key] < 0 for key in ("readDurationSeconds", "editDurationSeconds", "forcedTimeoutDurationSeconds", "recoveryDurationSeconds")):
                raise CodingResultError("surface-metrics-value-invalid")
            if any(type(metrics[key]) is not bool for key in ("readUnloadPassed", "editUnloadPassed")):
                raise CodingResultError("surface-unload-invalid")
        if record["temporaryModelPulled"] is True and record["temporaryModelRemoved"] is not True:
            raise CodingResultError("temporary-model-cleanup-invalid")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--qualification-result", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    args = parser.parse_args()
    runner = load_module("mac_qualification_runner", RUNNER_PATH)
    qualification_validator = load_module("mac_qualification_validator", QUALIFICATION_VALIDATOR_PATH)
    try:
        plan, qualification, policy = runner.load_json(args.plan), runner.load_json(args.qualification_result), runner.load_json(args.policy)
        qualification_validator.validate_result(qualification, plan, runner)
        validate_result(runner.load_json(args.result), plan, qualification, policy, runner)
    except (OSError, json.JSONDecodeError, CodingResultError, runner.QualificationError, qualification_validator.ResultError) as error:
        parser.error(str(error))
    print(json.dumps({"status": "validated", "result": str(args.result)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
