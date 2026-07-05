#!/usr/bin/env bash
set -uo pipefail

EXPECTED_VERSION="0.2.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FAILED=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --expected-version|-ExpectedVersion)
      EXPECTED_VERSION="$2"
      shift 2
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

pass() {
  printf 'PASS %s\n' "$1"
}

fail() {
  printf 'FAIL %s\n' "$1" >&2
  FAILED=1
}

require_file() {
  if [ -e "$REPO_ROOT/$1" ]; then
    pass "required file exists: $1"
  else
    fail "required file exists: $1"
  fi
}

CONFIG_PATH="$REPO_ROOT/.continue/config.yaml"

if [ -f "$CONFIG_PATH" ]; then
  pass ".continue/config.yaml exists"
else
  fail ".continue/config.yaml exists"
fi

CONFIG_CONTENT="$(cat "$CONFIG_PATH" 2>/dev/null || true)"

if printf '%s\n' "$CONFIG_CONTENT" | grep -Eq "^version:[[:space:]]+$EXPECTED_VERSION[[:space:]]*$"; then
  pass "config version is $EXPECTED_VERSION"
else
  fail "config version is $EXPECTED_VERSION"
fi

if printf '%s\n' "$CONFIG_CONTENT" | grep -Eq '^schema:[[:space:]]+v1[[:space:]]*$'; then
  pass "config schema is v1"
else
  fail "config schema is v1"
fi

if printf '%s\n' "$CONFIG_CONTENT" | grep -Eq '^mcpServers:[[:space:]]+\[\][[:space:]]*$'; then
  pass "default MCP server list is empty"
else
  fail "default MCP server list is empty"
fi

FILE_REFS="$(printf '%s\n' "$CONFIG_CONTENT" | grep -Eo 'file://\./[^[:space:]]+' | sed 's#file://./##' || true)"

while IFS= read -r ref; do
  [ -z "$ref" ] && continue
  if [ -e "$REPO_ROOT/.continue/$ref" ]; then
    pass "referenced file exists: .continue/$ref"
  else
    fail "referenced file exists: .continue/$ref"
  fi
done <<EOF
$FILE_REFS
EOF

