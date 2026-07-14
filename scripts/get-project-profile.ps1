[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [Alias("target-repo")]
    [string]$TargetRepo,
    [Alias("rules-path")]
    [string]$RulesPath,
    [Alias("output-path")]
    [string]$OutputPath,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $RulesPath) {
    $RulesPath = Join-Path $repoRoot "config/project-profile-rules.json"
}

if (-not (Test-Path -LiteralPath $TargetRepo -PathType Container)) {
    throw "TargetRepo does not exist: $TargetRepo"
}
if (-not (Test-Path -LiteralPath $RulesPath -PathType Leaf)) {
    throw "Project profile rules do not exist: $RulesPath"
}

$targetRoot = (Resolve-Path -LiteralPath $TargetRepo).Path
$rules = Get-Content -LiteralPath $RulesPath -Raw | ConvertFrom-Json
$ignored = @($rules.ignoredDirectories | ForEach-Object { [string]$_ })
$activationMinimumConfidence = [string]$rules.activationMinimumConfidence
if ($activationMinimumConfidence -notin @("high", "medium")) {
    throw "Unsupported activationMinimumConfidence: $activationMinimumConfidence"
}

function Get-RepositoryFiles {
    param([string]$Root, [string[]]$IgnoredDirectories)

    $files = [System.Collections.Generic.List[object]]::new()
    $stack = [System.Collections.Generic.Stack[System.IO.DirectoryInfo]]::new()
    $stack.Push([System.IO.DirectoryInfo]::new($Root))

    while ($stack.Count -gt 0) {
        $directory = $stack.Pop()
        try {
            foreach ($entry in $directory.EnumerateFileSystemInfos()) {
                if ($entry -is [System.IO.DirectoryInfo]) {
                    if ($entry.Name -in $IgnoredDirectories) { continue }
                    if (($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
                    $stack.Push($entry)
                    continue
                }

                $relative = [System.IO.Path]::GetRelativePath($Root, $entry.FullName).Replace("\", "/")
                $files.Add([pscustomobject]@{
                    Name = $entry.Name
                    RelativePath = $relative
                })
            }
        }
        catch {
            continue
        }
    }

    return @($files | Sort-Object RelativePath)
}

function Test-SignalPattern {
    param([object]$File, [string]$Pattern)

    $candidate = if ($Pattern.Contains("/")) { $File.RelativePath } else { $File.Name }
    $wildcard = [System.Management.Automation.WildcardPattern]::new(
        $Pattern,
        [System.Management.Automation.WildcardOptions]::IgnoreCase
    )
    return $wildcard.IsMatch($candidate)
}

function Get-Matches {
    param([object[]]$Files, [string[]]$Patterns, [string]$Strength)

    $matches = [System.Collections.Generic.List[object]]::new()
    foreach ($file in $Files) {
        foreach ($pattern in $Patterns) {
            if (Test-SignalPattern -File $file -Pattern $pattern) {
                $matches.Add([pscustomobject]@{
                    Path = $file.RelativePath
                    Strength = $Strength
                    Pattern = $pattern
                })
                break
            }
        }
    }
    return @($matches)
}

$files = @(Get-RepositoryFiles -Root $targetRoot -IgnoredDirectories $ignored)
$detections = [System.Collections.Generic.List[object]]::new()

foreach ($ecosystem in @($rules.ecosystems)) {
    $strong = @(Get-Matches -Files $files -Patterns @($ecosystem.strongPatterns) -Strength "strong")
    $supporting = @(Get-Matches -Files $files -Patterns @($ecosystem.supportingPatterns) -Strength "supporting")
    if ($strong.Count -eq 0 -and $supporting.Count -eq 0) { continue }

    $confidence = if ($strong.Count -gt 0) { "high" } else { "medium" }
    $score = ($strong.Count * 100) + ($supporting.Count * 10)
    $evidence = @($strong + $supporting | Sort-Object Path, Strength -Unique | Select-Object -First 25)

    $detections.Add([pscustomobject]@{
        Id = [string]$ecosystem.id
        DisplayName = [string]$ecosystem.displayName
        Confidence = $confidence
        Score = $score
        StrongEvidenceCount = $strong.Count
        SupportingEvidenceCount = $supporting.Count
        Evidence = $evidence
        RulePackId = if ($ecosystem.rulePackId) { [string]$ecosystem.rulePackId } else { $null }
        RulePackPath = if ($ecosystem.rulePackPath) { [string]$ecosystem.rulePackPath } else { $null }
    })
}

$orderedDetections = @($detections | Sort-Object @{ Expression = { $_.Score }; Descending = $true }, Id)
$confidenceRank = @{ high = 2; medium = 1; unconfirmed = 0 }
$minimumRank = $confidenceRank[$activationMinimumConfidence]
$selected = @($orderedDetections | Where-Object {
    $_.RulePackId -and $confidenceRank[$_.Confidence] -ge $minimumRank
} | ForEach-Object {
    [pscustomobject]@{
        Id = $_.RulePackId
        SourcePath = $_.RulePackPath
        ActivePath = "rules/active-language-$($_.RulePackId).md"
        Ecosystem = $_.Id
        Confidence = $_.Confidence
        Evidence = @($_.Evidence | ForEach-Object { $_.Path } | Sort-Object -Unique)
    }
})

$profile = [pscustomobject]@{
    SchemaVersion = 1
    ClassificationMethod = "deterministic-file-signals"
    ActivationMinimumConfidence = $activationMinimumConfidence
    PrimaryEcosystem = if ($orderedDetections.Count -gt 0) { $orderedDetections[0].Id } else { "unknown" }
    Confidence = if ($orderedDetections.Count -gt 0) { $orderedDetections[0].Confidence } else { "unconfirmed" }
    DetectedEcosystems = $orderedDetections
    SelectedRulePackIds = @($selected | ForEach-Object { $_.Id })
    SelectedRulePacks = $selected
    Unconfirmed = if ($orderedDetections.Count -eq 0) { @("No configured ecosystem signal matched an inspected file.") } else { @() }
    Privacy = [pscustomobject]@{
        TargetPathRecorded = $false
        FileContentsRead = $false
        IgnoredDirectories = $ignored
    }
}

$json = $profile | ConvertTo-Json -Depth 20
if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Set-Content -LiteralPath $OutputPath -Value $json -Encoding utf8
}

if ($AsJson -or -not $OutputPath) {
    Write-Output $json
} else {
    Write-Host "Primary ecosystem: $($profile.PrimaryEcosystem)"
    Write-Host "Confidence: $($profile.Confidence)"
    Write-Host "Selected rule packs: $(if ($profile.SelectedRulePackIds.Count) { $profile.SelectedRulePackIds -join ', ' } else { 'none' })"
    Write-Host "Project profile written to $OutputPath"
}
