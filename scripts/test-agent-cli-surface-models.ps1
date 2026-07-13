param(
    [string]$SurfaceName = "Aider CLI",
    [string]$SurfaceKey = "aider-cli",
    [string[]]$Models = @(),
    [string]$TargetRepo,
    [string]$OutputPath,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$AgentCommand = "aider",
    [string]$AgentArgumentsTemplate = '--message "{Prompt}" --yes-always --no-auto-commits',
    [string]$WriteAgentArgumentsTemplate,
    [string]$ModelArgumentTemplate = '--model "ollama_chat/{Model}"',
    [string]$InstallHint = "Install or configure the CLI, or pass -AgentCommand.",
    [int]$TimeoutSeconds = 600,
    [switch]$IncludeWriteSmoke,
    [switch]$AllowNonGeneratedTarget,
    [switch]$UnloadAfterEach,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $TargetRepo) {
    $TargetRepo = Join-Path $repoRoot "runtime-validation-output/sample-repositories/python-api"
}

if (-not $OutputPath) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/$SurfaceKey-model-tests-$timestamp.json"
}

function ConvertTo-SafeBaseUrl {
    param([string]$BaseUrl)
    return $BaseUrl.TrimEnd("/")
}

function Invoke-OllamaUnload {
    param([string]$Model)

    $body = @{
        model = $Model
        messages = @()
        keep_alive = 0
        stream = $false
    } | ConvertTo-Json -Depth 10

    Invoke-RestMethod -Uri "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/chat" -Method Post -Body $body -ContentType "application/json" -TimeoutSec $TimeoutSeconds | Out-Null
}

function Get-DefaultModels {
    $catalog = Join-Path $repoRoot "config/evidence-catalog.tsv"
    $models = [System.Collections.Generic.List[string]]::new()

    if (Test-Path -LiteralPath $catalog) {
        $lines = Get-Content -LiteralPath $catalog
        foreach ($line in $lines | Select-Object -Skip 1) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $parts = $line -split "`t"
            if ($parts.Count -lt 6) { continue }
            $surface = $parts[2]
            $model = $parts[4]
            if ($surface -match [regex]::Escape($SurfaceName) -and $model -and $model -ne "N/A") {
                $models.Add($model.Trim())
            }
        }
    }

    if ($models.Count -eq 0) {
        $models.Add("qwen3.5:9b")
    }

    return $models | Select-Object -Unique
}

function ConvertTo-ArgumentText {
    param(
        [string]$Template,
        [string]$Prompt,
        [string]$Model,
        [string]$PromptFile,
        [string]$TargetRepo,
        [string]$OllamaBaseUrl,
        [string]$TempDir
    )

    $safePrompt = ($Prompt -replace "`r?`n", " ").Replace('"', "'")
    return $Template.Replace("{Prompt}", $safePrompt).Replace("{Model}", $Model).Replace("{PromptFile}", $PromptFile).Replace("{TargetRepo}", $TargetRepo).Replace("{OllamaBaseUrl}", $OllamaBaseUrl).Replace("{TempDir}", $TempDir)
}

function Invoke-AgentCommand {
    param(
        [string]$Model,
        [string]$Prompt,
        [string]$Phase,
        [string]$RunDirectory
    )

    $promptFile = Join-Path ([System.IO.Path]::GetTempPath()) "$SurfaceKey-$Phase-$([guid]::NewGuid()).txt"
    Set-Content -LiteralPath $promptFile -Value $Prompt -Encoding UTF8
    $tempDir = [System.IO.Path]::GetTempPath().TrimEnd("\", "/")

    $agentTemplate = if ($Phase -eq "write" -and -not [string]::IsNullOrWhiteSpace($WriteAgentArgumentsTemplate)) {
        $WriteAgentArgumentsTemplate
    } else {
        $AgentArgumentsTemplate
    }

    $arguments = ConvertTo-ArgumentText -Template $agentTemplate -Prompt $Prompt -Model $Model -PromptFile $promptFile -TargetRepo $RunDirectory -OllamaBaseUrl $OllamaBaseUrl -TempDir $tempDir
    if (-not [string]::IsNullOrWhiteSpace($ModelArgumentTemplate)) {
        $modelArguments = ConvertTo-ArgumentText -Template $ModelArgumentTemplate -Prompt $Prompt -Model $Model -PromptFile $promptFile -TargetRepo $RunDirectory -OllamaBaseUrl $OllamaBaseUrl -TempDir $tempDir
        $arguments = "$modelArguments $arguments"
    }

    if ($DryRun) {
        return [pscustomobject]@{
            ExitCode = 0
            TimedOut = $false
            Stdout = "DRY_RUN README.md pyproject.toml app/main.py"
            Stderr = ""
            Command = "$AgentCommand $arguments"
        }
    }

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $AgentCommand
    $startInfo.Arguments = $arguments
    $startInfo.WorkingDirectory = $RunDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    [void]$process.Start()

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    $completed = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $completed) {
        try { $process.Kill($true) } catch { }
    }

    return [pscustomobject]@{
        ExitCode = if ($completed) { $process.ExitCode } else { -1 }
        TimedOut = -not $completed
        Stdout = $stdoutTask.GetAwaiter().GetResult()
        Stderr = $stderrTask.GetAwaiter().GetResult()
        Command = "$AgentCommand $arguments"
    }
}

