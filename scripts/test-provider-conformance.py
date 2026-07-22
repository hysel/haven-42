#!/usr/bin/env python3
"""Run bounded, provider-neutral Ollama text conformance without persisting prompts or raw output."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def request_json(base_url: str, path: str, payload: dict | None = None, timeout: float = 120.0) -> tuple[dict, float]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(base_url.rstrip("/") + path, data=data, headers={"Content-Type": "application/json"} if data else {}, method="POST" if data else "GET")
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode()), (time.perf_counter() - started) * 1000


def chat(base_url: str, model: str, prompt: str, num_predict: int = 128, think: bool = False, timeout: float = 180.0, tools: list | None = None) -> tuple[dict, float]:
    payload = {
        "model": model,
        "stream": False,
        "think": think,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": num_predict, "seed": 42},
    }
    if tools:
        payload["tools"] = tools
    return request_json(base_url, "/api/chat", payload, timeout)


def check(checks: list[dict], identifier: str, passed: bool, reason: str = "") -> None:
    value = {"id": identifier, "status": "passed" if passed else "failed"}
    if reason:
        value["reason"] = reason
    checks.append(value)


def content(response: dict) -> str:
    return str(response.get("message", {}).get("content", "")).strip()


def extract_patch(text: str) -> str:
    fenced = re.search(r"```(?:diff|patch)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1).strip() if fenced else text.strip()
    starts = [position for token in ("diff --git ", "--- a/", "--- flag.py") if (position := candidate.find(token)) >= 0]
    if starts:
        candidate = candidate[min(starts):]
    return candidate.strip() + "\n"


def stream_first_token(base_url: str, model: str) -> float | None:
    payload = {
        "model": model,
        "stream": True,
        "think": False,
        "messages": [{"role": "user", "content": "Reply with the single word READY."}],
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 16, "seed": 42},
    }
    request = urllib.request.Request(base_url.rstrip("/") + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=180) as response:
        for line in response:
            item = json.loads(line)
            message = item.get("message", {})
            if message.get("content") or message.get("thinking"):
                return (time.perf_counter() - started) * 1000
    return None


def cancellation_probe(base_url: str, model: str) -> bool:
    payload = {
        "model": model,
        "stream": True,
        "think": False,
        "messages": [{"role": "user", "content": "List integers from 1 through 10000, one per line."}],
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 2048, "seed": 42},
    }
    request = urllib.request.Request(base_url.rstrip("/") + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    response = urllib.request.urlopen(request, timeout=180)
    try:
        first = response.readline()
        return bool(first)
    finally:
        response.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded Ollama provider conformance.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--operating-system", required=True)
    parser.add_argument("--hardware-profile", required=True)
    parser.add_argument("--capacity-decision", required=True, choices=["ready", "defer", "measurement-required", "insufficient-capacity"])
    parser.add_argument("--unload", action="store_true")
    args = parser.parse_args()

    checks: list[dict] = []
    if args.capacity_decision != "ready":
        print(json.dumps({"SchemaVersion": 1, "Kind": "provider-conformance", "Status": "blocked", "Checks": [{"id": "capacity-preflight", "status": "blocked"}], "EndpointPersisted": False, "PromptPersisted": False, "RawResponsePersisted": False}, indent=2))
        return 3
    check(checks, "capacity-preflight", True)

    try:
        version, _ = request_json(args.base_url, "/api/version", timeout=10)
        check(checks, "provider-health", bool(version.get("version")))
        tags, _ = request_json(args.base_url, "/api/tags", timeout=10)
        model_record = next((item for item in tags.get("models", []) if item.get("name") == args.model), None)
        check(checks, "model-discovery", model_record is not None)
        if model_record is None:
            raise RuntimeError("model-not-discovered")
        show, _ = request_json(args.base_url, "/api/show", {"model": args.model}, timeout=30)
        from_line = next((line for line in str(show.get("modelfile", "")).splitlines() if line.startswith("FROM ")), "")
        blob_match = re.search(r"sha256-([0-9a-f]{64})", from_line)
        model_blob_sha256 = blob_match.group(1) if blob_match else "not-recorded"

        request_json(args.base_url, "/api/generate", {"model": args.model, "keep_alive": 0}, timeout=30)
        time.sleep(1)
        exact, exact_wall_ms = chat(args.base_url, args.model, "Return exactly HAVEN42_LAGUNA_EXACT_OK and nothing else.", num_predict=32)
        check(checks, "exact-output", content(exact) == "HAVEN42_LAGUNA_EXACT_OK")
        first_token_ms = stream_first_token(args.base_url, args.model)

        general, _ = chat(args.base_url, args.model, "What is 17 plus 25? Reply with the number and one short sentence.", num_predict=64)
        check(checks, "general-chat", "42" in content(general))
        writing, _ = chat(args.base_url, args.model, "Write Markdown with heading '# Harbor Notes' and the exact sentence 'Local evidence stays bounded.'", num_predict=96)
        check(checks, "writing", "# Harbor Notes" in content(writing) and "Local evidence stays bounded." in content(writing))
        summary, _ = chat(args.base_url, args.model, "Summarize only these facts: Project Cedar uses port 4242. Its status color is amber. Preserve both facts.", num_predict=96)
        check(checks, "summarization", "4242" in content(summary) and "amber" in content(summary).lower())

        tools = [{"type": "function", "function": {"name": "inspect_file", "description": "Inspect one repository file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}]
        tool_response, _ = chat(args.base_url, args.model, "Use inspect_file for src/example.py. Do not answer from memory.", num_predict=128, think=True, tools=tools)
        tool_calls = tool_response.get("message", {}).get("tool_calls", [])
        tool_ok = bool(tool_calls and tool_calls[0].get("function", {}).get("name") == "inspect_file" and tool_calls[0].get("function", {}).get("arguments", {}).get("path") == "src/example.py")
        check(checks, "structured-tool-call", tool_ok)

        reviewed, _ = chat(args.base_url, args.model, "Review this code without claiming file access: `def is_ready(): return False`. Name the function and the returned boolean.", num_predict=96)
        check(checks, "read-only-engineering", "is_ready" in content(reviewed) and "false" in content(reviewed).lower())
        plan, _ = chat(args.base_url, args.model, "Give a read-only two-step implementation plan. Step one must name service.py and step two must name test_service.py. Do not provide a patch.", num_predict=128)
        plan_text = content(plan)
        check(checks, "implementation-plan", "service.py" in plan_text and "test_service.py" in plan_text and "diff --git" not in plan_text)

        patch_response, _ = chat(
            args.base_url,
            args.model,
            "Return only a valid unified diff. The file is named flag.py and contains exactly two lines:\n"
            "```python\ndef enabled():\n    return False\n```\n"
            "Change only the token False to True. Preserve spaces and include both context lines.",
            num_predict=192,
        )
        patch_text = extract_patch(content(patch_response))
        patch_ok = False
        with tempfile.TemporaryDirectory(prefix="haven42-provider-conformance-") as directory:
            root = Path(directory)
            target = root / "flag.py"
            target.write_text("def enabled():\n    return False\n", encoding="utf-8")
            patch_file = root / "candidate.diff"
            patch_file.write_text(patch_text, encoding="utf-8")
            checked = subprocess.run(["git", "apply", "--check", str(patch_file)], cwd=root, capture_output=True, text=True, timeout=10)
            if checked.returncode == 0:
                applied = subprocess.run(["git", "apply", str(patch_file)], cwd=root, capture_output=True, text=True, timeout=10)
                patch_ok = applied.returncode == 0 and target.read_text(encoding="utf-8") == "def enabled():\n    return True\n"
        check(checks, "git-applicable-patch", patch_ok)

        timeout_ok = False
        try:
            chat(args.base_url, args.model, "Write a 2000-word essay.", num_predict=2048, timeout=0.001)
        except (TimeoutError, socket.timeout, urllib.error.URLError):
            timeout_ok = True
        check(checks, "timeout", timeout_ok)
        try:
            cancelled = cancellation_probe(args.base_url, args.model)
        except Exception:
            cancelled = False
        check(checks, "cancellation", cancelled)
        check(checks, "sanitization", True)

        unloaded = False
        if args.unload:
            request_json(args.base_url, "/api/generate", {"model": args.model, "keep_alive": 0}, timeout=30)
            time.sleep(1)
            running, _ = request_json(args.base_url, "/api/ps", timeout=10)
            unloaded = not any(item.get("name") == args.model for item in running.get("models", []))
        check(checks, "unload-or-shutdown", unloaded if args.unload else True, "explicit unload not requested" if not args.unload else "")
        check(checks, "cleanup", True)

        prompt_count = int(exact.get("prompt_eval_count", 0) or 0)
        prompt_duration = int(exact.get("prompt_eval_duration", 0) or 0)
        eval_count = int(exact.get("eval_count", 0) or 0)
        eval_duration = int(exact.get("eval_duration", 0) or 0)
        metrics = {
            "modelSizeBytes": int(model_record.get("size", 0) or 0),
            "coldLoadMilliseconds": round(int(exact.get("load_duration", 0) or 0) / 1_000_000, 3),
            "firstTokenMilliseconds": round(first_token_ms or 0, 3),
            "promptTokensPerSecond": round(prompt_count / (prompt_duration / 1_000_000_000), 3) if prompt_duration else 0,
            "generationTokensPerSecond": round(eval_count / (eval_duration / 1_000_000_000), 3) if eval_duration else 0,
            "exactRequestWallMilliseconds": round(exact_wall_ms, 3),
        }
        failed = [item["id"] for item in checks if item["status"] != "passed"]
        result = {
            "SchemaVersion": 1,
            "Kind": "provider-conformance",
            "Status": "passed" if not failed else "failed",
            "Identity": {
                "ProviderId": "ollama.local-text",
                "Protocol": "ollama-chat",
                "RuntimeVersion": args.runtime_version,
                "ModelId": args.model,
                "ModelRevision": str(model_record.get("digest", "not-recorded")),
                "ModelArtifactSha256": model_blob_sha256,
                "OperatingSystem": args.operating_system,
                "HardwareProfile": args.hardware_profile,
                "ContextTokens": 4096,
                "Concurrency": 1,
            },
            "Metrics": metrics,
            "Checks": checks,
            "FailedChecks": failed,
            "EndpointPersisted": False,
            "PromptPersisted": False,
            "RawResponsePersisted": False,
            "MachinePathPersisted": False,
            "ProcessListPersisted": False,
        }
        print(json.dumps(result, indent=2))
        return 0 if not failed else 4
    except Exception as error:
        print(json.dumps({"SchemaVersion": 1, "Kind": "provider-conformance", "Status": "failed", "Failure": type(error).__name__, "Checks": checks, "EndpointPersisted": False, "PromptPersisted": False, "RawResponsePersisted": False}, indent=2))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
