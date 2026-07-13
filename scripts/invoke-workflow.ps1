[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$WorkflowId,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$WorkflowArguments = @(),
    [string]$WorkflowArgumentsJson,
    [ValidateSet("windows", "linux", "macos")]
    [string]$Platform = "windows",
    [string]$RegistryPath,
    [switch]$List,
    [switch]$Json,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

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
    if ($Json) {
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

if ($Json) {
    $resolved | ConvertTo-Json -Depth 10
}

& $entryPath @WorkflowArguments
exit $LASTEXITCODE
