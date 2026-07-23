param(
    [ValidateSet("aider", "opencode")]
    [string]$Surface = "aider",
    [ValidateSet("Plan", "Install", "Configure", "Health")]
    [string]$Action = "Plan",
    [string]$TargetRepo,
    [string]$Model,
    [string]$RecommendationPath,
    [ValidateSet("WriteSafe", "PlanOnly", "DeepReview")]
    [string]$Lane = "WriteSafe",
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [ValidateSet("aider-install", "pipx", "uv", "npm")]
    [string]$InstallMethod = "pipx",
    [string]$AiderCommand = "aider",
    [string]$OpenCodeCommand = "opencode",
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

function Get-InstallPlan([string]$SurfaceName, [string]$Method) {
    if ($SurfaceName -eq "opencode") {
        if ($Method -ne "npm") { throw "$SurfaceName supports only the npm install method in this adapter." }
        return @("user-managed exact install required: opencode-ai@1.18.2")
    }

    switch ($Method) {
        "pipx" { return @("user-managed pipx required", "user-managed exact install required: aider-chat==0.86.2") }
        "uv" { return @("user-managed uv required", "user-managed exact install required: aider-chat==0.86.2") }
        default { return @("aider-install bootstrap is blocked because it does not provide an admitted immutable dependency closure") }
    }
}

$configName = if ($Surface -eq "aider") { ".aider.conf.local.yml" } else { ".opencode.local.json" }
$commandName = if ($Surface -eq "aider") { $AiderCommand } else { $OpenCodeCommand }
$displayName = if ($Surface -eq "aider") { "Aider" } else { "OpenCode" }
if ($Surface -eq "opencode" -and -not $PSBoundParameters.ContainsKey("InstallMethod")) { $InstallMethod = "npm" }
if ($Surface -eq "opencode" -and $InstallMethod -eq "aider-install") { $InstallMethod = "npm" }

if ($Action -eq "Plan") {
    [pscustomobject]@{
        Surface = $displayName
        InstallMethod = $InstallMethod
        InstallCommands = Get-InstallPlan -SurfaceName $Surface -Method $InstallMethod
        ConfigFile = $configName
        LaunchCommand = if ($Surface -eq "aider") { "$commandName --config $configName" } else { "`$env:OPENCODE_CONFIG='$configName'; $commandName" }
        TestCommand = if ($Surface -eq "aider") { ".\scripts\test-aider-cli-models.ps1 -Models <model>" } else { ".\scripts\test-opencode-cli-models.ps1 -Models <model>" }
        Safety = "Generated config is local-only and must not be committed."
    } | ConvertTo-Json -Depth 5
    exit 0
}

if ($Action -eq "Install") {
    $commands = Get-InstallPlan -SurfaceName $Surface -Method $InstallMethod
    foreach ($command in $commands) { Write-Host "$displayName install step: $command" }
    throw "Automated third-party installation is blocked until an immutable reviewed dependency manifest and verified artifacts are admitted."
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
    if ($Surface -eq "opencode") {
        $openCodeEndpoint = if ($endpoint.EndsWith("/v1")) { $endpoint } else { "$endpoint/v1" }
        $content = @{
            '$schema' = "https://opencode.ai/config.json"
            model = "ollama/$selectedModel"
            provider = @{
                ollama = @{
                    npm = "@ai-sdk/openai-compatible"
                    name = "Ollama (local)"
                    options = @{ baseURL = $openCodeEndpoint }
                    models = @{ $selectedModel = @{ name = "$selectedModel (local)" } }
                }
            }
        } | ConvertTo-Json -Depth 10
    }
    if ((Test-Path -LiteralPath $configPath) -and -not $Force) { throw "$configName already exists. Use -Force to replace it." }
    Write-Host "$displayName config target: $configPath"
    Write-Host "Selected lane/model: $Lane / $selectedModel"
    if ($DryRun) { Write-Host "Dry run complete; no config was written."; exit 0 }
    $configParent = Split-Path -Parent $configPath
    if ($configParent) { New-Item -ItemType Directory -Force -Path $configParent | Out-Null }
    Set-Content -LiteralPath $configPath -Value $content -NoNewline
    if (Test-Path -LiteralPath (Join-Path $resolvedTarget ".git")) {
        $excludePath = Join-Path $resolvedTarget ".git/info/exclude"
        $exclude = if (Test-Path -LiteralPath $excludePath) { @(Get-Content -LiteralPath $excludePath) } else { @() }
        if ($configName -notin $exclude) { Add-Content -LiteralPath $excludePath -Value $configName }
    }
    if ($Surface -eq "aider") {
        Write-Host "Aider config written. Launch with: $AiderCommand --config $configName"
    } else {
        Write-Host "OpenCode config written. Launch with: `$env:OPENCODE_CONFIG='$configName'; $OpenCodeCommand"
    }
    exit 0
}

$checks = [System.Collections.Generic.List[object]]::new()
$agentCommand = Get-Command $commandName -ErrorAction SilentlyContinue
$checks.Add([pscustomobject]@{ Name = "$Surface-command"; Status = if ($agentCommand) { "pass" } else { "fail" }; Detail = if ($agentCommand) { "$commandName is available" } else { "$commandName was not found on PATH" } })
$checks.Add([pscustomobject]@{ Name = "local-config"; Status = if (Test-Path -LiteralPath $configPath) { "pass" } else { "fail" }; Detail = $configName })
if (Test-Path -LiteralPath $configPath) {
    $configText = Get-Content -LiteralPath $configPath -Raw
    if ($Surface -eq "aider") {
        $checks.Add([pscustomobject]@{ Name = "ollama-model"; Status = if ($configText -match '(?m)^model: ollama_chat/') { "pass" } else { "fail" }; Detail = "ollama_chat model configured" })
        $checks.Add([pscustomobject]@{ Name = "safe-git-mode"; Status = if ($configText -match '(?m)^auto-commits: false\r?$' -and $configText -match '(?m)^dirty-commits: false\r?$') { "pass" } else { "fail" }; Detail = "automatic commits disabled" })
    } else {
        try {
            $openCodeConfig = $configText | ConvertFrom-Json
            $hasModel = $openCodeConfig.model -match '^ollama/' -and $null -ne $openCodeConfig.provider.ollama
            $checks.Add([pscustomobject]@{ Name = "ollama-model"; Status = if ($hasModel) { "pass" } else { "fail" }; Detail = "Ollama provider and model configured" })
        } catch {
            $checks.Add([pscustomobject]@{ Name = "ollama-model"; Status = "fail"; Detail = "OpenCode config is not valid JSON" })
        }
    }
}
$status = if (@($checks | Where-Object Status -eq "fail").Count -eq 0) { "healthy" } else { "attention-required" }
[pscustomobject]@{ Surface = $displayName; Status = $status; Checks = @($checks); NextCommand = if ($Surface -eq "aider") { "$AiderCommand --config $configName --version" } else { "`$env:OPENCODE_CONFIG='$configName'; $OpenCodeCommand --version" } } | ConvertTo-Json -Depth 5
if ($status -ne "healthy") { exit 1 }
