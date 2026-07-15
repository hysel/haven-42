[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [Alias("target-repo")]
    [string]$TargetRepo,
    [ValidateSet("repository-discovery", "implementation-plan", "code-review", "scoped-write")]
    [string]$Operation = "repository-discovery",
    [Alias("matrix-path")]
    [string]$MatrixPath,
    [Alias("operating-system")]
    [string]$OperatingSystem = "Windows",
    [string]$Surface = "Continue CLI",
    [Alias("surface-version")]
    [string]$SurfaceVersion = "1.5.47",
    [string]$Provider = "Ollama",
    [Alias("output-path")]
    [string]$OutputPath,
    [switch]$AsJson
)
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $MatrixPath) { $MatrixPath = Join-Path $repoRoot "config/language-workflow-validation-matrix.json" }
if (-not (Test-Path -LiteralPath $TargetRepo -PathType Container)) { throw "TargetRepo does not exist: $TargetRepo" }
if (-not (Test-Path -LiteralPath $MatrixPath -PathType Leaf)) { throw "Language workflow matrix does not exist: $MatrixPath" }
$profileJson = & (Join-Path $PSScriptRoot "get-project-profile.ps1") -TargetRepo $TargetRepo -AsJson
$profile = $profileJson | ConvertFrom-Json
$matrix = Get-Content -LiteralPath $MatrixPath -Raw | ConvertFrom-Json
$evidenceCandidates = @($matrix.latestValidation) + @($matrix.nativeOperatingSystemEvidence)
$evidenceContext = @($evidenceCandidates | Where-Object {
    $_.surface -eq $Surface -and $_.surfaceVersion -eq $SurfaceVersion -and $_.provider -eq $Provider -and
    ($_.operatingSystem -eq $OperatingSystem -or $_.operatingSystem -like "$OperatingSystem *")
}) | Select-Object -First 1
$evidenceMatches = $null -ne $evidenceContext
$lanes = [System.Collections.Generic.List[object]]::new()
$unavailable = [System.Collections.Generic.List[object]]::new()
foreach ($pack in @($profile.SelectedRulePacks)) {
    $entry = @($matrix.entries | Where-Object { $_.rulePackId -eq $pack.Id }) | Select-Object -First 1
    if (-not $entry) { $unavailable.Add([pscustomobject]@{ RulePackId = $pack.Id; Ecosystem = $pack.Ecosystem; Reason = "NO_MATRIX_ENTRY" }); continue }
    $status = [string]$entry.operations.$Operation
    $model = [string]$entry.operationModels.$Operation
    if (-not $evidenceMatches -or $status -ne "validated" -or -not $model) {
        $reason = if (-not $evidenceMatches) { "EVIDENCE_CONTEXT_MISMATCH" } else { "OPERATION_NOT_VALIDATED" }
        $unavailable.Add([pscustomobject]@{ RulePackId = $pack.Id; Ecosystem = $pack.Ecosystem; Reason = $reason }); continue
    }
    $lanes.Add([pscustomobject]@{ RulePackId = $pack.Id; Ecosystem = $pack.Ecosystem; Operation = $Operation; Model = $model; Status = "validated"; EvidenceFiles = @($pack.Evidence); EvidenceDocument = [string]$evidenceContext.evidenceDocument })
}
$distinctModels = @($lanes | Select-Object -ExpandProperty Model -Unique)
$result = [pscustomobject]@{
    SchemaVersion = 1
    Status = if ($lanes.Count -gt 0) { "validated-lane-available" } else { "no-validated-lane" }
    Request = [pscustomobject]@{ Operation = $Operation; Surface = $Surface; SurfaceVersion = $SurfaceVersion; Provider = $Provider; OperatingSystem = $OperatingSystem }
    Project = [pscustomobject]@{ PrimaryEcosystem = $profile.PrimaryEcosystem; Confidence = $profile.Confidence; SelectedRulePackIds = @($profile.SelectedRulePackIds) }
    Lanes = @($lanes)
    Unavailable = @($unavailable)
    ContinueModelProfiles = @($distinctModels | ForEach-Object { [pscustomobject]@{ Name = "Validated $Operation lane - $_"; Model = $_; Roles = @("chat", "edit", "apply") } })
    Limitation = "This recommendation selects evidence-backed lanes. Agent surfaces must still explicitly select a model or profile; runtime auto-switching is not assumed."
    Evidence = [pscustomobject]@{ Date = $evidenceContext.date; Document = $evidenceContext.evidenceDocument; ValidatedCells = $evidenceContext.validatedCells; FailedCells = $evidenceContext.failedCells; OperatingSystem = $evidenceContext.operatingSystem }
    Privacy = [pscustomobject]@{ TargetPathRecorded = $false; FileContentsReadBySelector = $false }
}
$json = $result | ConvertTo-Json -Depth 12
if ($OutputPath) { $parent = Split-Path -Parent $OutputPath; if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }; Set-Content -LiteralPath $OutputPath -Value $json -Encoding utf8 }
if ($AsJson -or -not $OutputPath) { Write-Output $json }
else { Write-Host "Language model lane status: $($result.Status)"; Write-Host "Recommended models: $(if ($distinctModels.Count) { $distinctModels -join ', ' } else { 'none' })"; Write-Host "Recommendation written to $OutputPath" }
