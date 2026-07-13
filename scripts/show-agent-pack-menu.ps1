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
$surfaceMatrixPath = Join-Path $repoRoot "config/agent-surface-capabilities.json"

$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
$surfaceMatrix = Get-Content -LiteralPath $surfaceMatrixPath -Raw | ConvertFrom-Json

function Get-Workflow {
    param([string]$Id)

    $matches = @($registry.workflows | Where-Object { $_.id -eq $Id })
    if ($matches.Count -ne 1) {
        throw "Workflow not found or not unique: $Id"
    }
    return $matches[0]
}

function Get-ScriptCommand {
    param(
        [object]$Workflow,
        [string]$Arguments = ""
    )

    $entry = $Workflow.entryPoints.$Platform
    if ([string]::IsNullOrWhiteSpace($entry)) {
        throw "Workflow $($Workflow.id) does not support $Platform."
    }

    if ($Platform -eq "windows") {
        $path = ".\" + ($entry -replace "/", "\")
        if ($entry -match "\.ps1$") {
            return "pwsh -NoProfile -ExecutionPolicy Bypass -File $path $Arguments".Trim()
        }
        return "$path $Arguments".Trim()
    }

    return "./$entry $Arguments".Trim()
}

function New-MenuItem {
    param(
        [string]$Id,
        [string]$Title,
        [string]$Intent,
        [string]$PrimaryWorkflowId,
        [string[]]$RelatedWorkflowIds = @(),
        [string]$Description,
        [string]$Command,
        [bool]$BeginnerRecommended = $false
    )

    $primary = Get-Workflow -Id $PrimaryWorkflowId
    [pscustomobject]@{
        Id = $Id
        Title = $Title
        Intent = $Intent
        BeginnerRecommended = $BeginnerRecommended
        PrimaryWorkflowId = $PrimaryWorkflowId
        RelatedWorkflowIds = @($RelatedWorkflowIds)
        SafetyLevel = $primary.safetyLevel
        Description = $Description
        Command = $Command
    }
}

$beginner = Get-Workflow -Id "get-beginner-setup-plan"
$health = Get-Workflow -Id "test-local-agent-health"
$recommend = Get-Workflow -Id "recommend-agent-config"
$install = Get-Workflow -Id "install-pack-assets"
$validate = Get-Workflow -Id "test-local-agent-models"
$cleanup = Get-Workflow -Id "cleanup-local-agent-artifacts"
$release = Get-Workflow -Id "test-release-readiness"
$evidence = Get-Workflow -Id "generate-evidence-dashboard"

