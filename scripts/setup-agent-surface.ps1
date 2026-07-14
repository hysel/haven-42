param(
    [ValidateSet("aider")]
    [string]$Surface = "aider",
    [ValidateSet("Plan", "Install", "Configure", "Health")]
    [string]$Action = "Plan",
    [string]$TargetRepo,
    [string]$Model,
    [string]$RecommendationPath,
    [ValidateSet("WriteSafe", "PlanOnly", "DeepReview")]
    [string]$Lane = "WriteSafe",
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [ValidateSet("aider-install", "pipx", "uv")]
    [string]$InstallMethod = "aider-install",
    [string]$AiderCommand = "aider",
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Resolve-AdapterModel {
    if ($Model) { return $Model }
    if (-not $RecommendationPath) { throw "Model or RecommendationPath is required for Configure." }
    if (-not (Test-Path -LiteralPath $RecommendationPath)) { throw "RecommendationPath does not exist: $RecommendationPath" }
    $recommendation = Get-Content -LiteralPath $RecommendationPath -Raw | ConvertFrom-Json
    $property = "${Lane}Model"
    $selected = $recommendation.Recommendation.$property
    if ([string]::IsNullOrWhiteSpace([string]$selected)) { throw "Recommendation does not contain a model for lane $Lane." }
    return [string]$selected
}

function Assert-SafeModelName([string]$Value) {
    if ($Value -notmatch '^[A-Za-z0-9._:/-]+$') { throw "Model contains unsupported characters." }
}

function Get-SafeEndpoint([string]$Value) {
    $uri = $null
    if (-not [uri]::TryCreate($Value, [System.UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -notin @("http", "https") -or $uri.UserInfo -or $uri.Query -or $uri.Fragment) {
        throw "OllamaBaseUrl must be an absolute HTTP(S) URL without credentials, query, or fragment."
    }
    return $uri.AbsoluteUri.TrimEnd('/')
}

function Get-InstallPlan([string]$Method) {
    switch ($Method) {
        "pipx" { return @("python -m pip install pipx", "pipx install aider-chat") }
        "uv" { return @("python -m pip install uv", "uv tool install --force --python python3.12 --with pip aider-chat@latest") }
        default { return @("python -m pip install aider-install", "aider-install") }
    }
}

if ($Surface -ne "aider") { throw "Unsupported surface: $Surface" }
$configName = ".aider.conf.local.yml"

if ($Action -eq "Plan") {
    [pscustomobject]@{
        Surface = "Aider"
        InstallMethod = $InstallMethod
        InstallCommands = Get-InstallPlan -Method $InstallMethod
        ConfigFile = $configName
        LaunchCommand = "$AiderCommand --config $configName"
        TestCommand = ".\scripts\test-aider-cli-models.ps1 -Models <model>"
        Safety = "Generated config is local-only and must not be committed."
    } | ConvertTo-Json -Depth 5
    exit 0
}

if ($Action -eq "Install") {
    $commands = Get-InstallPlan -Method $InstallMethod
    foreach ($command in $commands) { Write-Host "Aider install step: $command" }
    if ($DryRun) { Write-Host "Dry run complete; no network install was executed."; exit 0 }
    if ($InstallMethod -eq "pipx") {
        & python -m pip install pipx
        if ($LASTEXITCODE -ne 0) { throw "pipx bootstrap failed." }
        & pipx install aider-chat
    } elseif ($InstallMethod -eq "uv") {
        & python -m pip install uv
        if ($LASTEXITCODE -ne 0) { throw "uv bootstrap failed." }
        & uv tool install --force --python python3.12 --with pip aider-chat@latest
    } else {
        & python -m pip install aider-install
        if ($LASTEXITCODE -ne 0) { throw "aider-install bootstrap failed." }
        & aider-install
    }
    if ($LASTEXITCODE -ne 0) { throw "Aider installation failed." }
    Write-Host "Aider installation completed. Run this script with -Action Health next."
    exit 0
}

if (-not $TargetRepo) { throw "TargetRepo is required for $Action." }
$resolvedTarget = (Resolve-Path -LiteralPath $TargetRepo).Path
$configPath = Join-Path $resolvedTarget $configName

if ($Action -eq "Configure") {
    $selectedModel = Resolve-AdapterModel
    Assert-SafeModelName -Value $selectedModel
    $endpoint = Get-SafeEndpoint -Value $OllamaBaseUrl
    $content = @(
        "# Generated local-only Aider config. Do not commit this file."
        "model: ollama_chat/$selectedModel"
        "set-env:"
        "  - OLLAMA_API_BASE=$endpoint"
        "auto-commits: false"
        "dirty-commits: false"
        "gitignore: false"
        "check-update: false"
        "analytics-disable: true"
        "map-tokens: 0"
        "line-endings: platform"
    ) -join [Environment]::NewLine
    if ((Test-Path -LiteralPath $configPath) -and -not $Force) { throw "$configName already exists. Use -Force to replace it." }
    Write-Host "Aider config target: $configPath"
    Write-Host "Selected lane/model: $Lane / $selectedModel"
    if ($DryRun) { Write-Host "Dry run complete; no config was written."; exit 0 }
    Set-Content -LiteralPath $configPath -Value $content -NoNewline
    if (Test-Path -LiteralPath (Join-Path $resolvedTarget ".git")) {
        $excludePath = Join-Path $resolvedTarget ".git/info/exclude"
        $exclude = if (Test-Path -LiteralPath $excludePath) { @(Get-Content -LiteralPath $excludePath) } else { @() }
        if ($configName -notin $exclude) { Add-Content -LiteralPath $excludePath -Value $configName }
    }
    Write-Host "Aider config written. Launch with: $AiderCommand --config $configName"
    exit 0
}

$checks = [System.Collections.Generic.List[object]]::new()
$aider = Get-Command $AiderCommand -ErrorAction SilentlyContinue
$checks.Add([pscustomobject]@{ Name = "aider-command"; Status = if ($aider) { "pass" } else { "fail" }; Detail = if ($aider) { "$AiderCommand is available" } else { "$AiderCommand was not found on PATH" } })
$checks.Add([pscustomobject]@{ Name = "local-config"; Status = if (Test-Path -LiteralPath $configPath) { "pass" } else { "fail" }; Detail = $configName })
if (Test-Path -LiteralPath $configPath) {
    $configText = Get-Content -LiteralPath $configPath -Raw
    $checks.Add([pscustomobject]@{ Name = "ollama-model"; Status = if ($configText -match '(?m)^model: ollama_chat/') { "pass" } else { "fail" }; Detail = "ollama_chat model configured" })
    $checks.Add([pscustomobject]@{ Name = "safe-git-mode"; Status = if ($configText -match '(?m)^auto-commits: false\r?$' -and $configText -match '(?m)^dirty-commits: false\r?$') { "pass" } else { "fail" }; Detail = "automatic commits disabled" })
}
$status = if (@($checks | Where-Object Status -eq "fail").Count -eq 0) { "healthy" } else { "attention-required" }
[pscustomobject]@{ Surface = "Aider"; Status = $status; Checks = @($checks); NextCommand = "$AiderCommand --config $configName --version" } | ConvertTo-Json -Depth 5
if ($status -ne "healthy") { exit 1 }
