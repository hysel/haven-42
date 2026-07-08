#!/usr/bin/env bash
set -euo pipefail

TARGET_REPO="$PWD"
OUTPUT_PATH=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-repo|-TargetRepo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ ! -d "$TARGET_REPO" ]; then
  printf 'Target repository path does not exist: %s\n' "$TARGET_REPO" >&2
  exit 1
fi

TARGET_REPO="$(cd "$TARGET_REPO" && pwd)"
if [ -z "$OUTPUT_PATH" ]; then
  OUTPUT_PATH="$TARGET_REPO/runtime-context.md"
fi

{
  printf '# Runtime Repository Context\n\n'
  printf 'Generated: %s\n\n' "$(date '+%Y-%m-%d %H:%M')"
  printf 'Target repository: sanitized local path\n\n'
  printf '## File Tree\n\n'
  find "$TARGET_REPO" \
    -path "$TARGET_REPO/.git" -prune -o \
    -path "$TARGET_REPO/bin" -prune -o \
    -path "$TARGET_REPO/obj" -prune -o \
    -path "$TARGET_REPO/node_modules" -prune -o \
    -path "$TARGET_REPO/runtime-validation-output" -prune -o \
    -type f -print |
    sed "s#^$TARGET_REPO/##" |
    sort |
    head -n 200

  printf '\n## Top-Level Documentation Excerpts\n\n'
  for doc in README.md SAMPLE-METADATA.md PROJECT.md ARCHITECTURE.md STYLEGUIDE.md ROADMAP.md TODO.md AI.md; do
    if [ -f "$TARGET_REPO/$doc" ]; then
      printf '### %s\n\n' "$doc"
      sed -n '1,80p' "$TARGET_REPO/$doc"
      printf '\n\n'
    fi
  done

  printf '## Project Files\n\n'
  find "$TARGET_REPO" \
    -path "$TARGET_REPO/.git" -prune -o \
    -path "$TARGET_REPO/bin" -prune -o \
    -path "$TARGET_REPO/obj" -prune -o \
    -type f \( -name '*.csproj' -o -name '*.sln' -o -name '*.slnx' -o -name '*.fsproj' -o -name '*.vbproj' -o -name 'package.json' -o -name 'package-lock.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'pyproject.toml' -o -name 'requirements*.txt' -o -name 'pom.xml' -o -name 'build.gradle' -o -name 'settings.gradle' -o -name 'gradle.properties' -o -name 'go.mod' -o -name 'go.sum' -o -name 'Cargo.toml' -o -name 'Cargo.lock' \) -print |
    sed "s#^$TARGET_REPO/##" |
    sort

  printf '\n## Project File Excerpts\n\n'
  find "$TARGET_REPO" \
    -path "$TARGET_REPO/.git" -prune -o \
    -path "$TARGET_REPO/bin" -prune -o \
    -path "$TARGET_REPO/obj" -prune -o \
    -type f \( -name '*.csproj' -o -name '*.fsproj' -o -name '*.vbproj' -o -name 'package.json' -o -name 'package-lock.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'pyproject.toml' -o -name 'requirements*.txt' -o -name 'pom.xml' -o -name 'build.gradle' -o -name 'settings.gradle' -o -name 'gradle.properties' -o -name 'go.mod' -o -name 'go.sum' -o -name 'Cargo.toml' -o -name 'Cargo.lock' -o -name 'Dockerfile' -o -name 'docker-compose*.yml' -o -name 'compose*.yml' -o -name 'appsettings*.json' -o -name 'tsconfig*.json' -o -name 'vite.config.*' -o -name 'webpack.config.*' -o -name 'jest.config.*' -o -name 'vitest.config.*' -o -name '*.tf' -o -name '*.tfvars' -o -name '*.yaml' -o -name '*.yml' -o -name '*.sql' \) -print |
    sort |
    while IFS= read -r project_file; do
      relative_project_file="${project_file#"$TARGET_REPO/"}"
      printf '### %s\n\n' "$relative_project_file"
      printf '```text\n'
      sed -n '1,120p' "$project_file"
      printf '\n```\n\n'
    done

  printf '\n## Selected Source And Test Files\n\n'
  find "$TARGET_REPO" \
    -path "$TARGET_REPO/.git" -prune -o \
    -path "$TARGET_REPO/bin" -prune -o \
    -path "$TARGET_REPO/obj" -prune -o \
    -path "$TARGET_REPO/node_modules" -prune -o \
    -type f \( -name '*.cs' -o -name '*.fs' -o -name '*.js' -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' -o -name '*.py' -o -name '*.java' -o -name '*.go' -o -name '*.rs' \) -print |
    sed "s#^$TARGET_REPO/##" |
    sort |
    head -n 120
} > "$OUTPUT_PATH"

printf 'Runtime context written to %s\n' "$OUTPUT_PATH"
