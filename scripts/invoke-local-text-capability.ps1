[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("general.chat", "content.write", "content.summarize")]
    [string]$CapabilityId,
    [Parameter(Mandatory = $true)]
    [string]$Prompt,
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [Parameter(Mandatory = $true)]
    [string]$SessionPath,
    [ValidateSet("ollama.local-text", "llamacpp.local-text")]
    [string]$ProviderId = "ollama.local-text",
    [string]$RuntimeBaseUrl,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$EngineId,
    [string]$BackendId,
    [string]$HardwareProfile,
    [string]$ArtifactName = "result.json",
    [int]$TimeoutSeconds = 120,
    [string]$ResponseFixturePath,
    [switch]$Execute,
    [switch]$Apply,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$providers = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/providers.json") -Raw | ConvertFrom-Json).providers)
$provider = @($providers | Where-Object id -eq $ProviderId) | Select-Object -First 1
if (-not $provider -or @($provider.capabilityIds) -notcontains $CapabilityId) { throw "Provider is unknown or does not support the requested capability." }
$runtimeSelection = $null
if ($provider.protocol -eq "openai-chat-completions") {
    if ([string]::IsNullOrWhiteSpace($EngineId) -or [string]::IsNullOrWhiteSpace($BackendId) -or [string]::IsNullOrWhiteSpace($HardwareProfile)) { throw "OpenAI-compatible providers require EngineId, BackendId, and HardwareProfile." }
    $engines = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/inference-engine-registry.json") -Raw | ConvertFrom-Json).engines)
    $engine = @($engines | Where-Object id -eq $EngineId) | Select-Object -First 1
    $backend = if ($engine) { @($engine.backends | Where-Object id -eq $BackendId) | Select-Object -First 1 } else { $null }
    $admitted = $engine -and $engine.status -eq "validated-exact-profile" -and @($engine.providerContracts) -contains $provider.providerContract -and $backend -and $backend.status -eq "validated-exact-profile" -and @($backend.profiles) -contains $HardwareProfile
    if (-not $admitted) { throw "Engine, backend, and hardware profile are not an admitted exact profile for this provider." }
    $runtimeSelection = [ordered]@{ engineId = $EngineId; backendId = $BackendId; hardwareProfile = $HardwareProfile; admission = "validated-exact-profile" }
} elseif ($EngineId -or $BackendId -or $HardwareProfile) { throw "Explicit engine selection is only supported for engine-backed OpenAI-compatible providers." }
$sessionFullPath = [IO.Path]::GetFullPath($SessionPath)
$repoPrefix = $repoRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
if ($sessionFullPath.Equals($repoRoot, [StringComparison]::OrdinalIgnoreCase) -or $sessionFullPath.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Provider sessions must stay outside the pack repository."
}
if (-not (Test-Path -LiteralPath $sessionFullPath -PathType Container)) { throw "Session path does not exist: $sessionFullPath" }
$metadataPath = Join-Path $sessionFullPath "session.json"
if (-not (Test-Path -LiteralPath $metadataPath -PathType Leaf)) { throw "Session metadata is missing: $metadataPath" }
$session = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
if ($session.capabilityId -ne $CapabilityId) { throw "Session capability '$($session.capabilityId)' does not match requested capability '$CapabilityId'." }
if ($ArtifactName -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,95}\.json$') { throw "ArtifactName must be a safe JSON filename." }
if ([string]::IsNullOrWhiteSpace($Prompt)) { throw "Prompt must not be empty." }
if ([string]::IsNullOrWhiteSpace($Model)) { throw "Model must not be empty." }
if ($Apply -and -not $Execute) { throw "-Apply requires -Execute." }
$artifactDirectory = Join-Path $sessionFullPath "artifacts"
$artifactPath = [IO.Path]::GetFullPath((Join-Path $artifactDirectory $ArtifactName))
$artifactPrefix = [IO.Path]::GetFullPath($artifactDirectory).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
if (-not $artifactPath.StartsWith($artifactPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Artifact path escaped the session artifact directory." }
if ($Apply -and (Test-Path -LiteralPath $artifactPath)) { throw "Artifact already exists: $artifactPath" }

$systemPrompt = switch ($CapabilityId) {
    "general.chat" { "Answer the user's general question clearly. Do not claim repository access or actions you did not perform." }
    "content.write" { "Create the requested general-purpose content as clean Markdown. Do not claim external facts were verified unless the user supplied them." }
    "content.summarize" { "Summarize only the material supplied by the user. Preserve uncertainty and do not invent missing facts. Return clean Markdown." }
}

$content = $null
$providerSource = "not-executed"
if ($Execute) {
    if (-not [string]::IsNullOrWhiteSpace($ResponseFixturePath)) {
        $response = Get-Content -LiteralPath $ResponseFixturePath -Raw | ConvertFrom-Json
        $providerSource = "validation-fixture"
    } else {
        $baseUrl = if ($RuntimeBaseUrl) { $RuntimeBaseUrl } elseif ($provider.protocol -eq "ollama-chat") { $OllamaBaseUrl } else { "http://127.0.0.1:8080" }
        $uri = $baseUrl.TrimEnd('/') + $(if ($provider.protocol -eq "ollama-chat") { "/api/chat" } else { "/v1/chat/completions" })
        $body = @{
            model = $Model
            stream = $false
            messages = @(
                @{ role = "system"; content = $systemPrompt },
                @{ role = "user"; content = $Prompt }
            )
        }
        if ($provider.protocol -eq "ollama-chat") { $body.options = @{ temperature = 0.2 } } else { $body.temperature = 0.2 }
        $body = $body | ConvertTo-Json -Depth 8
        $response = Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body -TimeoutSec $TimeoutSeconds
        $providerSource = $provider.protocol
    }
    $content = if ($provider.protocol -eq "ollama-chat") { [string]$response.message.content } else { [string]$response.choices[0].message.content }
    if ([string]::IsNullOrWhiteSpace($content)) { throw "Local text provider returned empty content." }
}

$artifactType = if ($CapabilityId -eq "general.chat") { "chat-message" } else { "markdown-document" }
$artifactContent = if ($CapabilityId -eq "general.chat") {
    [ordered]@{ role = "assistant"; text = $content }
} else {
    [ordered]@{ title = if ($CapabilityId -eq "content.write") { "Generated Writing" } else { "Summary" }; body = $content }
}
$providerMetadata = [ordered]@{ id = $provider.id; model = $Model; source = $providerSource }
if ($runtimeSelection) { $providerMetadata.runtimeSelection = $runtimeSelection }
$artifact = [ordered]@{
    schemaVersion = 1
    artifactType = $artifactType
    status = if ($Execute) { "succeeded" } else { "planned" }
    createdAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    sourceCapabilityId = $CapabilityId
    provider = $providerMetadata
    content = $artifactContent
    policy = @{
        localExecution = $true
        externalProvider = $false
        repositoryRead = $false
        fileWrite = [bool]$Apply
        networkAccess = [bool]($Execute -and [string]::IsNullOrWhiteSpace($ResponseFixturePath))
        modelDownload = $false
        approvalRequired = [bool]$Apply
    }
}
if ($Apply) {
    New-Item -ItemType Directory -Path $artifactDirectory -Force | Out-Null
    $artifact | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $artifactPath -Encoding utf8NoBOM
}
$result = [pscustomobject]@{
    SchemaVersion = 1
    Kind = "local-text-capability"
    Status = if ($Execute) { "succeeded" } else { "planned" }
    CapabilityId = $CapabilityId
    ProviderId = $provider.id
    Protocol = $provider.protocol
    RuntimeSelection = $runtimeSelection
    Model = $Model
    ArtifactPath = $artifactPath
    ArtifactWritten = [bool]$Apply
    NetworkUsed = [bool]($Execute -and [string]::IsNullOrWhiteSpace($ResponseFixturePath))
    PromptPersisted = $false
    EndpointPersisted = $false
    RepositoryRead = $false
    Artifact = $artifact
}
if ($AsJson) { $result | ConvertTo-Json -Depth 12 }
else {
    Write-Output "Capability: $CapabilityId"
    Write-Output "Provider: $($provider.id)"
    Write-Output "Status: $($result.Status)"
    Write-Output "Artifact: $artifactPath"
    Write-Output "Artifact written: $([bool]$Apply)"
    if ($Execute) { Write-Output ""; Write-Output $content }
}
exit 0
