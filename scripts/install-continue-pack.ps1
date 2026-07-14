param(
    [string]$TargetRepo,
    [Alias("target-repo")]
    [string]$TargetRepoAlias,
    [switch]$DryRun,
    [Alias("dry-run")]
    [switch]$DryRunAlias,
    [switch]$AutoModelConfig,
    [Alias("auto-model-config")]
    [switch]$AutoModelConfigAlias,
    [switch]$ModelLanes,
    [Alias("install-profile")]
    [ValidateSet("default", "read-only", "approved-write")]
    [string]$InstallProfile = "default",
    [Alias("model-lanes")]
    [switch]$ModelLanesAlias,
    [switch]$GlobalConfig,
    [Alias("global-config")]
    [switch]$GlobalConfigAlias,
    [string]$GlobalConfigPath,
    [Alias("global-config-path")]
    [string]$GlobalConfigPathAlias,
    [string]$GlobalConfigApiBase,
    [Alias("global-config-api-base")]
    [string]$GlobalConfigApiBaseAlias,
    [switch]$GlobalConfigIncludeRules,
    [Alias("global-config-include-rules")]
    [switch]$GlobalConfigIncludeRulesAlias,
    [switch]$SharedAssets,
    [Alias("shared-assets")]
    [switch]$SharedAssetsAlias,
    [string]$SharedAssetsPath,
    [Alias("shared-assets-path")]
    [string]$SharedAssetsPathAlias
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceContinue = Join-Path $repoRoot ".continue"

if (-not $TargetRepo -and $TargetRepoAlias) {
    $TargetRepo = $TargetRepoAlias
}

if ($DryRunAlias) {
    $DryRun = $true
}

if ($AutoModelConfigAlias) {
    $AutoModelConfig = $true
}

if ($ModelLanesAlias) {
    $ModelLanes = $true
}

if ($GlobalConfigAlias) {
    $GlobalConfig = $true
}

if (-not $GlobalConfigPath -and $GlobalConfigPathAlias) {
    $GlobalConfigPath = $GlobalConfigPathAlias
}

if (-not $GlobalConfigApiBase -and $GlobalConfigApiBaseAlias) {
    $GlobalConfigApiBase = $GlobalConfigApiBaseAlias
}

if ($GlobalConfigIncludeRulesAlias) {
    $GlobalConfigIncludeRules = $true
}

if ($SharedAssetsAlias) {
    $SharedAssets = $true
}

if (-not $SharedAssetsPath -and $SharedAssetsPathAlias) {
    $SharedAssetsPath = $SharedAssetsPathAlias
}

if (-not $TargetRepo) {
    throw "TargetRepo is required. Use -TargetRepo <path> or --target-repo <path>."
}

if ($InstallProfile -eq "approved-write") {
    $ModelLanes = $true
}

$ReadOnlyProfile = $InstallProfile -eq "read-only"

if ($ReadOnlyProfile -and ($AutoModelConfig -or $ModelLanes)) {
    throw "The read-only install profile cannot be combined with -AutoModelConfig or -ModelLanes."
}

if ($AutoModelConfig -and $ModelLanes) {
    throw "Use either -AutoModelConfig or -ModelLanes, not both."
}

if ($SharedAssets -and ($AutoModelConfig -or $ModelLanes -or $ReadOnlyProfile)) {
    throw "Shared-assets mode currently supports reusable assets and global config generation only. Do not combine it with -AutoModelConfig, -ModelLanes, or read-only/approved-write install profiles."
}

if (-not $GlobalConfigPath) {
    $GlobalConfigPath = Join-Path $HOME ".continue/config.yaml"
}

if ($SharedAssets -and -not $SharedAssetsPath) {
    $SharedAssetsPath = Join-Path $HOME ".local-engineering-agent-pack/assets"
}

if ($SharedAssets) {
    $GlobalConfig = $true
}

if (-not (Test-Path -LiteralPath $sourceContinue)) {
    throw "Source .continue folder does not exist: $sourceContinue"
}

if (-not (Test-Path -LiteralPath $TargetRepo)) {
    throw "Target repository path does not exist: $TargetRepo"
}

$repoRootResolved = (Resolve-Path -LiteralPath $repoRoot).Path
$targetResolved = (Resolve-Path -LiteralPath $TargetRepo).Path

if ($repoRootResolved.TrimEnd('\', '/') -eq $targetResolved.TrimEnd('\', '/')) {
    throw "Target repository must be different from this pack repository."
}

$targetContinue = Join-Path $targetResolved ".continue"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupContinue = Join-Path $targetResolved ".continue.backup-$timestamp"
$globalConfigResolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($GlobalConfigPath)
$backupGlobalConfig = "$globalConfigResolved.backup-$timestamp"
$sharedAssetsResolved = $null
$backupSharedAssets = $null

if ($SharedAssets) {
    $sharedAssetsResolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($SharedAssetsPath)
    $backupSharedAssets = "$sharedAssetsResolved.backup-$timestamp"
}

function Write-Plan {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Get-PackFiles {
    Get-ChildItem -LiteralPath $sourceContinue -Recurse -File -Force |
        Where-Object {
            $relative = [System.IO.Path]::GetRelativePath($sourceContinue, $_.FullName).Replace('\', '/')
            $relative -notmatch "^config\.local.*\.ya?ml$"
        }
}

function Copy-PackFiles {
    foreach ($file in Get-PackFiles) {
        $relative = [System.IO.Path]::GetRelativePath($sourceContinue, $file.FullName)
        $destination = Join-Path $targetContinue $relative
        $destinationDirectory = Split-Path -Parent $destination

        if (-not (Test-Path -LiteralPath $destinationDirectory)) {
            New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
        }

        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    }
}

function Copy-PackFilesToRoot {
    param([string]$DestinationRoot)

    foreach ($file in Get-PackFiles) {
        $relative = [System.IO.Path]::GetRelativePath($sourceContinue, $file.FullName)
        $destination = Join-Path $DestinationRoot $relative
        $destinationDirectory = Split-Path -Parent $destination

        if (-not (Test-Path -LiteralPath $destinationDirectory)) {
            New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
        }

        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    }
}

function Test-InstalledPack {
    param([string]$AssetRoot = $targetContinue)

    $configPath = Join-Path $AssetRoot "config.yaml"

    if (-not (Test-Path -LiteralPath $configPath)) {
        throw "Installed config is missing: $configPath"
    }

    $config = Get-Content -LiteralPath $configPath -Raw
    $fileRefs = [regex]::Matches($config, "file://\.\/([^`r`n]+)") | ForEach-Object {
        $_.Groups[1].Value.Trim()
    }

    foreach ($ref in $fileRefs) {
        if ([System.IO.Path]::IsPathFullyQualified($ref) -or $ref -match "(^|/)\.\.(/|$)") {
            throw "Installed config has unsafe file reference: $ref"
        }

        $refPath = Join-Path $AssetRoot $ref
        if (-not (Test-Path -LiteralPath $refPath)) {
            throw "Installed config references a missing file: $ref"
        }
    }

    $localConfigFiles = Get-ChildItem -LiteralPath $AssetRoot -Force -File -Filter "config.local*.yaml" -ErrorAction SilentlyContinue
    if ($localConfigFiles.Count -gt 0) {
        throw "Installed pack should not include local config overrides."
    }
}

function Get-TargetProjectProfile {
    $classifier = Join-Path $repoRoot "scripts/get-project-profile.ps1"
    if (-not (Test-Path -LiteralPath $classifier -PathType Leaf)) {
        throw "Project profile classifier is missing: $classifier"
    }

    $json = (& $classifier -TargetRepo $targetResolved -AsJson | Out-String).Trim()
    if (-not $json) {
        throw "Project profile classifier did not return JSON output."
    }

    return [pscustomobject]@{
        Json = $json
        Value = ($json | ConvertFrom-Json)
    }
}

function Install-TargetProjectProfile {
    param([Parameter(Mandatory = $true)][object]$ProfileResult)

    $profilePath = Join-Path $targetContinue "project-profile.json"
    Set-Content -LiteralPath $profilePath -Value $ProfileResult.Json -Encoding utf8

    foreach ($rulePack in @($ProfileResult.Value.SelectedRulePacks)) {
        $sourceRelative = [string]$rulePack.SourcePath
        $activeRelative = [string]$rulePack.ActivePath
        if ([System.IO.Path]::IsPathFullyQualified($sourceRelative) -or
            [System.IO.Path]::IsPathFullyQualified($activeRelative) -or
            $sourceRelative -match "(^|[/\\])\.\.([/\\]|$)" -or
            $activeRelative -match "(^|[/\\])\.\.([/\\]|$)") {
            throw "Project profile contains an unsafe rule-pack path."
        }

        $source = Join-Path $targetContinue $sourceRelative
        $destination = Join-Path $targetContinue $activeRelative
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Selected project rule pack is missing: $sourceRelative"
        }

        $destinationDirectory = Split-Path -Parent $destination
        New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination -Force
    }

    Write-Host "Installed sanitized project profile: $profilePath" -ForegroundColor Green
    if (@($ProfileResult.Value.SelectedRulePackIds).Count -gt 0) {
        Write-Host "Activated project rule packs: $(@($ProfileResult.Value.SelectedRulePackIds) -join ', ')" -ForegroundColor Green
    } else {
        Write-Host "No optional project rule packs were activated." -ForegroundColor Yellow
    }
}

function Get-RecommendedModel {
    $profileScript = Join-Path $repoRoot "scripts/get-local-model-profile.windows.ps1"

    if (-not (Test-Path -LiteralPath $profileScript)) {
        throw "Hardware profile script is missing: $profileScript"
    }

    $profileJson = (& $profileScript -AsJson | Out-String).Trim()
    if (-not $profileJson) {
        throw "Hardware profile script did not return JSON output."
    }

    $profile = $profileJson | ConvertFrom-Json
    $model = $profile.ModelRecommendation.PrimaryModel

    if (-not $model) {
        throw "Hardware profile did not return a recommended model."
    }

    return $model
}

function Write-LocalModelConfig {
    param([string]$Model)

    $configPath = Join-Path $targetContinue "config.yaml"
    $localConfigPath = Join-Path $targetContinue "config.local.yaml"
    $lines = Get-Content -LiteralPath $configPath
    $replaced = $false
    $updated = foreach ($line in $lines) {
        if (-not $replaced -and $line -match "^(\s*model:\s*).*$") {
            $replaced = $true
            "$($Matches[1])$Model"
        } else {
            $line
        }
    }

    if (-not $replaced) {
        throw "Could not find a model entry in installed config."
    }

    $header = @(
        "# Local-only Continue config generated by install-continue-pack.ps1.",
        "# Do not commit this file. It may contain machine-specific model choices."
    )

    @($header + $updated) | Set-Content -LiteralPath $localConfigPath
    Write-Host "Generated local model config: $localConfigPath" -ForegroundColor Green
    Write-Host "Selected model: $Model" -ForegroundColor Green
}

function Get-ModelLaneLines {
    @(
        "models:",
        "  - name: 1 - WRITE SAFE - qwen3.5:9b",
        "    provider: ollama",
        "    model: qwen3.5:9b",
        "    roles:",
        "      - chat",
        "      - edit",
        "      - apply",
        "    capabilities:",
        "      - tool_use",
        "    defaultCompletionOptions:",
        "      temperature: 0.1",
        "      contextLength: 16384",
        "      maxTokens: 2048",
        "      keepAlive: 1800",
        "  - name: 2 - PLAN ONLY - qwen3.5:9b",
        "    provider: ollama",
        "    model: qwen3.5:9b",
        "    roles:",
        "      - chat",
        "    capabilities:",
        "      - tool_use",
        "    defaultCompletionOptions:",
        "      temperature: 0.2",
        "      contextLength: 16384",
        "      maxTokens: 2048",
        "      keepAlive: 1800",
        "  - name: 3 - DEEP REVIEW - qwen3.5:9b",
        "    provider: ollama",
        "    model: qwen3.5:9b",
        "    roles:",
        "      - chat",
        "    capabilities:",
        "      - tool_use",
        "    defaultCompletionOptions:",
        "      temperature: 0.2",
        "      contextLength: 16384",
        "      maxTokens: 2048",
        "      keepAlive: 1800",
        "  - name: Ollama Nomic Embed",
        "    provider: ollama",
        "    model: nomic-embed-text",
        "    roles:",
        "      - embed"
    )
}

function Replace-TopLevelConfigSection {
    param(
        [string[]]$Lines,
        [string]$SectionName,
        [string[]]$ReplacementLines
    )

    $updated = New-Object System.Collections.Generic.List[string]
    $skip = $false
    $inserted = $false
    $sectionPattern = "^$([regex]::Escape($SectionName)):\s*$"

    foreach ($line in $Lines) {
        if ($line -match $sectionPattern) {
            foreach ($replacementLine in $ReplacementLines) {
                $updated.Add($replacementLine)
            }
            $skip = $true
            $inserted = $true
            continue
        }

        if ($skip -and $line -match "^[A-Za-z_][A-Za-z0-9_-]*:") {
            $skip = $false
        }

        if (-not $skip) {
            $updated.Add($line)
        }
    }

    if (-not $inserted) {
        throw "Could not find top-level $SectionName section in config."
    }

    return $updated.ToArray()
}

function Get-ReadOnlyModelLines {
    @(
        "models:",
        "  - name: READ ONLY - qwen3.5:9b",
        "    provider: ollama",
        "    model: qwen3.5:9b",
        "    roles:",
        "      - chat",
        "    capabilities:",
        "      - tool_use",
        "    defaultCompletionOptions:",
        "      temperature: 0.2",
        "      contextLength: 16384",
        "      maxTokens: 2048",
        "      keepAlive: 1800",
        "  - name: Ollama Nomic Embed",
        "    provider: ollama",
        "    model: nomic-embed-text",
        "    roles:",
        "      - embed"
    )
}

function Write-ReadOnlyProfileConfig {
    $configPath = Join-Path $targetContinue "config.yaml"
    $localConfigPath = Join-Path $targetContinue "config.local.yaml"
    $lines = Get-Content -LiteralPath $configPath
    $updated = Replace-TopLevelConfigSection -Lines $lines -SectionName "models" -ReplacementLines (Get-ReadOnlyModelLines)

    $header = @(
        "# Local-only Continue config generated by install-continue-pack.ps1.",
        "# Do not commit this file. It is scoped for read-only review workflows.",
        "# This profile intentionally omits edit/apply roles."
    )

    @($header + $updated) | Set-Content -LiteralPath $localConfigPath
    Write-Host "Generated read-only profile config: $localConfigPath" -ForegroundColor Green
}

function Write-ModelLanesConfig {
    $configPath = Join-Path $targetContinue "config.yaml"
    $localConfigPath = Join-Path $targetContinue "config.local.yaml"
    $lines = Get-Content -LiteralPath $configPath
    $updated = Replace-TopLevelConfigSection -Lines $lines -SectionName "models" -ReplacementLines (Get-ModelLaneLines)

    $header = @(
        "# Local-only Continue config generated by install-continue-pack.ps1.",
        "# Do not commit this file. It contains workflow-specific model lane choices.",
        "# Only the WRITE SAFE lane has edit/apply roles. Validate it before real code changes."
    )

    @($header + $updated) | Set-Content -LiteralPath $localConfigPath
    Write-Host "Generated model lanes config: $localConfigPath" -ForegroundColor Green
}

function Convert-ToFileUri {
    param([string]$Path)

    $resolvedPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path).Replace('\', '/')

    if ($resolvedPath -match "^[A-Za-z]:/") {
        return "file://$resolvedPath"
    }

    return "file://$resolvedPath"
}

function Set-OllamaApiBase {
    param(
        [string[]]$Lines,
        [string]$ApiBase
    )

    if (-not $ApiBase) {
        return $Lines
    }

    $updated = New-Object System.Collections.Generic.List[string]
    $inModel = $false
    $inOllamaModel = $false
    $sawApiBase = $false

    foreach ($line in $Lines) {
        if ($line -match "^\s{2}-\s+name:") {
            if ($inOllamaModel -and -not $sawApiBase) {
                $updated.Add("    apiBase: $ApiBase")
            }

            $inModel = $true
            $inOllamaModel = $false
            $sawApiBase = $false
        }

        if ($inModel -and $line -match "^\s{4}provider:\s*ollama\s*$") {
            $inOllamaModel = $true
        }

        if ($inOllamaModel -and $line -match "^\s{4}apiBase:") {
            $updated.Add("    apiBase: $ApiBase")
            $sawApiBase = $true
            continue
        }

        if ($inModel -and $line -match "^[A-Za-z_][A-Za-z0-9_-]*:") {
            if ($inOllamaModel -and -not $sawApiBase) {
                $updated.Add("    apiBase: $ApiBase")
            }

            $inModel = $false
            $inOllamaModel = $false
            $sawApiBase = $false
        }

        $updated.Add($line)
    }

    if ($inOllamaModel -and -not $sawApiBase) {
        $updated.Add("    apiBase: $ApiBase")
    }

    return $updated.ToArray()
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

function Write-GlobalContinueConfig {
    if ($SharedAssets) {
        $assetRoot = $sharedAssetsResolved
    } else {
        $assetRoot = $targetContinue
    }

    $installedConfigPath = Join-Path $assetRoot "config.yaml"
    $localConfigPath = Join-Path $assetRoot "config.local.yaml"

    if (Test-Path -LiteralPath $localConfigPath) {
        $sourceConfigPath = $localConfigPath
    } else {
        $sourceConfigPath = $installedConfigPath
    }

    if (-not (Test-Path -LiteralPath $sourceConfigPath)) {
        throw "Cannot write global config because source config is missing: $sourceConfigPath"
    }

    $globalConfigDirectory = Split-Path -Parent $globalConfigResolved
    if (-not (Test-Path -LiteralPath $globalConfigDirectory)) {
        New-Item -ItemType Directory -Force -Path $globalConfigDirectory | Out-Null
    }

    if (Test-Path -LiteralPath $globalConfigResolved) {
        Copy-Item -LiteralPath $globalConfigResolved -Destination $backupGlobalConfig -Force
    }

    $fileUriBase = Convert-ToFileUri -Path $assetRoot
    $lines = Get-Content -LiteralPath $sourceConfigPath
    $rewritten = foreach ($line in $lines) {
        $line -replace "file://\./", "$fileUriBase/"
    }

    if (-not $GlobalConfigIncludeRules) {
        $rewritten = Remove-TopLevelConfigSection -Lines $rewritten -SectionName "rules"
    }

    $rewritten = Set-OllamaApiBase -Lines $rewritten -ApiBase $GlobalConfigApiBase

    $header = @(
        "# Global Continue config generated by install-continue-pack.ps1.",
        "# This file points Continue at reusable pack assets.",
        "# The rules section is omitted by default to avoid duplicate rules when the opened repository also has .continue/rules.",
        "# Regenerate it when you move or reinstall the referenced asset folder."
    )

    @($header + $rewritten) | Set-Content -LiteralPath $globalConfigResolved
    Write-Host "Updated global Continue config: $globalConfigResolved" -ForegroundColor Green

    if (Test-Path -LiteralPath $backupGlobalConfig) {
        Write-Host "Global config backup created at $backupGlobalConfig" -ForegroundColor Yellow
    }
}

$targetProjectProfile = if ($SharedAssets) { $null } else { Get-TargetProjectProfile }

Write-Plan "Install Local Engineering Agent Pack"
Write-Plan "Source: $sourceContinue"
Write-Plan "Target: $targetContinue"

if ($SharedAssets) {
    Write-Plan "Target repository .continue will not be changed in shared-assets mode."
} elseif (Test-Path -LiteralPath $targetContinue) {
    Write-Plan "Existing target .continue will be backed up to: $backupContinue"
} else {
    Write-Plan "Target .continue does not exist and will be created."
}

Write-Plan "Local config overrides matching config.local*.yaml will be excluded."
Write-Plan "Install profile: $InstallProfile"
if ($SharedAssets) {
    Write-Plan "Shared-assets mode is enabled."
    Write-Plan "Shared assets target: $sharedAssetsResolved"
    Write-Plan "Global Continue config update is enabled because shared-assets mode was requested."
    if (Test-Path -LiteralPath $sharedAssetsResolved) {
        Write-Plan "Existing shared assets will be backed up to: $backupSharedAssets"
    }
    Write-Plan "Project-specific classification and rule activation are skipped in shared-assets mode."
} else {
    Write-Plan "Detected project ecosystem: $($targetProjectProfile.Value.PrimaryEcosystem) ($($targetProjectProfile.Value.Confidence) confidence)"
    $selectedRulePacks = @($targetProjectProfile.Value.SelectedRulePackIds)
    Write-Plan "Project rule packs selected: $(if ($selectedRulePacks.Count -gt 0) { $selectedRulePacks -join ', ' } else { 'none' })"
}
if ($AutoModelConfig) {
    Write-Plan "Auto model config is enabled. A target .continue/config.local.yaml file will be generated after install."
}
if ($ReadOnlyProfile) {
    Write-Plan "Read-only install profile is enabled. A target .continue/config.local.yaml file will be generated without edit/apply roles."
}
if ($ModelLanes) {
    Write-Plan "Model lanes config is enabled. A target .continue/config.local.yaml file will be generated after install."
}
if ($GlobalConfig) {
    Write-Plan "Global Continue config update is enabled."
    Write-Plan "Global config target: $globalConfigResolved"
    if (Test-Path -LiteralPath $globalConfigResolved) {
        Write-Plan "Existing global config will be backed up to: $backupGlobalConfig"
    }
    if ($GlobalConfigApiBase) {
        Write-Plan "Global config Ollama apiBase override is enabled."
    }
    if ($GlobalConfigIncludeRules) {
        Write-Plan "Global config rule references are enabled. Use only when the editor will not also load project-local rules."
    } else {
        Write-Plan "Global config rule references will be omitted to avoid duplicate rule warnings."
    }
}

if ($DryRun) {
    Write-Plan "Dry run only. No files will be changed."
    Write-Plan "Files that would be copied:"
    if ($SharedAssets) {
        Get-PackFiles | ForEach-Object {
            $relative = [System.IO.Path]::GetRelativePath($sourceContinue, $_.FullName).Replace('\', '/')
            Write-Host "- $sharedAssetsResolved/$relative"
        }
    } else {
        Get-PackFiles | ForEach-Object {
            $relative = [System.IO.Path]::GetRelativePath($sourceContinue, $_.FullName).Replace('\', '/')
            Write-Host "- .continue/$relative"
        }
        Write-Plan "Would write .continue/project-profile.json and activate the selected project rule packs under .continue/rules/."
    }
    if ($AutoModelConfig) {
        Write-Plan "Would generate .continue/config.local.yaml using the hardware profile recommended model."
    }
    if ($ReadOnlyProfile) {
        Write-Plan "Would generate .continue/config.local.yaml for read-only review without edit/apply roles."
    }
    if ($ModelLanes) {
        Write-Plan "Would generate .continue/config.local.yaml with WRITE SAFE, PLAN ONLY, and DEEP REVIEW model profiles plus the embedding model."
    }
    if ($GlobalConfig) {
        Write-Plan "Would write global Continue config with absolute file references to: $globalConfigResolved"
        if ($GlobalConfigApiBase) {
            Write-Plan "Would set Ollama apiBase in generated global config."
        }
        if ($GlobalConfigIncludeRules) {
            Write-Plan "Would include rules in generated global config."
        } else {
            Write-Plan "Would omit rules from generated global config to avoid duplicate rule warnings."
        }
    }
    exit 0
}

if ($SharedAssets) {
    if (Test-Path -LiteralPath $sharedAssetsResolved) {
        Move-Item -LiteralPath $sharedAssetsResolved -Destination $backupSharedAssets
    }

    New-Item -ItemType Directory -Force -Path $sharedAssetsResolved | Out-Null
    Copy-PackFilesToRoot -DestinationRoot $sharedAssetsResolved
    Test-InstalledPack -AssetRoot $sharedAssetsResolved
} else {
    if (Test-Path -LiteralPath $targetContinue) {
        Move-Item -LiteralPath $targetContinue -Destination $backupContinue
    }

    New-Item -ItemType Directory -Force -Path $targetContinue | Out-Null
    Copy-PackFiles
    Test-InstalledPack
    Install-TargetProjectProfile -ProfileResult $targetProjectProfile
}

if ($AutoModelConfig) {
    $recommendedModel = Get-RecommendedModel
    Write-LocalModelConfig -Model $recommendedModel
}

if ($ReadOnlyProfile) {
    Write-ReadOnlyProfileConfig
}

if ($ModelLanes) {
    Write-ModelLanesConfig
}

if ($GlobalConfig) {
    Write-GlobalContinueConfig
}

Write-Host "Install complete." -ForegroundColor Green
if ($SharedAssets) {
    Write-Host "Installed shared assets to $sharedAssetsResolved" -ForegroundColor Green
} else {
    Write-Host "Installed .continue to $targetContinue" -ForegroundColor Green
}

if (Test-Path -LiteralPath $backupContinue) {
    Write-Host "Backup created at $backupContinue" -ForegroundColor Yellow
}

if ($backupSharedAssets -and (Test-Path -LiteralPath $backupSharedAssets)) {
    Write-Host "Shared assets backup created at $backupSharedAssets" -ForegroundColor Yellow
}
