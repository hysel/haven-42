#!/usr/bin/env bash
set -euo pipefail

INSTALL=false
INSTALL_OLLAMA=false
INSTALL_MLX=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --install) INSTALL=true; shift ;;
    --with-ollama) INSTALL_OLLAMA=true; shift ;;
    --with-mlx) INSTALL_MLX=true; shift ;;
    --help|-h) printf '%s\n' 'Usage: ./scripts/bootstrap-macos-agent-host.sh [--install] [--with-ollama] [--with-mlx]'; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

[ "$(uname -s)" = Darwin ] || { printf '%s\n' 'This bootstrap script is for macOS only.' >&2; exit 1; }
[ "$INSTALL_OLLAMA" = false ] || [ "$INSTALL" = true ] || { printf '%s\n' '--with-ollama requires --install.' >&2; exit 1; }
[ "$INSTALL_MLX" = false ] || [ "$INSTALL" = true ] || { printf '%s\n' '--with-mlx requires --install.' >&2; exit 1; }

ensure_brew_path() {
  if [ -x /opt/homebrew/bin/brew ]; then PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH";
  elif [ -x /usr/local/bin/brew ]; then PATH="/usr/local/bin:/usr/local/sbin:$PATH"; fi
}

ensure_brew_path
if [ "$INSTALL" = true ]; then
  printf '%s\n' 'Automated macOS installation is blocked: Haven 42 does not execute moving Homebrew or Python package sources.' >&2
  printf '%s\n' 'Install reviewed exact tool versions through their official package workflow, then rerun this script without --install for read-only discovery.' >&2
  exit 2
fi

printf 'Platform: macOS %s\n' "$(uname -m)"
for command_name in brew node npm ollama git python3 curl; do
  if command -v "$command_name" >/dev/null 2>&1; then printf '%s: %s\n' "$command_name" "$(command -v "$command_name")";
  else printf '%s: missing\n' "$command_name"; fi
done

MLX_VENV="$HOME/.haven-42-mlx"
if [ -x "$MLX_VENV/bin/mlx_lm.server" ]; then
  printf '%s\n' 'MLX runtime: available (pack virtual environment)'
else
  printf '%s\n' 'MLX runtime: not detected (install a reviewed exact MLX environment through a user-managed workflow)'
fi

if command -v ollama >/dev/null 2>&1; then
  if curl -fsS --max-time 5 http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
    printf '%s\n' 'Ollama service: reachable'
    printf '%s\n' 'Next: pull a validated model, then run the macOS matrix.'
  else
    printf '%s\n' 'Ollama service: not reachable'
    printf '%s\n' 'Next: start Ollama, pull a validated model, then run the macOS matrix.'
  fi
else
  printf '%s\n' 'Next: install a reviewed Ollama version through its official package workflow, then rerun this read-only discovery.'
fi

if [ -x "$MLX_VENV/bin/mlx_lm.server" ]; then
  printf '%s\n' 'MLX note: serve models only on 127.0.0.1 and validate endpoint and tool behavior before using an agent surface.'
fi
