param(
    [string]$MatrixPath,
    [string]$ReadConfigPath,
    [string]$WriteConfigPath,
    [string[]]$Ecosystems = @(),
    [string[]]$Operations = @(),
    [string]$OutputPath,
    [string]$ContinueCommand = "npx",
    [int]$LoadTimeoutSeconds = 900,
    [int]$TimeoutSeconds = 900,
    [switch]$UnloadAfterRun,
    [switch]$AllowLoadedModels,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $PSScriptRoot "CommandResolution.psm1") -Force
$runtimePolicy = (& (Join-Path $PSScriptRoot "get-model-runtime-policy.ps1") | ConvertFrom-Json)
if ($runtimePolicy.residencyMode -eq "unload-after-run") { $UnloadAfterRun = $true } else { $AllowLoadedModels = $true }
$sampleRoot = Join-Path $repoRoot "runtime-validation-output/sample-repositories"
$resolvedContinueCommand = $ContinueCommand

if (-not $MatrixPath) { $MatrixPath = Join-Path $repoRoot "config/language-workflow-validation-matrix.json" }
if (-not $ReadConfigPath) { $ReadConfigPath = Join-Path $repoRoot ".continue/config.local.yaml" }
if (-not $WriteConfigPath) { $WriteConfigPath = $ReadConfigPath }
if (-not $OutputPath) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/language-workflow-matrix-$timestamp.json"
}

function Get-ConfigValue {
    param([string]$Path, [string]$Key)

    $match = Select-String -LiteralPath $Path -Pattern "^\s*$([regex]::Escape($Key)):\s*(\S+)" | Select-Object -First 1
    if ($match) { return $match.Matches[0].Groups[1].Value.Trim().Trim('"', "'") }
    return $null
}

function Initialize-SampleBaseline {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath (Join-Path $Path ".git"))) {
        & git -C $Path init | Out-Null
        & git -C $Path config core.autocrlf false | Out-Null
        & git -C $Path config core.eol lf | Out-Null
        & git -C $Path add . | Out-Null
        & git -C $Path -c user.name="Local Agent Validation" -c user.email="local-agent-validation@example.invalid" commit -m "Initial generated sample" | Out-Null
        return
    }

    $dirty = (& git -C $Path status --short 2>$null | Out-String).Trim()
    if ($dirty) {
        & git -C $Path restore . | Out-Null
        & git -C $Path clean -fd | Out-Null
    }
}

function Get-OperationPrompt {
    param([object]$Entry, [string]$Operation)

    $files = @($Entry.operationEvidence.$Operation)
    $fileText = $files -join ", "
    switch ($Operation) {
        "repository-discovery" {
            return "Inspect this repository in read-only mode for the $($Entry.ecosystem) component. Do not modify or create files. Use the available read tools to open every named evidence file before writing the answer. If a read tool cannot open every named file, respond exactly TOOLS_UNAVAILABLE and stop. Do not treat a filename as evidence that its contents were read. Begin the final answer with 'Evidence files inspected:' and list each of these exact repository paths on its own bullet before the analysis: $fileText. Then identify the project structure, architecture, source, tests, configuration, risks, and next steps. Copy paths exactly; do not invent or shorten filenames."
        }
        "implementation-plan" {
            return "Create a read-only implementation plan for the scenario in SCENARIO.md, scoped to the $($Entry.ecosystem) component. Do not modify or create files. Use the available read tools to open every named evidence file before writing the plan. If a read tool cannot open every named file, respond exactly TOOLS_UNAVAILABLE and stop. Do not treat a filename as evidence that its contents were read. Begin the final answer with 'Evidence files inspected:' and list each of these exact repository paths on its own bullet before the plan: $fileText. Include affected components, ordered steps, tests, risks, and rollback. Copy paths exactly; do not invent or shorten filenames."
        }
        "code-review" {
            return "Review the $($Entry.ecosystem) component in read-only mode. Do not modify or create files. Use the available read tools to open every named evidence file before writing findings. If a read tool cannot open every named file, respond exactly TOOLS_UNAVAILABLE and stop. Do not treat a filename as evidence that its contents were read. Begin the final answer with 'Evidence files inspected:' and list each of these exact repository paths on its own bullet before the findings: $fileText. Then lead with correctness, security, regression, maintainability, and missing-test findings. Copy paths exactly; do not invent or shorten filenames."
        }
        "scoped-write" {
            $target = $Entry.operationEvidence.'scoped-write'.targetFile
            $marker = $Entry.operationEvidence.'scoped-write'.marker
            return "Use approved write mode for this disposable validation fixture. Modify only the existing file $target. Add one new line if needed. Append exactly this one final line, with no other text on that line:`n$marker`nDo not modify or create any other file. Do not reformat existing content. Before responding, read the target and verify that its final line exactly matches the marker above. Then respond exactly: Changed file: $target Do not commit."
        }
        default { throw "Unsupported operation: $Operation" }
    }
}

