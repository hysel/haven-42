#!/usr/bin/env python3
"""Run the fixed Windows Alpha response-policy matrix through Haven's text path."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
SCRIPTS = ROOT / "scripts"
for search_path in (str(WEB), str(SCRIPTS)):
    if search_path not in sys.path:
        sys.path.insert(0, search_path)

from server import HavenState  # noqa: E402


MATRIX_PATH = ROOT / "config" / "windows-alpha-response-guardrail-cases.json"
RECOMMENDATIONS_PATH = ROOT / "config" / "text-capability-model-recommendations.json"
OUTPUT_PARENT = (ROOT / "dist" / "local-review").resolve()
MODEL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}")
MODEL_DIGEST = re.compile(r"[a-f0-9]{64}")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("invalid-compliance-contract")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_plan(
    candidate_model: str | None = None,
    candidate_digest: str | None = None,
    candidate_capabilities: tuple[str, ...] = (),
    candidate_case_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    matrix = _load(MATRIX_PATH)
    recommendations = _load(RECOMMENDATIONS_PATH)
    capabilities = matrix.get("capabilities")
    cases = matrix.get("cases")
    catalog = recommendations.get("capabilities")
    if (
        matrix.get("schemaVersion") != 1
        or matrix.get("executionStatus") != "native-evaluation-required"
        or capabilities != ["general.chat", "content.write", "content.summarize"]
        or not isinstance(cases, list) or len(cases) != 10
        or not isinstance(catalog, dict)
    ):
        raise ValueError("invalid-compliance-contract")
    seen_cases: set[str] = set()
    normalized_cases: list[dict[str, str]] = []
    for case in cases:
        if (
            not isinstance(case, dict)
            or set(case) != {"id", "severity", "prompt", "expectedBehavior", "forbiddenBehavior"}
            or not isinstance(case["id"], str) or not re.fullmatch(r"[a-z0-9-]{3,64}", case["id"])
            or case["id"] in seen_cases
            or case["severity"] not in {"critical", "high"}
            or any(not isinstance(case[field], str) or not case[field].strip() for field in (
                "prompt", "expectedBehavior", "forbiddenBehavior",
            ))
            or any(len(case[field]) > 1000 for field in ("prompt", "expectedBehavior", "forbiddenBehavior"))
        ):
            raise ValueError("invalid-compliance-case")
        seen_cases.add(case["id"])
        normalized_cases.append(dict(case))
    cells: list[dict[str, str]] = []
    identities: set[tuple[str, str]] = set()
    if candidate_model is not None or candidate_digest is not None:
        if (
            not isinstance(candidate_model, str) or not MODEL_NAME.fullmatch(candidate_model)
            or not isinstance(candidate_digest, str) or not MODEL_DIGEST.fullmatch(candidate_digest)
            or not candidate_capabilities
            or any(capability not in capabilities for capability in candidate_capabilities)
            or len(set(candidate_capabilities)) != len(candidate_capabilities)
            or not candidate_case_ids
            or any(case_id not in seen_cases for case_id in candidate_case_ids)
            or len(set(candidate_case_ids)) != len(candidate_case_ids)
        ):
            raise ValueError("invalid-candidate-compliance-plan")
        identities.add((candidate_model, candidate_digest))
        for capability_id in candidate_capabilities:
            for case in normalized_cases:
                if case["id"] not in candidate_case_ids:
                    continue
                cells.append({
                    "capabilityId": capability_id,
                    "model": candidate_model,
                    "modelDigest": candidate_digest,
                    "caseId": case["id"],
                    "severity": case["severity"],
                    "prompt": case["prompt"],
                    "expectedBehavior": case["expectedBehavior"],
                    "forbiddenBehavior": case["forbiddenBehavior"],
                })
    else:
        for capability_id in capabilities:
            records = catalog.get(capability_id)
            if not isinstance(records, list):
                raise ValueError("invalid-compliance-recommendations")
            eligible = [record for record in records if record.get("evidenceStatus") == "passed"]
            for record in eligible:
                model = record.get("model")
                digest = record.get("digest")
                if (
                    not isinstance(model, str) or not MODEL_NAME.fullmatch(model)
                    or not isinstance(digest, str) or not MODEL_DIGEST.fullmatch(digest)
                ):
                    raise ValueError("invalid-compliance-model-identity")
                identities.add((model, digest))
                for case in normalized_cases:
                    cells.append({
                        "capabilityId": capability_id,
                        "model": model,
                        "modelDigest": digest,
                        "caseId": case["id"],
                        "severity": case["severity"],
                        "prompt": case["prompt"],
                        "expectedBehavior": case["expectedBehavior"],
                        "forbiddenBehavior": case["forbiddenBehavior"],
                    })
    if not cells or len(cells) > 300:
        raise ValueError("invalid-compliance-plan-size")
    return {
        "schemaVersion": 1,
        "kind": "windows-alpha-response-compliance-plan",
        "candidateOnly": candidate_model is not None,
        "matrixSha256": _sha256(MATRIX_PATH),
        "recommendationsSha256": _sha256(RECOMMENDATIONS_PATH),
        "models": [
            {"model": model, "modelDigest": digest}
            for model, digest in sorted(identities)
        ],
        "cellCount": len(cells),
        "cells": cells,
    }


def _output_directory(raw: str) -> Path:
    target = (OUTPUT_PARENT / raw).resolve()
    if target.parent != OUTPUT_PARENT or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", target.name):
        raise ValueError("invalid-compliance-output-directory")
    if target.exists() and (target.is_symlink() or not target.is_dir() or any(target.iterdir())):
        raise ValueError("compliance-output-directory-not-empty")
    target.mkdir(parents=True, exist_ok=True)
    return target


def _write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_review_packet(path: Path, evidence: dict[str, Any]) -> None:
    lines = [
        "# Windows Alpha response compliance review",
        "",
        "This is local review evidence. Prompts are fixed public fixtures; responses must be reviewed manually.",
        "Passing this behavior check is not security evidence.",
        "",
    ]
    for index, result in enumerate(evidence["results"], start=1):
        lines.extend([
            f"## {index}. {result['capabilityId']} · {result['caseId']} · {result['severity']}",
            "",
            f"Model: `{result['model']}` (`{result['modelDigest']}`)",
            "",
            f"Expected: {result['expectedBehavior']}",
            "",
            f"Forbidden: {result['forbiddenBehavior']}",
            "",
            "Response:",
            "",
            "```text",
            result["response"].replace("```", "` ` `"),
            "```",
            "",
            "Reviewer result: [ ] Pass  [ ] Critical violation  [ ] High violation",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def execute(
    endpoint: str,
    output_name: str,
    timeout_seconds: int,
    candidate_model: str | None = None,
    candidate_digest: str | None = None,
    candidate_capabilities: tuple[str, ...] = (),
    candidate_case_ids: tuple[str, ...] = (),
) -> Path:
    plan = build_plan(candidate_model, candidate_digest, candidate_capabilities, candidate_case_ids)
    output = _output_directory(output_name)
    evidence: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "windows-alpha-response-compliance-evidence",
        "status": "in-progress",
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "endpointRecorded": False,
        "authenticationRecorded": False,
        "matrixSha256": plan["matrixSha256"],
        "recommendationsSha256": plan["recommendationsSha256"],
        "cellCount": plan["cellCount"],
        "results": [],
        "humanReviewRequired": True,
        "securityEvidence": False,
        "automaticSelectionAuthority": False,
        "candidateOnly": plan["candidateOnly"],
    }
    evidence_path = output / "evidence.json"
    _write_json(evidence_path, evidence)
    with tempfile.TemporaryDirectory(prefix="haven42-response-compliance-") as raw:
        state = HavenState(diagnostic_root=Path(raw) / "Haven42-Logs")
        try:
            connection = state.connect(endpoint, timeout_seconds, 0, "none", "")
            if connection.get("connected") is not True:
                raise RuntimeError("provider-connection-not-confirmed")
            with state.lock:
                installed = dict(state.model_digests)
            for identity in plan["models"]:
                if installed.get(identity["model"]) != identity["modelDigest"]:
                    raise RuntimeError("eligible-model-digest-not-installed")
            for index, cell in enumerate(plan["cells"], start=1):
                print(
                    f"[{index}/{plan['cellCount']}] {cell['capabilityId']} · {cell['caseId']}",
                    flush=True,
                )
                result = state.run_text_capability(
                    cell["capabilityId"],
                    cell["model"],
                    [{"role": "user", "content": cell["prompt"]}],
                    [],
                    [],
                    False,
                )
                evidence["results"].append({
                    **cell,
                    "response": result["content"],
                    "runtimeVersion": result["runtimeVersion"],
                    "modelUnloaded": result["modelUnloaded"],
                })
                _write_json(evidence_path, evidence)
            if not state.unload_used_models():
                raise RuntimeError("model-unload-failed")
            evidence["status"] = "awaiting-human-review"
            evidence["completedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            evidence["allModelsUnloaded"] = True
            _write_json(evidence_path, evidence)
            _write_review_packet(output / "review-packet.md", evidence)
        finally:
            state.unload_used_models()
            state.diagnostics.close()
            state.diagnostics.remove_all()
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint")
    parser.add_argument("--output-name")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--candidate-model")
    parser.add_argument("--candidate-digest")
    parser.add_argument("--candidate-capabilities", default="")
    parser.add_argument("--candidate-case-ids", default="")
    args = parser.parse_args()
    candidate_capabilities = tuple(filter(None, args.candidate_capabilities.split(",")))
    candidate_case_ids = tuple(filter(None, args.candidate_case_ids.split(",")))
    if args.plan_only:
        plan = build_plan(
            args.candidate_model,
            args.candidate_digest,
            candidate_capabilities,
            candidate_case_ids,
        )
        print(json.dumps({key: value for key, value in plan.items() if key != "cells"}, indent=2, sort_keys=True))
        return 0
    if not args.endpoint or not args.output_name or not 10 <= args.timeout_seconds <= 600:
        parser.error("--endpoint, --output-name, and a bounded timeout are required")
    output = execute(
        args.endpoint,
        args.output_name,
        args.timeout_seconds,
        args.candidate_model,
        args.candidate_digest,
        candidate_capabilities,
        candidate_case_ids,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
