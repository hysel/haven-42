param(
    [string]$ExpectedVersion = "0.1.12"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$failed = $false
$testCount = 0

function Add-TestPass {
    param([string]$Name)

    Write-Host "PASS $Name" -ForegroundColor Green
}

function Add-TestFailure {
    param(
        [string]$Name,
        [string]$Message
    )

    Write-Host "FAIL $Name - $Message" -ForegroundColor Red
    $script:failed = $true
}

function Invoke-PackTest {
    param(
        [string]$Name,
        [scriptblock]$Test
    )

    $script:testCount++

    try {
        & $Test
        Add-TestPass -Name $Name
    }
    catch {
        Add-TestFailure -Name $Name -Message $_.Exception.Message
    }
}

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Assert-Equal {
    param(
        $Actual,
        $Expected,
        [string]$Message
    )

    if ($Actual -ne $Expected) {
        throw "$Message Expected '$Expected' but got '$Actual'."
    }
}

function Invoke-CommandCapture {
    param(
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $repoRoot
    )

    $output = & pwsh -NoProfile -ExecutionPolicy Bypass -File $FilePath @Arguments 2>&1

    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = ($output -join "`n")
    }
}

function Copy-RepositoryForTest {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "continue-pack-test-$([guid]::NewGuid())"
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

    Get-ChildItem -LiteralPath $repoRoot -Force |
        Where-Object {
            $_.Name -notin @(".git", "runtime-validation-output") -and
            $_.Name -ne ".vscode"
        } |
        ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $tempRoot -Recurse -Force
        }

    return $tempRoot
}

function Invoke-TempValidation {
    param(
        [string]$TempRoot,
        [string[]]$Arguments = @()
    )

    $scriptPath = Join-Path $TempRoot "scripts/validate-pack.ps1"
    return Invoke-CommandCapture -FilePath $scriptPath -Arguments $Arguments -WorkingDirectory $TempRoot
}

Invoke-PackTest "validate-pack succeeds for repository" {
    $result = Invoke-CommandCapture -FilePath (Join-Path $repoRoot "scripts/validate-pack.ps1")
    Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "validate-pack should succeed."
    Assert-True -Condition ($result.Output -match "Validation passed\.") -Message "Validation pass message was not found."
}

Invoke-PackTest "validate-pack fails for wrong expected version" {
    $result = Invoke-CommandCapture -FilePath (Join-Path $repoRoot "scripts/validate-pack.ps1") -Arguments @("-ExpectedVersion", "0.0.0")
    Assert-True -Condition ($result.ExitCode -ne 0) -Message "validate-pack should fail for a mismatched version."
    Assert-True -Condition ($result.Output -match "FAIL config version is 0\.0\.0") -Message "Expected version failure was not reported."
}

