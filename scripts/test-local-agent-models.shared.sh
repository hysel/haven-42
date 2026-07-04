#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OLLAMA_BASE_URL="http://127.0.0.1:11434"
TARGET_REPO="$(pwd)"
OUTPUT_PATH=""
PULL_MISSING=false
UNLOAD_AFTER_EACH=false
MODELS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --ollama-base-url|-OllamaBaseUrl)
      OLLAMA_BASE_URL="$2"
      shift 2
      ;;
    --target-repo|-TargetRepo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --pull-missing|-PullMissing)
      PULL_MISSING=true
      shift
      ;;
    --unload-after-each|-UnloadAfterEach)
      UNLOAD_AFTER_EACH=true
      shift
      ;;
    --model|-Model)
      MODELS+=("$2")
      shift 2
      ;;
    --models|-Models)
      IFS=',' read -r -a split_models <<< "$2"
      for model in "${split_models[@]}"; do
        MODELS+=("$(printf '%s' "$model" | sed 's/^ *//;s/ *$//')")
      done
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for this validation script.\n' >&2
  exit 1
fi

if [ -z "$OUTPUT_PATH" ]; then
  OUTPUT_PATH="$REPO_ROOT/runtime-validation-output/local-agent-model-tests-$(date '+%Y%m%d-%H%M%S').json"
fi

MODEL_ARGS=()
for model in "${MODELS[@]}"; do
  [ -z "$model" ] && continue
  MODEL_ARGS+=(--model "$model")
done

python3 - "$REPO_ROOT" "$OLLAMA_BASE_URL" "$TARGET_REPO" "$OUTPUT_PATH" "$PULL_MISSING" "$UNLOAD_AFTER_EACH" "${MODEL_ARGS[@]}" <<'PY'
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

repo_root, base_url, target_repo, output_path, pull_missing, unload_after_each, *rest = sys.argv[1:]
pull_missing = pull_missing.lower() == "true"
unload_after_each = unload_after_each.lower() == "true"

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--model", action="append", default=[])
args, _ = parser.parse_known_args(rest)

base_url = base_url.rstrip("/")

def post_json(path, body, timeout=120):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        base_url + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def get_json(path, timeout=120):
    with urllib.request.urlopen(base_url + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def catalog_candidates():
    path = os.path.join(repo_root, "config", "model-recommendations.tsv")
    candidates = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("|")
                if len(parts) >= 3 and parts[2].strip():
                    candidates.append(parts[2].strip())
    if not candidates:
        candidates = [
            "qwen3.5:9b",
            "devstral-small-2:24b",
            "qwen3-coder:30b",
        ]
    return list(dict.fromkeys(candidates))

models = [m for m in args.model if m]
if not models:
    models = catalog_candidates()

try:
    tags = get_json("/api/tags")
    installed = {m.get("name") for m in tags.get("models", [])}
except Exception as exc:
    raise SystemExit(f"Could not reach Ollama at {base_url}: {exc}")

def pull_model(model):
    try:
        post_json("/api/pull", {"model": model, "stream": False})
        return {"Attempted": True, "Success": True, "Error": None}
    except Exception as exc:
        return {"Attempted": True, "Success": False, "Error": str(exc)}

def load_model(model, keep_alive="10m"):
    try:
        post_json("/api/chat", {"model": model, "messages": [], "keep_alive": keep_alive, "stream": False})
        return {"Success": True, "Error": None}
    except Exception as exc:
        return {"Success": False, "Error": str(exc)}

def tool_test(model):
    tools = [{
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a repository file by relative path.",
            "parameters": {
                "type": "object",
                "properties": {"filepath": {"type": "string"}},
                "required": ["filepath"],
            },
        },
    }]
    try:
        response = post_json("/api/chat", {
            "model": model,
            "stream": False,
            "think": False,
            "keep_alive": "10m",
            "options": {"temperature": 0, "num_predict": 256},
            "tools": tools,
            "messages": [{"role": "user", "content": "Use the read_file tool to read README.md. Return a tool call only."}],
        })
        message = response.get("message", {})
        content = message.get("content") or ""
        calls = message.get("tool_calls") or []
        first = calls[0] if calls else {}
        func = first.get("function", {})
        name = func.get("name")
        arguments = func.get("arguments") or {}
        filepath = arguments.get("filepath")
        raw = any(token in content.lower() for token in ["<function=", "tool_call", "function="]) or '"name"' in content
        return {
            "Passed": name == "read_file" and filepath == "README.md" and not raw,
            "ToolName": name,
            "FilePath": filepath,
            "RawToolSyntax": raw,
            "ContentPreview": " ".join(content.split()),
            "Error": None,
        }
    except Exception as exc:
        return {"Passed": False, "ToolName": None, "FilePath": None, "RawToolSyntax": False, "ContentPreview": "", "Error": str(exc)}

