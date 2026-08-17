#!/usr/bin/env bash
set -Eeuo pipefail

# Run the approved North Mini Code candidate after the exact Qwen 3.8 cell.
# The immutable registry manifest is verified before bounded qualification and
# the exact test artifact is removed after evidence is closed.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly OLLAMA_BIN="${OLLAMA_BIN:-/usr/local/bin/ollama}"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PREREQUISITE="$EVIDENCE_ROOT/cuda-qwen38-followup.complete"
readonly MODEL_ID="north-mini-code-10-30b-a3b-q4"
readonly MODEL_NAME="north-mini-code-1.0:q4_K_M"
readonly EXPECTED_MANIFEST="d8b269ad5c7c7144ce104b83ce93bc3efb85e0f74e01be6be5f5d6f7ca90b60f"
readonly PROFILE="cuda-32gib-system-64gib"
readonly OPERATING_SYSTEM_ID="ubuntu-dual-v100"
readonly SYSTEM_MEMORY_GIB="128"
readonly GPU_MEMORY_GIB="64"
readonly MINIMUM_FREE_KIB=$((55 * 1024 * 1024))

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
readonly PID_FILE="$EVIDENCE_ROOT/cuda-north-mini-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

while [[ ! -f "$PREREQUISITE" ]]; do
  sleep 30
done

available_kib=$(df -Pk "$BASE" | awk 'NR == 2 {print $4}')
[[ "$available_kib" =~ ^[0-9]+$ ]] || exit 1
(( available_kib >= MINIMUM_FREE_KIB )) || {
  printf 'Refused: less than 55 GiB is free.\n' >&2
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
  touch "$EVIDENCE_ROOT/cuda-north-mini-followup.complete"
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

for capability in coding tools long-context failure-recovery; do
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
touch "$EVIDENCE_ROOT/cuda-north-mini-followup.complete"
printf 'CAMPAIGN_COMPLETE\n'