Invoke-PackTest "validate-pack ignores local config overrides" {
    $tempRoot = Copy-RepositoryForTest

    try {
        $privateEndpoint = "http://" + "192" + ".168.0.10:11434"
        $localConfigPath = Join-Path $tempRoot ".continue/config.local.test.yaml"
        "models:`n  - apiBase: $privateEndpoint" | Set-Content -LiteralPath $localConfigPath

        $result = Invoke-TempValidation -TempRoot $tempRoot
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Local config override should be ignored by private endpoint scanning."
        Assert-True -Condition ($result.Output -match "Validation passed\.") -Message "Validation pass message was not found."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "validate-pack fails when private endpoint is committed" {
    $tempRoot = Copy-RepositoryForTest

    try {
        $privateEndpoint = "http://" + "192" + ".168.0.10:11434"
        "Do not commit $privateEndpoint" | Set-Content -LiteralPath (Join-Path $tempRoot "docs/private-endpoint-test.md")

        $result = Invoke-TempValidation -TempRoot $tempRoot
        Assert-True -Condition ($result.ExitCode -ne 0) -Message "Validation should fail for committed private endpoint text."
        Assert-True -Condition ($result.Output -match "FAIL no private IP address committed") -Message "Private endpoint failure was not reported."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "validate-pack fails when required safety doc is missing" {
    $tempRoot = Copy-RepositoryForTest

    try {
        Remove-Item -LiteralPath (Join-Path $tempRoot "docs/local-config-safety.md") -Force

        $result = Invoke-TempValidation -TempRoot $tempRoot
        Assert-True -Condition ($result.ExitCode -ne 0) -Message "Validation should fail when a required doc is missing."
        Assert-True -Condition ($result.Output -match "FAIL required file exists: docs/local-config-safety.md") -Message "Missing safety doc failure was not reported."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "model recommendation catalog has valid schema" {
    $catalogPath = Join-Path $repoRoot "config/model-recommendations.tsv"
    $rows = Get-Content -LiteralPath $catalogPath | Where-Object { $_ -and -not $_.StartsWith("#") }
    $allowedTiers = @("High", "Medium", "Low")
    $fallbacks = @{}

    foreach ($row in $rows) {
        $parts = $row -split "\|", 5
        Assert-Equal -Actual $parts.Count -Expected 5 -Message "Catalog row should have five pipe-delimited columns: $row"
        Assert-True -Condition ($parts[0] -in $allowedTiers) -Message "Catalog row has an unsupported tier: $row"
        Assert-True -Condition ($parts[3].Trim().Length -gt 0) -Message "Catalog row must include recommended use: $row"
        Assert-True -Condition ($parts[4].Trim().Length -gt 0) -Message "Catalog row must include validation note: $row"

        if ($parts[1]) {
            try {
                [regex]::new($parts[1]) | Out-Null
            }
            catch {
                throw "Catalog row has invalid regex pattern '$($parts[1])'."
            }
        } else {
            Assert-True -Condition ($parts[2].Trim().Length -gt 0) -Message "Fallback row must include fallback model: $row"
            Assert-True -Condition ($parts[2] -notmatch "\s+or\s+") -Message "Fallback model must be one concrete model value: $row"
            $fallbacks[$parts[0]] = $true
        }
    }

    foreach ($tier in $allowedTiers) {
        Assert-True -Condition $fallbacks.ContainsKey($tier) -Message "Catalog must include a fallback row for $tier."
    }

    $catalogText = Get-Content -LiteralPath $catalogPath -Raw
    Assert-True -Condition ($catalogText -match "WRITE SAFE lane") -Message "Catalog should include the validated WRITE SAFE profile model."
    Assert-True -Condition ($catalogText -notmatch "rejected starter model") -Message "Catalog should avoid rejected starter-model guidance."
}

Invoke-PackTest "committed config uses a starter sample model" {
    $configPath = Join-Path $repoRoot ".continue/config.yaml"
    $config = Get-Content -LiteralPath $configPath -Raw

    Assert-True -Condition ($config -match "model: qwen3\.5:9b") -Message "Committed config should use the validated WRITE SAFE starter candidate."
    Assert-True -Condition ($config -notmatch "model: qwen3-coder:30b") -Message "Committed config should not require the high-resource sample model."
}

Invoke-PackTest "MLX model recommendation catalog has valid schema" {
    $catalogPath = Join-Path $repoRoot "config/model-recommendations.mlx.tsv"
    $rows = Get-Content -LiteralPath $catalogPath | Where-Object { $_ -and -not $_.StartsWith("#") }
    $allowedTiers = @("High", "Medium", "Low")
    $seenTiers = @{}

    foreach ($row in $rows) {
        $parts = $row -split "\|", 4
        Assert-Equal -Actual $parts.Count -Expected 4 -Message "MLX catalog row should have four pipe-delimited columns: $row"
        Assert-True -Condition ($parts[0] -in $allowedTiers) -Message "MLX catalog row has an unsupported tier: $row"
        Assert-True -Condition ($parts[1].Trim().Length -gt 0) -Message "MLX catalog row must include a recommended model: $row"
        Assert-True -Condition ($parts[2].Trim().Length -gt 0) -Message "MLX catalog row must include recommended use: $row"
        Assert-True -Condition ($parts[3].Trim().Length -gt 0) -Message "MLX catalog row must include validation note: $row"
        $seenTiers[$parts[0]] = $true
    }

    foreach ($tier in $allowedTiers) {
        Assert-True -Condition $seenTiers.ContainsKey($tier) -Message "MLX catalog must include a row for $tier."
    }
}

Invoke-PackTest "hardware profile scripts report CPU architecture" {
    $scriptNames = @(
        "get-local-model-profile.windows.ps1",
        "get-local-model-profile.linux.sh",
        "get-local-model-profile.macos.sh"
    )

    foreach ($scriptName in $scriptNames) {
        $scriptPath = Join-Path $repoRoot "scripts/$scriptName"
        $content = Get-Content -LiteralPath $scriptPath -Raw

        Assert-True -Condition ($content -match "CpuArchitecture") -Message "$scriptName should include CpuArchitecture in JSON output."
        Assert-True -Condition ($content -match "Architecture:") -Message "$scriptName should include Architecture in text output."
    }
}

Invoke-PackTest "macOS hardware profile reports MLX separately from Ollama" {
    $scriptPath = Join-Path $repoRoot "scripts/get-local-model-profile.macos.sh"
    $content = Get-Content -LiteralPath $scriptPath -Raw

    Assert-True -Condition ($content -match "MlxStatus") -Message "macOS profile JSON output should include MlxStatus."
    Assert-True -Condition ($content -match "MlxTools") -Message "macOS profile JSON output should include MlxTools."
    Assert-True -Condition ($content -match "MLX tooling:") -Message "macOS profile text output should include MLX tooling status."
    Assert-True -Condition ($content -match "MlxRecommendation") -Message "macOS profile JSON output should include MlxRecommendation."
    Assert-True -Condition ($content -match "MLX recommendation:") -Message "macOS profile text output should include MLX recommendation."
    Assert-True -Condition ($content -match "mlx_lm\.server") -Message "macOS profile should look for MLX server tooling."
    Assert-True -Condition ($content -match "model-recommendations\.mlx\.tsv") -Message "macOS profile should use the separate MLX catalog."
    Assert-True -Condition ($content -match "OllamaModels") -Message "macOS profile should keep Ollama models as a separate output."
}

Invoke-PackTest "Linux hardware profile reports ARM platform notes" {
    $scriptPath = Join-Path $repoRoot "scripts/get-local-model-profile.linux.sh"
    $content = Get-Content -LiteralPath $scriptPath -Raw

    Assert-True -Condition ($content -match "PlatformNotes") -Message "Linux profile JSON output should include PlatformNotes."
    Assert-True -Condition ($content -match "Platform notes:") -Message "Linux profile text output should include Platform notes."
    Assert-True -Condition ($content -match "nv_tegra_release") -Message "Linux profile should look for NVIDIA Tegra release indicators."
    Assert-True -Condition ($content -match "jetson\|tegra\|nvidia") -Message "Linux profile should look for Jetson or Tegra device-tree indicators."
    Assert-True -Condition ($content -match "ARM Linux detected") -Message "Linux profile should add conservative notes for ARM Linux."
    Assert-True -Condition ($content -match "GPU_DETECTION_TOOLS") -Message "Linux profile should track optional GPU detection tools."
    Assert-True -Condition ($content -match "Linux GPU detection is limited") -Message "Linux profile should warn when optional GPU detection tools are missing."
    Assert-True -Condition ($content -match "no GPU was detected") -Message "Linux profile should warn when tools are present but no GPU is detected."
    Assert-True -Condition ($content -match "detect_container_context") -Message "Linux profile should detect common container contexts."
    Assert-True -Condition ($content -match "Container or LXC-style environment detected") -Message "Linux profile should warn when container context is detected."
}

Invoke-PackTest "compatibility docs include cloud and container smoke tests" {
    $docPath = Join-Path $repoRoot "docs/compatibility.md"
    $content = Get-Content -LiteralPath $docPath -Raw

    Assert-True -Condition ($content -match "Recommended enterprise/cloud smoke test") -Message "Compatibility docs should include enterprise/cloud smoke-test guidance."
    Assert-True -Condition ($content -match "Recommended container smoke test") -Message "Compatibility docs should include container smoke-test guidance."
    Assert-True -Condition ($content -match "get-local-model-profile\.linux\.sh") -Message "Compatibility smoke tests should reference the Linux hardware profile helper."
}

Invoke-PackTest "editor compatibility docs cover config and tool validation" {
    $docPath = Join-Path $repoRoot "docs/editor-compatibility.md"
    $evidencePath = Join-Path $repoRoot "examples/editor-surface-validation.md"
    $content = Get-Content -LiteralPath $docPath -Raw
    $evidence = Get-Content -LiteralPath $evidencePath -Raw

    Assert-True -Condition ($content -match "VS Code") -Message "Editor compatibility docs should cover VS Code."
    Assert-True -Condition ($content -match "VSCodium") -Message "Editor compatibility docs should cover VSCodium."
    Assert-True -Condition ($content -match "project-local") -Message "Editor compatibility docs should explain project-local config."
    Assert-True -Condition ($content -match "Duplicate rule") -Message "Editor compatibility docs should cover duplicate rules."
    Assert-True -Condition ($content -match "Agent mode") -Message "Editor compatibility docs should cover Agent mode."
    Assert-True -Condition ($content -like "*npx -y @continuedev/cli --config .continue/config.yaml*") -Message "Editor compatibility docs should include CLI fallback command."
    Assert-True -Condition ($content -match "Terminal Preflight Checks") -Message "Editor compatibility docs should include terminal preflight checks."
    Assert-True -Condition ($content -match "examples/editor-surface-validation.md") -Message "Editor compatibility docs should reference sanitized evidence."
    Assert-True -Condition ($evidence -match "Editor Surface Validation Evidence") -Message "Editor evidence should have the expected title."
    Assert-True -Condition ($evidence -match "VS Code-compatible build") -Message "Editor evidence should record VS Code-compatible detection."
    Assert-True -Condition ($evidence -match "VSCodium") -Message "Editor evidence should record VSCodium detection."
    Assert-True -Condition ($evidence -match "Read-only tool validated") -Message "Editor evidence should record VS Code-compatible read-only validation."
    Assert-True -Condition ($evidence -match "qwen3-coder:30b") -Message "Editor evidence should record the validated model."
    Assert-True -Condition ($evidence -match "Do not mark approved-write ready") -Message "Editor evidence should avoid overstating write readiness."
    Assert-True -Condition ($evidence -match "VSCodium Agent Tool Test") -Message "Editor evidence should include VSCodium Agent test results."
    Assert-True -Condition ($evidence -match "<function=ls>") -Message "Editor evidence should record the VSCodium tool-call markup failure."
    Assert-True -Condition ($evidence -match "Controlled Retest") -Message "Editor evidence should record the VSCodium controlled retest."
    Assert-True -Condition ($evidence -match "Ollama Qwen Coder") -Message "Editor evidence should record the VSCodium retest model label."
    Assert-True -Condition ($evidence -match "Continue listed files in \.") -Message "Editor evidence should record successful VSCodium tool execution."
    Assert-True -Condition ($evidence -match "model connection error") -Message "Editor evidence should record CLI connection failure safely."
    Assert-True -Condition ($evidence -match "Duplicate-Rule Warning Check") -Message "Editor evidence should record duplicate-rule warning validation."
    Assert-True -Condition ($evidence -match "No duplicate-rule warnings observed") -Message "Editor evidence should record clean duplicate-rule status."
}

Invoke-PackTest "model tool-use validation docs define evidence workflow" {
    $docPath = Join-Path $repoRoot "docs/model-tool-use-validation.md"
    $localAgentTestingPath = Join-Path $repoRoot "docs/local-agent-model-testing.md"
    $templatePath = Join-Path $repoRoot "examples/model-tool-use-validation.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Model tool-use validation doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $localAgentTestingPath) -Message "Local Agent model testing doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $templatePath) -Message "Model tool-use evidence template should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $localAgentTesting = Get-Content -LiteralPath $localAgentTestingPath -Raw
    $template = Get-Content -LiteralPath $templatePath -Raw

    Assert-True -Condition ($doc -match "Candidate") -Message "Validation doc should define candidate status."
    Assert-True -Condition ($doc -match "Read-only tool validated") -Message "Validation doc should define read-only tool validated status."
    Assert-True -Condition ($doc -match "read-only listing only") -Message "Validation doc should define read-only listing only status."
    Assert-True -Condition ($doc -match "Approved-write ready") -Message "Validation doc should define approved-write ready status."
    Assert-True -Condition ($doc -match "raw JSON") -Message "Validation doc should explain raw JSON tool-call failure."
    Assert-True -Condition ($doc -match "read file contents") -Message "Validation doc should require file-content reading for implementation workflows."
    Assert-True -Condition ($doc -match "READ_TOOLS_UNAVAILABLE") -Message "Validation doc should document the read-tools unavailable signal."
    Assert-True -Condition ($doc -match "WRITE_NOT_APPLIED") -Message "Validation doc should document the write-not-applied signal."
    Assert-True -Condition ($doc -match "PATH_AMBIGUOUS") -Message "Validation doc should document ambiguous target path handling."
    Assert-True -Condition ($doc -match "WORKSPACE_UNAVAILABLE") -Message "Validation doc should document workspace discovery failure handling."
    Assert-True -Condition ($doc -match "APPLY_TARGET_MISMATCH") -Message "Validation doc should document apply target mismatch handling."
    Assert-True -Condition ($doc -match "create_new_file") -Message "Validation doc should cover disabling create_new_file during existing-file write validation."
    Assert-True -Condition ($doc -match "DUPLICATE_APPROVALS") -Message "Validation doc should document duplicate approval handling."
    Assert-True -Condition ($doc -match "DUPLICATE_CONTENT") -Message "Validation doc should document duplicate content handling."
    Assert-True -Condition ($doc -match "edit_file") -Message "Validation doc should explain printed edit-call text without a diff."
    Assert-True -Condition ($doc -match "Validation labels must match the evidence") -Message "Validation doc should require status/failure consistency."
    Assert-True -Condition ($doc -match "opened repository root or current folder") -Message "Validation doc should require current-folder path resolution."
    Assert-True -Condition ($doc -match "external shell or git check") -Message "Validation doc should require external write verification."
    Assert-True -Condition ($doc -match "Test-Path") -Message "Validation doc should include Windows external file verification."
    Assert-True -Condition ($doc -match "test -f") -Message "Validation doc should include Linux/macOS external file verification."
    Assert-True -Condition ($doc -match "active shell and operating system") -Message "Validation doc should require platform-aware command use."
    Assert-True -Condition ($doc -match "continue-agent-write-test\.md") -Message "Validation doc should include the approved-write smoke test file."
    Assert-True -Condition ($doc -match "I can't directly edit files") -Message "Validation doc should cover refusal-to-edit failure mode."
    Assert-True -Condition ($doc -match "examples/model-tool-use-validation.md") -Message "Validation doc should reference the evidence template."
    Assert-True -Condition ($doc -match "Do not record") -Message "Validation doc should include sanitization rules."
    Assert-True -Condition ($doc -match "docs/local-agent-model-testing.md") -Message "Validation doc should reference automated local model preflight."

    Assert-True -Condition ($localAgentTesting -match "pull candidate Ollama models") -Message "Local Agent testing doc should describe model pulling."
    Assert-True -Condition ($localAgentTesting -match "load a model") -Message "Local Agent testing doc should describe model loading."
    Assert-True -Condition ($localAgentTesting -match "unload a model") -Message "Local Agent testing doc should describe model unloading."
    Assert-True -Condition ($localAgentTesting -match "tool-call behavior") -Message "Local Agent testing doc should describe tool-call checks."
    Assert-True -Condition ($localAgentTesting -match "exact-content output") -Message "Local Agent testing doc should describe exact output checks."
    Assert-True -Condition ($localAgentTesting -match "does not replace Continue UI Apply validation") -Message "Local Agent testing doc should keep manual Apply validation boundary."
    Assert-True -Condition ($localAgentTesting -match "MODEL_DOES_NOT_SUPPORT_TOOLS") -Message "Local Agent testing doc should list model tool support failure."
    Assert-True -Condition ($localAgentTesting -match "THINK_TAG_LEAK") -Message "Local Agent testing doc should list reasoning tag leak failure."
    Assert-True -Condition ($localAgentTesting -match "runtime-validation-output") -Message "Local Agent testing doc should document report output."
    Assert-True -Condition ($doc -match "model lanes") -Message "Validation doc should explain model lanes role boundaries."

    Assert-True -Condition ($template -match "Model Tool-Use Validation Evidence") -Message "Evidence template should have the expected title."
    Assert-True -Condition ($template -match "Read-only listing only") -Message "Evidence template should include read-only listing only status."
    Assert-True -Condition ($template -match "Failure signal") -Message "Evidence template should record failure signals."
    Assert-True -Condition ($template -match "Provider: Ollama") -Message "Evidence template should record provider."
    Assert-True -Condition ($template -match "Editor surface") -Message "Evidence template should record editor surface."
    Assert-True -Condition ($template -match "MCP state") -Message "Evidence template should record MCP state."
    Assert-True -Condition ($template -match "Read-content tool execution") -Message "Evidence template should record read-content validation."
    Assert-True -Condition ($template -match "Path resolution and current-folder behavior") -Message "Evidence template should record current-folder path validation."
    Assert-True -Condition ($template -match "Workspace discovery with no active file") -Message "Evidence template should record no-active-file workspace discovery validation."
    Assert-True -Condition ($template -match "Apply target alignment") -Message "Evidence template should record apply target alignment validation."
    Assert-True -Condition ($template -match "Duplicate approval guard") -Message "Evidence template should include duplicate approval guard testing."
    Assert-True -Condition ($template -match "DUPLICATE_APPROVALS") -Message "Evidence template should record duplicate approval failure signals."
    Assert-True -Condition ($template -match "External write verification") -Message "Evidence template should require external write verification for write tests."
    Assert-True -Condition ($template -match "Platform-aware command use") -Message "Evidence template should record platform-aware command validation."
    Assert-True -Condition ($template -match "Sanitization Checklist") -Message "Evidence template should include sanitization checklist."
}

Invoke-PackTest "tool-use docs define platform-aware approved write behavior" {
    $generalRulePath = Join-Path $repoRoot ".continue/rules/general.md"
    $toolModesPath = Join-Path $repoRoot "docs/tool-use-modes.md"
    $approvedChangesPath = Join-Path $repoRoot "docs/approved-tool-backed-changes.md"
    $readmePath = Join-Path $repoRoot "README.md"

    $generalRule = Get-Content -LiteralPath $generalRulePath -Raw
    $toolModes = Get-Content -LiteralPath $toolModesPath -Raw
    $approvedChanges = Get-Content -LiteralPath $approvedChangesPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw

    Assert-True -Condition ($generalRule -match "Match commands to the user's active operating system and shell") -Message "General rules should require platform-aware command selection."
    Assert-True -Condition ($generalRule -match "READ_TOOLS_UNAVAILABLE") -Message "General rules should require a clear read-tool failure signal."
    Assert-True -Condition ($generalRule -match "WRITE_NOT_APPLIED") -Message "General rules should require a clear write-not-applied signal."
    Assert-True -Condition ($generalRule -match "PATH_AMBIGUOUS") -Message "General rules should require ambiguous path failure reporting."
    Assert-True -Condition ($generalRule -match "WORKSPACE_UNAVAILABLE") -Message "General rules should require workspace discovery failure reporting."
    Assert-True -Condition ($generalRule -match "APPLY_TARGET_MISMATCH") -Message "General rules should require apply target mismatch reporting."
    Assert-True -Condition ($generalRule -match "create_new_file") -Message "General rules should cover duplicate approval mitigation for create_new_file."
    Assert-True -Condition ($generalRule -match "edit_file") -Message "General rules should reject printed edit-call text without applied changes."
    Assert-True -Condition ($generalRule -match "Keep validation labels consistent with evidence") -Message "General rules should require status/failure consistency."
    Assert-True -Condition ($generalRule -match "no file is open") -Message "General rules should handle no-active-file workspace discovery."
    Assert-True -Condition ($generalRule -match "src/main\.py") -Message "General rules should guard against unrelated apply targets."
    Assert-True -Condition ($generalRule -match "current workspace root") -Message "General rules should define current workspace root path resolution."
    Assert-True -Condition ($generalRule -match "src/README\.md") -Message "General rules should guard against wrong-folder README creation."
    Assert-True -Condition ($generalRule -match "git diff") -Message "General rules should require diff verification after edits."
    Assert-True -Condition ($generalRule -match "external shell or git check") -Message "General rules should require external write verification for readiness."
    Assert-True -Condition ($generalRule -match "typical") -Message "General rules should forbid typical-pattern implementation guesses."
    Assert-True -Condition ($generalRule -match "Select-String") -Message "General rules should include PowerShell-native search guidance."
    Assert-True -Condition ($generalRule -match "write tools are unavailable") -Message "General rules should require clear write-tool failure reporting."
    Assert-True -Condition ($generalRule -match "I can't directly edit files") -Message "General rules should prohibit false refusal-to-edit responses."
    Assert-True -Condition ($toolModes -match "Platform-Aware Commands") -Message "Tool-use docs should include platform-aware command guidance."
    Assert-True -Condition ($toolModes -match "READ_TOOLS_UNAVAILABLE") -Message "Tool-use docs should define the read-tools unavailable signal."
    Assert-True -Condition ($toolModes -match "WRITE_TOOLS_UNAVAILABLE") -Message "Tool-use docs should define the write-tools unavailable signal."
    Assert-True -Condition ($toolModes -match "WRITE_NOT_APPLIED") -Message "Tool-use docs should define the write-not-applied signal."
    Assert-True -Condition ($toolModes -match "PATH_AMBIGUOUS") -Message "Tool-use docs should define the ambiguous target path signal."
    Assert-True -Condition ($toolModes -match "WORKSPACE_UNAVAILABLE") -Message "Tool-use docs should define workspace discovery failure."
    Assert-True -Condition ($toolModes -match "APPLY_TARGET_MISMATCH") -Message "Tool-use docs should define apply target mismatch."
    Assert-True -Condition ($toolModes -match "create_new_file") -Message "Tool-use docs should include create_new_file guidance for existing-file validation."
    Assert-True -Condition ($toolModes -match "DUPLICATE_APPROVALS") -Message "Tool-use docs should define duplicate approval handling."
    Assert-True -Condition ($toolModes -match "DUPLICATE_CONTENT") -Message "Tool-use docs should define duplicate content handling."
    Assert-True -Condition ($toolModes -match "opened repository root or current folder") -Message "Tool-use docs should require current-folder path resolution."
    Assert-True -Condition ($toolModes -match "continue-agent-write-test\.md") -Message "Tool-use docs should include approved-write smoke test."
    Assert-True -Condition ($toolModes -match "Assistant-only readback is not enough") -Message "Tool-use docs should require external verification beyond assistant readback."
    Assert-True -Condition ($toolModes -match "Test-Path") -Message "Tool-use docs should include Windows write verification."
    Assert-True -Condition ($toolModes -match "test -f") -Message "Tool-use docs should include Linux/macOS write verification."
    Assert-True -Condition ($approvedChanges -match "Safe write smoke-test prompt") -Message "Approved changes docs should include write smoke-test prompt."
    Assert-True -Condition ($approvedChanges -match "PATH_AMBIGUOUS") -Message "Approved changes docs should cover ambiguous target paths."
    Assert-True -Condition ($approvedChanges -match "git diff") -Message "Approved changes docs should require diff inspection."
    Assert-True -Condition ($approvedChanges -match "Assistant-only readback is not enough") -Message "Approved changes docs should require external write verification."
    Assert-True -Condition ($approvedChanges -match "Test-Path") -Message "Approved changes docs should include Windows write verification."
    Assert-True -Condition ($approvedChanges -match "test -f") -Message "Approved changes docs should include Linux/macOS write verification."
    Assert-True -Condition ($approvedChanges -match "Remove-Item") -Message "Approved changes docs should include Windows cleanup."
    Assert-True -Condition ($readme -match "write tools are not validated yet") -Message "README should explain unvalidated write-tool behavior."
    Assert-True -Condition ($readme -match "read file contents") -Message "README should require content-read validation before real code changes."
    Assert-True -Condition ($readme -match "git diff -- <file>") -Message "README should require user diff verification after approved writes."
    Assert-True -Condition ($readme -match "currently opened repository folder") -Message "README should explain current-folder path resolution."
    Assert-True -Condition ($readme -match "WORKSPACE_UNAVAILABLE") -Message "README should reference workspace discovery failure guidance."
    Assert-True -Condition ($readme -match "APPLY_TARGET_MISMATCH") -Message "README should reference apply target mismatch guidance."
    Assert-True -Condition ($readme -match "create_new_file") -Message "README should mention create_new_file exclusion for existing-file write tests."
    Assert-True -Condition ($readme -match "Two approval prompts") -Message "README should cover duplicate approval prompts."
    Assert-True -Condition ($readme -match "edit_file") -Message "README should mention printed edit-call text without real changes."
    Assert-True -Condition ($readme -match "created and read back a file") -Message "README should cover false positive write readback."
    Assert-True -Condition ($readme -match "READ_TOOLS_UNAVAILABLE.*read-only tool validated") -Message "README should explain failure signals cannot be successful status labels."
    Assert-True -Condition ($readme -match "ModelLanes") -Message "README should document model lanes installer option."
    Assert-True -Condition ($readme -match "1 - WRITE SAFE") -Message "README should describe WRITE SAFE lane guidance."

    $troubleshootingPath = Join-Path $repoRoot "docs/troubleshooting.md"
    $troubleshooting = Get-Content -LiteralPath $troubleshootingPath -Raw
    Assert-True -Condition ($troubleshooting -match "Agent Says It Cannot Edit Files") -Message "Troubleshooting should cover refusal-to-edit behavior."
    Assert-True -Condition ($troubleshooting -match "WRITE_TOOLS_UNAVAILABLE") -Message "Troubleshooting should document the write-tools unavailable signal."
    Assert-True -Condition ($troubleshooting -match "Agent Lists Files But Cannot Read Or Edit Them") -Message "Troubleshooting should cover partial tool-access failure."
    Assert-True -Condition ($troubleshooting -match "READ_TOOLS_UNAVAILABLE") -Message "Troubleshooting should document the read-tools unavailable signal."
    Assert-True -Condition ($troubleshooting -match "Agent Claims A Change But Git Diff Is Empty") -Message "Troubleshooting should cover claimed-but-missing writes."
    Assert-True -Condition ($troubleshooting -match "WRITE_NOT_APPLIED") -Message "Troubleshooting should document the write-not-applied signal."
    Assert-True -Condition ($troubleshooting -match "Test-Path") -Message "Troubleshooting should include external file existence verification."
    Assert-True -Condition ($troubleshooting -match "Assistant-only readback is not enough") -Message "Troubleshooting should warn against assistant-only readback."
    Assert-True -Condition ($troubleshooting -match "Agent Creates A File In The Wrong Folder") -Message "Troubleshooting should cover wrong-folder file creation."
    Assert-True -Condition ($troubleshooting -match "PATH_AMBIGUOUS") -Message "Troubleshooting should document ambiguous target path handling."
    Assert-True -Condition ($troubleshooting -match "Agent Says No File Is Open And Asks For A Path") -Message "Troubleshooting should cover no-active-file path requests."
    Assert-True -Condition ($troubleshooting -match "WORKSPACE_UNAVAILABLE") -Message "Troubleshooting should document workspace discovery failure handling."
    Assert-True -Condition ($troubleshooting -match "Apply Target Does Not Match The Requested File") -Message "Troubleshooting should cover apply target mismatches."
    Assert-True -Condition ($troubleshooting -match "APPLY_TARGET_MISMATCH") -Message "Troubleshooting should document apply target mismatch handling."
    Assert-True -Condition ($troubleshooting -match "Duplicate Approval Prompts Or Duplicate Content") -Message "Troubleshooting should cover duplicate approval prompts."
    Assert-True -Condition ($troubleshooting -match "DUPLICATE_APPROVALS") -Message "Troubleshooting should document duplicate approval handling."
    Assert-True -Condition ($troubleshooting -match "DUPLICATE_CONTENT") -Message "Troubleshooting should document duplicate content handling."
    Assert-True -Condition ($troubleshooting -match "edit_file") -Message "Troubleshooting should cover printed edit-call text without a diff."
    Assert-True -Condition ($troubleshooting -match "read-only listing only") -Message "Troubleshooting should classify list-only access separately from validated reads."

    $localModelSelectionPath = Join-Path $repoRoot "docs/local-model-selection.md"
    $localModelSelection = Get-Content -LiteralPath $localModelSelectionPath -Raw
    Assert-True -Condition ($localModelSelection -match "Model Lanes") -Message "Local model selection docs should include model lanes guidance."
    Assert-True -Condition ($localModelSelection -match "Why These Profiles") -Message "Local model selection docs should explain why the default profiles were chosen."
    Assert-True -Condition ($localModelSelection -match "WRITE SAFE") -Message "Local model selection docs should describe WRITE SAFE lane."
    Assert-True -Condition ($localModelSelection -match "PLAN ONLY") -Message "Local model selection docs should describe PLAN ONLY lane."
    Assert-True -Condition ($localModelSelection -match "DEEP REVIEW") -Message "Local model selection docs should describe DEEP REVIEW lane."
    Assert-True -Condition ($localModelSelection -match "edit.*apply") -Message "Local model selection docs should explain edit/apply lane restrictions."
}

Invoke-PackTest "Continue file references are relative and resolvable" {
    $configPath = Join-Path $repoRoot ".continue/config.yaml"
    $config = Get-Content -LiteralPath $configPath -Raw
    $fileRefs = [regex]::Matches($config, "file://\.\/([^`r`n]+)") | ForEach-Object {
        $_.Groups[1].Value.Trim()
    }

    Assert-True -Condition ($fileRefs.Count -gt 0) -Message "Config should include local file references."

    foreach ($ref in $fileRefs) {
        Assert-True -Condition (-not [System.IO.Path]::IsPathFullyQualified($ref)) -Message "File reference should not be absolute: $ref"
        Assert-True -Condition ($ref -notmatch "(^|/)\.\.(/|$)") -Message "File reference should not traverse outside .continue: $ref"

        $target = Join-Path (Join-Path $repoRoot ".continue") $ref
        Assert-True -Condition (Test-Path -LiteralPath $target) -Message "File reference does not resolve: $ref"
    }
}

Invoke-PackTest "runtime context generation captures useful files and excludes build output" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-runtime-context-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRepo "src") | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRepo "bin") | Out-Null

        "# Sample" | Set-Content -LiteralPath (Join-Path $tempRepo "README.md")
        "public class App { }" | Set-Content -LiteralPath (Join-Path $tempRepo "src/App.cs")
        "public class BuildOutput { }" | Set-Content -LiteralPath (Join-Path $tempRepo "bin/Ignored.cs")
        "<Project Sdk=`"Microsoft.NET.Sdk`" />" | Set-Content -LiteralPath (Join-Path $tempRepo "Sample.csproj")

        $outputPath = Join-Path $tempRepo "runtime-context.md"
        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/generate-runtime-context.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-OutputPath", $outputPath)

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Runtime context generation should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $outputPath) -Message "Runtime context file should be created."

        $context = Get-Content -LiteralPath $outputPath -Raw
        Assert-True -Condition ($context -match "# Runtime Repository Context") -Message "Runtime context should include the expected title."
        Assert-True -Condition ($context -match "README.md") -Message "Runtime context should include top-level docs."
        Assert-True -Condition ($context -match "src/App.cs") -Message "Runtime context should include source files."
        Assert-True -Condition ($context -notmatch "bin/Ignored.cs") -Message "Runtime context should exclude build output."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "runtime context generation fails for missing target repository" {
    $missingPath = Join-Path ([System.IO.Path]::GetTempPath()) "continue-missing-repo-$([guid]::NewGuid())"
    $result = Invoke-CommandCapture `
        -FilePath (Join-Path $repoRoot "scripts/generate-runtime-context.ps1") `
        -Arguments @("-TargetRepo", $missingPath)

    Assert-True -Condition ($result.ExitCode -ne 0) -Message "Runtime context generation should fail for a missing target path."
    Assert-True -Condition ($result.Output -match "Target repository path does not exist") -Message "Missing target error should be reported."
}

Invoke-PackTest "runtime context generation accepts shell-friendly argument aliases" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-runtime-context-alias-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRepo "src") | Out-Null
        "# Sample" | Set-Content -LiteralPath (Join-Path $tempRepo "README.md")
        "public class App { }" | Set-Content -LiteralPath (Join-Path $tempRepo "src/App.cs")

        $outputPath = Join-Path $tempRepo "runtime-context.alias.md"
        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/generate-runtime-context.ps1") `
            -Arguments @("--target-repo", $tempRepo, "--output-path", $outputPath)

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Runtime context generation should accept shell-friendly aliases."
        Assert-True -Condition (Test-Path -LiteralPath $outputPath) -Message "Runtime context file should be created when aliases are used."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script dry run does not modify target repository" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-dry-run-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-DryRun")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install dry run should succeed."
        Assert-True -Condition ($result.Output -match "Dry run only") -Message "Dry-run output should identify that no files were changed."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $tempRepo ".continue"))) -Message "Dry run should not create .continue."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script auto model config dry run is explicit" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-auto-model-dry-run-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-DryRun", "-AutoModelConfig")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install dry run with auto model config should succeed."
        Assert-True -Condition ($result.Output -match "Would generate \.continue/config\.local\.yaml") -Message "Dry run should explain local model config generation."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $tempRepo ".continue"))) -Message "Dry run should not create .continue."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script model lanes generate scoped roles" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-model-lanes-test-$([guid]::NewGuid())"
    $globalConfigPath = Join-Path $tempRepo "global-config.yaml"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-ModelLanes", "-GlobalConfig", "-GlobalConfigPath", $globalConfigPath, "-GlobalConfigApiBase", "http://127.0.0.1:11434")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install with model lanes should succeed."

        $localConfigPath = Join-Path $tempRepo ".continue/config.local.yaml"
        Assert-True -Condition (Test-Path -LiteralPath $localConfigPath) -Message "Model lanes should generate local config."
        Assert-True -Condition (Test-Path -LiteralPath $globalConfigPath) -Message "Model lanes global config should be written."

        $localConfig = Get-Content -LiteralPath $localConfigPath -Raw
        $globalConfig = Get-Content -LiteralPath $globalConfigPath -Raw

        Assert-True -Condition ($localConfig -match "1 - WRITE SAFE - qwen3\.5:9b") -Message "Model lanes should include WRITE SAFE lane."
        Assert-True -Condition ($localConfig -match "2 - PLAN ONLY - devstral-small-2:24b") -Message "Model lanes should include PLAN ONLY lane."
        Assert-True -Condition ($localConfig -match "3 - DEEP REVIEW - qwen3-coder:30b") -Message "Model lanes should include DEEP REVIEW lane."
        Assert-True -Condition ($localConfig -match "Ollama Nomic Embed") -Message "Model lanes should keep a separate embedding model."
        Assert-True -Condition ($localConfig -notmatch "4 - ") -Message "Model lanes should include only three Agent lanes."
        Assert-True -Condition ($localConfig -notmatch "5 - ") -Message "Embedding should not be labeled as an Agent lane."
        Assert-True -Condition ($localConfig -match '(?s)1 - WRITE SAFE - qwen3\.5:9b.*roles:\s*\r?\n\s*- chat\s*\r?\n\s*- edit\s*\r?\n\s*- apply') -Message "WRITE SAFE lane should include chat/edit/apply roles."
        Assert-True -Condition ($localConfig -match '(?s)2 - PLAN ONLY - devstral-small-2:24b.*roles:\s*\r?\n\s*- chat') -Message "PLAN ONLY lane should include chat role."
        Assert-True -Condition ($localConfig -notmatch '(?s)2 - PLAN ONLY - devstral-small-2:24b.*roles:.*- edit') -Message "PLAN ONLY lane should not include edit role."
        Assert-True -Condition ($localConfig -notmatch '(?s)3 - DEEP REVIEW - qwen3-coder:30b.*roles:.*- apply') -Message "DEEP REVIEW lane should not include apply role."
        Assert-True -Condition ($globalConfig -match "apiBase: http://127\.0\.0\.1:11434") -Message "Global model lanes config should include requested apiBase."
    } finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script global config dry run is explicit" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-global-dry-run-test-$([guid]::NewGuid())"
    $globalConfigPath = Join-Path ([System.IO.Path]::GetTempPath()) "continue-global-config-dry-run-$([guid]::NewGuid()).yaml"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-DryRun", "-GlobalConfig", "-GlobalConfigPath", $globalConfigPath, "-GlobalConfigApiBase", "http://127.0.0.1:11434")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install dry run with global config should succeed."
        Assert-True -Condition ($result.Output -match "Would write global Continue config") -Message "Dry run should explain global config generation."
        Assert-True -Condition ($result.Output -match "Would omit rules from generated global config") -Message "Dry run should explain duplicate-rule-safe default."
        Assert-True -Condition (-not (Test-Path -LiteralPath $globalConfigPath)) -Message "Dry run should not create global config."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $tempRepo ".continue"))) -Message "Dry run should not create .continue."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $globalConfigPath -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script backs up existing .continue and excludes local config" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-test-$([guid]::NewGuid())"

    try {
        $targetContinue = Join-Path $tempRepo ".continue"
        New-Item -ItemType Directory -Force -Path $targetContinue | Out-Null
        "old config" | Set-Content -LiteralPath (Join-Path $targetContinue "config.yaml")

        $sourceLocalConfig = Join-Path $repoRoot ".continue/config.local.test.yaml"
        "local: true" | Set-Content -LiteralPath $sourceLocalConfig

        try {
            $result = Invoke-CommandCapture `
                -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
                -Arguments @("-TargetRepo", $tempRepo)

            Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install should succeed."
            Assert-True -Condition ($result.Output -match "Install complete\.") -Message "Install success message should be present."
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $targetContinue "config.yaml")) -Message "Installed config should exist."
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $targetContinue "prompts/repository-discovery.md")) -Message "Installed prompts should exist."
            Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $targetContinue "config.local.test.yaml"))) -Message "Local config overrides should not be installed."

            $backupDirs = Get-ChildItem -LiteralPath $tempRepo -Force -Directory |
                Where-Object { $_.Name -like ".continue.backup-*" }
            Assert-Equal -Actual $backupDirs.Count -Expected 1 -Message "Install should create one backup folder."
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $backupDirs[0].FullName "config.yaml")) -Message "Backup should contain previous config."
        }
        finally {
            Remove-Item -LiteralPath $sourceLocalConfig -Force -ErrorAction SilentlyContinue
        }
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script writes global config with target references and omits rules by default" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-global-test-$([guid]::NewGuid())"
    $globalConfigPath = Join-Path ([System.IO.Path]::GetTempPath()) "continue-global-config-test-$([guid]::NewGuid()).yaml"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-GlobalConfig", "-GlobalConfigPath", $globalConfigPath, "-GlobalConfigApiBase", "http://127.0.0.1:11434")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install with global config should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $globalConfigPath) -Message "Global config should be created."

        $globalConfig = Get-Content -LiteralPath $globalConfigPath -Raw
        Assert-True -Condition ($globalConfig -match "Global Continue config generated") -Message "Global config should include generated header."
        Assert-True -Condition ($globalConfig -match "apiBase: http://127\.0\.0\.1:11434") -Message "Global config should include requested Ollama apiBase."
        Assert-True -Condition ($globalConfig -match "file://[A-Za-z]:/") -Message "Global config should use Continue-friendly Windows absolute file references."
        Assert-True -Condition ($globalConfig -notmatch "file:///[A-Za-z]:/") -Message "Global config should not use triple-slash Windows file references."
        Assert-True -Condition ($globalConfig -notmatch "rules/general\.md") -Message "Global config should omit rules by default to avoid duplicate-rule warnings."
        Assert-True -Condition ($globalConfig -notmatch "(?m)^rules:\s*$") -Message "Global config should not include a rules section by default."
        Assert-True -Condition ($globalConfig -match "prompts/repository-discovery\.md") -Message "Global config should reference installed prompts."
        Assert-True -Condition ($globalConfig -notmatch "file://\./") -Message "Global config should not keep project-relative file references."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $globalConfigPath -Force -ErrorAction SilentlyContinue
        Get-ChildItem -LiteralPath ([System.IO.Path]::GetTempPath()) -Filter "$(Split-Path -Leaf $globalConfigPath).backup-*" -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script can include rules in global config by explicit opt-in" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-global-rules-test-$([guid]::NewGuid())"
    $globalConfigPath = Join-Path ([System.IO.Path]::GetTempPath()) "continue-global-config-rules-test-$([guid]::NewGuid()).yaml"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-GlobalConfig", "-GlobalConfigPath", $globalConfigPath, "-GlobalConfigIncludeRules")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install with global config rules opt-in should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $globalConfigPath) -Message "Global config should be created."

        $globalConfig = Get-Content -LiteralPath $globalConfigPath -Raw
        Assert-True -Condition ($globalConfig -match "(?m)^rules:\s*$") -Message "Global config should include rules section when explicitly requested."
        Assert-True -Condition ($globalConfig -match "rules/general\.md") -Message "Global config should reference installed rules when explicitly requested."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $globalConfigPath -Force -ErrorAction SilentlyContinue
        Get-ChildItem -LiteralPath ([System.IO.Path]::GetTempPath()) -Filter "$(Split-Path -Leaf $globalConfigPath).backup-*" -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script refuses to target pack repository" {
    $result = Invoke-CommandCapture `
        -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
        -Arguments @("-TargetRepo", $repoRoot)

    Assert-True -Condition ($result.ExitCode -ne 0) -Message "Install should fail when targeting the pack repository."
    Assert-True -Condition ($result.Output -match "Target repository must be different") -Message "Expected self-targeting error should be reported."
}

Invoke-PackTest "install script accepts shell-friendly argument aliases" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-alias-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("--target-repo", $tempRepo, "--dry-run", "--auto-model-config", "--global-config", "--global-config-path", (Join-Path $tempRepo "global-config.yaml"))

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install dry run with shell-friendly aliases should succeed."
        Assert-True -Condition ($result.Output -match "Dry run only") -Message "Dry-run output should be present."
        Assert-True -Condition ($result.Output -match "Would generate \.continue/config\.local\.yaml") -Message "Auto model config alias should be accepted."
        Assert-True -Condition ($result.Output -match "Would write global Continue config") -Message "Global config alias should be accepted."
        Assert-True -Condition ($result.Output -match "Would omit rules from generated global config") -Message "Global config should default to omitting rules."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $tempRepo ".continue"))) -Message "Alias dry run should not create .continue."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install wrapper scripts exist and call shared Bash installer" {
    $wrapperNames = @(
        "install-continue-pack.linux.sh",
        "install-continue-pack.macos.sh"
    )

    foreach ($wrapperName in $wrapperNames) {
        $wrapperPath = Join-Path $repoRoot "scripts/$wrapperName"
        Assert-True -Condition (Test-Path -LiteralPath $wrapperPath) -Message "$wrapperName should exist."

        $content = Get-Content -LiteralPath $wrapperPath -Raw
        Assert-True -Condition ($content -match "install-continue-pack\.shared\.sh") -Message "$wrapperName should call the shared Bash installer."
        Assert-True -Condition ($content -notmatch "pwsh") -Message "$wrapperName should not require pwsh."
    }
}

