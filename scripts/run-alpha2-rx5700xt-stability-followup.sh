#!/usr/bin/env bash
set -Eeuo pipefail

# Close the RX 5700 XT host-stability and oversized-refusal cells only after
# every approved model and power cell has finished. This runner downloads
# nothing and records no raw kernel log, prompt, response, or machine identity.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly PREREQUISITE="$EVIDENCE_ROOT/rx5700xt-qwen35-followup.complete"
readonly WAIT_SECONDS=30
readonly -a REFUSAL_MODELS=(qwen35-9b-q4 gemma3-12b-q4 gemma4-12b-qat)

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || {
  printf 'Refused: BASE must be an existing absolute non-link directory.\n' >&2
  exit 1
}
mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT"
for script in scripts/alpha2-linux-host-stability.py scripts/alpha2-hardware-model-admission.py; do
  [[ -f "$script" && ! -L "$script" ]] || {
    printf 'Refused: required reviewed script is unavailable: %s\n' "$script" >&2
    exit 1
  }
done

readonly PID_FILE="$EVIDENCE_ROOT/rx5700xt-stability-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT
while [[ ! -f "$PREREQUISITE" ]]; do sleep "$WAIT_SECONDS"; done

python3 scripts/alpha2-linux-host-stability.py \
  --duration-seconds 600 --workers 4 \
  >"$EVIDENCE_ROOT/rx5700xt-host-stability.json"

for model_id in "${REFUSAL_MODELS[@]}"; do
  python3 scripts/alpha2-hardware-model-admission.py \
    --model-id "$model_id" \
    >"$EVIDENCE_ROOT/rx5700xt-$model_id-admission.json"
done

python3 - "$EVIDENCE_ROOT" "${REFUSAL_MODELS[@]}" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
stability = json.loads((root / "rx5700xt-host-stability.json").read_text(encoding="utf-8"))
if stability.get("outcome") != "passed":
    raise SystemExit(1)
for model_id in sys.argv[2:]:
    record = json.loads((root / f"rx5700xt-{model_id}-admission.json").read_text(encoding="utf-8"))
    if record.get("outcome") != "passed" or record.get("decision") != "refused-before-download":
        raise SystemExit(1)
PY

touch "$EVIDENCE_ROOT/rx5700xt-stability-followup.complete"
printf 'CAMPAIGN_COMPLETE\n'
