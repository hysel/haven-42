#!/usr/bin/env python3
"""Generate fail-closed Alpha 2 model certification records from explicit gates."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


MAX_INPUT_BYTES = 4 * 1024 * 1024
SAFE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,99}")
SAFE_DIGEST = re.compile(r"(?:sha256:)?[0-9a-f]{64}")
SAFE_TEXT = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._()+:/-]{0,199}")
GATES = (
    ("discovered", "Discovered"),
    ("taskQualified", "Task qualified"),
    ("soakPassed", "Soak passed"),
    ("hardwareVerified", "Hardware verified"),
    ("osVerified", "OS verified"),
    ("recommended", "Recommended"),
    ("defaultCandidate", "Default candidate"),
)
FAILURE_GATE = "failedNeedsRetest"
TASKS = ("chat", "writing", "summarization")
TASK_RESULTS = {"passed", "partial", "failed", "not-tested"}
CAMPAIGN_SCOPES = {"shared-baseline", "hardware-fit-expansion", "os-anchor"}
FIT_STATES = {"comfortable", "workable", "borderline", "does-not-fit"}
EXECUTION_MODES = {"full-accelerator", "partial-accelerator", "cpu-only"}
RECOMMENDATION_STATES = {"recommended", "candidate", "not-recommended"}


class CertificationError(ValueError):
    """Certification inputs were incomplete, unordered, or unsafe."""


def safe_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_INPUT_BYTES:
        raise CertificationError("unsafe-certification-input")


def load_manifest(path: Path) -> dict[str, Any]:
    safe_file(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CertificationError("invalid-certification-input") from error
    if not isinstance(value, dict) or value.get("schemaVersion") != 1 or not isinstance(value.get("records"), list) or not value["records"]:
        raise CertificationError("invalid-certification-input")
    return value


def safe_text(value: Any) -> str:
    if not isinstance(value, str) or not SAFE_TEXT.fullmatch(value):
        raise CertificationError("unsafe-certification-text")
    return value


def safe_evidence_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value or len(value) > 300:
        raise CertificationError("unsafe-evidence-reference")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CertificationError("unsafe-evidence-reference")
    return value


def validate_gate(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"passed", "evidence"}:
        raise CertificationError("invalid-certification-gate")
    passed, evidence = value["passed"], value["evidence"]
    if not isinstance(passed, bool) or not isinstance(evidence, list):
        raise CertificationError("invalid-certification-gate")
    references = [safe_evidence_path(item) for item in evidence]
    if len(references) != len(set(references)) or (passed and not references):
        raise CertificationError("invalid-certification-gate")
    return {"passed": passed, "evidence": references}


def optional_measurement(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1_000_000:
        raise CertificationError("invalid-certification-measurement")
    return round(float(value), 3)


def normalize_assessment(value: Any) -> dict[str, Any]:
    required = {
        "campaignScope", "fitStatus", "executionMode", "tasks",
        "recommendationStatus", "recommendationRole", "limitations", "measurements",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise CertificationError("invalid-certification-assessment")
    if value["campaignScope"] not in CAMPAIGN_SCOPES or value["fitStatus"] not in FIT_STATES:
        raise CertificationError("invalid-certification-assessment")
    if value["executionMode"] not in EXECUTION_MODES or value["recommendationStatus"] not in RECOMMENDATION_STATES:
        raise CertificationError("invalid-certification-assessment")
    tasks = value["tasks"]
    if not isinstance(tasks, dict) or set(tasks) != set(TASKS) or any(result not in TASK_RESULTS for result in tasks.values()):
        raise CertificationError("invalid-certification-assessment")
    limitations = value["limitations"]
    if not isinstance(limitations, list) or len(limitations) > 10:
        raise CertificationError("invalid-certification-assessment")
    normalized_limitations = [safe_text(item) for item in limitations]
    if len(normalized_limitations) != len(set(normalized_limitations)):
        raise CertificationError("invalid-certification-assessment")
    measurements = value["measurements"]
    measurement_names = {"averageTokensPerSecond", "acceleratorMemoryGiB", "systemMemoryGiB", "averagePowerWatts"}
    if not isinstance(measurements, dict) or set(measurements) != measurement_names:
        raise CertificationError("invalid-certification-assessment")
    return {
        "campaignScope": value["campaignScope"],
        "fitStatus": value["fitStatus"],
        "executionMode": value["executionMode"],
        "tasks": {task: tasks[task] for task in TASKS},
        "recommendationStatus": value["recommendationStatus"],
        "recommendationRole": safe_text(value["recommendationRole"]),
        "limitations": normalized_limitations,
        "measurements": {name: optional_measurement(measurements[name]) for name in sorted(measurement_names)},
    }


def normalize_record(record: Any) -> dict[str, Any]:
    required = {"modelId", "identity", "environment", "assessment", "gates", "ownerApprovalReference"}
    if not isinstance(record, dict) or set(record) != required:
        raise CertificationError("invalid-certification-record")
    model_id = record["modelId"]
    if not isinstance(model_id, str) or not SAFE_ID.fullmatch(model_id):
        raise CertificationError("invalid-certification-record")
    identity = record["identity"]
    environment = record["environment"]
    if not isinstance(identity, dict) or set(identity) != {"provider", "runtimeVersion", "model", "manifestDigest"}:
        raise CertificationError("invalid-certification-record")
    if not isinstance(environment, dict) or set(environment) != {"operatingSystem", "acceleratorVendor", "acceleratorModel", "driverVersion"}:
        raise CertificationError("invalid-certification-record")
    digest = identity["manifestDigest"]
    if not isinstance(digest, str) or not SAFE_DIGEST.fullmatch(digest):
        raise CertificationError("invalid-certification-record")
    normalized_identity = {name: safe_text(value) for name, value in identity.items() if name != "manifestDigest"}
    normalized_identity["manifestDigest"] = digest.removeprefix("sha256:")
    normalized_environment = {name: safe_text(value) for name, value in environment.items()}
    gates = record["gates"]
    expected_gates = {name for name, _ in GATES} | {FAILURE_GATE}
    if not isinstance(gates, dict) or set(gates) != expected_gates:
        raise CertificationError("invalid-certification-gates")
    normalized_gates = {name: validate_gate(gates[name]) for name in expected_gates}
    assessment = normalize_assessment(record["assessment"])
    failed = normalized_gates[FAILURE_GATE]["passed"]
    passed_prefix = True
    highest_label: str | None = None
    next_gate: str | None = None
    for name, label in GATES:
        passed = normalized_gates[name]["passed"]
        if passed and not passed_prefix:
            raise CertificationError("certification-gates-out-of-order")
        if passed:
            highest_label = label
        elif next_gate is None:
            next_gate = label
            passed_prefix = False
    if highest_label is None and not failed:
        raise CertificationError("discovery-evidence-required")
    approval = record["ownerApprovalReference"]
    if normalized_gates["defaultCandidate"]["passed"]:
        approval = safe_evidence_path(approval)
    elif approval is not None:
        raise CertificationError("unexpected-owner-approval-reference")
    recommendation_state = assessment["recommendationStatus"]
    if normalized_gates["recommended"]["passed"] != (recommendation_state == "recommended"):
        raise CertificationError("recommendation-gate-mismatch")
    if recommendation_state in {"recommended", "candidate"} and not any(
        assessment["tasks"][task] == "passed" for task in TASKS
    ):
        raise CertificationError("recommendation-task-evidence-required")
    if recommendation_state == "recommended" and assessment["fitStatus"] not in {"comfortable", "workable"}:
        raise CertificationError("unsafe-recommendation-fit")
    if normalized_gates["defaultCandidate"]["passed"] and (
        assessment["fitStatus"] not in {"comfortable", "workable"}
        or any(assessment["tasks"][task] != "passed" for task in TASKS)
    ):
        raise CertificationError("default-candidate-task-and-fit-required")
    label = "Failed or needs retest" if failed else highest_label
    return {
        "modelId": model_id, "identity": normalized_identity,
        "environment": normalized_environment, "assessment": assessment, "label": label,
        "nextGate": None if failed else next_gate, "gates": normalized_gates,
        "ownerApprovalReference": approval,
        "automaticPromotionAllowed": False,
    }


def build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    records = [normalize_record(item) for item in manifest["records"]]
    ids = [item["modelId"] for item in records]
    if len(ids) != len(set(ids)):
        raise CertificationError("duplicate-certification-record")
    label_counts = {
        label: sum(item["label"] == label for item in records)
        for label in [name for _, name in GATES] + ["Failed or needs retest"]
    }
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-model-certification-report",
        "generatedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "orderedLabels": [label for _, label in GATES] + ["Failed or needs retest"],
        "records": sorted(records, key=lambda item: item["modelId"]),
        "labelCounts": label_counts,
        "disclosures": {
            "automaticPromotionPerformed": False,
            "defaultSelectionChanged": False,
            "privateMachineIdentityRetained": False,
            "providerEndpointRetained": False,
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha 2 model certification report", "",
        "This report applies ordered evidence gates. A result at one level does not",
        "claim later levels, change the automatic model default, or certify untested",
        "hardware and operating-system combinations.", "",
        f"Generated: `{report['generatedAtUtc']}`", "",
        "| Model | Hardware and OS | Test scope | Fit and execution | Task fit | Recommendation | Current gate |", "|---|---|---|---|---|---|---|",
    ]
    for item in report["records"]:
        identity, environment = item["identity"], item["environment"]
        assessment = item["assessment"]
        task_fit = ", ".join(f"{task}: {assessment['tasks'][task]}" for task in TASKS)
        lines.append(
            f"| {identity['model']} | {environment['acceleratorModel']} · {environment['operatingSystem']} | "
            f"{assessment['campaignScope']} | {assessment['fitStatus']} · {assessment['executionMode']} | "
            f"{task_fit} | **{assessment['recommendationStatus']}** · {assessment['recommendationRole']} | "
            f"**{item['label']}** · next: {item['nextGate'] or '—'} |"
        )
    lines.extend(["", "No automatic promotion or default-selection change was performed.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    if any(path.exists() or path.is_symlink() for path in (args.output_json, args.output_markdown)):
        parser.error("output already exists or is unsafe")
    try:
        report = build_report(load_manifest(args.input))
        for path in (args.output_json, args.output_markdown):
            path.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.output_markdown.write_text(markdown(report), encoding="utf-8")
    except (CertificationError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({"records": len(report["records"]), "automaticPromotionPerformed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
