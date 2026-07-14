[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$WorkflowId,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$WorkflowArguments = @(),
    [string]$WorkflowArgumentsJson,
    [string]$RequestJson,
    [ValidateSet("windows", "linux", "macos")]
    [string]$Platform = "windows",
    [string]$RegistryPath,
    [switch]$List,
    [switch]$Json,
    [switch]$Envelope,
    [switch]$IncludeOutput,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$envelopeEvents = [System.Collections.Generic.List[object]]::new()
$requestId = $null
trap {
    if ($Envelope -or -not [string]::IsNullOrWhiteSpace($RequestJson)) {
        $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = $envelopeEvents.Count + 1; type = "error"; code = "WORKFLOW_DISPATCH_FAILED"; message = $_.Exception.Message })
        [pscustomobject][ordered]@{
            schemaVersion = 1
            kind = "workflow-execution"
            requestId = $requestId
            status = "failed"
            workflow = if ($WorkflowId) { [pscustomobject][ordered]@{ id = $WorkflowId; platform = $Platform } } else { $null }
            events = @($envelopeEvents)
            result = [pscustomobject][ordered]@{ exitCode = 1; invoked = $false; dryRun = [bool]$DryRun; outputLineCount = 0 }
        } | ConvertTo-Json -Depth 10
        exit 1
    }
    break
}

if (-not [string]::IsNullOrWhiteSpace($RequestJson)) {
    $request = ConvertFrom-Json -InputObject $RequestJson
    if ([int]$request.schemaVersion -ne 1) { throw "Unsupported workflow request schemaVersion: $($request.schemaVersion)" }
    if ([string]::IsNullOrWhiteSpace([string]$request.workflowId)) { throw "Workflow request workflowId is required." }
    $WorkflowId = [string]$request.workflowId
    if ($request.platform) { $Platform = [string]$request.platform }
    if ($Platform -notin @("windows", "linux", "macos")) { throw "Unsupported platform: $Platform" }
    $DryRun = [bool]$request.dryRun
    $IncludeOutput = [bool]$request.includeOutput
    $WorkflowArguments = @($request.arguments | ForEach-Object { [string]$_ })
    $requestId = if ($request.requestId) { [string]$request.requestId } else { $null }
    $Envelope = $true
}

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $RegistryPath) {
    $RegistryPath = Join-Path $repoRoot "config/workflows.json"
}

function ConvertTo-RepositoryPath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "Workflow entry point is empty."
    }

    if ([System.IO.Path]::IsPathFullyQualified($Path) -or $Path -match "(^|/|\\)\.\.(/|\\|$)") {
        throw "Workflow entry point must be repository-relative: $Path"
    }

    $resolved = Join-Path $repoRoot $Path
    if (-not (Test-Path -LiteralPath $resolved)) {
        throw "Workflow entry point does not exist: $Path"
    }

    return $resolved
}

function Get-WorkflowRegistry {
    if (-not (Test-Path -LiteralPath $RegistryPath)) {
        throw "Workflow registry does not exist: $RegistryPath"
    }

    return Get-Content -LiteralPath $RegistryPath -Raw | ConvertFrom-Json
}

$registry = Get-WorkflowRegistry

if (-not [string]::IsNullOrWhiteSpace($WorkflowArgumentsJson)) {
    $jsonArguments = @(ConvertFrom-Json -InputObject $WorkflowArgumentsJson)
    $WorkflowArguments = @($WorkflowArguments) + @($jsonArguments | ForEach-Object { [string]$_ })
}

if ($List) {
    $items = @($registry.workflows | ForEach-Object {
        [pscustomobject]@{
            Id = $_.id
            Name = $_.name
            Category = $_.category
            SafetyLevel = $_.safetyLevel
            UiReady = [bool]$_.uiReady
        }
    })

    if ($Json) {
        $items | ConvertTo-Json -Depth 10
    } else {
        $items | Sort-Object Id | Format-Table -AutoSize
    }
    exit 0
}

if ([string]::IsNullOrWhiteSpace($WorkflowId)) {
    throw "WorkflowId is required unless -List is used."
}

$matches = @($registry.workflows | Where-Object { $_.id -eq $WorkflowId })
if ($matches.Count -eq 0) {
    throw "Workflow not found: $WorkflowId"
}
if ($matches.Count -gt 1) {
    throw "Workflow id is not unique: $WorkflowId"
}

