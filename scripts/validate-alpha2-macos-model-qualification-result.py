#!/usr/bin/env python3
"""Validate a sanitized Apple-Silicon qualification result offline."""

from __future__ import annotations

import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
EXPECTED_CHECKS = {"generalChat", "contentWrite", "contentSummarize", "structuredTool", "structuredCode"}
# Assemble the platform-private path markers so this validator can test for
# them without placing a scanner-triggering example path in the public tree.
PRIVATE_PATH = re.compile(
    rf"(?:/{'Us' + 'ers'}/[^/\s]+|[A-Za-z]:\\{'Us' + 'ers'}\\[^\\\s]+)",
    re.IGNORECASE,
)
IPV4 = re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")


class ResultError(ValueError):
    pass


def load_runner():
    spec = importlib.util.spec_from_file_location("mac_qualification_runner", RUNNER_PATH)
    if not spec or not spec.loader:
        raise ResultError("runner-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)
    elif isinstance(value, str):
        yield value


def validate_no_private_content(result: dict[str, Any]) -> None:
    prohibited_keys = {"hostname", "username", "userid", "machineid", "serialnumber", "rawprompt", "rawresponse", "ipaddress"}
    for value in walk(result):
        if not isinstance(value, str):
            continue
        compact = re.sub(r"[^a-z0-9]", "", value.lower())
        if compact in prohibited_keys:
            raise ResultError("private-field-present")
        if PRIVATE_PATH.search(value):
            raise ResultError("private-path-present")
        for address in IPV4.findall(value):
            if address != "127.0.0.1":
                raise ResultError("private-address-present")


def validate_result(
    result: dict[str, Any],
    plan: dict[str, Any],
    runner: Any,
    model_ids: list[str] | None = None,
) -> None:
    candidates = runner.validate_plan(plan, ROOT)
    if model_ids is not None:
        if not model_ids or len(model_ids) != len(set(model_ids)):
            raise ResultError("invalid-candidate-selection")
        unknown = set(model_ids) - set(candidates)
        if unknown:
            raise ResultError("unknown-candidate-selection")
        candidates = {model_id: candidates[model_id] for model_id in model_ids}
    if result.get("schemaVersion") != 1 or result.get("kind") != "haven42-apple-silicon-model-qualification-result":
        raise ResultError("invalid-result-identity")
    if result.get("release") != plan.get("release") or result.get("status") != "completed":
        raise ResultError("incomplete-result")
    try:
        timestamp = datetime.strptime(result["observedAtUtc"], "%Y-%m-%dT%H:%M:%SZ")
    except (KeyError, TypeError, ValueError) as error:
        raise ResultError("invalid-observation-time") from error
    if timestamp.year < 2026:
        raise ResultError("invalid-observation-time")
    if result.get("planCanonicalSha256") != runner.canonical_sha256(plan):
        raise ResultError("stale-plan-binding")
    if result.get("inventoryCanonicalSha256") != plan["inventoryBinding"]["canonicalSha256"]:
        raise ResultError("stale-inventory-binding")
    if result.get("testContract") != plan["testContract"]:
        raise ResultError("test-contract-mismatch")
    expected_runtime = {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")}
    if result.get("runtime") != expected_runtime:
        raise ResultError("runtime-mismatch")
    hardware = result.get("hardwareProfile")
    if not isinstance(hardware, dict) or hardware.get("profileId") != plan["hardwareProfile"]["id"] or hardware.get("platformFamily") != "macos" or hardware.get("architecture") != "arm64" or hardware.get("backend") != "metal" or hardware.get("systemMemoryGiB", 0) < plan["hardwareProfile"]["minimumSystemMemoryGiB"]:
        raise ResultError("hardware-profile-mismatch")
    for key in ("rawPromptsOrResponsesRetained", "privateIdentityRetained", "automaticDefaultChangeAllowed", "automaticSelectionEvidenceAllowed", "automaticSupportChangeAllowed"):
        if result.get(key) is not False:
            raise ResultError("unsafe-result-authority")
    records = result.get("results")
    if not isinstance(records, list) or len(records) != len(candidates) or result.get("modelsRequested") != len(candidates):
        raise ResultError("candidate-count-mismatch")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or record.get("modelId") in seen or record.get("modelId") not in candidates:
            raise ResultError("invalid-candidate-result")
        seen.add(record["modelId"])
        candidate = candidates[record["modelId"]]
        if record.get("model") != candidate["model"] or record.get("manifestDigest") != candidate["manifestDigest"]:
            raise ResultError("candidate-binding-mismatch")
        if record.get("status") not in {"passed", "failed"} or record.get("codingSurfaceStatus") != "not-run" or record.get("codingRecommendationEligible") is not False:
            raise ResultError("invalid-candidate-status")
        checks, metrics = record.get("checks"), record.get("metrics")
        if not isinstance(checks, dict) or set(checks) != EXPECTED_CHECKS or not isinstance(metrics, dict) or set(metrics) != EXPECTED_CHECKS:
            raise ResultError("invalid-cell-set")
        for name in EXPECTED_CHECKS:
            check, measurement = checks[name], metrics[name]
            if not isinstance(check, dict) or check.get("status") not in {"passed", "failed"} or check.get("responseRetained") is not False or not isinstance(check.get("durationSeconds"), (int, float)) or check["durationSeconds"] < 0:
                raise ResultError("invalid-cell-result")
            if not isinstance(measurement, dict) or measurement.get("unloadPassed") is not True:
                raise ResultError("invalid-cell-metrics")
        all_passed = all(checks[name]["status"] == "passed" for name in EXPECTED_CHECKS)
        if record.get("corePassed") is not all_passed or (record["status"] == "passed") is not all_passed:
            raise ResultError("inconsistent-candidate-status")
    cleanup = result.get("cleanup")
    pulled = result.get("modelsPulled")
    if not isinstance(pulled, int) or pulled < 0 or not isinstance(cleanup, list) or len(cleanup) != pulled:
        raise ResultError("cleanup-count-mismatch")
    allowed_models = {candidate["model"] for candidate in candidates.values()}
    cleanup_models = [item.get("model") for item in cleanup if isinstance(item, dict)]
    if len(set(cleanup_models)) != len(cleanup_models) or any(model not in allowed_models for model in cleanup_models) or any(item.get("removed") is not True for item in cleanup if isinstance(item, dict)):
        raise ResultError("cleanup-not-proven")
    validate_no_private_content(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument(
        "--model-id",
        action="append",
        dest="model_ids",
        help="Validate only an explicitly selected plan candidate; repeat as needed.",
    )
    args = parser.parse_args()
    runner = load_runner()
    try:
        result = runner.load_json(args.result)
        plan = runner.load_json(args.plan)
        validate_result(result, plan, runner, args.model_ids)
    except (ResultError, runner.QualificationError) as error:
        parser.error(str(error))
    print("Apple-Silicon qualification result is structurally valid and sanitized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
