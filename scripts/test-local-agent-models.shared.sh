#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OLLAMA_BASE_URL="http://127.0.0.1:11434"
TARGET_REPO="$(pwd)"
OUTPUT_PATH=""
PULL_MISSING=false
UNLOAD_AFTER_EACH=false
REMOVE_FAILED_MODELS=false
MODEL_PROFILE_PATH=""
VRAM_SELECTION_MODE="TotalDedicated"
AVAILABLE_VRAM_GB=0
INCLUDE_OVERSIZED_MODELS=false
TIMEOUT_SECONDS=120
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
    --remove-failed-models|-RemoveFailedModels)
      REMOVE_FAILED_MODELS=true
      shift
      ;;
    --model-profile-path|-ModelProfilePath)
      MODEL_PROFILE_PATH="$2"
      shift 2
      ;;
    --vram-selection-mode|-VramSelectionMode)
      VRAM_SELECTION_MODE="$2"
      shift 2
      ;;
    --available-vram-gb|-AvailableVramGb)
      AVAILABLE_VRAM_GB="$2"
      shift 2
      ;;
    --include-oversized-models|-IncludeOversizedModels)
      INCLUDE_OVERSIZED_MODELS=true
      shift
      ;;
    --timeout-seconds|-TimeoutSeconds)
      TIMEOUT_SECONDS="$2"
      shift 2
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

IFS=$'\t' read -r RUNTIME_RESIDENCY_MODE MAX_RESIDENT_MODELS PRELOAD_KEEP_ALIVE_MINUTES <<< "$("$SCRIPT_DIR/get-model-runtime-policy.shared.sh")"
if [ "$RUNTIME_RESIDENCY_MODE" = "unload-after-run" ]; then UNLOAD_AFTER_EACH=true; fi

printf '[1/8] Preparing local Agent model test run...\n' >&2
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

python3 - "$REPO_ROOT" "$OLLAMA_BASE_URL" "$TARGET_REPO" "$OUTPUT_PATH" "$PULL_MISSING" "$UNLOAD_AFTER_EACH" "$REMOVE_FAILED_MODELS" "$MODEL_PROFILE_PATH" "$VRAM_SELECTION_MODE" "$AVAILABLE_VRAM_GB" "$INCLUDE_OVERSIZED_MODELS" "$TIMEOUT_SECONDS" "$MAX_RESIDENT_MODELS" "$PRELOAD_KEEP_ALIVE_MINUTES" "${MODEL_ARGS[@]}" <<'PY'
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

repo_root, base_url, target_repo, output_path, pull_missing, unload_after_each, remove_failed_models, model_profile_path, vram_selection_mode, available_vram_gb, include_oversized_models, timeout_seconds, max_resident_models, preload_keep_alive_minutes, *rest = sys.argv[1:]
print("[2/8] Validating target repository path...", file=sys.stderr)
pull_missing = pull_missing.lower() == "true"
unload_after_each = unload_after_each.lower() == "true"
remove_failed_models = remove_failed_models.lower() == "true"
available_vram_gb = float(available_vram_gb or 0)
include_oversized_models = include_oversized_models.lower() == "true"
timeout_seconds = int(timeout_seconds or 120)
max_resident_models = int(max_resident_models)
preload_keep_alive_minutes = int(preload_keep_alive_minutes)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--model", action="append", default=[])
args, _ = parser.parse_known_args(rest)

base_url = base_url.rstrip("/")
if not os.path.isdir(target_repo):
    raise SystemExit(f"TargetRepo does not exist: {target_repo}")


def current_platform_name():
    if sys.platform == "darwin":
        return "macOS"
    if sys.platform.startswith("linux"):
        return "Linux"
    if sys.platform.startswith("win"):
        return "Windows"
    return "Unknown"

def model_host_platform(path):
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                profile = json.load(handle)
            if profile.get("Platform"):
                return str(profile["Platform"])
        except Exception:
            return current_platform_name()
    return current_platform_name()

def normalize_platform_name(value):
    value = str(value or "")
    if re.search(r"(?i)mac|darwin", value):
        return "macOS"
    if re.search(r"(?i)linux", value):
        return "Linux"
    if re.search(r"(?i)windows", value):
        return "Windows"
    return "Unknown"

