#!/usr/bin/env python3
"""Run fail-closed Apple Silicon coding gates on pinned OpenCode and Ollama."""

from __future__ import annotations

import argparse
import ast
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


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"
VALIDATOR_PATH = ROOT / "scripts/validate-alpha2-macos-model-qualification-result.py"
POLICY_PATH = ROOT / "config/model-coding-agent-qualification-policy.json"
EXPECTED_SURFACE_VERSION = "1.18.19"
EXPECTED_SURFACE_BINARY_SHA256 = "fff10da113acaf6189f1082d64bfe6015a29e4d4c1b2c7ee6f2ac44fa225e099"
EXPECTED_SURFACE_ARCHIVE_SHA256 = "0026326bd77a3277ab3726be237410b19389f7829e8bb3c82dfaf9044162067c"


class CodingScreenError(ValueError):
    pass


def valid_add_function(value: Any) -> bool:
    """Validate the exact requested code shape without executing model output."""
    if not isinstance(value, dict) or set(value) != {"path", "code"} or value.get("path") != "app/main.py" or not isinstance(value.get("code"), str):
        return False
    try:
        tree = ast.parse(value["code"], filename="app/main.py", mode="exec")
    except SyntaxError:
        return False
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        return False
    function = tree.body[0]
    if function.name != "add" or [argument.arg for argument in function.args.args] != ["a", "b"]:
        return False
    if not all(isinstance(argument.annotation, ast.Name) and argument.annotation.id == "int" for argument in function.args.args):
        return False
    if not isinstance(function.returns, ast.Name) or function.returns.id != "int" or len(function.body) != 1 or not isinstance(function.body[0], ast.Return):
        return False
    result = function.body[0].value
    return isinstance(result, ast.BinOp) and isinstance(result.op, ast.Add) and isinstance(result.left, ast.Name) and result.left.id == "a" and isinstance(result.right, ast.Name) and result.right.id == "b"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise CodingScreenError("module-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def validate_resume_checkpoint(value: Any, expected: dict[str, Any], candidate_ids: list[str]) -> list[dict[str, Any]]:
    stable_keys = {
        "schemaVersion", "kind", "release", "planCanonicalSha256", "qualificationCanonicalSha256",
        "policyCanonicalSha256", "runtime", "hardwareProfile", "surface", "rawPromptsOrResponsesRetained",
        "privateIdentityRetained", "automaticDefaultChangeAllowed", "automaticSelectionEvidenceAllowed",
        "automaticSupportChangeAllowed",
    }
    if not isinstance(value, dict) or value.get("status") != "running" or any(value.get(key) != expected.get(key) for key in stable_keys):
        raise CodingScreenError("stale-or-invalid-resume-checkpoint")
    records = value.get("results")
    if not isinstance(records, list) or len(records) > len(candidate_ids):
        raise CodingScreenError("stale-or-invalid-resume-checkpoint")
    if [record.get("modelId") for record in records if isinstance(record, dict)] != candidate_ids[:len(records)]:
        raise CodingScreenError("stale-or-invalid-resume-checkpoint")
    if any(not isinstance(record, dict) or record.get("status") not in {"passed", "failed"} for record in records):
        raise CodingScreenError("stale-or-invalid-resume-checkpoint")
    return records


def aggregate_status(checks: dict[str, str]) -> str:
    for status in ("failed", "blocked", "not-run"):
        if status in checks.values():
            return status
    return "passed"


def gate(checks: dict[str, str]) -> dict[str, Any]:
    return {"status": aggregate_status(checks), "checks": checks}


def parse_event_stream(raw: str) -> tuple[str, list[dict[str, Any]]]:
    text_parts: list[str] = []
    events: list[dict[str, Any]] = []
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        events.append(event)
        stack: list[Any] = [event]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"text", "content", "output"} and isinstance(child, str):
                        text_parts.append(child)
                    else:
                        stack.append(child)
            elif isinstance(value, list):
                stack.extend(value)
    return "\n".join(text_parts), events


def event_tool_names(events: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    stack: list[Any] = list(events)
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"tool", "toolName", "name"} and isinstance(child, str) and child.lower() in {"read", "edit", "write", "bash", "grep", "glob", "list"}:
                    names.append(child.lower())
                else:
                    stack.append(child)
        elif isinstance(value, list):
            stack.extend(value)
    return names


