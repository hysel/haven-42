[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Executable,

    [ValidateSet("NoEffect", "Managed", "StorageDenied")]
    [string]$Mode = "NoEffect",

    [ValidateRange(10, 120)]
    [int]$StartupTimeoutSeconds = 30,

    [ValidatePattern("^(?:|[a-z0-9]+(?:-[a-z0-9]+)*)$")]
    [string]$ExpectedModelId = "",

    [ValidateSet("", "cpu", "cuda", "rocm", "vulkan")]
    [string]$ExpectedBackendMode = "",

    [ValidateSet("0.4.0-alpha.1", "0.4.0-alpha.2")]
    [string]$ExpectedVersion = "0.4.0-alpha.1"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function ConvertTo-CompactJson {
    param([Parameter(Mandatory = $true)]$Value)
    return ($Value | ConvertTo-Json -Depth 20 -Compress)
}

function Invoke-HavenGet {
    param(
        [Parameter(Mandatory = $true)][string]$Origin,
        [Parameter(Mandatory = $true)][string]$Path
    )
    return Invoke-RestMethod -Method Get -Uri ($Origin + $Path) -TimeoutSec 15
}

function Invoke-HavenPost {
    param(
        [Parameter(Mandatory = $true)][string]$Origin,
        [Parameter(Mandatory = $true)][string]$Token,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Body
    )
    $headers = @{
        "Origin" = $Origin
        "X-Haven-Token" = $Token
    }
    return Invoke-RestMethod `
        -Method Post `
        -Uri ($Origin + $Path) `
        -Headers $headers `
        -ContentType "application/json" `
        -Body (ConvertTo-CompactJson $Body) `
        -TimeoutSec 30
}

function Assert-Condition {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Code
    )
    if (-not $Condition) {
        throw $Code
    }
}

