#!/usr/bin/env bash
set -Eeuo pipefail

# Re-run the Qwen 3.6 35B task gate against the same immutable qualification
# metadata generation as its completed soak, then hand control to the already
# reviewed Qwen 3.8 follow-up. The earlier sanitized task files are retained in
# a metadata-history directory; no model is downloaded or removed here.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly HISTORY_ROOT="$EVIDENCE_ROOT/metadata-history/qwen36-35b-release-expansion"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PREREQUISITE="$EVIDENCE_ROOT/cuda-new-model-campaign.complete"
readonly MODEL_ID="qwen36-35b-a3b-q4"
readonly MODEL_NAME="qwen3.6:35b-a3b-q4_K_M"
readonly EXPECTED_MANIFEST="07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522"
readonly EXPECTED_INVENTORY_SHA="61f0c670f49304a20c7701c3c53fb503d90f1c0abfaac84307a57c710cdb5ac9"
readonly PROFILE="cuda-32gib-system-64gib"
readonly OPERATING_SYSTEM_ID="ubuntu-dual-v100"
readonly SYSTEM_MEMORY_GIB="128"
readonly GPU_MEMORY_GIB="64"
readonly NEXT_SCRIPT="$CERTIFICATION_ROOT/scripts/run-alpha2-cuda-qwen38-followup.sh"

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || {
  printf 'Refused: BASE must be an existing absolute non-link directory.\n' >&2
  exit 1
}
[[ -x "$NEXT_SCRIPT" && ! -L "$NEXT_SCRIPT" ]] || {
  printf 'Refused: reviewed Qwen 3.8 follow-up is unavailable.\n' >&2
  exit 1
}
mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT"

readonly PID_FILE="$EVIDENCE_ROOT/cuda-metadata-rebind-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT
while [[ ! -f "$PREREQUISITE" ]]; do sleep 30; done

actual_inventory_sha=$(python3 - <<'PY'
import hashlib
import json
from pathlib import Path

value = json.loads(Path("config/alpha-2-model-version-inventory.json").read_text(encoding="utf-8"))
print(hashlib.sha256(json.dumps(
    value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
).encode("utf-8")).hexdigest())
PY
)
[[ "$actual_inventory_sha" == "$EXPECTED_INVENTORY_SHA" ]] || {
  printf 'Refused: deployed qualification inventory is not the expected generation.\n' >&2
  exit 1
}

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
[[ "$actual_manifest" == "$EXPECTED_MANIFEST" ]] || {
  printf 'Refused: Qwen 3.6 35B manifest is absent or changed.\n' >&2
  exit 1
}

prefix="$EVIDENCE_ROOT/cuda-$MODEL_ID"
temporary_root=$(mktemp -d -- "$EVIDENCE_ROOT/.cuda-$MODEL_ID-current.XXXXXX")
cleanup() {
  rm -f "$PID_FILE"
  if [[ -d "$temporary_root" && ! -L "$temporary_root" ]]; then
    rm -f -- \
      "$temporary_root/general.chat.json" \
      "$temporary_root/content.write.json" \
      "$temporary_root/content.summarize.json"
    rmdir -- "$temporary_root" 2>/dev/null || true
  fi
}
trap cleanup EXIT

for capability in general.chat content.write content.summarize; do
  python3 scripts/alpha2-model-task-qualification.py \
    --origin "$ORIGIN" --model-id "$MODEL_ID" --capability "$capability" \
    --profile-id "$PROFILE" --operating-system-id "$OPERATING_SYSTEM_ID" \
    --platform-family linux --system-memory-gib "$SYSTEM_MEMORY_GIB" \
    --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
    >"$temporary_root/$capability.json" || true
done

python3 - "$temporary_root" "$EXPECTED_INVENTORY_SHA" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
expected_sha = sys.argv[2]
paths = sorted(root.glob("*.json"))
if len(paths) != 3:
    raise SystemExit("Refused: current task evidence set is incomplete.")
for path in paths:
    value = json.loads(path.read_text(encoding="utf-8"))
    evidence = value.get("evidence")
    if not isinstance(evidence, dict):
        raise SystemExit("Refused: current task evidence is malformed.")
    if evidence.get("qualificationInventoryCanonicalSha256") != expected_sha:
        raise SystemExit("Refused: current task evidence metadata is inconsistent.")
    if value.get("containsPrivateMachineIdentity") is not False:
        raise SystemExit("Refused: current task evidence privacy flag is invalid.")
    if value.get("containsRawPromptsOrResponses") is not False:
        raise SystemExit("Refused: current task evidence content flag is invalid.")
PY

mkdir -p "$HISTORY_ROOT"
for capability in general.chat content.write content.summarize; do
  destination="$prefix-task-$capability.json"
  if [[ -f "$destination" && ! -L "$destination" ]]; then
    cp --preserve=mode,timestamps -- "$destination" "$HISTORY_ROOT/task-$capability.json"
  fi
  mv -- "$temporary_root/$capability.json" "$destination"
done
rmdir "$temporary_root"
touch "$EVIDENCE_ROOT/cuda-metadata-rebind-followup.complete"
trap 'rm -f "$PID_FILE"' EXIT
printf 'METADATA_REBIND_COMPLETE\n'
exec bash "$NEXT_SCRIPT" "$BASE"
