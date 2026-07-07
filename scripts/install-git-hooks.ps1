param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$hooksPath = Join-Path $repoRoot ".githooks"
$prePushHook = Join-Path $hooksPath "pre-push"

if (-not (Test-Path -LiteralPath $prePushHook)) {
    throw "Missing pre-push hook: $prePushHook"
}

git -C $repoRoot config core.hooksPath .githooks

$configuredPath = git -C $repoRoot config --get core.hooksPath
if ($configuredPath -ne ".githooks") {
    throw "Failed to configure core.hooksPath. Current value: $configuredPath"
}

Write-Host "Git hooks enabled for this repository." -ForegroundColor Green
Write-Host "Pre-push validation will run before git push." -ForegroundColor Green
