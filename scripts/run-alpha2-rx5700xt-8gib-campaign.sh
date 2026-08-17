#!/usr/bin/env bash
set -uo pipefail

# Run the reviewed 8 GiB Vulkan qualification cells after models have been
# installed by a separately authorized process. This script never downloads a
# model, changes a runtime, or records prompts and responses.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PROFILE="vulkan-8gib-system-16gib"
readonly OPERATING_SYSTEM_ID="ubuntu-26.04-rx5700xt"
readonly SYSTEM_MEMORY_GIB="121"
readonly GPU_MEMORY_GIB="8"
readonly WAIT_SECONDS=30
readonly MAX_WAIT_CYCLES=1440

readonly -a MODEL_CELLS=(
  "gemma3-1b-q4|gemma3:1b-it-q4_K_M"
  "llama32-3b-q4|llama3.2:3b-instruct-q4_K_M"
  "granite41-3b-q4|granite4.1:3b-q4_K_M"
  "phi4-mini-38b-q4|phi4-mini:3.8b-q4_K_M"
  "ministral3-3b-q4|ministral-3:3b-instruct-2512-q4_K_M"
  "gemma3-4b-q4|gemma3:4b-it-q4_K_M"
  "gemma4-e2b-qat|gemma4:e2b-it-qat"
  "gemma4-e4b-qat|gemma4:e4b-it-qat"
  "granite41-8b-q4|granite4.1:8b-q4_K_M"
  "ministral3-8b-q4|ministral-3:8b-instruct-2512-q4_K_M"
)

mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT" || exit 1

readonly CAMPAIGN_PID_FILE="$EVIDENCE_ROOT/rx5700xt-campaign.pid"
printf '%s\n' "$$" >"$CAMPAIGN_PID_FILE"
trap 'rm -f "$CAMPAIGN_PID_FILE"' EXIT

model_is_installed() {
  local model_name="$1"
  python3 - "$ORIGIN" "$model_name" <<'PY'
import json
import sys
import urllib.request

origin, wanted = sys.argv[1:]
try:
    with urllib.request.urlopen(origin + "/api/tags", timeout=10) as response:
        payload = json.load(response)
except Exception:
    raise SystemExit(1)
matches = [
    item for item in payload.get("models", [])
    if isinstance(item, dict) and item.get("name") == wanted
]
raise SystemExit(0 if len(matches) == 1 else 1)
PY
}

task_gate_passed() {
  local prefix="$1"
  python3 - "$prefix" <<'PY'
import glob
import json
import sys

prefix = sys.argv[1]
paths = glob.glob(prefix + "-task-*.json")
if len(paths) != 3:
    raise SystemExit(1)
try:
    values = [json.load(open(path, encoding="utf-8")) for path in paths]
except (OSError, ValueError):
    raise SystemExit(1)
raise SystemExit(0 if all(value.get("outcome") == "passed" for value in values) else 1)
PY
}

for cell in "${MODEL_CELLS[@]}"; do
  IFS='|' read -r model_id model_name <<<"$cell"
  prefix="$EVIDENCE_ROOT/rx5700xt-$model_id"
  printf 'WAITING %s\n' "$model_id"
  installed=false
  for ((cycle = 0; cycle < MAX_WAIT_CYCLES; cycle += 1)); do
    if model_is_installed "$model_name"; then
      installed=true
      break
    fi
    sleep "$WAIT_SECONDS"
  done
  if [[ "$installed" != true ]]; then
    printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"model-install-wait-timeout","automaticPromotionAllowed":false}\n' \
      "$model_id" >"$prefix-status.json"
    continue
  fi

  printf 'TASK_GATE %s\n' "$model_id"
  for capability in general.chat content.write content.summarize; do
    python3 scripts/alpha2-model-task-qualification.py \
      --origin "$ORIGIN" \
      --model-id "$model_id" \
      --capability "$capability" \
      --profile-id "$PROFILE" \
      --operating-system-id "$OPERATING_SYSTEM_ID" \
      --platform-family linux \
      --system-memory-gib "$SYSTEM_MEMORY_GIB" \
      --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
      >"$prefix-task-$capability.json" || true
  done

  if ! task_gate_passed "$prefix"; then
    printf 'TASK_GATE_FAILED %s\n' "$model_id"
    continue
  fi

  printf 'SOAK %s\n' "$model_id"
  if python3 scripts/alpha2-linux-soak.py \
    --origin "$ORIGIN" \
    --model-id "$model_id" \
    --operating-system-id "$OPERATING_SYSTEM_ID" \
    --platform-family linux \
    --backend vulkan \
    --system-memory-gib "$SYSTEM_MEMORY_GIB" \
    --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
    --duration-minutes 30 \
    --interval-seconds 120 \
    --qualification-inventory \
    --qualification-profile-id "$PROFILE" \
    >"$prefix-soak.json" 2>"$prefix-soak.stderr"; then
    rm -f "$prefix-soak.stderr"
    printf 'PASSED %s\n' "$model_id"
  else
    printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"bounded-soak-failed","automaticPromotionAllowed":false}\n' \
      "$model_id" >"$prefix-soak.json"
    printf 'SOAK_FAILED %s\n' "$model_id"
  fi
done

touch "$EVIDENCE_ROOT/rx5700xt-campaign.complete"
printf 'CAMPAIGN_COMPLETE\n'