for prompt_path in "$REPO_ROOT"/.continue/prompts/*.md; do
  [ -e "$prompt_path" ] || continue
  prompt_file="$(basename "$prompt_path")"
  prompt_name="${prompt_file%.md}"
  relative_prompt_path="prompts/$prompt_file"
  prompt_content="$(cat "$prompt_path")"

  if printf '%s' "$prompt_file" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*\.md$'; then
    pass "prompt filename is kebab-case: .continue/$relative_prompt_path"
  else
    fail "prompt filename is kebab-case: .continue/$relative_prompt_path"
  fi

  if grep -Fxq "$relative_prompt_path" <<< "$FILE_REFS"; then
    pass "prompt is referenced in config: .continue/$relative_prompt_path"
  else
    fail "prompt is referenced in config: .continue/$relative_prompt_path"
  fi

  if grep -Eq '^---' <<< "$prompt_content"; then
    pass "prompt frontmatter starts on first line: .continue/$relative_prompt_path"
  else
    fail "prompt frontmatter starts on first line: .continue/$relative_prompt_path"
  fi

  if grep -Eq "^name:[[:space:]]+['\"]?$prompt_name['\"]?[[:space:]]*$" <<< "$prompt_content"; then
    pass "prompt name matches filename: .continue/$relative_prompt_path"
  else
    fail "prompt name matches filename: .continue/$relative_prompt_path"
  fi

  if grep -Eq '^description:[[:space:]]+.+$' <<< "$prompt_content"; then
    pass "prompt description is present: .continue/$relative_prompt_path"
  else
    fail "prompt description is present: .continue/$relative_prompt_path"
  fi

  if grep -Eq '^invokable:[[:space:]]+true[[:space:]]*$' <<< "$prompt_content"; then
    pass "prompt is invokable: .continue/$relative_prompt_path"
  else
    fail "prompt is invokable: .continue/$relative_prompt_path"
  fi
done

REQUIRED_FILES=(
  "README.md"
  "PROJECT.md"
  "ARCHITECTURE.md"
  "STYLEGUIDE.md"
  "ROADMAP.md"
  "TODO.md"
  "AI.md"
  "DECISIONS.md"
  "CHANGELOG.md"
  "LICENSE"
  "CONTRIBUTING.md"
  "config/model-recommendations.tsv"
  "config/model-recommendations.mlx.tsv"
  "docs/release.md"
  "docs/compatibility.md"
  "docs/runtime-validation.md"
  "docs/editor-compatibility.md"
  "docs/prompt-quality.md"
  "docs/validation-checklists.md"
  "docs/troubleshooting.md"
  "docs/tool-use-modes.md"
  "docs/approved-tool-backed-changes.md"
  "docs/scoped-edits.md"
  "docs/local-config-safety.md"
  "docs/local-model-selection.md"
  "docs/online-model-discovery.md"
  "docs/multi-repository-validation.md"
  "docs/runtime-output-verification.md"
  "docs/agent-surface-options.md"
  "docs/language-support.md"
  "docs/sample-repository-factory.md"
  "docs/local-agent-model-testing.md"
  "docs/model-tool-use-validation.md"
  "docs/local-model-reliability.md"
  "docs/banned-output-patterns.md"
  "docs/mcp-options.md"
  "docs/mcp-setup.md"
  "docs/mcp-examples.md"
  "docs/sonarqube-review.md"
  "docs/sonarqube-integration-options.md"
  "scripts/generate-sample-repositories.ps1"
  "scripts/generate-sample-repositories.linux.sh"
  "scripts/generate-sample-repositories.macos.sh"
  "scripts/generate-sample-repositories.shared.sh"
  "scripts/generate-runtime-context.ps1"
  "scripts/generate-runtime-context.linux.sh"
  "scripts/generate-runtime-context.macos.sh"
  "scripts/generate-runtime-context.shared.sh"
  "scripts/install-continue-pack.ps1"
  "scripts/install-continue-pack.linux.sh"
  "scripts/install-continue-pack.macos.sh"
  "scripts/install-continue-pack.shared.sh"
  "scripts/install-validated-model.ps1"
  "scripts/install-validated-model.linux.sh"
  "scripts/install-validated-model.macos.sh"
  "scripts/install-validated-model.shared.sh"
  "scripts/run-runtime-validation.ps1"
  "scripts/run-runtime-validation.linux.sh"
  "scripts/run-runtime-validation.macos.sh"
  "scripts/run-runtime-validation.shared.sh"
  "scripts/verify-runtime-output.ps1"
  "scripts/verify-runtime-output.linux.sh"
  "scripts/verify-runtime-output.macos.sh"
  "scripts/verify-runtime-output.shared.sh"
  "scripts/test-pack.ps1"
  "scripts/test-pack.linux.sh"
  "scripts/test-pack.macos.sh"
  "scripts/test-pack.shared.sh"
  "scripts/validate-pack.ps1"
  "scripts/validate-pack.linux.sh"
  "scripts/validate-pack.macos.sh"
  "scripts/validate-pack.shared.sh"
  "scripts/get-local-model-profile.windows.ps1"
  "scripts/get-local-model-profile.linux.sh"
  "scripts/get-local-model-profile.macos.sh"
  "scripts/pull-local-agent-models.ps1"
  "scripts/pull-local-agent-models.linux.sh"
  "scripts/pull-local-agent-models.macos.sh"
  "scripts/pull-local-agent-models.shared.sh"
  "scripts/test-local-agent-models.ps1"
  "scripts/test-local-agent-models.linux.sh"
  "scripts/test-local-agent-models.macos.sh"
  "scripts/test-local-agent-models.shared.sh"
  ".continue/prompts/legacy-dotnet-dependency-migration.md"
  ".continue/templates/LegacyDotNetDependencyMigration.md"
  "examples/fixtures/implementation-planning-quality-input.md"
  "examples/fixtures/config-pack-review-input.md"
  "examples/fixtures/documentation-review-quality-input.md"
  "examples/fixtures/legacy-dependency-migration-input.md"
  "examples/fixtures/sonarqube-findings.md"
  "examples/fixtures/repository-context.md"
  "examples/fixtures/security-review-input.md"
  "examples/fixtures/performance-review-input.md"
  "examples/fixtures/release-readiness-input.md"
  "examples/fixtures/release-readiness-quality-input.md"
  "examples/editor-surface-validation.md"
  "examples/model-tool-use-validation.md"
  "examples/multi-repository-validation.md"
  ".github/workflows/validate-pack.yml"
)

for required in "${REQUIRED_FILES[@]}"; do
  require_file "$required"
done

PRIVATE_IP_PATTERN='(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})'
SECRET_PATTERN='(api[_-]?key|access[_-]?token|personal[_-]?access[_-]?token|password|secret)[[:space:]]*[:=][[:space:]]*["'\'']?[A-Za-z0-9_-]{16,}'

while IFS= read -r file; do
  rel="${file#$REPO_ROOT/}"
  case "$rel" in
    .git/*|runtime-validation-output/*|.continue/config.local*.yaml) continue ;;
  esac

  case "$file" in
    *.md|*.yaml|*.yml|*.ps1|*.sh|*.tsv|*.txt)
      content="$(cat "$file" 2>/dev/null || true)"
      if printf '%s\n' "$content" | grep -Eiq "$PRIVATE_IP_PATTERN"; then
        fail "no private IP address committed: $rel"
      fi
      if printf '%s\n' "$content" | grep -Eiq "$SECRET_PATTERN"; then
        fail "no likely secret committed: $rel"
      fi
      ;;
  esac
done < <(find "$REPO_ROOT" -type f)

if [ "$FAILED" -eq 0 ]; then
  printf 'Validation passed.\n'
  exit 0
fi

printf 'Validation failed.\n' >&2
exit 1
