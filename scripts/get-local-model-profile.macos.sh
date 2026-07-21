#!/usr/bin/env bash
set -u

AS_JSON=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL_CATALOG_PATH="$REPO_ROOT/config/model-recommendations.tsv"
MLX_MODEL_CATALOG_PATH="$REPO_ROOT/config/model-recommendations.mlx.tsv"

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
    --mlx-model-catalog)
      MLX_MODEL_CATALOG_PATH="$2"
      shift 2
      ;;
    --help|-h)
      printf '%s\n' 'Usage: ./scripts/get-local-model-profile.macos.sh [--json] [--model-catalog <path>] [--mlx-model-catalog <path>]'
      exit 0
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

python_module_exists() {
  command_exists python3 && python3 -c "import $1" >/dev/null 2>&1
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
    "") printf 'Unknown' ;;
    *) printf '%s' "$1" ;;
  esac
}

gb_from_bytes() {
  awk -v bytes="$1" 'BEGIN { printf "%.1f", bytes / 1024 / 1024 / 1024 }'
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
    for model in "${OLLAMA_MODELS[@]-}"; do
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
    RECOMMENDED_MODEL="qwen3.5:9b"
    RECOMMENDED_USE="Validate the model against the target workflow before relying on it."
    VALIDATION_NOTE="Run read-only discovery and tool-call validation before approved write mode."
  fi
}

