[CmdletBinding()]
param(
    [ValidateSet("windows", "linux", "macos")]
    [string]$Platform = "windows",
    [string]$OutputPath,
    [string]$MarkdownOutputPath,
    [switch]$AsJson
)

$ErrorActionPreference = "Stop"

Import-Module (Join-Path $PSScriptRoot "OnboardingGuidance.psm1") -Force

$repoRoot = Split-Path -Parent $PSScriptRoot
$registryPath = Join-Path $repoRoot "config/workflows.json"
$registry = Import-OnboardingJson -Path $registryPath

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
    "onboarding" = "docs/haven-42-menu.md"
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
    "show-haven-42-menu" = "docs/haven-42-menu.md"
    "show-workflow-chooser" = "docs/workflow-chooser.md"
    "verify-runtime-output" = "docs/runtime-output-verification.md"
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
        Command = Get-OnboardingScriptCommand -Workflow $_ -Platform $Platform
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
        "Start with `docs/haven-42-menu.md` for the guided beginner path. Use this chooser when you need the complete workflow list.",
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

Write-OnboardingReport -Report $report -MarkdownRenderer ${function:ConvertTo-Markdown} -OutputPath $OutputPath -MarkdownOutputPath $MarkdownOutputPath -AsJson:$AsJson

exit 0