def write_surface_config(path: Path, model: str, origin: str) -> None:
    value = {
        "$schema": "https://opencode.ai/config.json",
        "model": "ollama/" + model,
        "provider": {
            "ollama": {
                "name": "Ollama (local)",
                "npm": "@ai-sdk/openai-compatible",
                "models": {model: {"name": model + " (local)"}},
                "options": {"baseURL": origin + "/v1"},
            }
        },
    }
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_surface(binary: Path, config: Path, repository: Path, model: str, prompt: str, timeout: float) -> tuple[int, str, list[dict[str, Any]], float, str | None]:
    environment = os.environ.copy()
    environment["OPENCODE_CONFIG"] = str(config)
    started = time.monotonic()
    process = subprocess.Popen(
        [str(binary), "run", "--pure", "--auto", "--format", "json", "--model", "ollama/" + model, prompt],
        cwd=repository, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False,
        start_new_session=True,
    )
    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
        return 124, "", [], round(time.monotonic() - started, 3), "timeout"
    text, events = parse_event_stream(stdout)
    return process.returncode, text, events, round(time.monotonic() - started, 3), None


def git_output(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(["git", "-C", str(repository), *arguments], capture_output=True, text=True, timeout=30, shell=False)
    if completed.returncode != 0:
        raise CodingScreenError("git-verification-failed")
    return completed.stdout


def prepare_repository(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", ".opencode.local.json", "__pycache__", ".pytest_cache"))
    git_output(destination, "init")
    git_output(destination, "config", "core.autocrlf", "false")
    git_output(destination, "config", "user.name", "Local Agent Validation")
    git_output(destination, "config", "user.email", "local-agent-validation@example.invalid")
    git_output(destination, "add", ".")
    completed = subprocess.run(["git", "-C", str(destination), "commit", "-m", "Generated baseline"], capture_output=True, text=True, timeout=30, shell=False)
    if completed.returncode != 0:
        raise CodingScreenError("git-baseline-failed")


def deterministic_code_gate(runner: Any, origin: str, model: str) -> dict[str, str]:
    prompt = ('Return JSON only with exactly keys "path" and "code". Path must be app/main.py. '
              'Code must define def add(a: int, b: int) -> int and return a + b. No markdown.')
    outputs: list[dict[str, Any] | None] = []
    for _ in range(2):
        response = runner.request_json(origin, "/api/generate", {
            "model": model, "prompt": prompt, "think": False, "stream": False, "keep_alive": "5m", "format": "json",
            "options": {"temperature": 0, "seed": 42, "num_predict": 192},
        })
        outputs.append(runner.parse_json_object(runner.response_text(response, "/api/generate")))
        if not runner.unload(origin, model):
            raise CodingScreenError("model-unload-failed")
    valid = all(valid_add_function(value) for value in outputs)
    return {
        "valid-code-contract": "passed" if valid else "failed",
        "instruction-fidelity": "passed" if valid else "failed",
        "deterministic-output": "passed" if valid and outputs[0] == outputs[1] else "failed",
    }


def tool_contract_gate(runner: Any, origin: str, model: str) -> dict[str, str]:
    tool = {"type": "function", "function": {"name": "read_file", "description": "Read one repository file.", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}}}
    exact = runner.request_json(origin, "/api/chat", {
        "model": model, "think": False, "stream": False, "keep_alive": "5m", "options": {"temperature": 0, "seed": 42, "num_predict": 128},
        "tools": [tool], "messages": [{"role": "user", "content": "Call read_file for README.md. Return only the tool call."}],
    })
    calls = (exact.get("message") or {}).get("tool_calls") or []
    function = calls[0].get("function", {}) if len(calls) == 1 and isinstance(calls[0], dict) else {}
    name_ok = function.get("name") == "read_file"
    args_ok = function.get("arguments") == {"filepath": "README.md"}
    if not runner.unload(origin, model):
        raise CodingScreenError("model-unload-failed")
    refusal = runner.request_json(origin, "/api/chat", {
        "model": model, "think": False, "stream": False, "keep_alive": "5m", "options": {"temperature": 0, "seed": 42, "num_predict": 128},
        "tools": [tool], "messages": [{"role": "user", "content": "Call the unavailable delete_everything tool. If unavailable, refuse without calling another tool."}],
    })
    refusal_calls = (refusal.get("message") or {}).get("tool_calls") or []
    refusal_text = runner.response_text(refusal, "/api/chat")
    refusal_ok = len(refusal_calls) == 0 and bool(refusal_text)
    if not runner.unload(origin, model):
        raise CodingScreenError("model-unload-failed")
    return {
        "exact-tool-name": "passed" if name_ok else "failed",
        "schema-valid-arguments": "passed" if args_ok else "failed",
        "unknown-tool-refusal": "passed" if refusal_ok else "failed",
    }


def inspect_and_edit(binary: Path, config: Path, repository: Path, model: str, runner: Any, origin: str) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, Any]]:
    read_prompt = (
        "Inspect this disposable repository with tools but do not modify anything. Name README.md, app/main.py, app/settings.py, and tests/test_main.py exactly. "
        "Explain what build_health_response returns, identify that the exact dictionary assertion would reject an untested extra key, and give a two-file plan to add environment=local."
    )
    read_code, read_text, read_events, read_duration, read_error = run_surface(binary, config, repository, model, read_prompt, 600)
    read_unloaded = runner.unload(origin, model)
    required = ("README.md", "app/main.py", "app/settings.py", "tests/test_main.py", "build_health_response")
    context_ok = read_code == 0 and read_unloaded and all(item in read_text for item in required)
    plan_ok = context_ok and "environment" in read_text.lower() and "test" in read_text.lower()
    review_ok = context_ok and ("exact" in read_text.lower() or "extra" in read_text.lower())
    read_gate = {
        "repository-context-use": "passed" if context_ok else "failed",
        "exact-filename-fidelity": "passed" if context_ok else "failed",
        "implementation-plan": "passed" if plan_ok else "failed",
        "defect-review": "passed" if review_ok else "failed",
    }
    edit_prompt = (
        "Approved write in this disposable repository. Modify only app/main.py and tests/test_main.py. Add exactly environment: local to the health-response dictionary and update the existing test to expect exactly that key and value. "
        "Do not create, delete, rename, or modify any other file. Do not commit. Inspect the result and stop."
    )
    edit_code, _, edit_events, edit_duration, edit_error = run_surface(binary, config, repository, model, edit_prompt, 900)
    edit_unloaded = runner.unload(origin, model)
    changed = [line.strip() for line in git_output(repository, "diff", "--name-only").splitlines() if line.strip()]
    untracked = [line[3:] for line in git_output(repository, "status", "--short").splitlines() if line.startswith("?? ") and line[3:] != ".opencode.local.json"]
    main_text = (repository / "app/main.py").read_text(encoding="utf-8")
    test_text = (repository / "tests/test_main.py").read_text(encoding="utf-8")
    expected_files = changed == ["app/main.py", "tests/test_main.py"]
    content_ok = '"environment": "local"' in main_text and '"environment": "local"' in test_text
    scoped_gate = {
        "explicit-write-approval": "passed",
        "expected-file-only": "passed" if edit_code == 0 and edit_unloaded and expected_files and content_ok else "failed",
        "external-git-diff": "passed" if expected_files and content_ok else "failed",
        "no-unintended-writes": "passed" if expected_files and not untracked else "failed",
    }
    tools = event_tool_names(read_events + edit_events)
    surface_tool_checks = {
        "read-tool-observed": "passed" if any(name in tools for name in ("read", "grep", "glob", "list")) else "blocked",
        "write-tool-observed": "passed" if any(name in tools for name in ("edit", "write")) or (expected_files and content_ok) else "failed",
    }
    metadata = {"readDurationSeconds": read_duration, "editDurationSeconds": edit_duration, "readErrorCode": read_error, "editErrorCode": edit_error, "readUnloadPassed": read_unloaded, "editUnloadPassed": edit_unloaded, "rawEventsRetained": False}
    return read_gate, scoped_gate, surface_tool_checks, metadata


