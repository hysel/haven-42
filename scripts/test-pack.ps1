param(
    [string]$ExpectedVersion = "0.2.0"
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


Invoke-PackTest "release packaging scripts define archives, checksums, and sanitized dry runs" {
    $psScriptPath = Join-Path $repoRoot "scripts/build-release-package.ps1"
    $linuxScriptPath = Join-Path $repoRoot "scripts/build-release-package.linux.sh"
    $macScriptPath = Join-Path $repoRoot "scripts/build-release-package.macos.sh"
    $sharedScriptPath = Join-Path $repoRoot "scripts/build-release-package.shared.sh"
    $releaseDocPath = Join-Path $repoRoot "docs/release.md"
    $gitignorePath = Join-Path $repoRoot ".gitignore"

    Assert-True -Condition (Test-Path -LiteralPath $psScriptPath) -Message "PowerShell release packager should exist."
    Assert-True -Condition (Test-Path -LiteralPath $linuxScriptPath) -Message "Linux release packager wrapper should exist."
    Assert-True -Condition (Test-Path -LiteralPath $macScriptPath) -Message "macOS release packager wrapper should exist."
    Assert-True -Condition (Test-Path -LiteralPath $sharedScriptPath) -Message "Shared release packager should exist."

    $result = Invoke-CommandCapture -FilePath $psScriptPath -Arguments @("-Version", "0.2.0", "-DryRun", "-AllowDirty")
    Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "PowerShell release packager dry run should succeed."
    Assert-True -Condition ($result.Output -match "Release package plan") -Message "Dry run should print a release package plan."
    Assert-True -Condition ($result.Output -match "local-engineering-agent-pack-0\.2\.0\.zip") -Message "Dry run should name the Windows archive."
    Assert-True -Condition ($result.Output -match "\.sha256") -Message "Dry run should name a checksum file."
    Assert-True -Condition ($result.Output -match "Excluded: \.git, \.vscode, runtime-validation-output, dist, local configs") -Message "Dry run should explain excluded local files."

    $psScript = Get-Content -LiteralPath $psScriptPath -Raw
    $sharedScript = Get-Content -LiteralPath $sharedScriptPath -Raw
    $releaseDoc = Get-Content -LiteralPath $releaseDocPath -Raw
    $gitignore = Get-Content -LiteralPath $gitignorePath -Raw

    Assert-True -Condition ($psScript.Contains('git -C $repoRoot ls-files')) -Message "PowerShell packager should package tracked files."
    Assert-True -Condition ($psScript -match "Compress-Archive") -Message "PowerShell packager should create a zip archive."
    Assert-True -Condition ($psScript -match "Get-FileHash") -Message "PowerShell packager should create a SHA-256 checksum."
    Assert-True -Condition ($psScript -match "config\\.local") -Message "PowerShell packager should exclude local config files."
    Assert-True -Condition ($psScript -match "runtime-validation-output") -Message "PowerShell packager should exclude runtime validation output."
    Assert-True -Condition ($psScript -match "AllowDirty") -Message "PowerShell packager should require an explicit dirty-tree override."
    Assert-True -Condition ($sharedScript -match "tar -C") -Message "Shared packager should create a tar.gz archive."
    Assert-True -Condition ($sharedScript -match "sha256sum") -Message "Shared packager should support sha256sum."
    Assert-True -Condition ($sharedScript -match "shasum -a 256") -Message "Shared packager should support macOS shasum."
    Assert-True -Condition ($sharedScript -notmatch "mapfile") -Message "Shared packager should avoid Bash 4-only mapfile for macOS compatibility."
    Assert-True -Condition ($sharedScript -match "config\\.local") -Message "Shared packager should exclude local config files."
    Assert-True -Condition ($sharedScript -match "runtime-validation-output") -Message "Shared packager should exclude runtime validation output."
    Assert-True -Condition ($releaseDoc -match "Build Release Artifacts") -Message "Release docs should explain artifact creation."
    Assert-True -Condition ($releaseDoc -match "Verify Checksums") -Message "Release docs should explain checksum verification."
    Assert-True -Condition ($releaseDoc -match "build-release-package") -Message "Release docs should mention packaging scripts."
    Assert-True -Condition ($releaseDoc -match "GitHub Release") -Message "Release docs should explain GitHub release uploads."
    Assert-True -Condition ((Get-Content -LiteralPath $gitignorePath) -contains "dist/") -Message "dist output should be ignored."
}
Invoke-PackTest "evidence catalog has valid schema and sanitized links" {
    $catalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
    $docPath = Join-Path $repoRoot "docs/evidence-catalog.md"
    $allowedStatuses = @(
        "candidate-only",
        "plan-review-candidate",
        "read-only-tool-validated",
        "read-only-cli-validated",
        "approved-write-ready",
        "static-validated",
        "validated-by-tests",
        "partial-pass"
    )

    Assert-True -Condition (Test-Path -LiteralPath $catalogPath) -Message "Evidence catalog should exist."
    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Evidence catalog docs should exist."

    $lines = Get-Content -LiteralPath $catalogPath | Where-Object { $_.Trim().Length -gt 0 }
    Assert-True -Condition ($lines.Count -gt 1) -Message "Evidence catalog should include rows."
    Assert-Equal -Actual $lines[0] -Expected "area`tsubject`tsurface`tos`tmodel`tstatus`tevidence`tnotes" -Message "Evidence catalog header changed."

    $seenApprovedWrite = $false
    $seenCandidateOnly = $false
    $seenReadOnly = $false

    foreach ($line in $lines[1..($lines.Count - 1)]) {
        $parts = $line -split "`t", 8
        Assert-Equal -Actual $parts.Count -Expected 8 -Message "Evidence catalog row should have eight tab-delimited columns: $line"

        foreach ($part in $parts) {
            Assert-True -Condition ($part.Trim().Length -gt 0) -Message "Evidence catalog row contains an empty field: $line"
        }

        $status = $parts[5]
        $evidence = $parts[6]
        Assert-True -Condition ($status -in $allowedStatuses) -Message "Evidence catalog row has unsupported status: $line"
        Assert-True -Condition ($evidence -notmatch "^[A-Za-z]:|^/|\\") -Message "Evidence path should be repository-relative: $line"
        Assert-True -Condition ($evidence -notmatch "\.\.") -Message "Evidence path should not traverse directories: $line"
        Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot $evidence)) -Message "Evidence path should exist: $evidence"
        Assert-True -Condition ($line -notmatch "192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|localhost|itama|Users\\|OneDrive|customer|token|secret") -Message "Evidence catalog row should stay sanitized: $line"

        if ($status -eq "approved-write-ready") { $seenApprovedWrite = $true }
        if ($status -eq "candidate-only") { $seenCandidateOnly = $true }
        if ($status -eq "read-only-tool-validated") { $seenReadOnly = $true }
    }

    Assert-True -Condition $seenApprovedWrite -Message "Evidence catalog should include approved-write-ready evidence."
    Assert-True -Condition $seenCandidateOnly -Message "Evidence catalog should include candidate-only evidence."
    Assert-True -Condition $seenReadOnly -Message "Evidence catalog should include read-only tool evidence."

    $doc = Get-Content -LiteralPath $docPath -Raw
    Assert-True -Condition ($doc -match "config/evidence-catalog\.tsv") -Message "Evidence catalog docs should reference the TSV file."
    Assert-True -Condition ($doc -match "approved-write-ready") -Message "Evidence catalog docs should define approved-write-ready."
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
    Assert-True -Condition ($catalogText -match "simple-hardware default") -Message "Catalog should include the simple-hardware profile model."
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

Invoke-PackTest "online model discovery docs preserve offline local-first defaults" {
    $docPath = Join-Path $repoRoot "docs/online-model-discovery.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $selectionPath = Join-Path $repoRoot "docs/local-model-selection.md"
    $agentTestingPath = Join-Path $repoRoot "docs/local-agent-model-testing.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Online model discovery doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $selection = Get-Content -LiteralPath $selectionPath -Raw
    $agentTesting = Get-Content -LiteralPath $agentTestingPath -Raw

    Assert-True -Condition ($doc -match "optional") -Message "Online discovery doc should mark discovery optional."
    Assert-True -Condition ($doc -match "candidate model names only") -Message "Online discovery doc should limit output to candidate model names."
    Assert-True -Condition ($doc -match "default workflow stays offline") -Message "Online discovery doc should preserve offline default workflow."
    Assert-True -Condition ($doc -match "must not") -Message "Online discovery doc should define hard limits."
    Assert-True -Condition ($doc -match "Pull models automatically") -Message "Online discovery doc should prevent implicit model pulls."
    Assert-True -Condition ($doc -match "Mark a model as tool-safe") -Message "Online discovery doc should prevent false validation."
    Assert-True -Condition ($doc -match "private repository content") -Message "Online discovery doc should prohibit sending private context online."
    Assert-True -Condition ($doc -match "Approved-write ready") -Message "Online discovery doc should define validated status progression."
    Assert-True -Condition ($readme -match "docs/online-model-discovery.md") -Message "README should link online discovery doc."
    Assert-True -Condition ($selection -match "docs/online-model-discovery.md") -Message "Local model selection should reference online discovery doc."
    Assert-True -Condition ($agentTesting -match "do not discover newer") -Message "Local Agent testing should distinguish testing from discovery."
}

