param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRepo,
    [Alias("target-repo")]
    [string]$TargetRepoAlias,
    [Parameter(Mandatory = $true)]
    [string]$RecommendationPath,
    [Alias("recommendation-path")]
    [string]$RecommendationPathAlias,
    [string]$OllamaBaseUrl,
    [Alias("ollama-base-url")]
    [string]$OllamaBaseUrlAlias,
    [switch]$DryRun,
    [Alias("dry-run")]
    [switch]$DryRunAlias,
    [switch]$GlobalConfig,
    [Alias("global-config")]
    [switch]$GlobalConfigAlias,
    [string]$GlobalConfigPath,
    [Alias("global-config-path")]
    [string]$GlobalConfigPathAlias,
    [switch]$GlobalConfigIncludeRules,
    [Alias("global-config-include-rules")]
    [switch]$GlobalConfigIncludeRulesAlias
)

$ErrorActionPreference = "Stop"

if (-not $TargetRepo -and $TargetRepoAlias) { $TargetRepo = $TargetRepoAlias }
if (-not $RecommendationPath -and $RecommendationPathAlias) { $RecommendationPath = $RecommendationPathAlias }
if (-not $OllamaBaseUrl -and $OllamaBaseUrlAlias) { $OllamaBaseUrl = $OllamaBaseUrlAlias }
if ($DryRunAlias) { $DryRun = $true }
if ($GlobalConfigAlias) { $GlobalConfig = $true }
if (-not $GlobalConfigPath -and $GlobalConfigPathAlias) { $GlobalConfigPath = $GlobalConfigPathAlias }
if ($GlobalConfigIncludeRulesAlias) { $GlobalConfigIncludeRules = $true }
if (-not $GlobalConfigPath) { $GlobalConfigPath = Join-Path $HOME ".continue/config.yaml" }

if (-not $TargetRepo) { throw "TargetRepo is required. Use -TargetRepo <path> or --target-repo <path>." }
if (-not $RecommendationPath) { throw "RecommendationPath is required. Use -RecommendationPath <path> or --recommendation-path <path>." }

$targetResolved = (Resolve-Path -LiteralPath $TargetRepo).Path
$recommendationResolved = (Resolve-Path -LiteralPath $RecommendationPath).Path
$targetContinue = Join-Path $targetResolved ".continue"
$baseConfigPath = Join-Path $targetContinue "config.yaml"
$localConfigPath = Join-Path $targetContinue "config.local.yaml"
$globalConfigResolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($GlobalConfigPath)

if (-not (Test-Path -LiteralPath $baseConfigPath)) {
    throw "Target repository must already have .continue/config.yaml. Install the pack first."
}

function Get-ScalarValue {
    param($Value)
    if ($null -eq $Value) { return $null }
    return ([string]$Value).Trim()
}

function Get-LaneLines {
    param(
        [string]$Label,
        $Profile,
        [string[]]$FallbackRoles,
        [string]$ApiBase
    )

    $model = Get-ScalarValue $Profile.Model
    if (-not $model) { return @() }

    $roles = @($Profile.Roles | ForEach-Object { [string]$_ })
    if ($roles.Count -eq 0) { $roles = $FallbackRoles }

    $contextLength = if ($Profile.ContextLength) { [int]$Profile.ContextLength } else { 16384 }
    $maxTokens = if ($Profile.MaxTokens) { [int]$Profile.MaxTokens } else { 2048 }
    $keepAlive = if ($Profile.KeepAlive) { [int]$Profile.KeepAlive } else { 1800 }

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("  - name: $Label - $model")
    $lines.Add("    provider: ollama")
    $lines.Add("    model: $model")
    if ($ApiBase) { $lines.Add("    apiBase: $ApiBase") }
    $lines.Add("    roles:")
    foreach ($role in $roles) { $lines.Add("      - $role") }
    $lines.Add("    capabilities:")
    $lines.Add("      - tool_use")
    $lines.Add("    defaultCompletionOptions:")
    $lines.Add("      temperature: 0.2")
    $lines.Add("      contextLength: $contextLength")
    $lines.Add("      maxTokens: $maxTokens")
    $lines.Add("      keepAlive: $keepAlive")
    return $lines.ToArray()
}

function Get-RecommendationModelLines {
    param($Recommendation, [string]$ApiBase)

    $profiles = $Recommendation.ContinueProfiles
    if (-not $profiles) { throw "Recommendation JSON does not include ContinueProfiles." }

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("models:")

    foreach ($line in (Get-LaneLines -Label "1 - WRITE SAFE" -Profile $profiles.WriteSafe -FallbackRoles @("chat", "edit", "apply") -ApiBase $ApiBase)) { $lines.Add($line) }
    foreach ($line in (Get-LaneLines -Label "2 - PLAN ONLY" -Profile $profiles.PlanOnly -FallbackRoles @("chat") -ApiBase $ApiBase)) { $lines.Add($line) }
    foreach ($line in (Get-LaneLines -Label "3 - DEEP REVIEW" -Profile $profiles.DeepReview -FallbackRoles @("chat") -ApiBase $ApiBase)) { $lines.Add($line) }

    $lines.Add("  - name: Ollama Nomic Embed")
    $lines.Add("    provider: ollama")
    $lines.Add("    model: nomic-embed-text")
    if ($ApiBase) { $lines.Add("    apiBase: $ApiBase") }
    $lines.Add("    roles:")
    $lines.Add("      - embed")

    return $lines.ToArray()
}

