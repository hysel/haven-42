#!/usr/bin/env python3
"""Run resumable 30-minute reliability soaks for Mac core-pass candidates."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"
VALIDATOR_PATH = ROOT / "scripts/validate-alpha2-macos-model-qualification-result.py"
MINUTES_PER_MODEL = 30
INTERVAL_SECONDS = 30


class SoakError(ValueError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise SoakError("module-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def checkpoint_base(plan: dict[str, Any], qualification: dict[str, Any], runner: Any, host: dict[str, Any], expected: list[str]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "haven42-apple-silicon-model-soak-result",
        "release": plan["release"],
        "status": "running",
        "planCanonicalSha256": runner.canonical_sha256(plan),
        "qualificationCanonicalSha256": runner.canonical_sha256(qualification),
        "runtime": {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")},
        "hardwareProfile": host | {"profileId": plan["hardwareProfile"]["id"]},
        "requestedMinutesPerModel": MINUTES_PER_MODEL,
        "intervalSeconds": INTERVAL_SECONDS,
        "modelIdsExpected": expected,
        "results": [],
        "rawPromptsOrResponsesRetained": False,
        "privateIdentityRetained": False,
        "automaticDefaultChangeAllowed": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticSupportChangeAllowed": False,
    }


def validate_resume(value: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    keys = ("schemaVersion", "kind", "release", "planCanonicalSha256", "qualificationCanonicalSha256", "runtime", "hardwareProfile", "requestedMinutesPerModel", "intervalSeconds", "modelIdsExpected")
    if any(value.get(key) != expected.get(key) for key in keys):
        raise SoakError("stale-or-invalid-resume-checkpoint")
    records = value.get("results")
    if not isinstance(records, list):
        raise SoakError("stale-or-invalid-resume-checkpoint")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or record.get("modelId") in seen or record.get("modelId") not in expected["modelIdsExpected"] or record.get("status") not in {"passed", "failed"}:
            raise SoakError("stale-or-invalid-resume-checkpoint")
        seen.add(record["modelId"])
    return records


def aggregate_cycle(result: dict[str, Any]) -> tuple[int, int, float, bool]:
    metrics, checks = result.get("metrics"), result.get("checks")
    if not isinstance(metrics, dict) or not isinstance(checks, dict):
        raise SoakError("invalid-cycle-result")
    output_tokens = 0
    rates: list[float] = []
    evidence_ok = result.get("corePassed") is True
    for name, check in checks.items():
        measurement = metrics.get(name)
        if not isinstance(check, dict) or check.get("status") != "passed" or check.get("responseRetained") is not False or not isinstance(measurement, dict):
            evidence_ok = False
            continue
        if measurement.get("unloadPassed") is not True or measurement.get("fullMetalResidency") is not True:
            evidence_ok = False
        if isinstance(measurement.get("outputTokens"), int):
            output_tokens += measurement["outputTokens"]
        if isinstance(measurement.get("tokensPerSecond"), (int, float)):
            rates.append(float(measurement["tokensPerSecond"]))
    return len(checks), output_tokens, (sum(rates) / len(rates) if rates else 0.0), evidence_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_result", type=Path)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pull-missing", action="store_true")
    parser.add_argument("--remove-new-models", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    runner = load_module("mac_qualification_runner", RUNNER_PATH)
    validator = load_module("mac_qualification_validator", VALIDATOR_PATH)
    partial = args.output.with_name(args.output.name + ".partial")

    def stop_for_signal(signum, frame):
        raise KeyboardInterrupt(f"signal-{signum}")

    signal.signal(signal.SIGTERM, stop_for_signal)
    signal.signal(signal.SIGINT, stop_for_signal)
    try:
        plan = runner.load_json(args.plan)
        qualification = runner.load_json(args.qualification_result)
        validator.validate_result(qualification, plan, runner)
        candidates = runner.validate_plan(plan, ROOT)
        expected = [record["modelId"] for record in qualification["results"] if record["status"] == "passed"]
        if not expected:
            raise SoakError("no-core-pass-candidates")
        origin = runner.validate_origin(args.origin)
        host = runner.host_preflight(plan)
        if runner.request_json(origin, "/api/version", timeout=20) != {"version": plan["runtime"]["version"]}:
            raise SoakError("runtime-version-mismatch")
        report = checkpoint_base(plan, qualification, runner, host, expected)
        if args.resume and partial.exists():
            report["results"] = validate_resume(runner.load_json(partial), report)
        elif partial.exists():
            raise SoakError("partial-result-exists-use-resume-or-new-output")
        completed = {record["modelId"] for record in report["results"]}
        atomic_write(partial, report)
        print(json.dumps({"event": "soak-started", "modelsExpected": len(expected), "modelsPreviouslyCompleted": len(completed)}, sort_keys=True), flush=True)
        for ordinal, model_id in enumerate(expected, start=1):
            if model_id in completed:
                continue
            candidate, pulled = candidates[model_id], False
            model = candidate["model"]
            started: float | None = None
            cycles = samples = output_tokens = unload_proofs = 0
            rates: list[float] = []
            failure: str | None = None
            removed: bool | None = None
            print(json.dumps({"event": "soak-model-started", "modelId": model_id, "ordinal": ordinal, "total": len(expected)}, sort_keys=True), flush=True)
            try:
                installed = runner.installed_models(origin)
                if model not in installed:
                    if not args.pull_missing:
                        raise SoakError("model-not-installed")
                    runner.request_json(origin, "/api/pull", {"model": model, "stream": False}, timeout=3600)
                    pulled = True
                if runner.installed_models(origin).get(model) != candidate["manifestDigest"]:
                    raise SoakError("manifest-digest-mismatch")
                started = time.monotonic()
                deadline = started + MINUTES_PER_MODEL * 60
                while time.monotonic() < deadline:
                    cycle = runner.run_candidate(origin, candidate)
                    cycle_samples, cycle_tokens, rate, evidence_ok = aggregate_cycle(cycle)
                    cycles += 1
                    samples += cycle_samples
                    output_tokens += cycle_tokens
                    unload_proofs += sum(item.get("unloadPassed") is True for item in cycle["metrics"].values())
                    if rate:
                        rates.append(rate)
                    if not evidence_ok:
                        failure = "task-residency-or-unload-gate-failed"
                        break
                    remaining = deadline - time.monotonic()
                    if remaining > 0:
                        time.sleep(min(INTERVAL_SECONDS, remaining))
            except (SoakError, runner.QualificationError) as error:
                failure = str(error)
            finally:
                try:
                    unloaded = runner.unload(origin, model)
                except runner.QualificationError:
                    unloaded = False
                if not unloaded and failure is None:
                    failure = "final-unload-failed"
                if pulled and args.remove_new_models:
                    try:
                        runner.request_json(origin, "/api/delete", {"model": model}, timeout=120)
                        removed = model not in runner.installed_models(origin)
                    except runner.QualificationError:
                        removed = False
                    if not removed and failure is None:
                        failure = "temporary-model-cleanup-failed"
            elapsed = round(time.monotonic() - started, 3) if started is not None else 0.0
            if elapsed < MINUTES_PER_MODEL * 60 and failure is None:
                failure = "minimum-duration-not-met"
            record = {"modelId": model_id, "model": model, "manifestDigest": candidate["manifestDigest"], "status": "passed" if failure is None else "failed", "durationSeconds": elapsed, "cycles": cycles, "samples": samples, "outputTokens": output_tokens, "averageTokensPerSecond": round(sum(rates) / len(rates), 3) if rates else None, "unloadProofs": unload_proofs, "temporaryModelPulled": pulled, "temporaryModelRemoved": removed, "responseRetained": False}
            if failure is not None:
                record["errorCode"] = failure
            report["results"].append(record)
            atomic_write(partial, report)
            print(json.dumps({"event": "soak-model-finished", "modelId": model_id, "status": record["status"]}, sort_keys=True), flush=True)
        report["status"] = "completed"
        report["observedAtUtc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        atomic_write(partial, report)
        os.replace(partial, args.output)
        print(json.dumps({"event": "soak-finished", "passed": sum(item["status"] == "passed" for item in report["results"]), "failed": sum(item["status"] == "failed" for item in report["results"])}, sort_keys=True), flush=True)
        return 0 if all(item["status"] == "passed" for item in report["results"]) else 1
    except KeyboardInterrupt:
        print(json.dumps({"event": "soak-interrupted", "resumeAvailable": partial.exists()}, sort_keys=True), file=sys.stderr, flush=True)
        return 130
    except (SoakError, runner.QualificationError, validator.ResultError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
