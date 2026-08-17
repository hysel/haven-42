#!/usr/bin/env bash
set -Eeuo pipefail

# Qualify the approved compact release candidates after the primary RX 5700 XT
# campaign and its separately authorized download queue finish. Exact manifest
# identity is checked before every cell; only the exact test artifacts are
# removed after their evidence is closed.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly OLLAMA_BIN="${OLLAMA_BIN:-$BASE/runtime/0.32.13/bin/ollama}"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PREREQUISITE="$EVIDENCE_ROOT/rx5700xt-campaign.complete"
readonly PROFILE="vulkan-8gib-system-16gib"
readonly OPERATING_SYSTEM_ID="ubuntu-26.04-rx5700xt"
readonly SYSTEM_MEMORY_GIB="121"
readonly GPU_MEMORY_GIB="8"
readonly WAIT_SECONDS=30

readonly -a MODEL_CELLS=(
  "ornith-10-9b-q4|ornith:9b|a75697c145891910e312c95e4a9fc1ccb8653e5ef543b23b0403a4665b82fd91"
  "lfm25-8b-a1b-q4|lfm2.5:8b|9cf756159fc2f3b9128c6a3f544ec90c5e9b8afdbb4179a57b8aea9de589cfb2"
)

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || {
  printf 'Refused: BASE must be an existing absolute non-link directory.\n' >&2
  exit 1
}
[[ -x "$OLLAMA_BIN" && ! -L "$OLLAMA_BIN" ]] || {
  printf 'Refused: exact Ollama executable is unavailable.\n' >&2
  exit 1
}

mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT"

readonly PID_FILE="$EVIDENCE_ROOT/rx5700xt-release-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

while [[ ! -f "$PREREQUISITE" ]]; do
  sleep "$WAIT_SECONDS"
done

model_manifest() {
  local model_name="$1"
  python3 - "$ORIGIN" "$model_name" <<'PY'
import json
import sys
import urllib.request

origin, wanted = sys.argv[1:]
with urllib.request.urlopen(origin + "/api/tags", timeout=10) as response:
    payload = json.load(response)
matches = [
    item for item in payload.get("models", [])
    if isinstance(item, dict) and item.get("name") == wanted
]
if len(matches) != 1:
    raise SystemExit(1)
print(matches[0].get("digest", ""))
PY
}

for cell in "${MODEL_CELLS[@]}"; do
  IFS='|' read -r model_id model_name expected_manifest <<<"$cell"
  prefix="$EVIDENCE_ROOT/rx5700xt-$model_id"
  printf 'PULL %s\n' "$model_id"
  "$OLLAMA_BIN" pull "$model_name"
  actual_manifest=$(model_manifest "$model_name" 2>/dev/null || true)
  if [[ "$actual_manifest" != "$expected_manifest" ]]; then
    printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"manifest-missing-or-mismatch","automaticPromotionAllowed":false}\n' \
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

  if ! python3 - "$prefix" <<'PY'
import glob
import json
import sys

paths = glob.glob(sys.argv[1] + "-task-*.json")
if len(paths) != 3:
    raise SystemExit(1)
values = [json.load(open(path, encoding="utf-8")) for path in paths]
raise SystemExit(0 if all(value.get("outcome") == "passed" for value in values) else 1)
PY
  then
    printf 'TASK_GATE_FAILED %s\n' "$model_id"
    "$OLLAMA_BIN" rm "$model_name" >/dev/null 2>&1 || true
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

  if [[ "$model_id" == "ornith-10-9b-q4" ]]; then
    extended_capabilities=(coding tools failure-recovery)
  else
    extended_capabilities=(tools thinking failure-recovery)
  fi
  for capability in "${extended_capabilities[@]}"; do
    printf 'EXTENDED %s %s\n' "$model_id" "$capability"
    python3 scripts/alpha2-model-extended-qualification.py \
      --origin "$ORIGIN" \
      --model-id "$model_id" \
      --capability "$capability" \
      --profile-id "$PROFILE" \
      --operating-system-id "$OPERATING_SYSTEM_ID" \
      --platform-family linux \
      --system-memory-gib "$SYSTEM_MEMORY_GIB" \
      --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
      >"$prefix-extended-$capability.json" || true
  done
  "$OLLAMA_BIN" rm "$model_name" >/dev/null 2>&1 || true
done

touch "$EVIDENCE_ROOT/rx5700xt-release-followup.complete"
printf 'CAMPAIGN_COMPLETE\n'
