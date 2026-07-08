param(
    [Alias("output-path")]
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [Alias("context-path")]
    [Parameter(Mandatory = $true)]
    [string]$ContextPath,

    [Alias("workflow-name")]
    [string]$WorkflowName = "unknown"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $OutputPath)) {
    throw "Output path does not exist: $OutputPath"
}

if (-not (Test-Path -LiteralPath $ContextPath)) {
    throw "Runtime context path does not exist: $ContextPath"
}

$outputText = Get-Content -LiteralPath $OutputPath -Raw
$contextText = Get-Content -LiteralPath $ContextPath -Raw
$failures = New-Object System.Collections.Generic.List[string]

$filePattern = '(?<![\w.-])[\w.-]+(?:[\\/][\w.-]+)*\.(csproj|vbproj|fsproj|sln|config|props|targets|dna|xll|json|md|cs|sql|xml|yaml|yml|txt)(?![\w.-])'
$contextFiles = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

foreach ($match in [regex]::Matches($contextText, $filePattern)) {
    $value = $match.Value.Trim("`'""()[]{}:,;")
    if ($value) {
        [void]$contextFiles.Add($value)
        [void]$contextFiles.Add((Split-Path -Leaf $value))
    }
}

$outputFileMentions = New-Object System.Collections.Generic.List[object]
foreach ($line in ($outputText -split "`r?`n")) {
    foreach ($match in [regex]::Matches($line, $filePattern)) {
        $value = $match.Value.Trim("`'""()[]{}:,;")
        if ($value) {
            $outputFileMentions.Add([pscustomobject]@{ File = $value; Line = $line })
        }
    }
}

$recommendedNewFilePattern = '(?i)recommended new file|missing file recommendation|new file recommendation|file to add|new documentation file|new config file'
foreach ($mention in $outputFileMentions | Sort-Object File -Unique) {
    $file = $mention.File
    $leaf = Split-Path -Leaf $file
    if (-not $contextFiles.Contains($file) -and -not $contextFiles.Contains($leaf)) {
        if ($mention.Line -match $recommendedNewFilePattern) {
            continue
        }
        $failures.Add("FILENAME_NOT_IN_CONTEXT: $file")
    }
}

$claimPatterns = @(
    'compatible with',
    'actively maintained',
    'supports \.NET',
    'support(ed)? until',
    'stable version',
    'no evidence of dependencies requiring',
    'no migration readiness issues are identified'
)

$claimQualifier = 'current-source verification|requires verification|verify with current|unverified|not proven|source evidence'

if ($WorkflowName -match 'legacy|dependency|migration|repository-discovery') {
    $lines = $outputText -split "`r?`n"
    foreach ($line in $lines) {
        foreach ($pattern in $claimPatterns) {
            if ($line -match $pattern -and $line -notmatch $claimQualifier) {
                $failures.Add("UNSOURCED_COMPATIBILITY_CLAIM: $($line.Trim())")
                break
            }
        }
    }
}

if ($WorkflowName -match 'legacy|dependency|migration') {
    $unsafePatterns = @(
        '<PackageReference\s+Include=',
        'Remove\s+packages\.config',
        'Delete\s+packages\.config',
        'Replace\s+the\s+entire\s+ItemGroup',
        'dotnet\s+restore',
        'dotnet\s+build'
    )

    foreach ($pattern in $unsafePatterns) {
        if ($outputText -match $pattern) {
            $failures.Add("UNSAFE_LEGACY_MIGRATION_PATTERN: $pattern")
        }
    }
}

if ($failures.Count -gt 0) {
    foreach ($failure in $failures) {
        Write-Output "FAIL $failure"
    }
    exit 1
}

Write-Output "PASS runtime output verification passed for $WorkflowName"
exit 0