function Invoke-GitText {
    param([string[]]$Arguments)
    $output = & git -C $TargetRepo @Arguments
    return ($output | Out-String).Trim()
}

function Initialize-DisposableGitBaseline {
    param([string]$RunDirectory)

    if ($RunDirectory -notmatch "runtime-validation-output[\\/]sample-repositories") {
        return
    }

    if (-not (Test-Path -LiteralPath (Join-Path $RunDirectory ".git"))) {
        & git -C $RunDirectory init | Out-Null
    }

    & git -C $RunDirectory config core.autocrlf false | Out-Null
    & git -C $RunDirectory config core.eol lf | Out-Null

    & git -C $RunDirectory rev-parse --verify HEAD *> $null
    if ($LASTEXITCODE -ne 0) {
        & git -C $RunDirectory add . | Out-Null
        & git -C $RunDirectory -c user.name="Local Agent Validation" -c user.email="local-agent-validation@example.invalid" commit -m "Initial generated sample" | Out-Null
        return
    }

    $dirty = (& git -C $RunDirectory status --short 2>$null | Out-String).Trim()
    if ($dirty) {
        & git -C $RunDirectory restore . | Out-Null
        & git -C $RunDirectory clean -fd | Out-Null
    }
}

Write-Host "[1/7] Preparing $SurfaceName model test run..."

if (-not (Test-Path -LiteralPath $TargetRepo)) {
    $generator = Join-Path $repoRoot "scripts/generate-sample-repositories.ps1"
    if (Test-Path -LiteralPath $generator) {
        Write-Host "[2/7] Target sample missing; generating disposable sample repositories..."
        & $generator -Force | Out-Null
    }
}

if (-not (Test-Path -LiteralPath $TargetRepo)) {
    throw "TargetRepo does not exist: $TargetRepo"
}

if ($IncludeWriteSmoke -and -not $AllowNonGeneratedTarget -and $TargetRepo -notmatch "runtime-validation-output[\\/]sample-repositories") {
    throw "Write smoke tests are allowed only for generated disposable samples unless -AllowNonGeneratedTarget is set."
}

$resolvedTarget = (Resolve-Path -LiteralPath $TargetRepo).Path
Initialize-DisposableGitBaseline -RunDirectory $resolvedTarget
$modelsToTest = @($Models | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim() })
if ($modelsToTest.Count -eq 0) {
    $modelsToTest = @(Get-DefaultModels)
}

if (-not $DryRun -and -not (Get-Command $AgentCommand -ErrorAction SilentlyContinue)) {
    throw "$SurfaceName command was not found: $AgentCommand. $InstallHint"
}

Write-Host "[2/7] Target repository: generated sample $((Split-Path -Leaf $resolvedTarget))"
Write-Host "[3/7] Candidate models: $($modelsToTest -join ', ')"
Write-Host "[4/7] Agent command: $AgentCommand"

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null

$results = [System.Collections.Generic.List[object]]::new()
$readPrompt = @"
Use the available read-only repository context or tools to inspect the opened repository root. Do not modify files. Do not create files. Do not run package installation. Do not guess. Return only the actual top-level files and folders inspected, the project type, key source and test files inspected, risks or missing information, and a failure signal. If no repository context or tools are available, say TOOLS_UNAVAILABLE.
"@

