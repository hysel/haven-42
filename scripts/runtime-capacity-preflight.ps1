[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProfilePath,
    [Parameter(Mandatory = $true)][int]$RequiredAcceleratorMiB,
    [Parameter(Mandatory = $true)][int]$RequiredSystemMiB,
    [Parameter(Mandatory = $true)][int]$RequiredDiskMiB,
    [int]$ReserveMiB = 1024,
    [int]$MaxUtilizationPercent = 20,
    [switch]$AsJson
)
$ErrorActionPreference = "Stop"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python 3 is required for runtime capacity preflight." }
$arguments = @(
    (Join-Path $PSScriptRoot "runtime-capacity-preflight.py"),
    "--profile-path", $ProfilePath,
    "--required-accelerator-mib", $RequiredAcceleratorMiB,
    "--required-system-mib", $RequiredSystemMiB,
    "--required-disk-mib", $RequiredDiskMiB,
    "--reserve-mib", $ReserveMiB,
    "--max-utilization-percent", $MaxUtilizationPercent
)
if ($AsJson) { $arguments += "--json" }
& $python.Source @arguments
exit $LASTEXITCODE
