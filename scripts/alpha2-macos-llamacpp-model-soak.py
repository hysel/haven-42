#!/usr/bin/env python3
"""Run 30-minute reliability soaks for core-pass Apple M4 GGUF candidates."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "alpha2-macos-llamacpp-model-qualification.py"
MINUTES = 30


class SoakError(ValueError):
    pass


def load_runner():
    spec = importlib.util.spec_from_file_location("llamacpp_qualification", RUNNER)
    if not spec or not spec.loader:
        raise SoakError("runner-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_result", type=Path)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runner = load_runner()
    plan, qualification = runner.load_json(args.plan), runner.load_json(args.qualification_result)
    candidates = runner.validate_plan(plan, args.server, args.models)
    if qualification.get("planCanonicalSha256") != runner.canonical_sha256(plan):
        parser.error("qualification-plan-mismatch")
    passed = {record.get("modelId") for record in qualification.get("results", []) if record.get("corePassed") is True}
    selected = [candidate for candidate in candidates if candidate["modelId"] in passed]
    if not selected:
        parser.error("no-core-pass-candidates")
    report = {
        "schemaVersion": 1, "kind": "haven42-apple-silicon-llamacpp-model-soak-result", "release": plan["release"],
        "status": "running", "planCanonicalSha256": runner.canonical_sha256(plan),
        "qualificationCanonicalSha256": runner.canonical_sha256(qualification), "runtime": plan["runtime"],
        "hardwareProfile": plan["hardwareProfile"], "requestedMinutesPerModel": MINUTES,
        "modelIdsExpected": [candidate["modelId"] for candidate in selected], "results": [],
        "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False,
        "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False,
    }
    partial = args.output.with_name(args.output.name + ".partial")
    atomic_write(partial, report)
    for candidate in selected:
        started = time.monotonic()
        deadline = started + MINUTES * 60
        cycles = samples = output_tokens = unload_proofs = 0
        failure: str | None = None
        while time.monotonic() < deadline and failure is None:
            for name, body, validator in runner.task_cells():
                try:
                    check, metric = runner.run_cell(args.server, args.models / candidate["filename"], candidate["modelId"], body | {"model": candidate["modelId"]}, validator)
                except Exception as error:
                    failure = f"{name}:{type(error).__name__}"
                    break
                samples += 1
                output_tokens += int(metric.get("outputTokens", 0))
                unload_proofs += metric.get("unloadPassed") is True
                if check.get("status") != "passed":
                    failure = f"{name}:gate-failed"
                    break
            cycles += 1
            report["active"] = {"modelId": candidate["modelId"], "cycles": cycles, "samples": samples}
            atomic_write(partial, report)
        record = {
            "modelId": candidate["modelId"], "status": "passed" if failure is None else "failed",
            "requestedMinutes": MINUTES, "durationSeconds": round(time.monotonic() - started, 3),
            "cycles": cycles, "taskSamples": samples, "outputTokens": output_tokens,
            "unloadProofs": unload_proofs, "failureCode": failure, "responseRetained": False,
        }
        report["results"].append(record)
        report.pop("active", None)
        atomic_write(partial, report)
    report["status"] = "completed"
    report["observedAtUtc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    atomic_write(args.output, report)
    partial.unlink(missing_ok=True)
    print(json.dumps({"status": report["status"], "results": [{"modelId": record["modelId"], "status": record["status"]} for record in report["results"]]}, sort_keys=True))
    return 0 if all(record["status"] == "passed" for record in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
