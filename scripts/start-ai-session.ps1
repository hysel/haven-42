[CmdletBinding()]
param(
    [string]$Text,
    [string]$CapabilityId,
    [switch]$List,
    [string]$WorkspaceRoot,
    [string]$SessionId,
    [switch]$Apply,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$registryPath = Join-Path $repoRoot "config/capabilities.json"
$resolverPath = Join-Path $PSScriptRoot "resolve-capability.ps1"
$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json

function Test-IsWithinPath {
    param([string]$Child, [string]$Parent)
    $parentWithSeparator = $Parent.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    return $Child.Equals($Parent, [System.StringComparison]::OrdinalIgnoreCase) -or $Child.StartsWith($parentWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)
}

function Write-SessionResult {
    param([object]$Result)
    if ($AsJson) {
        $Result | ConvertTo-Json -Depth 12
        return
    }
    if ($Result.Kind -eq "capability-menu") {
        Write-Output "What would you like to do?"
        foreach ($item in @($Result.Items)) { Write-Output "$($item.Number). $($item.Name) [$($item.Availability)] - $($item.Id)" }
        Write-Output "Use -Text or -CapabilityId to create a session plan."
        return
    }
    Write-Output "Session: $($Result.SessionId)"
    Write-Output "Capability: $($Result.Capability.Id) [$($Result.Capability.Availability.state)]"
    Write-Output "Workspace: $($Result.SessionPath)"
    Write-Output "Mode: $($Result.Status)"
    Write-Output "Capability invoked: no"
}

if ($List) {
    $items = @()
    $number = 0
    foreach ($capability in @($registry.capabilities)) {
        $number++
        $items += [pscustomobject]@{
            Number = $number
            Id = $capability.id
            Name = $capability.name
            Description = $capability.description
            Availability = $capability.availability.state
            RepositoryMode = $capability.repositoryMode
            Policy = $capability.policy
            OutputArtifactTypes = @($capability.outputArtifactTypes)
        }
    }
    Write-SessionResult ([pscustomobject]@{ SchemaVersion = 1; Kind = "capability-menu"; SourceRegistry = "config/capabilities.json"; Items = $items })
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Text) -and [string]::IsNullOrWhiteSpace($CapabilityId)) {
    throw "Provide -Text, -CapabilityId, or -List."
}
$pwshPath = (Get-Process -Id $PID).Path
$resolverArguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $resolverPath, "-AsJson")
if (-not [string]::IsNullOrWhiteSpace($CapabilityId)) { $resolverArguments += @("-CapabilityId", $CapabilityId) }
else { $resolverArguments += @("-Text", $Text) }
$routingOutput = & $pwshPath @resolverArguments 2>&1
if ($LASTEXITCODE -ne 0) { throw "Capability routing failed: $($routingOutput -join ' ')" }
$routing = ($routingOutput -join "`n") | ConvertFrom-Json
if ($routing.Status -ne "selected") {
    $result = [pscustomobject]@{
        SchemaVersion = 1
        Kind = "ai-session-plan"
        Status = $routing.Status
        Routing = $routing
        WorkspaceCreated = $false
        CapabilityInvoked = $false
        Reason = "A unique capability is required before a session workspace can be planned."
    }
    Write-SessionResult $result
    exit 0
}

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    $WorkspaceRoot = Join-Path ([System.IO.Path]::GetTempPath()) "haven-42/sessions"
}
$workspaceFullPath = [System.IO.Path]::GetFullPath($WorkspaceRoot)
if (Test-IsWithinPath -Child $workspaceFullPath -Parent $repoRoot) {
    throw "Session workspaces must stay outside the pack repository: $workspaceFullPath"
}
if ([string]::IsNullOrWhiteSpace($SessionId)) {
    $SessionId = "session-$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))-$([guid]::NewGuid().ToString('N').Substring(0,8))"
}
if ($SessionId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$') {
    throw "SessionId must contain 1-64 safe filename characters and start with a letter or number."
}
$sessionPath = [System.IO.Path]::GetFullPath((Join-Path $workspaceFullPath $SessionId))
if (-not (Test-IsWithinPath -Child $sessionPath -Parent $workspaceFullPath)) { throw "Resolved session path escaped the workspace root." }
$metadataPath = Join-Path $sessionPath "session.json"
$artifactPath = Join-Path $sessionPath "artifacts"
$status = if ($Apply) { "created" } else { "planned" }

$metadata = [ordered]@{
    schemaVersion = 1
    sessionId = $SessionId
    status = "planned"
    createdAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    capabilityId = $routing.Selected.Id
    capabilityAvailability = $routing.Selected.Availability.state
    repositoryMode = $routing.Selected.RepositoryMode
    artifactDirectory = "artifacts"
    sourceCapabilityRegistry = "config/capabilities.json"
    sourceArtifactContract = "config/typed-artifact-contract.json"
}
if ($Apply) {
    if (Test-Path -LiteralPath $sessionPath) { throw "Session path already exists: $sessionPath" }
    New-Item -ItemType Directory -Path $artifactPath -Force | Out-Null
    $metadata | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $metadataPath -Encoding utf8NoBOM
}

$result = [pscustomobject]@{
    SchemaVersion = 1
    Kind = "ai-session-plan"
    Status = $status
    SessionId = $SessionId
    WorkspaceRoot = $workspaceFullPath
    SessionPath = $sessionPath
    IntendedWrites = @($metadataPath, $artifactPath)
    WorkspaceCreated = [bool]$Apply
    CapabilityInvoked = $false
    Capability = $routing.Selected
    Disclosures = [pscustomobject]@{
        RepositoryMode = $routing.Selected.RepositoryMode
        Availability = $routing.Selected.Availability.state
        Policy = $routing.Selected.Policy
        ArtifactPathDisclosedBeforeWrite = $true
    }
}
Write-SessionResult $result
exit 0
