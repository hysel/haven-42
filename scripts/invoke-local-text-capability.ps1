[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet("general.chat", "content.write", "content.summarize")][string]$CapabilityId,
    [Parameter(Mandatory = $true)][string]$Prompt,
    [Parameter(Mandatory = $true)][string]$Model,
    [Parameter(Mandatory = $true)][string]$SessionPath,
    [ValidateSet("ollama.local-text", "llamacpp.local-text")][string]$ProviderId = "ollama.local-text",
    [string]$RuntimeBaseUrl,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [ValidateSet("loopback", "trusted-lan", "external")][string]$EndpointTrustScope = "loopback",
    [string]$EngineId,
    [string]$BackendId,
    [string]$HardwareProfile,
    [string]$ArtifactName = "result.json",
    [int]$TimeoutSeconds = 120,
    [int]$MaximumResponseBytes = 8388608,
    [string]$ResponseFixturePath,
    [switch]$Execute,
    [switch]$Apply,
    [switch]$AsJson
)
$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python 3 is required for the hardened local text provider." }
$arguments = @(
    (Join-Path $PSScriptRoot "invoke-local-text-capability.py"), "--repo-root", $repoRoot,
    "--provider-registry", (Join-Path $repoRoot "config/providers.json"),
    "--engine-registry", (Join-Path $repoRoot "config/inference-engine-registry.json"),
    "--capability-id", $CapabilityId, "--prompt-stdin", "--model", $Model, "--session-path", $SessionPath,
    "--provider-id", $ProviderId, "--ollama-base-url", $OllamaBaseUrl, "--endpoint-trust-scope", $EndpointTrustScope,
    "--artifact-name", $ArtifactName, "--timeout-seconds", "$TimeoutSeconds", "--maximum-response-bytes", "$MaximumResponseBytes"
)
if ($RuntimeBaseUrl) { $arguments += @("--runtime-base-url", $RuntimeBaseUrl) }
if ($EngineId) { $arguments += @("--engine-id", $EngineId) }
if ($BackendId) { $arguments += @("--backend-id", $BackendId) }
if ($HardwareProfile) { $arguments += @("--hardware-profile", $HardwareProfile) }
if ($ResponseFixturePath) { $arguments += @("--response-fixture-path", $ResponseFixturePath) }
if ($Execute) { $arguments += "--execute" }
if ($Apply) { $arguments += "--apply" }
if ($AsJson) { $arguments += "--json" }
$Prompt | & $python.Source @arguments
exit $LASTEXITCODE
