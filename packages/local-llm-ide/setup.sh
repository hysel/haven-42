#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/haven42_ide.py" "$@"
fi
printf '%s\n' 'Python 3 is required to configure the IDE tools.' >&2
exit 1
