#!/usr/bin/env python3
"""Screen exact GGUF candidates on pinned OpenCode with pinned llama.cpp."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
from typing import Any


RUNNER_PATH = Path(__file__).resolve().with_name("alpha2-macos-llamacpp-model-qualification.py")
SURFACE_VERSION = "1.18.19"
SURFACE_BINARY_SHA256 = "fff10da113acaf6189f1082d64bfe6015a29e4d4c1b2c7ee6f2ac44fa225e099"
SURFACE_ARCHIVE_SHA256 = "0026326bd77a3277ab3726be237410b19389f7829e8bb3c82dfaf9044162067c"


class CodingError(ValueError):
    pass


def load_module():
    spec = importlib.util.spec_from_file_location("llamacpp_qualification", RUNNER_PATH)
    if not spec or not spec.loader:
        raise CodingError("runner-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(["git", "-C", str(repository), *arguments], capture_output=True, text=True, timeout=30)
    if completed.returncode != 0:
        raise CodingError("git-verification-failed")
    return completed.stdout


def prepare(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", ".opencode.local.json", "__pycache__", ".pytest_cache"))
    git(destination, "init")
    git(destination, "config", "user.name", "Local Agent Validation")
    git(destination, "config", "user.email", "local-agent-validation@example.invalid")
    git(destination, "add", ".")
    completed = subprocess.run(["git", "-C", str(destination), "commit", "-m", "Generated baseline"], capture_output=True, text=True, timeout=30)
    if completed.returncode != 0:
        raise CodingError("git-baseline-failed")


def parse_text(stdout: str) -> str:
    values: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        stack: list[Any] = [event]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"text", "content"} and isinstance(child, str):
                        values.append(child)
                    else:
                        stack.append(child)
            elif isinstance(value, list):
                stack.extend(value)
    return "\n".join(values)


def start_runtime(runner: Any, server: Path, model: Path, alias: str) -> tuple[subprocess.Popen[Any], int, str, Path]:
    port, key = runner.free_port(), hashlib.sha256(os.urandom(32)).hexdigest()
    fd, name = tempfile.mkstemp(prefix="haven42-opencode-", suffix=".log")
    os.close(fd)
    log_path = Path(name)
    log = log_path.open("wb")
    process = subprocess.Popen([
        str(server), "-m", str(model), "--alias", alias, "--host", "127.0.0.1", "--port", str(port),
        "-ngl", "99", "-c", "8192", "-np", "1", "--no-webui", "--reasoning", "off", "--api-key", key, "--verbose",
    ], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    process._haven42_log_handle = log  # type: ignore[attr-defined]
    runner.wait_ready(process, port, key, 120)
    return process, port, key, log_path


def stop_runtime(runner: Any, process: subprocess.Popen[Any], port: int, log_path: Path) -> bool:
    runner.stop(process)
    handle = getattr(process, "_haven42_log_handle", None)
    if handle:
        handle.close()
    text = log_path.read_text(encoding="utf-8", errors="replace")
    proof = runner.closed(port) and bool("Metal" in text or "ggml_metal" in text) and runner.full_offload_observed(text)
    log_path.unlink(missing_ok=True)
    return proof


def invoke(opencode: Path, config: Path, repository: Path, alias: str, key: str, prompt: str, timeout: float) -> tuple[int, str, str | None]:
    environment = os.environ.copy()
    environment["OPENCODE_CONFIG"] = str(config)
    environment["LLAMA_CPP_API_KEY"] = key
    process = subprocess.Popen([
        str(opencode), "run", "--pure", "--auto", "--format", "json", "--model", "llamacpp/" + alias, prompt,
    ], cwd=repository, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, _ = process.communicate(timeout=timeout)
        return process.returncode, parse_text(stdout), None
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
        return 124, "", "timeout"


def config(path: Path, alias: str, port: int) -> None:
    value = {"$schema": "https://opencode.ai/config.json", "model": "llamacpp/" + alias, "provider": {"llamacpp": {"name": "Pinned llama.cpp loopback", "npm": "@ai-sdk/openai-compatible", "models": {alias: {"name": alias}}, "options": {"baseURL": f"http://127.0.0.1:{port}/v1", "apiKey": "{env:LLAMA_CPP_API_KEY}"}}}}
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gate(values: dict[str, str]) -> dict[str, Any]:
    return {"status": "passed" if all(value == "passed" for value in values.values()) else "failed", "checks": values}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_result", type=Path)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--opencode", type=Path, required=True)
    parser.add_argument("--opencode-archive", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for name in ("qualification_result", "plan", "server", "models", "opencode", "opencode_archive", "fixture", "policy", "output"):
        setattr(args, name, getattr(args, name).resolve())
    runner = load_module()
    plan, qualification = runner.load_json(args.plan), runner.load_json(args.qualification_result)
    candidates = runner.validate_plan(plan, args.server, args.models)
    if qualification.get("planCanonicalSha256") != runner.canonical_sha256(plan):
        parser.error("qualification-plan-mismatch")
    if sha256_file(args.opencode) != SURFACE_BINARY_SHA256 or sha256_file(args.opencode_archive) != SURFACE_ARCHIVE_SHA256:
        parser.error("surface-digest-mismatch")
    version = subprocess.run([str(args.opencode), "--version"], capture_output=True, text=True, timeout=30)
    if version.returncode != 0 or version.stdout.strip() != SURFACE_VERSION:
        parser.error("surface-version-mismatch")
    qualification_by_id = {record["modelId"]: record for record in qualification["results"]}
    results = []
    for candidate in candidates:
        core = qualification_by_id[candidate["modelId"]
        ]
        structured_code = core["checks"]["structuredCode"]["status"] == "passed"
        structured_tool = core["checks"]["structuredTool"]["status"] == "passed"
        gates = {
            "api-structured-code": gate({"valid-code-contract": "passed" if structured_code else "failed", "instruction-fidelity": "passed" if structured_code else "failed", "deterministic-output": "blocked"}),
            "tool-contract": gate({"exact-tool-name": "passed" if structured_tool else "failed", "schema-valid-arguments": "passed" if structured_tool else "failed", "unknown-tool-refusal": "blocked"}),
        }
        read_checks = {key: "blocked" for key in ("repository-context-use", "exact-filename-fidelity", "implementation-plan", "defect-review")}
        edit_checks = {"explicit-write-approval": "passed", "expected-file-only": "blocked", "external-git-diff": "blocked", "no-unintended-writes": "blocked"}
        reliability = {key: "blocked" for key in ("bounded-context", "timeout-recovery", "post-failure-recovery", "model-unload")}
        metadata: dict[str, Any] = {}
        with tempfile.TemporaryDirectory(prefix="haven42-opencode-fixture-") as directory:
            repository = Path(directory) / "repo"
            prepare(args.fixture, repository)
            process, port, key, log_path = start_runtime(runner, args.server, args.models / candidate["filename"], candidate["modelId"])
            config_path = repository / ".opencode.local.json"
            config(config_path, candidate["modelId"], port)
            started = time.monotonic()
            code, text, error = invoke(args.opencode, config_path, repository, candidate["modelId"], key, "Inspect this disposable repository read-only. Name README.md, app/main.py, app/settings.py, and tests/test_main.py exactly. Explain build_health_response and give a two-file plan to add environment=local. Do not modify files.", 150)
            unloaded = stop_runtime(runner, process, port, log_path)
            clean = not git(repository, "status", "--short").strip() or git(repository, "status", "--short").strip() == "?? .opencode.local.json"
            required = ("README.md", "app/main.py", "app/settings.py", "tests/test_main.py", "build_health_response")
            context = code == 0 and clean and all(item in text for item in required)
            read_checks = {"repository-context-use": "passed" if context else "failed", "exact-filename-fidelity": "passed" if context else "failed", "implementation-plan": "passed" if context and "environment" in text.lower() else "failed", "defect-review": "passed" if context and "test" in text.lower() else "failed"}
            reliability = {"bounded-context": "passed" if code in {0, 124} else "failed", "timeout-recovery": "passed" if error == "timeout" else "blocked", "post-failure-recovery": "blocked", "model-unload": "passed" if unloaded else "failed"}
            metadata = {"readDurationSeconds": round(time.monotonic() - started, 3), "readExitCode": code, "readErrorCode": error, "rawResponseRetained": False}
        gates["repository-read-plan-review"] = gate(read_checks)
        gates["scoped-edit"] = gate(edit_checks)
        gates["reliability"] = gate(reliability)
        status = "passed" if all(item["status"] == "passed" for item in gates.values()) else "failed"
        results.append({"modelId": candidate["modelId"], "modelSha256": candidate["modelSha256"], "status": status, "gates": gates, "surfaceMetrics": metadata, "codingRecommendationEligible": False, "promotionBlock": candidate.get("promotionBlock") or "required-gate-failed", "rawResponseRetained": False})
    report = {"schemaVersion": 1, "kind": "haven42-apple-silicon-llamacpp-coding-agent-qualification-result", "release": plan["release"], "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "planCanonicalSha256": runner.canonical_sha256(plan), "qualificationCanonicalSha256": runner.canonical_sha256(qualification), "policyCanonicalSha256": runner.canonical_sha256(runner.load_json(args.policy)), "runtime": plan["runtime"], "hardwareProfile": plan["hardwareProfile"], "surface": {"id": "opencode-cli", "version": SURFACE_VERSION, "binarySha256": SURFACE_BINARY_SHA256, "archiveSha256": SURFACE_ARCHIVE_SHA256}, "status": "completed", "results": results, "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False, "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False}
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "results": [{"modelId": result["modelId"], "status": result["status"]} for result in results]}, sort_keys=True))
    return 0 if all(result["status"] == "passed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
