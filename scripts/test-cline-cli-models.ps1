param(
    [string[]]$Models = @(),
    [string]$TargetRepo,
    [string]$OutputPath,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$ClineCommand = "cline",
    [string]$ClineArgumentsTemplate = '--json "{Prompt}"',
    [string]$ModelArgumentTemplate = "",
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
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/cline-cli-model-tests-$timestamp.json"
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
        foreach ($row in @(Import-Csv -LiteralPath $catalog -Delimiter "`t")) {
            if ($row.schema_version -eq "2" -and $row.surface -match "(?i)Cline" -and $row.model -and $row.model -ne "N/A") {
                $models.Add($row.model.Trim())
            }
        }
    }

    if ($models.Count -eq 0) {
        $models.Add("qwen3-coder:30b")
    }

    return $models | Select-Object -Unique
}

function ConvertTo-ArgumentText {
    param(
        [string]$Template,
        [string]$Prompt,
        [string]$Model,
        [string]$PromptFile,
        [string]$TargetRepo
    )

    $safePrompt = ($Prompt -replace "`r?`n", " ").Replace('"', "'")
    return $Template.Replace("{Prompt}", $safePrompt).Replace("{Model}", $Model).Replace("{PromptFile}", $PromptFile).Replace("{TargetRepo}", $TargetRepo)
}

function Invoke-ClineCommand {
    param(
        [string]$Model,
        [string]$Prompt,
        [string]$Phase,
        [string]$RunDirectory
    )

    $promptFile = Join-Path ([System.IO.Path]::GetTempPath()) "cline-$Phase-$([guid]::NewGuid()).txt"
    Set-Content -LiteralPath $promptFile -Value $Prompt -Encoding UTF8

    $arguments = ConvertTo-ArgumentText -Template $ClineArgumentsTemplate -Prompt $Prompt -Model $Model -PromptFile $promptFile -TargetRepo $RunDirectory
    if (-not [string]::IsNullOrWhiteSpace($ModelArgumentTemplate)) {
        $modelArguments = ConvertTo-ArgumentText -Template $ModelArgumentTemplate -Prompt $Prompt -Model $Model -PromptFile $promptFile -TargetRepo $RunDirectory
        $arguments = "$modelArguments $arguments"
    }

    $stdoutPath = Join-Path ([System.IO.Path]::GetTempPath()) "cline-$Phase-$([guid]::NewGuid()).out"
    $stderrPath = Join-Path ([System.IO.Path]::GetTempPath()) "cline-$Phase-$([guid]::NewGuid()).err"

    if ($DryRun) {
        return [pscustomobject]@{
            ExitCode = 0
            TimedOut = $false
            Stdout = "DRY_RUN README.md pyproject.toml app/main.py"
            Stderr = ""
            Command = "$ClineCommand $arguments"
        }
    }

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $ClineCommand
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

    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    Set-Content -LiteralPath $stdoutPath -Value $stdout -Encoding UTF8
    Set-Content -LiteralPath $stderrPath -Value $stderr -Encoding UTF8

    return [pscustomobject]@{
        ExitCode = if ($completed) { $process.ExitCode } else { -1 }
        TimedOut = -not $completed
        Stdout = $stdout
        Stderr = $stderr
        Command = "$ClineCommand $arguments"
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

Write-Host "[1/7] Preparing Cline CLI model test run..."

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

if (-not $DryRun -and -not (Get-Command $ClineCommand -ErrorAction SilentlyContinue)) {
    throw "Cline command was not found: $ClineCommand. Install with npm i -g cline or pass -ClineCommand."
}

Write-Host "[2/7] Target repository: generated sample $((Split-Path -Leaf $resolvedTarget))"
Write-Host "[3/7] Candidate models: $($modelsToTest -join ', ')"
Write-Host "[4/7] Cline command: $ClineCommand"

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null

$results = [System.Collections.Generic.List[object]]::new()
$readPrompt = @"
Use tools to inspect the opened repository root. Do not modify files. Do not create files. Do not run package installation. Do not guess. Return only the actual top-level files and folders inspected, the project type, key source and test files inspected, risks or missing information, and a failure signal. If tools are unavailable, say TOOLS_UNAVAILABLE.
"@

$writePrompt = @"
Use approved write mode for this disposable smoke test only. Modify the existing README.md by adding exactly this final line: Cline CLI approved-write smoke test passed. Do not modify any other files. Do not create new files. After editing, report the changed file and stop. Do not commit.
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
            if ($cleanBefore) {
                $failureSignals.Add("TARGET_REPO_NOT_CLEAN")
            }
        }

        $readRun = Invoke-ClineCommand -Model $model -Prompt $readPrompt -Phase "read" -RunDirectory $resolvedTarget
        $readOk = ($readRun.ExitCode -eq 0 -and -not $readRun.TimedOut -and $readRun.Stdout -match "README\.md" -and $readRun.Stdout -match "pyproject\.toml")
        $readStatus = if ($readOk) { "read-only-tool-validated" } else { "failed" }
        if (-not $readOk) { $failureSignals.Add("READ_VALIDATION_FAILED") }

        if (-not $DryRun) {
            $postReadStatus = Invoke-GitText -Arguments @("status", "--short")
            if ($postReadStatus) {
                $failureSignals.Add("UNEXPECTED_WRITE_DURING_READ")
            }
        }

        if ($IncludeWriteSmoke) {
            $writeRun = Invoke-ClineCommand -Model $model -Prompt $writePrompt -Phase "write" -RunDirectory $resolvedTarget
            $diffNames = Invoke-GitText -Arguments @("diff", "--name-only")
            $changedFiles = @($diffNames -split "`r?`n" | Where-Object { $_ })
            $diffCheck = Invoke-GitText -Arguments @("diff", "--check")
            $readme = Get-Content -LiteralPath (Join-Path $resolvedTarget "README.md") -Raw
            $writeOk = ($writeRun.ExitCode -eq 0 -and -not $writeRun.TimedOut -and $changedFiles.Count -eq 1 -and $changedFiles[0] -eq "README.md" -and -not $diffCheck -and $readme -match "Cline CLI approved-write smoke test passed\.`r?`n?$")
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
        catch {
            $failureSignals.Add("UNLOAD_FAILED")
        }
    }
    if ($failureSignals.Count -eq 0) { $failureSignals.Add("none") }

    $results.Add([pscustomobject]@{
        Model = $model
        Surface = "Cline CLI"
        Target = "generated-sample"
        ReadStatus = $readStatus
        WriteStatus = $writeStatus
        FailureSignals = @($failureSignals)
    })
}

$report = [pscustomobject]@{
    GeneratedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Surface = "Cline CLI"
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
