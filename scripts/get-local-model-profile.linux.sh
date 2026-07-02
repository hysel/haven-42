#!/usr/bin/env bash
set -u

AS_JSON=false
if [ "${1:-}" = "--json" ]; then
  AS_JSON=true
fi

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

gb_from_kb() {
  awk -v kb="$1" 'BEGIN { printf "%.1f", kb / 1024 / 1024 }'
}

gb_from_mb() {
  awk -v mb="$1" 'BEGIN { printf "%.1f", mb / 1024 }'
}

detect_vendor() {
  case "$1" in
    *NVIDIA*|*Nvidia*|*nvidia*) printf 'NVIDIA' ;;
    *AMD*|*Radeon*|*Advanced\ Micro\ Devices*) printf 'AMD' ;;
    *Intel*|*intel*) printf 'Intel' ;;
    *) printf 'Unknown' ;;
  esac
}

OS_SUMMARY="Linux"
if [ -r /etc/os-release ]; then
  OS_SUMMARY="$(grep '^PRETTY_NAME=' /etc/os-release | head -n 1 | cut -d= -f2- | tr -d '"')"
fi

RAM_GB="Unknown"
if [ -r /proc/meminfo ]; then
  MEM_KB="$(awk '/^MemTotal:/ { print $2; exit }' /proc/meminfo)"
  if [ -n "$MEM_KB" ]; then
    RAM_GB="$(gb_from_kb "$MEM_KB")"
  fi
fi

CPU="Unknown"
if command_exists lscpu; then
  CPU_MODEL="$(lscpu | awk -F: '/^Model name:/ { sub(/^[ \t]+/, "", $2); print $2; exit }')"
  CPU_COUNT="$(lscpu | awk -F: '/^CPU\(s\):/ { sub(/^[ \t]+/, "", $2); print $2; exit }')"
  if [ -n "$CPU_MODEL" ]; then
    CPU="$CPU_MODEL ($CPU_COUNT logical processors)"
  fi
fi

GPU_NAMES=()
GPU_VRAMS=()
GPU_SOURCES=()
GPU_VENDORS=()
GPU_MEMORY_TYPES=()

add_gpu() {
  GPU_NAMES+=("$1")
  GPU_VRAMS+=("$2")
  GPU_SOURCES+=("$3")
  GPU_VENDORS+=("$4")
  GPU_MEMORY_TYPES+=("$5")
}

if command_exists nvidia-smi; then
  while IFS=, read -r name memory; do
    name="$(printf '%s' "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    memory="$(printf '%s' "$memory" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    if [ -n "$name" ] && [ -n "$memory" ]; then
      add_gpu "$name" "$(gb_from_mb "$memory")" "nvidia-smi" "NVIDIA" "dedicated"
    fi
  done < <(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null)
fi

if [ "${#GPU_NAMES[@]}" -eq 0 ] && command_exists rocm-smi; then
  ROCM_OUTPUT="$(rocm-smi --showproductname --showmeminfo vram 2>/dev/null || true)"
  while IFS= read -r index; do
    name="$(printf '%s\n' "$ROCM_OUTPUT" | awk -v idx="GPU\\[$index\\]" '$0 ~ idx && ($0 ~ /Card series|Card model|Product Name|Marketing Name/) { sub(/^.*: */, ""); print; exit }')"
    memory_line="$(printf '%s\n' "$ROCM_OUTPUT" | awk -v idx="GPU\\[$index\\]" '$0 ~ idx && $0 ~ /VRAM Total Memory/ { print; exit }')"
    vram="Unknown"
    if printf '%s' "$memory_line" | grep -Eq '[0-9.]+'; then
      value="$(printf '%s' "$memory_line" | grep -Eo '[0-9.]+' | tail -n 1)"
      if printf '%s' "$memory_line" | grep -Eq 'GB'; then
        vram="$value"
      elif printf '%s' "$memory_line" | grep -Eq 'MB'; then
        vram="$(gb_from_mb "$value")"
      else
        vram="$(awk -v b="$value" 'BEGIN { printf "%.1f", b / 1024 / 1024 / 1024 }')"
      fi
    fi
    [ -z "$name" ] && name="AMD GPU $index"
    add_gpu "$name" "$vram" "rocm-smi" "AMD" "dedicated"
  done < <(printf '%s\n' "$ROCM_OUTPUT" | grep -Eo 'GPU\[[0-9]+\]' | grep -Eo '[0-9]+' | sort -u)
fi

if [ "${#GPU_NAMES[@]}" -eq 0 ] && command_exists lspci; then
  while IFS= read -r row; do
    name="$(printf '%s' "$row" | sed 's/^[^ ]* //')"
    vendor="$(detect_vendor "$name")"
    memory_type="unknown"
    if [ "$vendor" = "Intel" ]; then
      memory_type="shared or integrated"
    fi
    add_gpu "$name" "Unknown" "lspci" "$vendor" "$memory_type"
  done < <(lspci 2>/dev/null | grep -Ei 'vga compatible controller|3d controller|display controller')
