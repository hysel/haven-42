#!/usr/bin/env bash
set -Eeuo pipefail

# Qualify the three exact Qwen 3.5 artifacts in the RX 5700 XT model ladder.
# This follow-up cannot start until the earlier campaign and power capture have
# closed and the separately deployed fourth metadata generation is verified.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly OLLAMA_BIN="${OLLAMA_BIN:-$BASE/runtime/0.32.13/bin/ollama}"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PREREQUISITE="$EVIDENCE_ROOT/rx5700xt-power-followup.complete"
readonly METADATA_READY="$EVIDENCE_ROOT/rx5700xt-qwen35-metadata.ready"
readonly EXPECTED_INVENTORY_SHA="76e01a821f1610bfed91e0fc6e8758b00aab4c6f5ea5715c5c572eec88309137"
readonly PROFILE="vulkan-8gib-system-16gib"
readonly OPERATING_SYSTEM_ID="ubuntu-26.04-rx5700xt"
readonly SYSTEM_MEMORY_GIB="121"
readonly GPU_MEMORY_GIB="8"
readonly MINIMUM_FREE_KIB=$((16 * 1024 * 1024))

readonly -a MODEL_CELLS=(
  "qwen35-08b-q8|qwen3.5:0.8b|f3817196d142eaf72ce79dfebe53dcb20bd21da87ce13e138a8f8e10a866b3a4"
  "qwen35-2b-q8|qwen3.5:2b|324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df"
  "qwen35-4b-q4|qwen3.5:4b|2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd"
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
readonly PID_FILE="$EVIDENCE_ROOT/rx5700xt-qwen35-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

while [[ ! -f "$PREREQUISITE" || ! -f "$METADATA_READY" ]]; do sleep 30; done

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
  printf 'Refused: deployed Qwen 3.5 qualification metadata is not exact.\n' >&2
  exit 1
}

model_manifest() {
  python3 - "$ORIGIN" "$1" <<'PY'
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

task_gate_passed() {
  python3 - "$1" "$EXPECTED_INVENTORY_SHA" <<'PY'
import glob
import json
import sys

paths = glob.glob(sys.argv[1] + "-task-*.json")
expected_sha = sys.argv[2]
if len(paths) != 3:
    raise SystemExit(1)
values = [json.load(open(path, encoding="utf-8")) for path in paths]
if any(value.get("evidence", {}).get("qualificationInventoryCanonicalSha256") != expected_sha for value in values):
    raise SystemExit(1)
raise SystemExit(0 if all(value.get("outcome") == "passed" for value in values) else 1)
PY
}

for cell in "${MODEL_CELLS[@]}"; do
  IFS='|' read -r model_id model_name expected_manifest <<<"$cell"
  prefix="$EVIDENCE_ROOT/rx5700xt-$model_id"
  available_kib=$(df -Pk "$BASE" | awk 'NR == 2 {print $4}')
  if [[ ! "$available_kib" =~ ^[0-9]+$ ]] || (( available_kib < MINIMUM_FREE_KIB )); then
    printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"storage-admission-failed","automaticPromotionAllowed":false}\n' "$model_id" >"$prefix-status.json"
    continue
  fi
  if ! "$OLLAMA_BIN" pull "$model_name"; then
    printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"model-download-failed","automaticPromotionAllowed":false}\n' "$model_id" >"$prefix-status.json"
    continue
  fi
  actual_manifest=$(model_manifest "$model_name" 2>/dev/null || true)
  if [[ "$actual_manifest" != "$expected_manifest" ]]; then
    printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"manifest-missing-or-mismatch","automaticPromotionAllowed":false}\n' "$model_id" >"$prefix-status.json"
    "$OLLAMA_BIN" rm "$model_name" >/dev/null 2>&1 || true
    continue
  fi

  for capability in general.chat content.write content.summarize; do
    python3 scripts/alpha2-model-task-qualification.py \
      --origin "$ORIGIN" --model-id "$model_id" --capability "$capability" \
      --profile-id "$PROFILE" --operating-system-id "$OPERATING_SYSTEM_ID" \
      --platform-family linux --system-memory-gib "$SYSTEM_MEMORY_GIB" \
      --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
      >"$prefix-task-$capability.json" || true
  done
  if ! task_gate_passed "$prefix"; then
    "$OLLAMA_BIN" rm "$model_name" >/dev/null 2>&1 || true
    continue
  fi

  if python3 scripts/alpha2-linux-soak.py \
    --origin "$ORIGIN" --model-id "$model_id" \
    --operating-system-id "$OPERATING_SYSTEM_ID" --platform-family linux \
    --backend vulkan --system-memory-gib "$SYSTEM_MEMORY_GIB" \
    --usable-gpu-memory-gib "$GPU_MEMORY_GIB" --duration-minutes 30 \
    --interval-seconds 120 --qualification-inventory \
    --qualification-profile-id "$PROFILE" \
    >"$prefix-soak.json" 2>"$prefix-soak.stderr"; then
    rm -f "$prefix-soak.stderr"
  else
    printf '{"schemaVersion":1,"kind":"alpha2-vulkan-campaign-status","modelId":"%s","outcome":"failed","errorCode":"bounded-soak-failed","automaticPromotionAllowed":false}\n' "$model_id" >"$prefix-status.json"
  fi
  "$OLLAMA_BIN" rm "$model_name" >/dev/null 2>&1 || true
done

touch "$EVIDENCE_ROOT/rx5700xt-qwen35-followup.complete"
printf 'CAMPAIGN_COMPLETE\n'
