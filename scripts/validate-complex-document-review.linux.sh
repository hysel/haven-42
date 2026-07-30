#!/bin/sh
set -eu

if [ "$(uname -s)" != "Linux" ]; then
  echo "This validation command requires native Linux." >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
cd "$REPO_ROOT"
exec python3 scripts/run-native-complex-document-validation.py --platform linux
