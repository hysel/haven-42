#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WIKI_PATH="${REPO_ROOT}.wiki"
CHECK=0

print_usage() {
  cat <<'EOF'
Usage: sync-wiki.shared.sh [--wiki-path PATH] [--check]

Synchronize mapped repository documentation to the separate GitHub wiki clone.

Options:
  --wiki-path PATH  Wiki clone path; defaults to the sibling repository.
  --check           Report drift without modifying the wiki.
  -h, --help        Show this help text.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --wiki-path) WIKI_PATH="$2"; shift 2 ;;
    --check) CHECK=1; shift ;;
    -h|--help) print_usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

[ -d "$WIKI_PATH" ] || { printf 'Wiki directory does not exist: %s\n' "$WIKI_PATH" >&2; exit 1; }
MAP_PATH="$REPO_ROOT/config/wiki-sync.tsv"
NAVIGATION_PATH="$REPO_ROOT/config/wiki-navigation.tsv"
RETIRED_PATH="$REPO_ROOT/config/wiki-retired-pages.txt"
DIFFERENCES=0
ENTRY_COUNT=0
NAVIGATION_COUNT=0
SIDEBAR_TEMP="$(mktemp)"
MAPPED_TEMP="$(mktemp)"
LINKS_TEMP="$(mktemp)"
RENDERED_TEMP="$(mktemp)"
trap 'rm -f "$SIDEBAR_TEMP" "$MAPPED_TEMP" "$LINKS_TEMP" "$RENDERED_TEMP"' EXIT
printf '%s\n' '- [Home](Home)' > "$SIDEBAR_TEMP"

while IFS=$'\t' read -r source page title; do
  source="${source%$'\r'}"; page="${page%$'\r'}"; title="${title%$'\r'}"
  [ "$source" != "source" ] || continue
  [ -n "$source" ] || continue
  case "$source" in /*|../*|*/../*|*'/..') printf 'Mapped wiki source escapes the repository: %s\n' "$source" >&2; exit 1 ;; esac
  case "$page" in */*|*'\'*|.*|*[!A-Za-z0-9._-]*|*.md.md) printf 'Invalid mapped wiki page: %s\n' "$page" >&2; exit 1 ;; esac
  case "$page" in *.md) ;; *) printf 'Mapped wiki page must be Markdown: %s\n' "$page" >&2; exit 1 ;; esac
  if grep -Fqx "$page" "$MAPPED_TEMP"; then
    printf 'Duplicate mapped wiki page: %s\n' "$page" >&2
    exit 1
  fi
  printf '%s\n' "$page" >> "$MAPPED_TEMP"
  ENTRY_COUNT=$((ENTRY_COUNT + 1))
  [ -f "$REPO_ROOT/$source" ] || { printf 'Mapped wiki source does not exist: %s\n' "$source" >&2; exit 1; }
done < "$MAP_PATH"

while IFS=$'\t' read -r source page title; do
  source="${source%$'\r'}"; page="${page%$'\r'}"; title="${title%$'\r'}"
  [ "$source" != "source" ] || continue
  [ -n "$source" ] || continue
  h1_count="$(grep -c '^# [^#]' "$REPO_ROOT/$source" || true)"
  [ "$h1_count" -eq 1 ] || { printf 'Mapped wiki source must contain exactly one level-one heading: %s\n' "$source" >&2; exit 1; }
  fence_count="$(grep -c '^```' "$REPO_ROOT/$source" || true)"
  [ $((fence_count % 2)) -eq 0 ] || { printf 'Mapped wiki source contains an unmatched code fence: %s\n' "$source" >&2; exit 1; }
  case "${source##*/}" in
    wiki-*.md)
      last_byte="$(tail -c 1 "$REPO_ROOT/$source" | od -An -t u1 | tr -d '[:space:]')"
      [ "$last_byte" = "10" ] && awk 'END { exit(NR == 0 || $0 == "") }' "$REPO_ROOT/$source" || { printf 'Mapped wiki source must end with exactly one newline: %s\n' "$source" >&2; exit 1; }
      if grep -Eqi '<br[[:space:]]*/?>' "$REPO_ROOT/$source"; then printf 'User-facing wiki source contains an HTML line break: %s\n' "$source" >&2; exit 1; fi
      ;;
  esac
  if grep -Eq '^\|.*\[\[' "$REPO_ROOT/$source"; then printf 'Wiki-style link inside a Markdown table must use standard Markdown syntax: %s\n' "$source" >&2; exit 1; fi

  case "$page" in
    Eng-*.md) ;;
    *)
      grep -oE '\[\[[^]]+\]\]' "$REPO_ROOT/$source" > "$LINKS_TEMP" || true
      while IFS= read -r link; do
        target="${link#'[['}"; target="${target%']]'}"; target="${target##*|}"; target="${target%%#*}"
        grep -Fqxi -- "$target.md" "$MAPPED_TEMP" || { printf 'Broken wiki link in %s: %s\n' "$source" "$target" >&2; exit 1; }
      done < "$LINKS_TEMP"

      grep -oE '\]\([^)]+\)' "$REPO_ROOT/$source" > "$LINKS_TEMP" || true
      while IFS= read -r link; do
        target="${link#']('}"; target="${target%')'}"; target="${target%%#*}"
        case "$target" in *:*) continue ;; esac
        case "$target" in */*|*'\'*) printf 'Path-like relative Markdown link in %s: %s\n' "$source" "$target" >&2; exit 1 ;; esac
        target="${target##*/}"
        target="${target%.md}"
        grep -Fqxi -- "$target.md" "$MAPPED_TEMP" || { printf 'Broken relative Markdown link in %s: %s\n' "$source" "$target" >&2; exit 1; }
      done < "$LINKS_TEMP"
      ;;
  esac
