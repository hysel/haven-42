#!/usr/bin/env bash
set -Eeuo pipefail

# Preserve the failed base chat gate, but still characterize the model's
# advertised vision and recovery capabilities after the power retry is done.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly ROOT="$BASE/certification"
readonly EVIDENCE="$ROOT/evidence"
readonly OLLAMA="$BASE/runtime/0.32.13/bin/ollama"
readonly ORIGIN='http://127.0.0.1:11434'
readonly PROFILE='vulkan-8gib-system-16gib'
readonly MODEL_ID='minicpm-v46-1b-q4'
readonly MODEL='minicpm-v4.6:1b'
readonly EXPECTED='e95583acac773b45d95469c069db44808c87295f924183f4c942d52616b2d132'
readonly PREFIX="$EVIDENCE/rx5700xt-$MODEL_ID"

cd "$ROOT"
while [[ ! -f "$EVIDENCE/rx5700xt-power-retry.complete" ]]; do sleep 10; done
[[ -f "$PREFIX-task-general.chat.json" ]] || { echo 'Refused: base MiniCPM result missing' >&2; exit 1; }
for capability in vision failure-recovery; do
  [[ ! -e "$PREFIX-extended-$capability.json" ]] || { echo 'Refused: MiniCPM extended output exists' >&2; exit 1; }
done
[[ ! -e "$PREFIX-full-residency.json" ]] || { echo 'Refused: MiniCPM residency output exists' >&2; exit 1; }

"$OLLAMA" pull "$MODEL"
observed=$(python3 - "$MODEL" <<'PY'
import json,sys,urllib.request
with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=10) as response:
    payload=json.load(response)
matches=[item for item in payload.get('models',[]) if isinstance(item,dict) and item.get('name')==sys.argv[1]]
if len(matches)!=1: raise SystemExit(1)
print(matches[0].get('digest',''))
PY
)
[[ "$observed" == "$EXPECTED" ]] || { echo 'Refused: MiniCPM manifest mismatch' >&2; exit 1; }

python3 scripts/alpha2-ollama-full-residency-monitor.py \
  --inventory config/alpha-2-model-version-inventory.json \
  --model-id "$MODEL_ID" --output-dir "$EVIDENCE" --output-prefix rx5700xt- \
  --operating-system-id ubuntu-26.04-rx5700xt --backend vulkan \
  --hardware-profile-id amd-radeon-rx5700xt-8g --timeout-seconds 1800 &
monitor_pid=$!
for capability in vision failure-recovery; do
  python3 scripts/alpha2-model-extended-qualification.py \
    --origin "$ORIGIN" --model-id "$MODEL_ID" --capability "$capability" \
    --profile-id "$PROFILE" \
    --operating-system-id ubuntu-26.04-rx5700xt --platform-family linux \
    --system-memory-gib 121 --usable-gpu-memory-gib 8 \
    >"$PREFIX-extended-$capability.json" || true
done
wait "$monitor_pid"
"$OLLAMA" rm "$MODEL"
touch "$EVIDENCE/rx5700xt-minicpm-extended-retry.complete"
