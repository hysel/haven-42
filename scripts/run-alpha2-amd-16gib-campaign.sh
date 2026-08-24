#!/usr/bin/env bash
set -uo pipefail

# Run the reviewed 16 GiB AMD boundary cells after a separately authorized
# process installs their exact model tags. This script does not download a
# model, start a runtime, retain model output, or change selection policy.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly SYSTEM_MEMORY_GIB="${2:-31}"
readonly GPU_MEMORY_GIB="${3:-15}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PROFILE="vulkan-16gib-system-32gib"
readonly OPERATING_SYSTEM_ID="ubuntu-26.04-rx6800"
readonly WAIT_SECONDS=30
readonly MAX_WAIT_CYCLES=1440

readonly -a MODEL_CELLS=(
  "qwen35-9b-q4|qwen3.5:9b"
  "gemma4-12b-qat|gemma4:12b-it-qat"
  "gemma3-12b-q4|gemma3:12b-it-q4_K_M"
)

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || {
  printf 'Refused: BASE must be an existing absolute non-link directory.\n' >&2
  exit 1
}
[[ "$SYSTEM_MEMORY_GIB" =~ ^[0-9]+([.][0-9]+)?$ ]] || exit 2
[[ "$GPU_MEMORY_GIB" =~ ^[0-9]+([.][0-9]+)?$ ]] || exit 2

mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT" || exit 1

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
  IFS='|' read -r model_id model_name <<<"$cell"
  prefix="$EVIDENCE_ROOT/rx6800-$model_id"
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

touch "$EVIDENCE_ROOT/rx6800-16gib-campaign.complete"
printf 'CAMPAIGN_COMPLETE\n'
