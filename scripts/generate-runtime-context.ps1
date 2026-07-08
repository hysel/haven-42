param(
    [Alias("target-repo")]
    [string]$TargetRepo = (Get-Location).Path,
    [Alias("output-path")]
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

function Get-NormalizedPath {
    param([string]$Path)

    return [System.IO.Path]::GetFullPath($Path).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
}

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

function Test-IsIgnoredPath {
    param([string]$Path)

    $relative = Get-RelativePath -Path $Path
    return $relative -match "(^|/)(bin|obj|\.git|\.vs|node_modules|packages)(/|$)"
}

function Get-FilesByPattern {
    param([string[]]$Patterns)

    $files = New-Object System.Collections.Generic.List[string]

    foreach ($pattern in $Patterns) {
        Get-ChildItem -LiteralPath $target -Recurse -File -Include $pattern -ErrorAction SilentlyContinue |
            Where-Object { -not (Test-IsIgnoredPath -Path $_.FullName) } |
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

$targetIsGitRoot = $false
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitRoot = Invoke-InTarget { git rev-parse --show-toplevel 2>$null }
    if ($gitRoot) {
        $targetIsGitRoot = (Get-NormalizedPath -Path ([string]$gitRoot)) -ieq (Get-NormalizedPath -Path $target.Path)
    }
}

$gitStatus = if ($targetIsGitRoot) {
    Invoke-InTarget { git status --short --branch 2>$null }
} else {
    @("Not a git repository at the target root, or target is inside a parent repository.")
}
Add-Section -Lines $lines -Title "Git Status" -Content $gitStatus

$trackedFiles = if ($targetIsGitRoot) {
    Invoke-InTarget { git ls-files 2>$null }
} else {
    @()
}

if (-not $trackedFiles) {
    $trackedFiles = Get-ChildItem -LiteralPath $target -Recurse -File |
        Where-Object { -not (Test-IsIgnoredPath -Path $_.FullName) } |
        ForEach-Object { Get-RelativePath -Path $_.FullName }
}

Add-Section -Lines $lines -Title "Tracked File Inventory" -Content ($trackedFiles | Sort-Object)

$solutionFiles = Get-FilesByPattern -Patterns @("*.sln", "*.slnx")
Add-Section -Lines $lines -Title "Solution Files" -Content $solutionFiles

$projectFiles = Get-FilesByPattern -Patterns @("*.csproj", "*.vbproj", "*.fsproj", "*.props", "*.targets", "packages.config", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "pyproject.toml", "requirements*.txt", "pom.xml", "build.gradle", "settings.gradle", "gradle.properties", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock")
Add-Section -Lines $lines -Title "Project And Dependency Files" -Content $projectFiles

$configFiles = Get-FilesByPattern -Patterns @("appsettings*.json", "Dockerfile", "docker-compose*.yml", "compose*.yml", "*.config", "*.runsettings", "Directory.Build.*", "global.json", "tsconfig*.json", "vite.config.*", "webpack.config.*", "jest.config.*", "vitest.config.*")
Add-Section -Lines $lines -Title "Configuration Files" -Content $configFiles

$infraFiles = Get-FilesByPattern -Patterns @("*.tf", "*.tfvars", "*.yaml", "*.yml")
Add-Section -Lines $lines -Title "Infrastructure And Workflow Files" -Content $infraFiles

$sqlFiles = Get-FilesByPattern -Patterns @("*.sql")
Add-Section -Lines $lines -Title "Database Migration Files" -Content $sqlFiles

$testFiles = $trackedFiles | Where-Object { $_ -match "(?i)(test|tests|spec)" } | Sort-Object
Add-Section -Lines $lines -Title "Test-Related Files" -Content $testFiles

$sourceFiles = $trackedFiles |
    Where-Object { $_ -match "\.(cs|vb|fs|py|js|jsx|ts|tsx|java|go|rs)$" } |
    Where-Object { $_ -notmatch "(?i)(bin|obj|designer|generated|node_modules)" } |
    Sort-Object
Add-Section -Lines $lines -Title "Source Files" -Content $sourceFiles

$topLevelDocs = @("README.md", "SAMPLE-METADATA.md", "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md", "docs/README.md")
foreach ($doc in $topLevelDocs) {
    $docContent = Read-SmallFile -RelativePath $doc -MaxLines 120
    if ($docContent.Count -gt 0) {
        Add-Section -Lines $lines -Title "Document: $doc" -Content $docContent
    }
}

$metadataFiles = @($projectFiles + $configFiles + $infraFiles + $sqlFiles) | Sort-Object -Unique
foreach ($projectFile in $metadataFiles) {
    if ($projectFile -match "\.(csproj|vbproj|fsproj|props|targets|config|json|toml|txt|xml|yaml|yml|tf|tfvars|sql)$" -or [System.IO.Path]::GetFileName($projectFile) -in @("Dockerfile", "go.mod", "go.sum", "packages.config", "Cargo.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock")) {
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
