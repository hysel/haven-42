param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteHost,
    [string]$RemoteUser,
    [int]$RemotePort = 22,
    [string]$IdentityFile,
    [ValidateSet("Linux", "macOS")]
    [string]$RemotePlatform = "Linux",
    [string]$OutputPath,
    [int]$TimeoutSeconds = 60,
    [switch]$AllowInteractiveSsh
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "[1/6] Checking local SSH tools..."
$ssh = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $ssh) {
    throw "ssh is required. Install OpenSSH Client and try again."
}

$scp = Get-Command scp -ErrorAction SilentlyContinue
if ($AllowInteractiveSsh -and -not $scp) {
    throw "scp is required for interactive SSH mode. Install OpenSSH Client and try again."
}

$scriptName = if ($RemotePlatform -eq "macOS") {
    "get-local-model-profile.macos.sh"
} else {
    "get-local-model-profile.linux.sh"
}

Write-Host "[2/6] Selected $RemotePlatform profile script: $scriptName"
$scriptPath = Join-Path $PSScriptRoot $scriptName
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "Profile script not found: $scriptPath"
}

$target = if ([string]::IsNullOrWhiteSpace($RemoteUser)) {
    $RemoteHost
} else {
    "$RemoteUser@$RemoteHost"
}

function New-SshBaseArguments {
    param([switch]$Interactive)

    $items = [System.Collections.Generic.List[string]]::new()
    $items.Add("-p")
    $items.Add([string]$RemotePort)
    $items.Add("-o")
    $items.Add("ConnectTimeout=$TimeoutSeconds")
    $items.Add("-o")
    $items.Add("ServerAliveInterval=15")
    $items.Add("-o")
    $items.Add("ServerAliveCountMax=2")
    if (-not $Interactive) {
        $items.Add("-o")
        $items.Add("BatchMode=yes")
    }
    if (-not [string]::IsNullOrWhiteSpace($IdentityFile)) {
        $items.Add("-i")
        $items.Add($IdentityFile)
    }

    return $items
}

function Invoke-ProcessCapture {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$StandardInput,
        [switch]$Interactive
    )

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo.FileName = $FilePath
    foreach ($argument in $Arguments) {
        [void]$process.StartInfo.ArgumentList.Add($argument)
    }
    $process.StartInfo.RedirectStandardInput = (-not $Interactive -and $null -ne $StandardInput)
    $process.StartInfo.RedirectStandardOutput = $true
    $process.StartInfo.RedirectStandardError = $true
    $process.StartInfo.UseShellExecute = $false
    $process.StartInfo.CreateNoWindow = (-not $Interactive)

    [void]$process.Start()

    $stdinError = $null
    if (-not $Interactive -and $null -ne $StandardInput) {
        try {
            $process.StandardInput.Write($StandardInput)
            $process.StandardInput.Close()
        }
        catch {
            $stdinError = $_.Exception.Message
            try { $process.StandardInput.Close() } catch { }
        }
    }

    $completed = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $completed) {
        try { $process.Kill($true) } catch { $process.Kill() }
        $process.Dispose()
        throw "Remote profile collection timed out after $TimeoutSeconds seconds. Verify SSH connectivity separately with ssh and a simple echo command."
    }

    $output = $process.StandardOutput.ReadToEnd()
    $errorOutput = $process.StandardError.ReadToEnd()
    $exitCode = $process.ExitCode
    $process.Dispose()

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $output
        ErrorOutput = $errorOutput
        StandardInputError = $stdinError
    }
}

Write-Host "[3/6] Preparing remote profile collection for $target on port $RemotePort..."

if ($AllowInteractiveSsh) {
    Write-Host "[4/6] Interactive SSH mode enabled. Uploading a temporary profiler with scp; enter the SSH password if prompted."

    $remoteScriptPath = "/tmp/local-engineering-agent-profile-$([guid]::NewGuid().ToString('N')).sh"
    $scpArgs = [System.Collections.Generic.List[string]]::new()
    foreach ($argument in (New-SshBaseArguments -Interactive)) {
        if ($argument -eq "-p") { $scpArgs.Add("-P") } else { $scpArgs.Add($argument) }
    }
    $scpArgs.Add($scriptPath)
    $scpArgs.Add("${target}:$remoteScriptPath")

    Write-Host "[4/6] Upload target: $remoteScriptPath"
    $scpResult = Invoke-ProcessCapture -FilePath $scp.Source -Arguments $scpArgs.ToArray() -Interactive
    if ($scpResult.ExitCode -ne 0) {
        throw "Remote profile upload failed with exit code $($scpResult.ExitCode). $($scpResult.ErrorOutput)"
    }

    $sshArgs = [System.Collections.Generic.List[string]]::new()
    foreach ($argument in (New-SshBaseArguments -Interactive)) { $sshArgs.Add($argument) }
    $sshArgs.Add($target)
    $sshArgs.Add("bash '$remoteScriptPath' --json; status=`$?; rm -f '$remoteScriptPath'; exit `$status")

    Write-Host "[5/6] Running remote GPU/CPU detection; enter the SSH password again if prompted."
    $runResult = Invoke-ProcessCapture -FilePath $ssh.Source -Arguments $sshArgs.ToArray() -Interactive
    if ($runResult.ExitCode -ne 0) {
        throw "Remote profile collection failed with exit code $($runResult.ExitCode). $($runResult.ErrorOutput)"
    }

    $output = $runResult.Output
} else {
    Write-Host "[4/6] Non-interactive SSH mode enabled. Streaming the profiler over SSH stdin; key-based SSH must already work."

    $sshArgs = [System.Collections.Generic.List[string]]::new()
    $sshArgs.Add("-T")
    foreach ($argument in (New-SshBaseArguments)) { $sshArgs.Add($argument) }
    $sshArgs.Add($target)
    $sshArgs.Add("bash -s -- --json")

    $scriptContent = Get-Content -LiteralPath $scriptPath -Raw
    Write-Host "[5/6] Running remote GPU/CPU detection..."
    $runResult = Invoke-ProcessCapture -FilePath $ssh.Source -Arguments $sshArgs.ToArray() -StandardInput $scriptContent

    if ($runResult.StandardInputError) {
        $detail = if ([string]::IsNullOrWhiteSpace($runResult.ErrorOutput)) { $runResult.StandardInputError } else { $runResult.ErrorOutput.Trim() }
        throw "SSH closed before the profile script could be sent. $detail"
    }

    if ($runResult.ExitCode -ne 0) {
        throw "Remote profile collection failed with exit code $($runResult.ExitCode). $($runResult.ErrorOutput)"
    }

    $output = $runResult.Output
}

if ([string]::IsNullOrWhiteSpace($output)) {
    throw "Remote profile collection returned no output."
}

Write-Host "[6/6] Validating remote profile JSON..."
# Validate that the remote output is JSON before saving it.
$output | ConvertFrom-Json | Out-Null

if ($OutputPath) {
    $outputDirectory = Split-Path -Parent $OutputPath
    if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    }
    Set-Content -LiteralPath $OutputPath -Value $output.TrimEnd() -Encoding UTF8
    Write-Host "[6/6] Remote model profile written to $OutputPath"
} else {
    $output.TrimEnd()
}


