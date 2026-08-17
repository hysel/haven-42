#!/usr/bin/env bash
set -Eeuo pipefail

# Sequentially qualify exact Granite and Nemotron release candidates after the
# coding follow-up. Each artifact is pulled, manifest-verified, tested, and
# removed before the next candidate to keep storage bounded.

readonly BASE="${1:-$HOME/Haven42-Data}"
readonly CERTIFICATION_ROOT="$BASE/certification"
readonly EVIDENCE_ROOT="$CERTIFICATION_ROOT/evidence"
readonly OLLAMA_BIN="${OLLAMA_BIN:-/usr/local/bin/ollama}"
readonly ORIGIN="http://127.0.0.1:11434"
readonly PREREQUISITE="$EVIDENCE_ROOT/cuda-north-mini-followup.complete"
readonly OPERATING_SYSTEM_ID="ubuntu-dual-v100"
readonly SYSTEM_MEMORY_GIB="128"
readonly GPU_MEMORY_GIB="64"
readonly MINIMUM_FREE_KIB=$((55 * 1024 * 1024))
readonly -a MODEL_CELLS=(
  "granite41-30b-q4|granite4.1:30b|3f3e5df8a021439fd6f867a0e526bdc303cac79c811201cb6bac193298cb9fcd|cuda-32gib-system-64gib|coding,tools,failure-recovery"
  "nemotron3-nano-omni-33b-q4|nemotron3:33b|f6d8b7ff496ccc53429cc480ad53971d522b443ee4a5aa58a6da49e57acf42cf|cuda-64gib-system-96gib|vision,tools,thinking,failure-recovery"
)

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || exit 1
[[ -x "$OLLAMA_BIN" && ! -L "$OLLAMA_BIN" ]] || exit 1
mkdir -p "$EVIDENCE_ROOT"
cd "$CERTIFICATION_ROOT"
readonly PID_FILE="$EVIDENCE_ROOT/cuda-multimodal-followup.pid"
printf '%s\n' "$$" >"$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

while [[ ! -f "$PREREQUISITE" ]]; do sleep 30; done

for cell in "${MODEL_CELLS[@]}"; do
  IFS='|' read -r model_id model_name expected_manifest profile extended_csv <<<"$cell"
  prefix="$EVIDENCE_ROOT/cuda-$model_id"
  available_kib=$(df -Pk "$BASE" | awk 'NR == 2 {print $4}')
  [[ "$available_kib" =~ ^[0-9]+$ ]] || exit 1
  (( available_kib >= MINIMUM_FREE_KIB )) || exit 1

  printf 'PULL %s\n' "$model_id"
  "$OLLAMA_BIN" pull "$model_name"
  actual_manifest=$(python3 - "$ORIGIN" "$model_name" <<'PY'
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
  if [[ "$actual_manifest" != "$expected_manifest" ]]; then
    printf '{"schemaVersion":1,"kind":"alpha2-cuda-campaign-status","modelId":"%s","outcome":"failed","errorCode":"manifest-mismatch","automaticPromotionAllowed":false}\n' "$model_id" >"$prefix-status.json"
    exit 1
  fi

  for capability in general.chat content.write content.summarize; do
    python3 scripts/alpha2-model-task-qualification.py \
      --origin "$ORIGIN" --model-id "$model_id" --capability "$capability" \
      --profile-id "$profile" --operating-system-id "$OPERATING_SYSTEM_ID" \
      --platform-family linux --system-memory-gib "$SYSTEM_MEMORY_GIB" \
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
with open(paths[0], encoding="utf-8") as handle:
    values = [json.load(handle)]
for path in paths[1:]:
    with open(path, encoding="utf-8") as handle:
        values.append(json.load(handle))
raise SystemExit(0 if all(value.get("outcome") == "passed" for value in values) else 1)
PY
  then
    printf '{"schemaVersion":1,"kind":"alpha2-cuda-campaign-status","modelId":"%s","outcome":"failed","errorCode":"task-gate-failed","automaticPromotionAllowed":false}\n' "$model_id" >"$prefix-status.json"
    "$OLLAMA_BIN" rm "$model_name" >/dev/null 2>&1 || true
    continue
  fi

  if python3 scripts/alpha2-linux-soak.py \
    --origin "$ORIGIN" --model-id "$model_id" \
    --operating-system-id "$OPERATING_SYSTEM_ID" --platform-family linux \
    --backend cuda --system-memory-gib "$SYSTEM_MEMORY_GIB" \
    --usable-gpu-memory-gib "$GPU_MEMORY_GIB" --duration-minutes 30 \
    --interval-seconds 120 --qualification-inventory \
    --qualification-profile-id "$profile" \
    >"$prefix-soak.json" 2>"$prefix-soak.stderr"; then
    rm -f "$prefix-soak.stderr"
  else
    printf '{"schemaVersion":1,"kind":"alpha2-cuda-campaign-status","modelId":"%s","outcome":"failed","errorCode":"bounded-soak-failed","automaticPromotionAllowed":false}\n' "$model_id" >"$prefix-status.json"
    "$OLLAMA_BIN" rm "$model_name" >/dev/null 2>&1 || true
    continue
  fi

  IFS=',' read -r -a extended_capabilities <<<"$extended_csv"
  for capability in "${extended_capabilities[@]}"; do
    python3 scripts/alpha2-model-extended-qualification.py \
      --origin "$ORIGIN" --model-id "$model_id" --capability "$capability" \
      --profile-id "$profile" --operating-system-id "$OPERATING_SYSTEM_ID" \
      --platform-family linux --system-memory-gib "$SYSTEM_MEMORY_GIB" \
      --usable-gpu-memory-gib "$GPU_MEMORY_GIB" \
      >"$prefix-extended-$capability.json" || true
  done
  "$OLLAMA_BIN" rm "$model_name" >/dev/null 2>&1 || true
done

touch "$EVIDENCE_ROOT/cuda-multimodal-followup.complete"
printf 'CAMPAIGN_COMPLETE\n'