Invoke-PackTest "multi-repository validation docs define sanitized evidence workflow" {
    $docPath = Join-Path $repoRoot "docs/multi-repository-validation.md"
    $runtimeOutputVerificationPath = Join-Path $repoRoot "docs/runtime-output-verification.md"
    $templatePath = Join-Path $repoRoot "examples/multi-repository-validation.md"
    $readmePath = Join-Path $repoRoot "README.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Multi-repository validation doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $runtimeOutputVerificationPath) -Message "Runtime output verification doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $templatePath) -Message "Multi-repository validation evidence template should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $runtimeOutputVerification = Get-Content -LiteralPath $runtimeOutputVerificationPath -Raw
    $template = Get-Content -LiteralPath $templatePath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw

    Assert-True -Condition ($doc -match "Repository Categories") -Message "Multi-repository validation doc should define repository categories."
    Assert-True -Condition ($doc -match "Legacy \.NET") -Message "Multi-repository validation doc should cover legacy .NET repositories."
    Assert-True -Condition ($doc -match "Modern \.NET") -Message "Multi-repository validation doc should cover modern .NET repositories."
    Assert-True -Condition ($doc -match "Documentation or configuration pack") -Message "Multi-repository validation doc should cover documentation/config repositories."
    Assert-True -Condition ($doc -match "Frontend application") -Message "Multi-repository validation doc should cover frontend repositories."
    Assert-True -Condition ($doc -match "Script or tooling repository") -Message "Multi-repository validation doc should cover script/tooling repositories."
    Assert-True -Condition ($doc -match "clean git working tree") -Message "Multi-repository validation doc should require clean-tree validation."
    Assert-True -Condition ($doc -match "deterministic output verification") -Message "Multi-repository validation doc should require output verification."
    Assert-True -Condition ($doc -match "local sample repositories") -Message "Multi-repository validation doc should allow generated local samples."
    Assert-True -Condition ($doc -match "examples/multi-repository-validation.md") -Message "Multi-repository validation doc should reference the evidence template."
    Assert-True -Condition ($doc -match "docs/runtime-output-verification.md") -Message "Multi-repository validation doc should reference runtime output verification."
    Assert-True -Condition ($doc -match "Do not record") -Message "Multi-repository validation doc should define sanitization limits."
    Assert-True -Condition ($doc -match "private repository names") -Message "Multi-repository validation doc should prohibit private repository names."
    Assert-True -Condition ($template -match "Multi-Repository Validation Evidence") -Message "Evidence template should have expected title."
    Assert-True -Condition ($template -match "Repository category") -Message "Evidence template should record repository category."
    Assert-True -Condition ($template -match "Clean git tree before validation") -Message "Evidence template should record clean-tree status."
    Assert-True -Condition ($template -match "Failure signals") -Message "Evidence template should record failure signals."
    Assert-True -Condition ($template -match "Sanitization Checklist") -Message "Evidence template should include sanitization checklist."
    Assert-True -Condition ($template -match "No private repository names") -Message "Evidence template should prohibit private repository names."
    Assert-True -Condition ($readme -match "docs/multi-repository-validation.md") -Message "README should link multi-repository validation doc."
    Assert-True -Condition ($readme -match "docs/runtime-output-verification.md") -Message "README should link runtime output verification doc."
    Assert-True -Condition ($readme -match "examples/multi-repository-validation.md") -Message "README should link multi-repository validation template."
    Assert-True -Condition ($runtimeOutputVerification -match "filename") -Message "Runtime output verification doc should describe filename checks."
    Assert-True -Condition ($runtimeOutputVerification -match "unsafe mechanical migration patterns") -Message "Runtime output verification doc should describe unsafe migration checks."
    Assert-True -Condition ($runtimeOutputVerification -match "current-source verification") -Message "Runtime output verification doc should describe source verification qualifiers."
}



Invoke-PackTest "sample repository factory validation evidence is sanitized" {
    $evidencePath = Join-Path $repoRoot "examples/sample-repository-factory-validation.md"
    $docPath = Join-Path $repoRoot "docs/sample-repository-factory.md"
    $readmePath = Join-Path $repoRoot "README.md"

    Assert-True -Condition (Test-Path -LiteralPath $evidencePath) -Message "Sample factory validation evidence should exist."

    $evidence = Get-Content -LiteralPath $evidencePath -Raw
    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw

    Assert-True -Condition ($evidence -match "Sample Repository Factory Validation Evidence") -Message "Evidence should have expected title."
    Assert-True -Condition ($evidence -match "python-api") -Message "Evidence should include python-api sample."
    Assert-True -Condition ($evidence -match "typescript-frontend") -Message "Evidence should include typescript-frontend sample."
    Assert-True -Condition ($evidence -match "Runtime context generation") -Message "Evidence should mention runtime context generation."
    Assert-True -Condition ($evidence -match "does not prove model or editor Agent behavior") -Message "Evidence should avoid overstating Agent validation."
    Assert-True -Condition ($evidence -match "No private local paths") -Message "Evidence should include sanitization checklist."
    Assert-True -Condition ($doc -match "examples/sample-repository-factory-validation\.md") -Message "Sample factory doc should link evidence."
    Assert-True -Condition ($readme -match "examples/sample-repository-factory-validation\.md") -Message "README should link evidence."
}

Invoke-PackTest "sample repository factory docs define generated fixtures" {
    $docPath = Join-Path $repoRoot "docs/sample-repository-factory.md"
    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath (Join-Path $repoRoot "README.md") -Raw
    $roadmap = Get-Content -LiteralPath (Join-Path $repoRoot "ROADMAP.md") -Raw

    Assert-True -Condition ($doc -match "python-api") -Message "Sample factory doc should list python-api."
    Assert-True -Condition ($doc -match "typescript-frontend") -Message "Sample factory doc should list typescript-frontend."
    Assert-True -Condition ($doc -match "generate-sample-repositories\.ps1") -Message "Sample factory doc should include the Windows script."
    Assert-True -Condition ($doc -match "generate-sample-repositories\.linux\.sh") -Message "Sample factory doc should include the Linux script."
    Assert-True -Condition ($doc -match "generate-sample-repositories\.macos\.sh") -Message "Sample factory doc should include the macOS script."
    Assert-True -Condition ($doc -match "production starter projects") -Message "Sample factory doc should include guardrails."
    Assert-True -Condition ($readme -match "docs/sample-repository-factory\.md") -Message "README should link to sample factory docs."
    Assert-True -Condition ($roadmap -match "Milestone 16: Sample Repository Factory") -Message "Roadmap should include Milestone 16."
}

Invoke-PackTest "agent surface docs define portability boundary" {
    $docPath = Join-Path $repoRoot "docs/agent-surface-options.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Agent surface options doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw

    Assert-True -Condition ($doc -match "Continue is the first supported surface") -Message "Agent surface doc should keep Continue as the current supported surface."
    Assert-True -Condition ($doc -match "Candidate means") -Message "Agent surface doc should define candidate status."
    Assert-True -Condition ($doc -match "Approved-write ready") -Message "Agent surface doc should define approved-write readiness."
    Assert-True -Condition ($doc -match "Cline") -Message "Agent surface doc should include Cline as a candidate."
    Assert-True -Condition ($doc -match "Aider") -Message "Agent surface doc should include Aider as a candidate."
    Assert-True -Condition ($doc -match "Non-Enterprise Use") -Message "Agent surface doc should address non-enterprise users."
    Assert-True -Condition ($readme -match "docs/agent-surface-options.md") -Message "README should link agent surface options."
    Assert-True -Condition ($roadmap -match "Milestone 14: Agent Surface Portability And Broader Audience") -Message "Roadmap should include Milestone 14."
}


Invoke-PackTest "language support docs define staged multi-language boundary" {
    $docPath = Join-Path $repoRoot "docs/language-support.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Language support doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw

    Assert-True -Condition ($doc -match "\.NET.*most mature") -Message "Language support doc should identify .NET as the current mature path."
    Assert-True -Condition ($doc -match "Python") -Message "Language support doc should include Python."
    Assert-True -Condition ($doc -match "JavaScript / TypeScript") -Message "Language support doc should include JavaScript/TypeScript."
    Assert-True -Condition ($doc -match "Infrastructure as Code") -Message "Language support doc should include Infrastructure as Code."
    Assert-True -Condition ($doc -match "Do not apply \.NET-specific advice") -Message "Language support doc should guard against .NET advice in non-.NET repos."
    Assert-True -Condition ($readme -match "docs/language-support.md") -Message "README should link language support doc."
    Assert-True -Condition ($roadmap -match "Milestone 15: Multi-Language Engineering Support") -Message "Roadmap should include Milestone 15."
}


