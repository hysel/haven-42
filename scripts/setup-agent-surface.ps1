param(
    [ValidateSet("aider", "kilo", "opencode")]
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
    [string]$InstallMethod = "aider-install",
    [string]$AiderCommand = "aider",
    [string]$KiloCommand = "kilo",
    [string]$OpenCodeCommand = "opencode",
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if ($Surface -eq "kilo") {
    [Console]::Error.WriteLine("Kilo Code support is quarantined at CLI 7.4.11 after failed write and scoped-edit gates. The retained setup code and test harness are maintainer-only until a relevant upstream version or tool-protocol change passes revalidation.")
    exit 2
}

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
    if ($SurfaceName -in @("kilo", "opencode")) {
        if ($Method -ne "npm") { throw "$SurfaceName supports only the npm install method in this adapter." }
        if ($SurfaceName -eq "kilo") { return @("npm install -g @kilocode/cli") }
        return @("npm install -g opencode-ai")
    }

    switch ($Method) {
        "pipx" { return @("python -m pip install pipx", "pipx install aider-chat") }
        "uv" { return @("python -m pip install uv", "uv tool install --force --python python3.12 --with pip aider-chat@latest") }
        default { return @("python -m pip install aider-install", "aider-install") }
    }
}

$configName = switch ($Surface) { "aider" { ".aider.conf.local.yml" } "kilo" { ".kilo/kilo.jsonc" } default { ".opencode.local.json" } }
$commandName = switch ($Surface) { "aider" { $AiderCommand } "kilo" { $KiloCommand } default { $OpenCodeCommand } }
$displayName = switch ($Surface) { "aider" { "Aider" } "kilo" { "Kilo Code" } default { "OpenCode" } }
if ($Surface -in @("kilo", "opencode") -and $InstallMethod -eq "aider-install") { $InstallMethod = "npm" }

if ($Action -eq "Plan") {
    [pscustomobject]@{
        Surface = $displayName
        InstallMethod = $InstallMethod
        InstallCommands = Get-InstallPlan -SurfaceName $Surface -Method $InstallMethod
        ConfigFile = $configName
        LaunchCommand = switch ($Surface) { "aider" { "$commandName --config $configName" } "kilo" { "$commandName" } default { "`$env:OPENCODE_CONFIG='$configName'; $commandName" } }
        TestCommand = if ($Surface -eq "aider") { ".\scripts\test-aider-cli-models.ps1 -Models <model>" } elseif ($Surface -eq "kilo") { ".\scripts\test-kilo-code-cli-models.ps1 -Models <model>" } else { ".\scripts\test-opencode-cli-models.ps1 -Models <model>" }
        Safety = "Generated config is local-only and must not be committed."
    } | ConvertTo-Json -Depth 5
    exit 0
}

if ($Action -eq "Install") {
    $commands = Get-InstallPlan -SurfaceName $Surface -Method $InstallMethod
    foreach ($command in $commands) { Write-Host "$displayName install step: $command" }
    if ($DryRun) { Write-Host "Dry run complete; no network install was executed."; exit 0 }
    if ($Surface -in @("kilo", "opencode")) {
        $package = if ($Surface -eq "kilo") { "@kilocode/cli" } else { "opencode-ai" }
        & npm install -g $package
    } elseif ($InstallMethod -eq "pipx") {
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
    Write-Host "$displayName installation completed. Run this script with -Action Health next."
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
    } elseif ($Surface -eq "kilo") {
        $kiloEndpoint = if ($endpoint.EndsWith("/v1")) { $endpoint } else { "$endpoint/v1" }
        $content = @{
            '$schema' = "https://app.kilo.ai/config.json"
            model = "ollama/$selectedModel"
            provider = @{
                ollama = @{
                    options = @{ baseURL = $kiloEndpoint; timeout = 600000 }
                    models = @{
                        $selectedModel = @{
                            name = "$selectedModel (local)"
                            tool_call = $true
                            limit = @{ context = 32768; output = 8192 }
                        }
                    }
                }
            }
            permission = @{ '*' = "ask"; bash = "ask"; edit = "ask" }
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
        $excludeEntry = if ($Surface -eq "kilo") { ".kilo/" } else { $configName }
        if ($excludeEntry -notin $exclude) { Add-Content -LiteralPath $excludePath -Value $excludeEntry }
    }
    if ($Surface -eq "aider") {
        Write-Host "Aider config written. Launch with: $AiderCommand --config $configName"
    } elseif ($Surface -eq "kilo") {
        Write-Host "Kilo Code config written. Launch from the repository root with: $KiloCommand"
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
    } elseif ($Surface -eq "kilo") {
        try {
            $kiloConfig = $configText | ConvertFrom-Json
            $hasModel = $kiloConfig.model -match '^ollama/' -and $null -ne $kiloConfig.provider.ollama
            $safePermissions = $kiloConfig.permission.'*' -eq "ask" -and $kiloConfig.permission.edit -eq "ask"
            $checks.Add([pscustomobject]@{ Name = "ollama-model"; Status = if ($hasModel) { "pass" } else { "fail" }; Detail = "Ollama provider and model configured" })
            $checks.Add([pscustomobject]@{ Name = "safe-permissions"; Status = if ($safePermissions) { "pass" } else { "fail" }; Detail = "default and edit permissions require approval" })
        } catch {
            $checks.Add([pscustomobject]@{ Name = "ollama-model"; Status = "fail"; Detail = "Kilo config is not valid JSON" })
        }
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
[pscustomobject]@{ Surface = $displayName; Status = $status; Checks = @($checks); NextCommand = switch ($Surface) { "aider" { "$AiderCommand --config $configName --version" } "kilo" { "$KiloCommand --version" } default { "`$env:OPENCODE_CONFIG='$configName'; $OpenCodeCommand --version" } } } | ConvertTo-Json -Depth 5
if ($status -ne "healthy") { exit 1 }
