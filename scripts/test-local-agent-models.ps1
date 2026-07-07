param(
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string[]]$Models = @(),
    [string]$ModelCatalogPath,
    [string]$TargetRepo = (Get-Location).Path,
    [string]$OutputPath,
    [switch]$PullMissing,
    [switch]$UnloadAfterEach,
    [switch]$RemoveFailedModels,
    [string]$ModelProfilePath,
    [ValidateSet("TotalDedicated", "MaxDedicated")]
    [string]$VramSelectionMode = "TotalDedicated",
    [double]$AvailableVramGb = 0,
    [switch]$IncludeOversizedModels,
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "[1/8] Preparing local Agent model test run..."

if (-not $ModelCatalogPath) {
    $ModelCatalogPath = Join-Path $repoRoot "config/model-recommendations.tsv"
}

if (-not $OutputPath) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/local-agent-model-tests-$timestamp.json"
}

function ConvertTo-SafeBaseUrl {
    param([string]$Value)

    return $Value.TrimEnd("/")
}

function Invoke-OllamaJson {
    param(
        [string]$Path,
        [hashtable]$Body
    )

    $uri = "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)$Path"
    $json = $Body | ConvertTo-Json -Depth 20

    return Invoke-RestMethod -Uri $uri -Method Post -Body $json -ContentType "application/json" -TimeoutSec $TimeoutSeconds
}

function Get-OllamaTags {
    $uri = "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/tags"
    return Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec $TimeoutSeconds
}

function Get-CandidateModels {
    $candidates = [System.Collections.Generic.List[string]]::new()

    foreach ($model in $Models) {
        if (-not [string]::IsNullOrWhiteSpace($model)) {
            $candidates.Add($model.Trim())
        }
    }

    if ($candidates.Count -eq 0 -and (Test-Path -LiteralPath $ModelCatalogPath)) {
        $lines = Get-Content -LiteralPath $ModelCatalogPath
        foreach ($line in $lines) {
            if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
                continue
            }

            $parts = $line -split "\|"
            if ($parts.Count -lt 3) {
                continue
            }

            $fallbackModel = $parts[2].Trim()
            if (-not [string]::IsNullOrWhiteSpace($fallbackModel)) {
                $candidates.Add($fallbackModel)
            }
        }
    }

    if ($candidates.Count -eq 0) {
        @(
            "qwen3.5:9b"
        ) | ForEach-Object { $candidates.Add($_) }
    }

    return $candidates | Select-Object -Unique
}


function Get-ModelSizeBillion {
    param([string]$Model)

    $match = [regex]::Match($Model, '(?i)(\d+(?:\.\d+)?)b')
    if (-not $match.Success) {
        return 0
    }

    return [double]::Parse($match.Groups[1].Value, [System.Globalization.CultureInfo]::InvariantCulture)
}

function Get-RecommendedMinVramGb {
    param([string]$Model)

    if ($Model -match '(?i)(cloud|-mlx)') {
        return 999999
    }

    $size = Get-ModelSizeBillion -Model $Model
    if ($size -le 0) { return 0 }
    if ($size -le 1) { return 4 }
    if ($size -le 2) { return 6 }
    if ($size -le 4) { return 8 }
    if ($size -le 9) { return 12 }
    if ($size -le 14) { return 20 }
    if ($size -le 27) { return 36 }
    if ($size -le 35) { return 48 }
    if ($size -le 80) { return 80 }
    if ($size -le 122) { return 128 }

    return 512
}
function Get-CurrentPlatformName {
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::OSX)) {
        return "macOS"
    }
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Linux)) {
        return "Linux"
    }
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)) {
        return "Windows"
    }

    return "Unknown"
}

function Get-ModelHostPlatform {
    param([string]$Path)

    if (-not [string]::IsNullOrWhiteSpace($Path) -and (Test-Path -LiteralPath $Path)) {
        try {
            $profile = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
            if ($profile.Platform) {
                return [string]$profile.Platform
            }
        }
        catch {
            return Get-CurrentPlatformName
        }
    }

    return Get-CurrentPlatformName
}

