[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [string]$PackagePath,
    [Parameter(Mandatory = $true)][ValidateSet("windows", "linux", "macos")][string]$HostOs,
    [Parameter(Mandatory = $true)][ValidateSet("x64", "arm64", "intel64")][string]$HostArchitecture,
    [Parameter(Mandatory = $true)][string]$TargetTriple,
    [Parameter(Mandatory = $true)][string]$CurrentVersion,
    [Parameter(Mandatory = $true)][string]$UpdaterVersion,
    [ValidateSet("stable", "beta")][string]$Channel = "stable",
    [switch]$AsJson
)
$ErrorActionPreference = "Stop"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python 3 is required for core update policy evaluation." }
$arguments = @((Join-Path $PSScriptRoot "core-update-policy.py"), "--manifest-path", $ManifestPath, "--host-os", $HostOs, "--host-architecture", $HostArchitecture, "--target-triple", $TargetTriple, "--current-version", $CurrentVersion, "--updater-version", $UpdaterVersion, "--channel", $Channel)
if ($PackagePath) { $arguments += @("--package-path", $PackagePath) }
if ($AsJson) { $arguments += "--json" }
& $python.Source @arguments
exit $LASTEXITCODE
