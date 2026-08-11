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
$navigationPath = Join-Path $repoRoot "config/wiki-navigation.tsv"
$retiredPath = Join-Path $repoRoot "config/wiki-retired-pages.txt"
$entries = @(Import-Csv -LiteralPath $mapPath -Delimiter "`t")
if ($entries.Count -eq 0) {
    throw "Wiki synchronization map is empty: $mapPath"
}
$navigationEntries = @(Import-Csv -LiteralPath $navigationPath -Delimiter "`t")
if ($navigationEntries.Count -eq 0) {
    throw "Wiki navigation map is empty: $navigationPath"
}
if ($navigationEntries.Count -lt 10 -or $navigationEntries.Count -gt 25) {
    throw "Wiki navigation must contain between 10 and 25 primary links: $navigationPath"
}

function Get-RenderedWikiText {
    param(
        [Parameter(Mandatory)]$Entry,
        [Parameter(Mandatory)][string]$SourceText
    )
    if ($Entry.page -notlike 'Eng-*.md') {
        return $SourceText
    }
    $source = ($Entry.source -replace '\\', '/')
    $sourceUrl = "https://github.com/hysel/haven-42/blob/main/$source"
    return "# $($Entry.title)`n`n> **Internal engineering page:** This is an internal engineering page - see [Home](Home) if you are trying to install or use Haven 42.`n`nThe canonical document is [$source]($sourceUrl).`n"
}

$differences = [System.Collections.Generic.List[string]]::new()
$mappedPages = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$repoPrefix = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$wikiPrefix = $WikiPath.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
foreach ($entry in $entries) {
    if ([string]::IsNullOrWhiteSpace($entry.source) -or [string]::IsNullOrWhiteSpace($entry.page) -or
        $entry.page -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*\.md$') {
        throw "Invalid wiki synchronization entry: source='$($entry.source)' page='$($entry.page)'"
    }
    if (-not $mappedPages.Add($entry.page)) {
        throw "Duplicate mapped wiki page: $($entry.page)"
    }
    $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $entry.source))
    $destinationPath = [System.IO.Path]::GetFullPath((Join-Path $WikiPath $entry.page))
    if (-not $sourcePath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Mapped wiki source escapes the repository: $($entry.source)"
    }
    if (-not $destinationPath.StartsWith($wikiPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Mapped wiki page escapes the wiki directory: $($entry.page)"
    }
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Mapped wiki source does not exist: $($entry.source)"
    }
}

$mappedPageStems = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($page in $mappedPages) {
    [void]$mappedPageStems.Add([System.IO.Path]::GetFileNameWithoutExtension($page))
}
foreach ($entry in $entries) {
    $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $entry.source))
    $sourceText = [System.IO.File]::ReadAllText($sourcePath)
    if ([System.IO.Path]::GetFileName($entry.source) -like 'wiki-*.md' -and
        $sourceText -notmatch '(?s)[^\r\n](?:\r\n|\n)\z') {
        throw "Mapped wiki source must end with exactly one newline: $($entry.source)"
    }
    $h1Count = ([regex]::Matches($sourceText, '(?m)^# [^#\r\n]')).Count
    if ($h1Count -ne 1) {
        throw "Mapped wiki source must contain exactly one level-one heading: $($entry.source)"
    }
    $fenceCount = ([regex]::Matches($sourceText, '(?m)^```')).Count
    if (($fenceCount % 2) -ne 0) {
        throw "Mapped wiki source contains an unmatched code fence: $($entry.source)"
    }
    if ([System.IO.Path]::GetFileName($entry.source) -like 'wiki-*.md' -and $sourceText -match '<br\s*/?>') {
        throw "User-facing wiki source contains an HTML line break: $($entry.source)"
    }
    if ($sourceText -match '(?m)^\|[^\r\n]*\[\[') {
        throw "Wiki-style link inside a Markdown table must use standard Markdown syntax: $($entry.source)"
    }
    if ($entry.page -notlike 'Eng-*.md') {
        foreach ($match in [regex]::Matches($sourceText, '\[\[(?:[^\]|]+\|)?([^\]#]+)(?:#[^\]]+)?\]\]')) {
            $target = $match.Groups[1].Value.Trim()
            if (-not $mappedPageStems.Contains($target)) {
                throw "Broken wiki link in $($entry.source): $target"
            }
        }
        foreach ($match in [regex]::Matches($sourceText, '(?<!\!)\[[^\]]+\]\(([^)#]+)(?:#[^)]*)?\)')) {
            $target = $match.Groups[1].Value.Trim()
            if ($target -match '^[a-z][a-z0-9+.-]*:') { continue }
            if ($target -match '[/\\]') {
                throw "Path-like relative Markdown link in $($entry.source): $target"
            }
            $targetStem = [System.IO.Path]::GetFileNameWithoutExtension($target)
            if (-not $mappedPageStems.Contains($targetStem)) {
                throw "Broken relative Markdown link in $($entry.source): $target"
            }
        }
    }
}

foreach ($entry in $entries) {
    $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $entry.source))
    $destinationPath = [System.IO.Path]::GetFullPath((Join-Path $WikiPath $entry.page))
    $sourceText = ([System.IO.File]::ReadAllText($sourcePath) -replace "`r`n", "`n")
    $renderedText = Get-RenderedWikiText -Entry $entry -SourceText $sourceText
    $renderedBytes = if ($entry.page -like 'Eng-*.md') {
        [System.Text.UTF8Encoding]::new($false).GetBytes($renderedText)
    } else {
        [System.IO.File]::ReadAllBytes($sourcePath)
    }
    $destinationText = if (Test-Path -LiteralPath $destinationPath -PathType Leaf) {
        ([System.IO.File]::ReadAllText($destinationPath) -replace "`r`n", "`n")
    } else { $null }
    $matches = $null -ne $destinationText -and $renderedText -ceq $destinationText
    if (-not $matches) {
        $differences.Add($entry.page)
        if (-not $Check) {
            [System.IO.File]::WriteAllBytes($destinationPath, $renderedBytes)
            Write-Output "SYNC $($entry.page)"
        }
    }
}

$sidebarLines = @("- [Home](Home)")
$navigationPages = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$currentSection = $null
foreach ($entry in $navigationEntries) {
    if ([string]::IsNullOrWhiteSpace($entry.section) -or [string]::IsNullOrWhiteSpace($entry.title) -or
        $entry.section -notmatch '^[A-Za-z0-9][A-Za-z0-9 &+(),./-]*$' -or
        $entry.title -notmatch '^[A-Za-z0-9][A-Za-z0-9 &+(),./-]*$' -or
        -not $mappedPages.Contains($entry.page)) {
        throw "Invalid wiki navigation entry: section='$($entry.section)' page='$($entry.page)' title='$($entry.title)'"
    }
    if (-not $navigationPages.Add($entry.page)) {
        throw "Duplicate wiki navigation page: $($entry.page)"
    }
    if ($entry.section -ne $currentSection) {
        $sidebarLines += ""
        $sidebarLines += "**$($entry.section)**"
        $currentSection = $entry.section
    }
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
    Write-Output "Wiki synchronization check passed for $($entries.Count) mapped pages and $($navigationEntries.Count) navigation links."
} else {
    Write-Output "Wiki synchronization completed for $($entries.Count) mapped pages and $($navigationEntries.Count) navigation links."
}
