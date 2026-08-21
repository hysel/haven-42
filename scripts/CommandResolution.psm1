Set-StrictMode -Version Latest

function Resolve-ExternalCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Command
    )

    $runningOnWindows = if (Get-Variable -Name IsWindows -ErrorAction SilentlyContinue) { [bool]$IsWindows } else { $env:OS -eq 'Windows_NT' }
    $commandInfo = Get-Command $Command -ErrorAction Stop | Select-Object -First 1
    $source = $commandInfo.Source
    if ([string]::IsNullOrWhiteSpace($source)) {
        throw "Command does not resolve to an executable or script path: $Command"
    }

    if ($runningOnWindows -and $source -match '(?i)\.ps1$') {
        $cmdShim = [System.IO.Path]::ChangeExtension($source, '.cmd')
        if (Test-Path -LiteralPath $cmdShim) {
            return [pscustomobject]@{
                FilePath = $cmdShim
                ArgumentPrefix = ''
                PrefixArguments = @()
                Source = $source
                LaunchKind = 'windows-cmd-shim'
            }
        }
    }

    if ($source -match '(?i)\.ps1$') {
        $powerShell = Get-Command pwsh -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $powerShell -and $runningOnWindows) {
            $powerShell = Get-Command powershell -ErrorAction SilentlyContinue | Select-Object -First 1
        }
        if (-not $powerShell) { throw "PowerShell is required to launch script command: $source" }
        return [pscustomobject]@{
            FilePath = $powerShell.Source
            ArgumentPrefix = "-NoProfile -File `"$source`""
            PrefixArguments = @('-NoProfile', '-File', $source)
            Source = $source
            LaunchKind = 'powershell-script'
        }
    }

    return [pscustomobject]@{
        FilePath = $source
        ArgumentPrefix = ''
        PrefixArguments = @()
        Source = $source
        LaunchKind = 'native'
    }
}

function Resolve-Python3Command {
    [CmdletBinding()]
    param()

    $runningOnWindows = if (Get-Variable -Name IsWindows -ErrorAction SilentlyContinue) { [bool]$IsWindows } else { $env:OS -eq 'Windows_NT' }
    $candidates = if ($runningOnWindows) { @('python', 'python3') } else { @('python3', 'python') }
    foreach ($candidate in $candidates) {
        $commandInfo = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $commandInfo -or [string]::IsNullOrWhiteSpace($commandInfo.Source)) { continue }
        if ($runningOnWindows -and $commandInfo.Source -match '(?i)\\Microsoft\\WindowsApps\\python3?\.exe$') {
            continue
        }
        return $commandInfo
    }
    throw 'Python 3 does not resolve to an executable. Install it for repository engineering, or use the self-contained Haven 42 package.'
}

function Join-ResolvedCommandArguments {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [psobject]$Resolution,
        [AllowEmptyString()]
        [string]$Arguments = ''
    )

    return (@($Resolution.ArgumentPrefix, $Arguments) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) -join ' '
}

Export-ModuleMember -Function Resolve-ExternalCommand,Resolve-Python3Command,Join-ResolvedCommandArguments
