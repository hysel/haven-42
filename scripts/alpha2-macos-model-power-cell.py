#!/usr/bin/env python3
"""Collect model-bound Apple SoC power evidence with a restricted helper.

This is a maintainer qualification tool, not an end-user installer. It binds
one exact reviewed model to the pinned runtime, warms it on Metal, runs a
bounded generation while the root-owned powermetrics helper samples, discards
raw telemetry and model text, unloads the model, and optionally removes only a
model pulled by this invocation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"
SUMMARY_PATH = ROOT / "scripts/summarize-macos-powermetrics.py"
DEFAULT_HELPER = Path("/usr/local/libexec/haven42-powermetrics-sample")


class PowerCellError(ValueError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise PowerCellError("module-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_helper(path: Path) -> None:
    try:
        info = path.stat()
    except OSError as error:
        raise PowerCellError("power-helper-unavailable") from error
    if path.is_symlink() or not path.is_file() or info.st_uid != 0 or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise PowerCellError("unsafe-power-helper")


def validate_warmup(response: dict[str, Any], text: str, residency: dict[str, Any]) -> None:
    """Require a completed, non-empty generation fully resident on Metal.

    Exact instruction following belongs to the qualification workload.  A
    power cell only needs to prove that the reviewed model completed a real
    generation on the intended accelerator before sampling begins.
    """
    if response.get("done") is not True or not text.strip():
        raise PowerCellError("warmup-generation-failed")
    if not residency.get("fullMetalResidency"):
        raise PowerCellError("warmup-metal-residency-failed")


def build_report(plan: dict[str, Any], candidate: dict[str, Any], runtime: dict[str, Any], host: dict[str, Any], summary: dict[str, Any], workload: dict[str, Any], cleanup: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-macos-model-power-result",
        "release": plan["release"],
        "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "passed" if cleanup["unloadPassed"] and cleanup["temporaryModelRemoved"] is not False else "failed",
        "planCanonicalSha256": runtime["planCanonicalSha256"],
        "runtime": {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")},
        "hardwareProfile": host | {"profileId": plan["hardwareProfile"]["id"]},
        "model": {key: candidate[key] for key in ("modelId", "model", "manifestDigest", "modelBytes")},
        "workload": workload,
        "appleSocPower": summary,
        "measurementBoundary": "Apple powermetrics CPU/GPU/ANE estimates; not wall-outlet or whole-system energy",
        "cleanup": cleanup,
        "rawTelemetryRetained": False,
        "rawPromptsOrResponsesRetained": False,
        "privateIdentityRetained": False,
        "automaticDefaultChangeAllowed": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticSupportChangeAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_id")
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--helper", type=Path, default=DEFAULT_HELPER)
    parser.add_argument("--pull-missing", action="store_true")
    parser.add_argument("--remove-new-model", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runner = load_module("mac_qualification_runner", RUNNER_PATH)
    summarizer = load_module("mac_power_summary", SUMMARY_PATH)
    pulled = False
    cleanup = {"unloadPassed": False, "temporaryModelRemoved": None}
    try:
        plan = runner.load_json(args.plan)
        candidates = runner.validate_plan(plan, ROOT)
        if args.model_id not in candidates:
            raise PowerCellError("unreviewed-model-id")
        candidate = candidates[args.model_id]
        origin = runner.validate_origin(args.origin)
        host = runner.host_preflight(plan)
        version = runner.request_json(origin, "/api/version", timeout=20)
        if version != {"version": plan["runtime"]["version"]}:
            raise PowerCellError("runtime-version-mismatch")
        validate_helper(args.helper)
        installed = runner.installed_models(origin)
        if candidate["model"] not in installed:
            if not args.pull_missing:
                raise PowerCellError("model-not-installed")
            runner.request_json(origin, "/api/pull", {"model": candidate["model"], "stream": False}, timeout=3600)
            pulled = True
        if runner.installed_models(origin).get(candidate["model"]) != candidate["manifestDigest"]:
            raise PowerCellError("manifest-digest-mismatch")
        warm = runner.request_json(origin, "/api/generate", {"model": candidate["model"], "prompt": "Reply exactly: READY", "think": False, "stream": False, "keep_alive": "5m", "options": {"temperature": 0, "seed": 42, "num_predict": 16}}, timeout=600)
        residency = runner.residency(origin, candidate["model"])
        validate_warmup(warm, runner.response_text(warm, "/api/generate"), residency)
        sampler = subprocess.Popen(["sudo", "-n", str(args.helper)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        generated_tokens = 0
        requests = 0
        started = time.monotonic()
        while sampler.poll() is None:
            value = runner.request_json(origin, "/api/generate", {"model": candidate["model"], "prompt": "Write a concise, numbered software test plan with distinct steps and continue until the token limit.", "think": False, "stream": False, "keep_alive": "5m", "options": {"temperature": 0, "seed": 42, "num_predict": 512}}, timeout=900)
            generated_tokens += value.get("eval_count", 0) if isinstance(value.get("eval_count"), int) else 0
            requests += 1
        raw, error_text = sampler.communicate(timeout=30)
        if sampler.returncode != 0:
            raise PowerCellError("power-helper-failed")
        summary = summarizer.summarize(raw)
        cleanup["unloadPassed"] = runner.unload(origin, candidate["model"])
        if pulled and args.remove_new_model:
            runner.request_json(origin, "/api/delete", {"model": candidate["model"]}, timeout=120)
            cleanup["temporaryModelRemoved"] = candidate["model"] not in runner.installed_models(origin)
        workload = {"kind": "bounded-repeat-generation", "requests": requests, "outputTokens": generated_tokens, "durationSeconds": round(time.monotonic() - started, 3), "responseRetained": False, "fullMetalResidencyObserved": True}
        report = build_report(plan, candidate, {"planCanonicalSha256": runner.canonical_sha256(plan)}, host, summary, workload, cleanup)
        encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name + ".tmp")
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, args.output)
        print(encoded, end="")
        return 0 if report["status"] == "passed" else 1
    except (PowerCellError, runner.QualificationError, summarizer.PowerSummaryError, OSError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    finally:
        if "runner" in locals() and "origin" in locals() and "candidate" in locals():
            try:
                cleanup["unloadPassed"] = runner.unload(origin, candidate["model"])
            except Exception:
                pass
            if pulled and args.remove_new_model:
                try:
                    runner.request_json(origin, "/api/delete", {"model": candidate["model"]}, timeout=120)
                except Exception:
                    pass
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
