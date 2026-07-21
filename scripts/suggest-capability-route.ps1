[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Text,
    [Parameter(Mandatory = $true)][string]$Model,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$ResponseFixturePath,
    [switch]$Execute,
    [int]$TimeoutSeconds = 60,
    [switch]$AsJson
)
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$capabilities = @((Get-Content -LiteralPath (Join-Path $repoRoot "config/capabilities.json") -Raw | ConvertFrom-Json).capabilities)
$suggestion = $null
$providerSource = "not-executed"
$parseError = $false
if ($Execute) {
    $allowed = @($capabilities | ForEach-Object { [ordered]@{ id = $_.id; name = $_.name; description = $_.description } }) | ConvertTo-Json -Compress -Depth 5
    $system = "Suggest exactly one capability ID from the supplied registry, or request clarification. Return JSON only. Never claim an action was invoked. Registry: $allowed"
    if ($ResponseFixturePath) {
        $response = Get-Content -LiteralPath $ResponseFixturePath -Raw | ConvertFrom-Json
        $providerSource = "validation-fixture"
    } else {
        $format = @{ type = "object"; properties = @{ capabilityId = @{ type = @("string", "null") }; needsClarification = @{ type = "boolean" }; clarificationQuestion = @{ type = @("string", "null") } }; required = @("capabilityId", "needsClarification", "clarificationQuestion") }
        $body = @{ model = $Model; stream = $false; format = $format; messages = @(@{ role = "system"; content = $system }, @{ role = "user"; content = $Text }); options = @{ temperature = 0 } } | ConvertTo-Json -Depth 12
        $response = Invoke-RestMethod -Method Post -Uri ($OllamaBaseUrl.TrimEnd('/') + "/api/chat") -ContentType "application/json" -Body $body -TimeoutSec $TimeoutSeconds
        $providerSource = "ollama-chat"
    }
    $raw = [string]$response.message.content
    try { $suggestion = $raw | ConvertFrom-Json -ErrorAction Stop }
    catch {
        if ($raw -match '(?s)\{.*\}') {
            try { $suggestion = $Matches[0] | ConvertFrom-Json -ErrorAction Stop } catch { $parseError = $true }
        } else { $parseError = $true }
    }
}
$suggestedId = if ($suggestion) { [string]$suggestion.capabilityId } else { $null }
$selected = if ($suggestedId) { @($capabilities | Where-Object id -eq $suggestedId) | Select-Object -First 1 } else { $null }
$needsClarification = [bool]($suggestion -and $suggestion.needsClarification)
if (-not $Execute) { $status = "planned"; $reason = "Execution is required before asking the optional LLM for a suggestion." }
elseif ($parseError) { $status = "rejected"; $reason = "The LLM response was not valid routing JSON." }
elseif ($suggestedId -and -not $selected) { $status = "rejected"; $reason = "The LLM suggested an ID outside the committed capability registry." }
elseif ($needsClarification -or -not $selected) { $status = "needs-clarification"; $reason = "The LLM requested clarification; no capability was selected." }
else { $status = "suggested"; $reason = "The LLM suggestion matched a committed capability; deterministic availability and policy checks still apply." }
$public = if ($selected) { [pscustomobject]@{ Id = $selected.id; Name = $selected.name; Availability = $selected.availability; RepositoryMode = $selected.repositoryMode; Policy = $selected.policy } } else { $null }
$result = [pscustomobject]@{
    SchemaVersion = 1; Kind = "llm-capability-suggestion"; Status = $status; ProviderSource = $providerSource
    Selected = $public; ClarificationQuestion = if ($needsClarification) { $suggestion.clarificationQuestion } else { $null }
    RegistryValidated = [bool]$selected; ExecutionEligible = [bool]($selected -and $selected.availability.state -eq "available")
    InvocationAllowed = $false; PromptPersisted = $false; EndpointPersisted = $false; Reason = $reason
}
if ($AsJson) { $result | ConvertTo-Json -Depth 10 }
else {
    Write-Output "Status: $status"
    if ($selected) { Write-Output "Suggested capability: $($selected.id)" }
    if ($result.ClarificationQuestion) { Write-Output "Clarification: $($result.ClarificationQuestion)" }
    Write-Output "Auto invoke: no"
}
exit 0
