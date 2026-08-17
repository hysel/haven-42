#!/usr/bin/env bash
set -Eeuo pipefail

# Qualify the exact compact MiniCPM vision candidate after the RX release
# follow-up. The fixture is synthetic and generated in memory by the checker.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly OLLAMA_BIN="${OLLAMA_BIN:-$BASE/runtime/0.32.13/bin/ollama}"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PREREQUISITE="$EVIDENCE_ROOT/rx5700xt-release-followup.complete"
readonly MODEL_ID="minicpm-v46-1b-q4"
readonly MODEL_NAME="minicpm-v4.6:1b"
readonly EXPECTED_MANIFEST="e95583acac773b45d95469c069db44808c87295f924183f4c942d52616b2d132"
readonly PROFILE="vulkan-8gib-system-16gib"
readonly OPERATING_SYSTEM_ID="ubuntu-26.04-rx5700xt"
readonly SYSTEM_MEMORY_GIB="121"
readonly GPU_MEMORY_GIB="8"

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || exit 1
[[ -x "$OLLAMA_BIN" && ! -L "$OLLAMA_BIN" ]] || exit 1
mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT"
readonly PID_FILE="$EVIDENCE_ROOT/rx5700xt-minicpm-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT
while [[ ! -f "$PREREQUISITE" ]]; do sleep 30; done

"$OLLAMA_BIN" pull "$MODEL_NAME"
actual_manifest=$(python3 - "$ORIGIN" "$MODEL_NAME" <<'PY'
import json
import sys
import urllib.request
origin, wanted = sys.argv[1:]
with urllib.request.urlopen(origin + "/api/tags", timeout=10) as response:
    payload = json.load(response)
matches = [item for item in payload.get("models", []) if isinstance(item, dict) and item.get("name") == wanted]
if len(matches) != 1:
    raise SystemExit(1)
print(matches[0].get("digest", ""))
PY
)
[[ "$actual_manifest" == "$EXPECTED_MANIFEST" ]] || exit 1

prefix="$EVIDENCE_ROOT/rx5700xt-$MODEL_ID"
python3 scripts/alpha2-model-task-qualification.py \
  --origin "$ORIGIN" --model-id "$MODEL_ID" --capability general.chat \
  --profile-id "$PROFILE" --operating-system-id "$OPERATING_SYSTEM_ID" \
  --platform-family linux --system-memory-gib "$SYSTEM_MEMORY_GIB" \
  --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
  >"$prefix-task-general.chat.json" || true
if ! python3 - "$prefix-task-general.chat.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
raise SystemExit(0 if payload.get("outcome") == "passed" else 1)
PY
then
  printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"task-gate-failed","automaticPromotionAllowed":false}\n' "$MODEL_ID" >"$prefix-status.json"
  "$OLLAMA_BIN" rm "$MODEL_NAME" >/dev/null 2>&1 || true
  touch "$EVIDENCE_ROOT/rx5700xt-minicpm-followup.complete"
  exit 0
fi
if python3 scripts/alpha2-linux-soak.py \
  --origin "$ORIGIN" --model-id "$MODEL_ID" \
  --operating-system-id "$OPERATING_SYSTEM_ID" --platform-family linux \
  --backend vulkan --system-memory-gib "$SYSTEM_MEMORY_GIB" \
  --usable-gpu-memory-gib "$GPU_MEMORY_GIB" --duration-minutes 30 \
  --interval-seconds 120 --qualification-inventory \
  --qualification-profile-id "$PROFILE" \
  >"$prefix-soak.json" 2>"$prefix-soak.stderr"; then
  rm -f "$prefix-soak.stderr"
else
  printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"bounded-soak-failed","automaticPromotionAllowed":false}\n' "$MODEL_ID" >"$prefix-status.json"
  "$OLLAMA_BIN" rm "$MODEL_NAME" >/dev/null 2>&1 || true
  touch "$EVIDENCE_ROOT/rx5700xt-minicpm-followup.complete"
  exit 0
fi
for capability in vision failure-recovery; do
  python3 scripts/alpha2-model-extended-qualification.py \
    --origin "$ORIGIN" --model-id "$MODEL_ID" --capability "$capability" \
    --profile-id "$PROFILE" --operating-system-id "$OPERATING_SYSTEM_ID" \
    --platform-family linux --system-memory-gib "$SYSTEM_MEMORY_GIB" \
    --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
    >"$prefix-extended-$capability.json" || true
done
"$OLLAMA_BIN" rm "$MODEL_NAME" >/dev/null 2>&1 || true
touch "$EVIDENCE_ROOT/rx5700xt-minicpm-followup.complete"
printf 'CAMPAIGN_COMPLETE\n'
