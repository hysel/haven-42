[CmdletBinding()]
param(
    [string]$CapabilityId,
    [string]$ProviderId = "ollama.local-text",
    [string]$Model,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [switch]$Probe,
    [string]$ResponseFixturePath,
    [int]$TimeoutSeconds = 10,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$capabilities = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/capabilities.json") -Raw | ConvertFrom-Json).capabilities)
$providers = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/providers.json") -Raw | ConvertFrom-Json).providers)
if ($CapabilityId) {
    $capabilities = @($capabilities | Where-Object id -eq $CapabilityId)
    if ($capabilities.Count -eq 0) { throw "Unknown capability id: $CapabilityId" }
}

$probeResult = $null
if ($Probe) {
    $provider = @($providers | Where-Object id -eq $ProviderId) | Select-Object -First 1
    if (-not $provider) { throw "Unknown provider id: $ProviderId" }
    if ($provider.protocol -ne "ollama-chat") { throw "The selected provider does not support Ollama health discovery." }
    if ([string]::IsNullOrWhiteSpace($Model)) { throw "-Model is required with -Probe." }
    try {
        if ($ResponseFixturePath) {
            $response = Get-Content -LiteralPath $ResponseFixturePath -Raw | ConvertFrom-Json
            $source = "validation-fixture"
        } else {
            $response = Invoke-RestMethod -Method Get -Uri ($OllamaBaseUrl.TrimEnd('/') + "/api/tags") -TimeoutSec $TimeoutSeconds
            $source = "ollama-tags"
        }
        $installed = @($response.models | ForEach-Object { if ($_.name) { $_.name } else { $_.model } }) -contains $Model
        $probeResult = [pscustomobject]@{ providerId = $provider.id; status = if ($installed) { "available" } else { "configuration-required" }; modelInstalled = $installed; source = $source }
    } catch {
        $probeResult = [pscustomobject]@{ providerId = $provider.id; status = "unavailable"; modelInstalled = $false; source = "health-discovery-failed" }
    }
}

$items = foreach ($capability in $capabilities) {
    $candidates = @($providers | Where-Object { $_.capabilityIds -contains $capability.id } | ForEach-Object {
        $state = $_.defaultAvailability
        if ($probeResult -and $_.id -eq $probeResult.providerId) { $state = $probeResult.status }
        [pscustomobject]@{ Id = $_.id; Kind = $_.kind; ValidationStatus = $_.validationStatus; Availability = $state }
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
