param(
    [string]$TargetRepo = (Get-Location).Path,
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $TargetRepo)) {
    throw "Target repository path does not exist: $TargetRepo"
}

if (-not $OutputPath) {
    $OutputPath = Join-Path $TargetRepo "runtime-context.md"
}

$target = Resolve-Path -LiteralPath $TargetRepo

function Invoke-InTarget {
    param([scriptblock]$Script)

    Push-Location -LiteralPath $target
    try {
        & $Script
    }
    finally {
        Pop-Location
    }
}

function Add-Section {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [string]$Title,
        [string[]]$Content
    )

    $Lines.Add("")
    $Lines.Add("## $Title")
    $Lines.Add("")

    if ($Content -and $Content.Count -gt 0) {
        foreach ($line in $Content) {
            $Lines.Add([string]$line)
        }
    } else {
        $Lines.Add("Not found.")
    }
}

function Get-RelativePath {
    param([string]$Path)

    $relative = [System.IO.Path]::GetRelativePath($target, $Path)
    return $relative.Replace('\', '/')
}

function Get-FilesByPattern {
    param([string[]]$Patterns)

    $files = New-Object System.Collections.Generic.List[string]

    foreach ($pattern in $Patterns) {
        Get-ChildItem -LiteralPath $target -Recurse -File -Include $pattern -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "\\(bin|obj|\.git|\.vs|node_modules|packages)($|\\)" } |
            ForEach-Object { $files.Add((Get-RelativePath -Path $_.FullName)) }
    }

    return $files | Sort-Object -Unique
}

function Read-SmallFile {
    param(
        [string]$RelativePath,
        [int]$MaxLines = 120
    )

    $path = Join-Path $target $RelativePath

    if (-not (Test-Path -LiteralPath $path)) {
        return @()
    }

    $content = Get-Content -LiteralPath $path -TotalCount $MaxLines
    $result = New-Object System.Collections.Generic.List[string]
    $result.Add("### $RelativePath")
    $result.Add("")
    $result.Add('```text')
    foreach ($line in $content) {
        $result.Add([string]$line)
    }
    $result.Add('```')
    return $result
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Runtime Repository Context")
$lines.Add("")
$lines.Add("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm')")
$lines.Add("")
$lines.Add("This file is generated for AI runtime validation. Review it before sharing or committing.")

$gitStatus = Invoke-InTarget {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        git status --short --branch 2>$null
    }
}
Add-Section -Lines $lines -Title "Git Status" -Content $gitStatus

$trackedFiles = Invoke-InTarget {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        git ls-files 2>$null
    }
}

if (-not $trackedFiles) {
    $trackedFiles = Get-ChildItem -LiteralPath $target -Recurse -File |
        Where-Object { $_.FullName -notmatch "\\(bin|obj|\.git|\.vs|node_modules|packages)($|\\)" } |
        ForEach-Object { Get-RelativePath -Path $_.FullName }
}

Add-Section -Lines $lines -Title "Tracked File Inventory" -Content ($trackedFiles | Sort-Object)

$solutionFiles = Get-FilesByPattern -Patterns @("*.sln", "*.slnx")
Add-Section -Lines $lines -Title "Solution Files" -Content $solutionFiles

$projectFiles = Get-FilesByPattern -Patterns @("*.csproj", "*.vbproj", "*.fsproj", "*.props", "*.targets", "packages.config")
Add-Section -Lines $lines -Title "Project And Dependency Files" -Content $projectFiles

$configFiles = Get-FilesByPattern -Patterns @("appsettings*.json", "Dockerfile", "docker-compose*.yml", "*.config", "*.runsettings", "Directory.Build.*", "global.json")
Add-Section -Lines $lines -Title "Configuration Files" -Content $configFiles

$testFiles = $trackedFiles | Where-Object { $_ -match "(?i)(test|tests|spec)" } | Sort-Object
Add-Section -Lines $lines -Title "Test-Related Files" -Content $testFiles

$sourceFiles = $trackedFiles |
    Where-Object { $_ -match "\.(cs|vb|fs)$" } |
    Where-Object { $_ -notmatch "(?i)(bin|obj|designer|generated)" } |
    Sort-Object
Add-Section -Lines $lines -Title ".NET Source Files" -Content $sourceFiles

$topLevelDocs = @("README.md", "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md", "docs/README.md")
foreach ($doc in $topLevelDocs) {
    $docContent = Read-SmallFile -RelativePath $doc -MaxLines 120
    if ($docContent.Count -gt 0) {
        Add-Section -Lines $lines -Title "Document: $doc" -Content $docContent
    }
}

foreach ($projectFile in $projectFiles) {
    if ($projectFile -match "\.(csproj|vbproj|fsproj|props|targets|config)$") {
        $projectContent = Read-SmallFile -RelativePath $projectFile -MaxLines 160
        if ($projectContent.Count -gt 0) {
            Add-Section -Lines $lines -Title "Project File: $projectFile" -Content $projectContent
        }
    }
}

$interestingSource = $sourceFiles |
    Where-Object { $_ -match "(?i)(program|startup|controller|endpoint|service|repository|context|module|host|addin)" } |
    Select-Object -First 20

Add-Section -Lines $lines -Title "Representative Source Files For Manual Review" -Content $interestingSource

$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
}

$lines | Set-Content -LiteralPath $OutputPath
Write-Host "Runtime context written to $OutputPath" -ForegroundColor Green
