#!/usr/bin/env bash
set -uo pipefail

# Run reviewed CUDA qualification cells for newly inventoried models after a
# separately authorized process installs their exact artifacts. No downloads,
# model output, private host identity, or automatic promotion are performed.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly ORIGIN="http://127.0.0.1:11434"
readonly OPERATING_SYSTEM_ID="ubuntu-dual-v100"
readonly SYSTEM_MEMORY_GIB="128"
readonly AGGREGATE_GPU_MEMORY_GIB="64"
readonly WAIT_SECONDS=30
readonly MAX_WAIT_CYCLES=1440

readonly -a MODEL_CELLS=(
  "qwen36-27b-q4|qwen3.6:27b-q4_K_M|cuda-32gib-system-16gib"
  "qwen36-35b-a3b-q4|qwen3.6:35b-a3b-q4_K_M|cuda-32gib-system-64gib"
  "muse-glimmer-30b-q4|muse-glimmer:30b|cuda-32gib-system-64gib"
  "nemotron35-lightning-30b-a3b-q4|nemotron-3.5-lightning:30b-a3b-q4_K_M|cuda-64gib-system-96gib"
  "nemotron35-lightning-30b-a3b-q8|nemotron-3.5-lightning:30b-a3b-q8_0|cuda-64gib-system-96gib"
)

mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT" || exit 1

readonly CAMPAIGN_PID_FILE="$EVIDENCE_ROOT/cuda-new-model-campaign.pid"
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

paths = glob.glob(sys.argv[1] + "-task-*.json")
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
  IFS='|' read -r model_id model_name profile <<<"$cell"
  prefix="$EVIDENCE_ROOT/cuda-$model_id"
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
    printf '{"schemaVersion":1,"kind":"alpha2-cuda-campaign-status","modelId":"%s","outcome":"failed","errorCode":"model-install-wait-timeout","automaticPromotionAllowed":false}\n' \
      "$model_id" >"$prefix-status.json"
    continue
  fi

  printf 'TASK_GATE %s\n' "$model_id"
  for capability in general.chat content.write content.summarize; do
    python3 scripts/alpha2-model-task-qualification.py \
      --origin "$ORIGIN" \
      --model-id "$model_id" \
      --capability "$capability" \
      --profile-id "$profile" \
      --operating-system-id "$OPERATING_SYSTEM_ID" \
      --platform-family linux \
      --system-memory-gib "$SYSTEM_MEMORY_GIB" \
      --usable-gpu-memory-gib "$AGGREGATE_GPU_MEMORY_GIB" \
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
    --backend cuda \
    --system-memory-gib "$SYSTEM_MEMORY_GIB" \
    --usable-gpu-memory-gib "$AGGREGATE_GPU_MEMORY_GIB" \
    --duration-minutes 30 \
    --interval-seconds 120 \
    --qualification-inventory \
    --qualification-profile-id "$profile" \
    >"$prefix-soak.json" 2>"$prefix-soak.stderr"; then
    rm -f "$prefix-soak.stderr"
    printf 'PASSED %s\n' "$model_id"
  else
    printf '{"schemaVersion":1,"kind":"alpha2-cuda-campaign-status","modelId":"%s","outcome":"failed","errorCode":"bounded-soak-failed","automaticPromotionAllowed":false}\n' \
      "$model_id" >"$prefix-soak.json"
    printf 'SOAK_FAILED %s\n' "$model_id"
  fi
done

touch "$EVIDENCE_ROOT/cuda-new-model-campaign.complete"
printf 'CAMPAIGN_COMPLETE\n'
