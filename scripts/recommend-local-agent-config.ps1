param(
    [Parameter(Mandatory = $true)]
    [string]$ModelProfilePath,
    [string]$ModelCatalogPath,
    [string]$EvidenceCatalogPath,
    [string]$OutputPath,
    [ValidateSet("TotalDedicated", "MaxDedicated")]
    [string]$VramSelectionMode = "MaxDedicated"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $ModelCatalogPath) {
    $ModelCatalogPath = Join-Path $repoRoot "config/model-recommendations.tsv"
}

if (-not $EvidenceCatalogPath) {
    $EvidenceCatalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
}

if (-not $OutputPath) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/model-config-recommendation-$timestamp.json"
}

function Get-NormalizedPlatformName {
    param([string]$Platform)

    if ($Platform -match '(?i)mac|darwin') { return "macOS" }
    if ($Platform -match '(?i)linux') { return "Linux" }
    if ($Platform -match '(?i)windows') { return "Windows" }
    return "Unknown"
}

function Get-ModelSizeBillion {
    param([string]$Model)

    $match = [regex]::Match($Model, '(?i)(\d+(?:\.\d+)?)b')
    if (-not $match.Success) { return 0 }
    return [double]::Parse($match.Groups[1].Value, [System.Globalization.CultureInfo]::InvariantCulture)
}

function Get-RecommendedMinVramGb {
    param([string]$Model)

    if ($Model -match '(?i)(cloud|-mlx)') { return 999999 }

    $size = Get-ModelSizeBillion -Model $Model
    if ($size -le 0) { return 0 }
    if ($size -le 4) { return 8 }
    if ($size -le 9) { return 12 }
    if ($size -le 14) { return 20 }
    if ($size -le 27) { return 36 }
    if ($size -le 35) { return 48 }
    if ($size -le 80) { return 80 }
    if ($size -le 122) { return 128 }
    return 512
}

function Get-WorkflowRank {
    param([string]$Status)

    switch ($Status) {
        "approved-write-ready" { return 0 }
        "read-only-tool-validated" { return 1 }
        "plan-review-candidate" { return 2 }
        default { return 3 }
    }
}

function Get-ModelPreferenceRank {
    param([string]$Model)

    if ($Model -match '(?i)^qwen3\.5:9b$') { return 0 }
    if ($Model -match '(?i)(devstral|coder|code|codestral)') { return 1 }
    if ($Model -match '(?i)(qwen|gpt-oss|llama3\.1)') { return 2 }
    return 3
}

function Get-AvailableVram {
    param(
        $Profile,
        [string]$SelectionMode
    )

    $values = @()
    foreach ($gpu in @($Profile.Gpus)) {
        if ($null -eq $gpu -or $null -eq $gpu.VramGb) { continue }

        $memoryType = [string]$gpu.MemoryType
        if ($memoryType -and $memoryType -notmatch '(?i)dedicated|unknown') { continue }

        try {
            $value = [double]::Parse([string]$gpu.VramGb, [System.Globalization.CultureInfo]::InvariantCulture)
            if ($value -gt 0) { $values += $value }
        }
        catch { continue }
    }

    if ($values.Count -eq 0) { return $null }
    if ($SelectionMode -eq "TotalDedicated") {
        return [math]::Round(($values | Measure-Object -Sum).Sum, 2)
    }

    return [math]::Round(($values | Measure-Object -Maximum).Maximum, 2)
}

function Read-ModelCatalog {
    param([string]$Path)

    $rows = [System.Collections.Generic.List[object]]::new()
    foreach ($line in (Get-Content -LiteralPath $Path)) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) { continue }
        $parts = $line -split "\|", 5
        if ($parts.Count -lt 5) { continue }

        $rows.Add([pscustomobject]@{
            Tier = $parts[0]
            MatchPattern = $parts[1]
            FallbackModel = $parts[2]
            RecommendedUse = $parts[3]
            ValidationNote = $parts[4]
        })
    }

    return $rows
}

function Read-EvidenceCatalog {
    param([string]$Path)

    $evidence = @{}
    if (-not (Test-Path -LiteralPath $Path)) { return $evidence }

    $lines = Get-Content -LiteralPath $Path | Select-Object -Skip 1
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line -split "`t", 8
        if ($parts.Count -lt 8 -or $parts[0] -ne "model-tool-use") { continue }

        $model = $parts[4]
        if (-not $evidence.ContainsKey($model)) {
            $evidence[$model] = [pscustomobject]@{
                Status = $parts[5]
                Evidence = $parts[6]
                Notes = $parts[7]
            }
        }
    }

    return $evidence
}

