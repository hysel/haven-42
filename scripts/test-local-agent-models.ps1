param(
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string[]]$Models = @(),
    [string]$ModelCatalogPath,
    [string]$TargetRepo = (Get-Location).Path,
    [string]$OutputPath,
    [switch]$PullMissing,
    [switch]$UnloadAfterEach,
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

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
            "qwen3.5:9b",
            "devstral-small-2:24b",
            "qwen3-coder:30b"
        ) | ForEach-Object { $candidates.Add($_) }
    }

    return $candidates | Select-Object -Unique
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

try {
    $targetRepoResolved = (Resolve-Path -LiteralPath $TargetRepo).Path
}
catch {
    throw "TargetRepo does not exist: $TargetRepo"
}

$installed = @()
try {
    $tags = Get-OllamaTags
    $installed = @($tags.models | ForEach-Object { $_.name })
}
catch {
    throw "Could not reach Ollama at $OllamaBaseUrl. $($_.Exception.Message)"
}

$candidateModels = @(Get-CandidateModels)
$results = [System.Collections.Generic.List[object]]::new()

foreach ($model in $candidateModels) {
    Write-Host "Testing model: $model"

    $isInstalled = $installed -contains $model
    $pullResult = [pscustomobject]@{
        Attempted = $false
        Success = $isInstalled
        Error = $null
    }

    if (-not $isInstalled -and $PullMissing) {
        Write-Host "Pulling missing model: $model"
        $pull = Pull-Model -Model $model
        $pullResult = [pscustomobject]@{
            Attempted = $true
            Success = $pull.Success
            Error = $pull.Error
        }
        $isInstalled = $pull.Success
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
        })
        continue
    }

    $loadResult = Set-ModelLoaded -Model $model -KeepAlive "10m"
    $toolResult = Invoke-ToolCallTest -Model $model
    $contentResult = Invoke-ExactContentTest -Model $model
    $failureSignal = Get-FailureSignal -LoadResult $loadResult -ToolResult $toolResult -ContentResult $contentResult

    if ($UnloadAfterEach) {
        Set-ModelLoaded -Model $model -KeepAlive 0 | Out-Null
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
    })
}

$report = [pscustomobject]@{
    GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    OllamaBaseUrl = "redacted"
    TargetRepo = "redacted"
    TargetRepoDetected = [bool]$targetRepoResolved
    PullMissing = [bool]$PullMissing
    UnloadAfterEach = [bool]$UnloadAfterEach
    Results = $results
    Note = "This tests Ollama API tool-call and exact-content behavior. It does not replace Continue UI Apply validation."
}

$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

foreach ($result in $results) {
    $status = if ($result.ApprovedWriteCandidate) { "candidate" } else { "failed" }
    Write-Host "$($result.Model): $status ($($result.FailureSignal))"
}

Write-Host "Report written to $OutputPath"
