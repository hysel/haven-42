#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for provider-neutral model discovery.\n' >&2
  exit 1
fi

output_present=false
for argument in "$@"; do
  case "$argument" in --output-path|-OutputPath) output_present=true ;; esac
done
arguments=(
  --source-config "$REPO_ROOT/config/model-discovery-sources.json"
  --contract-path "$REPO_ROOT/config/model-discovery-contract.json"
)
if [ "$output_present" = false ]; then
  arguments+=(--output-path "$REPO_ROOT/runtime-validation-output/online-model-candidates-$(date '+%Y%m%d-%H%M%S').json")
fi

# The report contract fixes PullsModels and RewritesContinueConfig to false.
exec python3 "$SCRIPT_DIR/discover-online-model-candidates.py" "${arguments[@]}" "$@"
