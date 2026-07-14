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

function New-Step {
    param(
        [string]$Id,
        [string]$Title,
        [string]$WorkflowId,
        [string]$Why,
        [string]$Command,
        [bool]$RequiresReview = $false
    )

    $workflow = Get-OnboardingWorkflow -Registry $registry -Id $WorkflowId
    [pscustomobject]@{
        Id = $Id
        Title = $Title
        WorkflowId = $WorkflowId
        SafetyLevel = $workflow.safetyLevel
        RequiresReviewBeforeApply = $RequiresReview
        Why = $Why
        Command = $Command
    }
}

$profileCommand = if ($Platform -eq "windows") {
    "pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\get-local-model-profile.windows.ps1 -AsJson | Set-Content -Path runtime-validation-output\local-model-profile.json"
} elseif ($Platform -eq "linux") {
    "./scripts/get-local-model-profile.linux.sh --as-json > runtime-validation-output/local-model-profile.json"
} else {
    "./scripts/get-local-model-profile.macos.sh --as-json > runtime-validation-output/local-model-profile.json"
}

$steps = @(
    New-Step `
        -Id "check-local-health" `
        -Title "Check local setup health" `
        -WorkflowId "test-local-agent-health" `
        -Why "Verifies repository config and local output folders before changing anything." `
        -Command (Get-OnboardingScriptCommand -Workflow (Get-OnboardingWorkflow -Registry $registry -Id "test-local-agent-health") -Platform $Platform -Arguments "-TargetRepo <your-project-path> -SkipOllama -AsJson -OutputPath runtime-validation-output/beginner-health.json")
    New-Step `
        -Id "profile-hardware" `
        -Title "Profile local hardware and installed models" `
        -WorkflowId "profile-local-hardware" `
        -Why "Collects the sanitized profile used by recommendation and model testing workflows." `
        -Command $profileCommand
    New-Step `
        -Id "review-evidence" `
        -Title "Generate evidence dashboard" `
        -WorkflowId "generate-evidence-dashboard" `
        -Why "Shows what is tested, validated, planned, or recommendation-only before installation." `
        -Command (Get-OnboardingScriptCommand -Workflow (Get-OnboardingWorkflow -Registry $registry -Id "generate-evidence-dashboard") -Platform $Platform -Arguments "-OutputPath runtime-validation-output/evidence-dashboard.json -MarkdownOutputPath runtime-validation-output/evidence-dashboard.md -AsJson")
    New-Step `
        -Id "review-models" `
        -Title "Generate model scorecard" `
        -WorkflowId "generate-model-scorecard" `
        -Why "Summarizes model readiness from committed evidence before choosing a coding model." `
        -Command (Get-OnboardingScriptCommand -Workflow (Get-OnboardingWorkflow -Registry $registry -Id "generate-model-scorecard") -Platform $Platform -Arguments "-OutputPath runtime-validation-output/model-scorecard.json -MarkdownOutputPath runtime-validation-output/model-scorecard.md -AsJson")
    New-Step `
        -Id "recommend-config" `
        -Title "Generate model and config recommendation" `
        -WorkflowId "recommend-agent-config" `
        -Why "Uses the hardware profile, model catalog, and evidence catalog to pick conservative model lanes." `
        -Command (Get-OnboardingScriptCommand -Workflow (Get-OnboardingWorkflow -Registry $registry -Id "recommend-agent-config") -Platform $Platform -Arguments "-ModelProfilePath runtime-validation-output/local-model-profile.json -OutputPath runtime-validation-output/model-config-recommendation.json")
    New-Step `
        -Id "dry-run-config" `
        -Title "Preview local-only Continue config" `
        -WorkflowId "apply-agent-config" `
        -Why "Shows the local config change before writing project config files." `
        -Command (Get-OnboardingScriptCommand -Workflow (Get-OnboardingWorkflow -Registry $registry -Id "apply-agent-config") -Platform $Platform -Arguments "-TargetRepo <your-project-path> -RecommendationPath runtime-validation-output/model-config-recommendation.json -DryRun") `
        -RequiresReview $true
    New-Step `
        -Id "install-pack-dry-run" `
        -Title "Preview pack install" `
        -WorkflowId "install-pack-assets" `
        -Why "Confirms which files would be installed or backed up before copying assets." `
        -Command (Get-OnboardingScriptCommand -Workflow (Get-OnboardingWorkflow -Registry $registry -Id "install-pack-assets") -Platform $Platform -Arguments "-TargetRepo <your-project-path> -DryRun") `
        -RequiresReview $true
    New-Step `
        -Id "test-models" `
        -Title "Test local agent models" `
        -WorkflowId "test-local-agent-models" `
        -Why "Runs API-level local model checks and unloads models after each test." `
        -Command (Get-OnboardingScriptCommand -Workflow (Get-OnboardingWorkflow -Registry $registry -Id "test-local-agent-models") -Platform $Platform -Arguments "-TargetRepo <your-project-path> -ModelProfilePath runtime-validation-output/local-model-profile.json -UnloadAfterEach -OutputPath runtime-validation-output/local-agent-model-tests.json")
)

$report = [pscustomobject]@{
    SchemaVersion = 1
    GeneratedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    Platform = $Platform
    SourceWorkflowRegistry = "config/workflows.json"
    StepCount = $steps.Count
    Steps = $steps
}

function ConvertTo-Markdown {
    param([object]$Report)

    $lines = @(
        "# Beginner Setup Plan",
        "",
        "Generated from ``config/workflows.json`` for ``$($Report.Platform)``.",
        "",
        "| Step | Workflow | Safety | Review before apply |",
        "| --- | --- | --- | --- |"
    )

    foreach ($step in @($Report.Steps)) {
        $review = if ($step.RequiresReviewBeforeApply) { "yes" } else { "no" }
        $lines += "| $($step.Title) | ``$($step.WorkflowId)`` | ``$($step.SafetyLevel)`` | $review |"
    }

    $lines += @("", "## Commands", "")
    foreach ($step in @($Report.Steps)) {
        $lines += @(
            "### $($step.Title)",
            "",
            $step.Why,
            "",
            '```text',
            $step.Command,
            '```',
            ""
        )
    }

    return ($lines -join "`n") + "`n"
}

Write-OnboardingReport -Report $report -MarkdownRenderer ${function:ConvertTo-Markdown} -OutputPath $OutputPath -MarkdownOutputPath $MarkdownOutputPath -AsJson:$AsJson

exit 0