def model_pull_eligibility(model, host_platform):
    normalized_platform = normalize_platform_name(host_platform)
    if re.search(r"(?i)cloud", model):
        return {
            "Pullable": False,
            "Reason": "Cloud catalog tag; local Ollama pull is not supported.",
            "FailureSignal": "MODEL_SKIPPED_FOR_PLATFORM",
        }
    if re.search(r"(?i)-mlx($|[-_:])", model) and normalized_platform != "macOS":
        return {
            "Pullable": False,
            "Reason": "MLX model tag requires a macOS Apple Silicon model host.",
            "FailureSignal": "MODEL_SKIPPED_FOR_PLATFORM",
        }
    return {
        "Pullable": True,
        "Reason": "Model tag is pullable for this host platform.",
        "FailureSignal": "none",
    }

def available_vram_from_profile(path, selection_mode):
    if not path:
        return None
    if not os.path.exists(path):
        raise SystemExit(f"ModelProfilePath does not exist: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        profile = json.load(handle)
    values = []
    for gpu in profile.get("Gpus") or []:
        value = gpu.get("VramGb")
        memory_type = str(gpu.get("MemoryType") or "")
        if memory_type and not re.search(r"(?i)dedicated|unknown", memory_type):
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if value > 0:
            values.append(value)
    if not values:
        return None
    if selection_mode == "MaxDedicated":
        return round(max(values), 2)
    return round(sum(values), 2)


def post_json(path, body, timeout=None):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        base_url + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout or timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))

def get_json(path, timeout=None):
    with urllib.request.urlopen(base_url + path, timeout=timeout or timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))

print("[3/8] Connecting to Ollama and reading installed models...", file=sys.stderr)
try:
    tags = get_json("/api/tags")
    installed = {m.get("name") for m in tags.get("models", [])}
except Exception as exc:
    raise SystemExit(f"Could not reach Ollama at {base_url}: {exc}")

effective_available_vram_gb = available_vram_gb
vram_source = "explicit" if effective_available_vram_gb > 0 else None
if effective_available_vram_gb <= 0 and model_profile_path:
    print(f"[4/8] Reading VRAM from model profile using {vram_selection_mode} mode...", file=sys.stderr)
    profile_vram = available_vram_from_profile(model_profile_path, vram_selection_mode)
    if profile_vram and profile_vram > 0:
        effective_available_vram_gb = profile_vram
        vram_source = f"model-profile:{vram_selection_mode}"

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
        ]
    return list(dict.fromkeys(candidates))

model_host = model_host_platform(model_profile_path)
print(f"[5/8] Model host platform: {model_host}", file=sys.stderr)

models = [m for m in args.model if m]
if not models:
    models = catalog_candidates()

print(f"[5/8] Candidate models: {', '.join(models)}", file=sys.stderr)
if effective_available_vram_gb > 0:
    print(f"[5/8] Available VRAM estimate: {effective_available_vram_gb} GB ({vram_source})", file=sys.stderr)
else:
    print("[5/8] No VRAM estimate available; VRAM gating will not skip models.", file=sys.stderr)
print(f"[5/8] Timeout per Ollama API request: {timeout_seconds} seconds. Large model pulls may need a higher timeout or a manual ollama pull first.", file=sys.stderr)


def model_size_billion(model):
    match = re.search(r"(?i)(\d+(?:\.\d+)?)b", model)
    if not match:
        return 0
    return float(match.group(1))

def recommended_min_vram_gb(model):
    if re.search(r"(?i)(cloud|-mlx)", model):
        return 999999
    size = model_size_billion(model)
    if size <= 0:
        return 0
    if size <= 1:
        return 4
    if size <= 2:
        return 6
    if size <= 4:
        return 8
    if size <= 9:
        return 12
    if size <= 14:
        return 20
    if size <= 27:
        return 36
    if size <= 35:
        return 48
    if size <= 80:
        return 80
    if size <= 122:
        return 128
    return 512

def pull_model(model):
    try:
        post_json("/api/pull", {"model": model, "stream": False})
        return {"Attempted": True, "Success": True, "Error": None}
    except Exception as exc:
        return {"Attempted": True, "Success": False, "Error": str(exc)}

