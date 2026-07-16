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

function Get-TestBashPath {
    $gitBash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"
    if (Test-Path -LiteralPath $gitBash) { return $gitBash }

    $bash = Get-Command bash -ErrorAction SilentlyContinue
    if ($bash -and $bash.Source -notmatch '\\WindowsApps\\bash\.exe$') {
        return $bash.Source
    }

    return $null
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
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

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
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw

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
    Assert-True -Condition ($releaseDoc -match "Milestone 19 Completion Basis") -Message "Release docs should record the current Milestone 19 completion basis."
    Assert-True -Condition ($releaseDoc -match "config/evidence-catalog\.tsv") -Message "Release docs should cite evidence catalog for Milestone 19."
    Assert-True -Condition ($releaseDoc -match "partial for cross-agent install/configure/test parity") -Message "Release docs should keep cross-agent parity gap visible."
    Assert-True -Condition ($releaseDoc -match "Verify Checksums") -Message "Release docs should explain checksum verification."
    Assert-True -Condition ($releaseDoc -match "build-release-package") -Message "Release docs should mention packaging scripts."
    Assert-True -Condition ($releaseDoc -match "GitHub Release") -Message "Release docs should explain GitHub release uploads."
    Assert-True -Condition ($roadmap -match "\| Milestone 19: Installer Profiles, Evidence Catalog, And Release Packaging \| Partial \|") -Message "Roadmap should mark Milestone 19 partial for cross-agent parity."
    Assert-True -Condition ($roadmap -match "Cross-agent parity gap") -Message "Roadmap should state the Milestone 19 cross-agent parity gap."
    Assert-True -Condition ($todo -match "\[x\] Complete Milestone 19 Continue installer profile, evidence catalog, and release packaging exit criteria") -Message "TODO should mark Continue-scoped Milestone 19 completion complete."
    Assert-True -Condition ($todo -match "\[ \] Complete Milestone 19 cross-agent install/configure/test script parity") -Message "TODO should keep cross-agent Milestone 19 parity pending."
    Assert-True -Condition ($todo -match "Solution Architecture Review Backlog") -Message "TODO should keep future surface profile work in the architecture backlog."
    Assert-True -Condition ($todo -match "\[ \] Add future surface-specific profile generation after non-Continue validation") -Message "TODO should keep future surface-specific profile generation pending."
    Assert-True -Condition ((Get-Content -LiteralPath $gitignorePath) -contains "dist/") -Message "dist output should be ignored."
}
Invoke-PackTest "evidence catalog has valid schema and sanitized links" {
    $catalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
    $docPath = Join-Path $repoRoot "docs/evidence-catalog.md"
    $allowedStatuses = @(
        "candidate-only",
        "plan-review-candidate",
        "plan-validated",
        "review-validated",
        "read-only-tool-validated",
        "read-only-cli-validated",
        "write-smoke-validated",
        "approved-write-ready",
        "static-validated",
        "validated-by-tests",
        "partial-pass"
    )

    Assert-True -Condition (Test-Path -LiteralPath $catalogPath) -Message "Evidence catalog should exist."
    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Evidence catalog docs should exist."

    $lines = Get-Content -LiteralPath $catalogPath | Where-Object { $_.Trim().Length -gt 0 }
    Assert-True -Condition ($lines.Count -gt 1) -Message "Evidence catalog should include rows."
    Assert-Equal -Actual $lines[0] -Expected "schema_version`tarea`tsubject`tsurface`tsurface_version`tprovider`tos`tmodel`toperation`tvalidation_mode`tstatus`tevidence`tnotes" -Message "Evidence catalog header changed."

    $seenApprovedWrite = $false
    $seenCandidateOnly = $false
    $seenReadOnly = $false

    foreach ($line in $lines[1..($lines.Count - 1)]) {
        $parts = $line -split "`t", 13
        Assert-Equal -Actual $parts.Count -Expected 13 -Message "Evidence catalog row should have thirteen tab-delimited columns: $line"

        foreach ($part in $parts) {
            Assert-True -Condition ($part.Trim().Length -gt 0) -Message "Evidence catalog row contains an empty field: $line"
        }

        Assert-Equal -Actual $parts[0] -Expected "2" -Message "Evidence catalog rows should use schema version 2."
        $status = $parts[10]
        $evidence = $parts[11]
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
    $contractPath = Join-Path $repoRoot "config/capability-evidence-contract.json"
    Assert-True -Condition (Test-Path -LiteralPath $contractPath) -Message "Capability Evidence Contract should exist."
    $contract = Get-Content -LiteralPath $contractPath -Raw | ConvertFrom-Json
    Assert-Equal -Actual $contract.schemaVersion -Expected 2 -Message "Capability Evidence Contract should be version 2."
    Assert-True -Condition (-not $contract.aggregation.allowCrossSurfaceInheritance) -Message "Contract should prohibit cross-surface inheritance."
    Assert-True -Condition (-not $contract.aggregation.allowCrossOperationInheritance) -Message "Contract should prohibit cross-operation inheritance."
    Assert-True -Condition ($contract.aggregation.retainAllEvidencePaths) -Message "Contract should retain provenance."
    Assert-True -Condition ($doc -match "config/evidence-catalog\.tsv") -Message "Evidence catalog docs should reference the TSV file."
    Assert-True -Condition ($doc -match "approved-write-ready") -Message "Evidence catalog docs should define approved-write-ready."
    Assert-True -Condition ($doc -match "Capability Evidence Contract v2") -Message "Evidence catalog docs should explain contract v2."
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

Invoke-PackTest "model fit catalog defines explicit memory assumptions" {
    $catalogPath = Join-Path $repoRoot "config/model-fit-profiles.json"
    $catalog = Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json
    Assert-Equal -Actual $catalog.schemaVersion -Expected 1 -Message "Model fit catalog should use schema version 1."
    Assert-True -Condition ($catalog.defaults.contextTargetTokens -ge 1024) -Message "Model fit catalog should define a usable default context target."
    Assert-True -Condition ($catalog.defaults.memoryReserveGb -gt 0) -Message "Model fit catalog should define a positive memory reserve."
    Assert-True -Condition ($catalog.profiles.Count -ge 1) -Message "Model fit catalog should include curated profiles."
    foreach ($profile in $catalog.profiles) {
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($profile.matchPattern)) -Message "Each fit profile should define a match pattern."
        Assert-True -Condition ($profile.estimatedWeightsGb -gt 0) -Message "Each fit profile should define estimated weight memory."
        Assert-True -Condition ($profile.baselineContextTokens -gt 0 -and $profile.kvCacheGbAtBaseline -gt 0) -Message "Each fit profile should define context-sensitive cache assumptions."
        Assert-True -Condition ($profile.runtimeOverheadGb -gt 0) -Message "Each fit profile should define runtime overhead."
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($profile.quantizationAssumption)) -Message "Each fit profile should disclose its quantization assumption."
        Assert-True -Condition ($profile.architecture -in @("dense", "mixture-of-experts")) -Message "Each fit profile should identify its architecture class."
    }
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
    $sampleEvidencePath = Join-Path $repoRoot "examples/sample-repository-factory-validation.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Multi-repository validation doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $runtimeOutputVerificationPath) -Message "Runtime output verification doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $templatePath) -Message "Multi-repository validation evidence template should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $runtimeOutputVerification = Get-Content -LiteralPath $runtimeOutputVerificationPath -Raw
    $template = Get-Content -LiteralPath $templatePath -Raw
    $sampleEvidence = Get-Content -LiteralPath $sampleEvidencePath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw

    Assert-True -Condition ($doc -match "Repository Categories") -Message "Multi-repository validation doc should define repository categories."
    Assert-True -Condition ($doc -match "Legacy \.NET") -Message "Multi-repository validation doc should cover legacy .NET repositories."
    Assert-True -Condition ($doc -match "Modern \.NET") -Message "Multi-repository validation doc should cover modern .NET repositories."
    Assert-True -Condition ($doc -match "Documentation or configuration pack") -Message "Multi-repository validation doc should cover documentation/config repositories."
    Assert-True -Condition ($doc -match "Frontend application") -Message "Multi-repository validation doc should cover frontend repositories."
    Assert-True -Condition ($doc -match "Script or tooling repository") -Message "Multi-repository validation doc should cover script/tooling repositories."
    Assert-True -Condition ($doc -match "clean git working tree") -Message "Multi-repository validation doc should require clean-tree validation."
    Assert-True -Condition ($doc -match "deterministic output verification") -Message "Multi-repository validation doc should require output verification."
    Assert-True -Condition ($doc -match "local sample repositories") -Message "Multi-repository validation doc should allow generated local samples."
    Assert-True -Condition ($doc -match "Milestone 13 Completion Basis") -Message "Multi-repository validation doc should define Milestone 13 completion basis."
    Assert-True -Condition ($doc -match "Generated samples are acceptable for the milestone coverage target") -Message "Multi-repository validation doc should allow generated samples to satisfy milestone coverage."
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
    foreach ($sample in @("python-api", "typescript-frontend", "node-service", "java-spring-api", "go-service", "rust-cli", "iac-terraform-kubernetes", "sql-migrations")) {
        Assert-True -Condition ($sampleEvidence -match [regex]::Escape($sample)) -Message "Sample evidence should support Milestone 13 category coverage for $sample."
    }
    Assert-True -Condition ($roadmap -match "Milestone 13: Broader Multi-Repository Validation \| Complete") -Message "Roadmap should mark Milestone 13 complete."
    Assert-True -Condition ($roadmap -match "future real-repository runs continue as evidence expansion") -Message "Roadmap should keep real repository validation as evidence expansion."
    Assert-True -Condition ($todo -match "\[x\] Complete Milestone 13 coverage") -Message "TODO should mark Milestone 13 coverage complete."
    Assert-True -Condition ($todo -match "Future Multi-Repository Evidence Expansion") -Message "TODO should keep future multi-repository expansion separate."
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
    foreach ($sample in @("node-service", "java-spring-api", "go-service", "rust-cli", "iac-terraform-kubernetes", "sql-migrations")) {
        Assert-True -Condition ($evidence -match [regex]::Escape($sample)) -Message "Evidence should include expanded generated category sample: $sample."
    }
    Assert-True -Condition ($evidence -match "Generated Category Expansion Validation") -Message "Evidence should record expanded generated category validation."
    Assert-True -Condition ($evidence -match "Runtime context generation") -Message "Evidence should mention runtime context generation."
    Assert-True -Condition ($evidence -match "does not prove model or editor Agent behavior") -Message "Evidence should avoid overstating Agent validation."
    Assert-True -Condition ($evidence -match "No private local paths") -Message "Evidence should include sanitization checklist."
    Assert-True -Condition ($doc -match "Expanded generated-category evidence") -Message "Sample factory docs should mention expanded generated-category evidence."
    Assert-True -Condition ($doc -match "examples/sample-repository-factory-validation\.md") -Message "Sample factory doc should link evidence."
    Assert-True -Condition ($readme -match "examples/sample-repository-factory-validation\.md") -Message "README should link evidence."
}

Invoke-PackTest "sample repository factory docs define generated fixtures" {
    $docPath = Join-Path $repoRoot "docs/sample-repository-factory.md"
    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath (Join-Path $repoRoot "README.md") -Raw
    $roadmap = Get-Content -LiteralPath (Join-Path $repoRoot "ROADMAP.md") -Raw
    $todo = Get-Content -LiteralPath (Join-Path $repoRoot "TODO.md") -Raw
    $evidence = Get-Content -LiteralPath (Join-Path $repoRoot "examples/sample-repository-factory-validation.md") -Raw

    Assert-True -Condition ($doc -match "Milestone 16 Completion Basis") -Message "Sample factory doc should record Milestone 16 completion basis."
    Assert-True -Condition ($doc -match "examples/sample-repository-factory-validation\.md") -Message "Sample factory doc should link committed evidence."
    Assert-True -Condition ($doc -match "python-api") -Message "Sample factory doc should list python-api."
    Assert-True -Condition ($doc -match "typescript-frontend") -Message "Sample factory doc should list typescript-frontend."
    foreach ($sample in @("node-service", "java-spring-api", "go-service", "rust-cli", "iac-terraform-kubernetes", "sql-migrations")) {
        Assert-True -Condition ($doc -match [regex]::Escape($sample)) -Message "Sample factory doc should list expanded generated category sample: $sample."
    }
    Assert-True -Condition ($doc -match "generate-sample-repositories\.ps1") -Message "Sample factory doc should include the Windows script."
    Assert-True -Condition ($doc -match "generate-sample-repositories\.linux\.sh") -Message "Sample factory doc should include the Linux script."
    Assert-True -Condition ($doc -match "generate-sample-repositories\.macos\.sh") -Message "Sample factory doc should include the macOS script."
    Assert-True -Condition ($doc -match "production starter projects") -Message "Sample factory doc should include guardrails."
    Assert-True -Condition ($evidence -match "Generated Category Expansion Validation") -Message "Sample factory evidence should include expanded validation."
    Assert-True -Condition ($readme -match "docs/sample-repository-factory\.md") -Message "README should link to sample factory docs."
    Assert-True -Condition ($roadmap -match "\| Milestone 16: Sample Repository Factory \| Complete \|") -Message "Roadmap should mark Milestone 16 complete."
    Assert-True -Condition ($todo -match "\[x\] Complete Milestone 16 sample repository factory exit criteria") -Message "TODO should mark Milestone 16 completion audit complete."
}

Invoke-PackTest "agent surface docs define portability boundary" {
    $docPath = Join-Path $repoRoot "docs/agent-surface-options.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Agent surface options doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw

    Assert-True -Condition ($doc -match "Continue is the first supported surface") -Message "Agent surface doc should keep Continue as the current supported surface."
    Assert-True -Condition ($doc -match "Compatibility Matrix") -Message "Agent surface doc should include an explicit compatibility matrix."
    Assert-True -Condition ($doc -match "Milestone 14 Positioning Completion Basis") -Message "Agent surface doc should record scoped Milestone 14 completion basis."
    Assert-True -Condition ($doc -match "Full live validation parity belongs to Milestone 17") -Message "Agent surface doc should keep full validation parity gap visible."
    Assert-True -Condition ($doc -match "docs/cline-readonly-validation\.md") -Message "Agent surface doc should cite non-Continue read-only validation evidence."
    Assert-True -Condition ($doc -match "docs/surface-specific-config-bundles\.md") -Message "Agent surface doc should cite surface-specific config bundle policy."
    Assert-True -Condition ($doc -match "docs/setup-paths\.md") -Message "Agent surface doc should cite beginner and team setup paths."
    Assert-True -Condition ($doc -match "Candidate means") -Message "Agent surface doc should define candidate status."
    Assert-True -Condition ($doc -match "Read-only validated") -Message "Agent surface doc should define read-only validation."
    Assert-True -Condition ($doc -match "Plan validated") -Message "Agent surface doc should define plan validation."
    Assert-True -Condition ($doc -match "Approved-write ready") -Message "Agent surface doc should define approved-write readiness."
    foreach ($surface in @("Continue", "Cline", "Aider", "Kilo Code", "OpenCode", "OpenHands", "Roo Code")) {
        Assert-True -Condition ($doc -match [regex]::Escape($surface)) -Message "Agent surface doc should include $surface."
    }
    Assert-True -Condition ($doc -match "External verification commands") -Message "Agent surface doc should require external verification evidence."
    Assert-True -Condition ($doc -match "Blocked") -Message "Agent surface doc should block unvalidated approved writes."
    Assert-True -Condition ($doc -match "Non-Enterprise Use") -Message "Agent surface doc should address non-enterprise users."
    Assert-True -Condition ($readme -match "docs/agent-surface-options.md") -Message "README should link agent surface options."
    Assert-True -Condition ($roadmap -match "\| Milestone 14: Agent Surface Portability And Broader Audience \| Complete \|") -Message "Roadmap should mark Milestone 14 complete for portability and broader-audience scope."
    Assert-True -Condition ($todo -match "\[x\] Complete Milestone 14 positioning, support-boundary, and broader-audience exit criteria") -Message "TODO should mark Milestone 14 positioning scope complete."
    Assert-True -Condition ($todo -match "\[x\] Move full cross-agent validation and install/configure/test parity out of Milestone 14 and keep it tracked in Milestones 17 and 19") -Message "TODO should show full cross-agent parity moved to Milestones 17 and 19."
}


Invoke-PackTest "Cline read-only validation docs define read-only workflow" {
    $docPath = Join-Path $repoRoot "docs/cline-readonly-validation.md"
    $evidencePath = Join-Path $repoRoot "examples/cline-readonly-validation.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $catalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
    $todoPath = Join-Path $repoRoot "TODO.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Cline read-only validation doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $evidencePath) -Message "Cline read-only evidence template should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $evidence = Get-Content -LiteralPath $evidencePath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $catalog = Get-Content -LiteralPath $catalogPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw

    Assert-True -Condition ($doc -match "read-only validation path") -Message "Cline doc should keep validation scoped."
    Assert-True -Condition ($doc -match "Write mode") -Message "Cline doc should mention write mode status."
    Assert-True -Condition (($doc -match "write smoke-test") -and ($doc -match "real-project approved-write blocked")) -Message "Cline doc should distinguish write smoke test from real-project approved write."
    Assert-True -Condition ($doc -match "TOOLS_UNAVAILABLE") -Message "Cline doc should define tool-unavailable failure signals."
    Assert-True -Condition ($doc -match "HALLUCINATED_STRUCTURE") -Message "Cline doc should define hallucinated-structure failure signal."
    Assert-True -Condition ($doc -match "git status --short") -Message "Cline doc should require external git verification."
    Assert-True -Condition ($doc -match "examples/cline-readonly-validation.md") -Message "Cline doc should point at evidence template."
    Assert-True -Condition (($evidence -match "Read-only tool validated") -and ($evidence -match "Write smoke-test validated")) -Message "Cline evidence should record read and write-smoke validation scope."
    Assert-True -Condition ($evidence -match "Validation Record Template") -Message "Cline evidence should include a reusable template."
    Assert-True -Condition ($readme -match "docs/cline-readonly-validation.md") -Message "README should link the Cline validation doc."
    Assert-True -Condition (($catalog -match "Cline read-only validation workflow") -and ($catalog -match "read-only-tool-validated") -and ($catalog -match "Cline approved-write smoke test") -and ($catalog -match "write-smoke-validated")) -Message "Evidence catalog should include Cline read and write-smoke validation workflows."
    Assert-True -Condition ($todo -match "Cline read-only validation guide") -Message "TODO should track Cline validation guide completion."
    Assert-True -Condition ($roadmap -match "Cline read-only validation guide") -Message "Roadmap should track Cline validation guide completion."
}