Invoke-PackTest "optional language rule packs are evidence-gated and not globally loaded" {
    $pythonRulePath = Join-Path $repoRoot ".continue/rule-packs/python.md"
    $typescriptRulePath = Join-Path $repoRoot ".continue/rule-packs/typescript.md"
    $languageRuleDocPath = Join-Path $repoRoot "docs/language-rule-packs.md"
    $languageSupportPath = Join-Path $repoRoot "docs/language-support.md"
    $languageEvidencePath = Join-Path $repoRoot "examples/language-rule-pack-validation.md"
    $workflowEvidencePath = Join-Path $repoRoot "examples/multi-language-workflow-validation.md"
    $projectDetectionPath = Join-Path $repoRoot "docs/project-detection.md"
    $configPath = Join-Path $repoRoot ".continue/config.yaml"
    $readmePath = Join-Path $repoRoot "README.md"
    $todoPath = Join-Path $repoRoot "TODO.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"

    Assert-True -Condition (Test-Path -LiteralPath $pythonRulePath) -Message "Python optional rule pack should exist."
    Assert-True -Condition (Test-Path -LiteralPath $typescriptRulePath) -Message "TypeScript optional rule pack should exist."
    Assert-True -Condition (Test-Path -LiteralPath $languageRuleDocPath) -Message "Language rule-pack doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $languageEvidencePath) -Message "Language rule-pack validation evidence should exist."
    Assert-True -Condition (Test-Path -LiteralPath $workflowEvidencePath) -Message "Multi-language workflow validation evidence should exist."

    $pythonRule = Get-Content -LiteralPath $pythonRulePath -Raw
    $typescriptRule = Get-Content -LiteralPath $typescriptRulePath -Raw
    $languageRuleDoc = Get-Content -LiteralPath $languageRuleDocPath -Raw
    $languageSupport = Get-Content -LiteralPath $languageSupportPath -Raw
    $languageEvidence = Get-Content -LiteralPath $languageEvidencePath -Raw
    $workflowEvidence = Get-Content -LiteralPath $workflowEvidencePath -Raw
    $projectDetection = Get-Content -LiteralPath $projectDetectionPath -Raw
    $config = Get-Content -LiteralPath $configPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw

    Assert-True -Condition ($pythonRule -match "optional: true") -Message "Python rule pack should be marked optional."
    Assert-True -Condition ($pythonRule -match "pyproject\.toml") -Message "Python rule pack should require Python evidence."
    Assert-True -Condition ($pythonRule -match "unconfirmed") -Message "Python rule pack should prefer unconfirmed over guesses."
    Assert-True -Condition ($typescriptRule -match "optional: true") -Message "TypeScript rule pack should be marked optional."
    Assert-True -Condition ($typescriptRule -match "package\.json") -Message "TypeScript rule pack should require package metadata evidence."
    Assert-True -Condition ($typescriptRule -match "unconfirmed") -Message "TypeScript rule pack should prefer unconfirmed over guesses."
    Assert-True -Condition ($languageRuleDoc -match "not referenced from") -Message "Language rule-pack doc should state packs are not globally loaded."
    Assert-True -Condition ($languageRuleDoc -match "docs/project-detection.md") -Message "Language rule-pack doc should require project detection."
    Assert-True -Condition ($languageRuleDoc -match "examples/language-rule-pack-validation\.md") -Message "Language rule-pack doc should link validation evidence."
    Assert-True -Condition ($languageSupport -match "docs/language-rule-packs.md") -Message "Language support doc should link optional rule-pack doc."
    Assert-True -Condition ($languageSupport -match "examples/language-rule-pack-validation\.md") -Message "Language support doc should link language rule-pack evidence."
    Assert-True -Condition ($projectDetection -match "Optional Language Rule Packs") -Message "Project detection doc should mention optional language rule packs."
    Assert-True -Condition ($readme -match "docs/language-rule-packs.md") -Message "README should link optional language rule-pack doc."
    Assert-True -Condition ($readme -match "examples/language-rule-pack-validation\.md") -Message "README should link language rule-pack evidence."
    Assert-True -Condition ($todo -match "Add optional Python rule pack") -Message "TODO should track Python rule-pack completion."
    Assert-True -Condition ($roadmap -match "Milestone 18: Language Rule Packs") -Message "Roadmap should include language rule packs milestone."
    Assert-True -Condition ($roadmap -match "Optional Python and TypeScript rule packs") -Message "Roadmap should describe current optional packs."
    Assert-True -Condition ($languageEvidence -match "Language Rule Pack Validation Evidence") -Message "Evidence should have expected title."
    Assert-True -Condition ($languageEvidence -match "python-api") -Message "Evidence should include Python generated sample."
    Assert-True -Condition ($languageEvidence -match "typescript-frontend") -Message "Evidence should include TypeScript generated sample."
    Assert-True -Condition ($languageEvidence -match "pyproject\.toml") -Message "Evidence should include Python project metadata signal."
    Assert-True -Condition ($languageEvidence -match "package\.json") -Message "Evidence should include TypeScript project metadata signal."
    Assert-True -Condition ($languageEvidence -match "does not prove editor/model behavior") -Message "Evidence should avoid overstating editor/model validation."
    Assert-True -Condition ($workflowEvidence -match "Multi-Language Workflow Validation Evidence") -Message "Workflow evidence should have expected title."
    Assert-True -Condition ($workflowEvidence -match "Local Ollama API preflight \| Passed") -Message "Workflow evidence should record successful local Ollama preflight after rerun."
    Assert-True -Condition ($workflowEvidence -match "Repository discovery \| Passed verification") -Message "Workflow evidence should record verified repository discovery."
    Assert-True -Condition ($workflowEvidence -match "FILENAME_NOT_IN_CONTEXT") -Message "Workflow evidence should record filename-drift guardrail failures."
    Assert-True -Condition ($config -notmatch "rule-packs") -Message "Default Continue config should not load optional language rule packs."
}
Invoke-PackTest "project detection docs and guidance are evidence-gated" {
    $docPath = Join-Path $repoRoot "docs/project-detection.md"
    $languagePath = Join-Path $repoRoot "docs/language-support.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $generalRulePath = Join-Path $repoRoot ".continue/rules/general.md"
    $dotnetRulePath = Join-Path $repoRoot ".continue/rules/dotnet.md"
    $aspnetRulePath = Join-Path $repoRoot ".continue/rules/aspnetcore.md"
    $repositoryPromptPath = Join-Path $repoRoot ".continue/prompts/repository-discovery.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Project detection doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $language = Get-Content -LiteralPath $languagePath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $generalRule = Get-Content -LiteralPath $generalRulePath -Raw
    $dotnetRule = Get-Content -LiteralPath $dotnetRulePath -Raw
    $aspnetRule = Get-Content -LiteralPath $aspnetRulePath -Raw
    $repositoryPrompt = Get-Content -LiteralPath $repositoryPromptPath -Raw
    $agents = Get-ChildItem -LiteralPath (Join-Path $repoRoot ".continue/agents") -Filter "*.md" | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }
    $corePrompts = @(
        "repository-discovery.md",
        "implementation-plan.md",
        "code-review.md",
        "architecture-review.md",
        "security-review.md",
        "performance-review.md",
        "documentation.md"
    )

    Assert-True -Condition ($doc -match "Evidence Strength") -Message "Project detection doc should define evidence strength."
    Assert-True -Condition ($doc -match "Ecosystem Signals") -Message "Project detection doc should define ecosystem signals."
    Assert-True -Condition ($doc -match "Strong") -Message "Project detection doc should define strong evidence."
    Assert-True -Condition ($doc -match "Unconfirmed") -Message "Project detection doc should define unconfirmed evidence."
    Assert-True -Condition ($doc -match "Python") -Message "Project detection doc should include Python signals."
    Assert-True -Condition ($doc -match "JavaScript / TypeScript") -Message "Project detection doc should include TypeScript signals."
    Assert-True -Condition ($doc -match "Do not apply \.NET-specific guidance") -Message "Project detection doc should block unsupported .NET advice."
    Assert-True -Condition ($doc -match "package metadata is present") -Message "Project detection doc should prefer package metadata over source guesses."
    Assert-True -Condition ($language -match "docs/project-detection.md") -Message "Language support doc should link project detection."
    Assert-True -Condition ($readme -match "docs/project-detection.md") -Message "README should link project detection."
    Assert-True -Condition ($generalRule -match "Run project classification") -Message "General rule should require project classification."
    Assert-True -Condition ($generalRule -match "Do not apply \.NET") -Message "General rule should gate language-specific advice."
    Assert-True -Condition ($dotnetRule -match "Evidence Gate") -Message ".NET rule should include evidence gate."
    Assert-True -Condition ($aspnetRule -match "Evidence Gate") -Message "ASP.NET Core rule should include evidence gate."
    Assert-True -Condition ($repositoryPrompt -match "Project Classification") -Message "Repository discovery output should include project classification."

    foreach ($promptName in $corePrompts) {
        $prompt = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/prompts/$promptName") -Raw
        Assert-True -Condition ($prompt -match "docs/project-detection.md") -Message "$promptName should reference project detection doc."
        Assert-True -Condition ($prompt -match "Do not apply language-specific recommendations") -Message "$promptName should gate language-specific recommendations."
        Assert-True -Condition ($prompt -match "unconfirmed") -Message "$promptName should prefer unconfirmed over guesses."
    }

    foreach ($agentText in $agents) {
        Assert-True -Condition ($agentText -match "Project Detection") -Message "Each agent should include project detection guidance."
        Assert-True -Condition ($agentText -match "Do not apply language-specific recommendations") -Message "Each agent should gate language-specific recommendations."
    }
}

