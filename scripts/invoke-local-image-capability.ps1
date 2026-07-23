[CmdletBinding()]
param(
    [ValidateSet("media.image.create")][string]$CapabilityId = "media.image.create",
    [Parameter(Mandatory = $true)][string]$Prompt,
    [Parameter(Mandatory = $true)][string]$Model,
    [Parameter(Mandatory = $true)][string]$SessionPath,
    [string]$ComfyUiBaseUrl = "http://127.0.0.1:8188",
    [ValidateSet("loopback", "trusted-lan", "external")][string]$EndpointTrustScope = "loopback",
    [string]$ArtifactName = "image-result.json",
    [string]$ImageName = "generated-image.png",
    [string]$NegativePrompt = "text, watermark, logo, blurry, distorted",
    [int]$Width = 1024, [int]$Height = 1024, [int]$Steps = 20, [double]$Cfg = 7.0, [long]$Seed = 424242,
    [int]$TimeoutSeconds = 300,
    [int]$MaximumImageBytes = 67108864,
    [string]$ResponseFixturePath,
    [switch]$Execute, [switch]$Apply, [switch]$AsJson
)
$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python 3 is required for local image generation." }
$arguments = @(
    (Join-Path $PSScriptRoot "invoke-local-image-capability.py"), "--repo-root", $repoRoot,
    "--capability-id", $CapabilityId, "--prompt-stdin", "--model", $Model, "--session-path", $SessionPath,
    "--comfyui-base-url", $ComfyUiBaseUrl, "--artifact-name", $ArtifactName, "--image-name", $ImageName,
    "--negative-prompt", $NegativePrompt, "--width", "$Width", "--height", "$Height", "--steps", "$Steps",
    "--cfg", "$Cfg", "--seed", "$Seed", "--timeout-seconds", "$TimeoutSeconds",
    "--endpoint-trust-scope", $EndpointTrustScope, "--maximum-image-bytes", "$MaximumImageBytes"
)
if ($ResponseFixturePath) { $arguments += @("--response-fixture-path", $ResponseFixturePath) }
if ($Execute) { $arguments += "--execute" }
if ($Apply) { $arguments += "--apply" }
if ($AsJson) { $arguments += "--json" }
$Prompt | & $python.Source @arguments
exit $LASTEXITCODE
