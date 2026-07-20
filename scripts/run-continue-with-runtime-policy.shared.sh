#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL=""; PROMPT=""; CONFIG_PATH=""; TARGET_REPO="$(pwd)"; OLLAMA_BASE_URL="http://127.0.0.1:11434"; CONTINUE_COMMAND="npx"; TIMEOUT_SECONDS=900; READ_ONLY=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;; --prompt) PROMPT="$2"; shift 2 ;; --config-path) CONFIG_PATH="$2"; shift 2 ;; --target-repo) TARGET_REPO="$2"; shift 2 ;; --ollama-base-url) OLLAMA_BASE_URL="$2"; shift 2 ;; --continue-command) CONTINUE_COMMAND="$2"; shift 2 ;; --timeout-seconds) TIMEOUT_SECONDS="$2"; shift 2 ;; --readonly) READ_ONLY=true; shift ;; *) printf 'Unknown argument: %s\n' "$1" >&2; exit 1 ;; esac
done
[ -n "$MODEL" ] && [ -n "$PROMPT" ] || { printf '%s\n' '--model and --prompt are required.' >&2; exit 1; }
[ -n "$CONFIG_PATH" ] || CONFIG_PATH="$TARGET_REPO/.continue/config.local.yaml"
[ -f "$CONFIG_PATH" ] && [ -d "$TARGET_REPO" ] || { printf '%s\n' 'ConfigPath or TargetRepo does not exist.' >&2; exit 1; }
IFS=$'\t' read -r RESIDENCY_MODE MAX_RESIDENT PRELOAD_MINUTES <<< "$("$SCRIPT_DIR/get-model-runtime-policy.shared.sh")"
POLICY_PYTHON="python3"; command -v "$POLICY_PYTHON" >/dev/null 2>&1 || POLICY_PYTHON="python"; command -v "$POLICY_PYTHON" >/dev/null 2>&1 || POLICY_PYTHON="py"
command -v "$POLICY_PYTHON" >/dev/null 2>&1 || { printf '%s\n' 'python3, python, or py is required.' >&2; exit 1; }
BASE="${OLLAMA_BASE_URL%/}"
unload() { curl -fsS --max-time 60 -X POST "$BASE/api/generate" -H 'Content-Type: application/json' -d "{\"model\":\"$MODEL\",\"prompt\":\"\",\"keep_alive\":0,\"stream\":false}" >/dev/null; }
if [ "$RESIDENCY_MODE" = "unload-after-run" ]; then trap 'unload || printf "Could not unload %s.\n" "$MODEL" >&2' EXIT; fi
running="$(curl -fsS --max-time 30 "$BASE/api/ps")"
other="$(printf '%s' "$running" | "$POLICY_PYTHON" -c 'import json,sys; m=sys.argv[1]; print(sum(1 for x in json.load(sys.stdin).get("models",[]) if x.get("name") != m and x.get("model") != m))' "$MODEL")"
[ "$other" -lt "$MAX_RESIDENT" ] || { printf 'Runtime policy blocks loading %s: %s other model(s) are resident.\n' "$MODEL" "$other" >&2; exit 1; }
curl -fsS --max-time 900 -X POST "$BASE/api/generate" -H 'Content-Type: application/json' -d "{\"model\":\"$MODEL\",\"prompt\":\"\",\"keep_alive\":\"${PRELOAD_MINUTES}m\",\"stream\":false}" >/dev/null
args=(); [ "$CONTINUE_COMMAND" = npx ] && args+=(-y @continuedev/cli); args+=(--config "$CONFIG_PATH"); [ "$READ_ONLY" = true ] && args+=(--readonly) || args+=(--auto); args+=(--format json --silent -p "$PROMPT")
cd "$TARGET_REPO"; if command -v timeout >/dev/null 2>&1; then timeout "$TIMEOUT_SECONDS" "$CONTINUE_COMMAND" "${args[@]}"; else "$CONTINUE_COMMAND" "${args[@]}"; fi
