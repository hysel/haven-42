param(
    [Parameter(Mandatory = $true)]
    [string]$ModelProfilePath,
    [string]$ModelCatalogPath,
    [string]$ModelFitCatalogPath,
    [string]$EvidenceCatalogPath,
    [string]$OutputPath,
    [string]$Surface = "Continue Agent",
    [string]$SurfaceVersion = "not-recorded",
    [string]$Provider = "Ollama",
    [ValidateRange(1024, 1048576)]
    [int]$ContextTargetTokens = 16384,
    [ValidateRange(0, 1024)]
    [Nullable[double]]$MemoryReserveGb,
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

if (-not $ModelFitCatalogPath) {
    $ModelFitCatalogPath = Join-Path $repoRoot "config/model-fit-profiles.json"
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

function Read-ModelFitCatalog {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "ModelFitCatalogPath does not exist: $Path"
    }

    $catalog = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    if ($catalog.schemaVersion -ne 1 -or $null -eq $catalog.defaults -or $null -eq $catalog.profiles) {
        throw "Model fit catalog must use schemaVersion 1 and define defaults and profiles."
    }
    return $catalog
}

function Get-ModelFitEstimate {
    param(
        [string]$Model,
        [object]$FitCatalog,
        [int]$TargetContextTokens,
        [Nullable[double]]$ReserveOverrideGb
    )

    $profile = @($FitCatalog.profiles | Where-Object { $Model -match $_.matchPattern } | Select-Object -First 1)[0]
    if ($profile) {
        $baseline = [math]::Max(1, [double]$profile.baselineContextTokens)
        $kvCache = [double]$profile.kvCacheGbAtBaseline * ($TargetContextTokens / $baseline)
        $subtotal = [double]$profile.estimatedWeightsGb + $kvCache + [double]$profile.runtimeOverheadGb
        $fixedReserve = if ($null -ne $ReserveOverrideGb) { [double]$ReserveOverrideGb } elseif ($null -ne $profile.memoryReserveGb) { [double]$profile.memoryReserveGb } else { [double]$FitCatalog.defaults.memoryReserveGb }
        $reservePercent = if ($null -ne $profile.memoryReservePercent) { [double]$profile.memoryReservePercent } else { [double]$FitCatalog.defaults.memoryReservePercent }
        $reserve = if ($null -ne $ReserveOverrideGb) { $fixedReserve } else { [math]::Max($fixedReserve, $subtotal * ($reservePercent / 100)) }

        return [pscustomobject]@{
            Source = "model-fit-catalog"
            Confidence = "curated-estimate"
            ProfileId = $profile.id
            Architecture = $profile.architecture
            ParameterCountBillion = $profile.parameterCountBillion
            ActiveParameterCountBillion = $profile.activeParameterCountBillion
            QuantizationAssumption = $profile.quantizationAssumption
            ContextTargetTokens = $TargetContextTokens
            EstimatedWeightsGb = [math]::Round([double]$profile.estimatedWeightsGb, 2)
            EstimatedKvCacheGb = [math]::Round($kvCache, 2)
            RuntimeOverheadGb = [math]::Round([double]$profile.runtimeOverheadGb, 2)
            MemoryReserveGb = [math]::Round($reserve, 2)
            EstimatedRequiredVramGb = [math]::Round($subtotal + $reserve, 2)
        }
    }

    $heuristic = Get-RecommendedMinVramGb -Model $Model
    $reserve = if ($null -ne $ReserveOverrideGb -and $heuristic -gt 0 -and $heuristic -lt 999999) { [double]$ReserveOverrideGb } else { 0 }
    return [pscustomobject]@{
        Source = "model-name-heuristic"
        Confidence = "low"
        ProfileId = $null
        Architecture = "unknown"
        ParameterCountBillion = Get-ModelSizeBillion -Model $Model
        ActiveParameterCountBillion = $null
        QuantizationAssumption = "unknown"
        ContextTargetTokens = $TargetContextTokens
        EstimatedWeightsGb = $null
        EstimatedKvCacheGb = $null
        RuntimeOverheadGb = $null
        MemoryReserveGb = if ($reserve -gt 0) { $reserve } else { $null }
        EstimatedRequiredVramGb = if ($heuristic -gt 0 -and $heuristic -lt 999999) { [math]::Round($heuristic + $reserve, 2) } else { $null }
    }
}

function Get-WorkflowRank {
    param([string]$Status)

    switch ($Status) {
        "approved-write-ready" { return 0 }
        "review-validated" { return 0 }
        "plan-validated" { return 0 }
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

    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    return @(Import-Csv -LiteralPath $Path -Delimiter "`t")
}

function Get-EvidenceStatusRank {
    param([string]$Status)

    switch ($Status) {
        "approved-write-ready" { return 100 }
        "review-validated" { return 95 }
        "plan-validated" { return 90 }
        "write-smoke-validated" { return 80 }
        "read-only-tool-validated" { return 70 }
        "read-only-cli-validated" { return 60 }
        "plan-review-candidate" { return 50 }
        "validated-by-tests" { return 45 }
        "static-validated" { return 40 }
        "partial-pass" { return 20 }
        "candidate-only" { return 10 }
        default { return 0 }
    }
}

function Get-AggregatedEvidence {
    param(
        [object[]]$Rows,
        [string]$Model,
        [string]$TargetSurface,
        [string]$TargetSurfaceVersion,
        [string]$TargetProvider,
        [string]$OperatingSystem,
        [string]$Operation,
        [string]$ValidationMode
    )

    $matches = @($Rows | Where-Object {
        $_.schema_version -eq "2" -and
        $_.area -eq "model-tool-use" -and
        $_.model -eq $Model -and
        $_.surface -eq $TargetSurface -and
        $_.surface_version -eq $TargetSurfaceVersion -and
        $_.provider -eq $TargetProvider -and
        $_.os -eq $OperatingSystem -and
        $_.operation -eq $Operation -and
        $_.validation_mode -eq $ValidationMode
    })

    if ($matches.Count -eq 0) { return $null }
    $mostConservative = $matches | Sort-Object { Get-EvidenceStatusRank -Status $_.status } | Select-Object -First 1

    return [pscustomobject]@{
        Status = $mostConservative.status
        RecordCount = $matches.Count
        Evidence = @($matches | ForEach-Object { $_.evidence } | Sort-Object -Unique)
        Notes = @($matches | ForEach-Object { $_.notes } | Sort-Object -Unique)
        Key = [pscustomobject]@{
            Surface = $TargetSurface
            SurfaceVersion = $TargetSurfaceVersion
            Provider = $TargetProvider
            Model = $Model
            OS = $OperatingSystem
            Operation = $Operation
            ValidationMode = $ValidationMode
        }
    }
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
        [object[]]$EvidenceRows,
        [string]$Surface,
        [string]$SurfaceVersion,
        [string]$Provider,
        [string]$OperatingSystem,
        [Nullable[double]]$AvailableVramGb,
        [string]$Platform
    )

    if ([string]::IsNullOrWhiteSpace($Model)) { return }
    $modelName = $Model.Trim()
    if ($Seen.ContainsKey($modelName)) { return }
    $Seen[$modelName] = $true

    $fitEstimate = Get-ModelFitEstimate -Model $modelName -FitCatalog $modelFitCatalog -TargetContextTokens $ContextTargetTokens -ReserveOverrideGb $MemoryReserveGb
    $minVram = if ($null -ne $fitEstimate.EstimatedRequiredVramGb) { [double]$fitEstimate.EstimatedRequiredVramGb } elseif ($modelName -match '(?i)(cloud|-mlx)') { 999999 } else { 0 }
    $fitsVram = $true
    if ($null -ne $AvailableVramGb -and $minVram -gt 0 -and $minVram -lt 999999) {
        $fitsVram = $minVram -le $AvailableVramGb
    }
    elseif ($minVram -ge 999999) {
        $fitsVram = $false
    }

    $writeEvidence = Get-AggregatedEvidence -Rows $EvidenceRows -Model $modelName -TargetSurface $Surface -TargetSurfaceVersion $SurfaceVersion -TargetProvider $Provider -OperatingSystem $OperatingSystem -Operation "scoped-write" -ValidationMode "editor-agent"
    $planEvidence = Get-AggregatedEvidence -Rows $EvidenceRows -Model $modelName -TargetSurface $Surface -TargetSurfaceVersion $SurfaceVersion -TargetProvider $Provider -OperatingSystem $OperatingSystem -Operation "plan" -ValidationMode "editor-agent"
    $reviewEvidence = Get-AggregatedEvidence -Rows $EvidenceRows -Model $modelName -TargetSurface $Surface -TargetSurfaceVersion $SurfaceVersion -TargetProvider $Provider -OperatingSystem $OperatingSystem -Operation "review" -ValidationMode "editor-agent"
    $validationStatus = if ($writeEvidence) { $writeEvidence.Status } else { "candidate-only" }
    $eligibility = Get-PlatformEligibility -Model $modelName -Platform $Platform

    $Candidates.Add([pscustomobject]@{
        Model = $modelName
        Source = $Source
        ValidationStatus = $validationStatus
        Evidence = if ($writeEvidence) { $writeEvidence.Evidence } else { @() }
        OperationEvidence = [pscustomobject]@{
            ScopedWrite = $writeEvidence
            Plan = $planEvidence
            Review = $reviewEvidence
        }
        RecommendedMinVramGb = if ($minVram -gt 0 -and $minVram -lt 999999) { $minVram } else { $null }
        ModelFit = $fitEstimate
        FitsAvailableVram = [bool]$fitsVram
        Installed = $modelName -in @($installedModels)
        ModelSizeBillion = Get-ModelSizeBillion -Model $modelName
        PlatformEligible = [bool]$eligibility.Eligible
        PlatformReason = $eligibility.Reason
        RecommendedUse = if ($CatalogRow) { $CatalogRow.RecommendedUse } else { "Validate locally before relying on this model." }
        ValidationNote = if ($CatalogRow) { $CatalogRow.ValidationNote } else { "Run read-only and approved-write smoke tests before granting edit/apply roles." }
    })
}

function Get-LaneScore {
    param(
        [object]$Candidate,
        [ValidateSet("write", "plan", "review")][string]$Purpose,
        [Nullable[double]]$AvailableVramGb
    )

    $laneName = switch ($Purpose) {
        "write" { "WRITE SAFE" }
        "plan" { "PLAN ONLY" }
        default { "DEEP REVIEW" }
    }
    $evidence = switch ($Purpose) {
        "write" { $Candidate.OperationEvidence.ScopedWrite }
        "plan" { $Candidate.OperationEvidence.Plan }
        default { $Candidate.OperationEvidence.Review }
    }
    $requiredStatus = switch ($Purpose) {
        "write" { "approved-write-ready" }
        "plan" { "plan-validated" }
        default { "review-validated" }
    }

    $reasons = [System.Collections.Generic.List[string]]::new()
    if (-not $Candidate.PlatformEligible) { $reasons.Add($Candidate.PlatformReason) }
    if (-not $Candidate.FitsAvailableVram) { $reasons.Add("Model does not fit the selected VRAM estimate.") }
    if (-not $evidence -or $evidence.Status -ne $requiredStatus) {
        $actual = if ($evidence) { $evidence.Status } else { "missing" }
        $reasons.Add("Exact $Purpose evidence requires $requiredStatus; found $actual.")
    }

    $eligible = $reasons.Count -eq 0
    $score = 0.0
    if ($eligible) {
        $score += (Get-EvidenceStatusRank -Status $evidence.Status) * 100
        if ($Candidate.Installed) {
            $score += if ($Purpose -eq "write") { 500 } else { 100 }
            $reasons.Add("Installed model bonus applied.")
        }

        if ($Purpose -eq "write") {
            if ($null -ne $AvailableVramGb -and $Candidate.RecommendedMinVramGb) {
                $headroom = [math]::Max(0, [double]$AvailableVramGb - [double]$Candidate.RecommendedMinVramGb)
                $score += $headroom * 10
                $reasons.Add("Reliability-first VRAM headroom score: $([math]::Round($headroom, 2)) GB.")
            }
            $score -= (Get-ModelPreferenceRank -Model $Candidate.Model) * 10
        } else {
            $capacity = if ($Candidate.ModelSizeBillion -gt 0) { [double]$Candidate.ModelSizeBillion } elseif ($Candidate.RecommendedMinVramGb) { [double]$Candidate.RecommendedMinVramGb } else { 0 }
            $score += $capacity * 20
            $reasons.Add("Capacity score applied for a fitting $laneName model: $capacity.")
        }
    }

    return [pscustomobject]@{
        Eligible = $eligible
        Score = [math]::Round($score, 2)
        RequiredStatus = $requiredStatus
        EvidenceStatus = if ($evidence) { $evidence.Status } else { "missing" }
        Rationale = @($reasons)
    }
}

function Add-LaneScores {
    param([object[]]$Candidates, [Nullable[double]]$AvailableVramGb)

    foreach ($candidate in $Candidates) {
        $candidate | Add-Member -NotePropertyName LaneScores -NotePropertyValue ([pscustomobject]@{
            WriteSafe = Get-LaneScore -Candidate $candidate -Purpose "write" -AvailableVramGb $AvailableVramGb
            PlanOnly = Get-LaneScore -Candidate $candidate -Purpose "plan" -AvailableVramGb $AvailableVramGb
            DeepReview = Get-LaneScore -Candidate $candidate -Purpose "review" -AvailableVramGb $AvailableVramGb
        }) -Force
    }
}

function Select-PrimaryModel {
    param(
        [object[]]$Candidates,
        [string]$Purpose
    )

    $scoreProperty = switch ($Purpose) {
        "write" { "WriteSafe" }
        "plan" { "PlanOnly" }
        default { "DeepReview" }
    }
    $eligible = @($Candidates | Where-Object { $_.LaneScores.$scoreProperty.Eligible })

    if ($eligible.Count -eq 0) { return $null }

    return @($eligible | Sort-Object `
        @{ Expression = { $_.LaneScores.$scoreProperty.Score }; Descending = $true }, `
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
$evidenceRows = @(Read-EvidenceCatalog -Path $EvidenceCatalogPath)
$modelFitCatalog = Read-ModelFitCatalog -Path $ModelFitCatalogPath

Write-Host "[3/5] Building hardware-aware candidate list..."
$candidates = [System.Collections.Generic.List[object]]::new()
$seen = @{}

foreach ($row in $catalogRows) {
    if ($row.MatchPattern) {
        foreach ($installedModel in $installedModels) {
            if ($installedModel -match $row.MatchPattern) {
                Add-Candidate -Candidates $candidates -Seen $seen -Model $installedModel -Source "installed-catalog-match" -CatalogRow $row -EvidenceRows $evidenceRows -Surface $Surface -SurfaceVersion $SurfaceVersion -Provider $Provider -OperatingSystem $platform -AvailableVramGb $availableVramGb -Platform $platform
            }
        }
    }

    if ($row.FallbackModel) {
        Add-Candidate -Candidates $candidates -Seen $seen -Model $row.FallbackModel -Source "catalog-fallback" -CatalogRow $row -EvidenceRows $evidenceRows -Surface $Surface -SurfaceVersion $SurfaceVersion -Provider $Provider -OperatingSystem $platform -AvailableVramGb $availableVramGb -Platform $platform
    }
}

foreach ($modelName in @($evidenceRows | Where-Object {
    $_.schema_version -eq "2" -and $_.area -eq "model-tool-use" -and
    $_.surface -eq $Surface -and $_.surface_version -eq $SurfaceVersion -and
    $_.provider -eq $Provider -and $_.os -eq $platform
} | ForEach-Object { $_.model } | Sort-Object -Unique)) {
    Add-Candidate -Candidates $candidates -Seen $seen -Model $modelName -Source "evidence-catalog" -CatalogRow $null -EvidenceRows $evidenceRows -Surface $Surface -SurfaceVersion $SurfaceVersion -Provider $Provider -OperatingSystem $platform -AvailableVramGb $availableVramGb -Platform $platform
}

Write-Host "[4/5] Selecting model lanes and config defaults..."
Add-LaneScores -Candidates $candidates -AvailableVramGb $availableVramGb
$writeModel = Select-PrimaryModel -Candidates $candidates -Purpose "write"
$planModel = Select-PrimaryModel -Candidates $candidates -Purpose "plan"
$reviewModel = Select-PrimaryModel -Candidates $candidates -Purpose "review"

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
    ModelFitCatalogPath = "redacted"
    EvidenceCatalogPath = "redacted"
    Platform = $platform
    EvidenceContractVersion = 2
    EvidenceTarget = [pscustomobject]@{
        Surface = $Surface
        SurfaceVersion = $SurfaceVersion
        Provider = $Provider
        OS = $platform
    }
    CpuArchitecture = $profile.CpuArchitecture
    SystemRamGb = $profile.SystemRamGb
    VramSelectionMode = $VramSelectionMode
    AvailableVramGb = $availableVramGb
    InstalledModelCount = $installedModels.Count
    FitPolicy = [pscustomobject]@{
        Version = 1
        ContextTargetTokens = $ContextTargetTokens
        MemoryReserveOverrideGb = $MemoryReserveGb
        CatalogSchemaVersion = $modelFitCatalog.schemaVersion
        UnknownModelPolicy = $modelFitCatalog.defaults.unknownModelPolicy
        Note = "Catalog values are planning estimates; verify the installed artifact and runtime behavior before relying on a borderline fit."
    }
    SelectionPolicy = [pscustomobject]@{
        Version = 1
        WriteSafe = "Exact approved-write evidence first; prefer installed models and greater VRAM headroom."
        PlanOnly = "Exact plan evidence first; prefer greater fitting model capacity with a small installed-model bonus."
        DeepReview = "Exact review evidence first; prefer greater fitting model capacity with a small installed-model bonus."
        UnknownModelSizeBehavior = "Unknown sizes receive no capacity bonus and remain subject to exact evidence and platform checks."
    }
    Recommendation = [pscustomobject]@{
        Status = $recommendationStatus
        WriteSafeModel = if ($writeModel) { $writeModel.Model } else { $null }
        PlanOnlyModel = if ($planModel) { $planModel.Model } else { $null }
        DeepReviewModel = if ($reviewModel) { $reviewModel.Model } else { $null }
        Reason = "Selected with lane-specific evidence, platform, VRAM, installation, headroom, and capacity scores."
        NextStep = $nextStep
    }
    ModelLanes = [pscustomobject]@{
        Contract = "surface-neutral"
        WriteSafe = [pscustomobject]@{
            Model = if ($writeModel) { $writeModel.Model } else { $null }
            RequiresValidationStatus = "approved-write-ready"
            ToolUse = "approved-write"
            RecommendedRoles = @("chat", "edit", "apply")
            RequiresSurfaceConfigGenerator = $true
            RequiresEditorSmokeTest = $true
        }
        PlanOnly = [pscustomobject]@{
            Model = if ($planModel) { $planModel.Model } else { $null }
            RequiresValidationStatus = "plan-validated for the exact capability key"
            ToolUse = "plan-review"
            RecommendedRoles = @("chat")
            RequiresSurfaceConfigGenerator = $true
            RequiresEditorSmokeTest = $true
        }
        DeepReview = [pscustomobject]@{
            Model = if ($reviewModel) { $reviewModel.Model } else { $null }
            RequiresValidationStatus = "review-validated for the exact capability key"
            ToolUse = "deep-review"
            RecommendedRoles = @("chat")
            RequiresSurfaceConfigGenerator = $true
            RequiresEditorSmokeTest = $true
        }
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