$writeLine = "$SurfaceName approved-write smoke test passed."
$writePrompt = @"
Use approved write mode for this disposable smoke test only. Modify the existing README.md by adding exactly this final line: $writeLine Do not modify any other files. Do not create new files. After editing, report the changed file and stop. Do not commit.
"@

$index = 0
foreach ($model in $modelsToTest) {
    $index++
    Write-Host "[5/7] Testing model $index/$($modelsToTest.Count): $model"
    $readStatus = "not-run"
    $writeStatus = "not-run"
    $failureSignals = [System.Collections.Generic.List[string]]::new()

    try {
        if (-not $DryRun) {
            $cleanBefore = Invoke-GitText -Arguments @("status", "--short")
            if ($cleanBefore) { $failureSignals.Add("TARGET_REPO_NOT_CLEAN") }
        }

        $readRun = Invoke-AgentCommand -Model $model -Prompt $readPrompt -Phase "read" -RunDirectory $resolvedTarget
        $readOk = ($readRun.ExitCode -eq 0 -and -not $readRun.TimedOut -and $readRun.Stdout -match "README\.md" -and $readRun.Stdout -match "pyproject\.toml")
        $readStatus = if ($readOk) { "read-only-context-validated" } else { "failed" }
        if (-not $readOk) { $failureSignals.Add("READ_VALIDATION_FAILED") }

        if (-not $DryRun) {
            $postReadStatus = Invoke-GitText -Arguments @("status", "--short")
            if ($postReadStatus) { $failureSignals.Add("UNEXPECTED_WRITE_DURING_READ") }
        }

        if ($IncludeWriteSmoke) {
            $writeRun = Invoke-AgentCommand -Model $model -Prompt $writePrompt -Phase "write" -RunDirectory $resolvedTarget
            $diffNames = Invoke-GitText -Arguments @("diff", "--name-only")
            $changedFiles = @($diffNames -split "`r?`n" | Where-Object { $_ })
            $diffCheck = Invoke-GitText -Arguments @("diff", "--check")
            $readme = Get-Content -LiteralPath (Join-Path $resolvedTarget "README.md") -Raw
            $expectedLine = [regex]::Escape($writeLine)
            $writeOk = ($writeRun.ExitCode -eq 0 -and -not $writeRun.TimedOut -and $changedFiles.Count -eq 1 -and $changedFiles[0] -eq "README.md" -and -not $diffCheck -and $readme -match "$expectedLine`r?`n?$")
            $writeStatus = if ($writeOk) { "write-smoke-validated" } else { "failed" }
            if (-not $writeOk) { $failureSignals.Add("WRITE_VALIDATION_FAILED") }

            Invoke-GitText -Arguments @("restore", "README.md") | Out-Null
        }
    }
    catch {
        $failureSignals.Add("SCRIPT_EXCEPTION")
        $failureSignals.Add(($_.Exception.Message -replace "`r?`n", " "))
    }

    if ($UnloadAfterEach -and -not $DryRun) {
        try {
            Write-Host "[6/7] Unloading $model from Ollama..."
            Invoke-OllamaUnload -Model $model
        }
        catch { $failureSignals.Add("UNLOAD_FAILED") }
    }
    if ($failureSignals.Count -eq 0) { $failureSignals.Add("none") }

    $results.Add([pscustomobject]@{
        Model = $model
        Surface = $SurfaceName
        Target = "generated-sample"
        ReadStatus = $readStatus
        WriteStatus = $writeStatus
        FailureSignals = @($failureSignals)
    })
}

$report = [pscustomobject]@{
    GeneratedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Surface = $SurfaceName
    SurfaceKey = $SurfaceKey
    Target = "generated-sample"
    IncludeWriteSmoke = [bool]$IncludeWriteSmoke
    UnloadAfterEach = [bool]$UnloadAfterEach
    DryRun = [bool]$DryRun
    Results = @($results)
    Notes = "Report is sanitized: target paths, raw prompts, stdout, stderr, and private endpoints are intentionally omitted."
}

Write-Host "[6/7] Writing sanitized report..."
$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

foreach ($result in $results) {
    Write-Host "$($result.Model): read=$($result.ReadStatus), write=$($result.WriteStatus), failures=$($result.FailureSignals -join ',')"
}
Write-Host "[7/7] Report written to $OutputPath"
