param(
    [Alias("target-repo")]
    [string]$TargetRepo = (Get-Location).Path,
    [Alias("config-path")]
    [string]$ConfigPath,
    [Alias("context-path")]
    [string]$ContextPath,
    [Alias("append-summary")]
    [switch]$AppendSummary
)

$ErrorActionPreference = "Stop"

$packRoot = Split-Path -Parent $PSScriptRoot

if (-not $ConfigPath) {
    $localConfig = Join-Path $packRoot ".continue/config.local.yaml"
    $defaultConfig = Join-Path $packRoot ".continue/config.yaml"

    if (Test-Path -LiteralPath $localConfig) {
        $ConfigPath = $localConfig
    } else {
        $ConfigPath = $defaultConfig
    }
}

if (-not (Test-Path -LiteralPath $TargetRepo)) {
    throw "Target repository path does not exist: $TargetRepo"
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "Continue config path does not exist: $ConfigPath"
}

$ConfigPath = (Resolve-Path -LiteralPath $ConfigPath).Path

function Test-LocalOllamaConfig {
    param([string]$Path)

    $configText = Get-Content -LiteralPath $Path -Raw
    if ($configText -notmatch 'provider:\s*ollama' -or $configText -notmatch 'apiBase:\s*(\S+)') {
        return
    }

    $apiBase = $Matches[1].Trim().TrimEnd('/')
    try {
        Invoke-RestMethod -Uri "$apiBase/api/tags" -TimeoutSec 15 | Out-Null
    }
    catch {
        throw "Local Ollama API preflight failed. Confirm the local model server is reachable before running runtime validation."
    }
}

Test-LocalOllamaConfig -Path $ConfigPath

$promptRoot = Join-Path $packRoot ".continue/prompts"
$runtimeDoc = Join-Path $packRoot "docs/runtime-validation.md"
$outputRoot = Join-Path $packRoot "runtime-validation-output"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runRoot = Join-Path $outputRoot $timestamp

New-Item -ItemType Directory -Force -Path $runRoot | Out-Null

if (-not $ContextPath) {
    $ContextPath = Join-Path $runRoot "runtime-context.md"
    & (Join-Path $packRoot "scripts/generate-runtime-context.ps1") -TargetRepo $TargetRepo -OutputPath $ContextPath
}

if (-not (Test-Path -LiteralPath $ContextPath)) {
    throw "Runtime context path does not exist: $ContextPath"
}

$ContextPath = (Resolve-Path -LiteralPath $ContextPath).Path

$workflows = @(
    @{
        Name = "repository-discovery"
        Prompt = "repository-discovery.md"
        Task = "Review this repository. Inspect the file tree, project files, source layout, tests, configuration, and top-level documentation. Produce the full repository-discovery output."
    },
    @{
        Name = "architecture-review"
        Prompt = "architecture-review.md"
        Task = "Review this repository architecture. Evaluate Clean Architecture, SOLID, DDD, separation of concerns, layering, coupling, cohesion, dependency direction, scalability, maintainability, and extensibility."
    },
    @{
        Name = "code-review"
        Prompt = "code-review.md"
        Task = "Review the current repository and any current git changes. Focus on correctness, maintainability, security, tests, and regression risk."
    },
    @{
        Name = "implementation-plan"
        Prompt = "implementation-plan.md"
        Task = "Create an implementation plan for adding audit logging to important write operations. Do not modify files. Identify affected components, risks, tests, and rollout steps."
    },
    @{
        Name = "bug-investigation"
        Prompt = "bug-investigation.md"
        Task = "Investigate this hypothetical issue: API requests sometimes return 500 errors during order creation. Inspect likely code paths and produce an investigation plan. Do not modify files."
    },
    @{
        Name = "security-review"
        Prompt = "security-review.md"
        Task = "Review this repository for authentication, authorization, input validation, secrets, logging, dependency, and data exposure risks."
    },
    @{
        Name = "performance-review"
        Prompt = "performance-review.md"
        Task = "Review this repository for performance risks, including database access, async usage, memory, API latency, caching, batching, and scalability."
    },
    @{
        Name = "documentation"
        Prompt = "documentation.md"
        Task = "Review this repository documentation. Identify missing setup instructions, architecture notes, operational guidance, and developer onboarding gaps."
    },
    @{
        Name = "ai-framework-self-review"
        Prompt = "ai-framework-self-review.md"
        Task = "Review whether this repository is ready for AI-assisted engineering workflows. Identify missing guidance, risky ambiguity, and documentation gaps."
    },
    @{
        Name = "refactoring-planner"
        Prompt = "refactoring-planner.md"
        Task = "Identify one high-value refactoring opportunity in this repository and create a safe refactoring plan. Do not modify files."
    },
    @{
        Name = "product-manager"
        Prompt = "product-manager.md"
        Task = "Review this repository from a product and delivery perspective. Identify unclear user value, missing acceptance criteria, release risks, and prioritization questions."
    },
    @{
        Name = "release-readiness"
        Prompt = "release-readiness.md"
        Task = "Assess whether this repository appears ready for release. Review testing, documentation, security, operations, rollback, known risks, and go/no-go criteria."
    }
)

