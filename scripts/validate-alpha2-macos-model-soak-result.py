#!/usr/bin/env python3
"""Validate a completed, sanitized Apple Silicon reliability-soak result."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"
QUALIFICATION_VALIDATOR_PATH = ROOT / "scripts/validate-alpha2-macos-model-qualification-result.py"
MINIMUM_SECONDS = 30 * 60


class SoakResultError(ValueError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise SoakResultError("validator-dependency-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_dict(value: Any, keys: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise SoakResultError(code)
    return value


def validate_result(value: Any, plan: dict[str, Any], qualification: dict[str, Any], runner: Any) -> None:
    exact_dict(value, {
        "schemaVersion", "kind", "release", "status", "planCanonicalSha256",
        "qualificationCanonicalSha256", "runtime", "hardwareProfile",
        "requestedMinutesPerModel", "intervalSeconds", "modelIdsExpected",
        "results", "observedAtUtc", "rawPromptsOrResponsesRetained",
        "privateIdentityRetained", "automaticDefaultChangeAllowed",
        "automaticSelectionEvidenceAllowed", "automaticSupportChangeAllowed",
    }, "result-shape-invalid")
    if value["schemaVersion"] != 1 or value["kind"] != "haven42-apple-silicon-model-soak-result" or value["status"] != "completed":
        raise SoakResultError("result-identity-invalid")
    if value["release"] != plan["release"]:
        raise SoakResultError("release-mismatch")
    if value["planCanonicalSha256"] != runner.canonical_sha256(plan) or value["qualificationCanonicalSha256"] != runner.canonical_sha256(qualification):
        raise SoakResultError("evidence-binding-mismatch")
    expected_runtime = {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")}
    if value["runtime"] != expected_runtime:
        raise SoakResultError("runtime-mismatch")
    hardware = exact_dict(value["hardwareProfile"], {"architecture", "backend", "platformFamily", "profileId", "systemMemoryGiB"}, "hardware-shape-invalid")
    if hardware["profileId"] != plan["hardwareProfile"]["id"] or hardware["platformFamily"] != "macos" or hardware["architecture"] != "arm64" or hardware["backend"] != "metal":
        raise SoakResultError("hardware-mismatch")
    if not isinstance(hardware["systemMemoryGiB"], (int, float)) or hardware["systemMemoryGiB"] < plan["hardwareProfile"]["minimumSystemMemoryGiB"]:
        raise SoakResultError("hardware-memory-invalid")
    expected_ids = [record["modelId"] for record in qualification["results"] if record["status"] == "passed"]
    if value["requestedMinutesPerModel"] != 30 or value["intervalSeconds"] != 30 or value["modelIdsExpected"] != expected_ids:
        raise SoakResultError("soak-contract-mismatch")
    if value["rawPromptsOrResponsesRetained"] is not False or value["privateIdentityRetained"] is not False:
        raise SoakResultError("privacy-boundary-invalid")
    if any(value[key] is not False for key in ("automaticDefaultChangeAllowed", "automaticSelectionEvidenceAllowed", "automaticSupportChangeAllowed")):
        raise SoakResultError("promotion-authority-invalid")
    if not isinstance(value["observedAtUtc"], str) or not value["observedAtUtc"].endswith("Z"):
        raise SoakResultError("observation-time-invalid")
    results = value["results"]
    if not isinstance(results, list) or [record.get("modelId") for record in results if isinstance(record, dict)] != expected_ids:
        raise SoakResultError("result-coverage-invalid")
    candidates = {record["modelId"]: record for record in plan["candidates"]}
    for record in results:
        base_keys = {"modelId", "model", "manifestDigest", "status", "durationSeconds", "cycles", "samples", "outputTokens", "averageTokensPerSecond", "unloadProofs", "temporaryModelPulled", "temporaryModelRemoved", "responseRetained"}
        if not isinstance(record, dict) or set(record) not in (base_keys, base_keys | {"errorCode"}):
            raise SoakResultError("model-result-shape-invalid")
        candidate = candidates[record["modelId"]]
        if record["model"] != candidate["model"] or record["manifestDigest"] != candidate["manifestDigest"]:
            raise SoakResultError("model-binding-mismatch")
        if record["status"] not in {"passed", "failed"} or record["responseRetained"] is not False:
            raise SoakResultError("model-result-status-invalid")
        if record["status"] == "passed":
            if "errorCode" in record or not isinstance(record["durationSeconds"], (int, float)) or record["durationSeconds"] < MINIMUM_SECONDS:
                raise SoakResultError("passed-duration-invalid")
            if not all(isinstance(record[key], int) and record[key] > 0 for key in ("cycles", "samples", "outputTokens", "unloadProofs")):
                raise SoakResultError("passed-measurements-invalid")
            if not isinstance(record["averageTokensPerSecond"], (int, float)) or record["averageTokensPerSecond"] <= 0:
                raise SoakResultError("passed-rate-invalid")
        elif not isinstance(record.get("errorCode"), str) or not record["errorCode"]:
            raise SoakResultError("failed-error-code-missing")
        if record["temporaryModelPulled"] is True and record["temporaryModelRemoved"] is not True:
            raise SoakResultError("temporary-model-cleanup-invalid")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--qualification-result", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    args = parser.parse_args()
    runner = load_module("mac_qualification_runner", RUNNER_PATH)
    qualification_validator = load_module("mac_qualification_validator", QUALIFICATION_VALIDATOR_PATH)
    try:
        plan = runner.load_json(args.plan)
        qualification = runner.load_json(args.qualification_result)
        qualification_validator.validate_result(qualification, plan, runner)
        validate_result(runner.load_json(args.result), plan, qualification, runner)
    except (OSError, json.JSONDecodeError, SoakResultError, runner.QualificationError, qualification_validator.ResultError) as error:
        parser.error(str(error))
    print(json.dumps({"status": "validated", "result": str(args.result)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