Invoke-PackTest "sample repository factory creates expected fixtures" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "sample-factory-test-$([guid]::NewGuid())"

    try {
        $scriptPath = Join-Path $repoRoot "scripts/generate-sample-repositories.ps1"
        $result = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-OutputRoot", $tempRoot)
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Sample repository factory should succeed."
        Assert-True -Condition ($result.Output -match "Generated sample repositories") -Message "Sample factory should report generated output."

        $expectedFiles = @(
            "python-api/SAMPLE-METADATA.md",
            "python-api/pyproject.toml",
            "python-api/app/main.py",
            "python-api/tests/test_main.py",
            "typescript-frontend/package.json",
            "node-service/Dockerfile",
            "java-spring-api/pom.xml",
            "go-service/go.mod",
            "rust-cli/Cargo.toml",
            "iac-terraform-kubernetes/terraform/main.tf",
            "iac-terraform-kubernetes/k8s/deployment.yaml",
            "sql-migrations/schema/001_create_items.sql"
        )

        foreach ($relativePath in $expectedFiles) {
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $tempRoot $relativePath)) -Message "Expected generated file is missing: $relativePath"
        }


        $pythonReadme = Get-Content -LiteralPath (Join-Path $tempRoot "python-api/README.md") -Raw
        $pythonProject = Get-Content -LiteralPath (Join-Path $tempRoot "python-api/pyproject.toml") -Raw
        $pythonMain = Get-Content -LiteralPath (Join-Path $tempRoot "python-api/app/main.py") -Raw
        Assert-True -Condition ($pythonReadme -match "# Python API Sample") -Message "Python sample README should have the expected heading."
        Assert-True -Condition ($pythonReadme -match "python -m pytest") -Message "Python sample README should include pytest command guidance."
        Assert-True -Condition ($pythonProject -match "\[project\]") -Message "Python sample should include pyproject metadata."
        Assert-True -Condition ($pythonProject -match "\[tool\.pytest\.ini_options\]") -Message "Python sample should include pytest metadata."
        Assert-True -Condition ($pythonReadme -notmatch "Write-SampleFile") -Message "Python sample README should not leak factory script text."
        Assert-True -Condition ($pythonReadme -notmatch "@['`"]|['`"]@") -Message "Python sample README should not leak here-string markers."
        Assert-True -Condition ($pythonMain -notmatch "Write-SampleFile") -Message "Python sample source should not leak factory script text."
        $listResult = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-List")
        Assert-Equal -Actual $listResult.ExitCode -Expected 0 -Message "Sample repository factory list mode should succeed."
        Assert-True -Condition ($listResult.Output -match "python-api") -Message "List output should include python-api."
        Assert-True -Condition ($listResult.Output -match "sql-migrations") -Message "List output should include sql-migrations."

        $rerunResult = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-OutputRoot", $tempRoot)
        Assert-True -Condition ($rerunResult.ExitCode -ne 0) -Message "Sample repository factory should refuse to overwrite without -Force."
        Assert-True -Condition ($rerunResult.Output -match "overwrite generated samples") -Message "Overwrite refusal should explain how to overwrite generated samples."

        $runtimeContextScript = Join-Path $repoRoot "scripts/generate-runtime-context.ps1"
        $contextTargets = @(
            @{ Name = "typescript-frontend"; Expected = @("SAMPLE-METADATA.md", "tsconfig.json", "src/App.tsx") },
            @{ Name = "node-service"; Expected = @("package.json", "Dockerfile", "src/server.js") },
            @{ Name = "iac-terraform-kubernetes"; Expected = @("terraform/main.tf", "k8s/deployment.yaml", ".github/workflows/validate.yml") },
            @{ Name = "sql-migrations"; Expected = @("schema/001_create_items.sql", "migrations/002_add_item_status.sql", "seeds/items.sql") }
        )

        foreach ($contextTarget in $contextTargets) {
            $samplePath = Join-Path $tempRoot $contextTarget.Name
            $contextPath = Join-Path $tempRoot "$($contextTarget.Name)-runtime-context.md"
            $contextResult = Invoke-CommandCapture -FilePath $runtimeContextScript -Arguments @("-TargetRepo", $samplePath, "-OutputPath", $contextPath)
            Assert-Equal -Actual $contextResult.ExitCode -Expected 0 -Message "Runtime context generation should succeed for $($contextTarget.Name)."
            $context = Get-Content -LiteralPath $contextPath -Raw
            Assert-True -Condition ($context -match "Source Files") -Message "Runtime context should include language-neutral source files section."
            Assert-True -Condition ($context -match "Sample Metadata") -Message "Runtime context should include sample metadata excerpts."
            foreach ($expectedSignal in $contextTarget.Expected) {
                Assert-True -Condition ($context -match [regex]::Escape($expectedSignal)) -Message "Runtime context for $($contextTarget.Name) should include $expectedSignal."
            }
        }
        $forceResult = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-OutputRoot", $tempRoot, "-Force")
        Assert-Equal -Actual $forceResult.ExitCode -Expected 0 -Message "Sample repository factory should overwrite with -Force."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "prompt quality guardrails require filename fidelity and sourced lifecycle claims" {
    $legacyPromptPath = Join-Path $repoRoot ".continue/prompts/legacy-dotnet-dependency-migration.md"
    $repositoryPromptPath = Join-Path $repoRoot ".continue/prompts/repository-discovery.md"
    $promptQualityPath = Join-Path $repoRoot "docs/prompt-quality.md"
    $bannedPatternsPath = Join-Path $repoRoot "docs/banned-output-patterns.md"

    $legacyPrompt = Get-Content -LiteralPath $legacyPromptPath -Raw
    $repositoryPrompt = Get-Content -LiteralPath $repositoryPromptPath -Raw
    $promptQuality = Get-Content -LiteralPath $promptQualityPath -Raw
    $bannedPatterns = Get-Content -LiteralPath $bannedPatternsPath -Raw

    Assert-True -Condition ($legacyPrompt -match "exact filenames") -Message "Legacy migration prompt should require exact inspected filenames."
    Assert-True -Condition ($legacyPrompt -match "Do not invent or normalize filenames") -Message "Legacy migration prompt should ban filename invention."
    Assert-True -Condition ($legacyPrompt -match "Do not combine a basename") -Message "Legacy migration prompt should ban mixed filename synthesis."
    Assert-True -Condition ($legacyPrompt -match "Evidence Files") -Message "Legacy migration prompt should require evidence file output."
    Assert-True -Condition ($legacyPrompt -match "requires current-source verification") -Message "Legacy migration prompt should require verification for unsupported compatibility claims."
    Assert-True -Condition ($legacyPrompt -match "lifecycle/support claims") -Message "Legacy migration prompt should constrain lifecycle/support claims."
    Assert-True -Condition ($legacyPrompt -match "verify with current vendor documentation") -Message "Legacy migration prompt should require current vendor verification when evidence is missing."
    Assert-True -Condition ($repositoryPrompt -match "Use exact filenames") -Message "Repository discovery prompt should require exact filenames."
    Assert-True -Condition ($repositoryPrompt -match "filename-fidelity gate") -Message "Repository discovery prompt should require a filename-fidelity gate."
    Assert-True -Condition ($repositoryPrompt -match "Do not combine a basename") -Message "Repository discovery prompt should ban mixed filename synthesis."
    Assert-True -Condition ($repositoryPrompt -match "label it as unconfirmed") -Message "Repository discovery prompt should label unconfirmed filenames."
    Assert-True -Condition ($promptQuality -match "Use exact filenames") -Message "Prompt quality doc should include filename fidelity."
    Assert-True -Condition ($promptQuality -match "lifecycle/support claims") -Message "Prompt quality doc should cover sourced lifecycle/support claims."
    Assert-True -Condition ($promptQuality -match "Do not combine a basename") -Message "Prompt quality doc should ban mixed filename synthesis."
    Assert-True -Condition ($bannedPatterns -match "Invents, normalizes, or alters") -Message "Banned output patterns should reject altered filenames."
    Assert-True -Condition ($bannedPatterns -match "Combines a basename") -Message "Banned output patterns should reject mixed filename synthesis."
    Assert-True -Condition ($bannedPatterns -match "support-lifecycle claims") -Message "Banned output patterns should reject unsupported lifecycle claims."
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
    $tempRepo = Join-Path $repoRoot "runtime-validation-output/context-parent-git-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRepo "src") | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRepo "bin") | Out-Null

        "# Sample" | Set-Content -LiteralPath (Join-Path $tempRepo "README.md")
        "public class App { }" | Set-Content -LiteralPath (Join-Path $tempRepo "src/App.cs")
        "public class BuildOutput { }" | Set-Content -LiteralPath (Join-Path $tempRepo "bin/Ignored.cs")
        "<Project Sdk=`"Microsoft.NET.Sdk`" />" | Set-Content -LiteralPath (Join-Path $tempRepo "Sample.csproj")
        "{`"scripts`":{`"test`":`"vitest run`"}}" | Set-Content -LiteralPath (Join-Path $tempRepo "package.json")

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
        Assert-True -Condition ($context -match "package.json") -Message "Runtime context should include package metadata files."
        Assert-True -Condition ($context -match "vitest run") -Message "Runtime context should include package metadata excerpts."
        Assert-True -Condition ($context -match "Not a git repository at the target root") -Message "Runtime context should not inherit parent repository git status."
        Assert-True -Condition ($context -notmatch "scripts/test-pack.ps1") -Message "Runtime context should not include parent repository tracked files."
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

Invoke-PackTest "install script read-only profile omits edit roles" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-read-only-profile-test-$([guid]::NewGuid())"
    $globalConfigPath = Join-Path $tempRepo "global-config.yaml"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-InstallProfile", "read-only", "-GlobalConfig", "-GlobalConfigPath", $globalConfigPath)

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install with read-only profile should succeed."

        $localConfigPath = Join-Path $tempRepo ".continue/config.local.yaml"
        Assert-True -Condition (Test-Path -LiteralPath $localConfigPath) -Message "Read-only profile should generate local config."
        Assert-True -Condition (Test-Path -LiteralPath $globalConfigPath) -Message "Read-only profile global config should be written."

        $localConfig = Get-Content -LiteralPath $localConfigPath -Raw
        $globalConfig = Get-Content -LiteralPath $globalConfigPath -Raw

        Assert-True -Condition ($localConfig -match "READ ONLY - qwen3\.5:9b") -Message "Read-only profile should include a read-only model lane."
        Assert-True -Condition ($localConfig -match "Ollama Nomic Embed") -Message "Read-only profile should keep embedding model."
        Assert-True -Condition ($localConfig -notmatch "- edit") -Message "Read-only profile should not include edit role."
        Assert-True -Condition ($localConfig -notmatch "- apply") -Message "Read-only profile should not include apply role."
        Assert-True -Condition ($globalConfig -match "READ ONLY - qwen3\.5:9b") -Message "Global config should use read-only profile when present."
        Assert-True -Condition ($globalConfig -notmatch "- edit") -Message "Global read-only config should not include edit role."
    } finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script approved-write profile maps to model lanes" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-approved-write-profile-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-InstallProfile", "approved-write")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Install with approved-write profile should succeed."

        $localConfigPath = Join-Path $tempRepo ".continue/config.local.yaml"
        Assert-True -Condition (Test-Path -LiteralPath $localConfigPath) -Message "Approved-write profile should generate model lane config."

        $localConfig = Get-Content -LiteralPath $localConfigPath -Raw
        Assert-True -Condition ($localConfig -match "1 - WRITE SAFE - qwen3\.5:9b") -Message "Approved-write profile should include WRITE SAFE lane."
        Assert-True -Condition ($localConfig -match '(?s)1 - WRITE SAFE - qwen3\.5:9b.*roles:\s*\r?\n\s*- chat\s*\r?\n\s*- edit\s*\r?\n\s*- apply') -Message "Approved-write WRITE SAFE lane should include chat/edit/apply."
        Assert-True -Condition ($localConfig -notmatch '(?s)2 - PLAN ONLY - qwen3\.5:9b.*roles:.*- edit') -Message "Approved-write PLAN ONLY lane should stay read-only."
    } finally {
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
        Assert-True -Condition ($localConfig -match "2 - PLAN ONLY - qwen3\.5:9b") -Message "Model lanes should include simple-hardware PLAN ONLY lane."
        Assert-True -Condition ($localConfig -match "3 - DEEP REVIEW - qwen3\.5:9b") -Message "Model lanes should include simple-hardware DEEP REVIEW lane."
        Assert-True -Condition ($localConfig -match "Ollama Nomic Embed") -Message "Model lanes should keep a separate embedding model."
        Assert-True -Condition ($localConfig -notmatch "4 - ") -Message "Model lanes should include only three Agent lanes."
        Assert-True -Condition ($localConfig -notmatch "5 - ") -Message "Embedding should not be labeled as an Agent lane."
        Assert-True -Condition ($localConfig -match '(?s)1 - WRITE SAFE - qwen3\.5:9b.*roles:\s*\r?\n\s*- chat\s*\r?\n\s*- edit\s*\r?\n\s*- apply') -Message "WRITE SAFE lane should include chat/edit/apply roles."
        Assert-True -Condition ($localConfig -match '(?s)2 - PLAN ONLY - qwen3\.5:9b.*roles:\s*\r?\n\s*- chat') -Message "PLAN ONLY lane should include chat role."
        Assert-True -Condition ($localConfig -notmatch '(?s)2 - PLAN ONLY - qwen3\.5:9b.*roles:.*- edit') -Message "PLAN ONLY lane should not include edit role."
        Assert-True -Condition ($localConfig -notmatch '(?s)3 - DEEP REVIEW - qwen3\.5:9b.*roles:.*- apply') -Message "DEEP REVIEW lane should not include apply role."
        Assert-True -Condition ($globalConfig -match "apiBase: http://127\.0\.0\.1:11434") -Message "Global model lanes config should include requested apiBase."
    } finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "validated model installer updates local-only config" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-validated-model-test-$([guid]::NewGuid())"

    try {
        $targetContinue = Join-Path $tempRepo ".continue"
        New-Item -ItemType Directory -Force -Path $targetContinue | Out-Null
        Copy-Item -LiteralPath (Join-Path $repoRoot ".continue/config.yaml") -Destination (Join-Path $targetContinue "config.yaml")

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-validated-model.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-Model", "devstral-small-2:24b", "-Profile", "plan-only", "-NoPull")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Validated model installer should succeed without pulling when NoPull is set."

        $baseConfig = Get-Content -LiteralPath (Join-Path $targetContinue "config.yaml") -Raw
        $localConfigPath = Join-Path $targetContinue "config.local.yaml"
        $localConfig = Get-Content -LiteralPath $localConfigPath -Raw

        Assert-True -Condition ($baseConfig -notmatch "devstral-small-2:24b") -Message "Validated model installer should not modify shared config."
        Assert-True -Condition ($localConfig -match "2 - PLAN ONLY - devstral-small-2:24b") -Message "Validated model installer should update selected profile."
        Assert-True -Condition ($localConfig -match "1 - WRITE SAFE - qwen3\.5:9b") -Message "Validated model installer should preserve simple WRITE SAFE default."
        Assert-True -Condition ($localConfig -match "3 - DEEP REVIEW - qwen3\.5:9b") -Message "Validated model installer should preserve simple DEEP REVIEW default."
        Assert-True -Condition ($localConfig -match "Ollama Nomic Embed") -Message "Validated model installer should preserve embedding model."
    } finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "validated model installer dry run is local only" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-install-validated-model-dry-run-test-$([guid]::NewGuid())"

    try {
        $targetContinue = Join-Path $tempRepo ".continue"
        New-Item -ItemType Directory -Force -Path $targetContinue | Out-Null
        Copy-Item -LiteralPath (Join-Path $repoRoot ".continue/config.yaml") -Destination (Join-Path $targetContinue "config.yaml")

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-validated-model.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-Model", "qwen3-coder:30b", "-Profile", "deep-review", "-DryRun", "-NoPull")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Validated model installer dry run should succeed."
        Assert-True -Condition ($result.Output -match "Would install validated model") -Message "Dry run should describe selected model installation."
        Assert-True -Condition ($result.Output -match "Would write local-only config") -Message "Dry run should explain local-only config update."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $targetContinue "config.local.yaml"))) -Message "Dry run should not write local config."
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
    $wrappers = @(
        @{
            Name = "install-continue-pack.linux.sh"
            Target = "install-continue-pack.shared.sh"
        },
        @{
            Name = "install-continue-pack.macos.sh"
            Target = "install-continue-pack.shared.sh"
        },
        @{
            Name = "install-validated-model.linux.sh"
            Target = "install-validated-model.shared.sh"
        },
        @{
            Name = "install-validated-model.macos.sh"
            Target = "install-validated-model.shared.sh"
        }
    )

    foreach ($wrapper in $wrappers) {
        $wrapperPath = Join-Path $repoRoot "scripts/$($wrapper.Name)"
        Assert-True -Condition (Test-Path -LiteralPath $wrapperPath) -Message "$($wrapper.Name) should exist."

        $content = Get-Content -LiteralPath $wrapperPath -Raw
        Assert-True -Condition ($content -match [regex]::Escape($wrapper.Target)) -Message "$($wrapper.Name) should call the shared Bash installer."
        Assert-True -Condition ($content -notmatch "pwsh") -Message "$($wrapper.Name) should not require pwsh."
    }
}

Invoke-PackTest "shell wrapper scripts and hooks are executable in git" {
    $modeRows = & git -C $repoRoot ls-files -s "scripts/*.sh" ".githooks/pre-push"
    Assert-True -Condition ($LASTEXITCODE -eq 0) -Message "git ls-files should succeed for shell scripts."
    Assert-True -Condition ($modeRows.Count -gt 0) -Message "Repository should include shell scripts and hooks."

    foreach ($row in $modeRows) {
        $parts = $row -split "\s+"
        $mode = $parts[0]
        $path = $parts[-1]

        Assert-Equal -Actual $mode -Expected "100755" -Message "Shell script or hook should be executable in git: $path"
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
            Name = "verify-runtime-output.linux.sh"
            Target = "verify-runtime-output.shared.sh"
        },
        @{
            Name = "verify-runtime-output.macos.sh"
            Target = "verify-runtime-output.shared.sh"
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
        },
        @{
            Name = "generate-sample-repositories.linux.sh"
            Target = "generate-sample-repositories.shared.sh"
        },
        @{
            Name = "generate-sample-repositories.macos.sh"
            Target = "generate-sample-repositories.shared.sh"
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

Invoke-PackTest "runtime output verifier catches invented filenames and unsupported claims" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "continue-runtime-output-verifier-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

        $contextPath = Join-Path $tempRoot "runtime-context.md"
        $goodOutputPath = Join-Path $tempRoot "good.md"
        $badOutputPath = Join-Path $tempRoot "bad.md"

        @"
## Project Files

- BrickLinkBrickSet.csproj
- packages.config
- Properties/ExcelDna.Build.props
"@ | Set-Content -LiteralPath $contextPath

        "Use BrickLinkBrickSet.csproj and packages.config. Compatibility requires current-source verification." |
            Set-Content -LiteralPath $goodOutputPath

        "BrickLinkBrickSet-AddIn.csproj is compatible with .NET Framework 4.8." |
            Set-Content -LiteralPath $badOutputPath

        $good = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/verify-runtime-output.ps1") `
            -Arguments @("-OutputPath", $goodOutputPath, "-ContextPath", $contextPath, "-WorkflowName", "legacy-dotnet-dependency-migration")

        Assert-Equal -Actual $good.ExitCode -Expected 0 -Message "Verifier should pass output that uses context filenames and verification qualifiers."
        Assert-True -Condition ($good.Output -match "PASS runtime output verification") -Message "Verifier pass message should be present."

        $bad = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/verify-runtime-output.ps1") `
            -Arguments @("-OutputPath", $badOutputPath, "-ContextPath", $contextPath, "-WorkflowName", "legacy-dotnet-dependency-migration")

        Assert-True -Condition ($bad.ExitCode -ne 0) -Message "Verifier should fail invented filename output."
        Assert-True -Condition ($bad.Output -match "FILENAME_NOT_IN_CONTEXT") -Message "Verifier should report invented filenames."
        Assert-True -Condition ($bad.Output -match "UNSOURCED_COMPATIBILITY_CLAIM") -Message "Verifier should report unsupported compatibility claims."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "runtime validation runner writes verification outputs" {
    $runnerPath = Join-Path $repoRoot "scripts/run-runtime-validation.ps1"
    $sharedRunnerPath = Join-Path $repoRoot "scripts/run-runtime-validation.shared.sh"

    $runner = Get-Content -LiteralPath $runnerPath -Raw
    $sharedRunner = Get-Content -LiteralPath $sharedRunnerPath -Raw

    Assert-True -Condition ($runner -match "verify-runtime-output\.ps1") -Message "PowerShell runtime runner should call verifier."
    Assert-True -Condition ($runner -match "Local Ollama API preflight failed") -Message "PowerShell runtime runner should fail fast when local Ollama is unreachable."
    Assert-True -Condition ($runner -match "/api/tags") -Message "PowerShell runtime runner should preflight Ollama tags endpoint."
    Assert-True -Condition ($runner -match "Failed guardrail verification") -Message "PowerShell runtime runner should summarize verifier failures."
    Assert-True -Condition ($sharedRunner -match "verify-runtime-output\.shared\.sh") -Message "Bash runtime runner should call verifier."
    Assert-True -Condition ($sharedRunner -match "Local Ollama API preflight failed") -Message "Bash runtime runner should fail fast when local Ollama is unreachable."
    Assert-True -Condition ($sharedRunner -match "/api/tags") -Message "Bash runtime runner should preflight Ollama tags endpoint."
    Assert-True -Condition ($sharedRunner -match "\.verification\.txt") -Message "Bash runtime runner should write verification output files."
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

Invoke-PackTest "online model discovery scripts are candidate-only and cross-platform" {
    $scriptNames = @(
        "discover-online-model-candidates.ps1",
        "discover-online-model-candidates.shared.sh"
    )

    foreach ($scriptName in $scriptNames) {
        $scriptPath = Join-Path $repoRoot "scripts/$scriptName"
        $content = Get-Content -LiteralPath $scriptPath -Raw

        Assert-True -Condition ($content -match "PullsModels") -Message "$scriptName should report that it does not pull models."
        Assert-True -Condition ($content -match "RewritesContinueConfig") -Message "$scriptName should report that it does not rewrite Continue config."
        Assert-True -Condition ($content -notmatch "/api/pull") -Message "$scriptName should not call Ollama pull APIs."
        Assert-True -Condition ($content -notmatch "config\.local\.yaml") -Message "$scriptName should not write local Continue config."
    }

    $wrappers = @(
        @{
            Name = "discover-online-model-candidates.linux.sh"
            Target = "discover-online-model-candidates.shared.sh"
        },
        @{
            Name = "discover-online-model-candidates.macos.sh"
            Target = "discover-online-model-candidates.shared.sh"
        }
    )

    foreach ($wrapper in $wrappers) {
        $wrapperPath = Join-Path $repoRoot "scripts/$($wrapper.Name)"
        Assert-True -Condition (Test-Path -LiteralPath $wrapperPath) -Message "$($wrapper.Name) should exist."

        $content = Get-Content -LiteralPath $wrapperPath -Raw
        Assert-True -Condition ($content -match [regex]::Escape($wrapper.Target)) -Message "$($wrapper.Name) should call the shared discovery script."
        Assert-True -Condition ($content -notmatch "pwsh") -Message "$($wrapper.Name) should not require pwsh."
    }
}

Invoke-PackTest "online model discovery parses a local fixture without network" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "online-model-discovery-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
        $fixturePath = Join-Path $tempRoot "model-page.html"
        $outputPath = Join-Path $tempRoot "online-model-candidates.json"

        @"
<html>
  <a href="/library/qwen3.5:9b">qwen3.5:9b</a>
  <a href="/library/devstral-small-2:24b">devstral-small-2:24b</a>
</html>
"@ | Set-Content -LiteralPath $fixturePath

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/discover-online-model-candidates.ps1") `
            -Arguments @("-SourceHtmlPath", $fixturePath, "-Families", "qwen3.5,devstral-small-2", "-OutputPath", $outputPath)

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Discovery script should parse a local fixture."
        Assert-True -Condition (Test-Path -LiteralPath $outputPath) -Message "Discovery script should write a report."

        $report = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
        $models = @($report.Candidates | ForEach-Object { $_.Model })

        Assert-True -Condition ($report.RepositoryContentSent -eq $false) -Message "Discovery report should state repository content was not sent."
        Assert-True -Condition ($report.HardwareProfileSent -eq $false) -Message "Discovery report should state hardware profile was not sent."
        Assert-True -Condition ($report.PullsModels -eq $false) -Message "Discovery report should state models were not pulled."
        Assert-True -Condition ($report.RewritesContinueConfig -eq $false) -Message "Discovery report should state Continue config was not rewritten."
        Assert-True -Condition ($models -contains "qwen3.5:9b") -Message "Discovery report should include qwen3.5 fixture candidate."
        Assert-True -Condition ($models -contains "devstral-small-2:24b") -Message "Discovery report should include devstral fixture candidate."
        $doc = Get-Content -LiteralPath (Join-Path $repoRoot "docs/online-model-discovery.md") -Raw
        Assert-True -Condition ($doc -match "VRAM-Aware Candidate Annotation") -Message "Online discovery docs should explain local VRAM annotation."
        Assert-True -Condition ($doc -match "terminal output shows each family") -Message "Online discovery docs should explain terminal discovery output."
        Assert-True -Condition ($doc -match "HardwareProfileSent") -Message "Online discovery docs should state hardware profiles are not sent online."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "online model discovery supports local VRAM annotation without leaking profiles" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "online-model-discovery-vram-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
        $fixturePath = Join-Path $tempRoot "model-page.html"
        $profilePath = Join-Path $tempRoot "model-profile.json"
        $outputPath = Join-Path $tempRoot "online-model-candidates.json"

        @"
<html>
  <a href="/library/qwen3.5:9b">qwen3.5:9b</a>
  <a href="/library/qwen3.5:35b">qwen3.5:35b</a>
  <a href="/library/qwen3.5:9b-mlx">qwen3.5:9b-mlx</a>
  <a href="/library/qwen3.5:cloud">qwen3.5:cloud</a>
</html>
"@ | Set-Content -LiteralPath $fixturePath

        @"
{
  "Platform": "Windows",
  "Gpus": [
    {"Name":"fixture-gpu","VramGb":16,"MemoryType":"dedicated"}
  ]
}
"@ | Set-Content -LiteralPath $profilePath

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/discover-online-model-candidates.ps1") `
            -Arguments @("-SourceHtmlPath", $fixturePath, "-Families", "qwen3.5", "-ModelProfilePath", $profilePath, "-VramSelectionMode", "TotalDedicated", "-OutputPath", $outputPath)

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Discovery script should parse a fixture with local VRAM annotation."
        $report = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
        $small = @($report.Candidates | Where-Object { $_.Model -eq "qwen3.5:9b" }) | Select-Object -First 1
        $large = @($report.Candidates | Where-Object { $_.Model -eq "qwen3.5:35b" }) | Select-Object -First 1
        $cloud = @($report.SkippedCandidates | Where-Object { $_.Model -eq "qwen3.5:cloud" }) | Select-Object -First 1
        $mlx = @($report.SkippedCandidates | Where-Object { $_.Model -eq "qwen3.5:9b-mlx" }) | Select-Object -First 1
        $candidateModels = @($report.Candidates | ForEach-Object { $_.Model })

        Assert-True -Condition ($report.HardwareProfileSent -eq $false) -Message "Discovery report should state hardware profile was not sent."
        Assert-True -Condition ($report.ModelProfilePath -eq "redacted") -Message "Discovery report should redact model profile path."
        Assert-True -Condition ($report.AvailableVramGb -eq 16) -Message "Discovery report should record local VRAM estimate."
        Assert-True -Condition ($report.ModelHostPlatform -eq "Windows") -Message "Discovery report should record the model host platform."
        Assert-True -Condition ($small.VramRecommendation.FitsAvailableVram -eq $true) -Message "Small fixture model should fit the local VRAM estimate."
        Assert-True -Condition ($large.VramRecommendation.FitsAvailableVram -eq $false) -Message "Large fixture model should exceed the local VRAM estimate."
        Assert-True -Condition ($large.Status -eq "online candidate above vram estimate") -Message "Oversized fixture model should be marked above VRAM estimate."
        Assert-True -Condition ($null -ne $cloud) -Message "Cloud fixture model should be skipped, not treated as pullable."
        Assert-True -Condition ($null -ne $mlx) -Message "MLX fixture model should be skipped on non-macOS model hosts."
        Assert-True -Condition ($candidateModels -notcontains "qwen3.5:cloud") -Message "Cloud fixture model should not be included in pullable candidates."
        Assert-True -Condition ($candidateModels -notcontains "qwen3.5:9b-mlx") -Message "MLX fixture model should not be included in pullable candidates for Windows model host."
        Assert-True -Condition ($cloud.FailureSignal -eq "MODEL_SKIPPED_FOR_PLATFORM") -Message "Cloud fixture model should record a platform skip signal."
        Assert-True -Condition ($mlx.FailureSignal -eq "MODEL_SKIPPED_FOR_PLATFORM") -Message "MLX fixture model should record a platform skip signal."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "remote hardware profile scripts are documented and SSH-based" {
    $psScriptPath = Join-Path $repoRoot "scripts/get-remote-model-profile.ps1"
    $sharedScriptPath = Join-Path $repoRoot "scripts/get-remote-model-profile.shared.sh"
    $docPath = Join-Path $repoRoot "docs/remote-hardware-profile.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $selectionPath = Join-Path $repoRoot "docs/local-model-selection.md"

    Assert-True -Condition (Test-Path -LiteralPath $psScriptPath) -Message "Windows remote profile script should exist."
    Assert-True -Condition (Test-Path -LiteralPath $sharedScriptPath) -Message "Shared remote profile script should exist."
    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Remote hardware profile docs should exist."

    $psScript = Get-Content -LiteralPath $psScriptPath -Raw
    $sharedScript = Get-Content -LiteralPath $sharedScriptPath -Raw
    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $selection = Get-Content -LiteralPath $selectionPath -Raw

    Assert-True -Condition ($psScript -match "RemoteHost") -Message "Windows remote profile script should require a remote host."
    Assert-True -Condition ($psScript -match "get-local-model-profile\.linux\.sh") -Message "Windows remote profile script should reuse the Linux profile helper."
    Assert-True -Condition ($psScript -match "get-local-model-profile\.macos\.sh") -Message "Windows remote profile script should support macOS remote hosts."
    Assert-True -Condition ($psScript -match "ssh") -Message "Windows remote profile script should use SSH."
    Assert-True -Condition ($psScript -match "BatchMode=yes") -Message "Windows remote profile script should default to non-interactive SSH."
    Assert-True -Condition ($psScript -match "TimeoutSeconds") -Message "Windows remote profile script should expose a timeout."
    Assert-True -Condition ($psScript -match "SSH closed before the profile script could be sent") -Message "Windows remote profile script should report early SSH exits clearly."
    Assert-True -Condition ($psScript -match "scp") -Message "Windows remote profile script should use scp for interactive SSH mode."
    Assert-True -Condition ($psScript -match "local-engineering-agent-profile") -Message "Windows remote profile script should use a temporary remote profiler path."
    Assert-True -Condition ($psScript -match "\[1/6\] Checking local SSH tools") -Message "PowerShell remote profile script should show the first progress step."
    Assert-True -Condition ($psScript -match "\[6/6\] Validating remote profile JSON") -Message "PowerShell remote profile script should show the JSON validation progress step."
    Assert-True -Condition ($sharedScript -match "--remote-host") -Message "Shared remote profile script should expose remote-host."
    Assert-True -Condition ($sharedScript -match "BatchMode=yes") -Message "Shared remote profile script should default to non-interactive SSH."
    Assert-True -Condition ($sharedScript -match "--timeout-seconds") -Message "Shared remote profile script should expose a timeout."
    Assert-True -Condition ($sharedScript -match "scp") -Message "Shared remote profile script should use scp for interactive SSH mode."
    Assert-True -Condition ($sharedScript -match "local-engineering-agent-profile") -Message "Shared remote profile script should use a temporary remote profiler path."
    Assert-True -Condition ($sharedScript -match "\[1/6\] Checking local SSH tools") -Message "Shared remote profile script should show the first progress step."
    Assert-True -Condition ($sharedScript -match "\[6/6\] Validating remote profile JSON") -Message "Shared remote profile script should show the JSON validation progress step."
    Assert-True -Condition ($sharedScript -match "bash -s -- --json") -Message "Shared remote profile script should run the local profile script remotely as JSON."
    Assert-True -Condition ($sharedScript -match "get-local-model-profile\.linux\.sh") -Message "Shared remote profile script should reuse the Linux profile helper."
    Assert-True -Condition ($sharedScript -match "get-local-model-profile\.macos\.sh") -Message "Shared remote profile script should support macOS remote hosts."
    Assert-True -Condition ($doc -match "Windows laptop to Linux Ollama server") -Message "Remote hardware profile docs should cover Windows-to-Linux."
    Assert-True -Condition ($doc -match "ModelProfilePath") -Message "Remote hardware profile docs should show model test integration."
    Assert-True -Condition ($doc -match "does not install files on the remote machine") -Message "Remote hardware profile docs should describe the no-install remote behavior."
    Assert-True -Condition ($doc -match "SSH Preflight") -Message "Remote hardware profile docs should include SSH preflight guidance."
    Assert-True -Condition ($doc -match "TimeoutSeconds") -Message "Remote hardware profile docs should document timeout behavior."
    Assert-True -Condition ($doc -match "SSH pipe was closed") -Message "Remote hardware profile docs should cover early SSH pipe closure."
    Assert-True -Condition ($doc -match "copy-and-run") -Message "Remote hardware profile docs should explain interactive copy-and-run mode."
    Assert-True -Condition ($doc -match "scp") -Message "Remote hardware profile docs should mention scp for interactive mode."
    Assert-True -Condition ($doc -match "Progress Output") -Message "Remote hardware profile docs should explain numbered progress output."
    Assert-True -Condition ($doc -match "\[5/6\]") -Message "Remote hardware profile docs should explain the remote detection progress step."
    Assert-True -Condition ($readme -match "docs/remote-hardware-profile.md") -Message "README should link to remote hardware profile docs."
    Assert-True -Condition ($selection -match "remote-hardware-profile.md") -Message "Local model selection docs should link to remote hardware profile docs."
}
Invoke-PackTest "local agent model tests support explicit failed-model cleanup" {
    $psScriptPath = Join-Path $repoRoot "scripts/test-local-agent-models.ps1"
    $bashScriptPath = Join-Path $repoRoot "scripts/test-local-agent-models.shared.sh"
    $docPath = Join-Path $repoRoot "docs/local-agent-model-testing.md"

    $psScript = Get-Content -LiteralPath $psScriptPath -Raw
    $bashScript = Get-Content -LiteralPath $bashScriptPath -Raw
    $doc = Get-Content -LiteralPath $docPath -Raw

    Assert-True -Condition ($psScript -match "RemoveFailedModels") -Message "PowerShell model test script should expose RemoveFailedModels."
    Assert-True -Condition ($psScript -match "\[1/8\] Preparing local Agent model test run") -Message "PowerShell model test script should print numbered progress output."
    Assert-True -Condition ($psScript -match "\[8/8\] Writing sanitized report") -Message "PowerShell model test script should print report-writing progress output."
    Assert-True -Condition ($psScript -match "Large model pulls may need 1800 seconds") -Message "PowerShell model test script should explain large model pull timeouts."
    Assert-True -Condition ($psScript -match "/api/delete") -Message "PowerShell model test script should use Ollama delete API for cleanup."
    Assert-True -Condition ($psScript -match "Removal") -Message "PowerShell model test script should report per-model removal details."
    Assert-True -Condition ($bashScript -match "--remove-failed-models") -Message "Bash model test script should expose remove-failed-models."
    Assert-True -Condition ($bashScript -match "\[1/8\] Preparing local Agent model test run") -Message "Bash model test script should print numbered progress output."
    Assert-True -Condition ($bashScript -match "--timeout-seconds") -Message "Bash model test script should expose timeout-seconds."
    Assert-True -Condition ($bashScript -match "Large model pulls may need") -Message "Bash model test script should explain large model pull timeouts."
    Assert-True -Condition ($bashScript -match 'method="DELETE"') -Message "Bash model test script should use Ollama delete API for cleanup."
    Assert-True -Condition ($bashScript -match "Removal") -Message "Bash model test script should report per-model removal details."
    Assert-True -Condition ($doc -match "Remove Failed Models") -Message "Docs should explain failed-model cleanup."
    Assert-True -Condition ($doc -match "Progress Output And Pull Timeouts") -Message "Docs should explain model-test progress output."
    Assert-True -Condition ($doc -match "TimeoutSeconds 1800") -Message "Docs should show a longer timeout for large model pulls."
    Assert-True -Condition ($doc -match "--timeout-seconds 1800") -Message "Docs should show the Bash timeout flag for large model pulls."
    Assert-True -Condition ($doc -match "destructive") -Message "Docs should warn that failed-model cleanup is destructive."
    Assert-True -Condition ($doc -match "RemoveFailedModels") -Message "Docs should include the PowerShell cleanup flag."
    Assert-True -Condition ($doc -match "--remove-failed-models") -Message "Docs should include the Bash cleanup flag."
    Assert-True -Condition ($psScript -match "AvailableVramGb") -Message "PowerShell model test script should expose AvailableVramGb."
    Assert-True -Condition ($psScript -match "MODEL_SKIPPED_FOR_VRAM") -Message "PowerShell model test script should skip oversized models before pull."
    Assert-True -Condition ($psScript -match "IncludeOversizedModels") -Message "PowerShell model test script should allow explicit oversized testing override."
    Assert-True -Condition ($bashScript -match "--available-vram-gb") -Message "Bash model test script should expose available-vram-gb."
    Assert-True -Condition ($bashScript -match "MODEL_SKIPPED_FOR_VRAM") -Message "Bash model test script should skip oversized models before pull."
    Assert-True -Condition ($bashScript -match "--include-oversized-models") -Message "Bash model test script should allow explicit oversized testing override."
    Assert-True -Condition ($psScript -match "MODEL_SKIPPED_FOR_PLATFORM") -Message "PowerShell model test script should skip platform-incompatible models before pull."
    Assert-True -Condition ($bashScript -match "MODEL_SKIPPED_FOR_PLATFORM") -Message "Bash model test script should skip platform-incompatible models before pull."
    Assert-True -Condition ($psScript -match "Get-TestRecommendation") -Message "PowerShell model test script should produce a recommendation object."
    Assert-True -Condition ($bashScript -match "test_recommendation") -Message "Bash model test script should produce a recommendation object."
    Assert-True -Condition ($psScript -match "Recommended model:") -Message "PowerShell model test script should print a recommended model."
    Assert-True -Condition ($bashScript -match "Recommended model:") -Message "Bash model test script should print a recommended model."
    Assert-True -Condition ($doc -match "Recommendation Output") -Message "Docs should explain recommendation output."
    Assert-True -Condition ($doc -match "Recommended model:") -Message "Docs should mention the recommended model terminal output."
    Assert-True -Condition ($doc -match "Recommendation") -Message "Docs should mention the JSON recommendation object."
    Assert-True -Condition ($doc -match "Platform-Specific Pull Safety") -Message "Docs should explain platform-specific pull safety."
    Assert-True -Condition ($doc -match "MODEL_SKIPPED_FOR_PLATFORM") -Message "Docs should include the platform skip signal."
    Assert-True -Condition ($doc -match "MLX") -Message "Docs should mention MLX platform handling."
    Assert-True -Condition ($doc -match "cloud") -Message "Docs should mention cloud tag handling."
    Assert-True -Condition ($doc -match "Gate Pulls By Available VRAM") -Message "Docs should explain VRAM-gated pulls."
    Assert-True -Condition ($doc -match "AvailableVramGb") -Message "Docs should include the PowerShell VRAM flag."
    Assert-True -Condition ($doc -match "--available-vram-gb") -Message "Docs should include the Bash VRAM flag."
    Assert-True -Condition ($psScript -match "ModelProfilePath") -Message "PowerShell model test script should accept a model profile path."
    Assert-True -Condition ($psScript -match "VramSelectionMode") -Message "PowerShell model test script should expose VRAM selection mode."
    Assert-True -Condition ($psScript -match "Get-AvailableVramFromProfile") -Message "PowerShell model test script should derive VRAM from profile JSON."
    Assert-True -Condition ($bashScript -match "--model-profile-path") -Message "Bash model test script should accept a model profile path."
    Assert-True -Condition ($bashScript -match "--vram-selection-mode") -Message "Bash model test script should expose VRAM selection mode."
    Assert-True -Condition ($bashScript -match "available_vram_from_profile") -Message "Bash model test script should derive VRAM from profile JSON."
    Assert-True -Condition ($doc -match "get-local-model-profile") -Message "Docs should connect VRAM gating to the local model profile scripts."
    Assert-True -Condition ($doc -match "ModelProfilePath") -Message "Docs should include the PowerShell profile path flag."
    Assert-True -Condition ($doc -match "--model-profile-path") -Message "Docs should include the Bash profile path flag."
    Assert-True -Condition ($doc -match "VramSelectionMode") -Message "Docs should explain the VRAM selection mode."
}
Invoke-PackTest "hardware-aware recommendation scripts emit sanitized model lanes" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "hardware-recommendation-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
        $profilePath = Join-Path $tempRoot "model-profile.json"
        $outputPath = Join-Path $tempRoot "recommendation.json"

        @"
{
  "Platform": "Windows",
  "CpuArchitecture": "x64",
  "SystemRamGb": 32,
  "Gpus": [
    {"Name":"fixture gpu","VramGb":16,"MemoryType":"dedicated"}
  ],
  "OllamaModels": ["qwen3.5:9b", "qwen3-coder:30b"]
}
"@ | Set-Content -LiteralPath $profilePath

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/recommend-local-agent-config.ps1") `
            -Arguments @("-ModelProfilePath", $profilePath, "-OutputPath", $outputPath, "-VramSelectionMode", "MaxDedicated")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Recommendation script should run against a sanitized fixture."
        Assert-True -Condition (Test-Path -LiteralPath $outputPath) -Message "Recommendation script should write a report."

        $report = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
        $script = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/recommend-local-agent-config.ps1") -Raw
        $sharedScript = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/recommend-local-agent-config.shared.sh") -Raw
        $doc = Get-Content -LiteralPath (Join-Path $repoRoot "docs/hardware-aware-recommendations.md") -Raw
        $readme = Get-Content -LiteralPath (Join-Path $repoRoot "README.md") -Raw

        Assert-True -Condition ($report.Recommendation.Status -eq "recommended") -Message "Recommendation should select an approved-write model from evidence."
        Assert-True -Condition ($report.Recommendation.WriteSafeModel -eq "qwen3.5:9b") -Message "WRITE SAFE should choose the approved-write ready model."
        Assert-True -Condition ($report.ContinueProfiles.WriteSafe.Roles -contains "edit") -Message "WRITE SAFE should include edit role guidance."
        Assert-True -Condition ($report.ContinueProfiles.PlanOnly.Roles -notcontains "edit") -Message "PLAN ONLY should not include edit role guidance."
        Assert-True -Condition ($report.ModelProfilePath -eq "redacted") -Message "Recommendation output should redact model profile path."
        Assert-True -Condition ($report.Privacy.RepositoryContentSent -eq $false) -Message "Recommendation output should state repository content was not sent."
        Assert-True -Condition ($report.Privacy.HardwareProfileSentOnline -eq $false) -Message "Recommendation output should state hardware profile was not sent online."
        Assert-True -Condition (($report | ConvertTo-Json -Depth 20) -notmatch "Users|OneDrive|192\.168\.|localhost") -Message "Recommendation output should not leak local paths or endpoints."
        Assert-True -Condition ($script -match "VramSelectionMode") -Message "PowerShell recommendation script should support VRAM selection mode."
        Assert-True -Condition ($script -match "config/evidence-catalog.tsv") -Message "PowerShell recommendation script should use evidence catalog by default."
        Assert-True -Condition ($sharedScript -match "python3 is required") -Message "Bash recommendation script should clearly state its python3 requirement."
        Assert-True -Condition ($sharedScript -match "HardwareProfileSentOnline") -Message "Bash recommendation script should emit sanitized privacy fields."
        Assert-True -Condition ($doc -match "WRITE SAFE") -Message "Recommendation docs should explain WRITE SAFE lane."
        Assert-True -Condition ($doc -match "does not read repository source code") -Message "Recommendation docs should explain privacy boundaries."
        Assert-True -Condition ($readme -match "hardware-aware model/config recommendation") -Message "README should link the hardware-aware recommendation path."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "recommended agent config generation writes local-only config" {
    $tempRoot = Copy-RepositoryForTest
    $targetRoot = Join-Path ([System.IO.Path]::GetTempPath()) "recommended-config-target-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $targetRoot ".continue") | Out-Null
        Copy-Item -LiteralPath (Join-Path $repoRoot ".continue/config.yaml") -Destination (Join-Path $targetRoot ".continue/config.yaml") -Force

        $recommendationPath = Join-Path $tempRoot "recommendation.json"
        @"
{
  "Recommendation": {
    "Status": "recommended",
    "WriteSafeModel": "qwen3.5:9b",
    "PlanOnlyModel": "devstral-small-2:24b",
    "DeepReviewModel": "qwen3-coder:30b"
  },
  "ContinueProfiles": {
    "WriteSafe": {"Model":"qwen3.5:9b","Roles":["chat","edit","apply"],"ContextLength":16384,"MaxTokens":2048,"KeepAlive":1800},
    "PlanOnly": {"Model":"devstral-small-2:24b","Roles":["chat"],"ContextLength":16384,"MaxTokens":2048,"KeepAlive":1800},
    "DeepReview": {"Model":"qwen3-coder:30b","Roles":["chat"],"ContextLength":32768,"MaxTokens":4096,"KeepAlive":1800}
  }
}
"@ | Set-Content -LiteralPath $recommendationPath

        $dryRun = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/apply-recommended-agent-config.ps1") `
            -Arguments @("-TargetRepo", $targetRoot, "-RecommendationPath", $recommendationPath, "-DryRun")
        Assert-Equal -Actual $dryRun.ExitCode -Expected 0 -Message "Apply recommendation dry run should succeed."
        Assert-True -Condition ($dryRun.Output -match "Would apply hardware-aware recommendation") -Message "Dry run should describe the local config write."

        $apply = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/apply-recommended-agent-config.ps1") `
            -Arguments @("-TargetRepo", $targetRoot, "-RecommendationPath", $recommendationPath, "-OllamaBaseUrl", "http://example.local:11434")
        Assert-Equal -Actual $apply.ExitCode -Expected 0 -Message "Apply recommendation should succeed."

        $localConfigPath = Join-Path $targetRoot ".continue/config.local.yaml"
        Assert-True -Condition (Test-Path -LiteralPath $localConfigPath) -Message "Local config should be written."
        $localConfig = Get-Content -LiteralPath $localConfigPath -Raw
        Assert-True -Condition ($localConfig -match "1 - WRITE SAFE - qwen3\.5:9b") -Message "Local config should include WRITE SAFE lane."
        Assert-True -Condition ($localConfig -match "2 - PLAN ONLY - devstral-small-2:24b") -Message "Local config should include PLAN ONLY lane."
        Assert-True -Condition ($localConfig -match "3 - DEEP REVIEW - qwen3-coder:30b") -Message "Local config should include DEEP REVIEW lane."
        Assert-True -Condition ($localConfig -match "apiBase: http://example.local:11434") -Message "Local config should include the local-only endpoint when requested."
        Assert-True -Condition ($localConfig -notmatch [regex]::Escape($recommendationPath)) -Message "Local config should not record the recommendation file path."

        $globalConfigPath = Join-Path $tempRoot "global-config.yaml"
        $globalApply = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/apply-recommended-agent-config.ps1") `
            -Arguments @("-TargetRepo", $targetRoot, "-RecommendationPath", $recommendationPath, "-OllamaBaseUrl", "http://example.local:11434", "-GlobalConfig", "-GlobalConfigPath", $globalConfigPath)
        Assert-Equal -Actual $globalApply.ExitCode -Expected 0 -Message "Apply recommendation should write global config when requested."
        Assert-True -Condition (Test-Path -LiteralPath $globalConfigPath) -Message "Global config should be written when requested."
        $globalConfig = Get-Content -LiteralPath $globalConfigPath -Raw
        Assert-True -Condition ($globalConfig -match "1 - WRITE SAFE - qwen3\.5:9b") -Message "Global config should include generated model lanes."
        Assert-True -Condition ($globalConfig -match "prompts/repository-discovery\.md") -Message "Global config should include prompt references."
        Assert-True -Condition ($globalConfig -notmatch "file://\./") -Message "Global config should not contain project-relative file URIs."
        Assert-True -Condition ($globalConfig -notmatch "^rules:") -Message "Global config should omit rules by default."
        Assert-True -Condition ($globalConfig -notmatch [regex]::Escape($recommendationPath)) -Message "Global config should not record the recommendation file path."

        $script = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/apply-recommended-agent-config.ps1") -Raw
        $sharedScript = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/apply-recommended-agent-config.shared.sh") -Raw
        $doc = Get-Content -LiteralPath (Join-Path $repoRoot "docs/hardware-aware-recommendations.md") -Raw
        Assert-True -Condition ($script -match "GlobalConfig") -Message "PowerShell apply script should support global config output."
        Assert-True -Condition ($sharedScript -match "--global-config") -Message "Bash apply script should support global config output."
        Assert-True -Condition ($doc -match "global Continue config") -Message "Docs should explain global config generation."
        Assert-True -Condition ($doc -match "Do not commit this file") -Message "Docs should warn not to commit local config."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $targetRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
if ($failed) {
    Write-Host "Test run failed. $testCount tests executed." -ForegroundColor Red
    exit 1
}

Write-Host "Test run passed. $testCount tests executed." -ForegroundColor Green
exit 0

Invoke-PackTest "shared asset installation docs define centralized config strategy" {
    $docPath = Join-Path $repoRoot "docs/shared-asset-installation.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"
    $todoPath = Join-Path $repoRoot "TODO.md"
    $hardwareDocPath = Join-Path $repoRoot "docs/hardware-aware-recommendations.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Shared asset installation doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw
    $hardwareDoc = Get-Content -LiteralPath $hardwareDocPath -Raw

    Assert-True -Condition ($doc -match "Project-Local Mode") -Message "Shared asset doc should preserve project-local mode."
    Assert-True -Condition ($doc -match "Shared-Assets Mode") -Message "Shared asset doc should define shared-assets mode."
    Assert-True -Condition ($doc -match "SharedAssetsPath") -Message "Shared asset doc should define explicit path option."
    Assert-True -Condition ($doc -match "file://\./") -Message "Shared asset doc should warn against project-relative global references."
    Assert-True -Condition ($doc -match "duplicate rule") -Message "Shared asset doc should cover duplicate-rule behavior."
    Assert-True -Condition ($doc -match "Rollback") -Message "Shared asset doc should include rollback guidance."
    Assert-True -Condition ($readme -match "docs/shared-asset-installation.md") -Message "README should link shared asset doc."
    Assert-True -Condition ($hardwareDoc -match "docs/shared-asset-installation.md") -Message "Hardware-aware docs should link shared asset planning."
    Assert-True -Condition ($todo -match "centralized shared asset") -Message "TODO should track centralized shared asset work."
    Assert-True -Condition ($roadmap -match "centralized shared asset") -Message "Roadmap should track centralized shared asset work."
}