$summaryRows = New-Object System.Collections.Generic.List[string]
$summaryRows.Add("| Workflow | Status | Output File |")
$summaryRows.Add("| --- | --- | --- |")

function Test-ToolCallOnlyOutput {
    param([string]$Text)

    $trimmed = $Text.Trim()
    return $trimmed -match '^\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:'
}

function Invoke-OutputVerification {
    param(
        [string]$OutputPath,
        [string]$WorkflowName
    )

    $verifierPath = Join-Path $packRoot "scripts/verify-runtime-output.ps1"
    $verificationOutput = & $verifierPath -OutputPath $OutputPath -ContextPath $ContextPath -WorkflowName $WorkflowName 2>&1

    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = ($verificationOutput -join "`n")
    }
}

$runtimeGuardrails = "Use only filenames that appear in the supplied runtime repository context. Do not invent or assume conventional files such as CHANGELOG.md, CONTRIBUTING.md, ARCHITECTURE.md, CI workflows, migration scripts, manifests, or .continue/config.yaml. If a useful file is absent, label it as recommended new file: <path> or missing file recommendation: <path>. If uncertain, write unconfirmed filename instead of naming it as existing."
Push-Location -LiteralPath $TargetRepo
try {
    foreach ($workflow in $workflows) {
        $promptPath = Join-Path $promptRoot $workflow.Prompt
        $outputPath = Join-Path $runRoot "$($workflow.Name).md"

        if (-not (Test-Path -LiteralPath $promptPath)) {
            throw "Prompt file does not exist: $promptPath"
        }

        Write-Host "Running $($workflow.Name)..." -ForegroundColor Cyan

        $output = & npx @continuedev/cli `
            --config $ConfigPath `
            --prompt $promptPath `
            --prompt $ContextPath `
            --readonly `
            -p "$runtimeGuardrails Use the supplied runtime repository context. Do not call tools. Do not request List, Read, Bash, or git status. Produce final review text only. $($workflow.Task)" 2>&1

        $exitCode = $LASTEXITCODE
        $outputText = if ($null -eq $output) { "" } else { ($output -join "`n") }
        Set-Content -LiteralPath $outputPath -Value $outputText

        if ($exitCode -eq 0 -and [string]::IsNullOrWhiteSpace($outputText)) {
            $verificationPath = Join-Path $runRoot "$($workflow.Name).verification.txt"
            "FAIL EMPTY_MODEL_OUTPUT" | Set-Content -LiteralPath $verificationPath
            $summaryRows.Add("| $($workflow.Name) | Empty output | $outputPath |")
        } elseif ($exitCode -eq 0 -and (Test-ToolCallOnlyOutput -Text $outputText)) {
            $summaryRows.Add("| $($workflow.Name) | Tool call only output | $outputPath |")
        } elseif ($exitCode -eq 0) {
            $verification = Invoke-OutputVerification -OutputPath $outputPath -WorkflowName $workflow.Name
            $verificationPath = Join-Path $runRoot "$($workflow.Name).verification.txt"
            $verification.Output | Set-Content -LiteralPath $verificationPath

            if ($verification.ExitCode -eq 0) {
                $summaryRows.Add("| $($workflow.Name) | Completed; verification passed | $outputPath |")
            } else {
                $summaryRows.Add("| $($workflow.Name) | Failed guardrail verification | $outputPath |")
            }
        } else {
            $summaryRows.Add("| $($workflow.Name) | Failed with exit code $exitCode | $outputPath |")
        }
    }
}
finally {
    Pop-Location
}

$draftPath = Join-Path $runRoot "runtime-validation-summary-draft.md"
$date = Get-Date -Format "yyyy-MM-dd HH:mm"

$draft = @"
## Runtime Validation Run - $date

Repository type: TODO sanitize repository type
Model setup: TODO record model setup
Continue surface: Continue CLI through npx @continuedev/cli
Config used: TODO confirm sanitized config path

Raw outputs were written to an ignored local folder:

$runRoot

Runtime context used:

$ContextPath

Do not commit raw outputs until they have been reviewed and sanitized.

$($summaryRows -join "`n")

### What Worked

- TODO summarize after reviewing raw outputs.

### Gaps

- TODO summarize after reviewing raw outputs.

### Follow-up

- TODO list prompt, rule, fixture, or documentation improvements.
"@

$draft | Set-Content -LiteralPath $draftPath

if ($AppendSummary) {
    Add-Content -LiteralPath $runtimeDoc -Value "`n$draft"
    Write-Host "Appended sanitized summary template to $runtimeDoc" -ForegroundColor Green
}

Write-Host "Runtime validation outputs written to $runRoot" -ForegroundColor Green
Write-Host "Review and sanitize $draftPath before committing runtime validation notes." -ForegroundColor Yellow