function Get-NormalizedPlatformName {
    param([string]$Platform)

    if ($Platform -match '(?i)mac|darwin') { return "macOS" }
    if ($Platform -match '(?i)linux') { return "Linux" }
    if ($Platform -match '(?i)windows') { return "Windows" }
    return "Unknown"
}

function Get-ModelPullEligibility {
    param(
        [string]$Model,
        [string]$Platform
    )

    $normalizedPlatform = Get-NormalizedPlatformName -Platform $Platform
    if ($Model -match '(?i)cloud') {
        return [pscustomobject]@{
            Pullable = $false
            Reason = "Cloud catalog tag; local Ollama pull is not supported."
            FailureSignal = "MODEL_SKIPPED_FOR_PLATFORM"
        }
    }

    if ($Model -match '(?i)-mlx($|[-_:])' -and $normalizedPlatform -ne "macOS") {
        return [pscustomobject]@{
            Pullable = $false
            Reason = "MLX model tag requires a macOS Apple Silicon model host."
            FailureSignal = "MODEL_SKIPPED_FOR_PLATFORM"
        }
    }

    return [pscustomobject]@{
        Pullable = $true
        Reason = "Model tag is pullable for this host platform."
        FailureSignal = "none"
    }
}

function Get-AvailableVramFromProfile {
    param(
        [string]$Path,
        [string]$SelectionMode
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "ModelProfilePath does not exist: $Path"
    }

    $profile = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    $values = @()

    foreach ($gpu in @($profile.Gpus)) {
        if ($null -eq $gpu -or $null -eq $gpu.VramGb) {
            continue
        }

        $memoryType = [string]$gpu.MemoryType
        if ($memoryType -and $memoryType -notmatch '(?i)dedicated|unknown') {
            continue
        }

        try {
            $value = [double]::Parse([string]$gpu.VramGb, [System.Globalization.CultureInfo]::InvariantCulture)
            if ($value -gt 0) {
                $values += $value
            }
        }
        catch {
            continue
        }
    }

    if ($values.Count -eq 0) {
        return $null
    }

    if ($SelectionMode -eq "MaxDedicated") {
        return [math]::Round(($values | Measure-Object -Maximum).Maximum, 2)
    }

    return [math]::Round(($values | Measure-Object -Sum).Sum, 2)
}
function Pull-Model {
    param([string]$Model)

    try {
        Invoke-OllamaJson -Path "/api/pull" -Body @{
            model = $Model
            stream = $false
        } | Out-Null

        return [pscustomobject]@{
            Success = $true
            Error = $null
        }
    }
    catch {
        return [pscustomobject]@{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}


function Remove-Model {
    param([string]$Model)

    try {
        $uri = "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/delete"
        $body = @{
            model = $Model
        } | ConvertTo-Json -Depth 5

        Invoke-RestMethod -Uri $uri -Method Delete -Body $body -ContentType "application/json" -TimeoutSec $TimeoutSeconds | Out-Null

        return [pscustomobject]@{
            Attempted = $true
            Success = $true
            Error = $null
        }
    }
    catch {
        return [pscustomobject]@{
            Attempted = $true
            Success = $false
            Error = $_.Exception.Message
        }
    }
}
function Set-ModelLoaded {
    param(
        [string]$Model,
        [string]$KeepAlive = "10m"
    )

    try {
        Invoke-OllamaJson -Path "/api/chat" -Body @{
            model = $Model
            messages = @()
            keep_alive = $KeepAlive
            stream = $false
        } | Out-Null

        return [pscustomobject]@{
            Success = $true
            Error = $null
        }
    }
    catch {
        return [pscustomobject]@{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

function Invoke-ToolCallTest {
    param([string]$Model)

    $tools = @(
        @{
            type = "function"
            function = @{
                name = "read_file"
                description = "Read a repository file by relative path."
                parameters = @{
                    type = "object"
                    properties = @{
                        filepath = @{
                            type = "string"
                            description = "Repository-relative path to read."
                        }
                    }
                    required = @("filepath")
                }
            }
        }
    )

    try {
        $response = Invoke-OllamaJson -Path "/api/chat" -Body @{
            model = $Model
            stream = $false
            think = $false
            keep_alive = "10m"
            options = @{
                temperature = 0
                num_predict = 256
            }
            tools = $tools
            messages = @(
                @{
                    role = "user"
                    content = "Use the read_file tool to read README.md. Return a tool call only."
                }
            )
        }

        $message = $response.message
        $content = [string]$message.content
        $toolCalls = @($message.tool_calls)
        $firstCall = $toolCalls | Select-Object -First 1
        $toolName = $null
        $filePath = $null

        if ($firstCall -and $firstCall.function) {
            $toolName = [string]$firstCall.function.name
            if ($firstCall.function.arguments -and $firstCall.function.arguments.filepath) {
                $filePath = [string]$firstCall.function.arguments.filepath
            }
        }

        $rawToolSyntax = $content -match '(?i)(<function=|\{"name"\s*:|tool_call|function=)'
        $passed = ($toolName -eq "read_file" -and $filePath -eq "README.md" -and -not $rawToolSyntax)

        return [pscustomobject]@{
            Passed = $passed
            ToolName = $toolName
            FilePath = $filePath
            RawToolSyntax = [bool]$rawToolSyntax
            ContentPreview = ($content -replace "\s+", " ").Trim()
            Error = $null
        }
    }
    catch {
        return [pscustomobject]@{
            Passed = $false
            ToolName = $null
            FilePath = $null
            RawToolSyntax = $false
            ContentPreview = ""
            Error = $_.Exception.Message
        }
    }
}

function Invoke-ExactContentTest {
    param([string]$Model)

    $expected = "Continue Agent write test passed."

    try {
        $response = Invoke-OllamaJson -Path "/api/chat" -Body @{
            model = $Model
            stream = $false
            think = $false
            keep_alive = "10m"
            options = @{
                temperature = 0
                num_predict = 128
            }
            messages = @(
                @{
                    role = "system"
                    content = "Return only the exact requested file content. Do not include reasoning, tags, markdown, quotes, or explanations."
                },
                @{
                    role = "user"
                    content = "The entire file content must be exactly one line: $expected"
                }
            )
        }

        $content = [string]$response.message.content
        $normalized = ($content -replace "\r\n", "`n").Trim()
        $hasThinkLeak = $content -match "(?i)</?think>"
        $hasMarkdown = $content -match '```'
        $rawToolSyntax = $content -match "(?i)(<function=|tool_call|function=)"
        $passed = ($normalized -eq $expected -and -not $hasThinkLeak -and -not $hasMarkdown -and -not $rawToolSyntax)

        return [pscustomobject]@{
            Passed = $passed
            Expected = $expected
            Actual = $normalized
            ThinkLeak = [bool]$hasThinkLeak
            MarkdownFence = [bool]$hasMarkdown
            RawToolSyntax = [bool]$rawToolSyntax
            Error = $null
        }
    }
    catch {
        return [pscustomobject]@{
            Passed = $false
            Expected = $expected
            Actual = ""
            ThinkLeak = $false
            MarkdownFence = $false
            RawToolSyntax = $false
            Error = $_.Exception.Message
        }
    }
}

function Get-ModelPreferenceRank {
    param([string]$Model)

    if ($Model -match '(?i)^qwen3\.5:9b$') { return 0 }
    if ($Model -match '(?i)(coder|code|codestral|devstral)') { return 1 }
    if ($Model -match '(?i)(qwen|gpt-oss|llama3\.1)') { return 2 }
    return 3
}

function Get-TestRecommendation {
    param($Results)

    $approved = @($Results | Where-Object { $_.ApprovedWriteCandidate -eq $true })
    if ($approved.Count -eq 0) {
        return [pscustomobject]@{
            Status = "no-approved-model"
            PrimaryModel = $null
            Alternates = @()
            Reason = "No model passed both structured tool-call and exact-content checks."
            RecommendedUse = "Do not install a write-safe model from this run."
            NextStep = "Review failure signals, adjust candidates or settings, and rerun the test."
        }
    }

    $ranked = @($approved | Sort-Object `
        @{ Expression = { if ($_.VramRecommendation -and $_.VramRecommendation.RecommendedMinVramGb) { [double]$_.VramRecommendation.RecommendedMinVramGb } else { 9999 } } }, `
        @{ Expression = { Get-ModelPreferenceRank -Model $_.Model } }, `
        @{ Expression = { $_.Model } })

    $primary = $ranked | Select-Object -First 1
    $alternates = @($ranked | Select-Object -Skip 1 -First 3 | ForEach-Object { $_.Model })
    return [pscustomobject]@{
        Status = "recommended"
        PrimaryModel = $primary.Model
        Alternates = $alternates
        Reason = "Selected the smallest passing model, with a preference for previously validated coding-oriented local-agent families."
        RecommendedUse = "Use as the first model to validate in the editor. Keep approved-write validation as the final gate."
        NextStep = "Run Continue read-only and approved-write smoke tests before installing this model as write-safe."
    }
}

function Get-FailureSignal {
    param(
        $LoadResult,
        $ToolResult,
        $ContentResult
    )

    if (-not $LoadResult.Success) {
        return "MODEL_LOAD_FAILED"
    }

    if ($ToolResult.Error -match "does not support tools") {
        return "MODEL_DOES_NOT_SUPPORT_TOOLS"
    }

    if ($ToolResult.RawToolSyntax) {
        return "RAW_TOOL_CALL_OUTPUT"
    }

    if (-not $ToolResult.Passed) {
        return "TOOL_CALL_FAILED"
    }

    if ($ContentResult.ThinkLeak) {
        return "THINK_TAG_LEAK"
    }

    if ($ContentResult.RawToolSyntax) {
        return "RAW_TOOL_CALL_OUTPUT"
    }

    if (-not $ContentResult.Passed) {
        return "INCORRECT_EXACT_CONTENT"
    }

    return "none"
}

Write-Host "[2/8] Validating target repository path..."
try {
    $targetRepoResolved = (Resolve-Path -LiteralPath $TargetRepo).Path
}
catch {
    throw "TargetRepo does not exist: $TargetRepo"
}

Write-Host "[3/8] Connecting to Ollama and reading installed models..."
$installed = @()
try {
    $tags = Get-OllamaTags
    $installed = @($tags.models | ForEach-Object { $_.name })
}
catch {
    throw "Could not reach Ollama at $OllamaBaseUrl. $($_.Exception.Message)"
}

$effectiveAvailableVramGb = $AvailableVramGb
$vramSource = if ($effectiveAvailableVramGb -gt 0) { "explicit" } else { $null }

if ($effectiveAvailableVramGb -le 0 -and $ModelProfilePath) {
    Write-Host "[4/8] Reading VRAM from model profile using $VramSelectionMode mode..."
    $profileVram = Get-AvailableVramFromProfile -Path $ModelProfilePath -SelectionMode $VramSelectionMode
    if ($null -ne $profileVram -and $profileVram -gt 0) {
        $effectiveAvailableVramGb = $profileVram
        $vramSource = "model-profile:$VramSelectionMode"
    }
}

$modelHostPlatform = Get-ModelHostPlatform -Path $ModelProfilePath
Write-Host "[5/8] Model host platform: $modelHostPlatform"

$candidateModels = @(Get-CandidateModels)
Write-Host "[5/8] Candidate models: $($candidateModels -join ', ')"
if ($effectiveAvailableVramGb -gt 0) {
    Write-Host "[5/8] Available VRAM estimate: $effectiveAvailableVramGb GB ($vramSource)"
} else {
    Write-Host "[5/8] No VRAM estimate available; VRAM gating will not skip models."
}
Write-Host "[5/8] Timeout per Ollama API request: $TimeoutSeconds seconds. Large model pulls may need 1800 seconds or a manual ollama pull first."
$results = [System.Collections.Generic.List[object]]::new()

$totalModels = $candidateModels.Count
$modelIndex = 0
foreach ($model in $candidateModels) {
    $modelIndex++
    Write-Host "[6/8] Testing model $modelIndex/$($totalModels): $model"

    $recommendedMinVramGb = Get-RecommendedMinVramGb -Model $model
    $fitsAvailableVram = $true
    if ($effectiveAvailableVramGb -gt 0 -and $recommendedMinVramGb -gt 0) {
        $fitsAvailableVram = ($recommendedMinVramGb -le $effectiveAvailableVramGb)
    }

    $vramRecommendation = [pscustomobject]@{
        AvailableVramGb = if ($effectiveAvailableVramGb -gt 0) { $effectiveAvailableVramGb } else { $null }
        RecommendedMinVramGb = if ($recommendedMinVramGb -gt 0 -and $recommendedMinVramGb -lt 999999) { $recommendedMinVramGb } else { $null }
        FitsAvailableVram = [bool]$fitsAvailableVram
    }
    $platformEligibility = Get-ModelPullEligibility -Model $model -Platform $modelHostPlatform

    if (-not $platformEligibility.Pullable) {
        Write-Host "[6/8] Skipping $model before pull: $($platformEligibility.Reason)"
        $results.Add([pscustomobject]@{
            Model = $model
            Installed = $false
            Pull = [pscustomobject]@{
                Attempted = $false
                Success = $false
                Error = $platformEligibility.Reason
            }
            Loaded = $false
            ToolCall = $null
            ExactContent = $null
            FailureSignal = $platformEligibility.FailureSignal
            ApprovedWriteCandidate = $false
            Removal = [pscustomobject]@{
                Attempted = $false
                Success = $false
                Error = $null
            }
            ModelHostPlatform = $modelHostPlatform
            PlatformEligibility = $platformEligibility
            VramRecommendation = $vramRecommendation
        })
        continue
    }

    if (-not $fitsAvailableVram -and -not $IncludeOversizedModels) {
        Write-Host "[6/8] Skipping $model before pull: estimated minimum VRAM is $recommendedMinVramGb GB and available estimate is $effectiveAvailableVramGb GB."
        $results.Add([pscustomobject]@{
            Model = $model
            Installed = $false
            Pull = [pscustomobject]@{
                Attempted = $false
                Success = $false
                Error = "Skipped before pull because the model is above the available VRAM limit."
            }
            Loaded = $false
            ToolCall = $null
            ExactContent = $null
            FailureSignal = "MODEL_SKIPPED_FOR_VRAM"
            ApprovedWriteCandidate = $false
            Removal = [pscustomobject]@{
                Attempted = $false
                Success = $false
                Error = $null
            }
            ModelHostPlatform = $modelHostPlatform
            PlatformEligibility = $platformEligibility
            VramRecommendation = $vramRecommendation
        })
        continue
    }

    $isInstalled = $installed -contains $model
    $pullResult = [pscustomobject]@{
        Attempted = $false
        Success = $isInstalled
        Error = $null
    }

    if (-not $isInstalled -and $PullMissing) {
        Write-Host "[6/8] Pulling missing model: $model. This can take several minutes for large models. Timeout: $TimeoutSeconds seconds."
        $pull = Pull-Model -Model $model
        $pullResult = [pscustomobject]@{
            Attempted = $true
            Success = $pull.Success
            Error = $pull.Error
        }
        $isInstalled = $pull.Success
        if (-not $pull.Success) {
            Write-Host "[6/8] Pull failed or timed out for $model. Increase -TimeoutSeconds or run ollama pull on the model server first."
        }
    }

    if (-not $isInstalled) {
        $results.Add([pscustomobject]@{
            Model = $model
            Installed = $false
            Pull = $pullResult
            Loaded = $false
            ToolCall = $null
            ExactContent = $null
            FailureSignal = "MODEL_NOT_INSTALLED"
            ApprovedWriteCandidate = $false
            Removal = [pscustomobject]@{
                Attempted = $false
                Success = $false
                Error = $null
            }
            ModelHostPlatform = $modelHostPlatform
            PlatformEligibility = $platformEligibility
            VramRecommendation = $vramRecommendation
        })
        continue
    }

    Write-Host "[6/8] Loading $model and running API preflight checks..."
    $loadResult = Set-ModelLoaded -Model $model -KeepAlive "10m"
    $toolResult = Invoke-ToolCallTest -Model $model
    $contentResult = Invoke-ExactContentTest -Model $model
    $failureSignal = Get-FailureSignal -LoadResult $loadResult -ToolResult $toolResult -ContentResult $contentResult

    $removalResult = [pscustomobject]@{
        Attempted = $false
        Success = $false
        Error = $null
    }

    if ($UnloadAfterEach -or ($RemoveFailedModels -and $failureSignal -ne "none")) {
        Write-Host "[7/8] Unloading $model from Ollama..."
        Set-ModelLoaded -Model $model -KeepAlive 0 | Out-Null
    }

    if ($RemoveFailedModels -and $failureSignal -ne "none") {
        Write-Host "[7/8] Removing failed model: $model"
        $removalResult = Remove-Model -Model $model
    }

    $results.Add([pscustomobject]@{
        Model = $model
        Installed = $true
        Pull = $pullResult
        Loaded = $loadResult.Success
        ToolCall = $toolResult
        ExactContent = $contentResult
        FailureSignal = $failureSignal
        ApprovedWriteCandidate = ($failureSignal -eq "none")
        Removal = $removalResult
        ModelHostPlatform = $modelHostPlatform
        PlatformEligibility = $platformEligibility
        VramRecommendation = $vramRecommendation
    })
}

$recommendation = Get-TestRecommendation -Results $results

$report = [pscustomobject]@{
    GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    OllamaBaseUrl = "redacted"
    TargetRepo = "redacted"
    TargetRepoDetected = [bool]$targetRepoResolved
    PullMissing = [bool]$PullMissing
    UnloadAfterEach = [bool]$UnloadAfterEach
    RemoveFailedModels = [bool]$RemoveFailedModels
    ModelProfilePath = if ($ModelProfilePath) { "redacted" } else { $null }
    VramSelectionMode = $VramSelectionMode
    AvailableVramGb = if ($effectiveAvailableVramGb -gt 0) { $effectiveAvailableVramGb } else { $null }
    AvailableVramSource = $vramSource
    ModelHostPlatform = $modelHostPlatform
    IncludeOversizedModels = [bool]$IncludeOversizedModels
    Recommendation = $recommendation
    Results = $results
    Note = "This tests Ollama API tool-call and exact-content behavior. It does not replace Continue UI Apply validation."
}

$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host "[8/8] Writing sanitized report and summary..."

foreach ($result in $results) {
    $status = if ($result.ApprovedWriteCandidate) { "candidate" } else { "failed" }
    Write-Host "$($result.Model): $status ($($result.FailureSignal))"
}

if ($recommendation.PrimaryModel) {
    Write-Host "Recommended model: $($recommendation.PrimaryModel)"
    if (@($recommendation.Alternates).Count -gt 0) {
        Write-Host "Alternate passing models: $($recommendation.Alternates -join ', ')"
    }
    Write-Host "Recommendation note: $($recommendation.NextStep)"
} else {
    Write-Host "Recommended model: none"
    Write-Host "Recommendation note: $($recommendation.NextStep)"
}

Write-Host "Report written to $OutputPath"
