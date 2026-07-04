#!/usr/bin/env bash
set -euo pipefail

OLLAMA_BASE_URL="http://127.0.0.1:11434"
MODELS=(
  "qwen3.5:9b"
  "devstral-small-2:24b"
  "qwen3-coder:30b"
)
CUSTOM_MODELS=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --ollama-base-url|-OllamaBaseUrl)
      OLLAMA_BASE_URL="$2"
      shift 2
      ;;
    --model|-Model)
      if [ "$CUSTOM_MODELS" = false ]; then
        MODELS=()
        CUSTOM_MODELS=true
      fi
      MODELS+=("$2")
      shift 2
      ;;
    --models|-Models)
      if [ "$CUSTOM_MODELS" = false ]; then
        MODELS=()
        CUSTOM_MODELS=true
      fi
      IFS=',' read -r -a split_models <<< "$2"
      for model in "${split_models[@]}"; do
        MODELS+=("$(printf '%s' "$model" | sed 's/^ *//;s/ *$//')")
      done
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if ! command -v curl >/dev/null 2>&1; then
  printf 'curl is required for this script.\n' >&2
  exit 1
fi

OLLAMA_BASE_URL="${OLLAMA_BASE_URL%/}"

seen=""
for model in "${MODELS[@]}"; do
  [ -z "$model" ] && continue
  case " $seen " in
    *" $model "*) continue ;;
  esac
  seen="$seen $model"
  printf 'Pulling %s\n' "$model"
  curl -fsS "$OLLAMA_BASE_URL/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"stream\":false}" >/dev/null
  printf 'Pulled %s\n' "$model"
done

printf 'Model pull complete.\n'
