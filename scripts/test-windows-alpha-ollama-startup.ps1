[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Executable,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ModelsDirectory,

    [ValidateSet("cpu", "cuda", "rocm", "vulkan")]
    [string]$BackendMode = "cpu",

    [switch]$ConstrainedProfile,

    [switch]$InspectTags,

    [switch]$RunInference,

    [ValidateRange(5, 60)]
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Read-SharedText {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }
    $stream = New-Object System.IO.FileStream(
        $Path,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::ReadWrite
    )
    $reader = New-Object System.IO.StreamReader($stream)
    try {
        return $reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
        $stream.Dispose()
    }
}

$runtime = (Resolve-Path -LiteralPath $Executable).Path
if ([IO.Path]::GetFileName($runtime) -ine "ollama.exe") {
    throw "invalid-runtime-executable"
}
$models = [IO.Path]::GetFullPath($ModelsDirectory)
$diagnosticRoot = Join-Path ([IO.Path]::GetTempPath()) ("haven42-ollama-startup-" + [Guid]::NewGuid().ToString("N"))
$stdoutPath = Join-Path $diagnosticRoot "stdout.log"
$stderrPath = Join-Path $diagnosticRoot "stderr.log"
$process = $null
$started = $false

New-Item -ItemType Directory -Path $diagnosticRoot | Out-Null
New-Item -ItemType Directory -Path $models -Force | Out-Null
$previous = @{
    OLLAMA_HOST = $env:OLLAMA_HOST
    OLLAMA_MODELS = $env:OLLAMA_MODELS
    OLLAMA_ORIGINS = $env:OLLAMA_ORIGINS
    OLLAMA_VULKAN = $env:OLLAMA_VULKAN
    OLLAMA_LLM_LIBRARY = $env:OLLAMA_LLM_LIBRARY
    OLLAMA_NO_CLOUD = $env:OLLAMA_NO_CLOUD
    OLLAMA_NOHISTORY = $env:OLLAMA_NOHISTORY
    HOME = $env:HOME
    USERPROFILE = $env:USERPROFILE
    LOCALAPPDATA = $env:LOCALAPPDATA
    APPDATA = $env:APPDATA
    TEMP = $env:TEMP
    TMP = $env:TMP
}
try {
    $env:OLLAMA_HOST = "127.0.0.1:11435"
    $env:OLLAMA_MODELS = $models
    $env:OLLAMA_ORIGINS = "http://127.0.0.1"
    if ($BackendMode -eq "vulkan") {
        $env:OLLAMA_VULKAN = "1"
        Remove-Item Env:OLLAMA_LLM_LIBRARY -ErrorAction SilentlyContinue
    }
    elseif ($BackendMode -eq "cpu") {
        Remove-Item Env:OLLAMA_VULKAN -ErrorAction SilentlyContinue
        $env:OLLAMA_LLM_LIBRARY = "cpu"
    }
    else {
        Remove-Item Env:OLLAMA_VULKAN -ErrorAction SilentlyContinue
        Remove-Item Env:OLLAMA_LLM_LIBRARY -ErrorAction SilentlyContinue
    }
    if ($ConstrainedProfile) {
        $managedRoot = [IO.Directory]::GetParent($models).FullName
        $managedEnvironment = @{
            OLLAMA_NO_CLOUD = "1"
            OLLAMA_NOHISTORY = "1"
            HOME = Join-Path $managedRoot "home"
            USERPROFILE = Join-Path $managedRoot "home"
            LOCALAPPDATA = Join-Path $managedRoot "appdata\local"
            APPDATA = Join-Path $managedRoot "appdata\roaming"
            TEMP = Join-Path $managedRoot "temp"
            TMP = Join-Path $managedRoot "temp"
        }
        foreach ($path in @(
            $managedEnvironment.HOME,
            $managedEnvironment.LOCALAPPDATA,
            $managedEnvironment.APPDATA,
            $managedEnvironment.TEMP
        )) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
        foreach ($name in $managedEnvironment.Keys) {
            Set-Item ("Env:" + $name) $managedEnvironment[$name]
        }
    }
    $process = Start-Process `
        -FilePath $runtime `
        -ArgumentList @("serve") `
        -WorkingDirectory ([IO.Path]::GetDirectoryName($runtime)) `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($process.HasExited) {
            break
        }
        try {
            $version = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11435/api/version" -TimeoutSec 2
            if (-not [string]::IsNullOrWhiteSpace([string]$version.version)) {
                $started = $true
                break
            }
        }
        catch {
        }
        Start-Sleep -Milliseconds 250
    }
    $combined = (Read-SharedText -Path $stdoutPath) + "`n" + (Read-SharedText -Path $stderrPath)
    if ($combined.Length -gt 8192) {
        $combined = $combined.Substring($combined.Length - 8192)
    }
    $redacted = $combined.Replace($env:USERPROFILE, "<user-profile>")
    $redacted = [regex]::Replace(
        $redacted,
        "ssh-ed25519\s+[A-Za-z0-9+/=]+",
        "ssh-ed25519 <redacted-public-key>"
    )
    $tagRecords = @()
    if ($started -and $InspectTags) {
        $tags = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11435/api/tags" -TimeoutSec 10
        $tagRecords = @($tags.models | ForEach-Object {
            [ordered]@{
                name = $_.name
                digest = $_.digest
                size = $_.size
            }
        })
    }
    $inferenceMetadata = $null
    $processMetadata = @()
    if ($started -and $RunInference) {
        $tagName = [string]$tagRecords[0].name
        if ([string]::IsNullOrWhiteSpace($tagName)) {
            $tags = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11435/api/tags" -TimeoutSec 10
            $tagName = [string]$tags.models[0].name
        }
        $requestBody = @{
            model = $tagName
            prompt = "Reply with only the word ready."
            stream = $false
            keep_alive = "5m"
            options = @{ temperature = 0; seed = 42; num_predict = 8 }
        } | ConvertTo-Json -Depth 5 -Compress
        $generated = Invoke-RestMethod `
            -Method Post `
            -Uri "http://127.0.0.1:11435/api/generate" `
            -ContentType "application/json" `
            -Body $requestBody `
            -TimeoutSec 300
        $inferenceMetadata = [ordered]@{
            properties = @($generated.PSObject.Properties.Name | Sort-Object)
            done = $generated.done
            doneReason = $generated.done_reason
            responseLength = ([string]$generated.response).Length
            evalCount = $generated.eval_count
            evalCountType = if ($null -eq $generated.eval_count) { "null" } else { $generated.eval_count.GetType().FullName }
        }
        $running = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:11435/api/ps" -TimeoutSec 10
        $processMetadata = @($running.models | ForEach-Object {
            [ordered]@{ name = $_.name; size = $_.size; sizeVram = $_.size_vram }
        })
    }
    [ordered]@{
        schemaVersion = 1
        kind = "windows-alpha-ollama-startup-diagnostic"
        started = $started
        backendMode = $BackendMode
        constrainedProfile = [bool]$ConstrainedProfile
        processExited = $process.HasExited
        tags = $tagRecords
        inference = $inferenceMetadata
        loadedModels = $processMetadata
        diagnostic = $redacted
        persisted = $false
    } | ConvertTo-Json -Depth 5
    if (-not $started) {
        exit 1
    }
}
finally {
    if ($null -ne $process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
    }
    foreach ($name in @(
        "OLLAMA_HOST", "OLLAMA_MODELS", "OLLAMA_ORIGINS", "OLLAMA_VULKAN", "OLLAMA_LLM_LIBRARY",
        "OLLAMA_NO_CLOUD", "OLLAMA_NOHISTORY", "HOME", "USERPROFILE",
        "LOCALAPPDATA", "APPDATA", "TEMP", "TMP"
    )) {
        if ($null -eq $previous[$name]) {
            Remove-Item ("Env:" + $name) -ErrorAction SilentlyContinue
        }
        else {
            Set-Item ("Env:" + $name) $previous[$name]
        }
    }
    if (Test-Path -LiteralPath $diagnosticRoot) {
        Remove-Item -LiteralPath $diagnosticRoot -Recurse -Force
    }
}
