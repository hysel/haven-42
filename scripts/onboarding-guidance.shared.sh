#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$#" -lt 1 ]; then
  printf 'Usage: %s <beginner-plan|agent-menu|workflow-chooser> [options]\n' "$(basename "$0")" >&2
  exit 2
fi

VIEW="$1"
shift
case "$VIEW" in
  beginner-plan|agent-menu|workflow-chooser) ;;
  *) printf 'Unknown onboarding view: %s\n' "$VIEW" >&2; exit 2 ;;
esac

PLATFORM="linux"
ARGS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --platform|-Platform) PLATFORM="$2"; shift 2 ;;
    --output-path|-OutputPath) ARGS+=(--output-path "$2"); shift 2 ;;
    --markdown-output-path|-MarkdownOutputPath) ARGS+=(--markdown-output-path "$2"); shift 2 ;;
    --as-json|-AsJson) ARGS+=(--as-json); shift ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

command -v python3 >/dev/null 2>&1 || {
  printf 'python3 is required for native onboarding rendering.\n' >&2
  exit 127
}
exec python3 "$SCRIPT_DIR/onboarding-guidance.py" "$VIEW" --platform "$PLATFORM" "${ARGS[@]}"
