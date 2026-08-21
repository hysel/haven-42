#!/usr/bin/env python3
"""Qualify exact GGUF candidates with a pinned llama.cpp server on Apple M4."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable


class QualificationError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise QualificationError("invalid-json-object")
    return value


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def request_json(port: int, key: str | None, body: dict[str, Any] | None, timeout: float) -> tuple[int, dict[str, Any]]:
    endpoint = "/health" if body is None else "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    request = urllib.request.Request(f"http://127.0.0.1:{port}{endpoint}", data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode())
        if not isinstance(value, dict):
            raise QualificationError("invalid-runtime-response")
        return response.status, value


def wait_ready(process: subprocess.Popen[Any], port: int, key: str, seconds: int = 120) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise QualificationError("runtime-exited-before-ready")
        try:
            status, _ = request_json(port, key, None, 2)
            if status == 200:
                return
        except (OSError, ValueError, urllib.error.URLError):
            pass
        time.sleep(0.25)
    raise QualificationError("runtime-readiness-timeout")


def stop(process: subprocess.Popen[Any]) -> None:
    process.terminate()
    try:
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def closed(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", port)) != 0


def full_offload_observed(log_text: str) -> bool:
    if re.search(r"offloaded all layers", log_text, re.I):
        return True
    for match in re.finditer(r"offload(?:ed|ing)[^\r\n]*?\b([0-9]+)\s*/\s*([0-9]+)\b[^\r\n]*layers", log_text, re.I):
        if int(match.group(1)) > 0 and match.group(1) == match.group(2):
            return True
    return False


def validate_plan(plan: dict[str, Any], server: Path, models: Path) -> list[dict[str, Any]]:
    if plan.get("kind") != "haven42-apple-silicon-llamacpp-model-qualification-plan":
        raise QualificationError("invalid-plan-kind")
    runtime, rules = plan.get("runtime"), plan.get("rules")
    if not isinstance(runtime, dict) or not isinstance(rules, dict):
        raise QualificationError("invalid-plan")
    if sha256_file(server) != runtime.get("serverSha256"):
        raise QualificationError("runtime-digest-mismatch")
    false_rules = (
        "rawPromptsOrResponsesRetained", "privateIdentityRetained", "automaticDefaultChangeAllowed",
        "automaticSelectionEvidenceAllowed", "automaticSupportChangeAllowed", "continueEvidenceMayBeUsedForNewRecommendation",
    )
    if any(rules.get(key) is not False for key in false_rules):
        raise QualificationError("unsafe-plan-rule")
    candidates = plan.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise QualificationError("invalid-candidates")
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("modelId"), str) or candidate["modelId"] in seen:
            raise QualificationError("invalid-candidate")
        seen.add(candidate["modelId"])
        path = models / candidate.get("filename", "")
        if not path.is_file() or path.stat().st_size != candidate.get("modelBytes") or sha256_file(path) != candidate.get("modelSha256"):
            raise QualificationError(f"model-artifact-mismatch:{candidate['modelId']}")
    return candidates


def message(value: dict[str, Any]) -> dict[str, Any]:
    choices = value.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise QualificationError("invalid-completion")
    result = choices[0].get("message")
    if not isinstance(result, dict):
        raise QualificationError("invalid-completion")
    return result


def text_of(value: dict[str, Any]) -> str:
    text = message(value).get("content")
    if not isinstance(text, str):
        raise QualificationError("invalid-completion")
    return text.strip()


def single_sentence(text: str) -> bool:
    return bool(text) and len(re.findall(r"[.!?]", text)) == 1 and "\n" not in text


def valid_code_json(text: str) -> bool:
    """Validate the exact AST shape without executing model-generated code."""
    try:
        value = json.loads(text)
        if not isinstance(value, dict) or set(value) != {"path", "code"} or value.get("path") != "app/main.py" or not isinstance(value.get("code"), str):
            return False
        tree = ast.parse(value["code"], filename="app/main.py", mode="exec")
    except (json.JSONDecodeError, SyntaxError, TypeError):
        return False
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        return False
    function = tree.body[0]
    if function.name != "add" or len(function.args.args) != 2 or [arg.arg for arg in function.args.args] != ["a", "b"]:
        return False
    if not all(isinstance(arg.annotation, ast.Name) and arg.annotation.id == "int" for arg in function.args.args):
        return False
    if not isinstance(function.returns, ast.Name) or function.returns.id != "int" or len(function.body) != 1 or not isinstance(function.body[0], ast.Return):
        return False
    result = function.body[0].value
    return isinstance(result, ast.BinOp) and isinstance(result.op, ast.Add) and isinstance(result.left, ast.Name) and result.left.id == "a" and isinstance(result.right, ast.Name) and result.right.id == "b"


def valid_tool(value: dict[str, Any]) -> bool:
    calls = message(value).get("tool_calls") or []
    if not isinstance(calls, list) or len(calls) != 1 or not isinstance(calls[0], dict):
        return False
    function = calls[0].get("function")
    if not isinstance(function, dict) or function.get("name") != "read_file":
        return False
    arguments = function.get("arguments")
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return False
    return arguments == {"filepath": "README.md"}


def run_cell(server: Path, model: Path, alias: str, body: dict[str, Any], validator: Callable[[dict[str, Any]], bool]) -> tuple[dict[str, Any], dict[str, Any]]:
    port, key = free_port(), hashlib.sha256(os.urandom(32)).hexdigest()
    fd, name = tempfile.mkstemp(prefix="haven42-lfm25-", suffix=".log")
    os.close(fd)
    log_path = Path(name)
    process: subprocess.Popen[Any] | None = None
    started = time.monotonic()
    try:
        with log_path.open("wb") as log:
            process = subprocess.Popen([
                str(server), "-m", str(model), "--alias", alias, "--host", "127.0.0.1", "--port", str(port),
                "-ngl", "99", "-c", "4096", "-np", "1", "--no-webui", "--reasoning", "off", "--api-key", key,
                "--verbose",
            ], stdout=log, stderr=subprocess.STDOUT)
            wait_ready(process, port, key)
            unauthorized = False
            try:
                request_json(port, None, body, 3)
            except urllib.error.HTTPError as error:
                unauthorized = error.code in {401, 403}
            status, response = request_json(port, key, body, 180)
            passed = status == 200 and unauthorized and validator(response)
            usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
            stop(process)
            process = None
            listener_closed = closed(port)
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        metal = bool(re.search(r"Metal|ggml_metal", log_text, re.I))
        offload = full_offload_observed(log_text)
        passed = passed and listener_closed and metal and offload
        return {"status": "passed" if passed else "failed", "responseRetained": False}, {
            "durationSeconds": round(time.monotonic() - started, 3),
            "outputTokens": int(usage.get("completion_tokens", 0)), "metalDetected": metal,
            "allLayersOffloaded": offload, "authenticationRequired": unauthorized, "unloadPassed": listener_closed,
        }
    finally:
        if process is not None and process.poll() is None:
            stop(process)
        log_path.unlink(missing_ok=True)


def task_cells() -> list[tuple[str, dict[str, Any], Callable[[dict[str, Any]], bool]]]:
    base = {"temperature": 0, "stream": False, "max_tokens": 192}
    return [
        ("generalChat", base | {"messages": [{"role": "user", "content": "Reply exactly: MAC_CHAT_OK"}]}, lambda value: text_of(value) == "MAC_CHAT_OK"),
        ("contentWrite", base | {"messages": [{"role": "user", "content": "Write exactly one sentence of 6 to 18 words about careful software testing. Include the word testing."}]}, lambda value: single_sentence(text_of(value)) and 6 <= len(re.findall(r"\b[\w'-]+\b", text_of(value))) <= 18 and "testing" in text_of(value).lower()),
        ("contentSummarize", base | {"messages": [{"role": "user", "content": "Summarize in exactly one sentence of 6 to 24 words while preserving the exact labels RUNTIME_LOCAL, MODEL_LOCAL, and CLEAR_REMOVAL: A portable app keeps its runtime and model beside the app so removal is clear."}]}, lambda value: single_sentence(text_of(value)) and 6 <= len(re.findall(r"\b[\w'-]+\b", text_of(value))) <= 24 and all(label in text_of(value) for label in ("RUNTIME_LOCAL", "MODEL_LOCAL", "CLEAR_REMOVAL"))),
        ("structuredTool", base | {"messages": [{"role": "user", "content": "Call read_file for README.md. Return only the tool call."}], "tools": [{"type": "function", "function": {"name": "read_file", "description": "Read one repository file.", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}}}]}, valid_tool),
        ("structuredCode", base | {"response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": "Return JSON only with exactly keys path and code. Path must be app/main.py. Code must define def add(a: int, b: int) -> int and return a + b. No markdown."}]}, lambda value: valid_code_json(text_of(value))),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        parser.error("apple-silicon-host-required")
    plan = load_json(args.plan)
    candidates = validate_plan(plan, args.server, args.models)
    memory = int(subprocess.check_output(["/usr/sbin/sysctl", "-n", "hw.memsize"], text=True).strip())
    if memory / 1024**3 < plan["hardwareProfile"]["minimumSystemMemoryGiB"]:
        parser.error("insufficient-system-memory")
    results = []
    for candidate in candidates:
        checks: dict[str, Any] = {}
        metrics: dict[str, Any] = {}
        for name, body, validator in task_cells():
            try:
                check, measurement = run_cell(args.server, args.models / candidate["filename"], candidate["modelId"], body | {"model": candidate["modelId"]}, validator)
            except (QualificationError, OSError, subprocess.SubprocessError, urllib.error.URLError, TimeoutError) as error:
                check, measurement = {"status": "failed", "errorCode": str(error), "responseRetained": False}, {"unloadPassed": False}
            checks[name], metrics[name] = check, measurement
            if name == "structuredCode":
                # Model-generated code is parsed but never executed by this
                # qualification runner. A plan that explicitly requires
                # execution therefore fails closed instead of overstating the
                # observed evidence.
                metrics[name]["validationMethod"] = "ast-only"
                metrics[name]["modelGeneratedCodeExecuted"] = False
                if "execute" in str(plan.get("testContract", {}).get(name, "")).lower():
                    checks[name] = {
                        "status": "failed",
                        "errorCode": "planned-execution-not-performed-safety-boundary",
                        "responseRetained": False,
                    }
        core = all(check["status"] == "passed" for check in checks.values())
        results.append({"modelId": candidate["modelId"], "modelSha256": candidate["modelSha256"], "repositoryRevision": candidate["repositoryRevision"], "status": "passed" if core else "failed", "corePassed": core, "checks": checks, "metrics": metrics, "codingSurfaceStatus": "not-run", "codingRecommendationEligible": False, "promotionBlock": candidate.get("promotionBlock")})
    report = {
        "schemaVersion": 1, "kind": "haven42-apple-silicon-llamacpp-model-qualification-result",
        "release": plan["release"], "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "completed", "planCanonicalSha256": canonical_sha256(plan), "runtime": plan["runtime"],
        "hardwareProfile": plan["hardwareProfile"] | {"systemMemoryGiB": round(memory / 1024**3, 2)}, "results": results,
        "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False, "automaticDefaultChangeAllowed": False,
        "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "results": [{"modelId": result["modelId"], "status": result["status"]} for result in results]}, sort_keys=True))
    return 0 if all(result["status"] == "passed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
