[CmdletBinding()]
param(
    [string]$CapabilityId,
    [string]$ProviderId = "ollama.local-text",
    [string]$Model,
    [string]$RuntimeBaseUrl,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$EngineId,
    [string]$BackendId,
    [string]$HardwareProfile,
    [switch]$Probe,
    [string]$ResponseFixturePath,
    [int]$TimeoutSeconds = 10,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$capabilities = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/capabilities.json") -Raw | ConvertFrom-Json).capabilities)
$providers = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/providers.json") -Raw | ConvertFrom-Json).providers)
$engines = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/inference-engine-registry.json") -Raw | ConvertFrom-Json).engines)
if ($CapabilityId) {
    $capabilities = @($capabilities | Where-Object id -eq $CapabilityId)
    if ($capabilities.Count -eq 0) { throw "Unknown capability id: $CapabilityId" }
}

$probeResult = $null
if ($Probe) {
    $provider = @($providers | Where-Object id -eq $ProviderId) | Select-Object -First 1
    if (-not $provider) { throw "Unknown provider id: $ProviderId" }
    $runtimeSelection = $null
    if ($provider.protocol -eq "openai-chat-completions") {
        if ([string]::IsNullOrWhiteSpace($EngineId) -or [string]::IsNullOrWhiteSpace($BackendId) -or [string]::IsNullOrWhiteSpace($HardwareProfile)) { throw "OpenAI-compatible providers require EngineId, BackendId, and HardwareProfile." }
        $engine = @($engines | Where-Object id -eq $EngineId) | Select-Object -First 1
        $backend = if ($engine) { @($engine.backends | Where-Object id -eq $BackendId) | Select-Object -First 1 } else { $null }
        $admitted = $engine -and $engine.status -eq "validated-exact-profile" -and @($engine.providerContracts) -contains $provider.providerContract -and $backend -and $backend.status -eq "validated-exact-profile" -and @($backend.profiles) -contains $HardwareProfile
        if (-not $admitted) { throw "Engine, backend, and hardware profile are not an admitted exact profile for this provider." }
        $runtimeSelection = [ordered]@{ engineId = $EngineId; backendId = $BackendId; hardwareProfile = $HardwareProfile; admission = "validated-exact-profile" }
    } elseif ($provider.protocol -ne "ollama-chat") { throw "The selected provider protocol does not support health discovery." }
    if ([string]::IsNullOrWhiteSpace($Model)) { throw "-Model is required with -Probe." }
    try {
        if ($ResponseFixturePath) {
            $response = Get-Content -LiteralPath $ResponseFixturePath -Raw | ConvertFrom-Json
            $source = "validation-fixture"
        } else {
            $baseUrl = if ($RuntimeBaseUrl) { $RuntimeBaseUrl } elseif ($provider.protocol -eq "ollama-chat") { $OllamaBaseUrl } else { "http://127.0.0.1:8080" }
            $suffix = if ($provider.protocol -eq "ollama-chat") { "/api/tags" } else { "/v1/models" }
            $response = Invoke-RestMethod -Method Get -Uri ($baseUrl.TrimEnd('/') + $suffix) -TimeoutSec $TimeoutSeconds
            $source = if ($provider.protocol -eq "ollama-chat") { "ollama-tags" } else { "openai-models" }
        }
        $records = if ($provider.protocol -eq "ollama-chat") { @($response.models) } else { @($response.data) }
        $installed = @($records | ForEach-Object { if ($_.name) { $_.name } elseif ($_.model) { $_.model } else { $_.id } }) -contains $Model
        $probeResult = [pscustomobject]@{ providerId = $provider.id; status = if ($installed) { "available" } else { "configuration-required" }; modelInstalled = $installed; source = $source; runtimeSelection = $runtimeSelection }
    } catch {
        $probeResult = [pscustomobject]@{ providerId = $provider.id; status = "unavailable"; modelInstalled = $false; source = "health-discovery-failed"; runtimeSelection = $runtimeSelection }
    }
}

$items = foreach ($capability in $capabilities) {
    $candidates = @($providers | Where-Object { $_.capabilityIds -contains $capability.id } | ForEach-Object {
        $state = $_.defaultAvailability
        if ($probeResult -and $_.id -eq $probeResult.providerId) { $state = $probeResult.status }
        [pscustomobject]@{ Id = $_.id; Kind = $_.kind; Protocol = $_.protocol; ValidationStatus = $_.validationStatus; Availability = $state }
    })
    $effective = $capability.availability.state
    if ($candidates.Count -gt 0) {
        $effective = if (@($candidates | Where-Object Availability -eq "available").Count -gt 0) { "available" } else { $candidates[0].Availability }
    }
    [pscustomobject]@{ CapabilityId = $capability.id; DeclaredAvailability = $capability.availability.state; EffectiveAvailability = $effective; Providers = $candidates }
}
$result = [ordered]@{ SchemaVersion = 1; Kind = "capability-availability"; ProbeUsed = [bool]$Probe; EndpointPersisted = $false; CapabilityInvoked = $false; Items = @($items) }
if ($probeResult) { $result.Probe = $probeResult }
if ($AsJson) { $result | ConvertTo-Json -Depth 10 }
else {
    foreach ($item in $items) {
        Write-Output "$($item.CapabilityId): $($item.EffectiveAvailability)"
        foreach ($candidate in $item.Providers) { Write-Output "  - $($candidate.Id): $($candidate.Availability) [$($candidate.ValidationStatus)]" }
    }
}
exit 0
