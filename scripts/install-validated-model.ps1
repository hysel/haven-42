param(
    [string]$TargetRepo,
    [Alias("target-repo")]
    [string]$TargetRepoAlias,
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [ValidateSet("write-safe", "plan-only", "deep-review")]
    [string]$Profile = "write-safe",
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [Alias("ollama-base-url")]
    [string]$OllamaBaseUrlAlias,
    [switch]$NoPull,
    [Alias("no-pull")]
    [switch]$NoPullAlias,
    [switch]$DryRun,
    [Alias("dry-run")]
    [switch]$DryRunAlias,
    [int]$TimeoutSeconds = 600
)

$ErrorActionPreference = "Stop"

if (-not $TargetRepo -and $TargetRepoAlias) {
    $TargetRepo = $TargetRepoAlias
}

if (-not $OllamaBaseUrl -and $OllamaBaseUrlAlias) {
    $OllamaBaseUrl = $OllamaBaseUrlAlias
}

if ($NoPullAlias) {
    $NoPull = $true
}

if ($DryRunAlias) {
    $DryRun = $true
}

if (-not $TargetRepo) {
    throw "TargetRepo is required. Use -TargetRepo <path> or --target-repo <path>."
}

if ([string]::IsNullOrWhiteSpace($Model)) {
    throw "Model is required."
}

$targetResolved = (Resolve-Path -LiteralPath $TargetRepo).Path
$targetContinue = Join-Path $targetResolved ".continue"
$baseConfigPath = Join-Path $targetContinue "config.yaml"
$localConfigPath = Join-Path $targetContinue "config.local.yaml"

if (-not (Test-Path -LiteralPath $baseConfigPath)) {
    throw "Target repository must already have .continue/config.yaml. Install the pack first."
}

function ConvertTo-SafeBaseUrl {
    param([string]$Value)
    return $Value.TrimEnd("/")
}

function Invoke-OllamaPull {
    param([string]$ModelName)

    $uri = "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/pull"
    $body = @{
        model = $ModelName
        stream = $false
    } | ConvertTo-Json -Depth 5

    Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json" -TimeoutSec $TimeoutSeconds | Out-Null
}

function Get-ProfileLabel {
    param([string]$ProfileName)

    switch ($ProfileName) {
        "write-safe" { return "1 - WRITE SAFE" }
        "plan-only" { return "2 - PLAN ONLY" }
        "deep-review" { return "3 - DEEP REVIEW" }
        default { throw "Unsupported profile: $ProfileName" }
    }
}

function Get-DefaultModelProfileLines {
    param([string]$SelectedProfile, [string]$SelectedModel)

    $profiles = @(
        @{ Profile = "write-safe"; Label = "1 - WRITE SAFE"; Roles = @("chat", "edit", "apply") },
        @{ Profile = "plan-only"; Label = "2 - PLAN ONLY"; Roles = @("chat") },
        @{ Profile = "deep-review"; Label = "3 - DEEP REVIEW"; Roles = @("chat") }
    )

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("models:")

    foreach ($profile in $profiles) {
        $modelName = "qwen3.5:9b"
        if ($profile.Profile -eq $SelectedProfile) {
            $modelName = $SelectedModel
        }

        $lines.Add("  - name: $($profile.Label) - $modelName")
        $lines.Add("    provider: ollama")
        $lines.Add("    model: $modelName")
        $lines.Add("    roles:")
        foreach ($role in $profile.Roles) {
            $lines.Add("      - $role")
        }
        $lines.Add("    capabilities:")
        $lines.Add("      - tool_use")
        $lines.Add("    defaultCompletionOptions:")
        $lines.Add("      temperature: 0.2")
        $lines.Add("      contextLength: 16384")
        $lines.Add("      maxTokens: 2048")
        $lines.Add("      keepAlive: 1800")
    }

    $lines.Add("  - name: Ollama Nomic Embed")
    $lines.Add("    provider: ollama")
    $lines.Add("    model: nomic-embed-text")
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
        throw "Could not find top-level models section in config."
    }

    return $updated.ToArray()
}

$profileLabel = Get-ProfileLabel -ProfileName $Profile
$modelTrimmed = $Model.Trim()

if ($DryRun) {
    Write-Host "Would install validated model '$modelTrimmed' for profile '$profileLabel'." -ForegroundColor Cyan
    if (-not $NoPull) {
        Write-Host "Would pull model from configured Ollama endpoint." -ForegroundColor Cyan
    }
    Write-Host "Would write local-only config: $localConfigPath" -ForegroundColor Cyan
    exit 0
}

if (-not $NoPull) {
    Write-Host "Pulling $modelTrimmed"
    Invoke-OllamaPull -ModelName $modelTrimmed
    Write-Host "Pulled $modelTrimmed"
}

$sourceConfigPath = $baseConfigPath
if (Test-Path -LiteralPath $localConfigPath) {
    $sourceConfigPath = $localConfigPath
}

$sourceLines = Get-Content -LiteralPath $sourceConfigPath
$profileLines = Get-DefaultModelProfileLines -SelectedProfile $Profile -SelectedModel $modelTrimmed
$updated = Replace-TopLevelModelsSection -Lines $sourceLines -ReplacementLines $profileLines
$header = @(
    "# Local-only Continue config generated by install-validated-model.ps1.",
    "# Do not commit this file. It may contain machine-specific model choices."
)

@($header + $updated) | Set-Content -LiteralPath $localConfigPath

Write-Host "Updated local Continue config: $localConfigPath" -ForegroundColor Green
Write-Host "Profile: $profileLabel" -ForegroundColor Green
Write-Host "Model: $modelTrimmed" -ForegroundColor Green
