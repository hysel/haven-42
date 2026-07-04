#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_CONTINUE="$REPO_ROOT/.continue"
TARGET_REPO=""
DRY_RUN=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-repo|-TargetRepo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --dry-run|-DryRun)
      DRY_RUN=true
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$TARGET_REPO" ]; then
  printf 'Target repository is required. Use --target-repo <path>.\n' >&2
  exit 1
fi

if [ ! -d "$SOURCE_CONTINUE" ]; then
  printf 'Source .continue folder does not exist: %s\n' "$SOURCE_CONTINUE" >&2
  exit 1
fi

if [ ! -d "$TARGET_REPO" ]; then
  printf 'Target repository path does not exist: %s\n' "$TARGET_REPO" >&2
  exit 1
fi

REPO_ROOT_RESOLVED="$(cd "$REPO_ROOT" && pwd)"
TARGET_RESOLVED="$(cd "$TARGET_REPO" && pwd)"

if [ "$REPO_ROOT_RESOLVED" = "$TARGET_RESOLVED" ]; then
  printf 'Target repository must be different from this pack repository.\n' >&2
  exit 1
fi

TARGET_CONTINUE="$TARGET_RESOLVED/.continue"
BACKUP_CONTINUE="$TARGET_RESOLVED/.continue.backup-$(date '+%Y%m%d-%H%M%S')"

printf 'Installing Continue pack into %s\n' "$TARGET_RESOLVED"

if [ "$DRY_RUN" = true ]; then
  printf 'Dry run only. No files will be changed.\n'
  if [ -d "$TARGET_CONTINUE" ]; then
    printf 'Would back up existing .continue to %s\n' "$BACKUP_CONTINUE"
  fi
  printf 'Would copy .continue files excluding config.local*.yaml.\n'
  exit 0
fi

if [ -d "$TARGET_CONTINUE" ]; then
  mv "$TARGET_CONTINUE" "$BACKUP_CONTINUE"
  printf 'Backed up existing .continue to %s\n' "$BACKUP_CONTINUE"
fi

mkdir -p "$TARGET_CONTINUE"

while IFS= read -r source_file; do
  relative="${source_file#$SOURCE_CONTINUE/}"
  case "$relative" in
    config.local*.yaml|config.local*.yml) continue ;;
  esac

  destination="$TARGET_CONTINUE/$relative"
  mkdir -p "$(dirname "$destination")"
  cp "$source_file" "$destination"
done < <(find "$SOURCE_CONTINUE" -type f)

if [ ! -f "$TARGET_CONTINUE/config.yaml" ]; then
  printf 'Installed config is missing: %s\n' "$TARGET_CONTINUE/config.yaml" >&2
  exit 1
fi

CONFIG_CONTENT="$(cat "$TARGET_CONTINUE/config.yaml")"
FILE_REFS="$(printf '%s\n' "$CONFIG_CONTENT" | grep -Eo 'file://\./[^[:space:]]+' | sed 's#file://./##' || true)"

while IFS= read -r ref; do
  [ -z "$ref" ] && continue
  if [ ! -e "$TARGET_CONTINUE/$ref" ]; then
    printf 'Installed file reference does not resolve: %s\n' "$ref" >&2
    exit 1
  fi
done <<EOF
$FILE_REFS
EOF

printf 'Install complete.\n'
