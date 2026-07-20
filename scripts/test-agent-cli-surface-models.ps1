param(
    [string]$SurfaceName,
    [string]$SurfaceKey = "aider-cli",
    [string[]]$Models = @(),
    [string]$TargetRepo,
    [string]$OutputPath,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$AgentCommand,
    [string]$AgentArgumentsTemplate,
    [string]$WriteAgentArgumentsTemplate,
    [string]$ModelArgumentTemplate,
    [string]$AgentConfigPath,
    [string]$InstallHint,
    [int]$PreloadTimeoutSeconds = 900,
    [int]$TimeoutSeconds = 600,
    [switch]$IncludeWriteSmoke,
    [switch]$IncludeScopedEdit,
    [switch]$AllowNonGeneratedTarget,
    [switch]$UnloadAfterEach,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimePolicy = (& (Join-Path $PSScriptRoot "get-model-runtime-policy.ps1") | ConvertFrom-Json)
if ($runtimePolicy.residencyMode -eq "unload-after-run") { $UnloadAfterEach = $true }
$surfaceDefaultFound = $false
$agentCommandWasProvided = $PSBoundParameters.ContainsKey("AgentCommand")
$agentArgumentsTemplateWasProvided = $PSBoundParameters.ContainsKey("AgentArgumentsTemplate")
$requiresExplicitLiveOverrides = $false

$surfaceDefaultsPath = Join-Path $repoRoot "config/agent-cli-surface-defaults.json"
if (Test-Path -LiteralPath $surfaceDefaultsPath) {
    $surfaceDefaults = Get-Content -LiteralPath $surfaceDefaultsPath -Raw | ConvertFrom-Json
    $surfaceDefault = @($surfaceDefaults.surfaces | Where-Object { $_.surfaceKey -eq $SurfaceKey } | Select-Object -First 1)
    if ($surfaceDefault.Count -gt 0) {
        $surfaceDefaultFound = $true
        if ([string]::IsNullOrWhiteSpace($SurfaceName)) { $SurfaceName = $surfaceDefault[0].surfaceName }
        if ([string]::IsNullOrWhiteSpace($AgentCommand)) { $AgentCommand = $surfaceDefault[0].agentCommand }
        if ([string]::IsNullOrWhiteSpace($AgentArgumentsTemplate)) { $AgentArgumentsTemplate = $surfaceDefault[0].agentArgumentsTemplate }
        if ([string]::IsNullOrWhiteSpace($WriteAgentArgumentsTemplate)) { $WriteAgentArgumentsTemplate = $surfaceDefault[0].writeAgentArgumentsTemplate }
        if ([string]::IsNullOrWhiteSpace($ModelArgumentTemplate)) { $ModelArgumentTemplate = $surfaceDefault[0].modelArgumentTemplate }
        if ([string]::IsNullOrWhiteSpace($InstallHint)) { $InstallHint = $surfaceDefault[0].installHint }
        $requiresExplicitLiveOverrides = [bool]$surfaceDefault[0].requiresExplicitLiveOverrides
    }
}

if ([string]::IsNullOrWhiteSpace($SurfaceName)) { $SurfaceName = "Aider CLI" }
if ([string]::IsNullOrWhiteSpace($AgentCommand)) { $AgentCommand = "aider" }
if ([string]::IsNullOrWhiteSpace($AgentArgumentsTemplate)) { $AgentArgumentsTemplate = '--message "{Prompt}" --yes-always --no-auto-commits' }
if ([string]::IsNullOrWhiteSpace($ModelArgumentTemplate) -and -not $surfaceDefaultFound) { $ModelArgumentTemplate = '--model "ollama_chat/{Model}"' }
if ([string]::IsNullOrWhiteSpace($InstallHint)) { $InstallHint = "Install or configure the CLI, or pass -AgentCommand." }

if (-not $DryRun -and $requiresExplicitLiveOverrides -and (-not $agentCommandWasProvided -or -not $agentArgumentsTemplateWasProvided)) {
    throw "$SurfaceName live tests require explicit -AgentCommand and -AgentArgumentsTemplate values until its non-interactive command syntax is confirmed. Use -DryRun to validate the harness wiring."
}

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
        prompt = ""
        keep_alive = 0
        stream = $false
    } | ConvertTo-Json -Depth 10

    Invoke-RestMethod -Uri "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec $TimeoutSeconds | Out-Null
}

