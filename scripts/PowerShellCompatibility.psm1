Set-StrictMode -Version Latest

function Test-HavenPathFullyQualified {
    [CmdletBinding()]
    param(
        [AllowEmptyString()]
        [string]$Path
    )

    if ([string]::IsNullOrEmpty($Path)) { return $false }

    # IsPathFullyQualified is unavailable in the .NET Framework used by
    # Windows PowerShell 5.1. Conservatively reject rooted paths, drive-
    # relative paths, UNC paths, and device paths on every host.
    return [System.IO.Path]::IsPathRooted($Path) -or
        $Path -match '^[A-Za-z]:' -or
        $Path -match '^[\\/]'
}

function Get-HavenRelativePath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$BasePath,
        [Parameter(Mandatory)]
        [string]$TargetPath
    )

    $base = [System.IO.Path]::GetFullPath($BasePath).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $target = [System.IO.Path]::GetFullPath($TargetPath)
    $comparison = if ($env:OS -eq 'Windows_NT') {
        [System.StringComparison]::OrdinalIgnoreCase
    } else {
        [System.StringComparison]::Ordinal
    }

    if ($target.Equals($base, $comparison)) { return '.' }

    $prefix = $base + [System.IO.Path]::DirectorySeparatorChar
    if (-not $target.StartsWith($prefix, $comparison)) {
        throw 'TargetPath must be contained by BasePath.'
    }

    return $target.Substring($prefix.Length)
}

Export-ModuleMember -Function Test-HavenPathFullyQualified,Get-HavenRelativePath
