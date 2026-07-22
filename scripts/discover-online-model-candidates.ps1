param(
    [string[]]$Sources,
    [Alias("Queries")]
    [string[]]$Families,
    [string]$SourceBaseUrl,
    [string]$HuggingFaceBaseUrl,
    [string]$SourceHtmlPath,
    [string]$HuggingFaceJsonPath,
    [string]$OutputPath,
    [string]$ModelProfilePath,
    [ValidateSet("TotalDedicated", "MaxDedicated")]
    [string]$VramSelectionMode = "TotalDedicated",
    [double]$AvailableVramGb = 0,
    [switch]$IncludeOversizedModels,
    [int]$MaxResultsPerQuery = 10,
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputPath) {
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/online-model-candidates-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
}

$python = Get-Command python -ErrorAction SilentlyContinue
$pythonPath = if ($python) { $python.Source } elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { throw "Python 3 is required for provider-neutral model discovery." }
$pythonPrefixArguments = if ($python) { @() } else { @("-3") }
$arguments = @(
    (Join-Path $PSScriptRoot "discover-online-model-candidates.py"),
    "--source-config", (Join-Path $repoRoot "config/model-discovery-sources.json"),
    "--contract-path", (Join-Path $repoRoot "config/model-discovery-contract.json"),
    "--output-path", $OutputPath,
    "--vram-selection-mode", $VramSelectionMode,
    "--available-vram-gb", ([string]::Format([Globalization.CultureInfo]::InvariantCulture, "{0}", $AvailableVramGb)),
    "--max-results-per-query", $MaxResultsPerQuery,
    "--timeout-seconds", $TimeoutSeconds
)
foreach ($value in $Sources) { $arguments += @("--sources", $value) }
foreach ($value in $Families) { $arguments += @("--families", $value) }
if ($SourceBaseUrl) { $arguments += @("--ollama-base-url", $SourceBaseUrl) }
if ($HuggingFaceBaseUrl) { $arguments += @("--hugging-face-base-url", $HuggingFaceBaseUrl) }
if ($SourceHtmlPath) { $arguments += @("--ollama-html-fixture", $SourceHtmlPath) }
if ($HuggingFaceJsonPath) { $arguments += @("--huggingface-json-fixture", $HuggingFaceJsonPath) }
if ($ModelProfilePath) { $arguments += @("--model-profile-path", $ModelProfilePath) }
if ($IncludeOversizedModels) { $arguments += "--include-oversized-models" }

# The report contract fixes PullsModels and RewritesContinueConfig to false.
& $pythonPath @pythonPrefixArguments @arguments
exit $LASTEXITCODE
