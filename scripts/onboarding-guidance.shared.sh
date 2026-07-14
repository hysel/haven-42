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
  beginner-plan) WINDOWS_SCRIPT="get-beginner-setup-plan.ps1"; TITLE="Beginner Setup Plan" ;;
  agent-menu) WINDOWS_SCRIPT="show-agent-pack-menu.ps1"; TITLE="Agent Pack Menu" ;;
  workflow-chooser) WINDOWS_SCRIPT="show-workflow-chooser.ps1"; TITLE="Workflow Chooser" ;;
  *) printf 'Unknown onboarding view: %s\n' "$VIEW" >&2; exit 2 ;;
esac

PLATFORM="linux"
ARGS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --platform|-Platform) PLATFORM="$2"; ARGS+=(-Platform "$2"); shift 2 ;;
    --output-path|-OutputPath) ARGS+=(-OutputPath "$2"); shift 2 ;;
    --markdown-output-path|-MarkdownOutputPath) ARGS+=(-MarkdownOutputPath "$2"); shift 2 ;;
    --as-json|-AsJson) ARGS+=(-AsJson); shift ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

if command -v pwsh >/dev/null 2>&1; then
  if [ ${#ARGS[@]} -eq 0 ]; then
    ARGS=(-Platform "$PLATFORM")
  elif [[ " ${ARGS[*]} " != *" -Platform "* ]]; then
    ARGS=(-Platform "$PLATFORM" "${ARGS[@]}")
  fi
  exec pwsh -NoProfile -File "$SCRIPT_DIR/$WINDOWS_SCRIPT" "${ARGS[@]}"
fi

printf '# %s\n\n' "$TITLE"
printf 'Full native rendering is not available because PowerShell was not found. Use config/workflows.json directly or run this command on Windows.\n'
