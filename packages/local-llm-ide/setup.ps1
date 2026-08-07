$ErrorActionPreference = "Stop"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python 3 is required to configure the IDE tools. Install Python, then run this file again."
}
& $python.Source (Join-Path $PSScriptRoot "haven42_ide.py") @args
exit $LASTEXITCODE
