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
Import-Module (Join-Path $PSScriptRoot "CommandResolution.psm1") -Force
$python = Resolve-Python3Command
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
