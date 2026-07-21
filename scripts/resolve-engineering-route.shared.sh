#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if command -v python3 >/dev/null 2>&1; then PYTHON_COMMAND="python3"; elif command -v python >/dev/null 2>&1; then PYTHON_COMMAND="python"; else printf 'Python 3 is required for native engineering routing.\n' >&2; exit 1; fi
exec "$PYTHON_COMMAND" "$SCRIPT_DIR/resolve-engineering-route.py" --routes "$REPO_ROOT/config/engineering-routes.json" --workflows "$REPO_ROOT/config/workflows.json" "$@"
