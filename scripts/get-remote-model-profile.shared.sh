#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_HOST=""
REMOTE_USER=""
REMOTE_PORT="22"
IDENTITY_FILE=""
REMOTE_PLATFORM="Linux"
OUTPUT_PATH=""
TIMEOUT_SECONDS="60"
ALLOW_INTERACTIVE_SSH=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --remote-host|-RemoteHost)
      REMOTE_HOST="$2"
      shift 2
      ;;
    --remote-user|-RemoteUser)
      REMOTE_USER="$2"
      shift 2
      ;;
    --remote-port|-RemotePort)
      REMOTE_PORT="$2"
      shift 2
      ;;
    --identity-file|-IdentityFile)
      IDENTITY_FILE="$2"
      shift 2
      ;;
    --remote-platform|-RemotePlatform)
      REMOTE_PLATFORM="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --timeout-seconds|-TimeoutSeconds)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --allow-interactive-ssh|-AllowInteractiveSsh)
      ALLOW_INTERACTIVE_SSH=true
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$REMOTE_HOST" ]; then
  printf 'RemoteHost is required. Use --remote-host <host>.\n' >&2
  exit 1
fi

printf '[1/6] Checking local SSH tools...\n' >&2
if ! command -v ssh >/dev/null 2>&1; then
  printf 'ssh is required. Install an OpenSSH client and try again.\n' >&2
  exit 1
fi

if [ "$ALLOW_INTERACTIVE_SSH" = true ] && ! command -v scp >/dev/null 2>&1; then
  printf 'scp is required for interactive SSH mode. Install an OpenSSH client and try again.\n' >&2
  exit 1
fi

case "$REMOTE_PLATFORM" in
  Linux|linux)
    PROFILE_SCRIPT="$SCRIPT_DIR/get-local-model-profile.linux.sh"
    ;;
  macOS|macos|darwin)
    PROFILE_SCRIPT="$SCRIPT_DIR/get-local-model-profile.macos.sh"
    ;;
  *)
    printf 'Unsupported remote platform: %s\n' "$REMOTE_PLATFORM" >&2
    exit 1
    ;;
esac

printf '[2/6] Selected %s profile script: %s\n' "$REMOTE_PLATFORM" "$(basename "$PROFILE_SCRIPT")" >&2
if [ ! -f "$PROFILE_SCRIPT" ]; then
  printf 'Profile script not found: %s\n' "$PROFILE_SCRIPT" >&2
  exit 1
fi

TARGET="$REMOTE_HOST"
if [ -n "$REMOTE_USER" ]; then
  TARGET="$REMOTE_USER@$REMOTE_HOST"
fi

SSH_ARGS=(-p "$REMOTE_PORT" -o "ConnectTimeout=$TIMEOUT_SECONDS" -o "ServerAliveInterval=15" -o "ServerAliveCountMax=2")
if [ "$ALLOW_INTERACTIVE_SSH" != true ]; then
  SSH_ARGS+=(-o BatchMode=yes)
fi
if [ -n "$IDENTITY_FILE" ]; then
  SSH_ARGS+=(-i "$IDENTITY_FILE")
fi

if command -v timeout >/dev/null 2>&1; then
  TIMEOUT_CMD=(timeout "$TIMEOUT_SECONDS")
else
  TIMEOUT_CMD=()
fi

printf '[3/6] Preparing remote profile collection for %s on port %s...\n' "$TARGET" "$REMOTE_PORT" >&2

if [ "$ALLOW_INTERACTIVE_SSH" = true ]; then
  printf '[4/6] Interactive SSH mode enabled. Uploading a temporary profiler with scp; enter the SSH password if prompted.\n' >&2
  REMOTE_SCRIPT_PATH="/tmp/local-engineering-agent-profile-$(date +%s)-$$.sh"
  SCP_ARGS=()
  for arg in "${SSH_ARGS[@]}"; do
    if [ "$arg" = "-p" ]; then
      SCP_ARGS+=(-P)
    else
      SCP_ARGS+=("$arg")
    fi
  done
  printf '[4/6] Upload target: %s\n' "$REMOTE_SCRIPT_PATH" >&2
  "${TIMEOUT_CMD[@]}" scp "${SCP_ARGS[@]}" "$PROFILE_SCRIPT" "$TARGET:$REMOTE_SCRIPT_PATH"
  if [ -n "$OUTPUT_PATH" ]; then
    mkdir -p "$(dirname "$OUTPUT_PATH")"
    printf '[5/6] Running remote GPU/CPU detection; enter the SSH password again if prompted.\n' >&2
    "${TIMEOUT_CMD[@]}" ssh "${SSH_ARGS[@]}" "$TARGET" "bash '$REMOTE_SCRIPT_PATH' --json; status=\$?; rm -f '$REMOTE_SCRIPT_PATH'; exit \$status" > "$OUTPUT_PATH"
    printf '[6/6] Validating remote profile JSON...\n' >&2
    python3 -m json.tool "$OUTPUT_PATH" >/dev/null
    printf '[6/6] Remote model profile written to %s\n' "$OUTPUT_PATH"
  else
    printf '[5/6] Running remote GPU/CPU detection; enter the SSH password again if prompted.\n' >&2
    "${TIMEOUT_CMD[@]}" ssh "${SSH_ARGS[@]}" "$TARGET" "bash '$REMOTE_SCRIPT_PATH' --json; status=\$?; rm -f '$REMOTE_SCRIPT_PATH'; exit \$status"
  fi
else
  printf '[4/6] Non-interactive SSH mode enabled. Streaming the profiler over SSH stdin; key-based SSH must already work.\n' >&2
  SSH_STREAM_ARGS=(-T "${SSH_ARGS[@]}")
  if [ -n "$OUTPUT_PATH" ]; then
    mkdir -p "$(dirname "$OUTPUT_PATH")"
    printf '[5/6] Running remote GPU/CPU detection...\n' >&2
    "${TIMEOUT_CMD[@]}" ssh "${SSH_STREAM_ARGS[@]}" "$TARGET" 'bash -s -- --json' < "$PROFILE_SCRIPT" > "$OUTPUT_PATH"
    printf '[6/6] Validating remote profile JSON...\n' >&2
    python3 -m json.tool "$OUTPUT_PATH" >/dev/null
    printf '[6/6] Remote model profile written to %s\n' "$OUTPUT_PATH"
  else
    printf '[5/6] Running remote GPU/CPU detection...\n' >&2
    "${TIMEOUT_CMD[@]}" ssh "${SSH_STREAM_ARGS[@]}" "$TARGET" 'bash -s -- --json' < "$PROFILE_SCRIPT"
  fi
fi


