#!/usr/bin/env bash
set -u

AS_JSON=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL_CATALOG_PATH="$REPO_ROOT/config/model-recommendations.tsv"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --json)
      AS_JSON=true
      shift
      ;;
    --model-catalog)
      MODEL_CATALOG_PATH="$2"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

json_number_or_null() {
  case "$1" in
    ''|Unknown|Shared)
      printf 'null'
      ;;
    *)
      if printf '%s' "$1" | grep -Eq '^[0-9]+([.][0-9]+)?$'; then
        printf '%s' "$1"
      else
        printf 'null'
      fi
      ;;
  esac
}

normalize_architecture() {
  case "$1" in
    x86_64|amd64) printf 'x64' ;;
    i386|i686|x86) printf 'x86' ;;
    aarch64|arm64) printf 'arm64' ;;
    armv7l|armv7*) printf 'armv7' ;;
    armv6l|armv6*) printf 'armv6' ;;
    "") printf 'Unknown' ;;
    *) printf '%s' "$1" ;;
  esac
}

gb_from_kb() {
  awk -v kb="$1" 'BEGIN { printf "%.1f", kb / 1024 / 1024 }'
}

gb_from_mb() {
  awk -v mb="$1" 'BEGIN { printf "%.1f", mb / 1024 }'
}

format_vram_label() {
  case "$1" in
    Unknown|Shared|"") printf '%s VRAM' "${1:-Unknown}" ;;
    *) printf '%s GB VRAM' "$1" ;;
  esac
}

find_model() {
  for pattern in "$@"; do
    for model in "${OLLAMA_MODELS[@]}"; do
      if printf '%s' "$model" | grep -Eiq "$pattern"; then
        printf '%s' "$model"
        return 0
      fi
    done
  done

  return 1
}

recommend_from_catalog() {
  tier_name="$1"
  fallback_model=""
  fallback_use=""
  fallback_validation=""

  if [ -r "$MODEL_CATALOG_PATH" ]; then
    while IFS='|' read -r tier pattern model_name use validation; do
      case "$tier" in ""|\#*) continue ;; esac
      [ "$tier" != "$tier_name" ] && continue

      if [ -n "$pattern" ]; then
        installed_model="$(find_model "$pattern" || true)"
        if [ -n "$installed_model" ]; then
          RECOMMENDED_MODEL="$installed_model"
          RECOMMENDED_USE="$use"
          VALIDATION_NOTE="$validation"
          return 0
        fi
      elif [ -z "$fallback_model" ]; then
        fallback_model="$model_name"
        fallback_use="$use"
        fallback_validation="$validation"
      fi
    done < "$MODEL_CATALOG_PATH"
  fi

  if [ -n "$fallback_model" ]; then
    RECOMMENDED_MODEL="$fallback_model"
    RECOMMENDED_USE="$fallback_use"
    VALIDATION_NOTE="$fallback_validation"
  else
    RECOMMENDED_MODEL="qwen3-coder:30b"
    RECOMMENDED_USE="Validate the model against the target workflow before relying on it."
    VALIDATION_NOTE="Run read-only discovery and tool-call validation before approved write mode."
  fi
}

detect_vendor() {
  case "$1" in
    *NVIDIA*|*Nvidia*|*nvidia*) printf 'NVIDIA' ;;
    *AMD*|*Radeon*|*Advanced\ Micro\ Devices*) printf 'AMD' ;;
    *Intel*|*intel*) printf 'Intel' ;;
    *) printf 'Unknown' ;;
  esac
}

add_platform_note() {
  PLATFORM_NOTES+=("$1")
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
CPU_ARCHITECTURE="$(normalize_architecture "$(uname -m 2>/dev/null || true)")"
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
PLATFORM_NOTES=()

add_gpu() {
  GPU_NAMES+=("$1")
  GPU_VRAMS+=("$2")
  GPU_SOURCES+=("$3")
  GPU_VENDORS+=("$4")
  GPU_MEMORY_TYPES+=("$5")
}

case "$CPU_ARCHITECTURE" in
  arm64|armv7|armv6|arm*)
    add_platform_note "ARM Linux detected; treat local model recommendations conservatively until acceleration and tool execution are validated."
    ;;
esac

JETSON_DETECTED=false
if [ -r /etc/nv_tegra_release ]; then
  JETSON_DETECTED=true
fi

for model_file in /proc/device-tree/model /sys/firmware/devicetree/base/model; do
  if [ -r "$model_file" ]; then
    model_text="$(tr -d '\000' < "$model_file" 2>/dev/null || true)"
    if printf '%s' "$model_text" | grep -Eiq 'jetson|tegra|nvidia'; then
      JETSON_DETECTED=true
    fi
  fi
done

if [ "$JETSON_DETECTED" = true ]; then
  add_platform_note "NVIDIA Jetson or Tegra indicators detected; verify JetPack, CUDA, container/device access, and Ollama acceleration before trusting model sizing."
fi