done < "$MAP_PATH"

while IFS=$'\t' read -r source page title; do
  source="${source%$'\r'}"; page="${page%$'\r'}"; title="${title%$'\r'}"
  [ "$source" != "source" ] || continue
  [ -n "$source" ] || continue
  case "$page" in
    Eng-*.md)
      printf '# %s\n\n> **Internal engineering page:** This is an internal engineering page — see [Home](Home) if you'"'"'re trying to install or use Haven 42.\n\nThe canonical document is [%s](https://github.com/hysel/haven-42/blob/main/%s).\n' "$title" "$source" "$source" > "$RENDERED_TEMP"
      ;;
    *) cp "$REPO_ROOT/$source" "$RENDERED_TEMP" ;;
  esac
  if ! cmp -s "$RENDERED_TEMP" "$WIKI_PATH/$page"; then
    DIFFERENCES=1
    if [ "$CHECK" -eq 0 ]; then
      cp "$RENDERED_TEMP" "$WIKI_PATH/$page"
      printf 'SYNC %s\n' "$page"
    fi
  fi
done < "$MAP_PATH"

CURRENT_SECTION=''
NAVIGATION_PAGES_TEMP="$(mktemp)"
trap 'rm -f "$SIDEBAR_TEMP" "$MAPPED_TEMP" "$LINKS_TEMP" "$RENDERED_TEMP" "$NAVIGATION_PAGES_TEMP"' EXIT
while IFS=$'\t' read -r section page title; do
  section="${section%$'\r'}"; page="${page%$'\r'}"; title="${title%$'\r'}"
  [ "$section" != "section" ] || continue
  [ -n "$section" ] && [ -n "$page" ] && [ -n "$title" ] || { printf 'Invalid empty wiki navigation entry.\n' >&2; exit 1; }
  case "$section$title" in *'['*|*']'*|*'<'*|*'>'*|*'`'*|*'#'*|*'|'*) printf 'Wiki navigation text contains markup syntax.\n' >&2; exit 1 ;; esac
  grep -Fqx "$page" "$MAPPED_TEMP" || { printf 'Navigation page is not mapped: %s\n' "$page" >&2; exit 1; }
  if grep -Fqx "$page" "$NAVIGATION_PAGES_TEMP"; then
    printf 'Duplicate wiki navigation page: %s\n' "$page" >&2
    exit 1
  fi
  printf '%s\n' "$page" >> "$NAVIGATION_PAGES_TEMP"
  if [ "$section" != "$CURRENT_SECTION" ]; then
    printf '\n**%s**\n' "$section" >> "$SIDEBAR_TEMP"
    CURRENT_SECTION="$section"
  fi
  printf -- '- [%s](%s)\n' "$title" "${page%.md}" >> "$SIDEBAR_TEMP"
  NAVIGATION_COUNT=$((NAVIGATION_COUNT + 1))
done < "$NAVIGATION_PATH"
[ "$NAVIGATION_COUNT" -ge 10 ] && [ "$NAVIGATION_COUNT" -le 25 ] || { printf 'Wiki navigation must contain between 10 and 25 primary links.\n' >&2; exit 1; }

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
  printf 'Wiki synchronization check passed for %s mapped pages and %s navigation links.\n' "$ENTRY_COUNT" "$NAVIGATION_COUNT"
else
  printf 'Wiki synchronization completed for %s mapped pages and %s navigation links.\n' "$ENTRY_COUNT" "$NAVIGATION_COUNT"
fi
