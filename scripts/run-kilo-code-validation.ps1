param(
    [Parameter(Mandatory)]
    [string]$Model,
    [string]$TargetRepo,
    [string]$OutputPath,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [int]$TimeoutSeconds = 600,
    [switch]$IncludeWriteSmoke,
    [switch]$IncludeScopedEdit
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if ($Model -notmatch '^[A-Za-z0-9._:/-]+$') { throw "Model contains unsupported characters." }
if ($TimeoutSeconds -lt 1) { throw "TimeoutSeconds must be positive." }
if (-not $TargetRepo) { $TargetRepo = Join-Path $repoRoot "runtime-validation-output/sample-repositories/python-api" }
if (-not $OutputPath) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/kilo-code-cli-model-tests-$timestamp.json"
}

$uri = $null
if (-not [uri]::TryCreate($OllamaBaseUrl, [System.UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -notin @("http", "https") -or $uri.UserInfo -or $uri.Query -or $uri.Fragment) {
    throw "OllamaBaseUrl must be an absolute HTTP(S) URL without credentials, query, or fragment."
}
$safeBaseUrl = $uri.AbsoluteUri.TrimEnd("/")

Write-Host "Running only $Model. It will be unloaded when this launcher exits."
$exitCode = 1
try {
    & (Join-Path $PSScriptRoot "test-kilo-code-cli-models.ps1") `
        -Models $Model `
        -TargetRepo $TargetRepo `
        -OutputPath $OutputPath `
        -OllamaBaseUrl $safeBaseUrl `
        -TimeoutSeconds $TimeoutSeconds `
        -IncludeWriteSmoke:$IncludeWriteSmoke `
        -IncludeScopedEdit:$IncludeScopedEdit `
        -UnloadAfterEach
    $exitCode = $LASTEXITCODE
}
finally {
    try {
        $body = @{ model = $Model; prompt = ""; keep_alive = 0; stream = $false } | ConvertTo-Json
        Invoke-RestMethod -Uri "$safeBaseUrl/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30 | Out-Null
        Write-Host "Unloaded $Model from Ollama."
    }
    catch {
        Write-Warning "Could not confirm unload for ${Model}: $($_.Exception.Message)"
    }
}

exit $exitCode