Invoke-PackTest "Cline CLI model testing docs define automation workflow" {
    $docPath = Join-Path $repoRoot "docs/cline-cli-model-testing.md"
    $psScriptPath = Join-Path $repoRoot "scripts/test-cline-cli-models.ps1"
    $bashScriptPath = Join-Path $repoRoot "scripts/test-cline-cli-models.shared.sh"
    $catalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
    $readmePath = Join-Path $repoRoot "README.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Cline CLI testing doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $psScriptPath) -Message "PowerShell Cline CLI tester should exist."
    Assert-True -Condition (Test-Path -LiteralPath $bashScriptPath) -Message "Bash Cline CLI tester should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $psScript = Get-Content -LiteralPath $psScriptPath -Raw
    $bashScript = Get-Content -LiteralPath $bashScriptPath -Raw
    $catalog = Get-Content -LiteralPath $catalogPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw

    Assert-True -Condition ($doc -match "Cline CLI Model Testing") -Message "Cline CLI testing doc should have a clear title."
    Assert-True -Condition ($doc -match "test-cline-cli-models") -Message "Cline CLI testing doc should mention automation scripts."
    Assert-True -Condition ($doc -match "command-template") -Message "Cline CLI testing doc should describe command-template flexibility."
    Assert-True -Condition ($doc -match "Write Smoke Test") -Message "Cline CLI testing doc should define write smoke test flow."
    Assert-True -Condition ($psScript -match "ClineArgumentsTemplate") -Message "PowerShell Cline CLI tester should support argument templates."
    Assert-True -Condition ($psScript -match "IncludeWriteSmoke") -Message "PowerShell Cline CLI tester should support write-smoke tests."
    Assert-True -Condition ($psScript -match "UnloadAfterEach") -Message "PowerShell Cline CLI tester should support model unload after each run."
    Assert-True -Condition ($psScript -match "UnloadAfterEach") -Message "PowerShell Cline CLI tester should support model unload after each run."
    Assert-True -Condition ($psScript -match "runtime-validation-output/sample-repositories") -Message "PowerShell Cline CLI tester should default to disposable generated samples."
    Assert-True -Condition ($psScript -match "Initialize-DisposableGitBaseline") -Message "PowerShell Cline CLI tester should initialize a disposable Git baseline."
    Assert-True -Condition ($bashScript -match "CLINE_ARGS_TEMPLATE") -Message "Bash Cline CLI tester should support argument templates."
    Assert-True -Condition ($bashScript -match "INCLUDE_WRITE_SMOKE") -Message "Bash Cline CLI tester should support write-smoke tests."
    Assert-True -Condition ($bashScript -match "UNLOAD_AFTER_EACH") -Message "Bash Cline CLI tester should support model unload after each run."
    Assert-True -Condition ($bashScript -match "UNLOAD_AFTER_EACH") -Message "Bash Cline CLI tester should support model unload after each run."
    Assert-True -Condition ($catalog -match "Cline CLI model test harness") -Message "Evidence catalog should track Cline CLI harness validation."
    Assert-True -Condition ($readme -match "docs/cline-cli-model-testing.md") -Message "README should link Cline CLI model testing doc."
}
Invoke-PackTest "agent CLI surface testing docs define shared automation workflow" {
    $docPath = Join-Path $repoRoot "docs/agent-cli-surface-model-testing.md"
    $aiderDocPath = Join-Path $repoRoot "docs/aider-cli-model-testing.md"
    $evidencePath = Join-Path $repoRoot "examples/aider-validation.md"
    $psScriptPath = Join-Path $repoRoot "scripts/test-agent-cli-surface-models.ps1"
    $bashScriptPath = Join-Path $repoRoot "scripts/test-agent-cli-surface-models.shared.sh"
    $surfaceDefaultsPath = Join-Path $repoRoot "config/agent-cli-surface-defaults.json"
    $catalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
    $readmePath = Join-Path $repoRoot "README.md"
    $surfaceDocPath = Join-Path $repoRoot "docs/agent-surface-options.md"
    $promotionGatesPath = Join-Path $repoRoot "docs/agent-surface-promotion-gates.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Shared agent CLI testing doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $aiderDocPath) -Message "Aider CLI wrapper doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $evidencePath) -Message "Aider evidence template should exist."
    Assert-True -Condition (Test-Path -LiteralPath $psScriptPath) -Message "PowerShell shared agent CLI tester should exist."
    Assert-True -Condition (Test-Path -LiteralPath $bashScriptPath) -Message "Bash shared agent CLI tester should exist."
    Assert-True -Condition (Test-Path -LiteralPath $surfaceDefaultsPath) -Message "Agent CLI surface defaults catalog should exist."
    Assert-True -Condition (Test-Path -LiteralPath $promotionGatesPath) -Message "Agent surface promotion gates doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $aiderDoc = Get-Content -LiteralPath $aiderDocPath -Raw
    $evidence = Get-Content -LiteralPath $evidencePath -Raw
    $psScript = Get-Content -LiteralPath $psScriptPath -Raw
    $bashScript = Get-Content -LiteralPath $bashScriptPath -Raw
    $surfaceDefaults = Get-Content -LiteralPath $surfaceDefaultsPath -Raw | ConvertFrom-Json
    $catalog = Get-Content -LiteralPath $catalogPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $surfaceDoc = Get-Content -LiteralPath $surfaceDocPath -Raw
    $promotionGates = Get-Content -LiteralPath $promotionGatesPath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw

    Assert-True -Condition ($doc -match "Agent CLI Surface Model Testing") -Message "Shared CLI testing doc should have a clear title."
    Assert-True -Condition ($doc -match "live validation is blocked by task execution") -Message "Shared CLI doc should keep Kilo Code's live task-execution blocker explicit."
    foreach ($surface in @("Aider", "Roo Code", "Kilo Code", "OpenCode")) {
        Assert-True -Condition ($doc -match [regex]::Escape($surface)) -Message "Shared CLI testing doc should mention $surface."
        Assert-True -Condition ($catalog -match [regex]::Escape($surface)) -Message "Evidence catalog should mention $surface."
        Assert-True -Condition ($surfaceDoc -match [regex]::Escape($surface)) -Message "Agent surface docs should mention $surface."
    }
    Assert-True -Condition ($doc -match "OpenHands is platform-style") -Message "Shared CLI doc should avoid pretending OpenHands is a simple CLI harness target."
    Assert-True -Condition ($doc -match "Dry run") -Message "Shared CLI doc should explain dry-run behavior."
    Assert-True -Condition ($doc -match "UnloadAfterEach") -Message "Shared CLI doc should explain model unload support."
    Assert-True -Condition ($doc -match "test-agent-cli-surface-models") -Message "Shared CLI doc should mention the generic harness."
    Assert-True -Condition ($aiderDoc -match "agent-cli-surface-model-testing") -Message "Aider doc should point to the shared CLI harness doc."
    Assert-True -Condition ($evidence -match "Aider Validation Evidence") -Message "Aider evidence template should have a clear title."
    Assert-True -Condition ($evidence -match "Sanitization Checklist") -Message "Aider evidence template should include sanitization checklist."
    Assert-True -Condition ($psScript -match "SurfaceName") -Message "PowerShell shared CLI tester should support surface names."
    Assert-True -Condition ($psScript -match "agent-cli-surface-defaults\.json") -Message "PowerShell shared CLI tester should load default surface metadata from the catalog."
    Assert-True -Condition ($psScript -match "AgentArgumentsTemplate") -Message "PowerShell shared CLI tester should support argument templates."
    Assert-True -Condition ($psScript -match "IncludeWriteSmoke") -Message "PowerShell shared CLI tester should support write-smoke tests."
    Assert-True -Condition ($psScript -match "UnloadAfterEach") -Message "PowerShell shared CLI tester should support model unload after each run."
    Assert-True -Condition ($psScript -match "Initialize-DisposableGitBaseline") -Message "PowerShell shared CLI tester should initialize a disposable Git baseline."
    Assert-True -Condition ($bashScript -match "AGENT_ARGS_TEMPLATE") -Message "Bash shared CLI tester should support argument templates."
    Assert-True -Condition ($bashScript -match "agent-cli-surface-defaults\.json") -Message "Bash shared CLI tester should load default surface metadata from the catalog."
    Assert-True -Condition ($bashScript -match "load_surface_defaults") -Message "Bash shared CLI tester should centralize default loading."
    Assert-True -Condition ($bashScript -match "UNLOAD_AFTER_EACH") -Message "Bash shared CLI tester should support model unload after each run."
    Assert-True -Condition ($catalog -match "Shared agent CLI model test harness") -Message "Evidence catalog should track the shared CLI harness."
    Assert-True -Condition ($readme -match "docs/agent-cli-surface-model-testing.md") -Message "README should link shared agent CLI model testing doc."
    Assert-True -Condition ($readme -match "docs/agent-surface-promotion-gates.md") -Message "README should link agent surface promotion gates."
    Assert-True -Condition ($surfaceDoc -match "docs/agent-surface-promotion-gates.md") -Message "Agent surface options should link promotion gates."
    foreach ($surface in @("Cline", "Aider", "Roo Code", "Kilo Code", "OpenCode", "OpenHands")) {
        Assert-True -Condition ($promotionGates -match [regex]::Escape($surface)) -Message "Promotion gates should cover $surface."
    }
    Assert-True -Condition ($promotionGates -match "Milestone 17 Cline And Aider Completion Basis") -Message "Promotion gates should record scoped Milestone 17 completion basis."
    Assert-True -Condition ($promotionGates -match "partial for full tracked-surface compatibility") -Message "Promotion gates should keep full surface compatibility gap visible."
    Assert-True -Condition ($promotionGates -match "Approved-write ready") -Message "Promotion gates should define approved-write readiness."
    Assert-True -Condition ($promotionGates -match "real-project approved-write") -Message "Promotion gates should block real-project promotion from generated evidence alone."
    Assert-True -Condition ($promotionGates -match "Roo Code is historical only") -Message "Promotion gates should keep Roo Code retired upstream."
    $openHandsBoundary = Get-Content -Raw (Join-Path $repoRoot "docs/openhands-validation-boundary.md")
    Assert-True -Condition ($openHandsBoundary -match "OpenHands Validation Boundary") -Message "OpenHands boundary doc should have a clear title."
    Assert-True -Condition ($openHandsBoundary -match "disposable generated repository") -Message "OpenHands boundary should require a generated sample."
    Assert-True -Condition ($openHandsBoundary -match "SSH keys") -Message "OpenHands boundary should exclude host credentials."
    Assert-True -Condition ($openHandsBoundary -match "Docker socket") -Message "OpenHands boundary should exclude privileged container access."
    Assert-True -Condition ($openHandsBoundary -match "unrestricted network access") -Message "OpenHands boundary should limit network access."
    Assert-True -Condition ($promotionGates -match "docs/openhands-validation-boundary\.md") -Message "Promotion gates should link the OpenHands validation boundary."
    Assert-True -Condition ($roadmap -match "\| Milestone 17: Agent Surface Compatibility Validation \| Partial \|") -Message "Roadmap should mark Milestone 17 partial for full tracked-surface validation."
    Assert-True -Condition ($todo -match "\[x\] Complete Milestone 17 Cline and Aider compatibility validation exit criteria") -Message "TODO should mark Cline/Aider Milestone 17 scope complete."
    Assert-True -Condition ($todo -match "\[ \] Complete Milestone 17 full tracked-surface compatibility validation") -Message "TODO should keep full Milestone 17 surface validation pending."
    Assert-True -Condition ($todo -match "Future Agent Surface Evidence Expansion") -Message "TODO should track future agent surface evidence expansion."
    Assert-True -Condition ($todo -match "\[x\] Retire Roo Code from future validation") -Message "TODO should keep Roo Code retired upstream."
    Assert-True -Condition ($todo -match "\[ \] Resolve Kilo Code's current local-model task-execution failure") -Message "TODO should keep Kilo CLI validation evidence-gated."
    Assert-True -Condition ($todo -match "\[x\] Add a local-only OpenCode Ollama config generator") -Message "TODO should record the scaffolded OpenCode config generator."
    Assert-True -Condition ($todo -match "\[x\] Validate OpenCode's installed CLI") -Message "TODO should record generated-sample OpenCode CLI validation."
    Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot "docs/opencode-cli-model-testing.md")) -Message "OpenCode setup and validation documentation should exist."
    Assert-True -Condition ($doc -match "Confirmed Command Boundaries") -Message "Shared CLI doc should record verified command boundaries."
    Assert-True -Condition ($doc -match "opencode run") -Message "Shared CLI doc should record the OpenCode non-interactive command."
    Assert-True -Condition ($doc -match "instead of executing the supplied repository task") -Message "Shared CLI doc should keep Kilo task execution evidence-gated."
    Assert-True -Condition ($doc -match "upstream project is archived") -Message "Shared CLI doc should keep Roo Code retired upstream."
    Assert-True -Condition ($todo -match "\[x\] Define a safe OpenHands validation boundary before adding platform-agent validation automation") -Message "TODO should mark the OpenHands validation boundary complete."

    $wrapperBases = @("aider", "roo-code", "kilo-code", "opencode")
    $expectedSurfaceKeys = @("aider-cli", "roo-code-cli", "kilo-code-cli", "opencode-cli")
    foreach ($key in $expectedSurfaceKeys) {
        $default = @($surfaceDefaults.surfaces | Where-Object { $_.surfaceKey -eq $key })
        Assert-True -Condition ($default.Count -eq 1) -Message "Agent CLI defaults catalog should define $key exactly once."
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($default[0].surfaceName)) -Message "Agent CLI defaults should name $key."
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($default[0].agentCommand)) -Message "Agent CLI defaults should define command for $key."
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($default[0].agentArgumentsTemplate)) -Message "Agent CLI defaults should define read template for $key."
        if ($key -ne "opencode-cli") {
            Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($default[0].modelArgumentTemplate)) -Message "Agent CLI defaults should define model template for $key."
        }
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($default[0].installHint)) -Message "Agent CLI defaults should define install hint for $key."
    }
    foreach ($base in $wrapperBases) {
        $wrapperPs = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/test-$base-cli-models.ps1") -Raw
        $wrapperSh = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/test-$base-cli-models.shared.sh") -Raw
        Assert-True -Condition ($wrapperPs -match "test-agent-cli-surface-models.ps1") -Message "$base PowerShell wrapper should delegate to the shared harness."
        Assert-True -Condition ($wrapperPs -match "SurfaceKey" -and $wrapperPs -notmatch "InstallHint") -Message "$base PowerShell wrapper should rely on shared surface defaults."
        Assert-True -Condition ($wrapperSh -match "test-agent-cli-surface-models.shared.sh") -Message "$base Bash wrapper should delegate to the shared harness."
        Assert-True -Condition ($wrapperSh -match "--surface-key" -and $wrapperSh -notmatch "--install-hint" -and $wrapperSh -notmatch "--agent-command") -Message "$base Bash wrapper should rely on shared surface defaults."
    }
}
Invoke-PackTest "Continue CLI model testing docs define automation workflow" {
    $docPath = Join-Path $repoRoot "docs/continue-cli-model-testing.md"
    $psScriptPath = Join-Path $repoRoot "scripts/test-continue-cli-models.ps1"
    $bashScriptPath = Join-Path $repoRoot "scripts/test-continue-cli-models.shared.sh"
    $catalogPath = Join-Path $repoRoot "config/evidence-catalog.tsv"
    $readmePath = Join-Path $repoRoot "README.md"
    $surfaceDocPath = Join-Path $repoRoot "docs/agent-surface-options.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Continue CLI testing doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $psScriptPath) -Message "PowerShell Continue CLI tester should exist."
    Assert-True -Condition (Test-Path -LiteralPath $bashScriptPath) -Message "Bash Continue CLI tester should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $psScript = Get-Content -LiteralPath $psScriptPath -Raw
    $bashScript = Get-Content -LiteralPath $bashScriptPath -Raw
    $catalog = Get-Content -LiteralPath $catalogPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $surfaceDoc = Get-Content -LiteralPath $surfaceDocPath -Raw

    Assert-True -Condition ($doc -match "Continue CLI Model Testing") -Message "Continue CLI testing doc should have a clear title."
    Assert-True -Condition ($doc -match "test-continue-cli-models") -Message "Continue CLI testing doc should mention automation scripts."
    Assert-True -Condition ($doc -match "command-template") -Message "Continue CLI testing doc should describe command-template flexibility."
    Assert-True -Condition ($doc -match "Write Smoke Test") -Message "Continue CLI testing doc should define write smoke test flow."
    Assert-True -Condition ($doc -match "editor Apply") -Message "Continue CLI testing doc should distinguish CLI from editor Apply validation."
    Assert-True -Condition ($psScript -match "ContinueArgumentsTemplate") -Message "PowerShell Continue CLI tester should support argument templates."
    Assert-True -Condition ($psScript -match "ConfigPath") -Message "PowerShell Continue CLI tester should support config paths."
    Assert-True -Condition ($psScript -match "IncludeWriteSmoke") -Message "PowerShell Continue CLI tester should support write-smoke tests."
    Assert-True -Condition ($psScript -match "UnloadAfterEach") -Message "PowerShell Continue CLI tester should support model unload after each run."
    Assert-True -Condition ($psScript -match "UnloadAfterEach") -Message "PowerShell Continue CLI tester should support model unload after each run."
    Assert-True -Condition ($psScript -match "runtime-validation-output/sample-repositories") -Message "PowerShell Continue CLI tester should default to disposable generated samples."
    Assert-True -Condition ($psScript -match "Initialize-DisposableGitBaseline") -Message "PowerShell Continue CLI tester should initialize a disposable Git baseline."
    Assert-True -Condition ($bashScript -match "CONTINUE_ARGS_TEMPLATE") -Message "Bash Continue CLI tester should support argument templates."
    Assert-True -Condition ($bashScript -match "INCLUDE_WRITE_SMOKE") -Message "Bash Continue CLI tester should support write-smoke tests."
    Assert-True -Condition ($bashScript -match "UNLOAD_AFTER_EACH") -Message "Bash Continue CLI tester should support model unload after each run."
    Assert-True -Condition ($bashScript -match "UNLOAD_AFTER_EACH") -Message "Bash Continue CLI tester should support model unload after each run."
    Assert-True -Condition ($catalog -match "Continue CLI model test harness") -Message "Evidence catalog should track Continue CLI harness validation."
    Assert-True -Condition ($readme -match "docs/continue-cli-model-testing.md") -Message "README should link Continue CLI model testing doc."
    Assert-True -Condition ($surfaceDoc -match "docs/continue-cli-model-testing.md") -Message "Agent surface docs should link Continue CLI testing doc."
}
Invoke-PackTest "language support docs define staged multi-language boundary" {
    $docPath = Join-Path $repoRoot "docs/language-support.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"
    $todoPath = Join-Path $repoRoot "TODO.md"
    $workflowEvidencePath = Join-Path $repoRoot "examples/multi-language-workflow-validation.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Language support doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $workflowEvidencePath) -Message "Multi-language workflow evidence should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw
    $workflowEvidence = Get-Content -LiteralPath $workflowEvidencePath -Raw

    Assert-True -Condition ($doc -match "\.NET.*most mature") -Message "Language support doc should identify .NET as the current mature path."
    Assert-True -Condition ($doc -match "Milestone 15 Completion Basis") -Message "Language support doc should record Milestone 15 completion basis."
    Assert-True -Condition ($doc -match "examples/multi-language-workflow-validation\.md") -Message "Language support doc should link multi-language workflow evidence."
    Assert-True -Condition ($doc -match "Python") -Message "Language support doc should include Python."
    Assert-True -Condition ($doc -match "JavaScript / TypeScript") -Message "Language support doc should include JavaScript/TypeScript."
    Assert-True -Condition ($doc -match "Infrastructure as Code") -Message "Language support doc should include Infrastructure as Code."
    Assert-True -Condition ($doc -match "Do not apply \.NET-specific advice") -Message "Language support doc should guard against .NET advice in non-.NET repos."
    Assert-True -Condition (($workflowEvidence -match "Python API Sample") -and ($workflowEvidence -match "TypeScript Frontend Sample")) -Message "Workflow evidence should include Python and TypeScript samples."
    Assert-True -Condition (($workflowEvidence -match "Repository discovery \| Passed verification \| Passed verification") -and ($workflowEvidence -match "Implementation planning \| Passed verification \| Passed verification") -and ($workflowEvidence -match "Code review \| Passed verification \| Passed verification")) -Message "Workflow evidence should show required Python and TypeScript validation passes."
    Assert-True -Condition ($readme -match "docs/language-support.md") -Message "README should link language support doc."
    Assert-True -Condition ($roadmap -match "\| Milestone 15: Multi-Language Engineering Support \| Complete \|") -Message "Roadmap should mark Milestone 15 complete."
    Assert-True -Condition ($todo -match "\[x\] Validate repository discovery, implementation planning, and code review against Python and JavaScript/TypeScript samples") -Message "TODO should mark required Python and TypeScript validation complete."
}


Invoke-PackTest "optional language rule packs are evidence-gated and not globally loaded" {
    $pythonRulePath = Join-Path $repoRoot ".continue/rule-packs/python.md"
    $typescriptRulePath = Join-Path $repoRoot ".continue/rule-packs/typescript.md"
    $javaRulePath = Join-Path $repoRoot ".continue/rule-packs/java.md"
    $goRulePath = Join-Path $repoRoot ".continue/rule-packs/go.md"
    $rustRulePath = Join-Path $repoRoot ".continue/rule-packs/rust.md"
    $sqlRulePath = Join-Path $repoRoot ".continue/rule-packs/sql.md"
    $iacRulePath = Join-Path $repoRoot ".continue/rule-packs/infrastructure-as-code.md"
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
    Assert-True -Condition (Test-Path -LiteralPath $javaRulePath) -Message "Java optional rule pack should exist."
    Assert-True -Condition (Test-Path -LiteralPath $goRulePath) -Message "Go optional rule pack should exist."
    Assert-True -Condition (Test-Path -LiteralPath $rustRulePath) -Message "Rust optional rule pack should exist."
    Assert-True -Condition (Test-Path -LiteralPath $sqlRulePath) -Message "SQL optional rule pack should exist."
    Assert-True -Condition (Test-Path -LiteralPath $iacRulePath) -Message "Infrastructure as Code optional rule pack should exist."
    Assert-True -Condition (Test-Path -LiteralPath $languageRuleDocPath) -Message "Language rule-pack doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $languageEvidencePath) -Message "Language rule-pack validation evidence should exist."
    Assert-True -Condition (Test-Path -LiteralPath $workflowEvidencePath) -Message "Multi-language workflow validation evidence should exist."

    $pythonRule = Get-Content -LiteralPath $pythonRulePath -Raw
    $typescriptRule = Get-Content -LiteralPath $typescriptRulePath -Raw
    $javaRule = Get-Content -LiteralPath $javaRulePath -Raw
    $goRule = Get-Content -LiteralPath $goRulePath -Raw
    $rustRule = Get-Content -LiteralPath $rustRulePath -Raw
    $sqlRule = Get-Content -LiteralPath $sqlRulePath -Raw
    $iacRule = Get-Content -LiteralPath $iacRulePath -Raw
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
    Assert-True -Condition ($javaRule -match "optional: true") -Message "Java rule pack should be marked optional."
    Assert-True -Condition ($javaRule -match "pom\.xml") -Message "Java rule pack should require Java metadata evidence."
    Assert-True -Condition ($javaRule -match "unconfirmed") -Message "Java rule pack should prefer unconfirmed over guesses."
    Assert-True -Condition ($goRule -match "optional: true") -Message "Go rule pack should be marked optional."
    Assert-True -Condition ($goRule -match "go\.mod") -Message "Go rule pack should require Go module evidence."
    Assert-True -Condition ($goRule -match "unconfirmed") -Message "Go rule pack should prefer unconfirmed over guesses."
    Assert-True -Condition ($rustRule -match "optional: true") -Message "Rust rule pack should be marked optional."
    Assert-True -Condition ($rustRule -match "Cargo\.toml") -Message "Rust rule pack should require Cargo evidence."
    Assert-True -Condition ($rustRule -match "unconfirmed") -Message "Rust rule pack should prefer unconfirmed over guesses."
    Assert-True -Condition ($sqlRule -match "optional: true") -Message "SQL rule pack should be marked optional."
    Assert-True -Condition ($sqlRule -match "\.sql") -Message "SQL rule pack should require SQL or migration evidence."
    Assert-True -Condition ($sqlRule -match "unconfirmed") -Message "SQL rule pack should prefer unconfirmed over guesses."
    Assert-True -Condition ($iacRule -match "optional: true") -Message "Infrastructure as Code rule pack should be marked optional."
    Assert-True -Condition ($iacRule -match "Terraform") -Message "Infrastructure as Code rule pack should require IaC evidence."
    Assert-True -Condition ($iacRule -match "unconfirmed") -Message "Infrastructure as Code rule pack should prefer unconfirmed over guesses."
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
    Assert-True -Condition ($roadmap -match "Optional Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code rule packs") -Message "Roadmap should describe current optional packs."
    Assert-True -Condition ($languageEvidence -match "Language Rule Pack Validation Evidence") -Message "Evidence should have expected title."
    Assert-True -Condition ($languageEvidence -match "python-api") -Message "Evidence should include Python generated sample."
    Assert-True -Condition ($languageEvidence -match "typescript-frontend") -Message "Evidence should include TypeScript generated sample."
    Assert-True -Condition ($languageEvidence -match "java-spring-api") -Message "Evidence should include Java generated sample."
    Assert-True -Condition ($languageEvidence -match "go-service") -Message "Evidence should include Go generated sample."
    Assert-True -Condition ($languageEvidence -match "rust-cli") -Message "Evidence should include Rust generated sample."
    Assert-True -Condition ($languageEvidence -match "sql-migrations") -Message "Evidence should include SQL generated sample."
    Assert-True -Condition ($languageEvidence -match "iac-terraform-kubernetes") -Message "Evidence should include Infrastructure as Code generated sample."
    Assert-True -Condition ($languageEvidence -match "pyproject\.toml") -Message "Evidence should include Python project metadata signal."
    Assert-True -Condition ($languageEvidence -match "package\.json") -Message "Evidence should include TypeScript project metadata signal."
    Assert-True -Condition ($languageEvidence -match "pom\.xml") -Message "Evidence should include Java project metadata signal."
    Assert-True -Condition ($languageEvidence -match "go\.mod") -Message "Evidence should include Go project metadata signal."
    Assert-True -Condition ($languageEvidence -match "Cargo\.toml") -Message "Evidence should include Rust project metadata signal."
    Assert-True -Condition ($languageEvidence -match "schema/\*\.sql") -Message "Evidence should include SQL project metadata signal."
    Assert-True -Condition ($languageEvidence -match "terraform/\*\.tf") -Message "Evidence should include IaC project metadata signal."
    Assert-True -Condition ($languageEvidence -match "does not prove editor/model behavior") -Message "Evidence should avoid overstating editor/model validation."
    Assert-True -Condition ($workflowEvidence -match "Multi-Language Workflow Validation Evidence") -Message "Workflow evidence should have expected title."
    Assert-True -Condition ($workflowEvidence -match "Local Ollama API preflight \| Passed") -Message "Workflow evidence should record successful local Ollama preflight after rerun."
    Assert-True -Condition ($workflowEvidence -match "Repository discovery \| Passed verification") -Message "Workflow evidence should record verified repository discovery."
    Assert-True -Condition ($workflowEvidence -match "FILENAME_NOT_IN_CONTEXT") -Message "Workflow evidence should record filename-drift guardrail failures."
    Assert-True -Condition ($config -notmatch "rule-packs") -Message "Default Continue config should not load optional language rule packs."
}