fi

OLLAMA_STATUS="ollama command not found"
OLLAMA_MODELS=()
if command_exists ollama; then
  if OLLAMA_LIST="$(ollama list 2>/dev/null)"; then
    OLLAMA_STATUS="reachable"
    while IFS= read -r row; do
      model="$(printf '%s' "$row" | awk '{ print $1 }')"
      [ -n "$model" ] && [ "$model" != "NAME" ] && OLLAMA_MODELS+=("$model")
    done <<< "$OLLAMA_LIST"
  else
    OLLAMA_STATUS="installed but not reachable or no models listed"
  fi
fi

TIER="Low resource candidate"
RAM_INT=0
if [ "$RAM_GB" != "Unknown" ]; then
  RAM_INT="${RAM_GB%.*}"
fi
MAX_VRAM=0
for vram in "${GPU_VRAMS[@]}"; do
  if [ "$vram" != "Unknown" ]; then
    vram_int="${vram%.*}"
    [ "$vram_int" -gt "$MAX_VRAM" ] && MAX_VRAM="$vram_int"
  fi
done
if [ "$RAM_INT" -ge 32 ] && { [ "$MAX_VRAM" -ge 16 ] || [ "$MAX_VRAM" -eq 0 ]; }; then
  TIER="High resource candidate"
elif [ "$RAM_INT" -ge 16 ] || [ "$MAX_VRAM" -ge 8 ]; then
  TIER="Medium resource candidate"
fi

GENERATED="$(date '+%Y-%m-%d %H:%M')"

if [ "$AS_JSON" = true ]; then
  printf '{\n'
  printf '  "GeneratedAt": "%s",\n' "$(json_escape "$GENERATED")"
  printf '  "Platform": "Linux",\n'
  printf '  "OperatingSystem": "%s",\n' "$(json_escape "$OS_SUMMARY")"
  printf '  "SystemRamGb": "%s",\n' "$(json_escape "$RAM_GB")"
  printf '  "Cpu": "%s",\n' "$(json_escape "$CPU")"
  printf '  "Gpus": [\n'
  for i in "${!GPU_NAMES[@]}"; do
    [ "$i" -gt 0 ] && printf ',\n'
    printf '    {"Name":"%s","VramGb":"%s","Source":"%s","Vendor":"%s","MemoryType":"%s"}' \
      "$(json_escape "${GPU_NAMES[$i]}")" "$(json_escape "${GPU_VRAMS[$i]}")" "$(json_escape "${GPU_SOURCES[$i]}")" "$(json_escape "${GPU_VENDORS[$i]}")" "$(json_escape "${GPU_MEMORY_TYPES[$i]}")"
  done
  printf '\n  ],\n'
  printf '  "OllamaStatus": "%s",\n' "$(json_escape "$OLLAMA_STATUS")"
  printf '  "OllamaModels": ['
  for i in "${!OLLAMA_MODELS[@]}"; do
    [ "$i" -gt 0 ] && printf ', '
    printf '"%s"' "$(json_escape "${OLLAMA_MODELS[$i]}")"
  done
  printf '],\n'
  printf '  "RecommendationTier": "%s"\n' "$(json_escape "$TIER")"
  printf '}\n'
  exit 0
fi

printf 'Local Model Profile\n\n'
printf 'Generated: %s\n' "$GENERATED"
printf 'Platform: Linux\n'
printf 'OS: %s\n' "$OS_SUMMARY"
printf 'RAM: %s GB\n' "$RAM_GB"
printf 'CPU: %s\n\n' "$CPU"
printf 'GPU:\n'
if [ "${#GPU_NAMES[@]}" -eq 0 ]; then
  printf -- '- Not detected\n'
else
  for i in "${!GPU_NAMES[@]}"; do
    printf -- '- %s (%s VRAM, %s, %s, %s)\n' "${GPU_NAMES[$i]}" "${GPU_VRAMS[$i]}" "${GPU_SOURCES[$i]}" "${GPU_VENDORS[$i]}" "${GPU_MEMORY_TYPES[$i]}"
  done
fi
printf '\nOllama: %s\n' "$OLLAMA_STATUS"
if [ "${#OLLAMA_MODELS[@]}" -gt 0 ]; then
  printf 'Installed Ollama models:\n'
  for model in "${OLLAMA_MODELS[@]}"; do
    printf -- '- %s\n' "$model"
  done
else
  printf 'Installed Ollama models: None detected\n'
fi
printf '\nRecommendation tier: %s\n\n' "$TIER"
printf 'Use docs/local-model-selection.md to choose the final model. This helper does not collect hostnames, IP addresses, usernames, or local paths.\n'
