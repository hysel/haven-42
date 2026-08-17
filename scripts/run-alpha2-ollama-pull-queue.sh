#!/usr/bin/env bash
set -Eeuo pipefail

# Wait for one reviewed campaign marker, then acquire exact model tags supplied
# by the caller. This helper records only model tags and provider progress. It
# never changes a runtime, starts hardware, or promotes a model.

if (( $# < 4 )); then
  printf 'Usage: %s BASE OLLAMA_BIN COMPLETION_MARKER MODEL [MODEL ...]\n' "$0" >&2
  exit 2
fi

readonly BASE="$1"
readonly OLLAMA_BIN="$2"
readonly COMPLETION_MARKER="$3"
shift 3
readonly -a MODELS=("$@")

[[ "$BASE" == /* && -d "$BASE" && ! -L "$BASE" ]] || {
  printf 'Refused: BASE must be an existing absolute non-link directory.\n' >&2
  exit 1
}
[[ "$OLLAMA_BIN" == /* && -x "$OLLAMA_BIN" && ! -L "$OLLAMA_BIN" ]] || {
  printf 'Refused: OLLAMA_BIN must be an executable absolute non-link file.\n' >&2
  exit 1
}
[[ "$COMPLETION_MARKER" == "$BASE"/* && "$COMPLETION_MARKER" != *'..'* ]] || {
  printf 'Refused: completion marker must stay below BASE.\n' >&2
  exit 1
}

for model in "${MODELS[@]}"; do
  [[ "$model" =~ ^[a-z0-9][a-z0-9._/-]{0,95}:[A-Za-z0-9][A-Za-z0-9._-]{0,95}$ ]] || {
    printf 'Refused: unsafe exact model tag.\n' >&2
    exit 1
  }
done
while [[ ! -f "$COMPLETION_MARKER" ]]; do
  sleep 30
done

for model in "${MODELS[@]}"; do
  printf 'START %s\n' "$model"
  "$OLLAMA_BIN" pull "$model"
  printf 'DONE %s\n' "$model"
done