function Invoke-OllamaPreload {
    param([string]$Model)

    $running = Invoke-RestMethod -Uri "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/ps" -Method Get -TimeoutSec 30
    $otherResident = @($running.models | Where-Object { $_.name -ne $Model -and $_.model -ne $Model })
    if ($otherResident.Count -ge [int]$runtimePolicy.maxResidentModels) { throw "Runtime policy blocks loading ${Model}: $($otherResident.Count) other model(s) are resident." }
    if ($otherResident.Count -gt 0) { Write-Warning "Runtime policy warning: another model is resident before loading $Model." }
    $body = @{ model = $Model; prompt = ""; keep_alive = "$($runtimePolicy.preloadKeepAliveMinutes)m"; stream = $false } | ConvertTo-Json -Depth 10
    Invoke-RestMethod -Uri "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec $PreloadTimeoutSeconds | Out-Null
    $running = Invoke-RestMethod -Uri "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/ps" -Method Get -TimeoutSec 30
    if (@($running.models | Where-Object { $_.name -eq $Model -or $_.model -eq $Model }).Count -eq 0) {
        throw "Ollama did not report $Model as loaded after preflight."
    }
}

function Get-DefaultModels {
    $catalog = Join-Path $repoRoot "config/evidence-catalog.tsv"
    $models = [System.Collections.Generic.List[string]]::new()

    if (Test-Path -LiteralPath $catalog) {
        foreach ($row in @(Import-Csv -LiteralPath $catalog -Delimiter "`t")) {
            if ($row.schema_version -eq "2" -and $row.surface -match [regex]::Escape($SurfaceName) -and $row.model -and $row.model -ne "N/A") {
                $models.Add($row.model.Trim())
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

    $agentTemplate = if ($Phase -match "write" -and -not [string]::IsNullOrWhiteSpace($WriteAgentArgumentsTemplate)) {
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
    $resolvedCommand = Get-Command $AgentCommand -ErrorAction Stop
    $startInfo.FileName = $AgentCommand
    $startInfo.Arguments = $arguments
    if ($resolvedCommand.CommandType -eq "ExternalScript" -and $resolvedCommand.Source -match '\.ps1$') {
        $powerShell = Get-Command pwsh -ErrorAction SilentlyContinue
        if (-not $powerShell) { $powerShell = Get-Command powershell -ErrorAction Stop }
        $startInfo.FileName = $powerShell.Source
        $startInfo.Arguments = "-NoProfile -File `"$($resolvedCommand.Source)`" $arguments"
    }
    $startInfo.WorkingDirectory = $RunDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $kiloHome = $null
    if ($SurfaceKey -eq "kilo-code-cli") {
        # Kilo 7.x reads project config from .kilo/kilo.jsonc. An isolated profile
        # avoids a broken or stateful user-level Kilo directory affecting validation.
        $kiloHome = Join-Path ([System.IO.Path]::GetTempPath()) "local-engineering-agent-pack-kilo-$([guid]::NewGuid())"
        $kiloConfigHome = Join-Path $kiloHome ".config"
        $kiloDataHome = Join-Path $kiloHome ".data"
        $kiloAppDataHome = Join-Path $kiloHome ".appdata"
        $kiloLocalAppDataHome = Join-Path $kiloHome ".localappdata"
        New-Item -ItemType Directory -Force -Path $kiloConfigHome,$kiloDataHome,$kiloAppDataHome,$kiloLocalAppDataHome | Out-Null
        $startInfo.Environment["HOME"] = $kiloHome
        $startInfo.Environment["USERPROFILE"] = $kiloHome
        $startInfo.Environment["XDG_CONFIG_HOME"] = $kiloConfigHome
        $startInfo.Environment["XDG_DATA_HOME"] = $kiloDataHome
        $startInfo.Environment["APPDATA"] = $kiloAppDataHome
        $startInfo.Environment["LOCALAPPDATA"] = $kiloLocalAppDataHome
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    [void]$process.Start()

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    $completed = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $completed) {
        try { $process.Kill($true) } catch { }
    }

    $result = [pscustomobject]@{
        ExitCode = if ($completed) { $process.ExitCode } else { -1 }
        TimedOut = -not $completed
        Stdout = $stdoutTask.GetAwaiter().GetResult()
        Stderr = $stderrTask.GetAwaiter().GetResult()
        Command = "$AgentCommand $arguments"
    }
    if ($kiloHome) { Remove-Item -LiteralPath $kiloHome -Recurse -Force -ErrorAction SilentlyContinue }
    return $result
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

if (($IncludeWriteSmoke -or $IncludeScopedEdit) -and -not $AllowNonGeneratedTarget -and $TargetRepo -notmatch "runtime-validation-output[\\/]sample-repositories") {
    throw "Write and scoped-edit tests are allowed only for generated disposable samples unless -AllowNonGeneratedTarget is set."
}

$resolvedTarget = (Resolve-Path -LiteralPath $TargetRepo).Path
Initialize-DisposableGitBaseline -RunDirectory $resolvedTarget
if ($SurfaceKey -eq "kilo-code-cli" -and -not $DryRun) {
    if ([string]::IsNullOrWhiteSpace($AgentConfigPath)) { $AgentConfigPath = Join-Path (Join-Path $resolvedTarget ".kilo") "kilo.jsonc" }
    if (-not (Test-Path -LiteralPath $AgentConfigPath)) {
        throw "Kilo Code requires a generated local config for live tests: $AgentConfigPath. Run setup-agent-surface with -Surface kilo -Action Configure against this generated sample first."
    }
    $AgentConfigPath = (Resolve-Path -LiteralPath $AgentConfigPath).Path
}
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
if ($SurfaceKey -eq "kilo-code-cli" -and -not $DryRun) { Write-Host "[4/7] Kilo config: $AgentConfigPath" }

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null

$results = [System.Collections.Generic.List[object]]::new()
$readPrompt = @"
Use the available read-only repository context or tools to inspect the opened repository root. Do not modify files. Do not create files. Do not run package installation. Do not guess. Return only the actual top-level files and folders inspected, the project type, key source and test files inspected, risks or missing information, and a failure signal. If no repository context or tools are available, say TOOLS_UNAVAILABLE.
"@
if ($SurfaceKey -eq "opencode-cli") {
    $readPrompt = "Use repository tools to read README.md and pyproject.toml. Do not modify files. Return the exact two filenames you read. If either cannot be read, say TOOLS_UNAVAILABLE."
}

$writeLine = "$SurfaceName approved-write smoke test passed."
$writePrompt = @"
Use approved write mode for this disposable smoke test only. Modify the existing README.md by adding exactly this final line: $writeLine Do not modify any other files. Do not create new files. After editing, report the changed file and stop. Do not commit.
"@
$scopedPrompt = @"
Use approved write mode for this disposable Python sample only. Modify only app/settings.py and tests/test_main.py. Add a Settings validation_label field with the exact default value local-agent-validation, then update the existing test to assert that Settings().validation_label equals local-agent-validation. Do not modify any other files. Do not create files. Do not commit. Run the existing tests if practical, then report the changed files and stop.
"@

$index = 0
foreach ($model in $modelsToTest) {
    $index++
    Write-Host "[5/7] Testing model $index/$($modelsToTest.Count): $model"
    $readStatus = "not-run"
    $writeStatus = "not-run"
    $scopedEditStatus = "not-run"
    $failureSignals = [System.Collections.Generic.List[string]]::new()

    try {
        if (-not $DryRun) {
            Write-Host "[5/7] Preloading $model before starting the phase timer..."
            Invoke-OllamaPreload -Model $model
            $cleanBefore = Invoke-GitText -Arguments @("status", "--short")
            if ($cleanBefore) { $failureSignals.Add("TARGET_REPO_NOT_CLEAN") }
        }

        $readRun = Invoke-AgentCommand -Model $model -Prompt $readPrompt -Phase "read" -RunDirectory $resolvedTarget
        $readOutput = "$($readRun.Stdout)`n$($readRun.Stderr)"
        $readOk = ($readRun.ExitCode -eq 0 -and -not $readRun.TimedOut -and $readOutput -match "README\.md" -and $readOutput -match "pyproject\.toml")
        $readStatus = if ($readOk) { "read-only-context-validated" } else { "failed" }
        if (-not $readOk) {
            $failureSignals.Add("READ_VALIDATION_FAILED")
            $failureSignals.Add("READ_EXIT_$($readRun.ExitCode)")
            if ($readRun.TimedOut) { $failureSignals.Add("READ_TIMED_OUT") }
        }

        if (-not $DryRun) {
            $postReadStatus = Invoke-GitText -Arguments @("status", "--short")
            if ($postReadStatus) { $failureSignals.Add("UNEXPECTED_WRITE_DURING_READ") }
        }

        if ($IncludeWriteSmoke) {
            if ($DryRun) {
                $writeStatus = "write-smoke-validated"
            }
            else {
                $writeRun = Invoke-AgentCommand -Model $model -Prompt $writePrompt -Phase "write" -RunDirectory $resolvedTarget
                $diffNames = Invoke-GitText -Arguments @("diff", "--name-only")
                $changedFiles = @($diffNames -split "`r?`n" | Where-Object { $_ })
                $diffCheck = Invoke-GitText -Arguments @("diff", "--check")
                $readme = Get-Content -LiteralPath (Join-Path $resolvedTarget "README.md") -Raw
                $expectedLine = [regex]::Escape($writeLine)
                $writeOk = ($writeRun.ExitCode -eq 0 -and -not $writeRun.TimedOut -and $changedFiles.Count -eq 1 -and $changedFiles[0] -eq "README.md" -and -not $diffCheck -and $readme -match "$expectedLine`r?`n?$")
                $writeStatus = if ($writeOk) { "write-smoke-validated" } else { "failed" }
                if (-not $writeOk) {
                    $failureSignals.Add("WRITE_VALIDATION_FAILED")
                    $failureSignals.Add("WRITE_EXIT_$($writeRun.ExitCode)")
                    if ($writeRun.TimedOut) { $failureSignals.Add("WRITE_TIMED_OUT") }
                }

                Invoke-GitText -Arguments @("restore", "README.md") | Out-Null
            }
        }

        if ($IncludeScopedEdit) {
            $settingsPath = Join-Path $resolvedTarget "app/settings.py"
            $testPath = Join-Path $resolvedTarget "tests/test_main.py"
            if (-not (Test-Path -LiteralPath $settingsPath) -or -not (Test-Path -LiteralPath $testPath)) {
                $scopedEditStatus = "failed"
                $failureSignals.Add("SCOPED_EDIT_FIXTURE_UNSUPPORTED")
            }
            elseif ($DryRun) {
                $scopedEditStatus = "scoped-edit-validated"
            }
            else {
                $scopedRun = Invoke-AgentCommand -Model $model -Prompt $scopedPrompt -Phase "scoped-write" -RunDirectory $resolvedTarget
                $diffNames = Invoke-GitText -Arguments @("diff", "--name-only")
                $changedFiles = @($diffNames -split "`r?`n" | Where-Object { $_ } | Sort-Object)
                $diffCheck = Invoke-GitText -Arguments @("diff", "--check")
                $settings = Get-Content -LiteralPath $settingsPath -Raw
                $test = Get-Content -LiteralPath $testPath -Raw
                $scopedOk = ($scopedRun.ExitCode -eq 0 -and -not $scopedRun.TimedOut -and (@($changedFiles) -join "|") -eq "app/settings.py|tests/test_main.py" -and -not $diffCheck -and $settings -match "validation_label" -and $settings -match "local-agent-validation" -and $test -match "validation_label" -and $test -match "local-agent-validation")
                $scopedEditStatus = if ($scopedOk) { "scoped-edit-validated" } else { "failed" }
                if (-not $scopedOk) {
                    $failureSignals.Add("SCOPED_EDIT_VALIDATION_FAILED")
                    $failureSignals.Add("SCOPED_EDIT_EXIT_$($scopedRun.ExitCode)")
                    if ($scopedRun.TimedOut) { $failureSignals.Add("SCOPED_EDIT_TIMED_OUT") }
                }

                Invoke-GitText -Arguments @("restore", "app/settings.py", "tests/test_main.py") | Out-Null
            }
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
        ScopedEditStatus = $scopedEditStatus
        FailureSignals = @($failureSignals)
    })
}

$report = [pscustomobject]@{
    GeneratedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Surface = $SurfaceName
    SurfaceKey = $SurfaceKey
    Target = "generated-sample"
    IncludeWriteSmoke = [bool]$IncludeWriteSmoke
    IncludeScopedEdit = [bool]$IncludeScopedEdit
    UnloadAfterEach = [bool]$UnloadAfterEach
    DryRun = [bool]$DryRun
    Results = @($results)
    Notes = "Report is sanitized: target paths, raw prompts, stdout, stderr, and private endpoints are intentionally omitted."
}

Write-Host "[6/7] Writing sanitized report..."
$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

foreach ($result in $results) {
    Write-Host "$($result.Model): read=$($result.ReadStatus), write=$($result.WriteStatus), scoped-edit=$($result.ScopedEditStatus), failures=$($result.FailureSignals -join ',')"
}
Write-Host "[7/7] Report written to $OutputPath"