function Read-SharedText {
    param([Parameter(Mandatory = $true)][string]$Path)
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

function Assert-HavenError {
    param(
        [Parameter(Mandatory = $true)][string]$Origin,
        [Parameter(Mandatory = $true)][string]$Token,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Body,
        [Parameter(Mandatory = $true)][int]$StatusCode,
        [Parameter(Mandatory = $true)][string]$ErrorCode
    )
    try {
        Invoke-HavenPost -Origin $Origin -Token $Token -Path $Path -Body $Body | Out-Null
    }
    catch {
        $caught = $_
        $response = $caught.Exception.Response
        Assert-Condition ($null -ne $response) "missing-http-error-response"
        Assert-Condition ([int]$response.StatusCode -eq $StatusCode) "unexpected-http-error-status"
        $bodyText = [string]$caught.ErrorDetails.Message
        if ([string]::IsNullOrWhiteSpace($bodyText)) {
            $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
            try {
                $bodyText = $reader.ReadToEnd()
            }
            finally {
                $reader.Dispose()
            }
        }
        $value = $bodyText | ConvertFrom-Json
        Assert-Condition ($value.error -eq $ErrorCode) "unexpected-http-error-code"
        return
    }
    throw "request-unexpectedly-succeeded"
}

$resolvedExecutable = (Resolve-Path -LiteralPath $Executable).Path
Assert-Condition ([IO.Path]::GetFileName($resolvedExecutable) -ieq "haven42.exe") "invalid-executable-name"

$validationRoot = Join-Path ([IO.Path]::GetTempPath()) ("haven42-alpha-native-" + [Guid]::NewGuid().ToString("N"))
$stdoutPath = Join-Path $validationRoot "stdout.log"
$stderrPath = Join-Path $validationRoot "stderr.log"
$portableManagedState = Join-Path ([IO.Path]::GetDirectoryName($resolvedExecutable)) "Haven42-Data"
$legacyManagedState = Join-Path $env:LOCALAPPDATA "Haven42\alpha"
$portableStateExistedBefore = Test-Path -LiteralPath $portableManagedState
$legacyStateExistedBefore = Test-Path -LiteralPath $legacyManagedState
$process = $null
$shutdownAccepted = $false

New-Item -ItemType Directory -Path $validationRoot | Out-Null
try {
    $process = Start-Process `
        -FilePath $resolvedExecutable `
        -ArgumentList @("--port", "0", "--no-open") `
        -WorkingDirectory ([IO.Path]::GetDirectoryName($resolvedExecutable)) `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru

    $deadline = [DateTime]::UtcNow.AddSeconds($StartupTimeoutSeconds)
    $origin = $null
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($process.HasExited) {
            throw "haven-exited-before-ready"
        }
        if (Test-Path -LiteralPath $stdoutPath) {
            $text = Read-SharedText -Path $stdoutPath
            $match = [regex]::Match($text, "http://127\.0\.0\.1:[0-9]{1,5}")
            if ($match.Success) {
                $origin = $match.Value
                break
            }
        }
        Start-Sleep -Milliseconds 100
    }
    Assert-Condition ($null -ne $origin) "haven-startup-timeout"

    $bootstrap = Invoke-HavenGet -Origin $origin -Path "/api/bootstrap"
    $token = [string]$bootstrap.sessionToken
    Assert-Condition ($bootstrap.version -eq $ExpectedVersion) "wrong-alpha-version"
    Assert-Condition ($bootstrap.runtime.bindScope -eq "loopback-only") "non-loopback-bind"
    Assert-Condition ($bootstrap.alpha.chatOnly -eq $false) "chat-only-policy-still-enabled"
    Assert-Condition ($bootstrap.alpha.textOnly -eq $true) "text-only-policy-missing"
    Assert-Condition ($bootstrap.alpha.unsigned -eq $true) "unsigned-label-missing"
    Assert-Condition ($bootstrap.alpha.productionReady -eq $false) "production-claim-present"
    Assert-Condition ($bootstrap.package.required -eq $true) "package-not-required"
    Assert-Condition ($bootstrap.package.verified -eq $true) "package-integrity-not-verified"

    $readiness = Invoke-HavenPost -Origin $origin -Token $token -Path "/api/readiness" -Body @{ force = $true }
    Assert-Condition ($readiness.kind -eq "system-readiness") "invalid-readiness-kind"
    Assert-Condition ($readiness.effects.networkUsed -eq $false) "readiness-used-network"
    Assert-Condition ($readiness.effects.filesWritten -eq $false) "readiness-wrote-files"
    Assert-Condition ($readiness.effects.installationPerformed -eq $false) "readiness-installed-software"
    Assert-Condition ($readiness.effects.elevationRequested -eq $false) "readiness-requested-elevation"
    Assert-Condition ($readiness.effects.servicesChanged -eq $false) "readiness-changed-services"
    Assert-Condition ($readiness.effects.driversChanged -eq $false) "readiness-changed-drivers"

    $plan = Invoke-HavenPost `
        -Origin $origin `
        -Token $token `
        -Path "/api/setup-plan" `
        -Body @{ snapshotId = $readiness.snapshotId; intent = "guided-setup" }
    $managed = $plan.alphaCandidate.managedPlan
    if ($Mode -eq "StorageDenied") {
        Assert-Condition ($null -eq $managed) "storage-denial-created-managed-plan"
        Assert-Condition ($null -eq $plan.alphaCandidate.modelSelection.selected) "storage-denial-selected-model"
        Assert-Condition ($plan.alphaCandidate.modelSelection.automaticExecutionAllowed -eq $false) "storage-denial-allowed-execution"
        Assert-Condition ($plan.alphaCandidate.modelSelection.decision -eq "no-safe-recommendation") "storage-denial-model-decision"
        Assert-Condition ($plan.alphaCandidate.hardware.decision -eq "unsupported") "storage-denial-hardware-decision"
        Assert-Condition (@($plan.alphaCandidate.hardware.blockers) -contains "storage-threshold") "storage-denial-blocker-missing"
    }
    else {
        Assert-Condition ($managed.kind -eq "windows-alpha-setup-plan") "managed-plan-missing"
        Assert-Condition (@("cpu", "cuda", "rocm", "vulkan") -contains $managed.backendMode) "invalid-backend-mode"
        Assert-Condition ($managed.requiredStorageBytes -is [long] -or $managed.requiredStorageBytes -is [int]) "invalid-required-storage"
        Assert-Condition ([long]$managed.requiredStorageBytes -gt 0) "invalid-required-storage"
        if (-not [string]::IsNullOrWhiteSpace($ExpectedModelId)) {
            Assert-Condition ($managed.modelId -eq $ExpectedModelId) "unexpected-model-selection"
        }
        if (-not [string]::IsNullOrWhiteSpace($ExpectedBackendMode)) {
            Assert-Condition ($managed.backendMode -eq $ExpectedBackendMode) "unexpected-backend-selection"
        }
        Assert-Condition ($managed.effects.Count -eq 4) "invalid-managed-effects"
        Assert-Condition ($managed.effects[3] -eq "local-model-validation") "validation-effect-missing"
    }

    $resources = Invoke-HavenGet -Origin $origin -Path "/api/alpha/resources"
    Assert-Condition ($resources.kind -eq "windows-alpha-local-metrics") "invalid-resource-kind"
    Assert-Condition ($resources.persisted -eq $false) "resources-persisted"
    Assert-Condition ($resources.externalTelemetryUsed -eq $false) "external-telemetry-used"

    Assert-HavenError `
        -Origin $origin `
        -Token $token `
        -Path "/api/workflows" `
        -Body @{} `
        -StatusCode 404 `
        -ErrorCode "alpha-text-only"

    $status = Invoke-HavenGet -Origin $origin -Path "/api/alpha/setup-status"
    Assert-Condition ($status.phase -eq "idle") "setup-not-idle"
    Assert-Condition ($status.driverChanges -eq $false) "driver-change-reported"
    Assert-Condition ($status.serviceChanges -eq $false) "service-change-reported"
    Assert-Condition ($status.firewallChanges -eq $false) "firewall-change-reported"
    Assert-Condition ($status.elevationRequested -eq $false) "elevation-reported"

    $managedSetupCompleted = $false
    $managedChatCompleted = $false
    $modelUnloadVerified = $false
    $acceleratorUseVerified = $false
    if ($Mode -eq "NoEffect") {
        Assert-HavenError `
            -Origin $origin `
            -Token $token `
            -Path "/api/alpha/setup-approve" `
            -Body @{ planId = $managed.planId; effects = @("driver-install"); confirmed = $true } `
            -StatusCode 409 `
            -ErrorCode "approval-does-not-match-plan"
        $statusAfter = Invoke-HavenGet -Origin $origin -Path "/api/alpha/setup-status"
        Assert-Condition ($statusAfter.phase -eq "idle") "rejected-approval-changed-state"
    }
    elseif ($Mode -eq "Managed") {
        $approval = Invoke-HavenPost `
            -Origin $origin `
            -Token $token `
            -Path "/api/alpha/setup-approve" `
            -Body @{ planId = $managed.planId; effects = @($managed.effects); confirmed = $true }
        Assert-Condition ($approval.singleUse -eq $true) "approval-not-single-use"
        Assert-Condition ($approval.persisted -eq $false) "approval-persisted"
        $started = Invoke-HavenPost `
            -Origin $origin `
            -Token $token `
            -Path "/api/alpha/setup-execute" `
            -Body @{ approvalToken = $approval.approvalToken }
        Assert-Condition ($started.kind -eq "windows-alpha-setup-progress") "managed-setup-response-invalid"

        $setupDeadline = [DateTime]::UtcNow.AddHours(2)
        $previousPhase = ""
        while ([DateTime]::UtcNow -lt $setupDeadline) {
            Start-Sleep -Seconds 2
            $setupStatus = Invoke-HavenGet -Origin $origin -Path "/api/alpha/setup-status"
            if ($setupStatus.phase -ne $previousPhase) {
                [Console]::Error.WriteLine(
                    "Managed setup: {0} ({1}%)",
                    [string]$setupStatus.phase,
                    [int]$setupStatus.progressPercent
                )
                $previousPhase = [string]$setupStatus.phase
            }
            if ($setupStatus.phase -eq "complete") {
                $managedSetupCompleted = $true
                break
            }
            if (@("failed", "cancelled") -contains $setupStatus.phase) {
                throw ("managed-setup-" + [string]$setupStatus.phase + "-" + [string]$setupStatus.error)
            }
        }
        Assert-Condition $managedSetupCompleted "managed-setup-timeout"
        $acceleratorUseVerified = $managed.gpuAccelerationRequired -eq $true

        $connected = Invoke-HavenPost `
            -Origin $origin `
            -Token $token `
            -Path "/api/connect" `
            -Body @{
                endpoint = "http://127.0.0.1:11435"
                timeoutSeconds = 300
                idleUnloadSeconds = 300
                authentication = @{ mode = "none"; apiKey = "" }
            }
        Assert-Condition ($connected.connected -eq $true) "managed-provider-connect-failed"

        $selectedModel = [string]$plan.alphaCandidate.modelSelection.selected.name
        $chat = Invoke-HavenPost `
            -Origin $origin `
            -Token $token `
            -Path "/api/text" `
            -Body @{
                capabilityId = "general.chat"
                model = $selectedModel
                messages = @(@{ role = "user"; content = "Reply with only NATIVE_ALPHA_OK." })
                attachments = @()
                images = @()
                contextConsent = $false
            }
        Assert-Condition ($chat.kind -eq "chat-message") "managed-chat-kind-invalid"
        Assert-Condition (-not [string]::IsNullOrWhiteSpace([string]$chat.content)) "managed-chat-empty"
        $managedChatCompleted = $true

        $resourceAfterChat = Invoke-HavenGet -Origin $origin -Path "/api/alpha/resources"
        Assert-Condition ($resourceAfterChat.sessionTokens.requestCount -ge 1) "managed-token-count-missing"
        Assert-Condition ($resourceAfterChat.sessionTokens.totalTokens -ge 1) "managed-token-total-missing"

        $unloaded = Invoke-HavenPost -Origin $origin -Token $token -Path "/api/unload" -Body @{}
        Assert-Condition ($unloaded.modelUnloaded -eq $true) "managed-model-unload-failed"
        $modelUnloadVerified = $true
    }

    $shutdown = Invoke-HavenPost -Origin $origin -Token $token -Path "/api/shutdown" -Body @{}
    Assert-Condition ($shutdown.shutdownAccepted -eq $true) "shutdown-not-accepted"
    Assert-Condition ($shutdown.modelCleanupVerified -eq $true) "shutdown-cleanup-not-verified"
    $shutdownAccepted = $true
    if (-not $process.WaitForExit(15000)) {
        throw "haven-shutdown-timeout"
    }
    $process.Refresh()
    Assert-Condition ($process.HasExited) "haven-process-still-running"
    if (@("NoEffect", "StorageDenied") -contains $Mode) {
        Assert-Condition ((Test-Path -LiteralPath $legacyManagedState) -eq $legacyStateExistedBefore) "legacy-local-appdata-state-changed"
        Assert-Condition ((Test-Path -LiteralPath $portableManagedState) -eq $portableStateExistedBefore) "no-effect-portable-state-changed"
    }

    $managedPortClosed = $true
    if ($Mode -eq "Managed") {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $connection = $client.BeginConnect("127.0.0.1", 11435, $null, $null)
            $managedPortClosed = -not $connection.AsyncWaitHandle.WaitOne(1500)
            if (-not $managedPortClosed) {
                try {
                    $client.EndConnect($connection)
                    $managedPortClosed = $false
                }
                catch {
                    $managedPortClosed = $true
                }
            }
        }
        finally {
            $client.Dispose()
        }
        Assert-Condition $managedPortClosed "managed-provider-still-listening"
    }

    $safeAccelerators = @($readiness.accelerators | ForEach-Object {
        [ordered]@{
            vendor = $_.vendor
            model = $_.model
            memoryGiB = $_.memoryGiB
            driverDetected = -not [string]::IsNullOrWhiteSpace([string]$_.driverVersion)
            backendCandidate = $_.backendCandidate
        }
    })
    [ordered]@{
        schemaVersion = 1
        kind = "haven42-windows-alpha-native-validation"
        mode = $Mode
        status = "passed"
        version = $bootstrap.version
        packageVerified = $bootstrap.package.verified
        textOnly = $bootstrap.alpha.textOnly
        unsigned = $bootstrap.alpha.unsigned
        operatingSystem = $readiness.platform.operatingSystem
        productName = $readiness.platform.productName
        buildNumber = $readiness.platform.buildNumber
        architecture = $readiness.platform.architecture
        logicalProcessors = $readiness.platform.logicalProcessors
        systemMemoryGiB = $readiness.platform.systemMemoryGiB
        availableStorageGiB = $readiness.platform.availableStorageGiB
        accelerators = $safeAccelerators
        hardwareDecision = $plan.alphaCandidate.hardware.decision
        modelDecision = $plan.alphaCandidate.modelSelection.decision
        selectedModelId = if ($null -eq $managed) { $null } else { $managed.modelId }
        backendMode = if ($null -eq $managed) { $null } else { $managed.backendMode }
        requiredStorageGiB = if ($null -eq $managed) { $null } else { [Math]::Ceiling(([double]$managed.requiredStorageBytes / 1GB) * 10) / 10 }
        gpuAccelerationRequired = if ($null -eq $managed) { $false } else { $managed.gpuAccelerationRequired }
        storageDenialVerified = $Mode -eq "StorageDenied"
        rejectedAuthorityStayedIdle = @("NoEffect", "StorageDenied") -contains $Mode
        stateWritten = $Mode -eq "Managed"
        managedSetupCompleted = $managedSetupCompleted
        managedChatCompleted = $managedChatCompleted
        acceleratorUseVerified = $acceleratorUseVerified
        modelUnloadVerified = $modelUnloadVerified
        managedPortClosed = $managedPortClosed
        shutdownVerified = $true
        persistedUserContent = $false
        externalTelemetryUsed = $false
    } | ConvertTo-Json -Depth 20
}
finally {
    if ($null -ne $process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
    }
    if (Test-Path -LiteralPath $validationRoot) {
        Remove-Item -LiteralPath $validationRoot -Recurse -Force
    }
    if (-not $shutdownAccepted -and $null -ne $process -and -not $process.HasExited) {
        throw "exact-process-cleanup-failed"
    }
}
