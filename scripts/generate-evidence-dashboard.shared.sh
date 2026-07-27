#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EVIDENCE_CATALOG="$REPO_ROOT/config/evidence-catalog.tsv"
SURFACE_MATRIX="$REPO_ROOT/config/agent-surface-capabilities.json"
SURFACE_SOLUTIONS="$REPO_ROOT/config/agent-surface-solutions.json"
OUTPUT_PATH=""
MARKDOWN_OUTPUT_PATH=""
AS_JSON=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --evidence-catalog-path|-EvidenceCatalogPath)
      EVIDENCE_CATALOG="$2"
      shift 2
      ;;
    --surface-matrix-path|-SurfaceMatrixPath)
      SURFACE_MATRIX="$2"
      shift 2
      ;;
    --surface-solution-path|-SurfaceSolutionPath)
      SURFACE_SOLUTIONS="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --markdown-output-path|-MarkdownOutputPath)
      MARKDOWN_OUTPUT_PATH="$2"
      shift 2
      ;;
    --as-json|-AsJson)
      AS_JSON=1
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

args=(
  --evidence-catalog-path "$EVIDENCE_CATALOG"
  --surface-matrix-path "$SURFACE_MATRIX"
  --surface-solution-path "$SURFACE_SOLUTIONS"
)
[ -n "$OUTPUT_PATH" ] && args+=(--output-path "$OUTPUT_PATH")
[ -n "$MARKDOWN_OUTPUT_PATH" ] && args+=(--markdown-output-path "$MARKDOWN_OUTPUT_PATH")
[ "$AS_JSON" -eq 1 ] && args+=(--as-json)
if command -v python3 >/dev/null 2>&1 &&
   python3 -c 'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)' >/dev/null 2>&1; then
  python_command=(python3)
elif command -v python >/dev/null 2>&1 &&
     python -c 'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)' >/dev/null 2>&1; then
  python_command=(python)
elif command -v py >/dev/null 2>&1 &&
     py -3 -c 'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)' >/dev/null 2>&1; then
  python_command=(py -3)
else
  printf 'Python 3 is required to generate the evidence dashboard.\n' >&2
  exit 1
fi
exec "${python_command[@]}" "$SCRIPT_DIR/evidence_dashboard.py" "${args[@]}"