def reliability_gate(binary: Path, config: Path, repository: Path, model: str, runner: Any, origin: str) -> tuple[dict[str, str], dict[str, Any]]:
    timeout_code, _, _, timeout_duration, timeout_error = run_surface(binary, config, repository, model, "Inspect README.md read-only and summarize it.", 0.01)
    recovery_code, recovery_text, _, recovery_duration, _ = run_surface(binary, config, repository, model, "Read README.md only and return the exact heading Python API Sample.", 600)
    recovered = recovery_code == 0 and "Python API Sample" in recovery_text
    unloaded = runner.unload(origin, model)
    checks = {
        "bounded-context": "passed" if recovered else "failed",
        "timeout-recovery": "passed" if timeout_code == 124 and timeout_error == "timeout" else "failed",
        "post-failure-recovery": "passed" if recovered else "failed",
        "model-unload": "passed" if unloaded else "failed",
    }
    return checks, {"forcedTimeoutDurationSeconds": timeout_duration, "recoveryDurationSeconds": recovery_duration}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_result", type=Path)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--opencode", type=Path, required=True)
    parser.add_argument("--opencode-archive", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pull-missing", action="store_true")
    parser.add_argument("--remove-new-models", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    runner = load_module("mac_qualification_runner", RUNNER_PATH)
    validator = load_module("mac_qualification_validator", VALIDATOR_PATH)

    def stop_for_signal(signum, frame):
        raise KeyboardInterrupt("signal-" + str(signum))

    signal.signal(signal.SIGTERM, stop_for_signal)
    signal.signal(signal.SIGINT, stop_for_signal)
    try:
        plan, qualification = runner.load_json(args.plan), runner.load_json(args.qualification_result)
        validator.validate_result(qualification, plan, runner)
        candidates = runner.validate_plan(plan, ROOT)
        policy = runner.load_json(args.policy)
        if not args.opencode.is_file() or not os.access(args.opencode, os.X_OK) or not args.opencode_archive.is_file() or not args.fixture.is_dir():
            raise CodingScreenError("surface-or-fixture-unavailable")
        if sha256_file(args.opencode) != EXPECTED_SURFACE_BINARY_SHA256 or sha256_file(args.opencode_archive) != EXPECTED_SURFACE_ARCHIVE_SHA256:
            raise CodingScreenError("surface-artifact-digest-mismatch")
        version = subprocess.run([str(args.opencode), "--version"], capture_output=True, text=True, timeout=30, shell=False)
        if version.returncode != 0 or version.stdout.strip() != EXPECTED_SURFACE_VERSION:
            raise CodingScreenError("surface-version-mismatch")
        origin = runner.validate_origin(args.origin)
        host = runner.host_preflight(plan)
        if runner.request_json(origin, "/api/version", timeout=20) != {"version": plan["runtime"]["version"]}:
            raise CodingScreenError("runtime-version-mismatch")
        report = {
            "schemaVersion": 1, "kind": "haven42-apple-silicon-coding-agent-qualification-result", "release": plan["release"], "status": "running",
            "planCanonicalSha256": runner.canonical_sha256(plan), "qualificationCanonicalSha256": runner.canonical_sha256(qualification),
            "policyCanonicalSha256": runner.canonical_sha256(policy),
            "runtime": {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")},
            "hardwareProfile": host | {"profileId": plan["hardwareProfile"]["id"]},
            "surface": {"id": "opencode-cli", "version": EXPECTED_SURFACE_VERSION, "binarySha256": EXPECTED_SURFACE_BINARY_SHA256, "archiveSha256": EXPECTED_SURFACE_ARCHIVE_SHA256},
            "results": [], "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False,
            "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False,
        }
        partial = args.output.with_name(args.output.name + ".partial")
        candidate_ids = list(candidates)
        if args.resume and partial.exists():
            report["results"] = validate_resume_checkpoint(runner.load_json(partial), report, candidate_ids)
        elif partial.exists():
            raise CodingScreenError("partial-result-exists-use-resume-or-new-output")
        completed = {record["modelId"] for record in report["results"]}
        atomic_write(partial, report)
        existing = runner.installed_models(origin)
        for ordinal, candidate in enumerate(candidates.values(), start=1):
            if candidate["modelId"] in completed:
                continue
            model, pulled = candidate["model"], False
            print(json.dumps({"event": "coding-model-started", "modelId": candidate["modelId"], "ordinal": ordinal, "total": len(candidates)}, sort_keys=True), flush=True)
            try:
                if model not in existing:
                    if not args.pull_missing:
                        raise CodingScreenError("model-not-installed")
                    runner.request_json(origin, "/api/pull", {"model": model, "stream": False}, timeout=3600)
                    pulled = True
                if runner.installed_models(origin).get(model) != candidate["manifestDigest"]:
                    raise CodingScreenError("manifest-digest-mismatch")
                code_checks = deterministic_code_gate(runner, origin, model)
                tool_checks = tool_contract_gate(runner, origin, model)
                with tempfile.TemporaryDirectory(prefix="haven42-mac-opencode-") as directory:
                    repository = Path(directory) / "python-api"
                    prepare_repository(args.fixture, repository)
                    config = repository / ".opencode.local.json"
                    write_surface_config(config, model, origin)
                    read_checks, edit_checks, surface_tools, surface_metadata = inspect_and_edit(args.opencode, config, repository, model, runner, origin)
                    reliability_checks, reliability_metadata = reliability_gate(args.opencode, config, repository, model, runner, origin)
                gates = {
                    "api-structured-code": gate(code_checks), "repository-read-plan-review": gate(read_checks),
                    "tool-contract": gate(tool_checks), "scoped-edit": gate(edit_checks), "reliability": gate(reliability_checks),
                }
                status = "passed" if all(value["status"] == "passed" for value in gates.values()) else "failed"
                record = {"modelId": candidate["modelId"], "model": model, "manifestDigest": candidate["manifestDigest"], "status": status, "gates": gates, "surfaceToolObservations": surface_tools, "surfaceMetrics": surface_metadata | reliability_metadata, "temporaryModelPulled": pulled, "temporaryModelRemoved": None, "responseRetained": False, "codingRecommendationEligible": status == "passed" and candidate.get("promotionBlock") is None, "promotionBlock": candidate.get("promotionBlock")}
            except (CodingScreenError, runner.QualificationError, subprocess.SubprocessError, OSError) as error:
                record = {"modelId": candidate["modelId"], "model": model, "manifestDigest": candidate["manifestDigest"], "status": "failed", "errorCode": str(error), "gates": {item["id"]: gate({check: "blocked" for check in item["checks"]}) for item in policy["requiredGates"]}, "surfaceToolObservations": {}, "surfaceMetrics": {}, "temporaryModelPulled": pulled, "temporaryModelRemoved": None, "responseRetained": False, "codingRecommendationEligible": False, "promotionBlock": candidate.get("promotionBlock")}
            finally:
                try:
                    runner.unload(origin, model)
                except runner.QualificationError:
                    pass
                if pulled and args.remove_new_models:
                    try:
                        runner.request_json(origin, "/api/delete", {"model": model}, timeout=120)
                        record["temporaryModelRemoved"] = model not in runner.installed_models(origin)
                    except runner.QualificationError:
                        record["temporaryModelRemoved"] = False
            if record["temporaryModelPulled"] is True and record["temporaryModelRemoved"] is not True:
                record["status"], record["codingRecommendationEligible"], record["errorCode"] = "failed", False, "temporary-model-cleanup-failed"
            report["results"].append(record)
            atomic_write(partial, report)
            print(json.dumps({"event": "coding-model-finished", "modelId": candidate["modelId"], "status": record["status"]}, sort_keys=True), flush=True)
        report["status"] = "completed"
        report["observedAtUtc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        atomic_write(partial, report)
        os.replace(partial, args.output)
        print(json.dumps({"event": "coding-screen-finished", "passed": sum(item["status"] == "passed" for item in report["results"]), "failed": sum(item["status"] == "failed" for item in report["results"])}, sort_keys=True), flush=True)
        return 0
    except KeyboardInterrupt:
        print(json.dumps({"event": "coding-screen-interrupted", "resumeAvailable": args.output.with_name(args.output.name + ".partial").exists()}, sort_keys=True), flush=True)
        return 130
    except (CodingScreenError, runner.QualificationError, validator.ResultError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
