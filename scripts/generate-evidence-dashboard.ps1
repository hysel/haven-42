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
$scriptPath = Join-Path $PSScriptRoot "evidence_dashboard.py"
$candidates = @(
    @{ Name = "python"; Prefix = @() },
    @{ Name = "python3"; Prefix = @() },
    @{ Name = "py"; Prefix = @("-3") }
)
$python = $null
foreach ($candidate in $candidates) {
    $command = Get-Command $candidate.Name -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { continue }
    & $command.Source @($candidate.Prefix) -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $python = [pscustomobject]@{ Source = $command.Source; Prefix = $candidate.Prefix }
        break
    }
}
if (-not $python) {
    throw "Python 3 is required to generate the evidence dashboard."
}

$arguments = @($python.Prefix) + @($scriptPath)
if ($EvidenceCatalogPath) { $arguments += @("--evidence-catalog-path", $EvidenceCatalogPath) }
if ($SurfaceMatrixPath) { $arguments += @("--surface-matrix-path", $SurfaceMatrixPath) }
if ($SurfaceSolutionPath) { $arguments += @("--surface-solution-path", $SurfaceSolutionPath) }
if ($OutputPath) { $arguments += @("--output-path", $OutputPath) }
if ($MarkdownOutputPath) { $arguments += @("--markdown-output-path", $MarkdownOutputPath) }
if ($AsJson) { $arguments += "--as-json" }

& $python.Source @arguments
exit $LASTEXITCODE