function Invoke-Continue {
    param(
        [string]$ConfigPath,
        [string]$WorkingDirectory,
        [string]$Prompt,
        [bool]$ReadOnly
    )

    if ($DryRun) {
        return [pscustomobject]@{ ExitCode = 0; TimedOut = $false; Stdout = "DRY_RUN $Prompt"; Stderr = "" }
    }

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $resolvedContinueCommand
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $arguments = if ($ContinueCommand -eq "npx") {
        @("-y", "@continuedev/cli@1.5.47")
    }
    else {
        @()
    }
    $arguments += @("--config", $ConfigPath, $(if ($ReadOnly) { "--readonly" } else { "--auto" }), "--format", "json", "--silent", "-p", $Prompt)
    foreach ($argument in $continueCommandPrefixArguments + $arguments) {
        [void]$startInfo.ArgumentList.Add($argument)
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

    return [pscustomobject]@{
        ExitCode = if ($completed) { $process.ExitCode } else { -1 }
        TimedOut = -not $completed
        Stdout = $stdoutTask.GetAwaiter().GetResult()
        Stderr = $stderrTask.GetAwaiter().GetResult()
    }
}

function Invoke-OllamaUnload {
    param([string]$BaseUrl, [string]$Model)

    if (-not $BaseUrl -or -not $Model -or $DryRun) { return $true }
    $body = @{ model = $Model; prompt = ""; keep_alive = 0; stream = $false } | ConvertTo-Json -Depth 5
    $base = $BaseUrl.TrimEnd('/')
    foreach ($attempt in 1..3) {
        Invoke-RestMethod -Uri "$base/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 60 | Out-Null
        Start-Sleep -Seconds 2
        $models = @(Invoke-RestMethod -Uri "$base/api/ps" -Method Get -TimeoutSec 15).models
        if (-not @($models | Where-Object { $_.name -eq $Model -or $_.model -eq $Model })) { return $true }
    }
    return $false
}

function Invoke-OllamaPreload {
    param([string]$BaseUrl, [string]$Model)

    $base = $BaseUrl.TrimEnd('/')
    $models = @((Invoke-RestMethod -Uri "$base/api/ps" -Method Get -TimeoutSec 30).models)
    $otherResident = @($models | Where-Object { $_.name -ne $Model -and $_.model -ne $Model })
    if ($otherResident.Count -ge [int]$runtimePolicy.maxResidentModels) { throw "Runtime policy blocks loading ${Model}: $($otherResident.Count) other model(s) are resident." }
    if ($otherResident.Count -gt 0) { Write-Warning "Runtime policy warning: another model is resident before loading $Model." }
    $body = @{ model = $Model; prompt = ""; keep_alive = "$($runtimePolicy.preloadKeepAliveMinutes)m"; stream = $false } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec $LoadTimeoutSeconds | Out-Null
    $models = @((Invoke-RestMethod -Uri "$base/api/ps" -Method Get -TimeoutSec 30).models)
    if (@($models | Where-Object { $_.name -eq $Model -or $_.model -eq $Model }).Count -eq 0) { throw "Ollama did not report $Model as loaded after preflight." }
}

function Invoke-TestedModelUnload {
    if (-not $UnloadAfterRun) { return }

    Write-Host "[7/8] Unloading tested models..."
    $pairs = @(
        [pscustomobject]@{ BaseUrl = $readBaseUrl; Model = $readModel },
        [pscustomobject]@{ BaseUrl = $writeBaseUrl; Model = $writeModel }
    ) | Sort-Object BaseUrl, Model -Unique
    foreach ($pair in $pairs) {
        try {
            if (Invoke-OllamaUnload -BaseUrl $pair.BaseUrl -Model $pair.Model) {
                Write-Host "[7/8] Unloaded $($pair.Model)."
            }
            else {
                Write-Warning "Model $($pair.Model) is still loaded after three unload attempts."
            }
        }
        catch { Write-Warning "Could not unload $($pair.Model): $($_.Exception.Message)" }
    }
}

function ConvertTo-SanitizedOutput {
    param([string]$Text, [string]$SamplePath)

    $sanitized = $Text
    foreach ($privateValue in @($repoRoot, $SamplePath, $readBaseUrl, $writeBaseUrl) | Where-Object { $_ }) {
        $sanitized = $sanitized -replace [regex]::Escape($privateValue), "<local-value>"
    }
    $sanitized = $sanitized -replace '(?i)https?://[^\s)\]}>]+', '<endpoint>'
    $sanitized = $sanitized -replace '(?i)[A-Z]:\\Users\\[^\\\s]+', '<user-home>'
    if ($sanitized.Length -gt 6000) { $sanitized = $sanitized.Substring(0, 6000) + "`n[truncated]" }
    return $sanitized.Trim()
}

Write-Host "[1/8] Validating matrix, configs, and Continue CLI..."
foreach ($path in @($MatrixPath, $ReadConfigPath, $WriteConfigPath)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Required path does not exist: $path" }
}
if (-not $DryRun -and -not (Get-Command $ContinueCommand -ErrorAction SilentlyContinue)) {
    throw "Continue CLI command was not found: $ContinueCommand"
}
if (-not $DryRun) {
    $continueCommandResolution = Resolve-ExternalCommand -Command $ContinueCommand
    $resolvedContinueCommand = $continueCommandResolution.FilePath
    $continueCommandPrefixArguments = @($continueCommandResolution.PrefixArguments)
}

$surfaceVersion = if ($DryRun) {
    "dry-run"
}
else {
    if ($ContinueCommand -eq "npx") {
        ((& $resolvedContinueCommand @continueCommandPrefixArguments -y @continuedev/cli@1.5.47 --version 2>$null | Out-String).Trim())
    }
    else {
        ((& $resolvedContinueCommand @continueCommandPrefixArguments --version 2>$null | Out-String).Trim())
    }
}
if (-not $surfaceVersion) { $surfaceVersion = "unconfirmed" }

$matrix = Get-Content -LiteralPath $MatrixPath -Raw | ConvertFrom-Json
$selectedOperations = if ($Operations.Count -gt 0) { @($Operations) } else { @($matrix.requiredOperations) }
$unsupported = @($selectedOperations | Where-Object { $_ -notin @($matrix.requiredOperations) })
if ($unsupported.Count -gt 0) { throw "Unsupported operations: $($unsupported -join ', ')" }

$entries = @($matrix.entries)
if ($Ecosystems.Count -gt 0) { $entries = @($entries | Where-Object { $_.ecosystem -in $Ecosystems }) }
if ($entries.Count -eq 0) { throw "No matrix entries matched the requested ecosystems." }

$readConfig = (Resolve-Path -LiteralPath $ReadConfigPath).Path
$writeConfig = (Resolve-Path -LiteralPath $WriteConfigPath).Path
$readModel = Get-ConfigValue -Path $readConfig -Key "model"
$writeModel = Get-ConfigValue -Path $writeConfig -Key "model"
$readBaseUrl = Get-ConfigValue -Path $readConfig -Key "apiBase"
$writeBaseUrl = Get-ConfigValue -Path $writeConfig -Key "apiBase"

# A portable Continue config intentionally omits apiBase. Ollama uses this
# local default when no endpoint override is configured.
if ([string]::IsNullOrWhiteSpace($readBaseUrl)) { $readBaseUrl = "http://127.0.0.1:11434" }
if ([string]::IsNullOrWhiteSpace($writeBaseUrl)) { $writeBaseUrl = $readBaseUrl }

if (-not $DryRun) {
    foreach ($baseUrl in @($readBaseUrl, $writeBaseUrl) | Select-Object -Unique) {
        Invoke-RestMethod -Uri "$($baseUrl.TrimEnd('/'))/api/version" -TimeoutSec 15 | Out-Null
    }
    if (-not $AllowLoadedModels) {
        foreach ($baseUrl in @($readBaseUrl, $writeBaseUrl) | Select-Object -Unique) {
            $loadedModels = @((Invoke-RestMethod -Uri "$($baseUrl.TrimEnd('/'))/api/ps" -TimeoutSec 15).models |
                ForEach-Object { if ($_.name) { $_.name } else { $_.model } } |
                Where-Object { $_ })
            if ($loadedModels.Count -gt 0) {
                throw "Refusing to start: Ollama already has loaded model(s): $($loadedModels -join ', '). Unload them first, or explicitly use -AllowLoadedModels."
            }
        }
    }
}

Write-Host "[2/8] Generating clean medium-complexity fixtures..."
& (Join-Path $repoRoot "scripts/generate-sample-repositories.ps1") -Force | Out-Null
foreach ($sample in @($entries.sample | Select-Object -Unique)) {
    Initialize-SampleBaseline -Path (Join-Path $sampleRoot $sample)
}

$runRoot = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$rawRoot = Join-Path $runRoot ("language-workflow-matrix-raw-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $rawRoot | Out-Null

Write-Host "[3/8] Read model: $readModel"
Write-Host "[3/8] Write model: $writeModel"
Write-Host "[4/8] Operations: $($selectedOperations -join ', ')"

$results = [System.Collections.Generic.List[object]]::new()
$total = $entries.Count * $selectedOperations.Count
$index = 0

try {
    foreach ($entry in $entries) {
        $samplePath = Join-Path $sampleRoot $entry.sample
        foreach ($operation in $selectedOperations) {
        $index++
        Write-Host "[5/8] Running $index/$total`: $($entry.ecosystem) / $operation"
        Initialize-SampleBaseline -Path $samplePath
        $isWrite = $operation -eq "scoped-write"
        $config = if ($isWrite) { $writeConfig } else { $readConfig }
        $model = if ($isWrite) { $writeModel } else { $readModel }
        $prompt = Get-OperationPrompt -Entry $entry -Operation $operation
        if (-not $DryRun) {
            Write-Host "[5/8] Preloading $model before starting the cell timer..."
            Invoke-OllamaPreload -BaseUrl $(if ($isWrite) { $writeBaseUrl } else { $readBaseUrl }) -Model $model
        }
        $cellStarted = Get-Date
        $run = Invoke-Continue -ConfigPath $config -WorkingDirectory $samplePath -Prompt $prompt -ReadOnly (-not $isWrite)

        $safeName = "$($entry.ecosystem)-$operation" -replace "[^a-zA-Z0-9._-]", "-"
        Set-Content -LiteralPath (Join-Path $rawRoot "$safeName.stdout.txt") -Value $run.Stdout -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $rawRoot "$safeName.stderr.txt") -Value $run.Stderr -Encoding UTF8

        $signals = [System.Collections.Generic.List[string]]::new()
        if ($run.TimedOut) { $signals.Add("TIMEOUT") }
        if ($run.ExitCode -ne 0) { $signals.Add("CLI_EXIT_$($run.ExitCode)") }
        if ([string]::IsNullOrWhiteSpace($run.Stdout)) { $signals.Add("EMPTY_OUTPUT") }
        if ($run.Stdout -match '(?i)TOOLS_UNAVAILABLE|WRITE_NOT_APPLIED|RAW_TOOL_CALL_OUTPUT') { $signals.Add("MODEL_FAILURE_SIGNAL") }
        if ($run.Stdout.Trim() -match '^<function=|^\{\s*"name"\s*:') { $signals.Add("RAW_TOOL_CALL_ONLY") }

        $externalDiff = "not-applicable"
        if ($isWrite) {
            $target = $entry.operationEvidence.'scoped-write'.targetFile
            $marker = $entry.operationEvidence.'scoped-write'.marker
            if ($DryRun) {
                $externalDiff = "dry-run"
            }
            else {
                $writeVerificationFailed = $false
                $changed = @((& git -C $samplePath diff --name-only) | Where-Object { $_ })
                $diffCheck = (& git -C $samplePath diff --check 2>&1 | Out-String).Trim()
                $targetPath = Join-Path $samplePath $target
                $lines = if (Test-Path -LiteralPath $targetPath) { @(Get-Content -LiteralPath $targetPath) } else { @() }
                $markerCount = @($lines | Where-Object { $_ -ceq $marker }).Count
                $hasExactFinalMarker = $lines.Count -gt 0 -and $lines[-1] -ceq $marker
                if ($changed.Count -ne 1 -or $changed[0] -ne $target) { $signals.Add("WRITE_SCOPE_MISMATCH"); $writeVerificationFailed = $true }
                if ($diffCheck) { $signals.Add("GIT_DIFF_CHECK_FAILED"); $writeVerificationFailed = $true }
                if ($markerCount -ne 1) { $signals.Add("WRITE_MARKER_MISMATCH"); $writeVerificationFailed = $true }
                if (-not $hasExactFinalMarker) { $signals.Add("WRITE_FINAL_LINE_MISMATCH"); $writeVerificationFailed = $true }
                $externalDiff = if ($writeVerificationFailed) { "failed" } else { "passed" }
                & git -C $samplePath restore . | Out-Null
                & git -C $samplePath clean -fd | Out-Null
            }
        }
        else {
            foreach ($expectedFile in @($entry.operationEvidence.$operation)) {
                if ($run.Stdout -notmatch [regex]::Escape($expectedFile)) { $signals.Add("EXPECTED_FILE_MISSING:$expectedFile") }
            }
            if ($run.Stdout -match '(?i)no readable (source )?code was provided|inspection requires access to file contents|please provide or upload these files|cannot be validated against actual (file )?contents|without (inspecting|viewing|reviewing|seeing) (the )?(actual )?(implementation|source|file contents|code)|unable to (evaluate|assess).*(without|in absence of).*(source|code)|cannot (verify|assess|evaluate|identify).*(without|in absence of).*(implementation|source|file contents|code)') {
                $signals.Add("UNREAD_SOURCE_CLAIM")
            }
            if ((& git -C $samplePath status --short | Out-String).Trim()) { $signals.Add("UNEXPECTED_READ_WRITE") }
        }

        $status = if ($signals.Count -eq 0) { "validated" } else { "failed" }
        if ($signals.Count -eq 0) { $signals.Add("none") }
        $results.Add([pscustomobject]@{
            Ecosystem = $entry.ecosystem
            RulePackId = $entry.rulePackId
            Sample = $entry.sample
            Operation = $operation
            Status = $status
            Surface = "Continue CLI"
            SurfaceVersion = $surfaceVersion
            Provider = "Ollama"
            Model = $model
            OperatingSystem = "Windows"
            SanitizedOutput = ConvertTo-SanitizedOutput -Text $run.Stdout -SamplePath $samplePath
            ExternalDiffVerification = $externalDiff
            FailureSignals = @($signals)
        })
        $elapsedSeconds = [math]::Round(((Get-Date) - $cellStarted).TotalSeconds, 1)
        Write-Host "[5/8] Completed $($entry.ecosystem) / $operation`: $status in $elapsedSeconds seconds"
        }
    }
}
catch {
    Invoke-TestedModelUnload
    throw
}

Write-Host "[6/8] Writing sanitized matrix report..."
$report = [pscustomobject]@{
    SchemaVersion = 1
    GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Surface = "Continue CLI"
    SurfaceVersion = $surfaceVersion
    Provider = "Ollama"
    OperatingSystem = "Windows"
    ReadModel = $readModel
    WriteModel = $writeModel
    Results = @($results)
    Notes = "Raw output remains under ignored runtime output. The report omits endpoints, local paths, prompts, stdout, and stderr."
}
$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

Invoke-TestedModelUnload

foreach ($result in $results) {
    Write-Host "$($result.Ecosystem) / $($result.Operation): $($result.Status) ($($result.FailureSignals -join ','))"
}
Write-Host "[8/8] Sanitized report written to $OutputPath"