$workflow = $matches[0]
$entryPoint = $workflow.entryPoints.$Platform
$entryPath = ConvertTo-RepositoryPath -Path $entryPoint

$resolved = [pscustomobject]@{
    Id = $workflow.id
    Name = $workflow.name
    Category = $workflow.category
    SafetyLevel = $workflow.safetyLevel
    Platform = $Platform
    EntryPoint = $entryPoint
    ResolvedEntryPoint = $entryPoint
    Arguments = @($WorkflowArguments)
}

if ($DryRun) {
    if ($Envelope) {
        $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = 1; type = "accepted"; message = "Workflow request accepted." })
        $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = 2; type = "progress"; message = "Workflow entry point resolved." })
        $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = 3; type = "warning"; code = "DRY_RUN"; message = "Dry run only; workflow was not invoked." })
        $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = 4; type = "result"; message = "Workflow plan resolved." })
        [pscustomobject][ordered]@{
            schemaVersion = 1
            kind = "workflow-execution"
            requestId = $requestId
            status = "planned"
            workflow = [pscustomobject][ordered]@{ id = $workflow.id; name = $workflow.name; category = $workflow.category; safetyLevel = $workflow.safetyLevel; platform = $Platform; entryPoint = $entryPoint; argumentCount = @($WorkflowArguments).Count }
            events = @($envelopeEvents)
            result = [pscustomobject][ordered]@{ exitCode = 0; invoked = $false; dryRun = $true; outputLineCount = 0 }
        } | ConvertTo-Json -Depth 10
    } elseif ($Json) {
        $resolved | ConvertTo-Json -Depth 10
    } else {
        Write-Host "Workflow: $($resolved.Id)"
        Write-Host "Name: $($resolved.Name)"
        Write-Host "Safety level: $($resolved.SafetyLevel)"
        Write-Host "Platform: $($resolved.Platform)"
        Write-Host "Entry point: $($resolved.EntryPoint)"
        if ($WorkflowArguments.Count -gt 0) {
            Write-Host "Arguments: $($WorkflowArguments -join ' ')"
        } else {
            Write-Host "Arguments: none"
        }
        Write-Host "Dry run only; workflow was not invoked."
    }
    exit 0
}

if ($Envelope) {
    $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = 1; type = "accepted"; message = "Workflow request accepted." })
    $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = 2; type = "progress"; message = "Workflow entry point resolved." })
    $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = 3; type = "progress"; message = "Workflow invocation started." })
    $powerShellHost = (Get-Process -Id $PID).Path
    $childOutput = @(& $powerShellHost -NoProfile -File $entryPath @WorkflowArguments 2>&1 | ForEach-Object { [string]$_ })
    $exitCode = if ($null -eq $LASTEXITCODE) { 0 } else { [int]$LASTEXITCODE }
    $status = if ($exitCode -eq 0) { "succeeded" } else { "failed" }
    $eventType = if ($exitCode -eq 0) { "result" } else { "error" }
    $envelopeEvents.Add([pscustomobject][ordered]@{ sequence = 4; type = $eventType; code = if ($exitCode -eq 0) { $null } else { "WORKFLOW_EXIT_NONZERO" }; message = if ($exitCode -eq 0) { "Workflow completed." } else { "Workflow returned a nonzero exit code." } })
    $result = [ordered]@{ exitCode = $exitCode; invoked = $true; dryRun = $false; outputLineCount = $childOutput.Count }
    if ($IncludeOutput) { $result.output = @($childOutput) }
    [pscustomobject][ordered]@{
        schemaVersion = 1
        kind = "workflow-execution"
        requestId = $requestId
        status = $status
        workflow = [pscustomobject][ordered]@{ id = $workflow.id; name = $workflow.name; category = $workflow.category; safetyLevel = $workflow.safetyLevel; platform = $Platform; entryPoint = $entryPoint; argumentCount = @($WorkflowArguments).Count }
        events = @($envelopeEvents)
        result = [pscustomobject]$result
    } | ConvertTo-Json -Depth 10
    exit $exitCode
}

if ($Json) {
    $resolved | ConvertTo-Json -Depth 10
}

$powerShellHost = (Get-Process -Id $PID).Path
& $powerShellHost -NoProfile -File $entryPath @WorkflowArguments
exit $LASTEXITCODE
