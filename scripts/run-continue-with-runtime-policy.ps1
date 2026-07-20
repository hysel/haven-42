param(
    [Parameter(Mandatory)]
    [string]$Model,
    [Parameter(Mandatory)]
    [string]$Prompt,
    [string]$ConfigPath,
    [string]$TargetRepo = (Get-Location).Path,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$ContinueCommand = "npx",
    [int]$LoadTimeoutSeconds = 900,
    [int]$TimeoutSeconds = 900,
    [switch]$ReadOnly
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $ConfigPath) { $ConfigPath = Join-Path $TargetRepo ".continue/config.local.yaml" }
if (-not (Test-Path -LiteralPath $TargetRepo)) { throw "TargetRepo does not exist: $TargetRepo" }
if (-not (Test-Path -LiteralPath $ConfigPath)) { throw "ConfigPath does not exist: $ConfigPath" }
if ($LoadTimeoutSeconds -lt 1 -or $TimeoutSeconds -lt 1) { throw "Timeout values must be positive." }

$policy = (& (Join-Path $PSScriptRoot "get-model-runtime-policy.ps1") | ConvertFrom-Json)
$base = $OllamaBaseUrl.TrimEnd('/')
$commandInfo = Get-Command $ContinueCommand -ErrorAction Stop
$resolvedCommand = $commandInfo.Source
if ($resolvedCommand -match '(?i)\.ps1$') {
    $cmdShim = [System.IO.Path]::ChangeExtension($resolvedCommand, ".cmd")
    if (Test-Path -LiteralPath $cmdShim) { $resolvedCommand = $cmdShim }
}

function Invoke-OllamaUnload {
    $body = @{ model = $Model; prompt = ""; keep_alive = 0; stream = $false } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 60 | Out-Null
}

$shouldUnload = $policy.residencyMode -eq "unload-after-run"
try {
    $running = @((Invoke-RestMethod -Uri "$base/api/ps" -TimeoutSec 30).models)
    $other = @($running | Where-Object { $_.name -ne $Model -and $_.model -ne $Model })
    if ($other.Count -ge [int]$policy.maxResidentModels) { throw "Runtime policy blocks loading ${Model}: $($other.Count) other model(s) are resident." }
    if ($other.Count -gt 0) { Write-Warning "Runtime policy warning: another model is resident before Continue starts." }

    $preload = @{ model = $Model; prompt = ""; keep_alive = "$($policy.preloadKeepAliveMinutes)m"; stream = $false } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/api/generate" -Method Post -Body $preload -ContentType "application/json" -TimeoutSec $LoadTimeoutSeconds | Out-Null

    $arguments = if ($ContinueCommand -eq "npx") { @("-y", "@continuedev/cli") } else { @() }
    $arguments += @("--config", (Resolve-Path -LiteralPath $ConfigPath).Path, $(if ($ReadOnly) { "--readonly" } else { "--auto" }), "--format", "json", "--silent", "-p", $Prompt)
    $start = [System.Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $resolvedCommand
    $start.WorkingDirectory = (Resolve-Path -LiteralPath $TargetRepo).Path
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in $arguments) { [void]$start.ArgumentList.Add($argument) }
    $process = [System.Diagnostics.Process]::new(); $process.StartInfo = $start; [void]$process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync(); $stderrTask = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) { try { $process.Kill($true) } catch {}; throw "Continue timed out after $TimeoutSeconds seconds." }
    $stdout = $stdoutTask.GetAwaiter().GetResult(); $stderr = $stderrTask.GetAwaiter().GetResult()
    if ($stdout) { Write-Output $stdout }; if ($stderr) { Write-Error $stderr }
    exit $process.ExitCode
}
finally {
    if ($shouldUnload) {
        try { Invoke-OllamaUnload; Write-Host "Unloaded $Model per runtime policy." } catch { Write-Warning "Could not unload ${Model}: $($_.Exception.Message)" }
    }
}
