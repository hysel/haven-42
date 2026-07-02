param(
    [string]$ExpectedVersion = "0.1.3"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot ".continue/config.yaml"
$failed = $false

function Add-Failure {
    param([string]$Message)
    Write-Host "FAIL $Message" -ForegroundColor Red
    $script:failed = $true
}

function Add-Pass {
    param([string]$Message)
    Write-Host "PASS $Message" -ForegroundColor Green
}

if (-not (Test-Path -LiteralPath $configPath)) {
    Add-Failure ".continue/config.yaml exists"
} else {
    Add-Pass ".continue/config.yaml exists"
}

$config = Get-Content -LiteralPath $configPath -Raw

if ($config -match "(?m)^version:\s+$([regex]::Escape($ExpectedVersion))\s*$") {
    Add-Pass "config version is $ExpectedVersion"
} else {
    Add-Failure "config version is $ExpectedVersion"
}

if ($config -match "(?m)^schema:\s+v1\s*$") {
    Add-Pass "config schema is v1"
} else {
    Add-Failure "config schema is v1"
}

if ($config -match "(?m)^mcpServers:\s+\[\]\s*$") {
    Add-Pass "default MCP server list is empty"
} else {
    Add-Failure "default MCP server list is empty"
}

$fileRefs = [regex]::Matches($config, "file://\.\/([^`r`n]+)") | ForEach-Object {
    $_.Groups[1].Value.Trim()
}

foreach ($ref in $fileRefs) {
    $target = Join-Path (Join-Path $repoRoot ".continue") $ref
    if (Test-Path -LiteralPath $target) {
        Add-Pass "referenced file exists: .continue/$ref"
    } else {
        Add-Failure "referenced file exists: .continue/$ref"
    }
}

$requiredFiles = @(
    "README.md",
    "PROJECT.md",
    "ARCHITECTURE.md",
    "STYLEGUIDE.md",
    "ROADMAP.md",
    "TODO.md",
    "AI.md",
    "DECISIONS.md",
    "CHANGELOG.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "docs/release.md",
    "docs/compatibility.md",
    "docs/validation-checklists.md",
    "docs/troubleshooting.md",
    "docs/mcp-options.md",
    "docs/mcp-setup.md",
    "docs/sonarqube-review.md",
    "docs/sonarqube-integration-options.md",
    "examples/fixtures/sonarqube-findings.md",
    "examples/fixtures/repository-context.md"
)

foreach ($relativePath in $requiredFiles) {
    $path = Join-Path $repoRoot $relativePath
    if (Test-Path -LiteralPath $path) {
        Add-Pass "required file exists: $relativePath"
    } else {
        Add-Failure "required file exists: $relativePath"
    }
}

$textFiles = Get-ChildItem -LiteralPath $repoRoot -Recurse -File |
    Where-Object {
        $_.FullName -notmatch "\\.git\\" -and
        $_.Extension -in @(".md", ".yaml", ".yml", ".ps1", ".txt")
    }

$privateIpPattern = "\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b"
$secretPattern = "(?i)(api[_-]?key|access[_-]?token|personal[_-]?access[_-]?token|password|secret)\s*[:=]\s*['""]?[A-Za-z0-9_\-]{16,}"

foreach ($file in $textFiles) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
    $relative = Resolve-Path -LiteralPath $file.FullName -Relative

    if ($content -match $privateIpPattern) {
        Add-Failure "no private IP address committed: $relative"
    }

    if ($content -match $secretPattern) {
        Add-Failure "no likely secret committed: $relative"
    }
}

if (-not $failed) {
    Write-Host "Validation passed." -ForegroundColor Green
    exit 0
}

Write-Host "Validation failed." -ForegroundColor Red
exit 1
