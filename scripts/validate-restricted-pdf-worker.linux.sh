#!/usr/bin/env sh
set -eu

[ "$(uname -s 2>/dev/null || true)" = "Linux" ] || {
  printf '%s\n' "This validation command is for Linux only." >&2
  exit 2
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
exec python3 "$REPO_ROOT/scripts/run-native-pdf-worker-validation.py" --platform linux