def delete_model(model):
    try:
        data = json.dumps({"model": model}).encode("utf-8")
        req = urllib.request.Request(
            base_url + "/api/delete",
            data=data,
            headers={"Content-Type": "application/json"},
            method="DELETE",
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            response.read()
        return {"Attempted": True, "Success": True, "Error": None}
    except Exception as exc:
        return {"Attempted": True, "Success": False, "Error": str(exc)}

def load_model(model, keep_alive=None):
    try:
        if keep_alive not in (0, "0"):
            running = get_json("/api/ps").get("models", [])
            other_resident = [item for item in running if item.get("name") != model and item.get("model") != model]
            if len(other_resident) >= max_resident_models:
                return {"Success": False, "Error": f"Runtime policy blocks loading {model}: {len(other_resident)} other model(s) are resident."}
            if other_resident:
                print(f"Runtime policy warning: another model is resident before loading {model}.", file=sys.stderr)
        if keep_alive is None:
            keep_alive = f"{preload_keep_alive_minutes}m"
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

def model_preference_rank(model):
    if re.search(r"(?i)^qwen3\.5:9b$", model):
        return 0
    if re.search(r"(?i)(coder|code|codestral|devstral)", model):
        return 1
    if re.search(r"(?i)(qwen|gpt-oss|llama3\.1)", model):
        return 2
    return 3

def test_recommendation(results):
    approved = [item for item in results if item.get("ApprovedWriteCandidate") is True]
    if not approved:
        return {
            "Status": "no-approved-model",
            "PrimaryModel": None,
            "Alternates": [],
            "Reason": "No model passed both structured tool-call and exact-content checks.",
            "RecommendedUse": "Do not install a write-safe model from this run.",
            "NextStep": "Review failure signals, adjust candidates or settings, and rerun the test.",
        }
    ranked = sorted(
        approved,
        key=lambda item: (
            item.get("VramRecommendation", {}).get("RecommendedMinVramGb") or 9999,
            model_preference_rank(item.get("Model", "")),
            item.get("Model", ""),
        ),
    )
    primary = ranked[0]
    alternates = [item["Model"] for item in ranked[1:4]]
    return {
        "Status": "recommended",
        "PrimaryModel": primary["Model"],
        "Alternates": alternates,
        "Reason": "Selected the smallest passing model, with a preference for previously validated coding-oriented local-agent families.",
        "RecommendedUse": "Use as the first model to validate in the editor. Keep approved-write validation as the final gate.",
        "NextStep": "Run Continue read-only and approved-write smoke tests before installing this model as write-safe.",
    }

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
total_models = len(models)
for index, model in enumerate(models, start=1):
    print(f"[6/8] Testing model {index}/{total_models}: {model}")
    recommended_min_vram = recommended_min_vram_gb(model)
    fits_available_vram = True
    if effective_available_vram_gb > 0 and recommended_min_vram > 0:
        fits_available_vram = recommended_min_vram <= effective_available_vram_gb
    vram_recommendation = {
        "AvailableVramGb": effective_available_vram_gb if effective_available_vram_gb > 0 else None,
        "RecommendedMinVramGb": recommended_min_vram if recommended_min_vram > 0 and recommended_min_vram < 999999 else None,
        "FitsAvailableVram": bool(fits_available_vram),
    }
    platform_eligibility = model_pull_eligibility(model, model_host)
    if not platform_eligibility["Pullable"]:
        print(f"[6/8] Skipping {model} before pull: {platform_eligibility['Reason']}", file=sys.stderr)
        results.append({"Model": model, "Installed": False, "Pull": {"Attempted": False, "Success": False, "Error": platform_eligibility["Reason"]}, "Loaded": False, "ToolCall": None, "ExactContent": None, "FailureSignal": platform_eligibility["FailureSignal"], "ApprovedWriteCandidate": False, "Removal": {"Attempted": False, "Success": False, "Error": None}, "ModelHostPlatform": model_host, "PlatformEligibility": platform_eligibility, "VramRecommendation": vram_recommendation})
        continue
    if not fits_available_vram and not include_oversized_models:
        print(f"[6/8] Skipping {model} before pull: estimated minimum VRAM is {recommended_min_vram} GB and available estimate is {effective_available_vram_gb} GB.", file=sys.stderr)
        results.append({"Model": model, "Installed": False, "Pull": {"Attempted": False, "Success": False, "Error": "Skipped before pull because the model is above the available VRAM limit."}, "Loaded": False, "ToolCall": None, "ExactContent": None, "FailureSignal": "MODEL_SKIPPED_FOR_VRAM", "ApprovedWriteCandidate": False, "Removal": {"Attempted": False, "Success": False, "Error": None}, "ModelHostPlatform": model_host, "PlatformEligibility": platform_eligibility, "VramRecommendation": vram_recommendation})
        continue
    is_installed = model in installed
    pull = {"Attempted": False, "Success": is_installed, "Error": None}
    if not is_installed and pull_missing:
        print(f"[6/8] Pulling missing model: {model}. This can take several minutes for large models. Timeout: {timeout_seconds} seconds.")
        pull = pull_model(model)
        is_installed = bool(pull["Success"])
        if not pull["Success"]:
            print(f"[6/8] Pull failed or timed out for {model}. Increase --timeout-seconds or run ollama pull on the model server first, then rerun the test.", file=sys.stderr)
    if not is_installed:
        results.append({"Model": model, "Installed": False, "Pull": pull, "Loaded": False, "ToolCall": None, "ExactContent": None, "FailureSignal": "MODEL_NOT_INSTALLED", "ApprovedWriteCandidate": False, "Removal": {"Attempted": False, "Success": False, "Error": None}, "ModelHostPlatform": model_host, "PlatformEligibility": platform_eligibility, "VramRecommendation": vram_recommendation})
        continue
    print(f"[6/8] Loading {model} and running API preflight checks...", file=sys.stderr)
    load = load_model(model)
    tools = tool_test(model)
    content = content_test(model)
    signal = failure_signal(load, tools, content)
    removal = {"Attempted": False, "Success": False, "Error": None}
    if unload_after_each or (remove_failed_models and signal != "none"):
        print(f"[7/8] Unloading {model} from Ollama...", file=sys.stderr)
        load_model(model, 0)
    if remove_failed_models and signal != "none":
        print(f"[7/8] Removing failed model: {model}")
        removal = delete_model(model)
    results.append({"Model": model, "Installed": True, "Pull": pull, "Loaded": load["Success"], "ToolCall": tools, "ExactContent": content, "FailureSignal": signal, "ApprovedWriteCandidate": signal == "none", "Removal": removal, "ModelHostPlatform": model_host, "PlatformEligibility": platform_eligibility, "VramRecommendation": vram_recommendation})

recommendation = test_recommendation(results)

report = {
    "GeneratedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
    "OllamaBaseUrl": "redacted",
    "TargetRepo": "redacted",
    "TargetRepoDetected": os.path.isdir(target_repo),
    "PullMissing": pull_missing,
    "UnloadAfterEach": unload_after_each,
    "RemoveFailedModels": remove_failed_models,
    "ModelProfilePath": "redacted" if model_profile_path else None,
    "VramSelectionMode": vram_selection_mode,
    "AvailableVramGb": effective_available_vram_gb if effective_available_vram_gb > 0 else None,
    "AvailableVramSource": vram_source,
    "ModelHostPlatform": model_host,
    "IncludeOversizedModels": include_oversized_models,
    "Recommendation": recommendation,
    "Results": results,
    "Note": "This tests Ollama API tool-call and exact-content behavior. It does not replace Continue UI Apply validation.",
}

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)

print("[8/8] Writing sanitized report and summary...", file=sys.stderr)

for result in results:
    status = "candidate" if result["ApprovedWriteCandidate"] else "failed"
    print(f"{result['Model']}: {status} ({result['FailureSignal']})")
if recommendation.get("PrimaryModel"):
    print(f"Recommended model: {recommendation['PrimaryModel']}")
    if recommendation.get("Alternates"):
        print(f"Alternate passing models: {', '.join(recommendation['Alternates'])}")
    print(f"Recommendation note: {recommendation['NextStep']}")
else:
    print("Recommended model: none")
    print(f"Recommendation note: {recommendation['NextStep']}")
print(f"Report written to {output_path}")
PY