def content_test(model):
    expected = "Continue Agent write test passed."
    try:
        response = post_json("/api/chat", {
            "model": model,
            "stream": False,
            "think": False,
            "keep_alive": "10m",
            "options": {"temperature": 0, "num_predict": 128},
            "messages": [
                {"role": "system", "content": "Return only the exact requested file content. Do not include reasoning, tags, markdown, quotes, or explanations."},
                {"role": "user", "content": f"The entire file content must be exactly one line: {expected}"},
            ],
        })
        content = response.get("message", {}).get("content") or ""
        normalized = content.replace("\r\n", "\n").strip()
        lower = content.lower()
        think = "<think>" in lower or "</think>" in lower
        markdown = "```" in content
        raw = any(token in lower for token in ["<function=", "tool_call", "function="])
        return {"Passed": normalized == expected and not think and not markdown and not raw, "Expected": expected, "Actual": normalized, "ThinkLeak": think, "MarkdownFence": markdown, "RawToolSyntax": raw, "Error": None}
    except Exception as exc:
        return {"Passed": False, "Expected": expected, "Actual": "", "ThinkLeak": False, "MarkdownFence": False, "RawToolSyntax": False, "Error": str(exc)}

def failure_signal(load_result, tool_result, content_result):
    if not load_result["Success"]:
        return "MODEL_LOAD_FAILED"
    if tool_result.get("Error") and "does not support tools" in tool_result["Error"]:
        return "MODEL_DOES_NOT_SUPPORT_TOOLS"
    if tool_result.get("RawToolSyntax"):
        return "RAW_TOOL_CALL_OUTPUT"
    if not tool_result.get("Passed"):
        return "TOOL_CALL_FAILED"
    if content_result.get("ThinkLeak"):
        return "THINK_TAG_LEAK"
    if content_result.get("RawToolSyntax"):
        return "RAW_TOOL_CALL_OUTPUT"
    if not content_result.get("Passed"):
        return "INCORRECT_EXACT_CONTENT"
    return "none"

results = []
for model in models:
    print(f"Testing model: {model}")
    is_installed = model in installed
    pull = {"Attempted": False, "Success": is_installed, "Error": None}
    if not is_installed and pull_missing:
        print(f"Pulling missing model: {model}")
        pull = pull_model(model)
        is_installed = bool(pull["Success"])
    if not is_installed:
        results.append({"Model": model, "Installed": False, "Pull": pull, "Loaded": False, "ToolCall": None, "ExactContent": None, "FailureSignal": "MODEL_NOT_INSTALLED", "ApprovedWriteCandidate": False})
        continue
    load = load_model(model)
    tools = tool_test(model)
    content = content_test(model)
    signal = failure_signal(load, tools, content)
    if unload_after_each:
        load_model(model, 0)
    results.append({"Model": model, "Installed": True, "Pull": pull, "Loaded": load["Success"], "ToolCall": tools, "ExactContent": content, "FailureSignal": signal, "ApprovedWriteCandidate": signal == "none"})

report = {
    "GeneratedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
    "OllamaBaseUrl": "redacted",
    "TargetRepo": "redacted",
    "TargetRepoDetected": os.path.isdir(target_repo),
    "PullMissing": pull_missing,
    "UnloadAfterEach": unload_after_each,
    "Results": results,
    "Note": "This tests Ollama API tool-call and exact-content behavior. It does not replace Continue UI Apply validation.",
}

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)

for result in results:
    status = "candidate" if result["ApprovedWriteCandidate"] else "failed"
    print(f"{result['Model']}: {status} ({result['FailureSignal']})")
print(f"Report written to {output_path}")
PY
