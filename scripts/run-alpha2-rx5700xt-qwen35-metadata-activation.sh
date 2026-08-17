#!/usr/bin/env bash
set -Eeuo pipefail

# Activate the reviewed fourth metadata generation only after every earlier RX
# result and the power record have closed. The Qwen follow-up waits for the
# ready marker, so it cannot observe a half-activated pair.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly PREREQUISITE="$EVIDENCE_ROOT/rx5700xt-power-followup.complete"
readonly INVENTORY="config/alpha-2-model-version-inventory.json"
readonly MATRIX="config/alpha-2-model-qualification-matrix.json"
readonly STAGED_INVENTORY="$INVENTORY.qwen35-new"
readonly STAGED_MATRIX="$MATRIX.qwen35-new"
readonly OLD_INVENTORY_SHA="61f0c670f49304a20c7701c3c53fb503d90f1c0abfaac84307a57c710cdb5ac9"
readonly OLD_MATRIX_SHA="6d45244100771b03d91fc4c9307d296ea2f18ef52441083fe8b8fba3dc6403bc"
readonly NEW_INVENTORY_SHA="76e01a821f1610bfed91e0fc6e8758b00aab4c6f5ea5715c5c572eec88309137"
readonly NEW_MATRIX_SHA="ce61deccfc375383d48c7659e105255f7841aad1783f6960fa798354e649322d"

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || exit 1
cd "$CERTIFICATION_ROOT"
for path in "$INVENTORY" "$MATRIX" "$STAGED_INVENTORY" "$STAGED_MATRIX"; do
  [[ -f "$path" && ! -L "$path" ]] || {
    printf 'Refused: reviewed metadata file is unavailable: %s\n' "$path" >&2
    exit 1
  }
done
mkdir -p "$EVIDENCE_ROOT"
readonly PID_FILE="$EVIDENCE_ROOT/rx5700xt-qwen35-metadata-activation.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

while [[ ! -f "$PREREQUISITE" ]]; do sleep 30; done

readarray -t hashes < <(python3 - "$INVENTORY" "$MATRIX" "$STAGED_INVENTORY" "$STAGED_MATRIX" <<'PY'
import hashlib
import json
import sys

for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as handle:
        value = json.load(handle)
    print(hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest())
PY
)
[[ "${#hashes[@]}" -eq 4 ]] || exit 1
[[ "${hashes[0]}" == "$OLD_INVENTORY_SHA" && "${hashes[1]}" == "$OLD_MATRIX_SHA" ]] || {
  printf 'Refused: current metadata generation is unexpected.\n' >&2
  exit 1
}
[[ "${hashes[2]}" == "$NEW_INVENTORY_SHA" && "${hashes[3]}" == "$NEW_MATRIX_SHA" ]] || {
  printf 'Refused: staged metadata generation is not exact.\n' >&2
  exit 1
}

mv "$STAGED_INVENTORY" "$INVENTORY"
mv "$STAGED_MATRIX" "$MATRIX"
touch "$EVIDENCE_ROOT/rx5700xt-qwen35-metadata.ready"
touch "$EVIDENCE_ROOT/rx5700xt-qwen35-metadata-activation.complete"
printf 'METADATA_ACTIVATED\n'
