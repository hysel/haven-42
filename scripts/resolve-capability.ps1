[CmdletBinding()]
param(
    [string]$Text,
    [string]$CapabilityId,
    [switch]$List,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$registryPath = Join-Path $repoRoot "config/capabilities.json"
$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json

function Get-PublicCapability {
    param([object]$Capability)
    [pscustomobject]@{
        Id = $Capability.id
        Name = $Capability.name
        Category = $Capability.category
        Modality = $Capability.modality
        Description = $Capability.description
        Availability = $Capability.availability
        RepositoryMode = $Capability.repositoryMode
        OutputArtifactTypes = @($Capability.outputArtifactTypes)
        Policy = $Capability.policy
        WorkflowSource = $Capability.workflowSource
    }
}

function Write-Result {
    param([object]$Result)
    if ($AsJson) {
        $Result | ConvertTo-Json -Depth 12
        return
    }
    if ($Result.Status -eq "selected") {
        Write-Output "Capability: $($Result.Selected.Id)"
        Write-Output "Availability: $($Result.Selected.Availability.state)"
        Write-Output "Auto invoke: no"
        Write-Output "Reason: $($Result.Reason)"
    } else {
        Write-Output "Routing status: $($Result.Status)"
        Write-Output "Reason: $($Result.Reason)"
        foreach ($candidate in @($Result.Candidates)) { Write-Output "- $($candidate.Id): $($candidate.Name)" }
    }
}

if ($List) {
    $result = [pscustomobject]@{
        SchemaVersion = 1
        Kind = "capability-list"
        SourceRegistry = "config/capabilities.json"
        Capabilities = @($registry.capabilities | ForEach-Object { Get-PublicCapability $_ })
    }
    Write-Result $result
    exit 0
}

$selected = $null
$candidates = @()
$reason = ""
if (-not [string]::IsNullOrWhiteSpace($CapabilityId)) {
    $selected = @($registry.capabilities | Where-Object { $_.id -eq $CapabilityId }) | Select-Object -First 1
    if (-not $selected) { throw "Unknown capability id: $CapabilityId" }
    $reason = "Explicit capability id selected."
} elseif (-not [string]::IsNullOrWhiteSpace($Text)) {
    $normalized = (($Text.ToLowerInvariant() -replace '[^a-z0-9]+', ' ').Trim())
    $tokens = @($normalized -split ' ' | Where-Object { $_ })
    $scored = foreach ($capability in $registry.capabilities) {
        $score = 0
        $signals = @()
        foreach ($phrase in @($capability.routing.phrases)) {
            $normalizedPhrase = (($phrase.ToLowerInvariant() -replace '[^a-z0-9]+', ' ').Trim())
            if ($normalized.Contains($normalizedPhrase)) { $score += 1000 + $normalizedPhrase.Length; $signals += "phrase:$phrase" }
        }
        foreach ($keyword in @($capability.routing.keywords)) {
            if ($tokens -contains $keyword.ToLowerInvariant()) { $score += 10; $signals += "keyword:$keyword" }
        }
        if ($score -gt 0) { [pscustomobject]@{ Capability = $capability; Score = $score; Signals = $signals } }
    }
    if (@($scored).Count -gt 0) {
        $topScore = ($scored | Measure-Object -Property Score -Maximum).Maximum
        $top = @($scored | Where-Object Score -eq $topScore | Sort-Object { $_.Capability.id })
        if ($top.Count -eq 1) {
            $selected = $top[0].Capability
            $reason = "Deterministic registry signals selected this capability."
        } else {
            $candidates = @($top | ForEach-Object { Get-PublicCapability $_.Capability })
            $reason = "Multiple capabilities received the same routing score; clarification is required."
        }
    } else {
        $reason = "No deterministic registry signal matched; show the capability menu or ask a clarifying question."
    }
} else {
    throw "Provide -Text, -CapabilityId, or -List."
}

$status = if ($selected) { "selected" } elseif ($candidates.Count -gt 0) { "needs-clarification" } else { "unmatched" }
$result = [pscustomobject]@{
    SchemaVersion = 1
    Kind = "capability-routing"
    Status = $status
    SourceRegistry = "config/capabilities.json"
    Selected = if ($selected) { Get-PublicCapability $selected } else { $null }
    Candidates = $candidates
    InvocationAllowed = $false
    Reason = $reason
}
Write-Result $result
exit 0