recommend_mlx_from_catalog() {
  tier_name="$1"

  MLX_RECOMMENDED_MODEL="Not available"
  MLX_RECOMMENDED_USE="MLX tooling was not detected in the current shell."
  MLX_VALIDATION_NOTE="Install and validate MLX tooling before using MLX-hosted models with Continue."

  if [ "$MLX_STATUS" != "detected" ]; then
    return 0
  fi

  if [ -r "$MLX_MODEL_CATALOG_PATH" ]; then
    while IFS='|' read -r tier model_name use validation; do
      case "$tier" in ""|\#*) continue ;; esac
      [ "$tier" != "$tier_name" ] && continue

      MLX_RECOMMENDED_MODEL="$model_name"
      MLX_RECOMMENDED_USE="$use"
      MLX_VALIDATION_NOTE="$validation"
      return 0
    done < "$MLX_MODEL_CATALOG_PATH"
  fi

  MLX_RECOMMENDED_MODEL="MLX-compatible coding model"
  MLX_RECOMMENDED_USE="Use as an advanced Apple Silicon candidate only after serving validation."
  MLX_VALIDATION_NOTE="Serve through an OpenAI-compatible local endpoint and validate read-only tool behavior before approved write mode."
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
CPU_ARCHITECTURE="$(normalize_architecture "$(uname -m 2>/dev/null || true)")"
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

MLX_TOOLS=()
PACK_MLX_SERVER="$HOME/.haven-42-mlx/bin/mlx_lm.server"
if [ -x "$PACK_MLX_SERVER" ]; then
  MLX_TOOLS+=("pack virtual environment: mlx_lm.server")
fi
for tool in mlx-lm mlx_lm.generate mlx_lm.chat mlx_lm.server; do
  if command_exists "$tool"; then
    MLX_TOOLS+=("$tool")
  fi
done

if python_module_exists "mlx_lm"; then
  already_detected=false
  for tool in "${MLX_TOOLS[@]-}"; do
    if [ "$tool" = "python3 module: mlx_lm" ]; then
      already_detected=true
      break
    fi
  done
  [ "$already_detected" = false ] && MLX_TOOLS+=("python3 module: mlx_lm")
fi

if python_module_exists "mlx"; then
  already_detected=false
  for tool in "${MLX_TOOLS[@]-}"; do
    if [ "$tool" = "python3 module: mlx" ]; then
      already_detected=true
      break
    fi
  done
  [ "$already_detected" = false ] && MLX_TOOLS+=("python3 module: mlx")
fi

MLX_STATUS="not detected"
if [ -n "${MLX_TOOLS[*]-}" ]; then
  MLX_STATUS="detected"
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

RECOMMENDED_MODEL=""
RECOMMENDED_USE=""
VALIDATION_NOTE=""
MLX_RECOMMENDED_MODEL=""
MLX_RECOMMENDED_USE=""
MLX_VALIDATION_NOTE=""
MLX_TIER="Low"

# Unified memory is shared by macOS, the editor, and the MLX runtime. Keep the
# MLX recommendation more conservative than the generic Ollama RAM tier.
if [ "$RAM_INT" -ge 32 ]; then
  MLX_TIER="High"
elif [ "$RAM_INT" -ge 24 ]; then
  MLX_TIER="Medium"
fi

if [ "$TIER" = "High resource candidate" ]; then
  recommend_from_catalog "High"
elif [ "$TIER" = "Medium resource candidate" ]; then
  recommend_from_catalog "Medium"
else
  recommend_from_catalog "Low"
fi

recommend_mlx_from_catalog "$MLX_TIER"

# An MLX-only Apple Silicon host should not be told to pull the generic Ollama
# fallback. Keep the JSON field present for callers, but make its meaning clear.
if [ "$MLX_STATUS" = "detected" ] && [ "${#OLLAMA_MODELS[@]}" -eq 0 ]; then
  RECOMMENDED_MODEL="Not applicable on this MLX-only host"
  RECOMMENDED_USE="Use the MLX recommendation above; no local Ollama model is available."
  VALIDATION_NOTE="Keep the MLX endpoint bound to loopback and validate the intended editor workflow before approved writes."
fi

GENERATED="$(date '+%Y-%m-%d %H:%M')"

if [ "$AS_JSON" = true ]; then
  printf '{\n'
  printf '  "GeneratedAt": "%s",\n' "$(json_escape "$GENERATED")"
  printf '  "Platform": "macOS",\n'
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
  printf '  "OllamaStatus": "%s",\n' "$(json_escape "$OLLAMA_STATUS")"
  printf '  "OllamaModels": ['
  for i in "${!OLLAMA_MODELS[@]}"; do
    [ "$i" -gt 0 ] && printf ', '
    printf '"%s"' "$(json_escape "${OLLAMA_MODELS[$i]}")"
  done
  printf '],\n'
  printf '  "MlxStatus": "%s",\n' "$(json_escape "$MLX_STATUS")"
  printf '  "MlxTools": ['
  for i in "${!MLX_TOOLS[@]}"; do
    [ "$i" -gt 0 ] && printf ', '
    printf '"%s"' "$(json_escape "${MLX_TOOLS[$i]}")"
  done
  printf '],\n'
  printf '  "RecommendationTier": "%s",\n' "$(json_escape "$TIER")"
  printf '  "ModelRecommendation": {"PrimaryModel":"%s","Use":"%s","Validation":"%s"},\n' "$(json_escape "$RECOMMENDED_MODEL")" "$(json_escape "$RECOMMENDED_USE")" "$(json_escape "$VALIDATION_NOTE")"
  printf '  "MlxRecommendation": {"PrimaryModel":"%s","Use":"%s","Validation":"%s"}\n' "$(json_escape "$MLX_RECOMMENDED_MODEL")" "$(json_escape "$MLX_RECOMMENDED_USE")" "$(json_escape "$MLX_VALIDATION_NOTE")"
  printf '}\n'
  exit 0
fi

printf 'Local Model Profile\n\n'
printf 'Generated: %s\n' "$GENERATED"
printf 'Platform: macOS\n'
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
printf '\nOllama: %s\n' "$OLLAMA_STATUS"
if [ "${#OLLAMA_MODELS[@]}" -gt 0 ]; then
  printf 'Installed Ollama models:\n'
  for model in "${OLLAMA_MODELS[@]}"; do
    printf -- '- %s\n' "$model"
  done
else
  printf 'Installed Ollama models: None detected\n'
fi
printf '\nMLX tooling: %s\n' "$MLX_STATUS"
if [ -n "${MLX_TOOLS[*]-}" ]; then
  printf 'Detected MLX tools:\n'
  for tool in "${MLX_TOOLS[@]-}"; do
    printf -- '- %s\n' "$tool"
  done
fi
printf 'MLX recommendation: %s\n' "$MLX_RECOMMENDED_MODEL"
printf 'MLX use: %s\n' "$MLX_RECOMMENDED_USE"
printf 'MLX validation note: %s\n' "$MLX_VALIDATION_NOTE"
printf '\nRecommendation tier: %s\n\n' "$TIER"
if [ "$RECOMMENDED_MODEL" = "Not applicable on this MLX-only host" ]; then
  printf 'Ollama recommendation: not applicable; use the MLX recommendation above.\n\n'
else
  printf 'Recommended model: %s\n' "$RECOMMENDED_MODEL"
  printf 'Recommended use: %s\n' "$RECOMMENDED_USE"
  printf 'Validation note: %s\n\n' "$VALIDATION_NOTE"
fi
printf 'Use docs/local-model-selection.md to choose the final model. This helper does not collect hostnames, IP addresses, usernames, or local paths.\n'
