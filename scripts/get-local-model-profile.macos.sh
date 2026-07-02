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

gb_from_bytes() {
  awk -v bytes="$1" 'BEGIN { printf "%.1f", bytes / 1024 / 1024 / 1024 }'
}

gb_from_mb() {
  awk -v mb="$1" 'BEGIN { printf "%.1f", mb / 1024 }'
}

detect_vendor() {
  case "$1" in
    *NVIDIA*|*Nvidia*|*nvidia*) printf 'NVIDIA' ;;
    *AMD*|*Radeon*|*Advanced\ Micro\ Devices*) printf 'AMD' ;;
    *Intel*|*intel*) printf 'Intel' ;;
    *Apple*|*M1*|*M2*|*M3*|*M4*) printf 'Apple' ;;
    *) printf 'Unknown' ;;
  esac
}

OS_SUMMARY="$(sw_vers -productName 2>/dev/null) $(sw_vers -productVersion 2>/dev/null)"
MEM_BYTES="$(sysctl -n hw.memsize 2>/dev/null || true)"
RAM_GB="Unknown"
[ -n "$MEM_BYTES" ] && RAM_GB="$(gb_from_bytes "$MEM_BYTES")"

CPU="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || true)"
LOGICAL="$(sysctl -n hw.logicalcpu 2>/dev/null || true)"
if [ -z "$CPU" ]; then
  CPU="$(sysctl -n hw.model 2>/dev/null || printf 'Unknown')"
fi
CPU="$CPU ($LOGICAL logical processors)"

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

if command_exists system_profiler; then
  DISPLAY_INFO="$(system_profiler SPDisplaysDataType 2>/dev/null || true)"
  current_name=""
  while IFS= read -r line; do
    case "$line" in
      *"Chipset Model:"*)
        current_name="$(printf '%s' "$line" | sed 's/^.*Chipset Model:[[:space:]]*//')"
        ;;
      *"VRAM"*)
        if [ -n "$current_name" ]; then
          value="$(printf '%s' "$line" | sed 's/^.*VRAM[^:]*:[[:space:]]*//')"
          vram="Unknown"
          if printf '%s' "$value" | grep -Eq '[0-9]+[[:space:]]*GB'; then
            vram="$(printf '%s' "$value" | grep -Eo '[0-9]+' | head -n 1)"
          elif printf '%s' "$value" | grep -Eq '[0-9]+[[:space:]]*MB'; then
            mb="$(printf '%s' "$value" | grep -Eo '[0-9]+' | head -n 1)"
            vram="$(gb_from_mb "$mb")"
          fi
          vendor="$(detect_vendor "$current_name")"
          memory_type="dedicated"
          [ "$vendor" = "Intel" ] && memory_type="shared or integrated"
          [ "$vendor" = "Apple" ] && memory_type="unified"
          add_gpu "$current_name" "$vram" "system_profiler" "$vendor" "$memory_type"
          current_name=""
        fi
        ;;
      *"Total Number of Cores:"*)
        if [ -n "$current_name" ]; then
          vendor="$(detect_vendor "$current_name")"
          memory_type="unified"
          add_gpu "$current_name" "Shared" "system_profiler" "$vendor" "$memory_type"
          current_name=""
        fi
        ;;
    esac
  done <<< "$DISPLAY_INFO"
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
if [ "$RAM_INT" -ge 32 ]; then
  TIER="High resource candidate"
elif [ "$RAM_INT" -ge 16 ]; then
  TIER="Medium resource candidate"
fi

GENERATED="$(date '+%Y-%m-%d %H:%M')"

if [ "$AS_JSON" = true ]; then
  printf '{\n'
  printf '  "GeneratedAt": "%s",\n' "$(json_escape "$GENERATED")"
  printf '  "Platform": "macOS",\n'
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
printf 'Platform: macOS\n'
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
