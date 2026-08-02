[CmdletBinding()]
param(
    [string]$RepositoryRoot
)

$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSVersion -lt [version]"5.1") {
    throw "Haven 42 Windows scripts require Windows PowerShell 5.1 or PowerShell 7."
}

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Split-Path -Parent $PSScriptRoot
}
$RepositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$scriptsRoot = Join-Path $RepositoryRoot "scripts"
if (-not (Test-Path -LiteralPath $scriptsRoot -PathType Container)) {
    throw "The repository scripts directory is missing."
}

$parseFailures = New-Object System.Collections.Generic.List[string]
$trackedPaths = @(& git -C $RepositoryRoot ls-files -- "scripts/*.ps1" "scripts/*.psm1")
if ($LASTEXITCODE -ne 0) {
    throw "Git could not enumerate the tracked PowerShell compatibility surface."
}
$scriptsPrefix = $scriptsRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$files = @(
    foreach ($trackedPath in $trackedPaths) {
        $fullPath = [System.IO.Path]::GetFullPath((Join-Path $RepositoryRoot $trackedPath))
        if (-not $fullPath.StartsWith($scriptsPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "A tracked PowerShell path escaped the scripts directory."
        }
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            throw "A tracked PowerShell file is missing: $trackedPath"
        }
        Get-Item -LiteralPath $fullPath
    }
)
if ($files.Count -eq 0) {
    throw "No PowerShell files were found for compatibility validation."
}

foreach ($file in $files) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $file.FullName,
        [ref]$tokens,
        [ref]$errors
    )
    foreach ($error in @($errors)) {
        $relativePath = $file.FullName.Substring($RepositoryRoot.Length + 1)
        $parseFailures.Add(
            "${relativePath}:$($error.Extent.StartLineNumber):$($error.Extent.StartColumnNumber): $($error.Message)"
        )
    }
}
if ($parseFailures.Count -gt 0) {
    throw "PowerShell parser compatibility failed:`n$($parseFailures -join [Environment]::NewLine)"
}

$profileScript = Join-Path $scriptsRoot "get-local-model-profile.windows.ps1"
$profileOutput = @(& $profileScript -AsJson 2>&1)
$profileSucceeded = $?
if (-not $profileSucceeded) {
    throw "Windows hardware profile compatibility smoke failed: $($profileOutput -join ' ')"
}
try {
    $profile = ($profileOutput -join [Environment]::NewLine) | ConvertFrom-Json
}
catch {
    throw "Windows hardware profile did not return valid JSON: $($_.Exception.Message)"
}
if ([string]::IsNullOrWhiteSpace([string]$profile.PowerShellVersion)) {
    throw "Windows hardware profile did not report its PowerShell version."
}
if ([string]::IsNullOrWhiteSpace([string]$profile.OperatingSystem)) {
    throw "Windows hardware profile did not report its operating system."
}
if ($env:OS -eq "Windows_NT") {
    if ($profile.Platform -ne "Windows") {
        throw "Windows hardware profile misidentified the host platform as '$($profile.Platform)'."
    }
    if ($profile.OperatingSystem -eq "Unknown") {
        throw "Windows hardware profile reported an unknown operating system."
    }
}

Write-Host (
    "PowerShell compatibility passed: {0} files parsed and the Windows profile smoke passed under {1} {2}." -f
        $files.Count,
        $PSVersionTable.PSEdition,
        $PSVersionTable.PSVersion
) -ForegroundColor Green
