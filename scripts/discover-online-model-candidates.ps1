param(
    [string[]]$Families = @(
        "qwen3.5",
        "qwen3-coder",
        "devstral",
        "devstral-small",
        "codestral",
        "gpt-oss",
        "glm"
    ),
    [string]$SourceBaseUrl = "https://ollama.com/library",
    [string]$SourceHtmlPath,
    [string]$OutputPath,
    [string]$ModelProfilePath,
    [ValidateSet("TotalDedicated", "MaxDedicated")]
    [string]$VramSelectionMode = "TotalDedicated",
    [double]$AvailableVramGb = 0,
    [switch]$IncludeOversizedModels,
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $OutputPath) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $repoRoot "runtime-validation-output/online-model-candidates-$timestamp.json"
}

function ConvertTo-SafeSourceBaseUrl {
    param([string]$Value)

    return $Value.TrimEnd("/")
}

function Get-SourceContent {
    param([string]$Family)

    if ($SourceHtmlPath) {
        if (-not (Test-Path -LiteralPath $SourceHtmlPath)) {
            throw "SourceHtmlPath does not exist: $SourceHtmlPath"
        }

        return [pscustomobject]@{
            Source = "local-html-fixture"
            Url = "redacted"
            Content = Get-Content -LiteralPath $SourceHtmlPath -Raw
        }
    }

    $safeBase = ConvertTo-SafeSourceBaseUrl $SourceBaseUrl
    $url = "$safeBase/$Family"
    $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec $TimeoutSeconds -UseBasicParsing

    return [pscustomobject]@{
        Source = "ollama-library-page"
        Url = $url
        Content = [string]$response.Content
    }
}

function Get-ModelTagsFromContent {
    param(
        [string]$Content,
        [string]$Family
    )

    $candidates = [System.Collections.Generic.List[string]]::new()
    $escapedFamily = [regex]::Escape($Family)
    $patterns = @(
        "(?i)\b$escapedFamily[:][a-z0-9][a-z0-9._-]*\b",
        "(?i)/library/($escapedFamily[:][a-z0-9][a-z0-9._-]*)",
        "(?i)\b([a-z0-9][a-z0-9._/-]*$escapedFamily[a-z0-9._/-]*:[a-z0-9][a-z0-9._-]*)\b"
    )

    foreach ($pattern in $patterns) {
        foreach ($match in [regex]::Matches($Content, $pattern)) {
            $value = if ($match.Groups.Count -gt 1 -and $match.Groups[1].Value) {
                $match.Groups[1].Value
            } else {
                $match.Value
            }

            $value = $value.Trim().Trim('"', "'", '<', '>', ',', '.', ';', ')', '(')
            if ($value.StartsWith("/library/")) {
                $value = $value.Substring(9)
            }
            if ($value.StartsWith("library/")) {
                $value = $value.Substring(8)
            }

            if ($value -match "^[A-Za-z0-9][A-Za-z0-9._/-]*:[A-Za-z0-9][A-Za-z0-9._-]*$") {
                $candidates.Add($value)
            }
        }
    }

    return $candidates | Select-Object -Unique
}


function Get-ModelSizeBillion {
    param([string]$Model)

    $match = [regex]::Match($Model, '(?i)(\d+(?:\.\d+)?)b')
    if (-not $match.Success) {
        return 0
    }

    return [double]::Parse($match.Groups[1].Value, [System.Globalization.CultureInfo]::InvariantCulture)
}

function Get-RecommendedMinVramGb {
    param([string]$Model)

    if ($Model -match '(?i)(cloud|-mlx)') {
        return 999999
    }

    $size = Get-ModelSizeBillion -Model $Model
    if ($size -le 0) { return 0 }
    if ($size -le 1) { return 4 }
    if ($size -le 2) { return 6 }
    if ($size -le 4) { return 8 }
    if ($size -le 9) { return 12 }
    if ($size -le 14) { return 20 }
    if ($size -le 27) { return 36 }
    if ($size -le 35) { return 48 }
    if ($size -le 80) { return 80 }
    if ($size -le 122) { return 128 }

    return 512
}

function Get-CurrentPlatformName {
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::OSX)) {
        return "macOS"
    }
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Linux)) {
        return "Linux"
    }
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)) {
        return "Windows"
    }

    return "Unknown"
}

function Get-ModelHostPlatform {
    param([string]$Path)

    if (-not [string]::IsNullOrWhiteSpace($Path) -and (Test-Path -LiteralPath $Path)) {
        try {
            $profile = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
            if ($profile.Platform) {
                return [string]$profile.Platform
            }
        }
        catch {
            return Get-CurrentPlatformName
        }
    }

    return Get-CurrentPlatformName
}

function Get-NormalizedPlatformName {
    param([string]$Platform)

    if ($Platform -match '(?i)mac|darwin') { return "macOS" }
    if ($Platform -match '(?i)linux') { return "Linux" }
    if ($Platform -match '(?i)windows') { return "Windows" }
    return "Unknown"
}