Invoke-PackTest "project classifier selects sanitized rule packs across generated ecosystems" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "project-profile-test-$([guid]::NewGuid())"
    $classifier = Join-Path $repoRoot "scripts/get-project-profile.ps1"
    $catalogPath = Join-Path $repoRoot "config/project-profile-rules.json"
    $expected = [ordered]@{
        "python-api" = "python"
        "typescript-frontend" = "typescript"
        "node-service" = "typescript"
        "java-spring-api" = "java"
        "go-service" = "go"
        "rust-cli" = "rust"
        "sql-migrations" = "sql"
        "iac-terraform-kubernetes" = "infrastructure-as-code"
    }

    try {
        Assert-True -Condition (Test-Path -LiteralPath $catalogPath) -Message "Project profile signal catalog should exist."
        $catalog = Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json
        Assert-Equal -Actual $catalog.schemaVersion -Expected 1 -Message "Project profile catalog should use schema version 1."

        $generateResult = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/generate-sample-repositories.ps1") `
            -Arguments @("-OutputRoot", $tempRoot)
        Assert-Equal -Actual $generateResult.ExitCode -Expected 0 -Message "Sample repositories should be generated for classification tests."

        foreach ($sampleName in $expected.Keys) {
            $samplePath = Join-Path $tempRoot $sampleName
            $profileJson = (& $classifier -TargetRepo $samplePath -AsJson | Out-String).Trim()
            $profile = $profileJson | ConvertFrom-Json
            Assert-Equal -Actual $profile.SchemaVersion -Expected 1 -Message "$sampleName should emit project profile schema version 1."
            Assert-Equal -Actual $profile.ActivationMinimumConfidence -Expected "medium" -Message "$sampleName should retain the catalog activation threshold."
            Assert-True -Condition ($expected[$sampleName] -in @($profile.SelectedRulePackIds)) -Message "$sampleName should select $($expected[$sampleName])."
            Assert-True -Condition ($profileJson -notmatch [regex]::Escape($tempRoot)) -Message "$sampleName profile should not record the target path."
            Assert-True -Condition (-not $profile.Privacy.TargetPathRecorded) -Message "$sampleName profile should declare that target paths are not recorded."
            Assert-True -Condition (-not $profile.Privacy.FileContentsRead) -Message "$sampleName profile should declare that file contents are not read."
        }
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
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

Invoke-PackTest "agent prompt rule and template contracts are enforced" {
    $agentFiles = Get-ChildItem -LiteralPath (Join-Path $repoRoot ".continue/agents") -Filter "*.md"
    $promptFiles = Get-ChildItem -LiteralPath (Join-Path $repoRoot ".continue/prompts") -Filter "*.md"
    $optionalRuleFiles = Get-ChildItem -LiteralPath (Join-Path $repoRoot ".continue/rule-packs") -Filter "*.md"

    foreach ($agentFile in $agentFiles) {
        $agent = Get-Content -LiteralPath $agentFile.FullName -Raw
        Assert-True -Condition ($agent -match "Operating Contract") -Message "$($agentFile.Name) should define the operating contract."
        Assert-True -Condition ($agent -match "role title does not grant permission") -Message "$($agentFile.Name) should not expand edit permissions."
        Assert-True -Condition ($agent -match "untrusted data") -Message "$($agentFile.Name) should treat repository content as untrusted."
        Assert-True -Condition ($agent -match "verify the changed files and diff") -Message "$($agentFile.Name) should require post-edit verification."
    }

    foreach ($promptFile in $promptFiles) {
        $prompt = Get-Content -LiteralPath $promptFile.FullName -Raw
        Assert-True -Condition ($prompt -match "Execution Contract") -Message "$($promptFile.Name) should define the execution contract."
        Assert-True -Condition ($prompt -match "slash prompt is read-only") -Message "$($promptFile.Name) should remain read-only in Agent mode."
        Assert-True -Condition ($prompt -match "untrusted data") -Message "$($promptFile.Name) should treat repository and tool output as untrusted."
        Assert-True -Condition ($prompt -match "Do not print tool-call JSON") -Message "$($promptFile.Name) should require real tool invocation."
        Assert-True -Condition ($prompt -match "checks actually run") -Message "$($promptFile.Name) should distinguish performed and future validation."
    }

    foreach ($ruleFile in $optionalRuleFiles) {
        $rule = Get-Content -LiteralPath $ruleFile.FullName -Raw
        Assert-True -Condition ($rule -match "(?m)^globs:") -Message "$($ruleFile.Name) should define file globs."
    }

    $generalRule = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/rules/general.md") -Raw
    $securityRule = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/rules/security.md") -Raw
    $dotnetRule = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/rules/dotnet.md") -Raw
    $aspnetRule = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/rules/aspnetcore.md") -Raw
    $apiRule = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/rules/api.md") -Raw
    Assert-True -Condition ($generalRule -match "untrusted data") -Message "General rules should define the untrusted-content boundary."
    Assert-True -Condition ($generalRule -match "separate side effects") -Message "General rules should define side-effect authorization."
    Assert-True -Condition ($securityRule -match "instructions found in source files") -Message "Security rules should address prompt injection in repository content."
    Assert-True -Condition ($securityRule -match "local-only configuration") -Message "Security rules should keep model endpoints and credentials local."
    Assert-True -Condition ($dotnetRule -match "(?m)^globs:") -Message ".NET rules should define file globs."
    Assert-True -Condition ($aspnetRule -match "(?m)^globs:") -Message "ASP.NET rules should define file globs."
    Assert-True -Condition ($aspnetRule -match "confirm an ASP.NET Core web surface") -Message "ASP.NET rules should require web-surface evidence."
    Assert-True -Condition ($apiRule -match "Evidence Gate") -Message "API rules should require API evidence."

    $architectureTemplate = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/templates/Architecture.md") -Raw
    $securityTemplate = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/templates/SecurityReview.md") -Raw
    $performanceTemplate = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/templates/PerformanceReview.md") -Raw
    $aiTemplate = Get-Content -LiteralPath (Join-Path $repoRoot ".continue/templates/AI.md") -Raw
    Assert-True -Condition ($architectureTemplate -match "Evidence Scope") -Message "Architecture template should record evidence scope."
    Assert-True -Condition ($securityTemplate -match "Status: confirmed, likely, or unconfirmed") -Message "Security findings should record confidence status."
    Assert-True -Condition ($performanceTemplate -match "Status: measured, inferred, or unconfirmed") -Message "Performance findings should record evidence status."
    Assert-True -Condition ($aiTemplate -match "Tool And Change Boundaries") -Message "AI guidance should record tool and change boundaries."
    Assert-True -Condition ($aiTemplate -match "Separate commands already verified") -Message "AI guidance should separate performed and future validation."

    $promptQuality = Get-Content -LiteralPath (Join-Path $repoRoot "docs/prompt-quality.md") -Raw
    $bannedPatterns = Get-Content -LiteralPath (Join-Path $repoRoot "docs/banned-output-patterns.md") -Raw
    $languageRules = Get-Content -LiteralPath (Join-Path $repoRoot "docs/language-rule-packs.md") -Raw
    $readme = Get-Content -LiteralPath (Join-Path $repoRoot "README.md") -Raw
    Assert-True -Condition ($promptQuality -match "Execution And Evidence Contract") -Message "Prompt quality docs should define the execution contract."
    Assert-True -Condition ($bannedPatterns -match "pseudo function calls") -Message "Banned patterns should reject printed tool syntax."
    Assert-True -Condition ($languageRules -match "evidence-gated \.NET, ASP.NET Core, and API rules") -Message "Language rule docs should describe default rule loading accurately."
    Assert-True -Condition ($readme -match 'Version `0\.2\.0`') -Message "README should report the current pack version."
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
            "sql-migrations/schema/001_create_items.sql",
            "python-layered-api/app/service.py",
            "python-layered-api/tests/test_service.py",
            "typescript-service-medium/src/service.ts",
            "typescript-service-medium/tests/service.test.ts",
            "multi-language-platform/services/catalog/pom.xml",
            "multi-language-platform/workers/events/go.mod",
            "multi-language-platform/tools/manifest/Cargo.toml",
            "multi-language-platform/database/schema/001_catalog.sql",
            "multi-language-platform/infrastructure/terraform/main.tf",
            "multi-language-platform/infrastructure/k8s/catalog.yaml"
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
        Assert-True -Condition ($listResult.Output -match "python-layered-api") -Message "List output should include python-layered-api."
        Assert-True -Condition ($listResult.Output -match "typescript-service-medium") -Message "List output should include typescript-service-medium."
        Assert-True -Condition ($listResult.Output -match "multi-language-platform") -Message "List output should include multi-language-platform."

        $rerunResult = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-OutputRoot", $tempRoot)
        Assert-True -Condition ($rerunResult.ExitCode -ne 0) -Message "Sample repository factory should refuse to overwrite without -Force."
        Assert-True -Condition ($rerunResult.Output -match "overwrite generated samples") -Message "Overwrite refusal should explain how to overwrite generated samples."

        $runtimeContextScript = Join-Path $repoRoot "scripts/generate-runtime-context.ps1"
        $contextTargets = @(
            @{ Name = "typescript-frontend"; Expected = @("SAMPLE-METADATA.md", "tsconfig.json", "src/App.tsx") },
            @{ Name = "node-service"; Expected = @("package.json", "Dockerfile", "src/server.js") },
            @{ Name = "iac-terraform-kubernetes"; Expected = @("terraform/main.tf", "k8s/deployment.yaml", ".github/workflows/validate.yml") },
            @{ Name = "sql-migrations"; Expected = @("schema/001_create_items.sql", "migrations/002_add_item_status.sql", "seeds/items.sql") }
            @{ Name = "python-layered-api"; Expected = @("pyproject.toml", "app/service.py", "tests/test_service.py", "SCENARIO.md") }
            @{ Name = "typescript-service-medium"; Expected = @("tsconfig.json", "src/service.ts", "tests/service.test.ts", "SCENARIO.md") }
            @{ Name = "multi-language-platform"; Expected = @("services/catalog/pom.xml", "workers/events/go.mod", "tools/manifest/Cargo.toml", "database/schema/001_catalog.sql", "infrastructure/terraform/main.tf", "SCENARIO.md") }
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

Invoke-PackTest "medium language workflow matrix is complete and evidence-gated" {
    $matrixPath = Join-Path $repoRoot "config/language-workflow-validation-matrix.json"
    $docPath = Join-Path $repoRoot "docs/language-workflow-validation-matrix.md"
    $runnerPath = Join-Path $repoRoot "scripts/run-language-workflow-matrix.ps1"
    $sharedRunnerPath = Join-Path $repoRoot "scripts/run-language-workflow-matrix.shared.sh"
    $linuxRunnerPath = Join-Path $repoRoot "scripts/run-language-workflow-matrix.linux.sh"
    $macosRunnerPath = Join-Path $repoRoot "scripts/run-language-workflow-matrix.macos.sh"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "language-matrix-test-$([guid]::NewGuid())"

    try {
        Assert-True -Condition (Test-Path -LiteralPath $matrixPath) -Message "Language workflow matrix should exist."
        Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Language workflow matrix docs should exist."
        Assert-True -Condition (Test-Path -LiteralPath $runnerPath) -Message "Language workflow matrix runner should exist."
        Assert-True -Condition (Test-Path -LiteralPath $sharedRunnerPath) -Message "Shared native language workflow matrix runner should exist."
        Assert-True -Condition (Test-Path -LiteralPath $linuxRunnerPath) -Message "Linux language workflow matrix wrapper should exist."
        Assert-True -Condition (Test-Path -LiteralPath $macosRunnerPath) -Message "macOS language workflow matrix wrapper should exist."

        $matrix = Get-Content -LiteralPath $matrixPath -Raw | ConvertFrom-Json
        $doc = Get-Content -LiteralPath $docPath -Raw
        $runner = Get-Content -LiteralPath $runnerPath -Raw
        $sharedRunner = Get-Content -LiteralPath $sharedRunnerPath -Raw
        $linuxRunner = Get-Content -LiteralPath $linuxRunnerPath -Raw
        $macosRunner = Get-Content -LiteralPath $macosRunnerPath -Raw
        $expectedRulePacks = @("python", "typescript", "java", "go", "rust", "sql", "infrastructure-as-code")
        $expectedOperations = @("repository-discovery", "implementation-plan", "code-review", "scoped-write")

        Assert-Equal -Actual $matrix.schemaVersion -Expected 1 -Message "Language workflow matrix schema should remain stable."
        Assert-Equal -Actual @($matrix.entries).Count -Expected 7 -Message "Language workflow matrix should cover all optional rule packs."
        foreach ($operation in $expectedOperations) {
            Assert-True -Condition ($operation -in @($matrix.requiredOperations)) -Message "Matrix should require operation $operation."
        }

        $generateResult = Invoke-CommandCapture -FilePath (Join-Path $repoRoot "scripts/generate-sample-repositories.ps1") -Arguments @("-OutputRoot", $tempRoot)
        Assert-Equal -Actual $generateResult.ExitCode -Expected 0 -Message "Medium samples should generate for matrix validation."

        $validatedCells = 0
        $failedCells = 0
        foreach ($entry in $matrix.entries) {
            Assert-True -Condition ($entry.rulePackId -in $expectedRulePacks) -Message "Unexpected rule pack in matrix: $($entry.rulePackId)"
            Assert-Equal -Actual $entry.fixtureComplexity -Expected "medium" -Message "$($entry.rulePackId) should use a medium fixture."
            Assert-Equal -Actual $entry.fixtureStatus -Expected "static-validated" -Message "$($entry.rulePackId) fixture should be statically validated."
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot $entry.rulePackPath)) -Message "Rule pack path should exist: $($entry.rulePackPath)"

            $samplePath = Join-Path $tempRoot $entry.sample
            Assert-True -Condition (Test-Path -LiteralPath $samplePath) -Message "Matrix sample should be generated: $($entry.sample)"
            foreach ($evidenceFile in $entry.evidenceFiles) {
                Assert-True -Condition (Test-Path -LiteralPath (Join-Path $samplePath $evidenceFile)) -Message "$($entry.sample) should include $evidenceFile."
            }
            foreach ($operation in $expectedOperations) {
                $status = $entry.operations.$operation
                Assert-True -Condition ($status -in @("validated", "failed-model-validation")) -Message "$($entry.rulePackId) $operation should have an evidence-backed status."
                if ($status -eq "validated") { $validatedCells++ } else { $failedCells++ }

                if ($operation -eq "scoped-write") {
                    $writeEvidence = $entry.operationEvidence.'scoped-write'
                    Assert-True -Condition (Test-Path -LiteralPath (Join-Path $samplePath $writeEvidence.targetFile)) -Message "$($entry.rulePackId) scoped-write target should exist."
                    Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($writeEvidence.marker)) -Message "$($entry.rulePackId) scoped-write marker should be explicit."
                }
                else {
                    foreach ($operationFile in @($entry.operationEvidence.$operation)) {
                        Assert-True -Condition (Test-Path -LiteralPath (Join-Path $samplePath $operationFile)) -Message "$($entry.rulePackId) $operation evidence should exist: $operationFile"
                    }
                }
            }

            Assert-Equal -Actual @($entry.operationModels.PSObject.Properties.Name).Count -Expected 4 -Message "$($entry.rulePackId) should record an evidence-backed model for every operation."

            $profileJson = (& (Join-Path $repoRoot "scripts/get-project-profile.ps1") -TargetRepo $samplePath -AsJson | Out-String).Trim()
            $profile = $profileJson | ConvertFrom-Json
            Assert-True -Condition ($entry.rulePackId -in @($profile.SelectedRulePackIds)) -Message "$($entry.sample) should activate $($entry.rulePackId)."
            Assert-True -Condition ($profileJson -notmatch [regex]::Escape($tempRoot)) -Message "Matrix classification should not expose local paths."
        }

        Assert-Equal -Actual $validatedCells -Expected 28 -Message "Composite matrix evidence should validate every required cell."
        Assert-Equal -Actual $failedCells -Expected 0 -Message "Composite matrix evidence should not retain failed cells."
        Assert-Equal -Actual $matrix.latestValidation.surfaceVersion -Expected "1.5.47" -Message "Latest matrix evidence should record the Continue CLI version."
        Assert-True -Condition ("devstral-small-2:24b" -in @($matrix.latestValidation.models)) -Message "Latest matrix evidence should record the default model."
        Assert-True -Condition ("qwen3.5:35b" -in @($matrix.latestValidation.models)) -Message "Latest matrix evidence should record the TypeScript write model."
        $nativeEvidence = @($matrix.nativeOperatingSystemEvidence)
        Assert-Equal -Actual $nativeEvidence.Count -Expected 3 -Message "Matrix should retain the completed Linux and macOS evidence records."
        $linuxEvidence = @($nativeEvidence | Where-Object { $_.operatingSystem -like "Linux *" })
        $macosEvidence = @($nativeEvidence | Where-Object { $_.operatingSystem -eq "macOS (Apple Silicon)" })
        Assert-Equal -Actual $linuxEvidence.Count -Expected 2 -Message "Matrix should retain the completed Linux evidence records."
        Assert-Equal -Actual $macosEvidence.Count -Expected 1 -Message "Matrix should retain the completed macOS evidence record."
        Assert-Equal -Actual $macosEvidence[0].model -Expected "qwen3.5:9b" -Message "macOS evidence should retain the validated model."
        Assert-Equal -Actual $macosEvidence[0].validatedCells -Expected 4 -Message "macOS evidence should retain the Python validation count."
        Assert-Equal -Actual $macosEvidence[0].failedCells -Expected 0 -Message "macOS evidence should not retain failed cells."
        foreach ($item in $nativeEvidence) {
            Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($item.evidenceDocument)) -Message "Native evidence should link its sanitized evidence document."
        }

        Assert-True -Condition ($doc -match "Static fixture success alone never promotes") -Message "Matrix docs should prevent static evidence from promoting model support."
        Assert-True -Condition ($doc -match "external Git diff") -Message "Matrix docs should require external diff verification for scoped writes."
        Assert-True -Condition ($doc -match "28 of 28") -Message "Matrix docs should summarize the latest exact result."
        Assert-True -Condition ($doc -match "Native Linux and macOS runners are available") -Message "Matrix docs should describe native runner availability."
        Assert-True -Condition ($doc -match "Native Linux Evidence") -Message "Matrix docs should record the completed Linux evidence."
        Assert-True -Condition ($runner -match "--readonly") -Message "Matrix runner should separate read-only mode."
        Assert-True -Condition ($runner -match "--auto") -Message "Matrix runner should use explicit approved-write mode."
        Assert-True -Condition ($sharedRunner -match "--readonly") -Message "Shared native matrix runner should separate read-only mode."
        Assert-True -Condition ($sharedRunner -match "--auto") -Message "Shared native matrix runner should use explicit approved-write mode."
        Assert-True -Condition ($sharedRunner -match "unload_models") -Message "Shared native matrix runner should support unloading models."
        Assert-True -Condition ($sharedRunner -match "trap handle_interruption HUP INT TERM") -Message "Shared native matrix runner should release models when interrupted."
        Assert-True -Condition ($sharedRunner -match "--allow-loaded-models") -Message "Shared native matrix runner should require an explicit override for an already loaded Ollama model."
        Assert-True -Condition ($runner -match "AllowLoadedModels") -Message "Windows matrix runner should require an explicit override for an already loaded Ollama model."
        Assert-True -Condition ($linuxRunner -match "run-language-workflow-matrix.shared.sh") -Message "Linux wrapper should delegate to the shared runner."
        Assert-True -Condition ($macosRunner -match "run-language-workflow-matrix.shared.sh") -Message "macOS wrapper should delegate to the shared runner."
        Assert-True -Condition ($runner -match "git -C .* diff --name-only") -Message "Matrix runner should externally verify changed files."
        Assert-True -Condition ($runner -match "ConvertTo-SanitizedOutput") -Message "Matrix runner should sanitize committed evidence."
        Assert-True -Condition ($runner -match "UnloadAfterRun") -Message "Matrix runner should support unloading tested models."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "review prompts require filename fidelity gates" {
    $promptNames = @(
        "architecture-review.md",
        "bug-investigation.md",
        "code-review.md",
        "documentation.md",
        "implementation-plan.md",
        "performance-review.md",
        "product-manager.md",
        "refactoring-planner.md",
        "release-readiness.md",
        "repository-discovery.md",
        "security-review.md",
        "ai-framework-self-review.md"
    )

    foreach ($promptName in $promptNames) {
        $promptPath = Join-Path $repoRoot ".continue/prompts/$promptName"
        $prompt = Get-Content -LiteralPath $promptPath -Raw
        Assert-True -Condition ($prompt -match "Filename Fidelity Gate") -Message "$promptName should include the filename fidelity gate."
        Assert-True -Condition ($prompt -match "only source of truth") -Message "$promptName should treat inspected context as the source of truth."
        Assert-True -Condition ($prompt -match "engineering pack's own files") -Message "$promptName should not assume pack-local files exist in the reviewed repository."
        Assert-True -Condition ($prompt -match "recommended new file") -Message "$promptName should label missing files as recommended new files."
        Assert-True -Condition ($prompt -match "unconfirmed filename") -Message "$promptName should label uncertain filenames."
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
        Assert-True -Condition ($result.Output -match "Detected project ecosystem") -Message "Dry-run output should report project classification."
        Assert-True -Condition ($result.Output -match "Would write \.continue/project-profile\.json") -Message "Dry-run output should report project profile activation."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $tempRepo ".continue"))) -Message "Dry run should not create .continue."
    }
    finally {
        Remove-Item -LiteralPath $tempRepo -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "install script activates only evidence-backed project rule packs" {
    $tempRepo = Join-Path ([System.IO.Path]::GetTempPath()) "continue-project-profile-install-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null
        "[project]" | Set-Content -LiteralPath (Join-Path $tempRepo "pyproject.toml")

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-ModelLanes")
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Project-aware install should succeed."

        $profilePath = Join-Path $tempRepo ".continue/project-profile.json"
        $activePython = Join-Path $tempRepo ".continue/rules/active-language-python.md"
        $activeJava = Join-Path $tempRepo ".continue/rules/active-language-java.md"
        Assert-True -Condition (Test-Path -LiteralPath $profilePath) -Message "Installer should write the sanitized project profile."
        Assert-True -Condition (Test-Path -LiteralPath $activePython) -Message "Installer should activate the Python rule pack."
        Assert-True -Condition (-not (Test-Path -LiteralPath $activeJava)) -Message "Installer should not activate unmatched Java guidance."
        Assert-True -Condition (Test-Path -LiteralPath (Join-Path $tempRepo ".continue/config.local.yaml")) -Message "Model config generation should preserve project rule activation."

        $profileJson = Get-Content -LiteralPath $profilePath -Raw
        $profile = $profileJson | ConvertFrom-Json
        Assert-True -Condition ("python" -in @($profile.SelectedRulePackIds)) -Message "Installed project profile should select Python."
        Assert-True -Condition ($profileJson -notmatch [regex]::Escape($tempRepo)) -Message "Installed project profile should not record the target path."
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


Invoke-PackTest "install script supports centralized shared assets and global config" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "continue-shared-assets-test-$([guid]::NewGuid())"
    $tempRepo = Join-Path $tempRoot "target-repo"
    $sharedAssetsPath = Join-Path $tempRoot "shared-assets"
    $globalConfigPath = Join-Path $tempRoot "global-config.yaml"

    try {
        New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

        $dryRun = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-SharedAssets", "-SharedAssetsPath", $sharedAssetsPath, "-GlobalConfigPath", $globalConfigPath, "-DryRun")

        Assert-Equal -Actual $dryRun.ExitCode -Expected 0 -Message "Shared-assets dry run should succeed."
        Assert-True -Condition ($dryRun.Output -match "Shared-assets mode is enabled") -Message "Dry run should identify shared-assets mode."
        Assert-True -Condition ($dryRun.Output -match "Would write global Continue config") -Message "Dry run should explain global config generation."
        Assert-True -Condition (-not (Test-Path -LiteralPath $sharedAssetsPath)) -Message "Dry run should not create shared assets."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $tempRepo ".continue"))) -Message "Shared-assets dry run should not create project .continue."

        $result = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-SharedAssets", "-SharedAssetsPath", $sharedAssetsPath, "-GlobalConfigPath", $globalConfigPath, "-GlobalConfigApiBase", "http://127.0.0.1:11434")

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Shared-assets install should succeed."
        Assert-True -Condition (Test-Path -LiteralPath (Join-Path $sharedAssetsPath "config.yaml")) -Message "Shared assets should include config.yaml."
        Assert-True -Condition (Test-Path -LiteralPath (Join-Path $sharedAssetsPath "prompts/repository-discovery.md")) -Message "Shared assets should include prompts."
        Assert-True -Condition (Test-Path -LiteralPath (Join-Path $sharedAssetsPath "templates/LegacyDotNetDependencyMigration.md")) -Message "Shared assets should include templates."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $sharedAssetsPath "config.local.yaml"))) -Message "Shared assets should not include local config overrides."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $tempRepo ".continue"))) -Message "Shared-assets install should not create project .continue."
        Assert-True -Condition (Test-Path -LiteralPath $globalConfigPath) -Message "Shared-assets install should write global config."

        $globalConfig = Get-Content -LiteralPath $globalConfigPath -Raw
        $sharedUri = ($sharedAssetsPath -replace '\\', '/')
        Assert-True -Condition ($globalConfig -match [regex]::Escape("file://$sharedUri/prompts/repository-discovery.md")) -Message "Global config should point prompts at shared assets."
        Assert-True -Condition ($globalConfig -match "apiBase: http://127\.0\.0\.1:11434") -Message "Global config should include requested local Ollama API base."
        Assert-True -Condition ($globalConfig -notmatch "file://\./") -Message "Global config should not contain project-relative file references."
        Assert-True -Condition ($globalConfig -notmatch "(?m)^rules:\s*$") -Message "Global config should omit rules by default."
        Assert-True -Condition ($globalConfig -notmatch [regex]::Escape($tempRepo)) -Message "Global config should not point at the target repository in shared-assets mode."

        $invalid = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") `
            -Arguments @("-TargetRepo", $tempRepo, "-SharedAssets", "-SharedAssetsPath", (Join-Path $tempRoot "invalid-assets"), "-ModelLanes")

        Assert-True -Condition ($invalid.ExitCode -ne 0) -Message "Shared-assets mode should reject project-local model lane generation."
        Assert-True -Condition ($invalid.Output -match "Shared-assets mode currently supports reusable assets") -Message "Rejected shared-assets combination should explain the limitation."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "shared asset installer options are documented in scripts" {
    $psScript = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/install-continue-pack.ps1") -Raw
    $bashScript = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/install-continue-pack.shared.sh") -Raw

    Assert-True -Condition ($psScript -match "SharedAssets") -Message "PowerShell installer should expose SharedAssets."
    Assert-True -Condition ($psScript -match "shared-assets-path") -Message "PowerShell installer should expose shared-assets-path alias."
    Assert-True -Condition ($bashScript -match "--shared-assets") -Message "Bash installer should expose shared-assets."
    Assert-True -Condition ($bashScript -match "--shared-assets-path") -Message "Bash installer should expose shared-assets-path."
    Assert-True -Condition ($bashScript -match "LocalEngineeringAgentPack/assets") -Message "Bash installer should define a macOS shared asset default."
    Assert-True -Condition ($bashScript -match "local-engineering-agent-pack/assets") -Message "Bash installer should define a Linux shared asset default."
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
            Name = "test-cline-cli-models.linux.sh"
            Target = "test-cline-cli-models.shared.sh"
        },
        @{
            Name = "test-cline-cli-models.macos.sh"
            Target = "test-cline-cli-models.shared.sh"
        },
        @{
            Name = "test-aider-cli-models.linux.sh"
            Target = "test-aider-cli-models.shared.sh"
        },
        @{
            Name = "test-aider-cli-models.macos.sh"
            Target = "test-aider-cli-models.shared.sh"
        },
        @{
            Name = "generate-sample-repositories.linux.sh"
            Target = "generate-sample-repositories.shared.sh"
        },
        @{
            Name = "generate-sample-repositories.macos.sh"
            Target = "generate-sample-repositories.shared.sh"
        },
        @{
            Name = "invoke-workflow.linux.sh"
            Target = "invoke-workflow.shared.sh"
        },
        @{
            Name = "invoke-workflow.macos.sh"
            Target = "invoke-workflow.shared.sh"
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
    $sharedValidatorPath = Join-Path $repoRoot "scripts/validate-pack.shared.sh"
    $sharedValidator = Get-Content -LiteralPath $sharedValidatorPath -Raw

    Assert-True -Condition ($sharedValidator -match "matches_text") -Message "Shared validator should use a helper for content regex checks."
    Assert-True -Condition ($sharedValidator -notmatch 'printf ''%s\\n'' "\$CONFIG_CONTENT" \| grep -E') -Message "Shared validator should avoid CONFIG_CONTENT printf/grep pipelines under pipefail."
    Assert-True -Condition ($sharedValidator -notmatch 'printf ''%s\\n'' "\$content" \| grep -Ei') -Message "Shared validator should avoid scanned-file printf/grep pipelines under pipefail."

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
        $recommendedOutputPath = Join-Path $tempRoot "recommended.md"

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

        "recommended new file: CHANGELOG.md should document release history." |
            Set-Content -LiteralPath $recommendedOutputPath

        $good = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/verify-runtime-output.ps1") `
            -Arguments @("-OutputPath", $goodOutputPath, "-ContextPath", $contextPath, "-WorkflowName", "legacy-dotnet-dependency-migration")

        Assert-Equal -Actual $good.ExitCode -Expected 0 -Message "Verifier should pass output that uses context filenames and verification qualifiers."
        Assert-True -Condition ($good.Output -match "PASS runtime output verification") -Message "Verifier pass message should be present."

        $recommended = Invoke-CommandCapture `
            -FilePath (Join-Path $repoRoot "scripts/verify-runtime-output.ps1") `
            -Arguments @("-OutputPath", $recommendedOutputPath, "-ContextPath", $contextPath, "-WorkflowName", "documentation")

        Assert-Equal -Actual $recommended.ExitCode -Expected 0 -Message "Verifier should allow recommended-new-file references when clearly labeled."

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
    Assert-True -Condition ($runner -match "EMPTY_MODEL_OUTPUT") -Message "PowerShell runtime runner should record empty model output instead of crashing."
    Assert-True -Condition ($runner -match "Use only filenames that appear in the supplied runtime repository context") -Message "PowerShell runtime runner should inject filename fidelity guardrails."
    Assert-True -Condition ($runner -match "recommended new file") -Message "PowerShell runtime runner should instruct models how to label absent recommended files."
    Assert-True -Condition ($runner -match "New-FilenameFidelityFallback") -Message "PowerShell runtime runner should create filename-fidelity fallback artifacts."
    Assert-True -Condition ($runner -match "filename-fidelity-fallback\.md") -Message "PowerShell runtime runner should write deterministic fallback files for filename verification failures."
    Assert-True -Condition ($runner -match "FILENAME_NOT_IN_CONTEXT") -Message "PowerShell runtime runner fallback should be tied to filename verifier failures."
    Assert-True -Condition ($sharedRunner -match "verify-runtime-output\.shared\.sh") -Message "Bash runtime runner should call verifier."
    Assert-True -Condition ($sharedRunner -match "Local Ollama API preflight failed") -Message "Bash runtime runner should fail fast when local Ollama is unreachable."
    Assert-True -Condition ($sharedRunner -match "/api/tags") -Message "Bash runtime runner should preflight Ollama tags endpoint."
    Assert-True -Condition ($sharedRunner -match "EMPTY_MODEL_OUTPUT") -Message "Bash runtime runner should record empty model output instead of crashing."
    Assert-True -Condition ($sharedRunner -match "Use only filenames that appear in the supplied runtime repository context") -Message "Bash runtime runner should inject filename fidelity guardrails."
    Assert-True -Condition ($sharedRunner -match "recommended new file") -Message "Bash runtime runner should instruct models how to label absent recommended files."
    Assert-True -Condition ($sharedRunner -match "write_filename_fidelity_fallback") -Message "Bash runtime runner should create filename-fidelity fallback artifacts."
    Assert-True -Condition ($sharedRunner -match "filename-fidelity-fallback\.md") -Message "Bash runtime runner should write deterministic fallback files for filename verification failures."
    Assert-True -Condition ($sharedRunner -match "FILENAME_NOT_IN_CONTEXT") -Message "Bash runtime runner fallback should be tied to filename verifier failures."
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
        Assert-True -Condition ($report.ModelLanes.Contract -eq "surface-neutral") -Message "Recommendation should emit a surface-neutral model lane contract."
        Assert-True -Condition ($report.ModelLanes.WriteSafe.ToolUse -eq "approved-write") -Message "WRITE SAFE lane should describe approved-write tool use."
        Assert-True -Condition ($report.ModelLanes.WriteSafe.RecommendedRoles -contains "edit") -Message "Surface-neutral WRITE SAFE lane should include edit role guidance."
        Assert-True -Condition ($report.ContinueProfiles.WriteSafe.Roles -contains "edit") -Message "WRITE SAFE should include edit role guidance."
        Assert-True -Condition ($report.ContinueProfiles.PlanOnly.Roles -notcontains "edit") -Message "PLAN ONLY should not include edit role guidance."
        Assert-True -Condition ($report.ModelProfilePath -eq "redacted") -Message "Recommendation output should redact model profile path."
        Assert-True -Condition ($report.Privacy.RepositoryContentSent -eq $false) -Message "Recommendation output should state repository content was not sent."
        Assert-True -Condition ($report.Privacy.HardwareProfileSentOnline -eq $false) -Message "Recommendation output should state hardware profile was not sent online."
        Assert-True -Condition (($report | ConvertTo-Json -Depth 20) -notmatch "Users|OneDrive|192\.168\.|localhost") -Message "Recommendation output should not leak local paths or endpoints."
        Assert-True -Condition ($script -match "VramSelectionMode") -Message "PowerShell recommendation script should support VRAM selection mode."
        Assert-True -Condition ($script -match "config/evidence-catalog.tsv") -Message "PowerShell recommendation script should use evidence catalog by default."
        Assert-True -Condition ($sharedScript -match "python3 is required") -Message "Bash recommendation script should clearly state its python3 requirement."
        Assert-True -Condition ($sharedScript -match '"ModelLanes"') -Message "Bash recommendation script should emit surface-neutral model lanes."
        Assert-True -Condition ($sharedScript -match "HardwareProfileSentOnline") -Message "Bash recommendation script should emit sanitized privacy fields."
        Assert-True -Condition ($doc -match "ModelLanes") -Message "Recommendation docs should explain surface-neutral model lanes."
        Assert-True -Condition ($doc -match "WRITE SAFE") -Message "Recommendation docs should explain WRITE SAFE lane."
        Assert-True -Condition ($doc -match "does not read repository source code") -Message "Recommendation docs should explain privacy boundaries."
        Assert-True -Condition ($readme -match "hardware-aware model/config recommendation") -Message "README should link the hardware-aware recommendation path."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "capability evidence v2 blocks cross-surface inheritance and aggregates conservatively" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "evidence-v2-recommendation-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
        $profilePath = Join-Path $tempRoot "model-profile.json"
        $catalogPath = Join-Path $tempRoot "evidence.tsv"
        $outputPath = Join-Path $tempRoot "recommendation.json"

        @"
{
  "Platform": "Windows",
  "CpuArchitecture": "x64",
  "SystemRamGb": 32,
  "Gpus": [{"Name":"fixture gpu","VramGb":16,"MemoryType":"dedicated"}],
  "OllamaModels": ["qwen3.5:9b", "fixture-tool:1b"]
}
"@ | Set-Content -LiteralPath $profilePath

        @"
schema_version	area	subject	surface	surface_version	provider	os	model	operation	validation_mode	status	evidence	notes
2	model-tool-use	passing write	Continue Agent	not-recorded	Ollama	Windows	qwen3.5:9b	scoped-write	editor-agent	approved-write-ready	examples/model-tool-use-validation.md	Passing record.
2	model-tool-use	conflicting write	Continue Agent	not-recorded	Ollama	Windows	qwen3.5:9b	scoped-write	editor-agent	partial-pass	examples/model-tool-use-validation.md	Conservative duplicate.
2	model-tool-use	other surface write	Cline	not-recorded	Ollama	Windows	qwen3.5:9b	scoped-write	editor-agent	approved-write-ready	examples/cline-readonly-validation.md	Must not be inherited.
2	model-tool-use	exact write only	Continue Agent	not-recorded	Ollama	Windows	fixture-tool:1b	scoped-write	editor-agent	approved-write-ready	examples/model-tool-use-validation.md	Must not imply plan readiness.
"@ | Set-Content -LiteralPath $catalogPath

        $result = Invoke-CommandCapture -FilePath (Join-Path $repoRoot "scripts/recommend-local-agent-config.ps1") -Arguments @("-ModelProfilePath", $profilePath, "-EvidenceCatalogPath", $catalogPath, "-OutputPath", $outputPath)

        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Recommendation should process v2 duplicate evidence."
        $report = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
        $candidate = @($report.Candidates | Where-Object { $_.Model -eq "qwen3.5:9b" })[0]
        Assert-Equal -Actual $report.EvidenceContractVersion -Expected 2 -Message "Recommendation should report evidence contract v2."
        Assert-Equal -Actual $report.EvidenceTarget.Surface -Expected "Continue Agent" -Message "Recommendation should report the exact target surface."
        Assert-Equal -Actual $candidate.OperationEvidence.ScopedWrite.Status -Expected "partial-pass" -Message "Duplicate evidence should aggregate to the most conservative status."
        Assert-Equal -Actual $candidate.OperationEvidence.ScopedWrite.RecordCount -Expected 2 -Message "Aggregation should retain duplicate record count."
        Assert-Equal -Actual $candidate.OperationEvidence.ScopedWrite.Evidence.Count -Expected 1 -Message "Aggregation should retain unique provenance paths."
        Assert-Equal -Actual $report.Recommendation.WriteSafeModel -Expected "fixture-tool:1b" -Message "Exact write evidence should remain eligible."
        Assert-True -Condition ($null -eq $report.Recommendation.PlanOnlyModel) -Message "Write evidence should not be inherited by the plan operation."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-PackTest "lane-specific scoring keeps write conservative and prefers fitting capacity for plan and review" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "lane-scoring-test-$([guid]::NewGuid())"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
        $profilePath = Join-Path $tempRoot "model-profile.json"
        $catalogPath = Join-Path $tempRoot "evidence.tsv"
        $outputPath = Join-Path $tempRoot "recommendation.json"

        @"
{
  "Platform": "Windows",
  "CpuArchitecture": "x64",
  "SystemRamGb": 128,
  "Gpus": [{"Name":"fixture gpu","VramGb":64,"MemoryType":"dedicated"}],
  "OllamaModels": ["qwen3.5:9b", "qwen3-coder:30b"]
}
"@ | Set-Content -LiteralPath $profilePath

        @"
schema_version	area	subject	surface	surface_version	provider	os	model	operation	validation_mode	status	evidence	notes
2	model-tool-use	small write	Continue Agent	not-recorded	Ollama	Windows	qwen3.5:9b	scoped-write	editor-agent	approved-write-ready	examples/model-tool-use-validation.md	Small validated writer.
2	model-tool-use	small plan	Continue Agent	not-recorded	Ollama	Windows	qwen3.5:9b	plan	editor-agent	plan-validated	examples/model-tool-use-validation.md	Small validated planner.
2	model-tool-use	small review	Continue Agent	not-recorded	Ollama	Windows	qwen3.5:9b	review	editor-agent	review-validated	examples/model-tool-use-validation.md	Small validated reviewer.
2	model-tool-use	large plan	Continue Agent	not-recorded	Ollama	Windows	qwen3-coder:30b	plan	editor-agent	plan-validated	examples/model-tool-use-validation.md	Large validated planner.
2	model-tool-use	large review	Continue Agent	not-recorded	Ollama	Windows	qwen3-coder:30b	review	editor-agent	review-validated	examples/model-tool-use-validation.md	Large validated reviewer.
"@ | Set-Content -LiteralPath $catalogPath

        $result = Invoke-CommandCapture -FilePath (Join-Path $repoRoot "scripts/recommend-local-agent-config.ps1") -Arguments @("-ModelProfilePath", $profilePath, "-EvidenceCatalogPath", $catalogPath, "-OutputPath", $outputPath, "-ContextTargetTokens", "32768", "-MemoryReserveGb", "6")
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Lane-specific recommendation should succeed."

        $report = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
        Assert-Equal -Actual $report.SelectionPolicy.Version -Expected 1 -Message "Recommendation should identify lane scoring policy version 1."
        Assert-Equal -Actual $report.FitPolicy.Version -Expected 1 -Message "Recommendation should identify fit policy version 1."
        Assert-Equal -Actual $report.FitPolicy.ContextTargetTokens -Expected 32768 -Message "Recommendation should preserve the requested context target."
        Assert-Equal -Actual $report.Recommendation.WriteSafeModel -Expected "qwen3.5:9b" -Message "WRITE SAFE should keep the exact approved writer with greater headroom."
        Assert-Equal -Actual $report.Recommendation.PlanOnlyModel -Expected "qwen3-coder:30b" -Message "PLAN ONLY should prefer the larger fitting model with exact plan evidence."
        Assert-Equal -Actual $report.Recommendation.DeepReviewModel -Expected "qwen3-coder:30b" -Message "DEEP REVIEW should prefer the larger fitting model with exact review evidence."

        $small = @($report.Candidates | Where-Object { $_.Model -eq "qwen3.5:9b" })[0]
        $large = @($report.Candidates | Where-Object { $_.Model -eq "qwen3-coder:30b" })[0]
        Assert-True -Condition $small.LaneScores.WriteSafe.Eligible -Message "Small model should expose eligible WRITE SAFE scoring."
        Assert-Equal -Actual $small.ModelFit.Source -Expected "model-fit-catalog" -Message "Known models should use explicit fit metadata."
        Assert-Equal -Actual $small.ModelFit.MemoryReserveGb -Expected 6 -Message "Explicit memory reserve should override the catalog reserve."
        Assert-Equal -Actual $small.RecommendedMinVramGb -Expected 16.5 -Message "Context and reserve should affect the fit estimate."
        Assert-True -Condition (-not $large.LaneScores.WriteSafe.Eligible) -Message "Large model should remain write-ineligible without exact write evidence."
        Assert-True -Condition ($large.LaneScores.PlanOnly.Score -gt $small.LaneScores.PlanOnly.Score) -Message "Larger fitting validated planner should receive the higher plan score."
        Assert-True -Condition ($large.LaneScores.DeepReview.Score -gt $small.LaneScores.DeepReview.Score) -Message "Larger fitting validated reviewer should receive the higher review score."
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
Invoke-PackTest "shared asset installation docs define centralized config strategy" {
    $docPath = Join-Path $repoRoot "docs/shared-asset-installation.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"
    $todoPath = Join-Path $repoRoot "TODO.md"
    $hardwareDocPath = Join-Path $repoRoot "docs/hardware-aware-recommendations.md"
    $strategyPath = Join-Path $repoRoot "docs/config-generation-strategy.md"
    $surfaceBundlePath = Join-Path $repoRoot "docs/surface-specific-config-bundles.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Shared asset installation doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $strategyPath) -Message "Config generation strategy doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw
    $hardwareDoc = Get-Content -LiteralPath $hardwareDocPath -Raw
    $strategy = Get-Content -LiteralPath $strategyPath -Raw
    $surfaceBundle = Get-Content -LiteralPath $surfaceBundlePath -Raw

    Assert-True -Condition ($doc -match "Project-Local Mode") -Message "Shared asset doc should preserve project-local mode."
    Assert-True -Condition ($doc -match "Shared-Assets Mode") -Message "Shared asset doc should define shared-assets mode."
    Assert-True -Condition ($doc -match "SharedAssetsPath") -Message "Shared asset doc should define explicit path option."
    Assert-True -Condition ($doc -match "file://\./") -Message "Shared asset doc should warn against project-relative global references."
    Assert-True -Condition ($doc -match "duplicate rule") -Message "Shared asset doc should cover duplicate-rule behavior."
    Assert-True -Condition ($doc -match "Rollback") -Message "Shared asset doc should include rollback guidance."
    Assert-True -Condition ($readme -match "docs/shared-asset-installation.md") -Message "README should link shared asset doc."
    Assert-True -Condition ($readme -match "docs/config-generation-strategy.md") -Message "README should link config generation strategy."
    Assert-True -Condition ($hardwareDoc -match "docs/shared-asset-installation.md") -Message "Hardware-aware docs should link shared asset planning."
    Assert-True -Condition ($hardwareDoc -match "docs/config-generation-strategy.md") -Message "Hardware-aware docs should link config generation strategy."
    Assert-True -Condition ($doc -match "docs/config-generation-strategy.md") -Message "Shared asset docs should link config generation strategy."
    Assert-True -Condition ($surfaceBundle -match "docs/config-generation-strategy.md") -Message "Surface bundle docs should link config generation strategy."
    Assert-True -Condition ($strategy -match "Project-local assets") -Message "Config strategy should include project-local assets."
    Assert-True -Condition ($strategy -match "Shared assets") -Message "Config strategy should include shared assets."
    Assert-True -Condition ($strategy -match "config/agent-surface-solutions\.json") -Message "Config strategy should reference surface solution status."
    Assert-True -Condition ($strategy -match "ModelLanes") -Message "Config strategy should reference the reusable model lane contract."
    Assert-True -Condition ($strategy -match "ContinueProfiles") -Message "Config strategy should keep ContinueProfiles scoped to Continue."
    Assert-True -Condition ($strategy -match 'Do not generate config for a surface with `planned` or `blocked`') -Message "Config strategy should keep future surfaces evidence-gated."
    Assert-True -Condition ($todo -match "centralized shared asset") -Message "TODO should track centralized shared asset work."
    Assert-True -Condition ($todo -match "\[x\] Add config-generation strategy") -Message "TODO should mark config generation strategy complete."
    Assert-True -Condition ($roadmap -match "centralized shared asset") -Message "Roadmap should track centralized shared asset work."
}
Invoke-PackTest "workflow registry defines stable UI entry points" {
    $registryPath = Join-Path $repoRoot "config/workflows.json"
    $envelopeContractPath = Join-Path $repoRoot "config/workflow-envelope-contract.json"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $linuxDispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.linux.sh"
    $macosDispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.macos.sh"
    $sharedShellDispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.shared.sh"
    $docPath = Join-Path $repoRoot "docs/workflow-registry.md"
    $envelopeDocPath = Join-Path $repoRoot "docs/workflow-envelope-contract.md"
    $consolidationPath = Join-Path $repoRoot "docs/script-consolidation-plan.md"
    $appendixPath = Join-Path $repoRoot "docs/script-reference-appendix.md"
    $autonomousQueuePath = Join-Path $repoRoot "docs/autonomous-maintainer-queue.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $roadmapPath = Join-Path $repoRoot "ROADMAP.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

    Assert-True -Condition (Test-Path -LiteralPath $registryPath) -Message "Workflow registry should exist."
    Assert-True -Condition (Test-Path -LiteralPath $envelopeContractPath) -Message "Workflow envelope contract should exist."
    Assert-True -Condition (Test-Path -LiteralPath $dispatcherPath) -Message "Workflow dispatcher should exist."
    Assert-True -Condition (Test-Path -LiteralPath $linuxDispatcherPath) -Message "Linux workflow dispatcher should exist."
    Assert-True -Condition (Test-Path -LiteralPath $macosDispatcherPath) -Message "macOS workflow dispatcher should exist."
    Assert-True -Condition (Test-Path -LiteralPath $sharedShellDispatcherPath) -Message "Shared shell workflow dispatcher should exist."
    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Workflow registry docs should exist."
    Assert-True -Condition (Test-Path -LiteralPath $envelopeDocPath) -Message "Workflow envelope docs should exist."
    Assert-True -Condition (Test-Path -LiteralPath $consolidationPath) -Message "Script consolidation plan should exist."
    Assert-True -Condition (Test-Path -LiteralPath $appendixPath) -Message "Script reference appendix should exist."
    Assert-True -Condition (Test-Path -LiteralPath $autonomousQueuePath) -Message "Autonomous maintainer queue docs should exist."

    $registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
    $envelopeContract = Get-Content -LiteralPath $envelopeContractPath -Raw | ConvertFrom-Json
    $doc = Get-Content -LiteralPath $docPath -Raw
    $envelopeDoc = Get-Content -LiteralPath $envelopeDocPath -Raw
    $consolidation = Get-Content -LiteralPath $consolidationPath -Raw
    $appendix = Get-Content -LiteralPath $appendixPath -Raw
    $autonomousQueue = Get-Content -LiteralPath $autonomousQueuePath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $roadmap = Get-Content -LiteralPath $roadmapPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw
    $allowedSafetyLevels = @("read-only", "network-read", "network-write", "controlled-write", "approved-write")
    $requiredWorkflowIds = @(
        "profile-local-hardware",
        "discover-online-models",
        "generate-model-scorecard",
        "generate-evidence-dashboard",
        "get-beginner-setup-plan",
        "show-agent-pack-menu",
        "show-workflow-chooser",
        "test-local-agent-models",
        "recommend-agent-config",
        "apply-agent-config",
        "classify-project",
        "install-pack-assets",
        "generate-runtime-context",
        "run-runtime-validation",
        "test-local-agent-health",
        "cleanup-local-agent-artifacts",
        "test-agent-cli-surface",
        "validate-pack",
        "test-pack",
        "test-release-readiness",
        "verify-hosted-ci"
    )

    Assert-Equal -Actual $registry.schemaVersion -Expected 1 -Message "Workflow registry schema version changed."
    Assert-Equal -Actual $envelopeContract.schemaVersion -Expected 1 -Message "Workflow envelope schema version changed."
    foreach ($eventType in @("accepted", "progress", "warning", "result", "error")) {
        Assert-True -Condition ($eventType -in @($envelopeContract.response.eventTypes)) -Message "Workflow envelope should define event type $eventType."
    }
    Assert-True -Condition (-not [bool]$envelopeContract.privacy.argumentValuesReturnedByDefault) -Message "Workflow envelope should omit argument values by default."
    Assert-True -Condition (-not [bool]$envelopeContract.privacy.childOutputReturnedByDefault) -Message "Workflow envelope should omit child output by default."
    Assert-True -Condition ($registry.workflows.Count -ge 10) -Message "Workflow registry should include core workflows."

    $ids = @{}
    foreach ($workflow in $registry.workflows) {
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($workflow.id)) -Message "Workflow should include id."
        Assert-True -Condition (-not $ids.ContainsKey($workflow.id)) -Message "Workflow id should be unique: $($workflow.id)"
        $ids[$workflow.id] = $true

        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($workflow.name)) -Message "Workflow should include name: $($workflow.id)"
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($workflow.purpose)) -Message "Workflow should include purpose: $($workflow.id)"
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($workflow.category)) -Message "Workflow should include category: $($workflow.id)"
        Assert-True -Condition ($workflow.safetyLevel -in $allowedSafetyLevels) -Message "Workflow has unsupported safety level: $($workflow.id)"
        Assert-True -Condition ($null -ne $workflow.uiReady) -Message "Workflow should state UI readiness: $($workflow.id)"
        Assert-True -Condition ($workflow.inputs.Count -gt 0) -Message "Workflow should list inputs: $($workflow.id)"
        Assert-True -Condition ($workflow.outputs.Count -gt 0) -Message "Workflow should list outputs: $($workflow.id)"
        Assert-True -Condition ($appendix -match [regex]::Escape(('`' + $workflow.id + '`'))) -Message "Script appendix should cover workflow: $($workflow.id)"
        Assert-True -Condition ($appendix -match [regex]::Escape(('`' + $workflow.safetyLevel + '`'))) -Message "Script appendix should include safety level for workflow: $($workflow.id)"

        foreach ($os in @("windows", "linux", "macos")) {
            $entry = $workflow.entryPoints.$os
            Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($entry)) -Message "Workflow should include $os entry point: $($workflow.id)"
            Assert-True -Condition ($entry -notmatch "^[A-Za-z]:|^/|\\|\.\.") -Message "Workflow entry point should be repository-relative and slash-normalized: $entry"
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot $entry)) -Message "Workflow entry point should exist: $entry"
        }
        Assert-True -Condition ($appendix -match [regex]::Escape(('`' + $workflow.entryPoints.windows + '`'))) -Message "Script appendix should include Windows entry point for workflow: $($workflow.id)"

        $serialized = $workflow | ConvertTo-Json -Depth 20
        Assert-True -Condition ($serialized -notmatch "192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|localhost|Users\\|OneDrive|itama|token|secret") -Message "Workflow registry should stay sanitized: $($workflow.id)"
    }

    foreach ($id in $requiredWorkflowIds) {
        Assert-True -Condition $ids.ContainsKey($id) -Message "Workflow registry should include $id."
    }

    Assert-True -Condition ($doc -match "Safety Levels") -Message "Workflow registry docs should explain safety levels."
    Assert-True -Condition ($doc -match "UI Direction") -Message "Workflow registry docs should explain UI direction."
    Assert-True -Condition ($doc -match "config/workflows\.json") -Message "Workflow registry docs should reference the JSON file."
    Assert-True -Condition ($doc -match "docs/workflow-chooser.md") -Message "Workflow registry docs should link workflow chooser."
    Assert-True -Condition ($doc -match "docs/script-consolidation-plan.md") -Message "Workflow registry docs should link script consolidation plan."
    Assert-True -Condition ($doc -match "scripts/invoke-workflow\.ps1") -Message "Workflow registry docs should reference the dispatcher."
    Assert-True -Condition ($doc -match "scripts/invoke-workflow\.\*\.sh") -Message "Workflow registry docs should reference cross-platform dispatchers."
    Assert-True -Condition ($doc -match "-List") -Message "Workflow registry docs should document dispatcher list mode."
    Assert-True -Condition ($doc -match "-DryRun") -Message "Workflow registry docs should document dispatcher dry-run mode."
    Assert-True -Condition ($doc -match "Versioned Automation Envelope") -Message "Workflow registry docs should explain envelope mode."
    Assert-True -Condition ($envelopeDoc -match "Privacy Boundary") -Message "Workflow envelope docs should explain privacy handling."
    Assert-True -Condition ($envelopeDoc -match "-RequestJson" -and $envelopeDoc -match "--request-json") -Message "Workflow envelope docs should include Windows and native shell examples."
    Assert-True -Condition ($doc -match "docs/autonomous-maintainer-queue.md") -Message "Workflow registry docs should link autonomous maintainer queue."
    Assert-True -Condition ($appendix -match "Workflow Reference") -Message "Script appendix should include workflow reference table."
    Assert-True -Condition ($appendix -match "docs/agent-pack-menu.md") -Message "Script appendix should point beginners to the guided menu."
    Assert-True -Condition ($appendix -match "Maintenance Rule") -Message "Script appendix should define maintenance rule."
    Assert-True -Condition ($readme -match "docs/workflow-registry.md") -Message "README should link workflow registry docs."
    Assert-True -Condition ($readme -match "docs/workflow-chooser.md") -Message "README should link workflow chooser docs."
    Assert-True -Condition ($readme -match "docs/script-consolidation-plan.md") -Message "README should link script consolidation plan."
    Assert-True -Condition ($readme -match "docs/script-reference-appendix.md") -Message "README should link script appendix."
    Assert-True -Condition ($readme -match "docs/autonomous-maintainer-queue.md") -Message "README should link autonomous maintainer queue."
    Assert-True -Condition ($autonomousQueue -match "Safe Without Prompt") -Message "Autonomous queue should define safe autonomous work."
    Assert-True -Condition ($autonomousQueue -match "Needs Explicit Input") -Message "Autonomous queue should define input boundaries."
    Assert-True -Condition ($autonomousQueue -match "docs/script-consolidation-plan.md") -Message "Autonomous queue should link script consolidation plan."
    Assert-True -Condition ($autonomousQueue -match "scripts/test-pack.ps1") -Message "Autonomous queue should require pack tests."
    Assert-True -Condition ($autonomousQueue -match "git status --short --branch") -Message "Autonomous queue should start from git status."
    Assert-True -Condition ($autonomousQueue -match "verify-hosted-ci\.ps1 -CommitSha <full-sha>") -Message "Autonomous queue should require exact-SHA hosted GitHub Actions verification after push."
    Assert-True -Condition ($autonomousQueue -match "gh run watch --exit-status") -Message "Autonomous queue should require watching the exact pushed GitHub Actions run."
    Assert-True -Condition ($autonomousQueue -match "exact commit SHA and run URL") -Message "Autonomous queue should require reporting the pushed commit and hosted CI run URL."
    Assert-True -Condition ($consolidation -match "shared engines") -Message "Script consolidation plan should define shared engine direction."
    Assert-True -Condition ($consolidation -match "thin wrappers") -Message "Script consolidation plan should define thin wrapper direction."
    Assert-True -Condition ($consolidation -match "config/workflows\.json") -Message "Script consolidation plan should reference workflow registry."
    Assert-True -Condition ($consolidation -match "scripts/invoke-workflow\.ps1") -Message "Script consolidation plan should reference workflow dispatcher."
    Assert-True -Condition ($consolidation -match "scripts/invoke-workflow\.\*\.sh") -Message "Script consolidation plan should reference cross-platform workflow dispatchers."
    Assert-True -Condition ($consolidation -match "Do Not Consolidate Yet") -Message "Script consolidation plan should define no-consolidate-yet cases."
    Assert-True -Condition ($consolidation -match "test-agent-cli-surface-models") -Message "Script consolidation plan should cover shared agent CLI testing."
    Assert-True -Condition ($consolidation -match "Roo Code" -and $consolidation -match "Kilo Code" -and $consolidation -match "OpenCode") -Message "Script consolidation plan should cover planned agent wrappers."
    Assert-True -Condition ($consolidation -match "scripts/test-pack\.ps1") -Message "Script consolidation plan should require pack tests."
    Assert-True -Condition ($roadmap -match "workflow registry") -Message "Roadmap should track workflow registry work."
    Assert-True -Condition ($roadmap -match "PowerShell/Linux/macOS dispatchers are done") -Message "Roadmap should track cross-platform dispatcher work."
    Assert-True -Condition ($roadmap -match "Script consolidation planning is documented") -Message "Roadmap should track script consolidation planning."
    Assert-True -Condition ($todo -match "workflow registry") -Message "TODO should track workflow registry work."
    Assert-True -Condition ($todo -match "\[x\] Add cross-platform workflow dispatcher wrappers") -Message "TODO should mark cross-platform dispatchers complete."
    Assert-True -Condition ($todo -match "\[x\] Define a versioned workflow request") -Message "TODO should mark the workflow envelope contract complete."
    Assert-True -Condition ($todo -match "\[x\] Add a script consolidation plan") -Message "TODO should mark script consolidation planning complete."
    Assert-True -Condition ($todo -match "\[x\] Consolidate the onboarding/navigation script family") -Message "TODO should mark the first script-family consolidation complete."
    Assert-True -Condition ($todo -match "\[x\] Replace the no-PowerShell informational fallback") -Message "TODO should mark native onboarding rendering complete."

    $listResult = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-List", "-Json")
    Assert-Equal -Actual $listResult.ExitCode -Expected 0 -Message "Workflow dispatcher list mode should succeed."
    Assert-True -Condition ($listResult.Output -match '"Id":\s*"validate-pack"') -Message "Workflow dispatcher list output should include validate-pack."

    $dryRunResult = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "validate-pack", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-ExpectedVersion","0.2.0"]')
    Assert-Equal -Actual $dryRunResult.ExitCode -Expected 0 -Message "Workflow dispatcher dry run should succeed."
    Assert-True -Condition ($dryRunResult.Output -match "scripts/validate-pack\.ps1") -Message "Workflow dispatcher dry run should resolve validate-pack script."
    Assert-True -Condition ($dryRunResult.Output -match "read-only") -Message "Workflow dispatcher dry run should include safety level."
    Assert-True -Condition ($dryRunResult.Output -match "ExpectedVersion") -Message "Workflow dispatcher dry run should preserve passthrough arguments."

    $requestJson = @{ schemaVersion = 1; requestId = "pack-test"; workflowId = "validate-pack"; platform = "windows"; dryRun = $true; arguments = @("-ExpectedVersion", "0.2.0") } | ConvertTo-Json -Compress
    $envelopeResult = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-RequestJson", $requestJson)
    Assert-Equal -Actual $envelopeResult.ExitCode -Expected 0 -Message "PowerShell workflow request envelope should succeed."
    $envelope = $envelopeResult.Output | ConvertFrom-Json
    Assert-Equal -Actual $envelope.SchemaVersion -Expected 1 -Message "PowerShell workflow response should use schema v1."
    Assert-Equal -Actual $envelope.Status -Expected "planned" -Message "PowerShell dry-run envelope should be planned."
    Assert-Equal -Actual $envelope.Workflow.ArgumentCount -Expected 2 -Message "PowerShell envelope should report argument count."
    Assert-True -Condition (-not $envelope.Result.Invoked) -Message "PowerShell dry-run envelope should not invoke the workflow."
    Assert-True -Condition ($envelopeResult.Output -notmatch "ExpectedVersion") -Message "PowerShell envelope should not echo argument values by default."
    Assert-True -Condition ("warning" -in @($envelope.Events.Type)) -Message "PowerShell dry-run envelope should include a warning event."

    $badRequestJson = '{"schemaVersion":1,"requestId":"pack-error","workflowId":"missing-workflow","platform":"windows","dryRun":true,"arguments":[]}'
    $errorEnvelopeResult = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-RequestJson", $badRequestJson)
    Assert-True -Condition ($errorEnvelopeResult.ExitCode -ne 0) -Message "PowerShell workflow envelope should preserve failure exit codes."
    Assert-True -Condition ($errorEnvelopeResult.Output -match '"type":\s*"error"') -Message "PowerShell workflow failure should return an error event."
    Assert-True -Condition ($errorEnvelopeResult.Output -match '"requestId":\s*"pack-error"') -Message "PowerShell workflow failure should preserve the request id."
    Assert-True -Condition ($envelopeResult.Output -cmatch '"schemaVersion"' -and $envelopeResult.Output -cnotmatch '"SchemaVersion"') -Message "PowerShell envelope keys should match the lower-camel-case cross-platform wire format."

    $executionRequestJson = @{ schemaVersion = 1; requestId = "pack-execution"; workflowId = "validate-pack"; platform = "windows"; dryRun = $false; arguments = @("-ExpectedVersion", "0.2.0") } | ConvertTo-Json -Compress
    $executionEnvelopeResult = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-RequestJson", $executionRequestJson)
    Assert-Equal -Actual $executionEnvelopeResult.ExitCode -Expected 0 -Message "PowerShell workflow envelope should preserve named arguments during execution."
    $executionEnvelope = $executionEnvelopeResult.Output | ConvertFrom-Json
    Assert-Equal -Actual $executionEnvelope.status -Expected "succeeded" -Message "PowerShell execution envelope should report success."
    Assert-True -Condition ([bool]$executionEnvelope.result.invoked) -Message "PowerShell execution envelope should report invocation."
    Assert-True -Condition ($executionEnvelope.result.outputLineCount -gt 0) -Message "PowerShell execution envelope should report captured output count."
    Assert-True -Condition ("output" -notin @($executionEnvelope.result.PSObject.Properties.Name)) -Message "PowerShell execution envelope should omit child output by default."

    $sharedShell = Get-Content -LiteralPath $sharedShellDispatcherPath -Raw
    $linuxDispatcher = Get-Content -LiteralPath $linuxDispatcherPath -Raw
    $macosDispatcher = Get-Content -LiteralPath $macosDispatcherPath -Raw
    Assert-True -Condition ($sharedShell -match "config/workflows\.json") -Message "Shared shell dispatcher should read workflow registry."
    Assert-True -Condition ($sharedShell -match "Workflow not found") -Message "Shared shell dispatcher should report unknown workflows."
    Assert-True -Condition ($sharedShell -notmatch "pwsh") -Message "Shared shell dispatcher should not require PowerShell."
    Assert-True -Condition ($linuxDispatcher -match "invoke-workflow\.shared\.sh" -and $linuxDispatcher -match "--platform linux") -Message "Linux dispatcher should delegate to shared dispatcher."
    Assert-True -Condition ($macosDispatcher -match "invoke-workflow\.shared\.sh" -and $macosDispatcher -match "--platform macos") -Message "macOS dispatcher should delegate to shared dispatcher."

    $testBash = Get-TestBashPath
    $canRunShellDispatcher = $false
    if ($testBash) {
        & $testBash -c "python3 --version" *> $null
        $canRunShellDispatcher = $LASTEXITCODE -eq 0
    }
    if ($canRunShellDispatcher) {
        $linuxListResult = & $testBash $linuxDispatcherPath --list --json 2>&1
        $linuxListText = $linuxListResult | Out-String
        Assert-Equal -Actual $LASTEXITCODE -Expected 0 -Message "Linux workflow dispatcher list mode should succeed."
        Assert-True -Condition ($linuxListText -match '"Id":\s*"validate-pack"|\"Id\":\"validate-pack\"') -Message "Linux workflow dispatcher list output should include validate-pack."

        $linuxDryRunResult = & $testBash $linuxDispatcherPath --workflow-id validate-pack --dry-run --json --workflow-arguments-json '["--expected-version","0.2.0"]' 2>&1
        $linuxDryRunText = $linuxDryRunResult | Out-String
        Assert-Equal -Actual $LASTEXITCODE -Expected 0 -Message "Linux workflow dispatcher dry run should succeed."
        Assert-True -Condition ($linuxDryRunText -match "scripts/validate-pack\.linux\.sh") -Message "Linux workflow dispatcher should resolve Linux validate-pack script."
        Assert-True -Condition ($linuxDryRunText -match "read-only") -Message "Linux workflow dispatcher dry run should include safety level."
        Assert-True -Condition ($linuxDryRunText -match "expected-version") -Message "Linux workflow dispatcher dry run should preserve passthrough arguments."

        $linuxRequest = '{"schemaVersion":1,"requestId":"pack-bash","workflowId":"validate-pack","platform":"linux","dryRun":true,"arguments":["--expected-version","0.2.0"]}'
        $linuxEnvelopeResult = & $testBash $linuxDispatcherPath --request-json $linuxRequest 2>&1
        $linuxEnvelopeText = $linuxEnvelopeResult | Out-String
        Assert-Equal -Actual $LASTEXITCODE -Expected 0 -Message "Linux workflow request envelope should succeed."
        $linuxEnvelope = $linuxEnvelopeText | ConvertFrom-Json
        Assert-Equal -Actual $linuxEnvelope.schemaVersion -Expected 1 -Message "Linux workflow response should use schema v1."
        Assert-Equal -Actual $linuxEnvelope.status -Expected "planned" -Message "Linux dry-run envelope should be planned."
        Assert-True -Condition ($linuxEnvelopeText -notmatch "expected-version") -Message "Linux envelope should not echo argument values by default."

        $macosDryRunResult = & $testBash $macosDispatcherPath --workflow-id validate-pack --dry-run --json 2>&1
        $macosDryRunText = $macosDryRunResult | Out-String
        Assert-Equal -Actual $LASTEXITCODE -Expected 0 -Message "macOS workflow dispatcher dry run should succeed."
        Assert-True -Condition ($macosDryRunText -match "scripts/validate-pack\.macos\.sh") -Message "macOS workflow dispatcher should resolve macOS validate-pack script."
    }

    $missingResult = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "missing-workflow", "-DryRun")
    Assert-True -Condition ($missingResult.ExitCode -ne 0) -Message "Workflow dispatcher should fail for an unknown workflow."
    Assert-True -Condition ($missingResult.Output -match "Workflow not found") -Message "Workflow dispatcher should report an unknown workflow."
}
Invoke-PackTest "agent surface capability matrix preserves parity" {
    $matrixPath = Join-Path $repoRoot "config/agent-surface-capabilities.json"
    $registryPath = Join-Path $repoRoot "config/workflows.json"
    $docPath = Join-Path $repoRoot "docs/agent-surface-capability-parity.md"
    $optionsPath = Join-Path $repoRoot "docs/agent-surface-options.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

    Assert-True -Condition (Test-Path -LiteralPath $matrixPath) -Message "Agent surface capability matrix should exist."
    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Agent surface capability parity doc should exist."

    $matrix = Get-Content -LiteralPath $matrixPath -Raw | ConvertFrom-Json
    $registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
    $doc = Get-Content -LiteralPath $docPath -Raw
    $options = Get-Content -LiteralPath $optionsPath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw

    $allowedStatuses = @($matrix.statusLevels)
    $workflowIds = @{}
    foreach ($workflow in $registry.workflows) {
        $workflowIds[$workflow.id] = $true
    }

    Assert-Equal -Actual $matrix.schemaVersion -Expected 1 -Message "Agent surface capability schema version changed."
    Assert-True -Condition ($matrix.activities.Count -ge 8) -Message "Capability matrix should track core activities."
    Assert-True -Condition ($matrix.surfaces.Count -ge 7) -Message "Capability matrix should track known agent surfaces."

    foreach ($requiredSurface in @("continue", "cline", "aider", "roo-code", "kilo-code", "opencode", "openhands")) {
        Assert-True -Condition (@($matrix.surfaces | Where-Object { $_.id -eq $requiredSurface }).Count -eq 1) -Message "Capability matrix should include $requiredSurface."
    }

    foreach ($surface in $matrix.surfaces) {
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($surface.id)) -Message "Surface should include id."
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($surface.name)) -Message "Surface should include name: $($surface.id)"
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($surface.currentValidationLevel)) -Message "Surface should include validation level: $($surface.id)"

        foreach ($activity in $matrix.activities) {
            $entry = $surface.activities.$activity
            Assert-True -Condition ($null -ne $entry) -Message "$($surface.id) should track $activity."
            Assert-True -Condition ($entry.status -in $allowedStatuses) -Message "$($surface.id) $activity should use a known status."
            Assert-True -Condition ($null -ne $entry.entryPoints) -Message "$($surface.id) $activity should include entry point list."
            Assert-True -Condition ($entry.evidence.Count -gt 0) -Message "$($surface.id) $activity should include evidence references."

            foreach ($entryPoint in @($entry.entryPoints)) {
                Assert-True -Condition $workflowIds.ContainsKey($entryPoint) -Message "$($surface.id) $activity should reference known workflow $entryPoint."
            }

            foreach ($evidence in @($entry.evidence)) {
                Assert-True -Condition ($evidence -notmatch "^[A-Za-z]:|^/|\\|\.\.|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|Users|OneDrive|itama|token|secret") -Message "$($surface.id) $activity evidence should stay sanitized: $evidence"
                Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot $evidence)) -Message "$($surface.id) $activity evidence should exist: $evidence"
            }
        }
    }

    Assert-True -Condition ($doc -match "Install") -Message "Parity doc should mention install activity."
    Assert-True -Condition ($doc -match "Configure") -Message "Parity doc should mention configure activity."
    Assert-True -Condition ($doc -match "Test") -Message "Parity doc should mention test activity."
    Assert-True -Condition ($doc -match "config/agent-surface-capabilities\.json") -Message "Parity doc should point to matrix."
    Assert-True -Condition ($options -match "Compatibility Matrix") -Message "Surface options doc should retain compatibility matrix."
    Assert-True -Condition ($todo -match "surface-specific config") -Message "TODO should track surface-specific config work."
}
Invoke-PackTest "workflow chooser summarizes registry commands" {
    $scriptPath = Join-Path $repoRoot "scripts/show-workflow-chooser.ps1"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $registryPath = Join-Path $repoRoot "config/workflows.json"
    $docPath = Join-Path $repoRoot "docs/workflow-chooser.md"
    $menuDocPath = Join-Path $repoRoot "docs/agent-pack-menu.md"
    $appendixPath = Join-Path $repoRoot "docs/script-reference-appendix.md"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "workflow-chooser-test-$([guid]::NewGuid())"
    $jsonPath = Join-Path $tempRoot "workflow-chooser.json"
    $markdownPath = Join-Path $tempRoot "workflow-chooser.md"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

        $result = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-Platform", "windows", "-OutputPath", $jsonPath, "-MarkdownOutputPath", $markdownPath, "-AsJson")
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Workflow chooser generation should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $jsonPath) -Message "Workflow chooser should write JSON output."
        Assert-True -Condition (Test-Path -LiteralPath $markdownPath) -Message "Workflow chooser should write Markdown output."

        $report = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
        $markdown = Get-Content -LiteralPath $markdownPath -Raw
        $registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
        $doc = Get-Content -LiteralPath $docPath -Raw
        $menuDoc = Get-Content -LiteralPath $menuDocPath -Raw
        $appendix = Get-Content -LiteralPath $appendixPath -Raw

        Assert-Equal -Actual $report.SchemaVersion -Expected 1 -Message "Workflow chooser schema version should be stable."
        Assert-Equal -Actual $report.SourceWorkflowRegistry -Expected "config/workflows.json" -Message "Workflow chooser should identify source registry."
        Assert-Equal -Actual $report.WorkflowCount -Expected @($registry.workflows).Count -Message "Workflow chooser should cover every registered workflow."
        Assert-True -Condition ($report.UiReadyCount -ge 1) -Message "Workflow chooser should count UI-ready workflows."
        Assert-True -Condition (@($report.Workflows | Where-Object { $_.Id -eq "show-agent-pack-menu" -and $_.Reference -eq "docs/agent-pack-menu.md" }).Count -eq 1) -Message "Workflow chooser should include guided menu workflow."
        Assert-True -Condition (@($report.Workflows | Where-Object { $_.Id -eq "show-workflow-chooser" -and $_.Reference -eq "docs/workflow-chooser.md" }).Count -eq 1) -Message "Workflow chooser should reference its own docs."
        Assert-True -Condition (@($report.Workflows | Where-Object { $_.Id -eq "build-release-package" -and $_.UiReady -eq $false }).Count -eq 1) -Message "Workflow chooser should include non-UI workflows."
        Assert-True -Condition (@($report.Workflows | Where-Object { $_.Command -match "scripts\\show-workflow-chooser\.ps1" }).Count -eq 1) -Message "Workflow chooser should include its Windows command."

        foreach ($workflow in @($registry.workflows)) {
            Assert-True -Condition (@($report.Workflows | Where-Object { $_.Id -eq $workflow.id }).Count -eq 1) -Message "Workflow chooser should include $($workflow.id)."
        }

        Assert-True -Condition ($markdown -match "Workflow Chooser") -Message "Workflow chooser markdown should include title."
        Assert-True -Condition ($markdown -match "docs/script-reference-appendix.md") -Message "Workflow chooser markdown should link appendix."
        Assert-True -Condition ($doc -match "config/workflows\.json") -Message "Workflow chooser docs should reference workflow registry."
        Assert-True -Condition ($menuDoc -match "docs/workflow-chooser.md") -Message "Agent pack menu docs should link workflow chooser."
        Assert-True -Condition ($appendix -match "show-workflow-chooser") -Message "Script appendix should cover workflow chooser."
        Assert-True -Condition ($result.Output -notmatch "192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}|Users\\|OneDrive|itama|token|secret") -Message "Workflow chooser output should stay sanitized."

        $dispatch = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "show-workflow-chooser", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-AsJson"]')
        Assert-Equal -Actual $dispatch.ExitCode -Expected 0 -Message "Workflow dispatcher should resolve workflow chooser."
        Assert-True -Condition ($dispatch.Output -match "scripts/show-workflow-chooser\.ps1") -Message "Dispatcher should point at the workflow chooser script."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "onboarding generators share common engines" {
    $modulePath = Join-Path $repoRoot "scripts/OnboardingGuidance.psm1"
    $dispatcherPath = Join-Path $repoRoot "scripts/onboarding-guidance.shared.sh"
    $nativeRendererPath = Join-Path $repoRoot "scripts/onboarding-guidance.py"
    $module = Get-Content -LiteralPath $modulePath -Raw
    $dispatcher = Get-Content -LiteralPath $dispatcherPath -Raw
    $nativeRenderer = Get-Content -LiteralPath $nativeRendererPath -Raw

    foreach ($scriptName in @("get-beginner-setup-plan.ps1", "show-agent-pack-menu.ps1", "show-workflow-chooser.ps1")) {
        $content = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/$scriptName") -Raw
        Assert-True -Condition ($content -match "OnboardingGuidance\.psm1") -Message "$scriptName should import the shared onboarding module."
        Assert-True -Condition ($content -match "Write-OnboardingReport") -Message "$scriptName should use shared report output."
        Assert-True -Condition ($content -notmatch "function Get-ScriptCommand") -Message "$scriptName should not redefine platform command rendering."
    }

    $nativeViews = @{
        "get-beginner-setup-plan.shared.sh" = "beginner-plan"
        "show-agent-pack-menu.shared.sh" = "agent-menu"
        "show-workflow-chooser.shared.sh" = "workflow-chooser"
    }
    foreach ($entry in $nativeViews.GetEnumerator()) {
        $content = Get-Content -LiteralPath (Join-Path $repoRoot "scripts/$($entry.Key)") -Raw
        Assert-True -Condition ($content -match "onboarding-guidance\.shared\.sh") -Message "$($entry.Key) should delegate to the shared native dispatcher."
        Assert-True -Condition ($content -match [regex]::Escape($entry.Value)) -Message "$($entry.Key) should select $($entry.Value)."
        Assert-True -Condition ($content -notmatch "while \[") -Message "$($entry.Key) should remain a thin wrapper."
    }

    foreach ($functionName in @("Import-OnboardingJson", "Get-OnboardingWorkflow", "Get-OnboardingScriptCommand", "Write-OnboardingReport")) {
        Assert-True -Condition ($module -match [regex]::Escape($functionName)) -Message "Shared onboarding module should expose $functionName."
    }
    foreach ($view in @("beginner-plan", "agent-menu", "workflow-chooser")) {
        Assert-True -Condition ($dispatcher -match [regex]::Escape($view)) -Message "Native onboarding dispatcher should recognize $view."
    }
    Assert-True -Condition (Test-Path -LiteralPath $nativeRendererPath) -Message "Native onboarding renderer should exist."
    Assert-True -Condition ($dispatcher -match "onboarding-guidance\.py") -Message "Native onboarding dispatcher should call the Python renderer."
    Assert-True -Condition ($dispatcher -notmatch "Full native rendering is not available") -Message "Native onboarding dispatcher should not retain the PowerShell-only fallback."
    Assert-True -Condition ($nativeRenderer -match "workflow-chooser") -Message "Native renderer should support the workflow chooser."
}
Invoke-PackTest "agent surface solutions define install configure and test" {
    $solutionsPath = Join-Path $repoRoot "config/agent-surface-solutions.json"
    $matrixPath = Join-Path $repoRoot "config/agent-surface-capabilities.json"
    $registryPath = Join-Path $repoRoot "config/workflows.json"
    $docPath = Join-Path $repoRoot "docs/agent-surface-solutions.md"
    $bundleDocPath = Join-Path $repoRoot "docs/surface-specific-config-bundles.md"
    $promotionGatesPath = Join-Path $repoRoot "docs/agent-surface-promotion-gates.md"
    $menuDocPath = Join-Path $repoRoot "docs/agent-pack-menu.md"
    $dashboardDocPath = Join-Path $repoRoot "docs/evidence-dashboard.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

    Assert-True -Condition (Test-Path -LiteralPath $solutionsPath) -Message "Agent surface solution catalog should exist."
    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Agent surface solution docs should exist."
    Assert-True -Condition (Test-Path -LiteralPath $bundleDocPath) -Message "Surface-specific config bundle policy docs should exist."
    Assert-True -Condition (Test-Path -LiteralPath $promotionGatesPath) -Message "Agent surface promotion gates docs should exist."

    $solutions = Get-Content -LiteralPath $solutionsPath -Raw | ConvertFrom-Json
    $matrix = Get-Content -LiteralPath $matrixPath -Raw | ConvertFrom-Json
    $registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
    $doc = Get-Content -LiteralPath $docPath -Raw
    $bundleDoc = Get-Content -LiteralPath $bundleDocPath -Raw
    $promotionGates = Get-Content -LiteralPath $promotionGatesPath -Raw
    $menuDoc = Get-Content -LiteralPath $menuDocPath -Raw
    $dashboardDoc = Get-Content -LiteralPath $dashboardDocPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw

    $allowedStatuses = @($solutions.statusLevels)
    $workflowIds = @{}
    foreach ($workflow in $registry.workflows) {
        $workflowIds[$workflow.id] = $true
    }

    Assert-Equal -Actual $solutions.schemaVersion -Expected 1 -Message "Agent surface solution schema version should be stable."
    Assert-True -Condition (@($solutions.requiredActivities) -contains "install") -Message "Solution catalog should require install."
    Assert-True -Condition (@($solutions.requiredActivities) -contains "configure") -Message "Solution catalog should require configure."
    Assert-True -Condition (@($solutions.requiredActivities) -contains "test") -Message "Solution catalog should require test."
    Assert-True -Condition ($null -ne $solutions.configBundlePolicy) -Message "Solution catalog should define config bundle policy."
    Assert-Equal -Actual $solutions.configBundlePolicy.defaultSurface -Expected "continue" -Message "Continue should remain the default generated bundle surface."
    Assert-True -Condition ($solutions.configBundlePolicy.decision -match "only after compatibility evidence") -Message "Config bundle policy should be evidence-gated."
    Assert-True -Condition (@($solutions.configBundlePolicy.evidence) -contains "docs/surface-specific-config-bundles.md") -Message "Config bundle policy should cite policy docs."
    Assert-Equal -Actual @($solutions.surfaces).Count -Expected @($matrix.surfaces).Count -Message "Solution catalog should cover every capability matrix surface."

    foreach ($matrixSurface in @($matrix.surfaces)) {
        Assert-True -Condition (@($solutions.surfaces | Where-Object { $_.id -eq $matrixSurface.id }).Count -eq 1) -Message "Solution catalog should include $($matrixSurface.id)."
    }

    foreach ($surface in @($solutions.surfaces)) {
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($surface.id)) -Message "Solution surface should include id."
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($surface.name)) -Message "Solution surface should include name: $($surface.id)"
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($surface.currentValidationLevel)) -Message "Solution surface should include validation level: $($surface.id)"
        Assert-True -Condition ($null -ne $surface.configBundle) -Message "$($surface.id) should define config bundle status."
        Assert-True -Condition ($surface.configBundle.status -in $allowedStatuses) -Message "$($surface.id) config bundle should use a known status."
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($surface.configBundle.strategy)) -Message "$($surface.id) config bundle should describe strategy."
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($surface.configBundle.outputKind)) -Message "$($surface.id) config bundle should describe output kind."
        Assert-True -Condition ($surface.configBundle.evidence.Count -gt 0) -Message "$($surface.id) config bundle should include evidence."

        foreach ($evidence in @($surface.configBundle.evidence)) {
            Assert-True -Condition ($evidence -notmatch "^[A-Za-z]:|^/|\\|\.\.|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|Users|OneDrive|itama|token|secret") -Message "$($surface.id) config bundle evidence should stay sanitized: $evidence"
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot $evidence)) -Message "$($surface.id) config bundle evidence should exist: $evidence"
        }

        if ($surface.id -in @("continue", "aider")) {
            Assert-Equal -Actual $surface.configBundle.status -Expected "supported" -Message "$($surface.id) config bundle should be supported after evidence gates pass."
        } else {
            Assert-True -Condition ($surface.configBundle.status -ne "supported") -Message "$($surface.id) config bundle should not be supported before evidence gates pass."
        }

        foreach ($activity in @("install", "configure", "test")) {
            $entry = $surface.$activity
            Assert-True -Condition ($null -ne $entry) -Message "$($surface.id) should define $activity solution."
            Assert-True -Condition ($entry.status -in $allowedStatuses) -Message "$($surface.id) $activity should use a known status."
            Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($entry.solution)) -Message "$($surface.id) $activity should describe a solution."
            Assert-True -Condition ($null -ne $entry.workflowIds) -Message "$($surface.id) $activity should include workflowIds."
            Assert-True -Condition ($entry.evidence.Count -gt 0) -Message "$($surface.id) $activity should include evidence."
            Assert-True -Condition ($null -ne $entry.blockedReason) -Message "$($surface.id) $activity should include blockedReason field."

            foreach ($workflowId in @($entry.workflowIds)) {
                Assert-True -Condition $workflowIds.ContainsKey($workflowId) -Message "$($surface.id) $activity should reference known workflow $workflowId."
            }

            foreach ($evidence in @($entry.evidence)) {
                Assert-True -Condition ($evidence -notmatch "^[A-Za-z]:|^/|\\|\.\.|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|Users|OneDrive|itama|token|secret") -Message "$($surface.id) $activity evidence should stay sanitized: $evidence"
                Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot $evidence)) -Message "$($surface.id) $activity evidence should exist: $evidence"
            }

            if ($entry.status -in @("planned", "blocked")) {
                Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($entry.blockedReason)) -Message "$($surface.id) $activity should explain planned or blocked status."
            }
        }
    }

    foreach ($support in @("health", "cleanup", "releaseReadiness", "modelSelection", "evidence")) {
        $entry = $solutions.sharedSupport.$support
        Assert-True -Condition ($null -ne $entry) -Message "Shared support should include $support."
        Assert-True -Condition ($entry.status -in $allowedStatuses) -Message "Shared support $support should use a known status."
        foreach ($workflowId in @($entry.workflowIds)) {
            Assert-True -Condition $workflowIds.ContainsKey($workflowId) -Message "Shared support $support should reference known workflow $workflowId."
        }
    }

    Assert-True -Condition ($doc -match "Install") -Message "Solution docs should mention install."
    Assert-True -Condition ($doc -match "Configure") -Message "Solution docs should mention configure."
    Assert-True -Condition ($doc -match "Test") -Message "Solution docs should mention test."
    Assert-True -Condition ($doc -match "surface-specific-config-bundles\.md") -Message "Solution docs should link config bundle policy."
    Assert-True -Condition ($doc -match "agent-surface-promotion-gates\.md") -Message "Solution docs should link promotion gates."
    Assert-True -Condition ($bundleDoc -match "Continue and Aider") -Message "Config bundle docs should identify the supported generated config surfaces."
    Assert-True -Condition ($bundleDoc -match "Scoped write validation") -Message "Config bundle docs should require write validation before promotion."
    Assert-True -Condition ($promotionGates -match "Install supported") -Message "Promotion gates should define install promotion."
    Assert-True -Condition ($promotionGates -match "Configure supported") -Message "Promotion gates should define configure promotion."
    Assert-True -Condition ($menuDoc -match "docs/agent-surface-solutions.md") -Message "Menu docs should link solution catalog."
    Assert-True -Condition ($dashboardDoc -match "docs/agent-surface-solutions.md") -Message "Evidence dashboard docs should link solution catalog."
    Assert-True -Condition ($readme -match "docs/agent-surface-solutions.md") -Message "README should link solution catalog."
    Assert-True -Condition ($readme -match "docs/surface-specific-config-bundles.md") -Message "README should link config bundle policy."
    Assert-True -Condition ($todo -match "surface-neutral install/configure/test solution catalog") -Message "TODO should track solution catalog completion."
    Assert-True -Condition ($todo -match "\[x\] Decide whether install scripts should generate surface-specific config bundles") -Message "TODO should mark config bundle decision complete."
}
Invoke-PackTest "agent surface adapters plan installs configure and report health safely" {
    $adapterPath = Join-Path $repoRoot "scripts/setup-agent-surface.ps1"
    $sharedPath = Join-Path $repoRoot "scripts/setup-agent-surface.shared.sh"
    $registryPath = Join-Path $repoRoot "config/workflows.json"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "aider-adapter-test-$([guid]::NewGuid())"
    $recommendationPath = Join-Path $tempRoot "recommendation.json"

    try {
        New-Item -ItemType Directory -Force -Path (Join-Path $tempRoot ".git/info") | Out-Null
        "" | Set-Content -LiteralPath (Join-Path $tempRoot ".git/info/exclude")
        @"
{
  "Recommendation": {
    "WriteSafeModel": "qwen3.5:9b",
    "PlanOnlyModel": "devstral-small-2:24b",
    "DeepReviewModel": "qwen3-coder:30b"
  }
}
"@ | Set-Content -LiteralPath $recommendationPath

        $plan = Invoke-CommandCapture -FilePath $adapterPath -Arguments @("-Action", "Plan")
        Assert-Equal -Actual $plan.ExitCode -Expected 0 -Message "Aider adapter plan should succeed."
        Assert-True -Condition ($plan.Output -match "aider-install" -and $plan.Output -match "local-only") -Message "Aider plan should describe install and config safety."

        $install = Invoke-CommandCapture -FilePath $adapterPath -Arguments @("-Action", "Install", "-InstallMethod", "pipx", "-DryRun")
        Assert-Equal -Actual $install.ExitCode -Expected 0 -Message "Aider install dry run should succeed."
        Assert-True -Condition ($install.Output -match "pipx install aider-chat" -and $install.Output -match "no network install") -Message "Aider install dry run should be explicit and non-networking."

        $configure = Invoke-CommandCapture -FilePath $adapterPath -Arguments @("-Action", "Configure", "-TargetRepo", $tempRoot, "-RecommendationPath", $recommendationPath, "-Lane", "PlanOnly", "-OllamaBaseUrl", "http://example.invalid:11434")
        Assert-Equal -Actual $configure.ExitCode -Expected 0 -Message "Aider config generation should succeed."
        $configPath = Join-Path $tempRoot ".aider.conf.local.yml"
        $config = Get-Content -LiteralPath $configPath -Raw
        Assert-True -Condition ($config -match "model: ollama_chat/devstral-small-2:24b") -Message "Aider config should use the requested recommendation lane."
        Assert-True -Condition ($config -match "OLLAMA_API_BASE=http://example\.invalid:11434") -Message "Aider config should contain the explicit local endpoint."
        Assert-True -Condition ($config -match "auto-commits: false" -and $config -match "dirty-commits: false") -Message "Aider config should disable automatic commits."
        Assert-True -Condition (@(Get-Content -LiteralPath (Join-Path $tempRoot ".git/info/exclude")) -contains ".aider.conf.local.yml") -Message "Generated Aider config should be locally excluded from Git."

        $kiloPlan = Invoke-CommandCapture -FilePath $adapterPath -Arguments @("-Action", "Plan", "-Surface", "kilo")
        Assert-Equal -Actual $kiloPlan.ExitCode -Expected 0 -Message "Kilo Code adapter plan should succeed."
        Assert-True -Condition ($kiloPlan.Output -match "@kilocode/cli" -and $kiloPlan.Output -match "local-only") -Message "Kilo Code plan should describe its npm install and local config boundary."

        $kiloConfigure = Invoke-CommandCapture -FilePath $adapterPath -Arguments @("-Action", "Configure", "-Surface", "kilo", "-TargetRepo", $tempRoot, "-RecommendationPath", $recommendationPath, "-Lane", "WriteSafe", "-OllamaBaseUrl", "http://example.invalid:11434")
        Assert-Equal -Actual $kiloConfigure.ExitCode -Expected 0 -Message "Kilo Code config generation should succeed."
        $kiloConfigPath = Join-Path $tempRoot ".kilo.local.json"
        $kiloConfig = Get-Content -LiteralPath $kiloConfigPath -Raw | ConvertFrom-Json
        Assert-Equal -Actual $kiloConfig.model -Expected "local-ollama/qwen3.5:9b" -Message "Kilo Code config should use the requested recommendation lane."
        Assert-True -Condition ($null -ne $kiloConfig.provider.'local-ollama') -Message "Kilo Code config should define the local Ollama provider."
        Assert-Equal -Actual $kiloConfig.provider.'local-ollama'.options.baseURL -Expected "http://example.invalid:11434/v1" -Message "Kilo Code config should use an OpenAI-compatible Ollama endpoint."
        Assert-True -Condition ($kiloConfig.provider.'local-ollama'.models.'qwen3.5:9b'.tool_call) -Message "Kilo Code config should declare tool-call capability."
        Assert-True -Condition ($kiloConfig.permission.'*' -eq "ask" -and $kiloConfig.permission.edit -eq "ask") -Message "Kilo Code config should require approval for writes."
        Assert-True -Condition (@(Get-Content -LiteralPath (Join-Path $tempRoot ".git/info/exclude")) -contains ".kilo.local.json") -Message "Generated Kilo Code config should be locally excluded from Git."

        $health = Invoke-CommandCapture -FilePath $adapterPath -Arguments @("-Action", "Health", "-TargetRepo", $tempRoot, "-AiderCommand", (Get-Process -Id $PID).Path)
        Assert-Equal -Actual $health.ExitCode -Expected 0 -Message "Aider health should pass with an available command and valid local config."
        Assert-True -Condition ($health.Output -match '"Status":\s*"healthy"') -Message "Aider health should emit a healthy structured result."

        $registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
        $workflow = @($registry.workflows | Where-Object id -eq "setup-agent-surface")[0]
        Assert-True -Condition ($null -ne $workflow -and $workflow.uiReady) -Message "Aider adapter should be exposed through the UI-ready workflow registry."
        Assert-Equal -Actual $workflow.entryPoints.windows -Expected "scripts/setup-agent-surface.ps1" -Message "Workflow should use the unified Windows adapter."

        $shared = Get-Content -LiteralPath $sharedPath -Raw
        Assert-True -Condition ($shared -notmatch "pwsh") -Message "Native Aider adapter should not require PowerShell."
        Assert-True -Condition ($shared -match "local-ollama") -Message "Native adapter should generate Kilo Code's local Ollama provider config."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "solution architecture review tracks milestone gaps" {
    $docPath = Join-Path $repoRoot "docs/solution-architecture-review.md"
    $uiDocPath = Join-Path $repoRoot "docs/unified-starter-toolkit-ui.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Solution architecture review doc should exist."
    Assert-True -Condition (Test-Path -LiteralPath $uiDocPath) -Message "Unified starter toolkit UI design doc should exist."

    $doc = Get-Content -LiteralPath $docPath -Raw
    $uiDoc = Get-Content -LiteralPath $uiDocPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw

    Assert-True -Condition ($doc -match "Review Standard") -Message "Solution architecture review should define review standard."
    Assert-True -Condition ($doc -match "Previous Chat Interpretation") -Message "Solution architecture review should preserve stricter prior chat interpretation."
    Assert-True -Condition ($doc -match "documentation, scaffolding, or a candidate path") -Message "Solution architecture review should not treat scaffolding alone as complete."
    Assert-True -Condition ($doc -match "comparable `Install`, `Configure`, and `Test` coverage") -Message "Solution architecture review should require install/configure/test parity for agent surface milestones."
    Assert-True -Condition ($doc -match "Generated sample repositories can satisfy validation coverage") -Message "Solution architecture review should document generated-sample validation acceptance."
    Assert-True -Condition ($doc -match "Hosted GitHub Actions status must be checked") -Message "Solution architecture review should require hosted CI status checks after pushes."
    Assert-True -Condition ($doc -match "Milestone Audit") -Message "Solution architecture review should include milestone audit."
    foreach ($milestone in @("1: Minimum Usable Pack", "17: Agent Surface Compatibility Validation", "18: Language Rule Packs", "19: Installer Profiles", "20: Hardware-Aware Model")) {
        Assert-True -Condition ($doc -match [regex]::Escape($milestone)) -Message "Solution architecture review should cover milestone $milestone."
    }
    Assert-True -Condition ($doc -match "Input-Dependent Decisions") -Message "Solution architecture review should list input-dependent decisions."
    Assert-True -Condition ($doc -match "Kilo Code's current local-model task-execution failure") -Message "Solution architecture review should track the remaining Kilo Code live-validation gap."
    Assert-True -Condition ($doc -match "Complete for positioning, partial for full cross-agent parity") -Message "Solution architecture review should classify Milestone 14 accurately."
    Assert-True -Condition ($doc -match "comparable install/configure/test support is not complete") -Message "Solution architecture review should keep Milestone 14 parity gap visible."
    Assert-True -Condition ($doc -match "Complete for Cline and Aider, partial for active tracked surfaces") -Message "Solution architecture review should classify Milestone 17 accurately."
    Assert-True -Condition ($doc -match "OpenHands do not yet have full live validation evidence") -Message "Solution architecture review should keep full surface validation gap visible."
    Assert-True -Condition ($doc -match "Complete for Continue and Aider, partial for cross-agent parity") -Message "Solution architecture review should classify Milestone 19 accurately."
    Assert-True -Condition ($doc -match "install/configure/test script parity is still missing") -Message "Solution architecture review should keep remaining surface install/configure gaps visible."
    Assert-True -Condition ($doc -match "EMPTY_MODEL_OUTPUT") -Message "Solution architecture review should track language validation failure signals."
    Assert-True -Condition ($uiDoc -match "Evidence States") -Message "Unified UI design should define evidence states."
    foreach ($state in @("tested-passed", "tested-partial", "failed", "recommended-only", "blocked")) {
        Assert-True -Condition ($uiDoc -match [regex]::Escape($state)) -Message "Unified UI design should include evidence state $state."
    }
    Assert-True -Condition ($uiDoc -match "config/workflows\.json") -Message "Unified UI design should use workflow registry as source of truth."
    Assert-True -Condition ($uiDoc -match "scripts/invoke-workflow") -Message "Unified UI design should use workflow dispatcher boundary."
    Assert-True -Condition ($uiDoc -match "local-first") -Message "Unified UI design should preserve local-first boundary."
    Assert-True -Condition ($readme -match "docs/solution-architecture-review\.md") -Message "README should link solution architecture review."
    Assert-True -Condition ($readme -match "docs/unified-starter-toolkit-ui\.md") -Message "README should link unified UI design."
    Assert-True -Condition ($todo -match "Solution Architecture Review Backlog") -Message "TODO should include solution architecture backlog."
    Assert-True -Condition ($todo -match "\[x\] Add a milestone solution completeness audit") -Message "TODO should mark solution audit doc complete."
    Assert-True -Condition ($todo -match "\[ \] Provide or approve suitable non-generated repositories") -Message "TODO should track input-needed real repository targets."
    Assert-True -Condition ($todo -match "\[ \] Resolve Kilo Code's current local-model task-execution failure") -Message "TODO should track the remaining Kilo Code live-validation gap."
    Assert-True -Condition ($todo -match "\[x\] Design a unified web UI") -Message "TODO should mark unified UI design complete."
    Assert-True -Condition ($todo -match "\[x\] Keep the UI evidence-first") -Message "TODO should mark evidence-first UI design complete."
    Assert-True -Condition ($todo -match "\[ \] Add the unified web UI wrapper only after evidence v2, project-profile activation, lane scoring, one non-Continue adapter, and workflow envelopes are validated") -Message "TODO should keep UI implementation pending."
    Assert-True -Condition ($todo -match "\[ \] Confirm scope and priority for the unified starter-toolkit web UI") -Message "TODO should track UI scope input."
}
Invoke-PackTest "sample scenario packs reference existing assets" {
    $scenarioPath = Join-Path $repoRoot "config/sample-scenario-packs.json"
    $registryPath = Join-Path $repoRoot "config/workflows.json"
    $docPath = Join-Path $repoRoot "docs/sample-scenario-packs.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $todoPath = Join-Path $repoRoot "TODO.md"

    Assert-True -Condition (Test-Path -LiteralPath $scenarioPath) -Message "Sample scenario pack catalog should exist."
    Assert-True -Condition (Test-Path -LiteralPath $docPath) -Message "Sample scenario pack docs should exist."

    $catalog = Get-Content -LiteralPath $scenarioPath -Raw | ConvertFrom-Json
    $registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
    $doc = Get-Content -LiteralPath $docPath -Raw
    $readme = Get-Content -LiteralPath $readmePath -Raw
    $todo = Get-Content -LiteralPath $todoPath -Raw

    $workflowIds = @{}
    foreach ($workflow in $registry.workflows) {
        $workflowIds[$workflow.id] = $true
    }

    Assert-Equal -Actual $catalog.schemaVersion -Expected 1 -Message "Sample scenario pack schema version should be stable."
    foreach ($requiredScenario in @("legacy-migration", "config-refactoring", "bug-fixing", "security-review", "test-generation", "documentation-cleanup")) {
        Assert-True -Condition (@($catalog.scenarios | Where-Object { $_.id -eq $requiredScenario }).Count -eq 1) -Message "Scenario catalog should include $requiredScenario."
    }

    foreach ($scenario in @($catalog.scenarios)) {
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($scenario.title)) -Message "Scenario should include title: $($scenario.id)"
        Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($scenario.goal)) -Message "Scenario should include goal: $($scenario.id)"
        Assert-True -Condition ($scenario.recommendedPrompts.Count -gt 0) -Message "Scenario should list prompts: $($scenario.id)"
        Assert-True -Condition ($scenario.workflowIds.Count -gt 0) -Message "Scenario should list workflows: $($scenario.id)"
        Assert-True -Condition ($scenario.evidence.Count -gt 0) -Message "Scenario should list evidence: $($scenario.id)"

        foreach ($prompt in @($scenario.recommendedPrompts)) {
            Assert-True -Condition ($prompt -notmatch "^[A-Za-z]:|^/|\\|\.\.|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|Users|OneDrive|itama|token|secret") -Message "Scenario prompt reference should stay sanitized: $prompt"
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot ".continue/prompts/$prompt.md")) -Message "Scenario prompt should exist: $prompt"
        }

        foreach ($agent in @($scenario.recommendedAgents)) {
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot ".continue/agents/$agent.md")) -Message "Scenario agent should exist: $agent"
        }

        foreach ($workflowId in @($scenario.workflowIds)) {
            Assert-True -Condition $workflowIds.ContainsKey($workflowId) -Message "Scenario workflow should exist: $workflowId"
        }

        foreach ($evidence in @($scenario.evidence)) {
            Assert-True -Condition ($evidence -notmatch "^[A-Za-z]:|^/|\\|\.\.|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|Users|OneDrive|itama|token|secret") -Message "Scenario evidence should stay sanitized: $evidence"
            Assert-True -Condition (Test-Path -LiteralPath (Join-Path $repoRoot $evidence)) -Message "Scenario evidence should exist: $evidence"
        }
    }

    Assert-True -Condition ($doc -match "Legacy migration") -Message "Scenario docs should list legacy migration."
    Assert-True -Condition ($doc -match "approved-write status") -Message "Scenario docs should avoid promoting write readiness."
    Assert-True -Condition ($readme -match "docs/sample-scenario-packs.md") -Message "README should link scenario pack docs."
    Assert-True -Condition ($todo -match "sample scenario packs") -Message "TODO should track sample scenario packs."
}
Invoke-PackTest "release readiness gate checks core release invariants" {
    $scriptPath = Join-Path $repoRoot "scripts/test-release-readiness.ps1"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "release-readiness-test-$([guid]::NewGuid())"
    $outputPath = Join-Path $tempRoot "release-readiness.json"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

        $result = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-AllowDirty", "-SkipValidation", "-SkipTests", "-SkipPackageDryRun", "-AsJson", "-OutputPath", $outputPath)
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Release readiness gate should support non-recursive test mode."
        Assert-True -Condition (Test-Path -LiteralPath $outputPath) -Message "Release readiness gate should write JSON report."

        $report = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
        Assert-Equal -Actual $report.SchemaVersion -Expected 1 -Message "Release readiness report schema version should be stable."
        Assert-True -Condition ($report.OverallStatus -in @("pass", "warn", "skip")) -Message "Release readiness gate should not fail in skipped-command test mode."
        Assert-True -Condition (@($report.Checks | Where-Object { $_.Id -eq "workflow.registry" -and $_.Status -eq "pass" }).Count -eq 1) -Message "Release readiness gate should check workflow registry."
        Assert-True -Condition (@($report.Checks | Where-Object { $_.Id -eq "surface.parity" -and $_.Status -eq "pass" }).Count -eq 1) -Message "Release readiness gate should check surface parity."
        Assert-True -Condition (@($report.Checks | Where-Object { $_.Id -eq "validate-pack" -and $_.Status -eq "skip" }).Count -eq 1) -Message "Release readiness gate should record skipped validation."
        Assert-True -Condition ($result.Output -notmatch "192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}|token|secret") -Message "Release readiness output should stay sanitized."

        $dispatch = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "test-release-readiness", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-AllowDirty","-SkipTests"]')
        Assert-Equal -Actual $dispatch.ExitCode -Expected 0 -Message "Workflow dispatcher should resolve release readiness gate."
        Assert-True -Condition ($dispatch.Output -match "scripts/test-release-readiness\.ps1") -Message "Dispatcher should point at the release readiness script."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "model scorecard summarizes capability evidence without cross-surface inheritance" {
    $scriptPath = Join-Path $repoRoot "scripts/generate-model-scorecard.ps1"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $docPath = Join-Path $repoRoot "docs/model-scorecard.md"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "model-scorecard-test-$([guid]::NewGuid())"
    $jsonPath = Join-Path $tempRoot "scorecard.json"
    $markdownPath = Join-Path $tempRoot "scorecard.md"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

        $result = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-OutputPath", $jsonPath, "-MarkdownOutputPath", $markdownPath, "-AsJson")
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Model scorecard generation should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $jsonPath) -Message "Model scorecard should write JSON output."
        Assert-True -Condition (Test-Path -LiteralPath $markdownPath) -Message "Model scorecard should write Markdown output."

        $report = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
        $markdown = Get-Content -LiteralPath $markdownPath -Raw
        $doc = Get-Content -LiteralPath $docPath -Raw

        Assert-Equal -Actual $report.SchemaVersion -Expected 2 -Message "Model scorecard should emit capability contract v2."
        Assert-True -Condition ($report.ModelCount -ge 3) -Message "Model scorecard should include validated models."
        Assert-True -Condition ($report.CapabilityCount -gt $report.ModelCount) -Message "Scorecard should retain distinct surface and operation capabilities."
        Assert-True -Condition (@($report.Capabilities | Where-Object { $_.Model -eq "qwen3.5:9b" -and $_.Surface -eq "Continue Agent" -and $_.Operation -eq "scoped-write" -and $_.Status -eq "approved-write-ready" }).Count -eq 1) -Message "Scorecard should preserve exact qwen3.5 Continue Agent write evidence."
        Assert-True -Condition (@($report.Capabilities | Where-Object { $_.Model -eq "qwen3-coder:30b" }).Count -gt 1) -Message "Scorecard should retain qwen3-coder evidence per capability key."
        Assert-True -Condition (@($report.Capabilities | Where-Object { $_.Model -eq "N/A" -or $_.Model -eq "local-config" }).Count -eq 0) -Message "Scorecard should exclude non-model placeholders."
        Assert-True -Condition ($markdown -match "Model Scorecard") -Message "Markdown scorecard should include title."
        Assert-True -Condition ($doc -match "evidence-catalog\.tsv") -Message "Model scorecard doc should reference evidence catalog."

        $dispatch = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "generate-model-scorecard", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-AsJson"]')
        Assert-Equal -Actual $dispatch.ExitCode -Expected 0 -Message "Workflow dispatcher should resolve model scorecard."
        Assert-True -Condition ($dispatch.Output -match "scripts/generate-model-scorecard\.ps1") -Message "Dispatcher should point at the scorecard script."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "evidence dashboard summarizes catalog and surface status" {
    $scriptPath = Join-Path $repoRoot "scripts/generate-evidence-dashboard.ps1"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $docPath = Join-Path $repoRoot "docs/evidence-dashboard.md"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "evidence-dashboard-test-$([guid]::NewGuid())"
    $jsonPath = Join-Path $tempRoot "dashboard.json"
    $markdownPath = Join-Path $tempRoot "dashboard.md"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

        $result = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-OutputPath", $jsonPath, "-MarkdownOutputPath", $markdownPath, "-AsJson")
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Evidence dashboard generation should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $jsonPath) -Message "Evidence dashboard should write JSON output."
        Assert-True -Condition (Test-Path -LiteralPath $markdownPath) -Message "Evidence dashboard should write Markdown output."

        $report = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
        $markdown = Get-Content -LiteralPath $markdownPath -Raw
        $doc = Get-Content -LiteralPath $docPath -Raw

        Assert-Equal -Actual $report.SchemaVersion -Expected 2 -Message "Evidence dashboard should emit capability contract v2."
        Assert-True -Condition ($report.EvidenceCount -ge 20) -Message "Evidence dashboard should include catalog rows."
        Assert-True -Condition ($report.SurfaceCount -ge 7) -Message "Evidence dashboard should include known surfaces."
        Assert-True -Condition ($report.ModelCount -ge 3) -Message "Evidence dashboard should include validated models."
        Assert-True -Condition (@($report.StatusCounts | Where-Object { $_.Status -eq "approved-write-ready" }).Count -eq 1) -Message "Evidence dashboard should include approved-write-ready counts."
        Assert-True -Condition (@($report.StatusCounts | Where-Object { $_.Status -eq "validated-by-tests" }).Count -eq 1) -Message "Evidence dashboard should include validated-by-tests counts."
        Assert-True -Condition (@($report.OperationCounts | Where-Object { $_.Operation -eq "scoped-write" }).Count -eq 1) -Message "Evidence dashboard should summarize operation-specific evidence."
        Assert-True -Condition (@($report.ValidationModeCounts | Where-Object { $_.ValidationMode -eq "editor-agent" }).Count -eq 1) -Message "Evidence dashboard should summarize validation modes."
        Assert-True -Condition (@($report.SurfaceReadiness | Where-Object { $_.Id -eq "continue" -and $_.SupportedActivities -ge 5 }).Count -eq 1) -Message "Evidence dashboard should summarize Continue readiness."
        Assert-Equal -Actual $report.SourceSurfaceSolutions -Expected "config/agent-surface-solutions.json" -Message "Evidence dashboard should identify the surface solution catalog."
        Assert-True -Condition ($report.SurfaceSolutionCount -ge 7) -Message "Evidence dashboard should include surface solution statuses."
        Assert-True -Condition (@($report.SurfaceSolutionReadiness | Where-Object { $_.Id -eq "continue" -and $_.InstallStatus -eq "supported" -and $_.ConfigureStatus -eq "supported" -and $_.TestStatus -eq "validated" }).Count -eq 1) -Message "Evidence dashboard should summarize Continue install/configure/test status."
        Assert-True -Condition (@($report.SurfaceSolutionReadiness | Where-Object { $_.Id -eq "openhands" -and $_.InstallStatus -eq "blocked" -and $_.ConfigureStatus -eq "blocked" }).Count -eq 1) -Message "Evidence dashboard should preserve blocked surface status."
        Assert-True -Condition ($markdown -match "Evidence Dashboard") -Message "Markdown dashboard should include title."
        Assert-True -Condition ($markdown -match "Install Configure Test") -Message "Markdown dashboard should include install/configure/test status."
        Assert-True -Condition ($doc -match "agent-surface-capabilities\.json") -Message "Evidence dashboard doc should reference surface matrix."
        Assert-True -Condition ($doc -match "agent-surface-solutions\.json") -Message "Evidence dashboard doc should reference surface solution catalog."

        $dispatch = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "generate-evidence-dashboard", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-AsJson"]')
        Assert-Equal -Actual $dispatch.ExitCode -Expected 0 -Message "Workflow dispatcher should resolve evidence dashboard."
        Assert-True -Condition ($dispatch.Output -match "scripts/generate-evidence-dashboard\.ps1") -Message "Dispatcher should point at the evidence dashboard script."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "beginner setup plan maps first-run commands to workflows" {
    $scriptPath = Join-Path $repoRoot "scripts/get-beginner-setup-plan.ps1"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $docPath = Join-Path $repoRoot "docs/beginner-setup-mode.md"
    $setupPathsPath = Join-Path $repoRoot "docs/setup-paths.md"
    $readmePath = Join-Path $repoRoot "README.md"
    $todoPath = Join-Path $repoRoot "TODO.md"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "beginner-setup-test-$([guid]::NewGuid())"
    $jsonPath = Join-Path $tempRoot "beginner-plan.json"
    $markdownPath = Join-Path $tempRoot "beginner-plan.md"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

        $result = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-Platform", "windows", "-OutputPath", $jsonPath, "-MarkdownOutputPath", $markdownPath, "-AsJson")
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Beginner setup plan generation should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $jsonPath) -Message "Beginner setup plan should write JSON output."
        Assert-True -Condition (Test-Path -LiteralPath $markdownPath) -Message "Beginner setup plan should write Markdown output."

        $report = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
        $markdown = Get-Content -LiteralPath $markdownPath -Raw
        $doc = Get-Content -LiteralPath $docPath -Raw
        $setupPaths = Get-Content -LiteralPath $setupPathsPath -Raw
        $readme = Get-Content -LiteralPath $readmePath -Raw
        $todo = Get-Content -LiteralPath $todoPath -Raw

        Assert-Equal -Actual $report.SchemaVersion -Expected 1 -Message "Beginner setup plan schema version should be stable."
        Assert-Equal -Actual $report.Platform -Expected "windows" -Message "Beginner setup plan should preserve selected platform."
        Assert-True -Condition ($report.StepCount -ge 8) -Message "Beginner setup plan should include the first-run path."
        Assert-True -Condition (@($report.Steps | Where-Object { $_.WorkflowId -eq "test-local-agent-health" }).Count -eq 1) -Message "Beginner setup plan should include health check."
        Assert-True -Condition (@($report.Steps | Where-Object { $_.WorkflowId -eq "generate-evidence-dashboard" }).Count -eq 1) -Message "Beginner setup plan should include evidence dashboard."
        Assert-True -Condition (@($report.Steps | Where-Object { $_.WorkflowId -eq "apply-agent-config" -and $_.RequiresReviewBeforeApply -eq $true }).Count -eq 1) -Message "Beginner setup plan should require review before config apply."
        Assert-True -Condition ($markdown -match "Beginner Setup Plan") -Message "Beginner setup markdown should include title."
        Assert-True -Condition ($markdown -match "<your-project-path>") -Message "Beginner setup markdown should preserve target placeholder."
        Assert-True -Condition ($doc -match "RequiresReviewBeforeApply") -Message "Beginner setup docs should explain review boundary."
        Assert-True -Condition ($doc -match "docs/setup-paths.md") -Message "Beginner setup docs should link setup paths."
        Assert-True -Condition ($setupPaths -match "Beginner Path") -Message "Setup paths doc should define beginner path."
        Assert-True -Condition ($setupPaths -match "Team Or Enterprise Path") -Message "Setup paths doc should define team or enterprise path."
        Assert-True -Condition ($setupPaths -match "audit evidence") -Message "Setup paths doc should cover audit evidence."
        Assert-True -Condition ($setupPaths -match "Beginner-friendly does not mean weaker safety") -Message "Setup paths doc should preserve shared safety boundary."
        Assert-True -Condition ($readme -match "docs/setup-paths.md") -Message "README should link setup paths doc."
        Assert-True -Condition ($todo -match "\[x\] Keep beginner-friendly local setup guidance aligned with enterprise-safe review and audit guidance") -Message "TODO should mark setup path alignment complete."

        $dispatch = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "get-beginner-setup-plan", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-AsJson"]')
        Assert-Equal -Actual $dispatch.ExitCode -Expected 0 -Message "Workflow dispatcher should resolve beginner setup plan."
        Assert-True -Condition ($dispatch.Output -match "scripts/get-beginner-setup-plan\.ps1") -Message "Dispatcher should point at the beginner setup script."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "agent pack menu groups workflows by user intent" {
    $scriptPath = Join-Path $repoRoot "scripts/show-agent-pack-menu.ps1"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $docPath = Join-Path $repoRoot "docs/agent-pack-menu.md"
    $appendixPath = Join-Path $repoRoot "docs/script-reference-appendix.md"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "agent-menu-test-$([guid]::NewGuid())"
    $jsonPath = Join-Path $tempRoot "agent-menu.json"
    $markdownPath = Join-Path $tempRoot "agent-menu.md"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

        $result = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-Platform", "windows", "-OutputPath", $jsonPath, "-MarkdownOutputPath", $markdownPath, "-AsJson")
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Agent pack menu generation should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $jsonPath) -Message "Agent pack menu should write JSON output."
        Assert-True -Condition (Test-Path -LiteralPath $markdownPath) -Message "Agent pack menu should write Markdown output."

        $report = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
        $markdown = Get-Content -LiteralPath $markdownPath -Raw
        $doc = Get-Content -LiteralPath $docPath -Raw
        $appendix = Get-Content -LiteralPath $appendixPath -Raw

        Assert-Equal -Actual $report.SchemaVersion -Expected 1 -Message "Agent pack menu schema version should be stable."
        Assert-Equal -Actual $report.Platform -Expected "windows" -Message "Agent pack menu should preserve selected platform."
        Assert-True -Condition ($report.MenuItemCount -ge 7) -Message "Agent pack menu should include the core user intents."
        foreach ($requiredItem in @("first-time-setup", "health-check", "model-choice", "install-configure", "validate-model-agent", "review-evidence", "cleanup", "release-readiness")) {
            Assert-True -Condition (@($report.MenuItems | Where-Object { $_.Id -eq $requiredItem }).Count -eq 1) -Message "Agent pack menu should include $requiredItem."
        }
        Assert-True -Condition (@($report.MenuItems | Where-Object { $_.PrimaryWorkflowId -eq "get-beginner-setup-plan" -and $_.BeginnerRecommended -eq $true }).Count -eq 1) -Message "Agent pack menu should recommend the beginner setup plan."
        Assert-True -Condition (@($report.MenuItems | Where-Object { $_.PrimaryWorkflowId -eq "install-pack-assets" -and $_.Command -match "-DryRun" }).Count -eq 1) -Message "Agent pack menu should keep install/configure dry-run first."
        Assert-True -Condition ($report.SurfaceCount -ge 7) -Message "Agent pack menu should include agent surface snapshot."
        Assert-Equal -Actual $report.SourceSolutionCatalog -Expected "config/agent-surface-solutions.json" -Message "Agent pack menu should identify the solution catalog."
        Assert-True -Condition (@($report.AgentSurfaces | Where-Object { $_.Id -eq "continue" -and $_.InstallStatus -eq "supported" -and $_.ConfigureStatus -eq "supported" -and $_.TestStatus -eq "validated" -and $_.InstallSolution }).Count -eq 1) -Message "Agent pack menu should use solution catalog status for Continue."
        Assert-True -Condition (@($report.AgentSurfaces | Where-Object { $_.Id -eq "openhands" -and $_.InstallStatus -eq "blocked" -and $_.ConfigureStatus -eq "blocked" }).Count -eq 1) -Message "Agent pack menu should preserve blocked solution status."
        Assert-Equal -Actual $report.Appendix -Expected "docs/script-reference-appendix.md" -Message "Agent pack menu should point at the script appendix."
        Assert-True -Condition ($markdown -match "Agent Pack Menu") -Message "Agent pack menu markdown should include title."
        Assert-True -Condition ($markdown -match "First-Time Setup") -Message "Agent pack menu markdown should include first-time setup."
        Assert-True -Condition ($markdown -match "agent-surface-solutions\.json") -Message "Agent pack menu markdown should reference the solution catalog."
        Assert-True -Condition ($doc -match "primary human-facing navigation") -Message "Agent pack menu docs should explain the menu role."
        Assert-True -Condition ($doc -match "agent-surface-solutions\.json") -Message "Agent pack menu docs should reference the solution catalog."
        Assert-True -Condition ($appendix -match "individual script documentation") -Message "Script appendix should preserve detailed script docs."
        Assert-True -Condition ($result.Output -notmatch "192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}|Users\\|OneDrive|itama|token|secret") -Message "Agent pack menu output should stay sanitized."

        $dispatch = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "show-agent-pack-menu", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-AsJson"]')
        Assert-Equal -Actual $dispatch.ExitCode -Expected 0 -Message "Workflow dispatcher should resolve agent pack menu."
        Assert-True -Condition ($dispatch.Output -match "scripts/show-agent-pack-menu\.ps1") -Message "Dispatcher should point at the agent pack menu script."
        Assert-True -Condition ($dispatch.Output -notmatch "192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}|Users\\|OneDrive|itama|token|secret") -Message "Agent pack menu dispatcher output should stay sanitized."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "local agent health check reports setup status" {
    $scriptPath = Join-Path $repoRoot "scripts/test-local-agent-health.ps1"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "continue-health-test-$([guid]::NewGuid())"
    $outputPath = Join-Path $tempRoot "health.json"

    try {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

        $result = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-TargetRepo", $repoRoot, "-SkipOllama", "-AsJson", "-OutputPath", $outputPath)
        Assert-Equal -Actual $result.ExitCode -Expected 0 -Message "Local agent health check should succeed for a fixture repo."
        Assert-True -Condition (Test-Path -LiteralPath $outputPath) -Message "Local agent health check should write JSON report."

        $report = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
        Assert-Equal -Actual $report.SchemaVersion -Expected 1 -Message "Health report schema version should be stable."
        Assert-True -Condition ($report.OverallStatus -in @("pass", "warn", "skip")) -Message "Health report should not fail for the pack repository."
        Assert-True -Condition ($report.OllamaCheckSkipped -eq $true) -Message "Health report should record skipped Ollama check."
        Assert-True -Condition (@($report.Checks | Where-Object { $_.Id -eq "config.references" -and $_.Status -eq "pass" }).Count -eq 1) -Message "Health check should verify config references."
        Assert-True -Condition ($result.Output -notmatch "192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|Users\\|OneDrive|itama|token|secret") -Message "Health check output should stay sanitized."

        $dispatch = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "test-local-agent-health", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-SkipOllama","-AsJson"]')
        Assert-Equal -Actual $dispatch.ExitCode -Expected 0 -Message "Workflow dispatcher should resolve health check."
        Assert-True -Condition ($dispatch.Output -match "scripts/test-local-agent-health\.ps1") -Message "Dispatcher should point at the health check script."
        Assert-True -Condition ($dispatch.Output -notmatch "192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|Users\\|OneDrive|itama|token|secret") -Message "Health check dispatcher output should stay sanitized."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "local agent cleanup workflow is dry-run first" {
    $scriptPath = Join-Path $repoRoot "scripts/cleanup-local-agent-artifacts.ps1"
    $dispatcherPath = Join-Path $repoRoot "scripts/invoke-workflow.ps1"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "continue-cleanup-test-$([guid]::NewGuid())"
    $runtimeFile = Join-Path $tempRoot "runtime-validation-output/run/raw-output.md"
    $sampleFile = Join-Path $tempRoot "runtime-validation-output/sample-repositories/python-api/SAMPLE-METADATA.md"
    $backupFile = Join-Path $tempRoot ".continue.backup-20260713/config.yaml"
    $dryRunPath = Join-Path $tempRoot "cleanup-dry-run.json"
    $applyPath = Join-Path $tempRoot "cleanup-apply.json"

    try {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $runtimeFile) | Out-Null
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $sampleFile) | Out-Null
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupFile) | Out-Null
        Set-Content -LiteralPath $runtimeFile -Value "raw local output"
        Set-Content -LiteralPath $sampleFile -Value "generated sample"
        Set-Content -LiteralPath $backupFile -Value "backup"

        $dryRun = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-TargetRepo", $tempRoot, "-AsJson", "-OutputPath", $dryRunPath)
        Assert-Equal -Actual $dryRun.ExitCode -Expected 0 -Message "Cleanup dry run should succeed."
        Assert-True -Condition (Test-Path -LiteralPath $runtimeFile) -Message "Cleanup dry run should not remove runtime output."
        Assert-True -Condition (Test-Path -LiteralPath $backupFile) -Message "Cleanup dry run should not remove backups."

        $dryRunReport = Get-Content -LiteralPath $dryRunPath -Raw | ConvertFrom-Json
        Assert-Equal -Actual $dryRunReport.SchemaVersion -Expected 1 -Message "Cleanup report schema version should be stable."
        Assert-True -Condition ($dryRunReport.Applied -eq $false) -Message "Cleanup dry-run report should state it was not applied."
        Assert-True -Condition ($dryRunReport.ItemCount -ge 2) -Message "Cleanup dry run should find runtime output and backup artifacts."
        Assert-True -Condition (@($dryRunReport.Items | Where-Object { $_.Category -eq "runtime-output" }).Count -eq 1) -Message "Cleanup dry run should include runtime output."
        Assert-True -Condition (@($dryRunReport.Items | Where-Object { $_.Category -eq "backup" }).Count -eq 1) -Message "Cleanup dry run should include backup folders."

        $dispatch = Invoke-CommandCapture -FilePath $dispatcherPath -Arguments @("-WorkflowId", "cleanup-local-agent-artifacts", "-DryRun", "-Json", "-WorkflowArgumentsJson", '["-AsJson"]')
        Assert-Equal -Actual $dispatch.ExitCode -Expected 0 -Message "Workflow dispatcher should resolve cleanup workflow."
        Assert-True -Condition ($dispatch.Output -match "scripts/cleanup-local-agent-artifacts\.ps1") -Message "Dispatcher should point at the cleanup script."

        $apply = Invoke-CommandCapture -FilePath $scriptPath -Arguments @("-TargetRepo", $tempRoot, "-Apply", "-AsJson", "-OutputPath", $applyPath)
        Assert-Equal -Actual $apply.ExitCode -Expected 0 -Message "Cleanup apply should succeed for disposable temp artifacts."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $tempRoot "runtime-validation-output"))) -Message "Cleanup apply should remove runtime output."
        Assert-True -Condition (-not (Test-Path -LiteralPath (Split-Path -Parent $backupFile))) -Message "Cleanup apply should remove backup folders."

        $applyReport = Get-Content -LiteralPath $applyPath -Raw | ConvertFrom-Json
        Assert-True -Condition ($applyReport.Applied -eq $true) -Message "Cleanup apply report should state it was applied."
        Assert-True -Condition (@($applyReport.Items | Where-Object { $_.Removed -eq $true }).Count -ge 2) -Message "Cleanup apply report should mark removed items."
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Invoke-PackTest "hosted CI verifier enforces exact-SHA cross-platform completion" {
    $windowsPath = Join-Path $repoRoot "scripts/verify-hosted-ci.ps1"
    $sharedPath = Join-Path $repoRoot "scripts/verify-hosted-ci.shared.sh"
    $linuxPath = Join-Path $repoRoot "scripts/verify-hosted-ci.linux.sh"
    $macosPath = Join-Path $repoRoot "scripts/verify-hosted-ci.macos.sh"
    $docPath = Join-Path $repoRoot "docs/hosted-ci-verification.md"
    $queuePath = Join-Path $repoRoot "docs/autonomous-maintainer-queue.md"

    foreach ($path in @($windowsPath, $sharedPath, $linuxPath, $macosPath, $docPath, $queuePath)) {
        Assert-True -Condition (Test-Path -LiteralPath $path) -Message "Hosted CI verifier asset should exist: $path"
    }

    $windows = Get-Content -LiteralPath $windowsPath -Raw
    $shared = Get-Content -LiteralPath $sharedPath -Raw
    $doc = Get-Content -LiteralPath $docPath -Raw
    $queue = Get-Content -LiteralPath $queuePath -Raw

    foreach ($content in @($windows, $shared)) {
        Assert-True -Condition ($content -match "40") -Message "Verifier should require a full commit SHA."
        Assert-True -Condition ($content -match "--commit") -Message "Verifier should discover runs by commit."
        Assert-True -Condition ($content -match "headSha") -Message "Verifier should compare the hosted run SHA."
        Assert-True -Condition ($content -match "run.+watch") -Message "Verifier should wait for the hosted run."
        Assert-True -Condition ($content -match "--exit-status") -Message "Verifier should propagate hosted run failure."
        Assert-True -Condition ($content -match "--log-failed") -Message "Verifier should retrieve failed logs."
        foreach ($job in @("Windows PowerShell validation", "Linux script smoke tests", "macOS script smoke tests")) {
            Assert-True -Condition ($content -match [regex]::Escape($job)) -Message "Verifier should require hosted job: $job"
        }
        foreach ($state in @("Pushed", "CI running", "CI passed", "CI failed")) {
            Assert-True -Condition ($content -match [regex]::Escape($state)) -Message "Verifier should report state: $state"
        }
    }

    Assert-True -Condition ($doc -match "exact 40-character commit SHA") -Message "Hosted CI docs should require exact-SHA verification."
    Assert-True -Condition ($doc -match "Never reuse a successful run") -Message "Hosted CI docs should reject stale run evidence."
    Assert-True -Condition ($queue -match 'Never call a push successful before `CI passed`') -Message "Maintainer queue should forbid premature success claims."
}

if ($failed) {
    Write-Host "Test run failed. $testCount tests executed." -ForegroundColor Red
    exit 1
}

Write-Host "Test run passed. $testCount tests executed." -ForegroundColor Green
exit 0