$menuItems = @(
    New-MenuItem `
        -Id "first-time-setup" `
        -Title "First-Time Setup" `
        -Intent "Start here" `
        -PrimaryWorkflowId "get-beginner-setup-plan" `
        -RelatedWorkflowIds @("test-local-agent-health", "profile-local-hardware", "recommend-agent-config", "install-pack-assets") `
        -Description "Generate an ordered setup plan instead of choosing scripts manually." `
        -Command (Get-ScriptCommand -Workflow $beginner -Arguments "-Platform $Platform -MarkdownOutputPath runtime-validation-output/beginner-setup-plan.md -OutputPath runtime-validation-output/beginner-setup-plan.json -AsJson") `
        -BeginnerRecommended $true
    New-MenuItem `
        -Id "health-check" `
        -Title "Health Check" `
        -Intent "Check local setup" `
        -PrimaryWorkflowId "test-local-agent-health" `
        -RelatedWorkflowIds @("generate-evidence-dashboard") `
        -Description "Inspect repository config, local references, runtime output, and optional model-server reachability." `
        -Command (Get-ScriptCommand -Workflow $health -Arguments "-TargetRepo <your-project-path> -SkipOllama -AsJson -OutputPath runtime-validation-output/health.json") `
        -BeginnerRecommended $true
    New-MenuItem `
        -Id "model-choice" `
        -Title "Model Choice" `
        -Intent "Pick a local model" `
        -PrimaryWorkflowId "recommend-agent-config" `
        -RelatedWorkflowIds @("profile-local-hardware", "generate-model-scorecard", "discover-online-models") `
        -Description "Use hardware profile and evidence data to recommend conservative local model lanes." `
        -Command (Get-ScriptCommand -Workflow $recommend -Arguments "-ModelProfilePath runtime-validation-output/local-model-profile.json -OutputPath runtime-validation-output/model-config-recommendation.json")
    New-MenuItem `
        -Id "install-configure" `
        -Title "Install Or Configure Agent" `
        -Intent "Install assets" `
        -PrimaryWorkflowId "install-pack-assets" `
        -RelatedWorkflowIds @("apply-agent-config", "recommend-agent-config") `
        -Description "Preview asset install or local-only config changes before applying them to a project." `
        -Command (Get-ScriptCommand -Workflow $install -Arguments "-TargetRepo <your-project-path> -DryRun") `
        -BeginnerRecommended $true
    New-MenuItem `
        -Id "validate-model-agent" `
        -Title "Validate Model Or Agent" `
        -Intent "Test before trust" `
        -PrimaryWorkflowId "test-local-agent-models" `
        -RelatedWorkflowIds @("test-agent-cli-surface", "run-runtime-validation", "verify-runtime-output") `
        -Description "Run model and agent checks before promoting a surface or model to stronger use." `
        -Command (Get-ScriptCommand -Workflow $validate -Arguments "-TargetRepo <your-project-path> -ModelProfilePath runtime-validation-output/local-model-profile.json -UnloadAfterEach -OutputPath runtime-validation-output/local-agent-model-tests.json")
    New-MenuItem `
        -Id "review-evidence" `
        -Title "Review Evidence" `
        -Intent "Compare readiness" `
        -PrimaryWorkflowId "generate-evidence-dashboard" `
        -RelatedWorkflowIds @("generate-model-scorecard", "get-beginner-setup-plan") `
        -Description "Summarize evidence status, model coverage, and agent surface readiness." `
        -Command (Get-ScriptCommand -Workflow $evidence -Arguments "-OutputPath runtime-validation-output/evidence-dashboard.json -MarkdownOutputPath runtime-validation-output/evidence-dashboard.md -AsJson") `
        -BeginnerRecommended $true
    New-MenuItem `
        -Id "cleanup" `
        -Title "Cleanup Local Artifacts" `
        -Intent "Clean local output" `
        -PrimaryWorkflowId "cleanup-local-agent-artifacts" `
        -Description "Dry-run cleanup of ignored runtime output, generated samples, failed reports, and old backups." `
        -Command (Get-ScriptCommand -Workflow $cleanup -Arguments "-TargetRepo <your-project-path> -AsJson -OutputPath runtime-validation-output/cleanup-plan.json")
    New-MenuItem `
        -Id "release-readiness" `
        -Title "Release Readiness" `
        -Intent "Validate the pack" `
        -PrimaryWorkflowId "test-release-readiness" `
        -RelatedWorkflowIds @("validate-pack", "test-pack", "build-release-package") `
        -Description "Run the local gate before release, commit, or push." `
        -Command (Get-ScriptCommand -Workflow $release -Arguments "-AllowDirty -AsJson -OutputPath runtime-validation-output/release-readiness.json")
)

$surfaceSummary = @($surfaceMatrix.surfaces | Sort-Object name | ForEach-Object {
    $activities = @($_.activities.PSObject.Properties | ForEach-Object { $_.Value })
    [pscustomobject]@{
        Id = $_.id
        Name = $_.name
        ValidationLevel = $_.currentValidationLevel
        InstallStatus = $_.activities.install.status
        ConfigureStatus = $_.activities.configure.status
        TestStatus = $_.activities.test.status
        SupportedActivityCount = @($activities | Where-Object { $_.status -eq "supported" }).Count
        ValidatedActivityCount = @($activities | Where-Object { $_.status -eq "validated" }).Count
        BlockedActivityCount = @($activities | Where-Object { $_.status -eq "blocked" }).Count
    }
})

$report = [pscustomobject]@{
    SchemaVersion = 1
    GeneratedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    Platform = $Platform
    SourceWorkflowRegistry = "config/workflows.json"
    SourceSurfaceMatrix = "config/agent-surface-capabilities.json"
    MenuItemCount = $menuItems.Count
    MenuItems = $menuItems
    SurfaceCount = $surfaceSummary.Count
    AgentSurfaces = $surfaceSummary
    Appendix = "docs/script-reference-appendix.md"
}

function ConvertTo-Markdown {
    param([object]$Report)

    $lines = @(
        "# Agent Pack Menu",
        "",
        "Generated from `config/workflows.json` and `config/agent-surface-capabilities.json`.",
        "",
        "## Recommended Actions",
        "",
        "| Action | Intent | Safety | Workflow |",
        "| --- | --- | --- | --- |"
    )

    foreach ($item in @($Report.MenuItems)) {
        $lines += "| $($item.Title) | $($item.Intent) | `$($item.SafetyLevel)` | `$($item.PrimaryWorkflowId)` |"
    }

    $lines += @("", "## Commands", "")
    foreach ($item in @($Report.MenuItems)) {
        $lines += @(
            "### $($item.Title)",
            "",
            $item.Description,
            "",
            '```text',
            $item.Command,
            '```',
            ""
        )
    }

    $lines += @(
        "## Agent Surface Snapshot",
        "",
        "| Surface | Install | Configure | Test | Validation |",
        "| --- | --- | --- | --- | --- |"
    )

    foreach ($surface in @($Report.AgentSurfaces)) {
        $lines += "| $($surface.Name) | $($surface.InstallStatus) | $($surface.ConfigureStatus) | $($surface.TestStatus) | $($surface.ValidationLevel) |"
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
