[CmdletBinding()]
param(
    [string]$EvidenceCatalogPath,
    [string]$SurfaceMatrixPath,
    [string]$SurfaceSolutionPath,
    [string]$OutputPath,
    [string]$MarkdownOutputPath,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $EvidenceCatalogPath) {
    $EvidenceCatalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
}
if (-not $SurfaceMatrixPath) {
    $SurfaceMatrixPath = Join-Path $repoRoot "config/agent-surface-capabilities.json"
}
if (-not $SurfaceSolutionPath) {
    $SurfaceSolutionPath = Join-Path $repoRoot "config/agent-surface-solutions.json"
}

function ConvertFrom-Tsv {
    param([string]$Path)

    $lines = @(Get-Content -LiteralPath $Path | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($lines.Count -lt 2) {
        return @()
    }

    $headers = $lines[0] -split "`t"
    return @($lines | Select-Object -Skip 1 | ForEach-Object {
        $values = $_ -split "`t", $headers.Count
        $row = [ordered]@{}
        for ($i = 0; $i -lt $headers.Count; $i++) {
            $row[$headers[$i]] = if ($i -lt $values.Count) { $values[$i] } else { "" }
        }
        [pscustomobject]$row
    })
}

function ConvertTo-CountRows {
    param(
        [object[]]$Rows,
        [string]$PropertyName,
        [string]$OutputName
    )

    return @($Rows |
        Group-Object $PropertyName |
        Sort-Object Count, Name -Descending |
        ForEach-Object {
            [pscustomobject]@{
                $OutputName = $_.Name
                Count = $_.Count
            }
        })
}

function Get-Models {
    param([object[]]$Rows)

    $ignored = @("N/A", "local Ollama config")
    return @($Rows |
        ForEach-Object { $_.model -split "," } |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -and $_ -notin $ignored } |
        Sort-Object -Unique)
}

function ConvertTo-Markdown {
    param([object]$Report)

    $lines = @(
        "# Evidence Dashboard",
        "",
        "Generated from `config/evidence-catalog.tsv`, `config/agent-surface-capabilities.json`, and `config/agent-surface-solutions.json`.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        "| Evidence rows | $($Report.EvidenceCount) |",
        "| Agent surfaces | $($Report.SurfaceCount) |",
        "| Models with evidence | $($Report.ModelCount) |",
        "",
        "## Evidence Status",
        "",
        "| Status | Count |",
        "| --- | ---: |"
    )

    foreach ($status in @($Report.StatusCounts)) {
        $lines += "| $($status.Status) | $($status.Count) |"
    }

    $lines += @(
        "",
        "## Agent Surfaces",
        "",
        "| Surface | Validation level | Supported | Validated | Planned | Scaffolded | Blocked |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |"
    )

    foreach ($surface in @($Report.SurfaceReadiness)) {
        $lines += "| $($surface.Name) | $($surface.ValidationLevel) | $($surface.SupportedActivities) | $($surface.ValidatedActivities) | $($surface.PlannedActivities) | $($surface.ScaffoldedActivities) | $($surface.BlockedActivities) |"
    }

    $lines += @(
        "",
        "## Install Configure Test",
        "",
        "| Surface | Install | Configure | Test | Validation |",
        "| --- | --- | --- | --- | --- |"
    )

    foreach ($surface in @($Report.SurfaceSolutionReadiness)) {
        $lines += "| $($surface.Name) | $($surface.InstallStatus) | $($surface.ConfigureStatus) | $($surface.TestStatus) | $($surface.ValidationLevel) |"
    }

    $lines += @(
        "",
        "## Models",
        "",
        "| Model |",
        "| --- |"
    )

    foreach ($model in @($Report.Models)) {
        $lines += "| $model |"
    }

    return ($lines -join "`n") + "`n"
}

$evidenceRows = ConvertFrom-Tsv -Path $EvidenceCatalogPath
$surfaceMatrix = Get-Content -LiteralPath $SurfaceMatrixPath -Raw | ConvertFrom-Json
$surfaceSolutions = Get-Content -LiteralPath $SurfaceSolutionPath -Raw | ConvertFrom-Json
$models = Get-Models -Rows $evidenceRows

$surfaceReadiness = @($surfaceMatrix.surfaces | ForEach-Object {
    $surface = $_
    $activities = @($surface.activities.PSObject.Properties | ForEach-Object { $_.Value })
    [pscustomobject]@{
        Id = $surface.id
        Name = $surface.name
        Type = $surface.type
        ValidationLevel = $surface.currentValidationLevel
        ActivityCount = $activities.Count
        SupportedActivities = @($activities | Where-Object { $_.status -eq "supported" }).Count
        ValidatedActivities = @($activities | Where-Object { $_.status -eq "validated" }).Count
        PlannedActivities = @($activities | Where-Object { $_.status -eq "planned" }).Count
        ScaffoldedActivities = @($activities | Where-Object { $_.status -eq "scaffolded" }).Count
        BlockedActivities = @($activities | Where-Object { $_.status -eq "blocked" }).Count
    }
} | Sort-Object Name)

$surfaceSolutionReadiness = @($surfaceSolutions.surfaces | ForEach-Object {
    [pscustomobject]@{
        Id = $_.id
        Name = $_.name
        Type = $_.type
        ValidationLevel = $_.currentValidationLevel
        InstallStatus = $_.install.status
        ConfigureStatus = $_.configure.status
        TestStatus = $_.test.status
        InstallSolution = $_.install.solution
        ConfigureSolution = $_.configure.solution
        TestSolution = $_.test.solution
        InstallBlockedReason = $_.install.blockedReason
        ConfigureBlockedReason = $_.configure.blockedReason
        TestBlockedReason = $_.test.blockedReason
    }
} | Sort-Object Name)

$report = [pscustomobject]@{
    SchemaVersion = 2
    GeneratedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    SourceEvidenceCatalog = "config/evidence-catalog.tsv"
    SourceSurfaceMatrix = "config/agent-surface-capabilities.json"
    SourceSurfaceSolutions = "config/agent-surface-solutions.json"
    EvidenceCount = $evidenceRows.Count
    SurfaceCount = @($surfaceMatrix.surfaces).Count
    SurfaceSolutionCount = @($surfaceSolutions.surfaces).Count
    ModelCount = $models.Count
    StatusCounts = ConvertTo-CountRows -Rows $evidenceRows -PropertyName "status" -OutputName "Status"
    AreaCounts = ConvertTo-CountRows -Rows $evidenceRows -PropertyName "area" -OutputName "Area"
    SurfaceEvidenceCounts = ConvertTo-CountRows -Rows $evidenceRows -PropertyName "surface" -OutputName "Surface"
    OperationCounts = ConvertTo-CountRows -Rows $evidenceRows -PropertyName "operation" -OutputName "Operation"
    ValidationModeCounts = ConvertTo-CountRows -Rows $evidenceRows -PropertyName "validation_mode" -OutputName "ValidationMode"
    Models = $models
    SurfaceReadiness = $surfaceReadiness
    SurfaceSolutionReadiness = $surfaceSolutionReadiness
}

if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding utf8
}

if ($MarkdownOutputPath) {
    $parent = Split-Path -Parent $MarkdownOutputPath
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    ConvertTo-Markdown -Report $report | Set-Content -LiteralPath $MarkdownOutputPath -Encoding utf8
}

if ($AsJson -or $OutputPath) {
    $report | ConvertTo-Json -Depth 20
} else {
    ConvertTo-Markdown -Report $report
}

exit 0
