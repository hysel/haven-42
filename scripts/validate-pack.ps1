param(
    [string]$ExpectedVersion = "0.2.0"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot ".continue/config.yaml"
$failed = $false

function Add-Failure {
    param([string]$Message)
    Write-Host "FAIL $Message" -ForegroundColor Red
    $script:failed = $true
}

function Add-Pass {
    param([string]$Message)
    Write-Host "PASS $Message" -ForegroundColor Green
}

if (-not (Test-Path -LiteralPath $configPath)) {
    Add-Failure ".continue/config.yaml exists"
} else {
    Add-Pass ".continue/config.yaml exists"
}

$config = Get-Content -LiteralPath $configPath -Raw

if ($config -match "(?m)^version:\s+$([regex]::Escape($ExpectedVersion))\s*$") {
    Add-Pass "config version is $ExpectedVersion"
} else {
    Add-Failure "config version is $ExpectedVersion"
}

if ($config -match "(?m)^schema:\s+v1\s*$") {
    Add-Pass "config schema is v1"
} else {
    Add-Failure "config schema is v1"
}

if ($config -match "(?m)^mcpServers:\s+\[\]\s*$") {
    Add-Pass "default MCP server list is empty"
} else {
    Add-Failure "default MCP server list is empty"
}

$fileRefs = [regex]::Matches($config, "file://\.\/([^`r`n]+)") | ForEach-Object {
    $_.Groups[1].Value.Trim()
}

foreach ($ref in $fileRefs) {
    $target = Join-Path (Join-Path $repoRoot ".continue") $ref
    if (Test-Path -LiteralPath $target) {
        Add-Pass "referenced file exists: .continue/$ref"
    } else {
        Add-Failure "referenced file exists: .continue/$ref"
    }
}

$promptDir = Join-Path $repoRoot ".continue/prompts"
$promptFiles = Get-ChildItem -LiteralPath $promptDir -Filter "*.md" -File
$configuredPromptRefs = $fileRefs | Where-Object { $_ -match "^prompts\/.+\.md$" }
$configuredPromptPaths = @{}

foreach ($ref in $configuredPromptRefs) {
    $configuredPromptPaths[$ref] = $true
}

foreach ($promptFile in $promptFiles) {
    $relativePromptPath = "prompts/$($promptFile.Name)"
    $promptName = [System.IO.Path]::GetFileNameWithoutExtension($promptFile.Name)
    $promptContent = Get-Content -LiteralPath $promptFile.FullName -Raw

    if ($promptFile.Name -match "^[a-z0-9]+(-[a-z0-9]+)*\.md$") {
        Add-Pass "prompt filename is kebab-case: .continue/$relativePromptPath"
    } else {
        Add-Failure "prompt filename is kebab-case: .continue/$relativePromptPath"
    }

    if ($configuredPromptPaths.ContainsKey($relativePromptPath)) {
        Add-Pass "prompt is referenced in config: .continue/$relativePromptPath"
    } else {
        Add-Failure "prompt is referenced in config: .continue/$relativePromptPath"
    }

    $frontmatterMatch = [regex]::Match($promptContent, "\A---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)")

    if ($frontmatterMatch.Success) {
        Add-Pass "prompt frontmatter starts on first line: .continue/$relativePromptPath"
        $frontmatter = $frontmatterMatch.Groups[1].Value

        $nameMatch = [regex]::Match($frontmatter, "(?m)^name:\s+(.+?)\s*$")
        if ($nameMatch.Success -and $nameMatch.Groups[1].Value.Trim("'""") -eq $promptName) {
            Add-Pass "prompt name matches filename: .continue/$relativePromptPath"
        } else {
            Add-Failure "prompt name matches filename: .continue/$relativePromptPath"
        }

        $descriptionMatch = [regex]::Match($frontmatter, "(?m)^description:\s+(.+?)\s*$")
        if ($descriptionMatch.Success -and $descriptionMatch.Groups[1].Value.Trim().Length -gt 0) {
            Add-Pass "prompt description is present: .continue/$relativePromptPath"
        } else {
            Add-Failure "prompt description is present: .continue/$relativePromptPath"
        }

        if ($frontmatter -match "(?m)^invokable:\s+true\s*$") {
            Add-Pass "prompt is invokable: .continue/$relativePromptPath"
        } else {
            Add-Failure "prompt is invokable: .continue/$relativePromptPath"
        }
    } else {
        Add-Failure "prompt frontmatter starts on first line: .continue/$relativePromptPath"
    }
}

$requiredFiles = @(
    "README.md",
    "PROJECT.md",
    "ARCHITECTURE.md",
    "STYLEGUIDE.md",
    "ROADMAP.md",
    "TODO.md",
    "AI.md",
    "DECISIONS.md",
    "CHANGELOG.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "config/model-recommendations.tsv",
    "config/model-recommendations.mlx.tsv",
    "config/evidence-catalog.tsv",
    "docs/release.md",
    "docs/evidence-catalog.md",
    "docs/hardware-aware-recommendations.md",
    "docs/compatibility.md",
    "docs/runtime-validation.md",
    "docs/editor-compatibility.md",
    "docs/prompt-quality.md",
    "docs/validation-checklists.md",
    "docs/troubleshooting.md",
    "docs/tool-use-modes.md",
    "docs/approved-tool-backed-changes.md",
    "docs/scoped-edits.md",
    "docs/local-config-safety.md",
    "docs/local-model-selection.md",
    "docs/online-model-discovery.md",
    "docs/multi-repository-validation.md",
    "docs/runtime-output-verification.md",
    "docs/agent-surface-options.md",
    "docs/language-support.md",
    "docs/project-detection.md",
    "docs/language-rule-packs.md",
    "docs/sample-repository-factory.md",
    "docs/local-agent-model-testing.md",
    "docs/model-tool-use-validation.md",
    "docs/local-model-reliability.md",
    "docs/banned-output-patterns.md",
    "docs/mcp-options.md",
    "docs/mcp-setup.md",
    "docs/mcp-examples.md",
    "docs/sonarqube-review.md",
    "docs/sonarqube-integration-options.md",
    "scripts/generate-sample-repositories.ps1",
    "scripts/generate-sample-repositories.linux.sh",
    "scripts/generate-sample-repositories.macos.sh",
    "scripts/generate-sample-repositories.shared.sh",
    "scripts/build-release-package.ps1",
    "scripts/build-release-package.linux.sh",
    "scripts/build-release-package.macos.sh",
    "scripts/recommend-local-agent-config.ps1",
    "scripts/recommend-local-agent-config.linux.sh",
    "scripts/recommend-local-agent-config.macos.sh",
    "scripts/recommend-local-agent-config.shared.sh",
    "scripts/build-release-package.shared.sh",
    "scripts/generate-runtime-context.ps1",
    "scripts/generate-runtime-context.linux.sh",
    "scripts/generate-runtime-context.macos.sh",
    "scripts/generate-runtime-context.shared.sh",
    "scripts/install-continue-pack.ps1",
    "scripts/install-git-hooks.ps1",
    "scripts/install-continue-pack.linux.sh",
    "scripts/install-continue-pack.macos.sh",
    "scripts/install-continue-pack.shared.sh",
    "scripts/install-validated-model.ps1",
    "scripts/install-validated-model.linux.sh",
    "scripts/install-validated-model.macos.sh",
    "scripts/install-validated-model.shared.sh",
    "scripts/run-runtime-validation.ps1",
    "scripts/run-runtime-validation.linux.sh",
    "scripts/run-runtime-validation.macos.sh",
    "scripts/run-runtime-validation.shared.sh",
    "scripts/verify-runtime-output.ps1",
    "scripts/verify-runtime-output.linux.sh",
    "scripts/verify-runtime-output.macos.sh",
    "scripts/verify-runtime-output.shared.sh",
    "scripts/test-pack.ps1",
    "scripts/validate-pack.linux.sh",
    "scripts/test-pack.linux.sh",
    "scripts/validate-pack.macos.sh",
    "scripts/test-pack.macos.sh",
    "scripts/test-pack.shared.sh",
    "scripts/validate-pack.shared.sh",
    "scripts/get-local-model-profile.windows.ps1",
    "scripts/get-local-model-profile.linux.sh",
    "scripts/get-local-model-profile.macos.sh",
    "scripts/discover-online-model-candidates.ps1",
    "scripts/discover-online-model-candidates.linux.sh",
    "scripts/discover-online-model-candidates.macos.sh",
    "scripts/discover-online-model-candidates.shared.sh",
    "scripts/pull-local-agent-models.ps1",
    "scripts/pull-local-agent-models.linux.sh",
    "scripts/pull-local-agent-models.macos.sh",
    "scripts/pull-local-agent-models.shared.sh",
    "scripts/test-local-agent-models.ps1",
    "scripts/test-local-agent-models.linux.sh",
    "scripts/test-local-agent-models.macos.sh",
    "scripts/test-local-agent-models.shared.sh",
    ".continue/prompts/legacy-dotnet-dependency-migration.md",
    ".continue/templates/LegacyDotNetDependencyMigration.md",
    ".continue/rule-packs/python.md",
    ".continue/rule-packs/typescript.md",
    "examples/fixtures/implementation-planning-quality-input.md",
    "examples/fixtures/config-pack-review-input.md",
    "examples/fixtures/documentation-review-quality-input.md",
    "examples/fixtures/legacy-dependency-migration-input.md",
    "examples/fixtures/sonarqube-findings.md",
    "examples/fixtures/repository-context.md",
    "examples/fixtures/security-review-input.md",
    "examples/fixtures/performance-review-input.md",
    "examples/fixtures/release-readiness-input.md",
    "examples/fixtures/release-readiness-quality-input.md",
    "examples/editor-surface-validation.md",
    "examples/model-tool-use-validation.md",
    "examples/multi-repository-validation.md",
    "examples/sample-repository-factory-validation.md",
    "examples/language-rule-pack-validation.md",
    "examples/multi-language-workflow-validation.md",
    ".github/workflows/validate-pack.yml",
    ".githooks/pre-push"
)

foreach ($relativePath in $requiredFiles) {
    $path = Join-Path $repoRoot $relativePath
    if (Test-Path -LiteralPath $path) {
        Add-Pass "required file exists: $relativePath"
    } else {
        Add-Failure "required file exists: $relativePath"
    }
}

$textFiles = Get-ChildItem -LiteralPath $repoRoot -Recurse -File |
    Where-Object {
        $normalizedPath = $_.FullName.Replace('\', '/')

        $normalizedPath -notmatch "/\.git/" -and
        $normalizedPath -notmatch "/\.continue/config\.local.*\.yaml$" -and
        $normalizedPath -notmatch "/runtime-validation-output/" -and
        $_.Extension -in @(".md", ".yaml", ".yml", ".ps1", ".sh", ".tsv", ".txt")
    }

$privateIpPattern = "\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b"
$secretPattern = "(?i)(api[_-]?key|access[_-]?token|personal[_-]?access[_-]?token|password|secret)\s*[:=]\s*['""]?[A-Za-z0-9_\-]{16,}"

foreach ($file in $textFiles) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
    $relative = Resolve-Path -LiteralPath $file.FullName -Relative

    if ($content -match $privateIpPattern) {
        Add-Failure "no private IP address committed: $relative"
    }

    if ($content -match $secretPattern) {
        Add-Failure "no likely secret committed: $relative"
    }
}

if (-not $failed) {
    Write-Host "Validation passed." -ForegroundColor Green
    exit 0
}

Write-Host "Validation failed." -ForegroundColor Red
exit 1
