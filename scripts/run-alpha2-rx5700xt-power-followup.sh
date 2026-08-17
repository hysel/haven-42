#!/usr/bin/env bash
set -Eeuo pipefail

# Run the reviewed RX 5700 XT power profile only after all currently scheduled
# model qualification cells have finished. It records a pass or fail result,
# verifies unload in the profiler, and does not change support policy.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly PREREQUISITE="$EVIDENCE_ROOT/rx5700xt-minicpm-followup.complete"
readonly OUTPUT="$EVIDENCE_ROOT/rx5700xt-llama32-3b-q4-power.json"

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || exit 1
mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT"
readonly PID_FILE="$EVIDENCE_ROOT/rx5700xt-power-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

while [[ ! -f "$PREREQUISITE" ]]; do sleep 30; done

result=0
python3 scripts/alpha2-linux-amd-power-profile.py \
  --origin http://127.0.0.1:11434 \
  --model-id llama32-3b-q4 \
  >"$OUTPUT.new" || result=$?
mv "$OUTPUT.new" "$OUTPUT"
touch "$EVIDENCE_ROOT/rx5700xt-power-followup.complete"
if (( result == 0 )); then
  printf 'POWER_PROFILE_COMPLETE\n'
else
  printf 'POWER_PROFILE_FAILED_WITH_EVIDENCE\n'
fi
exit "$result"
