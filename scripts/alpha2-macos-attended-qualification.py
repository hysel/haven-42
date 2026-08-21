#!/usr/bin/env python3
"""Collect enumerated, sanitized results for attended macOS qualification gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time


SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
CHOICES = {"p": "passed", "f": "failed", "b": "blocked", "n": "not-run"}
REASONS = {
    "passed": "verified-as-instructed",
    "failed": "acceptance-condition-not-met",
    "blocked": "prerequisite-unavailable",
    "not-run": "operator-deferred",
}


class AttendedQualificationError(ValueError):
    pass


def load_plan(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value) != {"schemaVersion", "kind", "release", "profileId", "privacy", "gates", "authority"}
        or value.get("schemaVersion") != 1
        or value.get("kind") != "haven42-macos-attended-qualification-plan"
        or value.get("privacy") != {
            "freeformNotesAllowed": False,
            "privateIdentityAllowed": False,
            "privatePathsAllowed": False,
            "rawUserContentAllowed": False,
            "rawClipboardContentAllowed": False,
        }
        or value.get("authority") != {
            "automaticPassAllowed": False,
            "releaseAdmissionAllowed": False,
            "supportClaimAllowed": False,
            "productDataWriteAllowed": False,
        }
        or not isinstance(value.get("gates"), list)
        or not value["gates"]
    ):
        raise AttendedQualificationError("plan-invalid")
    if any(not isinstance(gate, dict) or set(gate) != {"id", "title", "instruction", "passCondition"} for gate in value["gates"]):
        raise AttendedQualificationError("plan-gates-invalid")
    ids = [gate["id"] for gate in value["gates"]]
    if len(ids) != len(set(ids)) or any(not isinstance(item, str) or not item for item in ids):
        raise AttendedQualificationError("plan-gates-invalid")
    if any(not isinstance(gate[key], str) or not gate[key].strip() for gate in value["gates"] for key in ("title", "instruction", "passCondition")):
        raise AttendedQualificationError("plan-gates-invalid")
    return value


def plan_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(plan: dict, *, artifact_sha256: str, source_commit: str, input_fn=input, output_fn=print) -> dict:
    if sys.platform != "darwin":
        raise AttendedQualificationError("physical-macos-required")
    if SHA256.fullmatch(artifact_sha256) is None or COMMIT.fullmatch(source_commit) is None:
        raise AttendedQualificationError("evidence-binding-invalid")
    output_fn("Haven 42 attended macOS qualification")
    output_fn("Record only the fixed outcomes shown. Do not enter names, paths, clipboard text, or notes.")
    gates = {}
    for index, gate in enumerate(plan["gates"], start=1):
        output_fn(f"\n[{index}/{len(plan['gates'])}] {gate['title']}")
        output_fn(gate["instruction"])
        output_fn(f"Pass only when: {gate['passCondition']}")
        while True:
            answer = input_fn("Outcome: [p]assed [f]ailed [b]locked [n]ot run: ").strip().lower()
            if answer in CHOICES:
                break
            output_fn("Choose only p, f, b, or n.")
        status = CHOICES[answer]
        gates[gate["id"]] = {"status": status, "reasonCode": REASONS[status]}
    statuses = {item["status"] for item in gates.values()}
    overall = "passed" if statuses == {"passed"} else ("failed" if "failed" in statuses else "incomplete")
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-attended-qualification-result",
        "release": plan["release"],
        "profileId": plan["profileId"],
        "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": overall,
        "bindings": {
            "planSha256": "",  # populated by main from the exact plan bytes
            "artifactSha256": artifact_sha256,
            "sourceCommit": source_commit,
        },
        "gates": gates,
        "privacy": {
            "freeformNotesRetained": False,
            "privateIdentityRetained": False,
            "privatePathsRetained": False,
            "rawUserContentRetained": False,
            "rawClipboardContentRetained": False,
        },
        "authority": {
            "releaseAdmissionGranted": False,
            "supportClaimGranted": False,
            "productionAdmissionGranted": False,
        },
    }


def write_atomic(path: Path, value: dict) -> None:
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--artifact-sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not sys.stdin.isatty():
        parser.error("interactive-terminal-required")
    try:
        plan = load_plan(args.plan)
        result = collect(plan, artifact_sha256=args.artifact_sha256, source_commit=args.source_commit)
        result["bindings"]["planSha256"] = plan_sha256(args.plan)
        write_atomic(args.output, result)
    except (OSError, UnicodeError, json.JSONDecodeError, AttendedQualificationError) as error:
        parser.error(str(error))
    print(f"Sanitized result written: {args.output}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
