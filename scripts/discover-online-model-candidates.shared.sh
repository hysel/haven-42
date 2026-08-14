#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for provider-neutral model discovery.\n' >&2
  exit 1
fi

output_path=""
markdown_present=false
arguments_in=("$@")
for ((index = 0; index < ${#arguments_in[@]}; index++)); do
  case "${arguments_in[$index]}" in
    --output-path|-OutputPath)
      if (( index + 1 < ${#arguments_in[@]} )); then
        output_path="${arguments_in[$((index + 1))]}"
      fi
      ;;
    --markdown-output-path) markdown_present=true ;;
  esac
done
if [ -z "$output_path" ]; then
  output_path="$REPO_ROOT/runtime-validation-output/online-model-candidates-$(date '+%Y%m%d-%H%M%S').json"
fi
arguments=(
  --source-config "$REPO_ROOT/config/model-discovery-sources.json"
  --contract-path "$REPO_ROOT/config/model-discovery-contract.json"
  --inventory-path "$REPO_ROOT/config/alpha-2-model-version-inventory.json"
)
if ! printf '%s\n' "${arguments_in[@]}" | grep -qx -- '--output-path'; then
  arguments+=(--output-path "$output_path")
fi
if [ "$markdown_present" = false ]; then
  arguments+=(--markdown-output-path "${output_path%.*}.md")
fi

# The report contract fixes PullsModels and RewritesContinueConfig to false.
exec python3 "$SCRIPT_DIR/discover-online-model-candidates.py" "${arguments[@]}" "$@"
