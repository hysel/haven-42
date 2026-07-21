#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/run-macos-wrapper.sh" "$0" "$SCRIPT_DIR/show-haven-42-menu.shared.sh" --platform macos "$@"