Invoke-PackTest "shell wrapper scripts are executable in git" {
    $modeRows = & git -C $repoRoot ls-files -s "scripts/*.sh"
    Assert-True -Condition ($LASTEXITCODE -eq 0) -Message "git ls-files should succeed for shell scripts."
    Assert-True -Condition ($modeRows.Count -gt 0) -Message "Repository should include shell scripts."

    foreach ($row in $modeRows) {
        $parts = $row -split "\s+"
        $mode = $parts[0]
        $path = $parts[-1]

        Assert-Equal -Actual $mode -Expected "100755" -Message "Shell script should be executable in git: $path"
    }
}

Invoke-PackTest "runtime context and validation wrapper scripts call shared Bash scripts" {
    $wrappers = @(
        @{
            Name = "generate-runtime-context.linux.sh"
            Target = "generate-runtime-context.shared.sh"
        },
        @{
            Name = "generate-runtime-context.macos.sh"
            Target = "generate-runtime-context.shared.sh"
        },
        @{
            Name = "run-runtime-validation.linux.sh"
            Target = "run-runtime-validation.shared.sh"
        },
        @{
            Name = "run-runtime-validation.macos.sh"
            Target = "run-runtime-validation.shared.sh"
        },
        @{
            Name = "pull-local-agent-models.linux.sh"
            Target = "pull-local-agent-models.shared.sh"
        },
        @{
            Name = "pull-local-agent-models.macos.sh"
            Target = "pull-local-agent-models.shared.sh"
        },
        @{
            Name = "test-local-agent-models.linux.sh"
            Target = "test-local-agent-models.shared.sh"
        },
        @{
            Name = "test-local-agent-models.macos.sh"
            Target = "test-local-agent-models.shared.sh"
        }
    )

    foreach ($wrapper in $wrappers) {
        $wrapperPath = Join-Path $repoRoot "scripts/$($wrapper.Name)"
        Assert-True -Condition (Test-Path -LiteralPath $wrapperPath) -Message "$($wrapper.Name) should exist."

        $content = Get-Content -LiteralPath $wrapperPath -Raw
        Assert-True -Condition ($content -match [regex]::Escape($wrapper.Target)) -Message "$($wrapper.Name) should call $($wrapper.Target)."
        Assert-True -Condition ($content -notmatch "pwsh") -Message "$($wrapper.Name) should not require pwsh."
    }
}

