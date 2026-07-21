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
  if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)";
  elif [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"; fi
}

ensure_brew_path
if ! command -v brew >/dev/null 2>&1; then
  if [ "$INSTALL" = false ]; then printf '%s\n' 'Homebrew: missing (rerun with --install to install it)';
  else /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; ensure_brew_path; fi
fi

if command -v brew >/dev/null 2>&1 && [ "$INSTALL" = true ]; then
  command -v node >/dev/null 2>&1 || brew install node
  if [ "$INSTALL_OLLAMA" = true ] && ! command -v ollama >/dev/null 2>&1; then brew install ollama; fi
  if [ "$INSTALL_MLX" = true ]; then
    brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
    MLX_PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
    MLX_VENV="$HOME/.haven-42-mlx"
    [ -x "$MLX_PYTHON" ] || { printf '%s\n' 'Homebrew Python 3.12 was not found after installation.' >&2; exit 1; }
    if [ -x "$MLX_VENV/bin/python" ] && ! "$MLX_VENV/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
      backup_path="$MLX_VENV.incompatible-python-$(date '+%Y%m%d-%H%M%S')"
      printf 'Existing MLX virtual environment uses an unsupported Python version; preserving it at %s\n' "$backup_path"
      mv "$MLX_VENV" "$backup_path"
    fi
    [ -x "$MLX_VENV/bin/python" ] || "$MLX_PYTHON" -m venv "$MLX_VENV"
    "$MLX_VENV/bin/python" -m pip install --upgrade pip mlx-lm
  fi
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
  printf '%s\n' 'MLX runtime: not detected (rerun with --install --with-mlx to install it)'
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
  printf '%s\n' 'Next: rerun with --install --with-ollama when you are ready to install Ollama.'
fi

if [ -x "$MLX_VENV/bin/mlx_lm.server" ]; then
  printf '%s\n' 'MLX note: serve models only on 127.0.0.1 and validate endpoint and tool behavior before using an agent surface.'
fi