function Get-PlatformEligibility {
    param(
        [string]$Model,
        [string]$Platform
    )

    $normalizedPlatform = Get-NormalizedPlatformName -Platform $Platform
    if ($Model -match '(?i)cloud') {
        return [pscustomobject]@{
            Eligible = $false
            Reason = "Cloud catalog tag; local Ollama pull is not supported."
        }
    }

    if ($Model -match '(?i)-mlx($|[-_:])' -and $normalizedPlatform -ne "macOS") {
        return [pscustomobject]@{
            Eligible = $false
            Reason = "MLX model tag requires a macOS Apple Silicon model host."
        }
    }

    return [pscustomobject]@{
        Eligible = $true
        Reason = "Model tag is compatible with the detected model host platform."
    }
}

function Add-Candidate {
    param(
        [System.Collections.Generic.List[object]]$Candidates,
        [hashtable]$Seen,
        [string]$Model,
        [string]$Source,
        [object]$CatalogRow,
        [hashtable]$Evidence,
        [Nullable[double]]$AvailableVramGb,
        [string]$Platform
    )

    if ([string]::IsNullOrWhiteSpace($Model)) { return }
    $modelName = $Model.Trim()
    if ($Seen.ContainsKey($modelName)) { return }
    $Seen[$modelName] = $true

    $minVram = Get-RecommendedMinVramGb -Model $modelName
    $fitsVram = $true
    if ($null -ne $AvailableVramGb -and $minVram -gt 0 -and $minVram -lt 999999) {
        $fitsVram = $minVram -le $AvailableVramGb
    }
    elseif ($minVram -ge 999999) {
        $fitsVram = $false
    }

    $evidenceItem = if ($Evidence.ContainsKey($modelName)) { $Evidence[$modelName] } else { $null }
    $validationStatus = if ($evidenceItem) { $evidenceItem.Status } else { "candidate-only" }
    $eligibility = Get-PlatformEligibility -Model $modelName -Platform $Platform

    $Candidates.Add([pscustomobject]@{
        Model = $modelName
        Source = $Source
        ValidationStatus = $validationStatus
        Evidence = if ($evidenceItem) { $evidenceItem.Evidence } else { $null }
        RecommendedMinVramGb = if ($minVram -gt 0 -and $minVram -lt 999999) { $minVram } else { $null }
        FitsAvailableVram = [bool]$fitsVram
        PlatformEligible = [bool]$eligibility.Eligible
        PlatformReason = $eligibility.Reason
        RecommendedUse = if ($CatalogRow) { $CatalogRow.RecommendedUse } else { "Validate locally before relying on this model." }
        ValidationNote = if ($CatalogRow) { $CatalogRow.ValidationNote } else { "Run read-only and approved-write smoke tests before granting edit/apply roles." }
    })
}

function Select-PrimaryModel {
    param(
        [object[]]$Candidates,
        [string]$Purpose
    )

    $eligible = @($Candidates | Where-Object { $_.PlatformEligible -and $_.FitsAvailableVram })
    if ($eligible.Count -eq 0) { return $null }

    if ($Purpose -eq "write") {
        $eligible = @($eligible | Where-Object { $_.ValidationStatus -eq "approved-write-ready" })
        if ($eligible.Count -eq 0) { return $null }
    }
    elseif ($Purpose -eq "plan") {
        $eligible = @($eligible | Where-Object { $_.ValidationStatus -in @("approved-write-ready", "read-only-tool-validated", "plan-review-candidate") })
    }
    else {
        $eligible = @($eligible | Where-Object { $_.ValidationStatus -ne "candidate-only" })
    }

    if ($eligible.Count -eq 0) { return $null }

    return @($eligible | Sort-Object `
        @{ Expression = { Get-WorkflowRank -Status $_.ValidationStatus } }, `
        @{ Expression = { if ($_.RecommendedMinVramGb) { [double]$_.RecommendedMinVramGb } else { 9999 } } }, `
        @{ Expression = { Get-ModelPreferenceRank -Model $_.Model } }, `
        @{ Expression = { $_.Model } } | Select-Object -First 1)[0]
}

if (-not (Test-Path -LiteralPath $ModelProfilePath)) {
    throw "ModelProfilePath does not exist: $ModelProfilePath"
}

Write-Host "[1/5] Reading local model profile..."
$profile = Get-Content -LiteralPath $ModelProfilePath -Raw | ConvertFrom-Json
$availableVramGb = Get-AvailableVram -Profile $profile -SelectionMode $VramSelectionMode
$platform = Get-NormalizedPlatformName -Platform ([string]$profile.Platform)
$installedModels = @($profile.OllamaModels | ForEach-Object { [string]$_ })

Write-Host "[2/5] Reading model and evidence catalogs..."
$catalogRows = @(Read-ModelCatalog -Path $ModelCatalogPath)
$evidence = Read-EvidenceCatalog -Path $EvidenceCatalogPath

