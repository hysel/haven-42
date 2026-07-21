#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WIKI_PATH="${REPO_ROOT}.wiki"
CHECK=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --wiki-path) WIKI_PATH="$2"; shift 2 ;;
    --check) CHECK=1; shift ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

[ -d "$WIKI_PATH" ] || { printf 'Wiki directory does not exist: %s\n' "$WIKI_PATH" >&2; exit 1; }
MAP_PATH="$REPO_ROOT/config/wiki-sync.tsv"
RETIRED_PATH="$REPO_ROOT/config/wiki-retired-pages.txt"
DIFFERENCES=0
ENTRY_COUNT=0
SIDEBAR_TEMP="$(mktemp)"
trap 'rm -f "$SIDEBAR_TEMP"' EXIT
printf '%s\n' '- [Home](Home)' > "$SIDEBAR_TEMP"

while IFS=$'\t' read -r source page title; do
  source="${source%$'\r'}"; page="${page%$'\r'}"; title="${title%$'\r'}"
  [ "$source" != "source" ] || continue
  [ -n "$source" ] || continue
  ENTRY_COUNT=$((ENTRY_COUNT + 1))
  [ -f "$REPO_ROOT/$source" ] || { printf 'Mapped wiki source does not exist: %s\n' "$source" >&2; exit 1; }
  if ! cmp -s "$REPO_ROOT/$source" "$WIKI_PATH/$page"; then
    DIFFERENCES=1
    if [ "$CHECK" -eq 0 ]; then
      cp "$REPO_ROOT/$source" "$WIKI_PATH/$page"
      printf 'SYNC %s\n' "$page"
    fi
  fi
  if [ "$page" != "Home.md" ]; then
    printf -- '- [%s](%s)\n' "$title" "${page%.md}" >> "$SIDEBAR_TEMP"
  fi
done < "$MAP_PATH"

if ! cmp -s "$SIDEBAR_TEMP" "$WIKI_PATH/_Sidebar.md"; then
  DIFFERENCES=1
  if [ "$CHECK" -eq 0 ]; then
    cp "$SIDEBAR_TEMP" "$WIKI_PATH/_Sidebar.md"
    printf 'SYNC _Sidebar.md\n'
  fi
fi

while IFS= read -r retired_page || [ -n "$retired_page" ]; do
  retired_page="${retired_page%$'\r'}"
  [ -n "$retired_page" ] || continue
  if [ -e "$WIKI_PATH/$retired_page" ]; then
    DIFFERENCES=1
    if [ "$CHECK" -eq 0 ]; then
      rm -f "$WIKI_PATH/$retired_page"
      printf 'REMOVE %s\n' "$retired_page"
    fi
  fi
done < "$RETIRED_PATH"

if [ "$CHECK" -eq 1 ] && [ "$DIFFERENCES" -ne 0 ]; then
  printf 'Wiki is out of date. Run the platform sync-wiki script and commit the wiki repository.\n' >&2
  exit 1
fi
if [ "$CHECK" -eq 1 ]; then
  printf 'Wiki synchronization check passed for %s mapped pages.\n' "$ENTRY_COUNT"
else
  printf 'Wiki synchronization completed for %s mapped pages.\n' "$ENTRY_COUNT"
fi
