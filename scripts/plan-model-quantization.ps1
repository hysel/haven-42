param(
    [Parameter(Mandatory = $true)]
    [string]$RequestPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,
    [string]$SupportMatrixPath
)

$ErrorActionPreference = "Stop"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python 3 is required to create a quantization plan."
}

$arguments = @((Join-Path $PSScriptRoot "quantization-planner.py"), "plan", "--request", $RequestPath, "--output", $OutputPath)
if ($SupportMatrixPath) {
    $arguments += @("--support-matrix", $SupportMatrixPath)
}

& $python.Source @arguments
exit $LASTEXITCODE
