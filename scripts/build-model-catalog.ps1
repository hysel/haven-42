param(
    [Parameter(Mandatory = $true)]
    [string]$DiscoveryReportPath,
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputPath) {
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/model-catalog-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
}

$python = Get-Command python -ErrorAction SilentlyContinue
$pythonPath = if ($python) { $python.Source } elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { throw "Python 3 is required for model catalog assembly." }
$pythonPrefixArguments = if ($python) { @() } else { @("-3") }

& $pythonPath @pythonPrefixArguments `
    (Join-Path $PSScriptRoot "build-model-catalog.py") `
    "--contract-path" (Join-Path $repoRoot "config/model-catalog-contract.json") `
    "--discovery-report" $DiscoveryReportPath `
    "--evidence-catalog" (Join-Path $repoRoot "config/evidence-catalog.tsv") `
    "--output-path" $OutputPath
exit $LASTEXITCODE
