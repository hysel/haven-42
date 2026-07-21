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
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$ArtifactName = "result.json",
    [int]$TimeoutSeconds = 120,
    [string]$ResponseFixturePath,
    [switch]$Execute,
    [switch]$Apply,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
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
        $uri = $OllamaBaseUrl.TrimEnd('/') + "/api/chat"
        $body = @{
            model = $Model
            stream = $false
            messages = @(
                @{ role = "system"; content = $systemPrompt },
                @{ role = "user"; content = $Prompt }
            )
            options = @{ temperature = 0.2 }
        } | ConvertTo-Json -Depth 8
        $response = Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body -TimeoutSec $TimeoutSeconds
        $providerSource = "ollama-chat"
    }
    $content = [string]$response.message.content
    if ([string]::IsNullOrWhiteSpace($content)) { throw "Local text provider returned empty content." }
}

$artifactType = if ($CapabilityId -eq "general.chat") { "chat-message" } else { "markdown-document" }
$artifactContent = if ($CapabilityId -eq "general.chat") {
    [ordered]@{ role = "assistant"; text = $content }
} else {
    [ordered]@{ title = if ($CapabilityId -eq "content.write") { "Generated Writing" } else { "Summary" }; body = $content }
}
$artifact = [ordered]@{
    schemaVersion = 1
    artifactType = $artifactType
    status = if ($Execute) { "succeeded" } else { "planned" }
    createdAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    sourceCapabilityId = $CapabilityId
    provider = @{ id = "ollama.local-text"; model = $Model; source = $providerSource }
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
    ProviderId = "ollama.local-text"
    Model = $Model
    ArtifactPath = $artifactPath
    ArtifactWritten = [bool]$Apply
    NetworkUsed = [bool]($Execute -and [string]::IsNullOrWhiteSpace($ResponseFixturePath))
    PromptPersisted = $false
    RepositoryRead = $false
    Artifact = $artifact
}
if ($AsJson) { $result | ConvertTo-Json -Depth 12 }
else {
    Write-Output "Capability: $CapabilityId"
    Write-Output "Provider: ollama.local-text"
    Write-Output "Status: $($result.Status)"
    Write-Output "Artifact: $artifactPath"
    Write-Output "Artifact written: $([bool]$Apply)"
    if ($Execute) { Write-Output ""; Write-Output $content }
}
exit 0
