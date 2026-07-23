#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for model catalog assembly.\n' >&2
  exit 1
fi

discovery_report=''
output_path=''

while [ "$#" -gt 0 ]; do
  case "$1" in
    --discovery-report|-DiscoveryReportPath) discovery_report="$2"; shift 2 ;;
    --output-path|-OutputPath) output_path="$2"; shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

[ -n "$discovery_report" ] || { printf '%s\n' '--discovery-report is required.' >&2; exit 2; }
if [ -z "$output_path" ]; then
  output_path="$REPO_ROOT/runtime-validation-output/model-catalog-$(date '+%Y%m%d-%H%M%S').json"
fi

exec python3 "$SCRIPT_DIR/build-model-catalog.py" \
  --contract-path "$REPO_ROOT/config/model-catalog-contract.json" \
  --discovery-report "$discovery_report" \
  --evidence-catalog "$REPO_ROOT/config/evidence-catalog.tsv" \
  --output-path "$output_path"