Invoke-PackTest "validation and test wrapper scripts call shared Bash scripts" {
    $wrappers = @(
        @{
            Name = "validate-pack.linux.sh"
            Target = "validate-pack.shared.sh"
        },
        @{
            Name = "validate-pack.macos.sh"
            Target = "validate-pack.shared.sh"
        },
        @{
            Name = "test-pack.linux.sh"
            Target = "test-pack.shared.sh"
        },
        @{
            Name = "test-pack.macos.sh"
            Target = "test-pack.shared.sh"
        }
    )

    foreach ($wrapper in $wrappers) {
        $wrapperPath = Join-Path $repoRoot "scripts/$($wrapper.Name)"
        Assert-True -Condition (Test-Path -LiteralPath $wrapperPath) -Message "$($wrapper.Name) should exist."

        $content = Get-Content -LiteralPath $wrapperPath -Raw
        Assert-True -Condition ($content -match [regex]::Escape($wrapper.Target)) -Message "$($wrapper.Name) should call $($wrapper.Target)."
        Assert-True -Condition ($content -notmatch "pwsh") -Message "$($wrapper.Name) should not require pwsh."
    }
}

Invoke-PackTest "runtime validation fails before CLI execution for missing target repository" {
    $missingPath = Join-Path ([System.IO.Path]::GetTempPath()) "continue-runtime-validation-missing-$([guid]::NewGuid())"
    $result = Invoke-CommandCapture `
        -FilePath (Join-Path $repoRoot "scripts/run-runtime-validation.ps1") `
        -Arguments @("-TargetRepo", $missingPath)

    Assert-True -Condition ($result.ExitCode -ne 0) -Message "Runtime validation should fail for a missing target path."
    Assert-True -Condition ($result.Output -match "Target repository path does not exist") -Message "Missing target error should be reported."
}

