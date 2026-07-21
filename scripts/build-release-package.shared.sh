#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION=""
OUTPUT_DIR="dist"
DRY_RUN=0
ALLOW_DIRTY=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --version|-Version)
      VERSION="$2"
      shift 2
      ;;
    --output-directory|-OutputDirectory)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --dry-run|-DryRun)
      DRY_RUN=1
      shift
      ;;
    --allow-dirty|-AllowDirty)
      ALLOW_DIRTY=1
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

read_pack_version() {
  if [ -n "$VERSION" ]; then
    printf '%s\n' "${VERSION#v}"
    return 0
  fi

  sed -n 's/^version:[[:space:]]*//p' "$REPO_ROOT/.continue/config.yaml" | head -n 1
}

assert_clean_git_tree() {
  if [ "$ALLOW_DIRTY" -eq 1 ]; then
    return 0
  fi

  if [ -n "$(git -C "$REPO_ROOT" status --short)" ]; then
    printf 'Working tree has uncommitted changes. Commit or stash before packaging, or use --allow-dirty for local packaging tests.\n' >&2
    exit 1
  fi
}

PACK_VERSION="$(read_pack_version)"
if ! printf '%s' "$PACK_VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([-.][0-9A-Za-z.-]+)?$'; then
  printf 'Version %s is not a supported semantic version.\n' "$PACK_VERSION" >&2
  exit 1
fi

PACKAGE_NAME="haven-42-$PACK_VERSION"
case "$OUTPUT_DIR" in
  /*) OUTPUT_ROOT="$OUTPUT_DIR" ;;
  *) OUTPUT_ROOT="$REPO_ROOT/$OUTPUT_DIR" ;;
esac

ARCHIVE_PATH="$OUTPUT_ROOT/$PACKAGE_NAME.tar.gz"
CHECKSUM_PATH="$OUTPUT_ROOT/$PACKAGE_NAME.sha256"
MANIFEST_PATH="$OUTPUT_ROOT/$PACKAGE_NAME.manifest.txt"

PACKAGE_FILES="$(
  git -C "$REPO_ROOT" ls-files |
    grep -Ev '^(\.git/|\.vscode/|runtime-validation-output/|dist/|\.continue/config\.local.*|\.continue\.backup-)' |
    grep -Ev '(^|/)config\.local\.yaml$|(^|/)\.env(\.|$)?|(^|/)secrets?(\.|/|$)|(^|/)token(s)?(\.|/|$)' |
    sort -u
)"
FILE_COUNT="$(printf '%s\n' "$PACKAGE_FILES" | sed '/^$/d' | wc -l | tr -d ' ')"

if [ "$FILE_COUNT" -eq 0 ]; then
  printf 'No package files were selected.\n' >&2
  exit 1
fi

printf 'Release package plan\n'
printf 'Version: %s\n' "$PACK_VERSION"
printf 'Archive: %s\n' "$ARCHIVE_PATH"
printf 'Checksum: %s\n' "$CHECKSUM_PATH"
printf 'Manifest: %s\n' "$MANIFEST_PATH"
printf 'Files: %s\n' "$FILE_COUNT"
printf 'Excluded: .git, .vscode, runtime-validation-output, dist, local configs, backups, env/secrets/token files\n'

if [ "$DRY_RUN" -eq 1 ]; then
  printf 'Dry run only. No release files were written.\n'
  exit 0
fi

assert_clean_git_tree
mkdir -p "$OUTPUT_ROOT"
TEMP_ROOT="$(mktemp -d)"
PACKAGE_ROOT="$TEMP_ROOT/$PACKAGE_NAME"
mkdir -p "$PACKAGE_ROOT"

cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT

printf '%s\n' "$PACKAGE_FILES" | while IFS= read -r file; do
  [ -n "$file" ] || continue
  mkdir -p "$PACKAGE_ROOT/$(dirname "$file")"
  cp "$REPO_ROOT/$file" "$PACKAGE_ROOT/$file"
done

rm -f "$ARCHIVE_PATH" "$CHECKSUM_PATH" "$MANIFEST_PATH"
tar -C "$TEMP_ROOT" -czf "$ARCHIVE_PATH" "$PACKAGE_NAME"

if command -v sha256sum >/dev/null 2>&1; then
  checksum="$(sha256sum "$ARCHIVE_PATH" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
  checksum="$(shasum -a 256 "$ARCHIVE_PATH" | awk '{print $1}')"
else
  printf 'Neither sha256sum nor shasum is available for checksum generation.\n' >&2
  exit 1
fi

printf '%s  %s\n' "$checksum" "$(basename "$ARCHIVE_PATH")" > "$CHECKSUM_PATH"
printf '%s\n' "$PACKAGE_FILES" > "$MANIFEST_PATH"

printf 'Release archive written: %s\n' "$ARCHIVE_PATH"
printf 'Checksum written: %s\n' "$CHECKSUM_PATH"
printf 'Manifest written: %s\n' "$MANIFEST_PATH"
