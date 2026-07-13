[CmdletBinding()]
param(
    [string]$TargetRepo,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [int]$TimeoutSeconds = 5,
    [string]$OutputPath,
    [switch]$SkipOllama,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $TargetRepo) {
    $TargetRepo = $repoRoot
}

function New-CheckResult {
    param(
        [string]$Id,
        [string]$Name,
        [ValidateSet("pass", "warn", "fail", "skip")]
        [string]$Status,
        [string]$Message
    )

    return [pscustomobject]@{
        Id = $Id
        Name = $Name
        Status = $Status
        Message = $Message
    }
}

function Get-ConfigFileRefs {
    param([string]$ConfigPath)

    if (-not (Test-Path -LiteralPath $ConfigPath)) {
        return @()
    }

    $config = Get-Content -LiteralPath $ConfigPath -Raw
    return @([regex]::Matches($config, "file://\.\/([^`r`n]+)") | ForEach-Object {
        $_.Groups[1].Value.Trim()
    })
}

function Get-OllamaStatus {
    if ($SkipOllama) {
        return New-CheckResult -Id "ollama.reachable" -Name "Ollama Reachability" -Status "skip" -Message "Ollama check skipped by request."
    }

    try {
        $uri = "$($OllamaBaseUrl.TrimEnd('/'))/api/tags"
        $response = Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec $TimeoutSeconds
        $modelCount = @($response.models).Count
        return New-CheckResult -Id "ollama.reachable" -Name "Ollama Reachability" -Status "pass" -Message "Ollama responded with $modelCount installed model(s)."
    }
    catch {
        return New-CheckResult -Id "ollama.reachable" -Name "Ollama Reachability" -Status "warn" -Message "Ollama did not respond within the health-check timeout."
    }
}

$resolvedTarget = Resolve-Path -LiteralPath $TargetRepo -ErrorAction SilentlyContinue
$checks = @()

if ($resolvedTarget) {
    $targetRoot = $resolvedTarget.Path
    $checks += New-CheckResult -Id "target.exists" -Name "Target Repository" -Status "pass" -Message "Target repository path exists."
} else {
    $targetRoot = $TargetRepo
    $checks += New-CheckResult -Id "target.exists" -Name "Target Repository" -Status "fail" -Message "Target repository path does not exist."
}

$configPath = Join-Path $targetRoot ".continue/config.yaml"
if (Test-Path -LiteralPath $configPath) {
    $checks += New-CheckResult -Id "config.exists" -Name "Continue Config" -Status "pass" -Message ".continue/config.yaml exists."

    $config = Get-Content -LiteralPath $configPath -Raw
    if ($config -match "(?m)^version:\s+\S+\s*$") {
        $checks += New-CheckResult -Id "config.version" -Name "Config Version" -Status "pass" -Message "Config declares a version."
    } else {
        $checks += New-CheckResult -Id "config.version" -Name "Config Version" -Status "warn" -Message "Config does not declare a version."
    }

    $fileRefs = Get-ConfigFileRefs -ConfigPath $configPath
    $missingRefs = @($fileRefs | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path (Join-Path $targetRoot ".continue") $_))
    })

    if ($missingRefs.Count -eq 0) {
        $checks += New-CheckResult -Id "config.references" -Name "Config File References" -Status "pass" -Message "All local file references resolve."
    } else {
        $checks += New-CheckResult -Id "config.references" -Name "Config File References" -Status "fail" -Message "$($missingRefs.Count) local file reference(s) are missing."
    }

    $duplicateRefs = @($fileRefs | Group-Object | Where-Object { $_.Count -gt 1 })
    if ($duplicateRefs.Count -eq 0) {
        $checks += New-CheckResult -Id "config.duplicates" -Name "Duplicate Config References" -Status "pass" -Message "No duplicate local file references found."
    } else {
        $checks += New-CheckResult -Id "config.duplicates" -Name "Duplicate Config References" -Status "warn" -Message "$($duplicateRefs.Count) duplicate local file reference group(s) found."
    }
} else {
    $checks += New-CheckResult -Id "config.exists" -Name "Continue Config" -Status "warn" -Message ".continue/config.yaml was not found."
}

$runtimeOutputPath = Join-Path $targetRoot "runtime-validation-output"
if (Test-Path -LiteralPath $runtimeOutputPath) {
    $runtimeFiles = @(Get-ChildItem -LiteralPath $runtimeOutputPath -File -Recurse -ErrorAction SilentlyContinue)
    $checks += New-CheckResult -Id "runtime.output" -Name "Runtime Output" -Status "warn" -Message "Runtime validation output exists with $($runtimeFiles.Count) file(s)."
} else {
    $checks += New-CheckResult -Id "runtime.output" -Name "Runtime Output" -Status "pass" -Message "No runtime validation output folder found."
}

$checks += Get-OllamaStatus

$statusRank = @{
    "fail" = 3
    "warn" = 2
    "skip" = 1
    "pass" = 0
}
$overall = ($checks | Sort-Object { $statusRank[$_.Status] } -Descending | Select-Object -First 1).Status

$report = [pscustomobject]@{
    SchemaVersion = 1
    GeneratedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    TargetRepoChecked = [bool]$resolvedTarget
    OllamaCheckSkipped = [bool]$SkipOllama
    OverallStatus = $overall
    Checks = $checks
}

if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
}

if ($AsJson -or $OutputPath) {
    $report | ConvertTo-Json -Depth 10
} else {
    Write-Host "Overall: $overall"
    foreach ($check in $checks) {
        Write-Host "$($check.Status.ToUpperInvariant()) $($check.Name): $($check.Message)"
    }
}

if ($overall -eq "fail") {
    exit 1
}

exit 0
