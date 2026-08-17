#!/usr/bin/env bash
set -Eeuo pipefail

# Retry the reviewed RX 5700 XT board-power profile only after every Qwen and
# host-stability cell is complete. The first failed record remains immutable.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly ROOT="$BASE/certification"
readonly EVIDENCE="$ROOT/evidence"
readonly OLLAMA="$BASE/runtime/0.32.13/bin/ollama"
readonly MODEL='llama3.2:3b-instruct-q4_K_M'
readonly EXPECTED='a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72'
readonly OUTPUT="$EVIDENCE/rx5700xt-llama32-3b-q4-power-retry.json"

cd "$ROOT"
while [[ ! -f "$EVIDENCE/rx5700xt-stability-followup.complete" ]]; do sleep 10; done
[[ -f "$EVIDENCE/rx5700xt-llama32-3b-q4-power.json" ]] || { echo 'Refused: original power record missing' >&2; exit 1; }
[[ ! -e "$OUTPUT" && ! -e "$OUTPUT.new" ]] || { echo 'Refused: retry output already exists' >&2; exit 1; }

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
[[ "$observed" == "$EXPECTED" ]] || { echo 'Refused: power model manifest mismatch' >&2; exit 1; }

result=0
python3 scripts/alpha2-linux-amd-power-profile.py --model-id llama32-3b-q4 >"$OUTPUT.new" || result=$?
mv "$OUTPUT.new" "$OUTPUT"
(( result == 0 )) || exit "$result"
python3 - "$OUTPUT" <<'PY'
import json,sys
record=json.load(open(sys.argv[1],encoding='utf-8'))
assert record.get('outcome') == 'passed'
assert record.get('powerScope') == 'gpu-board-sysfs-power1-average'
assert record.get('containsPrivateMachineIdentity') is False
assert record.get('containsRawPromptsOrResponses') is False
PY
touch "$EVIDENCE/rx5700xt-power-retry.complete"