function Get-AvailableVramFromProfile {
    param(
        [string]$Path,
        [string]$SelectionMode
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "ModelProfilePath does not exist: $Path"
    }

    $profile = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    $values = @()

    foreach ($gpu in @($profile.Gpus)) {
        if ($null -eq $gpu -or $null -eq $gpu.VramGb) {
            continue
        }

        $memoryType = [string]$gpu.MemoryType
        if ($memoryType -and $memoryType -notmatch '(?i)dedicated|unknown') {
            continue
        }

        try {
            $value = [double]::Parse([string]$gpu.VramGb, [System.Globalization.CultureInfo]::InvariantCulture)
            if ($value -gt 0) {
                $values += $value
            }
        }
        catch {
            continue
        }
    }

    if ($values.Count -eq 0) {
        return $null
    }

    if ($SelectionMode -eq "MaxDedicated") {
        return [math]::Round(($values | Measure-Object -Maximum).Maximum, 2)
    }

    return [math]::Round(($values | Measure-Object -Sum).Sum, 2)
}

function Get-VramRecommendation {
    param([string]$Model)

    $recommendedMinVramGb = Get-RecommendedMinVramGb -Model $Model
    $fitsAvailableVram = $true
    if ($effectiveAvailableVramGb -gt 0 -and $recommendedMinVramGb -gt 0) {
        $fitsAvailableVram = ($recommendedMinVramGb -le $effectiveAvailableVramGb)
    }

    return [pscustomobject]@{
        AvailableVramGb = if ($effectiveAvailableVramGb -gt 0) { $effectiveAvailableVramGb } else { $null }
        AvailableVramSource = $vramSource
        RecommendedMinVramGb = if ($recommendedMinVramGb -gt 0 -and $recommendedMinVramGb -lt 999999) { $recommendedMinVramGb } else { $null }
        FitsAvailableVram = [bool]$fitsAvailableVram
    }
}
function Get-ModelPullEligibility {
    param(
        [string]$Model,
        [string]$Platform
    )

    $normalizedPlatform = Get-NormalizedPlatformName -Platform $Platform
    if ($Model -match '(?i)cloud') {
        return [pscustomobject]@{
            Pullable = $false
            Reason = "Cloud catalog tag; local Ollama pull is not supported."
            FailureSignal = "MODEL_SKIPPED_FOR_PLATFORM"
        }
    }

    if ($Model -match '(?i)-mlx($|[-_:])' -and $normalizedPlatform -ne "macOS") {
        return [pscustomobject]@{
            Pullable = $false
            Reason = "MLX model tag requires a macOS Apple Silicon model host."
            FailureSignal = "MODEL_SKIPPED_FOR_PLATFORM"
        }
    }

    return [pscustomobject]@{
        Pullable = $true
        Reason = "Model tag is pullable for this host platform."
        FailureSignal = "none"
    }
}

function Get-CandidateReason {
    param([string]$Model)

    if ($Model -match "(?i)(coder|code|codestral|devstral)") {
        return "Coding-oriented model name discovered online. Requires local tool validation."
    }

    if ($Model -match "(?i)(qwen|glm|gpt-oss)") {
        return "General model family with prior local-agent interest. Requires local tool validation."
    }

    return "Discovered online candidate. Requires local validation before use."
}

$effectiveAvailableVramGb = $AvailableVramGb
$vramSource = if ($effectiveAvailableVramGb -gt 0) { "explicit" } else { $null }

if ($effectiveAvailableVramGb -le 0 -and $ModelProfilePath) {
    Write-Host "Reading VRAM from model profile using $VramSelectionMode mode. The profile is local-only and is not sent online."
    $profileVram = Get-AvailableVramFromProfile -Path $ModelProfilePath -SelectionMode $VramSelectionMode
    if ($null -ne $profileVram -and $profileVram -gt 0) {
        $effectiveAvailableVramGb = $profileVram
        $vramSource = "model-profile:$VramSelectionMode"
    }
}

if ($effectiveAvailableVramGb -gt 0) {
    Write-Host "Using local VRAM estimate: $effectiveAvailableVramGb GB ($vramSource)."
}
$modelHostPlatform = Get-ModelHostPlatform -Path $ModelProfilePath
Write-Host "Model host platform: $modelHostPlatform"

$results = [System.Collections.Generic.List[object]]::new()
$skippedResults = [System.Collections.Generic.List[object]]::new()
$errors = [System.Collections.Generic.List[object]]::new()

$familiesToCheck = [System.Collections.Generic.List[string]]::new()
foreach ($entry in $Families) {
    if ([string]::IsNullOrWhiteSpace($entry)) {
        continue
    }

    foreach ($familyPart in ($entry -split ",")) {
        if (-not [string]::IsNullOrWhiteSpace($familyPart)) {
            $familiesToCheck.Add($familyPart.Trim())
        }
    }
}