function Replace-TopLevelModelsSection {
    param([string[]]$Lines, [string[]]$ReplacementLines)

    $updated = New-Object System.Collections.Generic.List[string]
    $skip = $false
    $inserted = $false

    foreach ($line in $Lines) {
        if ($line -match "^models:\s*$") {
            foreach ($replacementLine in $ReplacementLines) { $updated.Add($replacementLine) }
            $skip = $true
            $inserted = $true
            continue
        }

        if ($skip -and $line -match "^[A-Za-z_][A-Za-z0-9_-]*:") { $skip = $false }
        if (-not $skip) { $updated.Add($line) }
    }

    if (-not $inserted) { throw "Could not find top-level models section in config." }
    return $updated.ToArray()
}

function Convert-ToFileUri {
    param([string]$Path)

    $resolved = (Resolve-Path -LiteralPath $Path).Path.Replace("\", "/")
    return "file://$resolved"
}

function Remove-TopLevelConfigSection {
    param(
        [string[]]$Lines,
        [string]$SectionName
    )

    $updated = New-Object System.Collections.Generic.List[string]
    $skip = $false
    $sectionPattern = "^$([regex]::Escape($SectionName)):\s*$"

    foreach ($line in $Lines) {
        if ($line -match $sectionPattern) {
            $skip = $true
            continue
        }

        if ($skip -and $line -match "^[A-Za-z_][A-Za-z0-9_-]*:") {
            $skip = $false
        }

        if (-not $skip) {
            $updated.Add($line)
        }
    }

    return $updated.ToArray()
}

function Write-GlobalConfig {
    param([string[]]$LocalLines)

    $globalConfigDirectory = Split-Path -Parent $globalConfigResolved
    if (-not (Test-Path -LiteralPath $globalConfigDirectory)) {
        New-Item -ItemType Directory -Force -Path $globalConfigDirectory | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "$globalConfigResolved.backup-$timestamp"
    if (Test-Path -LiteralPath $globalConfigResolved) {
        Copy-Item -LiteralPath $globalConfigResolved -Destination $backupPath -Force
    }

    $fileUriBase = Convert-ToFileUri -Path $targetContinue
    $rewritten = foreach ($line in $LocalLines) {
        $line -replace "file://\./", "$fileUriBase/"
    }

    if (-not $GlobalConfigIncludeRules) {
        $rewritten = Remove-TopLevelConfigSection -Lines $rewritten -SectionName "rules"
    }

    $header = @(
        "# Global Continue config generated by apply-recommended-agent-config.ps1.",
        "# This file points Continue at pack assets installed in a target repository.",
        "# The rules section is omitted by default to avoid duplicate rules when the opened repository also has .continue/rules.",
        "# Regenerate it when you move or reinstall the target repository."
    )

    @($header + $rewritten) | Set-Content -LiteralPath $globalConfigResolved
    Write-Host "Updated global Continue config: $globalConfigResolved" -ForegroundColor Green
    if (Test-Path -LiteralPath $backupPath) {
        Write-Host "Global config backup created at $backupPath" -ForegroundColor Yellow
    }
}

$recommendation = Get-Content -LiteralPath $recommendationResolved -Raw | ConvertFrom-Json
$status = Get-ScalarValue $recommendation.Recommendation.Status
$writeSafeModel = Get-ScalarValue $recommendation.Recommendation.WriteSafeModel

if ($status -ne "recommended" -or -not $writeSafeModel) {
    throw "Recommendation is not write-ready. Run model validation before generating a write-enabled local config."
}

if ($DryRun) {
    Write-Host "Would apply hardware-aware recommendation to local-only Continue config." -ForegroundColor Cyan
    Write-Host "Target config: $localConfigPath" -ForegroundColor Cyan
    if ($OllamaBaseUrl) { Write-Host "Would include a machine-specific Ollama endpoint in the local-only config." -ForegroundColor Cyan }
    if ($GlobalConfig) {
        Write-Host "Would write global Continue config: $globalConfigResolved" -ForegroundColor Cyan
        if (-not $GlobalConfigIncludeRules) { Write-Host "Would omit rules from generated global config to avoid duplicate rule warnings." -ForegroundColor Cyan }
    }
    Write-Host "WRITE SAFE model: $writeSafeModel" -ForegroundColor Cyan
    exit 0
}

$sourceConfigPath = if (Test-Path -LiteralPath $localConfigPath) { $localConfigPath } else { $baseConfigPath }
$sourceLines = Get-Content -LiteralPath $sourceConfigPath
$modelLines = Get-RecommendationModelLines -Recommendation $recommendation -ApiBase $OllamaBaseUrl
$updated = Replace-TopLevelModelsSection -Lines $sourceLines -ReplacementLines $modelLines
$header = @(
    "# Local-only Continue config generated by apply-recommended-agent-config.ps1.",
    "# Do not commit this file. It may contain machine-specific model choices or endpoints.",
    "# Source recommendation path is intentionally not recorded to avoid local path leaks."
)

$localLines = @($header + $updated)
$localLines | Set-Content -LiteralPath $localConfigPath

Write-Host "Updated local Continue config: $localConfigPath" -ForegroundColor Green
Write-Host "WRITE SAFE model: $writeSafeModel" -ForegroundColor Green
Write-Host "PLAN ONLY model: $($recommendation.Recommendation.PlanOnlyModel)" -ForegroundColor Green
Write-Host "DEEP REVIEW model: $($recommendation.Recommendation.DeepReviewModel)" -ForegroundColor Green

if ($GlobalConfig) {
    Write-GlobalConfig -LocalLines $localLines
}
