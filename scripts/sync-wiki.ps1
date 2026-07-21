[CmdletBinding()]
param(
    [string]$WikiPath,
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($WikiPath)) {
    $WikiPath = "$repoRoot.wiki"
}
$WikiPath = [System.IO.Path]::GetFullPath($WikiPath)
if (-not (Test-Path -LiteralPath $WikiPath -PathType Container)) {
    throw "Wiki directory does not exist: $WikiPath"
}

$mapPath = Join-Path $repoRoot "config/wiki-sync.tsv"
$retiredPath = Join-Path $repoRoot "config/wiki-retired-pages.txt"
$entries = @(Import-Csv -LiteralPath $mapPath -Delimiter "`t")
if ($entries.Count -eq 0) {
    throw "Wiki synchronization map is empty: $mapPath"
}

$differences = [System.Collections.Generic.List[string]]::new()
foreach ($entry in $entries) {
    $sourcePath = Join-Path $repoRoot $entry.source
    $destinationPath = Join-Path $WikiPath $entry.page
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Mapped wiki source does not exist: $($entry.source)"
    }
    $sourceBytes = [System.IO.File]::ReadAllBytes($sourcePath)
    $matches = (Test-Path -LiteralPath $destinationPath -PathType Leaf) -and
        [System.Linq.Enumerable]::SequenceEqual($sourceBytes, [System.IO.File]::ReadAllBytes($destinationPath))
    if (-not $matches) {
        $differences.Add($entry.page)
        if (-not $Check) {
            [System.IO.File]::WriteAllBytes($destinationPath, $sourceBytes)
            Write-Output "SYNC $($entry.page)"
        }
    }
}

$sidebarLines = @("- [Home](Home)")
foreach ($entry in $entries | Select-Object -Skip 1) {
    $sidebarLines += "- [$($entry.title)]($([System.IO.Path]::GetFileNameWithoutExtension($entry.page)))"
}
$sidebarContent = ($sidebarLines -join "`n") + "`n"
$sidebarPath = Join-Path $WikiPath "_Sidebar.md"
$currentSidebar = if (Test-Path -LiteralPath $sidebarPath -PathType Leaf) {
    ([System.IO.File]::ReadAllText($sidebarPath) -replace "`r`n", "`n")
} else { "" }
if ($currentSidebar -ne $sidebarContent) {
    $differences.Add("_Sidebar.md")
    if (-not $Check) {
        [System.IO.File]::WriteAllText($sidebarPath, $sidebarContent, [System.Text.UTF8Encoding]::new($false))
        Write-Output "SYNC _Sidebar.md"
    }
}

foreach ($retiredPage in Get-Content -LiteralPath $retiredPath) {
    $retiredPage = $retiredPage.Trim()
    if ([string]::IsNullOrWhiteSpace($retiredPage)) { continue }
    $retiredWikiPath = Join-Path $WikiPath $retiredPage
    if (Test-Path -LiteralPath $retiredWikiPath) {
        $differences.Add($retiredPage)
        if (-not $Check) {
            Remove-Item -LiteralPath $retiredWikiPath
            Write-Output "REMOVE $retiredPage"
        }
    }
}

if ($Check -and $differences.Count -gt 0) {
    Write-Error "Wiki is out of date: $($differences -join ', ')"
    exit 1
}
if ($Check) {
    Write-Output "Wiki synchronization check passed for $($entries.Count) mapped pages."
} else {
    Write-Output "Wiki synchronization completed for $($entries.Count) mapped pages."
}
