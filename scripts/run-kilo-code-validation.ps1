param(
    [Parameter(Mandatory)]
    [string]$Model,
    [string]$TargetRepo,
    [string]$OutputPath,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [int]$LoadTimeoutSeconds = 900,
    [int]$PreloadKeepAliveMinutes = 15,
    [int]$TimeoutSeconds = 600,
    [switch]$IncludeWriteSmoke,
    [switch]$IncludeScopedEdit
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if ($Model -notmatch '^[A-Za-z0-9._:/-]+$') { throw "Model contains unsupported characters." }
if ($LoadTimeoutSeconds -lt 1) { throw "LoadTimeoutSeconds must be positive." }
if ($PreloadKeepAliveMinutes -lt 1) { throw "PreloadKeepAliveMinutes must be positive." }
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
$preloadRequested = $false
try {
    if ($TargetRepo -match 'runtime-validation-output[\\/]sample-repositories') {
        $legacyConfigPath = Join-Path (Join-Path $TargetRepo ".kilo") "kilo.json"
        if (Test-Path -LiteralPath $legacyConfigPath) {
            Remove-Item -LiteralPath $legacyConfigPath -Force
            Write-Host "Removed legacy generated Kilo config: .kilo/kilo.json"
        }
    }

    & (Join-Path $PSScriptRoot "setup-agent-surface.ps1") `
        -Action Configure `
        -Surface kilo `
        -TargetRepo $TargetRepo `
        -Model $Model `
        -OllamaBaseUrl $safeBaseUrl `
        -Force
    if ($LASTEXITCODE -ne 0) { throw "Kilo configuration generation failed for $Model." }

    # Keep model load time outside the per-phase Kilo timeout. Ollama's /api/ps
    # response confirms that the named model is resident before validation starts.
    $preloadRequested = $true
    Write-Host "Preloading $Model before starting the Kilo phase timer..."
    $preloadBody = @{ model = $Model; prompt = ""; keep_alive = "${PreloadKeepAliveMinutes}m"; stream = $false } | ConvertTo-Json
    $preload = Invoke-RestMethod -Uri "$safeBaseUrl/api/generate" -Method Post -Body $preloadBody -ContentType "application/json" -TimeoutSec $LoadTimeoutSeconds
    $running = Invoke-RestMethod -Uri "$safeBaseUrl/api/ps" -Method Get -TimeoutSec 30
    $isLoaded = @($running.models | Where-Object { $_.name -eq $Model -or $_.model -eq $Model }).Count -gt 0
    if (-not $isLoaded) { throw "Ollama did not report $Model as loaded after preflight." }
    $loadSeconds = if ($null -ne $preload.load_duration) { [math]::Round(([double]$preload.load_duration / 1000000000), 2) } else { "unknown" }
    Write-Host "Preload complete (load duration: $loadSeconds seconds). Starting Kilo validation timer."

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
        if ($preloadRequested) {
            $body = @{ model = $Model; prompt = ""; keep_alive = 0; stream = $false } | ConvertTo-Json
            Invoke-RestMethod -Uri "$safeBaseUrl/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30 | Out-Null
            Write-Host "Unloaded $Model from Ollama."
        }
    }
    catch {
        Write-Warning "Could not confirm unload for ${Model}: $($_.Exception.Message)"
    }
}

exit $exitCode
