param(
    [string]$Version = "",
    [string]$OutputDirectory = "dist",
    [ValidateSet("zip")]
    [string]$Format = "zip",
    [switch]$DryRun,
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot ".continue/config.yaml"

function Get-PackVersion {
    if ($Version) { return $Version.TrimStart("v") }

    $versionLine = Get-Content -LiteralPath $configPath | Where-Object { $_ -match "^version:\s*" } | Select-Object -First 1
    if (-not $versionLine) {
        throw "Could not read version from .continue/config.yaml. Use -Version <semver>."
    }

    return ($versionLine -replace "^version:\s*", "").Trim()
}

function Assert-CleanGitTree {
    if ($AllowDirty) { return }

    $status = git -C $repoRoot status --short
    if ($LASTEXITCODE -ne 0) {
        throw "Git status failed. Run from a Git working tree or use -AllowDirty for local packaging tests."
    }

    if ($status) {
        throw "Working tree has uncommitted changes. Commit or stash before packaging, or use -AllowDirty for local packaging tests."
    }
}

function Copy-PackFile {
    param(
        [string]$RelativePath,
        [string]$DestinationRoot
    )

    $source = Join-Path $repoRoot $RelativePath
    $destination = Join-Path $DestinationRoot $RelativePath
    $destinationParent = Split-Path -Parent $destination
    New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
}

$packVersion = Get-PackVersion
if ($packVersion -notmatch "^\d+\.\d+\.\d+([-.][0-9A-Za-z.-]+)?$") {
    throw "Version '$packVersion' is not a supported semantic version."
}

$packageName = "haven-42-$packVersion"
$outputRoot = if ([System.IO.Path]::IsPathRooted($OutputDirectory)) { $OutputDirectory } else { Join-Path $repoRoot $OutputDirectory }
$archivePath = Join-Path $outputRoot "$packageName.zip"
$checksumPath = Join-Path $outputRoot "$packageName.sha256"
$manifestPath = Join-Path $outputRoot "$packageName.manifest.txt"

$excludedPatterns = @(
    "^\.git/",
    "^\.vscode/",
    "^runtime-validation-output/",
    "^dist/",
    "^\.continue/config\.local.*",
    "^\.continue\.backup-",
    "(^|/)config\.local\.yaml$",
    "(^|/)\.env(\.|$)?",
    "(^|/)secrets?(\.|/|$)",
    "(^|/)token(s)?(\.|/|$)"
)

$trackedFiles = git -C $repoRoot ls-files
if ($LASTEXITCODE -ne 0) {
    throw "git ls-files failed. Release packaging requires a Git working tree."
}

$packageFiles = @(
    $trackedFiles |
        Where-Object { $_ -and ($_ -notmatch "\\") } |
        Where-Object {
            $path = $_
            -not ($excludedPatterns | Where-Object { $path -match $_ })
        } |
        Sort-Object -Unique
)

if (-not $packageFiles) {
    throw "No package files were selected."
}

Write-Host "Release package plan"
Write-Host "Version: $packVersion"
Write-Host "Archive: $archivePath"
Write-Host "Checksum: $checksumPath"
Write-Host "Manifest: $manifestPath"
Write-Host "Files: $($packageFiles.Count)"
Write-Host "Excluded: .git, .vscode, runtime-validation-output, dist, local configs, backups, env/secrets/token files"

if ($DryRun) {
    Write-Host "Dry run only. No release files were written."
    exit 0
}

Assert-CleanGitTree

New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "haven-42-release-$([guid]::NewGuid())"
$packageRoot = Join-Path $tempRoot $packageName

try {
    New-Item -ItemType Directory -Force -Path $packageRoot | Out-Null

    foreach ($file in $packageFiles) {
        Copy-PackFile -RelativePath $file -DestinationRoot $packageRoot
    }

    if (Test-Path -LiteralPath $archivePath) { Remove-Item -LiteralPath $archivePath -Force }
    if (Test-Path -LiteralPath $checksumPath) { Remove-Item -LiteralPath $checksumPath -Force }
    if (Test-Path -LiteralPath $manifestPath) { Remove-Item -LiteralPath $manifestPath -Force }

    Compress-Archive -Path $packageRoot -DestinationPath $archivePath -CompressionLevel Optimal

    $hash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $(Split-Path -Leaf $archivePath)" | Set-Content -LiteralPath $checksumPath -Encoding ascii
    $packageFiles | Set-Content -LiteralPath $manifestPath -Encoding utf8

    Write-Host "Release archive written: $archivePath"
    Write-Host "Checksum written: $checksumPath"
    Write-Host "Manifest written: $manifestPath"
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
