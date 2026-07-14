[CmdletBinding()]
param(
    [string]$EvidenceCatalogPath,
    [string]$ModelCatalogPath,
    [string]$OutputPath,
    [string]$MarkdownOutputPath,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $EvidenceCatalogPath) {
    $EvidenceCatalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
}
if (-not $ModelCatalogPath) {
    $ModelCatalogPath = Join-Path $repoRoot "config/model-recommendations.tsv"
}

$statusRank = @{
    "approved-write-ready" = 100
    "review-validated" = 95
    "plan-validated" = 90
    "write-smoke-validated" = 80
    "read-only-tool-validated" = 65
    "read-only-cli-validated" = 60
    "validated-by-tests" = 55
    "plan-review-candidate" = 45
    "partial-pass" = 35
    "static-validated" = 30
    "candidate-only" = 20
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

function Get-RecommendedUse {
    param(
        [string]$Model,
        [object[]]$CatalogRows
    )

    foreach ($row in $CatalogRows) {
        if ($row.MatchPattern -and $Model -match $row.MatchPattern) {
            return $row.RecommendedUse
        }
        if ($row.FallbackModel -and $Model -eq $row.FallbackModel) {
            return $row.RecommendedUse
        }
    }

    return "Evidence-gated use only; no catalog recommendation is defined for this exact model."
}

function Get-ReadinessLabel {
    param([string]$Status)

    switch ($Status) {
        "approved-write-ready" { "approved-write ready" }
        "review-validated" { "review validated" }
        "plan-validated" { "plan validated" }
        "write-smoke-validated" { "disposable write-smoke validated" }
        "read-only-tool-validated" { "read-only tool validated" }
        "read-only-cli-validated" { "read-only CLI validated" }
        "validated-by-tests" { "script/test validated" }
        "plan-review-candidate" { "plan/review candidate" }
        "partial-pass" { "partial pass" }
        default { "candidate only" }
    }
}

function ConvertTo-Markdown {
    param([object[]]$Rows)

    $lines = @(
        "# Model Scorecard",
        "",
        "Generated from `config/evidence-catalog.tsv` and `config/model-recommendations.tsv`.",
        "",
        "| Model | Surface | OS | Operation | Mode | Readiness | Evidence count |",
        "| --- | --- | --- | --- | --- | --- | ---: |"
    )

    foreach ($row in $Rows) {
        $lines += "| $($row.Model) | $($row.Surface) | $($row.OS) | $($row.Operation) | $($row.ValidationMode) | $($row.Readiness) | $($row.EvidenceCount) |"
    }

    return ($lines -join "`n") + "`n"
}

$evidenceRows = ConvertFrom-Tsv -Path $EvidenceCatalogPath
$catalogRows = @()
if (Test-Path -LiteralPath $ModelCatalogPath) {
    $catalogRows = @(Get-Content -LiteralPath $ModelCatalogPath | Where-Object { $_ -and $_ -notmatch "^#" } | ForEach-Object {
        $parts = $_ -split "\|", 5
        [pscustomobject]@{
            Tier = $parts[0]
            MatchPattern = $parts[1]
            FallbackModel = $parts[2]
            RecommendedUse = $parts[3]
            ValidationNote = $parts[4]
        }
    })
}

$modelRows = @($evidenceRows | Where-Object {
    $_.model -and
    $_.model -notin @("N/A", "local-config", "local Ollama config") -and
    $_.model -notmatch ","
})

$scorecardRows = @($modelRows | Group-Object { "$($_.surface)|$($_.surface_version)|$($_.provider)|$($_.model)|$($_.os)|$($_.operation)|$($_.validation_mode)" } | ForEach-Object {
    $rows = @($_.Group)
    $mostConservative = $rows | Sort-Object { if ($statusRank.ContainsKey($_.status)) { $statusRank[$_.status] } else { 0 } } | Select-Object -First 1
    $score = if ($statusRank.ContainsKey($mostConservative.status)) { $statusRank[$mostConservative.status] } else { 0 }
    $statuses = @($rows | ForEach-Object { $_.status } | Sort-Object -Unique)

    [pscustomobject]@{
        Model = $mostConservative.model
        Surface = $mostConservative.surface
        SurfaceVersion = $mostConservative.surface_version
        Provider = $mostConservative.provider
        OS = $mostConservative.os
        Operation = $mostConservative.operation
        ValidationMode = $mostConservative.validation_mode
        Score = $score
        Status = $mostConservative.status
        Readiness = Get-ReadinessLabel -Status $mostConservative.status
        Statuses = $statuses
        EvidenceCount = $rows.Count
        RecommendedUse = Get-RecommendedUse -Model $mostConservative.model -CatalogRows $catalogRows
        Evidence = @($rows | ForEach-Object {
            [pscustomobject]@{
                Area = $_.area
                Surface = $_.surface
                SurfaceVersion = $_.surface_version
                Provider = $_.provider
                OS = $_.os
                Operation = $_.operation
                ValidationMode = $_.validation_mode
                Status = $_.status
                EvidencePath = $_.evidence
                Notes = $_.notes
            }
        })
    }
} | Sort-Object Score, Model -Descending)

$report = [pscustomobject]@{
    SchemaVersion = 2
    GeneratedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    SourceEvidenceCatalog = "config/evidence-catalog.tsv"
    SourceModelCatalog = "config/model-recommendations.tsv"
    ModelCount = @($modelRows.model | Sort-Object -Unique).Count
    CapabilityCount = $scorecardRows.Count
    Capabilities = $scorecardRows
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
    ConvertTo-Markdown -Rows $scorecardRows | Set-Content -LiteralPath $MarkdownOutputPath -Encoding utf8
}

if ($AsJson -or $OutputPath) {
    $report | ConvertTo-Json -Depth 20
} else {
    ConvertTo-Markdown -Rows $scorecardRows
}

exit 0
