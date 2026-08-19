param(
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [Parameter(Mandatory = $true)]
    [string]$OllamaBaseUrl,
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if ($Model -notmatch '^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$') {
    throw "Model contains unsupported characters."
}

$uri = $null
if (-not [Uri]::TryCreate($OllamaBaseUrl, [UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -notin @("http", "https") -or $uri.UserInfo -or $uri.Query -or $uri.Fragment) {
    throw "OllamaBaseUrl must be an HTTP(S) origin without credentials, query, or fragment."
}
$origin = $uri.GetLeftPart([UriPartial]::Authority).TrimEnd("/")

if (-not $OutputPath) {
    $safeModel = $Model -replace '[^A-Za-z0-9._-]', '-'
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/continue-configs/$safeModel.yaml"
}
$resolvedParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $OutputPath))
$allowedRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "runtime-validation-output"))
if (-not $resolvedParent.StartsWith($allowedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputPath must remain under runtime-validation-output."
}

New-Item -ItemType Directory -Force -Path $resolvedParent | Out-Null
$content = @"
name: Disposable Continue coding qualification
version: 0.1.0
schema: v1

models:
  - name: Exact candidate under test
    provider: ollama
    model: $Model
    apiBase: $origin
    roles:
      - chat
      - edit
      - apply
    capabilities:
      - tool_use
    defaultCompletionOptions:
      temperature: 0
      contextLength: 32768
      maxTokens: 4096
      keepAlive: 1800

context:
  - provider: file
  - provider: code
  - provider: diff
  - provider: terminal

mcpServers: []
"@
Set-Content -LiteralPath $OutputPath -Value $content -Encoding UTF8
Write-Output ([System.IO.Path]::GetFullPath($OutputPath))