Write-Host "[3/5] Building hardware-aware candidate list..."
$candidates = [System.Collections.Generic.List[object]]::new()
$seen = @{}

foreach ($row in $catalogRows) {
    if ($row.MatchPattern) {
        foreach ($installedModel in $installedModels) {
            if ($installedModel -match $row.MatchPattern) {
                Add-Candidate -Candidates $candidates -Seen $seen -Model $installedModel -Source "installed-catalog-match" -CatalogRow $row -Evidence $evidence -AvailableVramGb $availableVramGb -Platform $platform
            }
        }
    }

    if ($row.FallbackModel) {
        Add-Candidate -Candidates $candidates -Seen $seen -Model $row.FallbackModel -Source "catalog-fallback" -CatalogRow $row -Evidence $evidence -AvailableVramGb $availableVramGb -Platform $platform
    }
}

foreach ($modelName in $evidence.Keys) {
    Add-Candidate -Candidates $candidates -Seen $seen -Model $modelName -Source "evidence-catalog" -CatalogRow $null -Evidence $evidence -AvailableVramGb $availableVramGb -Platform $platform
}

Write-Host "[4/5] Selecting model lanes and config defaults..."
$writeModel = Select-PrimaryModel -Candidates $candidates -Purpose "write"
$planModel = Select-PrimaryModel -Candidates $candidates -Purpose "plan"
$reviewModel = Select-PrimaryModel -Candidates $candidates -Purpose "review"

if (-not $planModel) { $planModel = $writeModel }
if (-not $reviewModel) { $reviewModel = $planModel }

$recommendationStatus = if ($writeModel) { "recommended" } else { "no-approved-write-model" }
$nextStep = if ($writeModel) {
    "Generate local Continue config from this recommendation, then run editor read-only and approved-write smoke tests."
} else {
    "Run model validation before generating a write-enabled local config."
}

$report = [pscustomobject]@{
    GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    ModelProfilePath = "redacted"
    ModelCatalogPath = "redacted"
    EvidenceCatalogPath = "redacted"
    Platform = $platform
    CpuArchitecture = $profile.CpuArchitecture
    SystemRamGb = $profile.SystemRamGb
    VramSelectionMode = $VramSelectionMode
    AvailableVramGb = $availableVramGb
    InstalledModelCount = $installedModels.Count
    Recommendation = [pscustomobject]@{
        Status = $recommendationStatus
        WriteSafeModel = if ($writeModel) { $writeModel.Model } else { $null }
        PlanOnlyModel = if ($planModel) { $planModel.Model } else { $null }
        DeepReviewModel = if ($reviewModel) { $reviewModel.Model } else { $null }
        Reason = "Selected from catalog and validation evidence using platform compatibility, VRAM fit, and workflow validation status."
        NextStep = $nextStep
    }
    ContinueProfiles = [pscustomobject]@{
        WriteSafe = [pscustomobject]@{
            Model = if ($writeModel) { $writeModel.Model } else { $null }
            Roles = @("chat", "edit", "apply")
            ContextLength = 16384
            MaxTokens = 2048
            KeepAlive = 1800
            RequiresEditorSmokeTest = $true
        }
        PlanOnly = [pscustomobject]@{
            Model = if ($planModel) { $planModel.Model } else { $null }
            Roles = @("chat")
            ContextLength = 16384
            MaxTokens = 2048
            KeepAlive = 1800
        }
        DeepReview = [pscustomobject]@{
            Model = if ($reviewModel) { $reviewModel.Model } else { $null }
            Roles = @("chat")
            ContextLength = 32768
            MaxTokens = 4096
            KeepAlive = 1800
        }
    }
    Candidates = @($candidates | Sort-Object `
        @{ Expression = { Get-WorkflowRank -Status $_.ValidationStatus } }, `
        @{ Expression = { if ($_.RecommendedMinVramGb) { [double]$_.RecommendedMinVramGb } else { 9999 } } }, `
        @{ Expression = { $_.Model } })
    Privacy = [pscustomobject]@{
        RepositoryContentSent = $false
        HardwareProfileSentOnline = $false
        PrivatePathsWritten = $false
        EndpointsWritten = $false
        Note = "The recommendation output redacts input paths and does not include hostnames, usernames, endpoints, repository paths, or raw hardware reports."
    }
}

$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

Write-Host "[5/5] Recommendation written to $OutputPath"
Write-Host "Recommendation status: $($report.Recommendation.Status)"
Write-Host "WRITE SAFE model: $($report.Recommendation.WriteSafeModel)"
Write-Host "PLAN ONLY model: $($report.Recommendation.PlanOnlyModel)"
Write-Host "DEEP REVIEW model: $($report.Recommendation.DeepReviewModel)"
Write-Host "Next step: $($report.Recommendation.NextStep)"