Invoke-PackTest "review prompts include configuration-pack guardrails" {
    $promptNames = @(
        "architecture-review.md",
        "security-review.md",
        "code-review.md",
        "release-readiness.md",
        "refactoring-planner.md"
    )

    foreach ($promptName in $promptNames) {
        $promptPath = Join-Path $repoRoot ".continue/prompts/$promptName"
        $content = Get-Content -LiteralPath $promptPath -Raw

        Assert-True -Condition ($content -match "configuration packs") -Message "$promptName should mention configuration-pack repositories."
        Assert-True -Condition ($content -match "repository type") -Message "$promptName should require repository type classification."
    }
}

Invoke-PackTest "configuration-pack fixture documents bad recommendations" {
    $fixturePath = Join-Path $repoRoot "examples/fixtures/config-pack-review-input.md"
    $content = Get-Content -LiteralPath $fixturePath -Raw

    Assert-True -Condition ($content -match "not an application codebase") -Message "Fixture should define the non-application scenario."
    Assert-True -Condition ($content -match "Known Bad Recommendations") -Message "Fixture should document known bad recommendations."
    Assert-True -Condition ($content -match "npx @continuedev/cli") -Message "Fixture should protect the documented npx fallback."
}

if ($failed) {
    Write-Host "Test run failed. $testCount tests executed." -ForegroundColor Red
    exit 1
}

Write-Host "Test run passed. $testCount tests executed." -ForegroundColor Green
exit 0
