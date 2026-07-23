[CmdletBinding()]
param(
    [string]$CapabilityId,
    [string]$ProviderId = "ollama.local-text",
    [string]$Model,
    [string]$RuntimeBaseUrl,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [ValidateSet("loopback", "trusted-lan", "external")][string]$EndpointTrustScope = "loopback",
    [string]$EngineId,
    [string]$BackendId,
    [string]$HardwareProfile,
    [switch]$Probe,
    [string]$ResponseFixturePath,
    [int]$TimeoutSeconds = 10,
    [switch]$AsJson
)
$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python 3 is required for hardened provider discovery." }
$arguments = @(
    (Join-Path $PSScriptRoot "discover-capability-availability.py"),
    "--capability-registry", (Join-Path $repoRoot "config/capabilities.json"),
    "--provider-registry", (Join-Path $repoRoot "config/providers.json"),
    "--engine-registry", (Join-Path $repoRoot "config/inference-engine-registry.json"),
    "--provider-id", $ProviderId, "--ollama-base-url", $OllamaBaseUrl,
    "--endpoint-trust-scope", $EndpointTrustScope, "--timeout-seconds", "$TimeoutSeconds"
)
if ($CapabilityId) { $arguments += @("--capability-id", $CapabilityId) }
if ($Model) { $arguments += @("--model", $Model) }
if ($RuntimeBaseUrl) { $arguments += @("--runtime-base-url", $RuntimeBaseUrl) }
if ($EngineId) { $arguments += @("--engine-id", $EngineId) }
if ($BackendId) { $arguments += @("--backend-id", $BackendId) }
if ($HardwareProfile) { $arguments += @("--hardware-profile", $HardwareProfile) }
if ($Probe) { $arguments += "--probe" }
if ($ResponseFixturePath) { $arguments += @("--response-fixture-path", $ResponseFixturePath) }
if ($AsJson) { $arguments += "--json" }
& $python.Source @arguments
exit $LASTEXITCODE