GPU_DETECTION_TOOLS=()
command_exists nvidia-smi && GPU_DETECTION_TOOLS+=("nvidia-smi")
command_exists rocm-smi && GPU_DETECTION_TOOLS+=("rocm-smi")
command_exists lspci && GPU_DETECTION_TOOLS+=("lspci")

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

if [ "${#GPU_DETECTION_TOOLS[@]}" -eq 0 ]; then
  add_platform_note "Linux GPU detection is limited because nvidia-smi, rocm-smi, and lspci are not available; treat GPU and VRAM results as incomplete."
elif [ "${#GPU_NAMES[@]}" -eq 0 ]; then
  add_platform_note "Linux GPU detection tools were available but no GPU was detected; verify drivers, containers, permissions, or cloud instance GPU attachment before choosing larger models."
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

RECOMMENDED_MODEL=""
RECOMMENDED_USE=""
VALIDATION_NOTE=""

if [ "$TIER" = "High resource candidate" ]; then
  recommend_from_catalog "High"
elif [ "$TIER" = "Medium resource candidate" ]; then
  recommend_from_catalog "Medium"
else
  recommend_from_catalog "Low"
fi

GENERATED="$(date '+%Y-%m-%d %H:%M')"

if [ "$AS_JSON" = true ]; then
  printf '{\n'
  printf '  "GeneratedAt": "%s",\n' "$(json_escape "$GENERATED")"
  printf '  "Platform": "Linux",\n'
  printf '  "OperatingSystem": "%s",\n' "$(json_escape "$OS_SUMMARY")"
  printf '  "SystemRamGb": %s,\n' "$(json_number_or_null "$RAM_GB")"
  printf '  "Cpu": "%s",\n' "$(json_escape "$CPU")"
  printf '  "CpuArchitecture": "%s",\n' "$(json_escape "$CPU_ARCHITECTURE")"
  printf '  "Gpus": [\n'
  for i in "${!GPU_NAMES[@]}"; do
    [ "$i" -gt 0 ] && printf ',\n'
    printf '    {"Name":"%s","VramGb":%s,"Source":"%s","Vendor":"%s","MemoryType":"%s"}' \
      "$(json_escape "${GPU_NAMES[$i]}")" "$(json_number_or_null "${GPU_VRAMS[$i]}")" "$(json_escape "${GPU_SOURCES[$i]}")" "$(json_escape "${GPU_VENDORS[$i]}")" "$(json_escape "${GPU_MEMORY_TYPES[$i]}")"
  done
  printf '\n  ],\n'
  printf '  "PlatformNotes": ['
  for i in "${!PLATFORM_NOTES[@]}"; do
    [ "$i" -gt 0 ] && printf ', '
    printf '"%s"' "$(json_escape "${PLATFORM_NOTES[$i]}")"
  done
  printf '],\n'
  printf '  "OllamaStatus": "%s",\n' "$(json_escape "$OLLAMA_STATUS")"
  printf '  "OllamaModels": ['
  for i in "${!OLLAMA_MODELS[@]}"; do
    [ "$i" -gt 0 ] && printf ', '
    printf '"%s"' "$(json_escape "${OLLAMA_MODELS[$i]}")"
  done
  printf '],\n'
  printf '  "RecommendationTier": "%s",\n' "$(json_escape "$TIER")"
  printf '  "ModelRecommendation": {"PrimaryModel":"%s","Use":"%s","Validation":"%s"}\n' "$(json_escape "$RECOMMENDED_MODEL")" "$(json_escape "$RECOMMENDED_USE")" "$(json_escape "$VALIDATION_NOTE")"
  printf '}\n'
  exit 0
fi

printf 'Local Model Profile\n\n'
printf 'Generated: %s\n' "$GENERATED"
printf 'Platform: Linux\n'
printf 'OS: %s\n' "$OS_SUMMARY"
printf 'RAM: %s GB\n' "$RAM_GB"
printf 'CPU: %s\n' "$CPU"
printf 'Architecture: %s\n\n' "$CPU_ARCHITECTURE"
printf 'GPU:\n'
if [ "${#GPU_NAMES[@]}" -eq 0 ]; then
  printf -- '- Not detected\n'
else
  for i in "${!GPU_NAMES[@]}"; do
    vram_label="$(format_vram_label "${GPU_VRAMS[$i]}")"
    printf -- '- %s (%s, %s, %s, %s)\n' "${GPU_NAMES[$i]}" "$vram_label" "${GPU_SOURCES[$i]}" "${GPU_VENDORS[$i]}" "${GPU_MEMORY_TYPES[$i]}"
  done
fi
printf '\nPlatform notes:\n'
if [ "${#PLATFORM_NOTES[@]}" -eq 0 ]; then
  printf -- '- None\n'
else
  for note in "${PLATFORM_NOTES[@]}"; do
    printf -- '- %s\n' "$note"
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
printf 'Recommended model: %s\n' "$RECOMMENDED_MODEL"
printf 'Recommended use: %s\n' "$RECOMMENDED_USE"
printf 'Validation note: %s\n\n' "$VALIDATION_NOTE"
printf 'Use docs/local-model-selection.md to choose the final model. This helper does not collect hostnames, IP addresses, usernames, or local paths.\n'