$uniqueFamilies = @($familiesToCheck | Select-Object -Unique)
Write-Host "Discovery families: $($uniqueFamilies -join ', ')"
Write-Host "Source mode: $(if ($SourceHtmlPath) { 'local HTML fixture' } else { 'online Ollama library pages' })"
foreach ($family in $uniqueFamilies) {
    $family = $family.Trim()
    Write-Host "Checking family: $family"

    try {
        $source = Get-SourceContent -Family $family
        $modelTags = @(Get-ModelTagsFromContent -Content $source.Content -Family $family)
        Write-Host "Found $($modelTags.Count) candidate tag(s) for family: $family"
        if ($modelTags.Count -eq 0) {
            Write-Host "No candidates found for family: $family"
        }

        foreach ($modelTag in $modelTags) {
            $pullEligibility = Get-ModelPullEligibility -Model $modelTag -Platform $modelHostPlatform
            if (-not $pullEligibility.Pullable) {
                Write-Host "Skipped candidate: $modelTag ($($pullEligibility.Reason))"
                $skippedResults.Add([pscustomobject]@{
                    Model = $modelTag
                    Family = $family
                    Source = $source.Source
                    Status = "online candidate skipped for platform"
                    Reason = $pullEligibility.Reason
                    NextStep = "Do not pull this tag for the detected model host platform."
                    FailureSignal = $pullEligibility.FailureSignal
                    ModelHostPlatform = $modelHostPlatform
                })
                continue
            }

            $vramRecommendation = Get-VramRecommendation -Model $modelTag
            $status = if ($vramRecommendation.FitsAvailableVram -or $IncludeOversizedModels) { "online candidate" } else { "online candidate above vram estimate" }
            $nextStep = if ($vramRecommendation.FitsAvailableVram -or $IncludeOversizedModels) {
                "Pull and test locally with scripts/test-local-agent-models before using in Continue."
            } else {
                "Do not pull by default on this hardware estimate. Use a larger model host, manual override, or IncludeOversizedModels before local testing."
            }

            $fitLabel = if ($vramRecommendation.FitsAvailableVram) { "fits VRAM estimate" } else { "above VRAM estimate" }
            Write-Host "Discovered candidate: $modelTag ($fitLabel)"

            $results.Add([pscustomobject]@{
                Model = $modelTag
                Family = $family
                Source = $source.Source
                Status = $status
                Reason = Get-CandidateReason -Model $modelTag
                NextStep = $nextStep
                ModelHostPlatform = $modelHostPlatform
                VramRecommendation = $vramRecommendation
            })
        }
    }
    catch {
        $sourceName = if ($SourceHtmlPath) { "local-html-fixture" } else { "ollama-library-page" }
        $errorMessage = $_.Exception.Message
        Write-Host "Source error for family: $family ($sourceName) - $errorMessage"
        $errors.Add([pscustomobject]@{
            Family = $family
            Source = $sourceName
            Error = $errorMessage
        })
    }
}

$uniqueResults = $results |
    Sort-Object Model, Family -Unique |
    Sort-Object Model
$uniqueSkippedResults = $skippedResults |
    Sort-Object Model, Family -Unique |
    Sort-Object Model

$report = [pscustomobject]@{
    GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    DiscoveryMode = if ($SourceHtmlPath) { "local-fixture" } else { "online" }
    SourceBaseUrl = if ($SourceHtmlPath) { "redacted" } else { ConvertTo-SafeSourceBaseUrl $SourceBaseUrl }
    RepositoryContentSent = $false
    HardwareProfileSent = $false
    ModelProfilePath = if ($ModelProfilePath) { "redacted" } else { $null }
    VramSelectionMode = $VramSelectionMode
    AvailableVramGb = if ($effectiveAvailableVramGb -gt 0) { $effectiveAvailableVramGb } else { $null }
    AvailableVramSource = $vramSource
    ModelHostPlatform = $modelHostPlatform
    IncludeOversizedModels = [bool]$IncludeOversizedModels
    PullsModels = $false
    RewritesContinueConfig = $false
    Candidates = @($uniqueResults)
    SkippedCandidates = @($uniqueSkippedResults)
    Errors = @($errors)
    Note = "Online discovery reports candidate names only. It does not prove tool support, pull models, or update Continue config."
}

$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

Write-Host "Discovery summary: $(@($uniqueResults).Count) candidate(s), $(@($uniqueSkippedResults).Count) skipped candidate(s), $($errors.Count) source error(s)."
foreach ($candidate in $uniqueResults) {
    if ($candidate.VramRecommendation -and $candidate.VramRecommendation.FitsAvailableVram -eq $true) {
        $fitLabel = "fits VRAM estimate"
    } elseif ($candidate.VramRecommendation -and $candidate.VramRecommendation.FitsAvailableVram -eq $false) {
        $fitLabel = "above VRAM estimate"
    } else {
        $fitLabel = "not estimated"
    }
    Write-Host "$($candidate.Model): $($candidate.Status) ($fitLabel)"
}

foreach ($candidate in $uniqueSkippedResults) {
    Write-Host "$($candidate.Model): skipped ($($candidate.Reason))"
}

if ($errors.Count -gt 0) {
    Write-Host "Discovery completed with $($errors.Count) source error(s). See report."
}

if ($effectiveAvailableVramGb -gt 0) {
    Write-Host "VRAM annotations were calculated locally and were not sent to the online source."
}
Write-Host "Candidate report written to $OutputPath"
