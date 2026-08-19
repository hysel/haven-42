#!/usr/bin/env bash
set -u

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
runtime="$HOME/Haven42-Data/qualification/ollama/0.32.14-linux-x64/runtime"
model_store="$HOME/Haven42-Data/qualification/models/ollama-0.32.14-linux-gtx1650-super"
origin="http://127.0.0.1:11434"
events="$root/telemetry/events.tsv"
telemetry="$root/telemetry/nvidia-smi.csv"
core="$root/results/core"
soak="$root/results/soak"

model_ids=(
  qwen35-08b-q8 qwen35-2b-q8 gemma3-1b-q4 granite41-3b-q4
  phi4-mini-38b-q4 llama32-3b-q4 ministral3-3b-q4 minicpm-v46-1b-q4
)
capabilities=(general.chat content.write content.summarize)
server_pid=""
logger_pid=""

event() {
  printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" >> "$events"
}

cleanup() {
  local result=$?
  if [[ -n "$logger_pid" ]]; then
    kill "$logger_pid" 2>/dev/null || true
  fi
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
  fi
  printf '%s\n' "$result" > "$root/campaign.exit"
}
trap cleanup EXIT INT TERM

model_name() {
  python3 - "$root/config/alpha-2-model-version-inventory.json" "$1" <<'PY'
import json
import sys

inventory = json.load(open(sys.argv[1], encoding="utf-8"))
matches = []
for family in inventory["families"]:
    for version in family["versions"]:
        for candidate in version.get("candidates", []):
            if candidate.get("id") == sys.argv[2]:
                matches.append(candidate["model"])
if len(matches) != 1:
    raise SystemExit("candidate-name-resolution-failed")
print(matches[0])
PY
}

mkdir -p "$model_store" "$root/telemetry" "$core" "$soak"
chmod 700 "$model_store"
if curl -fsS --max-time 2 "$origin/api/version" >/dev/null 2>&1; then
  printf 'Refused: loopback port 11434 is already serving Ollama.\n' >&2
  exit 1
fi
if [[ ! -x "$runtime/bin/ollama" ]]; then
  printf 'Refused: reviewed isolated Ollama runtime is unavailable.\n' >&2
  exit 1
fi
if [[ -s "$events" ]]; then
  printf 'Refused: campaign event log already exists; use a fresh campaign directory.\n' >&2
  exit 1
fi

printf '%s\n' "$$" > "$root/campaign.pid"
printf '%s\n' 'timestamp, name, pci.bus_id, driver_version, pstate, temperature.gpu, memory.used, memory.total, utilization.gpu, power.draw, power.limit' > "$telemetry"
(
  while true; do
    nvidia-smi --query-gpu=timestamp,name,pci.bus_id,driver_version,pstate,temperature.gpu,memory.used,memory.total,utilization.gpu,power.draw,power.limit --format=csv,noheader,nounits >> "$telemetry" 2>> "$root/telemetry/logger.err" || true
    sleep 1
  done
) &
logger_pid=$!
printf '%s\n' "$logger_pid" > "$root/telemetry/logger.pid"

OLLAMA_HOST=127.0.0.1:11434 \
OLLAMA_MODELS="$model_store" \
OLLAMA_KEEP_ALIVE=0 \
  "$runtime/bin/ollama" serve > "$root/server.log" 2>&1 &
server_pid=$!
printf '%s\n' "$server_pid" > "$root/server.pid"

ready=false
for _ in $(seq 1 120); do
  if [[ $(curl -fsS --max-time 2 "$origin/api/version" 2>/dev/null || true) == '{"version":"0.32.14"}' ]]; then
    ready=true
    break
  fi
  sleep 1
done
if [[ "$ready" != true ]]; then
  printf 'Refused: reviewed Ollama runtime did not become ready.\n' >&2
  exit 1
fi

event campaign pre-idle-start
sleep 300
event campaign pre-idle-complete

printf 'model_id\tstatus\tfailure_cell\n' > "$core/summary.tsv"
event campaign core-start
for model_id in "${model_ids[@]}"; do
  model_dir="$core/$model_id"
  mkdir -p "$model_dir"
  event "$model_id" download-start
  if ! python3 "$root/scripts/alpha2-model-artifact-download.py" \
      --origin "$origin" --model-id "$model_id" --apply-download \
      > "$model_dir/download.json" 2> "$model_dir/download.err"; then
    event "$model_id" download-failed
    printf 'download-failed\n' > "$model_dir/complete.status"
    printf '%s\tdownload-failed\tdownload\n' "$model_id" >> "$core/summary.tsv"
    continue
  fi
  event "$model_id" download-complete

  passed=true
  failure_cell=""
  for capability in "${capabilities[@]}"; do
    for sample in 1 2 3; do
      cell="${capability//./-}-$sample"
      event "$model_id" "$cell-start"
      if python3 "$root/scripts/alpha2-linux-model-validation.py" \
          --origin "$origin" \
          --model-id "$model_id" \
          --capability "$capability" \
          --operating-system-id ubuntu-26-04-gnome \
          --platform-family linux \
          --backend cuda \
          --system-memory-gib 121 \
          --usable-gpu-memory-gib 4 \
          --qualification-inventory \
          > "$model_dir/$cell.json" 2> "$model_dir/$cell.err"; then
        event "$model_id" "$cell-passed"
      else
        event "$model_id" "$cell-failed"
        passed=false
        failure_cell="$cell"
        break 2
      fi
    done
  done

  if [[ "$passed" == true ]]; then
    status=passed
  else
    status=failed-validation
  fi
  printf '%s\n' "$status" > "$model_dir/complete.status"
  printf '%s\t%s\t%s\n' "$model_id" "$status" "$failure_cell" >> "$core/summary.tsv"
  event "$model_id" "$status"
done
event campaign core-complete

printf 'model_id\tstatus\n' > "$soak/summary.tsv"
event campaign soak-start
while IFS=$'\t' read -r model_id status failure_cell; do
  [[ "$model_id" == "model_id" || "$status" != "passed" ]] && continue
  event "$model_id" soak-start
  if python3 "$root/scripts/alpha2-linux-soak.py" \
      --origin "$origin" \
      --model-id "$model_id" \
      --operating-system-id ubuntu-26-04-gnome \
      --platform-family linux \
      --backend cuda \
      --system-memory-gib 121 \
      --usable-gpu-memory-gib 4 \
      --duration-minutes 30 \
      --interval-seconds 30 \
      --qualification-inventory \
      --qualification-profile-id cuda-4gib-system-16gib \
      > "$soak/$model_id.json" 2> "$soak/$model_id.err"; then
    soak_status=passed
  else
    soak_status=failed
  fi
  printf '%s\t%s\n' "$model_id" "$soak_status" >> "$soak/summary.tsv"
  event "$model_id" "soak-$soak_status"

  if name=$(model_name "$model_id"); then
    curl -fsS -X DELETE -H 'Content-Type: application/json' \
      --data "{\"model\":\"$name\"}" "$origin/api/delete" \
      > "$soak/$model_id-delete.json" 2> "$soak/$model_id-delete.err" || true
  fi
done < "$core/summary.tsv"

event campaign soak-complete
event campaign post-idle-start
sleep 300
event campaign post-idle-complete
printf 'GTX1650_SUPER_CAMPAIGN_COMPLETE\n'
