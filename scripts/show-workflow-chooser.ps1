[CmdletBinding()]
param(
    [ValidateSet("windows", "linux", "macos")]
    [string]$Platform = "windows",
    [string]$OutputPath,
    [string]$MarkdownOutputPath,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$registryPath = Join-Path $repoRoot "config/workflows.json"
$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json

$referenceByCategory = @{
    "agent-surface-validation" = "docs/agent-cli-surface-model-testing.md"
    "configuration" = "docs/hardware-aware-recommendations.md"
    "discovery" = "docs/hardware-aware-recommendations.md"
    "evidence" = "docs/evidence-dashboard.md"
    "health" = "docs/workflow-registry.md"
    "installation" = "docs/shared-asset-installation.md"
    "maintenance" = "docs/workflow-registry.md"
    "model-installation" = "docs/local-agent-model-testing.md"
    "model-selection" = "docs/local-model-selection.md"
    "model-validation" = "docs/local-agent-model-testing.md"
    "onboarding" = "docs/agent-pack-menu.md"
    "release-readiness" = "docs/release.md"
    "sample-generation" = "docs/sample-repository-factory.md"
    "validation" = "docs/runtime-validation.md"
}

$referenceByWorkflow = @{
    "discover-online-models" = "docs/online-model-discovery.md"
    "generate-evidence-dashboard" = "docs/evidence-dashboard.md"
    "generate-model-scorecard" = "docs/model-scorecard.md"
    "get-beginner-setup-plan" = "docs/beginner-setup-mode.md"
    "profile-remote-hardware" = "docs/remote-hardware-profile.md"
    "show-agent-pack-menu" = "docs/agent-pack-menu.md"
    "show-workflow-chooser" = "docs/workflow-chooser.md"
    "verify-runtime-output" = "docs/runtime-output-verification.md"
}

function Get-ScriptCommand {
    param([object]$Workflow)

    $entry = $Workflow.entryPoints.$Platform
    if ([string]::IsNullOrWhiteSpace($entry)) {
        throw "Workflow $($Workflow.id) does not support $Platform."
    }

    if ($Platform -eq "windows") {
        $path = ".\" + ($entry -replace "/", "\")
        if ($entry -match "\.ps1$") {
            return "pwsh -NoProfile -ExecutionPolicy Bypass -File $path"
        }
        return $path
    }

    return "./$entry"
}

function Get-ReferencePath {
    param([object]$Workflow)

    if ($referenceByWorkflow.ContainsKey($Workflow.id)) {
        return $referenceByWorkflow[$Workflow.id]
    }

    if ($referenceByCategory.ContainsKey($Workflow.category)) {
        return $referenceByCategory[$Workflow.category]
    }

    return "docs/script-reference-appendix.md"
}

$items = @($registry.workflows | Sort-Object category, id | ForEach-Object {
    [pscustomobject]@{
        Id = $_.id
        Name = $_.name
        Category = $_.category
        SafetyLevel = $_.safetyLevel
        UiReady = [bool]$_.uiReady
        Purpose = $_.purpose
        Command = Get-ScriptCommand -Workflow $_
        Reference = Get-ReferencePath -Workflow $_
        Appendix = "docs/script-reference-appendix.md"
    }
})

$report = [pscustomobject]@{
    SchemaVersion = 1
    GeneratedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    Platform = $Platform
    SourceWorkflowRegistry = "config/workflows.json"
    WorkflowCount = $items.Count
    UiReadyCount = @($items | Where-Object { $_.UiReady }).Count
    Categories = @($items | Select-Object -ExpandProperty Category -Unique)
    Workflows = $items
}

function ConvertTo-Markdown {
    param([object]$Report)

    $lines = @(
        "# Workflow Chooser",
        "",
        "Generated from `config/workflows.json`.",
        "",
        "Start with `docs/agent-pack-menu.md` for the guided beginner path. Use this chooser when you need the complete workflow list.",
        "",
        "| Category | Workflow | Safety | UI | Command | Reference |",
        "| --- | --- | --- | --- | --- | --- |"
    )

    foreach ($workflow in @($Report.Workflows)) {
        $ui = if ($workflow.UiReady) { "yes" } else { "no" }
        $lines += "| $($workflow.Category) | `$($workflow.Id)` | `$($workflow.SafetyLevel)` | $ui | `$($workflow.Command)` | `$($workflow.Reference)` |"
    }

    $lines += @(
        "",
        "Detailed script options stay in `docs/script-reference-appendix.md`."
    )

    return ($lines -join "`n") + "`n"
}

if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding utf8
}

if ($MarkdownOutputPath) {
    $parent = Split-Path -Parent $MarkdownOutputPath
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    ConvertTo-Markdown -Report $report | Set-Content -LiteralPath $MarkdownOutputPath -Encoding utf8
}

if ($AsJson -or $OutputPath) {
    $report | ConvertTo-Json -Depth 20
} else {
    ConvertTo-Markdown -Report $report
}

exit 0
