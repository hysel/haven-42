#!/usr/bin/env bash
set -Eeuo pipefail

# Run the approved exact Qwen 3.8 candidate after the first CUDA release
# campaign completes. The script removes only the five exact artifacts owned by
# that completed campaign, acquires one immutable candidate, verifies its
# manifest identity, runs bounded qualification, and removes that candidate
# after evidence is closed. It never changes a default or support label.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly OLLAMA_BIN="${OLLAMA_BIN:-/usr/local/bin/ollama}"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PREREQUISITE="$EVIDENCE_ROOT/cuda-new-model-campaign.complete"
readonly MODEL_ID="qwen38-27b-q4"
readonly MODEL_NAME="qwen3.8:27b"
readonly EXPECTED_MANIFEST="22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643"
readonly PROFILE="cuda-32gib-system-64gib"
readonly OPERATING_SYSTEM_ID="ubuntu-dual-v100"
readonly SYSTEM_MEMORY_GIB="128"
readonly GPU_MEMORY_GIB="64"
readonly MINIMUM_FREE_KIB=$((55 * 1024 * 1024))

readonly -a COMPLETED_CAMPAIGN_MODELS=(
  "qwen3.6:27b-q4_K_M"
  "qwen3.6:35b-a3b-q4_K_M"
  "muse-glimmer:30b"
  "nemotron-3.5-lightning:30b-a3b-q4_K_M"
  "nemotron-3.5-lightning:30b-a3b-q8_0"
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

readonly PID_FILE="$EVIDENCE_ROOT/cuda-qwen38-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

while [[ ! -f "$PREREQUISITE" ]]; do
  sleep 30
done

for model in "${COMPLETED_CAMPAIGN_MODELS[@]}"; do
  "$OLLAMA_BIN" rm "$model" >/dev/null 2>&1 || true
done

available_kib=$(df -Pk "$BASE" | awk 'NR == 2 {print $4}')
[[ "$available_kib" =~ ^[0-9]+$ ]] || {
  printf 'Refused: free storage could not be measured.\n' >&2
  exit 1
}
(( available_kib >= MINIMUM_FREE_KIB )) || {
  printf 'Refused: less than 55 GiB is free after exact campaign cleanup.\n' >&2
  exit 1
}

printf 'PULL %s\n' "$MODEL_ID"
"$OLLAMA_BIN" pull "$MODEL_NAME"

actual_manifest=$(python3 - "$ORIGIN" "$MODEL_NAME" <<'PY'
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
)
if [[ "$actual_manifest" != "$EXPECTED_MANIFEST" ]]; then
  printf '{"schemaVersion":1,"kind":"alpha2-cuda-campaign-status","modelId":"%s","outcome":"failed","errorCode":"manifest-mismatch","automaticPromotionAllowed":false}\n' \
    "$MODEL_ID" >"$EVIDENCE_ROOT/cuda-$MODEL_ID-status.json"
  exit 1
fi

prefix="$EVIDENCE_ROOT/cuda-$MODEL_ID"
printf 'TASK_GATE %s\n' "$MODEL_ID"
for capability in general.chat content.write content.summarize; do
  python3 scripts/alpha2-model-task-qualification.py \
    --origin "$ORIGIN" \
    --model-id "$MODEL_ID" \
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
  printf 'TASK_GATE_FAILED %s\n' "$MODEL_ID"
  "$OLLAMA_BIN" rm "$MODEL_NAME" >/dev/null 2>&1 || true
  touch "$EVIDENCE_ROOT/cuda-qwen38-followup.complete"
  exit 0
fi

printf 'SOAK %s\n' "$MODEL_ID"
if python3 scripts/alpha2-linux-soak.py \
  --origin "$ORIGIN" \
  --model-id "$MODEL_ID" \
  --operating-system-id "$OPERATING_SYSTEM_ID" \
  --platform-family linux \
  --backend cuda \
  --system-memory-gib "$SYSTEM_MEMORY_GIB" \
  --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
  --duration-minutes 30 \
  --interval-seconds 120 \
  --qualification-inventory \
  --qualification-profile-id "$PROFILE" \
  >"$prefix-soak.json" 2>"$prefix-soak.stderr"; then
  rm -f "$prefix-soak.stderr"
  printf 'PASSED %s\n' "$MODEL_ID"
else
  printf '{"schemaVersion":1,"kind":"alpha2-cuda-campaign-status","modelId":"%s","outcome":"failed","errorCode":"bounded-soak-failed","automaticPromotionAllowed":false}\n' \
    "$MODEL_ID" >"$prefix-soak.json"
  printf 'SOAK_FAILED %s\n' "$MODEL_ID"
fi

for capability in vision tools thinking failure-recovery; do
  printf 'EXTENDED %s %s\n' "$MODEL_ID" "$capability"
  python3 scripts/alpha2-model-extended-qualification.py \
    --origin "$ORIGIN" \
    --model-id "$MODEL_ID" \
    --capability "$capability" \
    --profile-id "$PROFILE" \
    --operating-system-id "$OPERATING_SYSTEM_ID" \
    --platform-family linux \
    --system-memory-gib "$SYSTEM_MEMORY_GIB" \
    --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
    >"$prefix-extended-$capability.json" || true
done

"$OLLAMA_BIN" rm "$MODEL_NAME" >/dev/null 2>&1 || true
touch "$EVIDENCE_ROOT/cuda-qwen38-followup.complete"
printf 'CAMPAIGN_COMPLETE\n'
