[CmdletBinding()]
param([string]$Text, [string]$RouteId, [switch]$AsJson)
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$routes = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/engineering-routes.json") -Raw | ConvertFrom-Json).routes)
$workflows = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/workflows.json") -Raw | ConvertFrom-Json).workflows)
$selected = $null
$ties = @()
if ($RouteId) {
    $selected = @($routes | Where-Object id -eq $RouteId) | Select-Object -First 1
    if (-not $selected) { throw "Unknown route id: $RouteId" }
} elseif ($Text) {
    $normalized = (($Text.ToLowerInvariant() -replace '[^a-z0-9]+', ' ').Trim())
    $tokens = @($normalized -split ' ' | Where-Object { $_ })
    $scored = foreach ($route in $routes) {
        $score = 0
        foreach ($phrase in @($route.phrases)) {
            $normalizedPhrase = (($phrase.ToLowerInvariant() -replace '[^a-z0-9]+', ' ').Trim())
            if ($normalized.Contains($normalizedPhrase)) { $score += 1000 + $normalizedPhrase.Length }
        }
        foreach ($keyword in @($route.keywords)) { if ($tokens -contains $keyword.ToLowerInvariant()) { $score += 10 } }
        if ($score -gt 0) { [pscustomobject]@{ Route = $route; Score = $score } }
    }
    if (@($scored).Count -gt 0) {
        $topScore = ($scored | Measure-Object Score -Maximum).Maximum
        $top = @($scored | Where-Object Score -eq $topScore | Sort-Object { $_.Route.id })
        if ($top.Count -eq 1) { $selected = $top[0].Route } else { $ties = @($top | ForEach-Object { $_.Route.id }) }
    }
} else { throw "Provide -Text or -RouteId." }

$steps = @()
if ($selected) {
    foreach ($workflowId in @($selected.workflowIds)) {
        $workflow = @($workflows | Where-Object id -eq $workflowId) | Select-Object -First 1
        if (-not $workflow) { throw "Route references unknown workflow: $workflowId" }
        $steps += [pscustomobject]@{ WorkflowId = $workflowId; Name = $workflow.name; SafetyLevel = $workflow.safetyLevel; EntryPoints = $workflow.entryPoints }
    }
}
$result = [pscustomobject]@{
    SchemaVersion = 1
    Kind = "engineering-route"
    Status = if ($selected) { "selected" } elseif ($ties.Count -gt 0) { "needs-clarification" } else { "unmatched" }
    SelectedRouteId = if ($selected) { $selected.id } else { $null }
    CapabilityId = if ($selected) { $selected.capabilityId } else { $null }
    RequiresRepository = if ($selected) { $selected.requiresRepository } else { $null }
    Steps = $steps
    Candidates = $ties
    InvocationAllowed = $false
    Reason = if ($selected) { "Deterministic route selected; review inputs and approval boundaries before invoking any workflow." } else { "A unique engineering route could not be selected." }
}
if ($AsJson) { $result | ConvertTo-Json -Depth 10 }
elseif ($selected) {
    Write-Output "Route: $($selected.id)"
    foreach ($step in $steps) { Write-Output "- $($step.WorkflowId) [$($step.SafetyLevel)]" }
    Write-Output "Auto invoke: no"
} else {
    Write-Output "Routing status: $($result.Status)"
    foreach ($candidate in $ties) { Write-Output "- $candidate" }
}
exit 0
