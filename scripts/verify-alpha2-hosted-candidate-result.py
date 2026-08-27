#!/usr/bin/env python3
"""Validate the sanitized hosted Alpha 2 candidate-build result."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "config" / "alpha-2-hosted-candidate-result.json"
EXPECTED_WORKFLOW = ROOT / ".github" / "workflows" / "alpha2-candidate.yml"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class HostedCandidateResultError(ValueError):
    """Raised when hosted candidate evidence is incomplete or overstated."""


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise HostedCandidateResultError("invalid-workflow-timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise HostedCandidateResultError("invalid-workflow-timestamp") from error


def _official_run_url(value: object, run_id: int) -> str:
    if not isinstance(value, str):
        raise HostedCandidateResultError("invalid-workflow-run-url")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or parsed.path != f"/hysel/haven-42/actions/runs/{run_id}"
        or parsed.query
        or parsed.fragment
    ):
        raise HostedCandidateResultError("invalid-workflow-run-url")
    return value


def _candidate(value: object, expected_platform: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "platform", "builderRunner", "archive", "knownLimitations",
    }:
        raise HostedCandidateResultError("invalid-candidate-shape")
    expected = {
        "windows-x64": ("windows-2025", ".zip"),
        "linux-x64": ("ubuntu-24.04", ".tar.gz"),
    }
    runner, suffix = expected[expected_platform]
    if value["platform"] != expected_platform or value["builderRunner"] != runner:
        raise HostedCandidateResultError("candidate-platform-mismatch")
    archive = value["archive"]
    if not isinstance(archive, dict) or set(archive) != {"name", "sha256", "sizeBytes"}:
        raise HostedCandidateResultError("invalid-candidate-archive")
    if (
        archive["name"] != f"haven42-0.4.0-alpha.2-{expected_platform}-unsigned{suffix}"
        or not isinstance(archive["sha256"], str)
        or not HEX64.fullmatch(archive["sha256"])
        or not isinstance(archive["sizeBytes"], int)
        or isinstance(archive["sizeBytes"], bool)
        or archive["sizeBytes"] <= 0
    ):
        raise HostedCandidateResultError("invalid-candidate-archive")
    limitations = value["knownLimitations"]
    if (
        not isinstance(limitations, dict)
        or set(limitations) != {"name", "sha256"}
        or limitations["name"] != "KNOWN-LIMITATIONS.md"
        or not isinstance(limitations["sha256"], str)
        or not HEX64.fullmatch(limitations["sha256"])
    ):
        raise HostedCandidateResultError("invalid-known-limitations")
    return value


def verify(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "schemaVersion", "recordId", "version", "workflow", "workflowRun",
        "candidates", "pairVerification", "artifactRetentionDays", "authority",
    }:
        raise HostedCandidateResultError("invalid-result-shape")
    if (
        value["schemaVersion"] != 1
        or value["recordId"] != "haven42.alpha2.hosted-candidate-result"
        or value["version"] != "0.4.0-alpha.2"
        or value["workflow"] != ".github/workflows/alpha2-candidate.yml"
        or not EXPECTED_WORKFLOW.is_file()
    ):
        raise HostedCandidateResultError("invalid-result-identity")

    run = value["workflowRun"]
    if not isinstance(run, dict) or set(run) != {
        "id", "url", "event", "conclusion", "sourceCommit", "createdAt",
        "completedAt", "jobs",
    }:
        raise HostedCandidateResultError("invalid-workflow-run")
    if (
        not isinstance(run["id"], int)
        or isinstance(run["id"], bool)
        or run["id"] <= 0
        or run["event"] != "workflow_dispatch"
        or run["conclusion"] != "success"
        or not isinstance(run["sourceCommit"], str)
        or not COMMIT.fullmatch(run["sourceCommit"])
    ):
        raise HostedCandidateResultError("invalid-workflow-run")
    _official_run_url(run["url"], run["id"])
    if _timestamp(run["completedAt"]) < _timestamp(run["createdAt"]):
        raise HostedCandidateResultError("invalid-workflow-timestamp")
    expected_jobs = [
        {"name": "Windows Alpha 2 candidate", "conclusion": "success"},
        {"name": "Linux Alpha 2 candidate", "conclusion": "success"},
        {"name": "Verify Alpha 2 candidate pair", "conclusion": "success"},
    ]
    if run["jobs"] != expected_jobs:
        raise HostedCandidateResultError("hosted-candidate-jobs-incomplete")

    candidates = value["candidates"]
    if not isinstance(candidates, list) or len(candidates) != 2:
        raise HostedCandidateResultError("invalid-candidate-set")
    windows = _candidate(candidates[0], "windows-x64")
    linux = _candidate(candidates[1], "linux-x64")
    limitations_match = (
        windows["knownLimitations"]["sha256"]
        == linux["knownLimitations"]["sha256"]
    )

    pair = value["pairVerification"]
    if pair != {
        "sameSourceCommit": True,
        "sameKnownLimitations": True,
        "candidatePairReadyForNativeValidation": True,
        "nativeValidationComplete": False,
    } or not limitations_match:
        raise HostedCandidateResultError("candidate-pair-not-ready")
    if value["artifactRetentionDays"] != 7:
        raise HostedCandidateResultError("invalid-artifact-retention")
    if value["authority"] != {
        "signed": False,
        "publicationAllowed": False,
        "productionReady": False,
    }:
        raise HostedCandidateResultError("publication-authority-overstated")

    return {
        "SchemaVersion": 1,
        "Version": value["version"],
        "WorkflowRunId": run["id"],
        "SourceCommit": run["sourceCommit"],
        "Platforms": [item["platform"] for item in candidates],
        "SameKnownLimitations": limitations_match,
        "CandidatePairReadyForNativeValidation": True,
        "NativeValidationComplete": False,
        "PublicationAllowed": False,
        "ProductionReady": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", default=str(DEFAULT_RECORD))
    args = parser.parse_args()
    path = Path(args.record).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise SystemExit(f"record must remain inside the repository: {error}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"record is unreadable: {error}")
    print(json.dumps(verify(value), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
