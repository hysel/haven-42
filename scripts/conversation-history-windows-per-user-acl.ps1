$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Native Windows proof only. It accepts no path or content and operates inside
# one freshly generated directory beneath the system temporary directory.
$contractPath = Join-Path $PSScriptRoot '..\config\conversation-history-windows-per-user-acl.json'
$contract = Get-Content -LiteralPath $contractPath -Raw | ConvertFrom-Json -Depth 16

if (
    $contract.schemaVersion -ne 1 -or
    $contract.status -ne 'development-synthetic-temporary-only' -or
    $contract.platform -ne 'windows' -or
    -not $contract.acl.testOwnedTemporaryDirectoryOnly -or
    $contract.acl.callerPathAllowed -or
    $contract.acl.reparsePointsAllowed -or
    -not $contract.acl.inheritanceMustBeProtected -or
    -not $contract.acl.unexpectedPrincipalFailsClosed -or
    -not $contract.acl.unexpectedDenyOrRightsFailsClosed -or
    $contract.acl.productionApplicationDirectoryProven -or
    -not $contract.authority.syntheticTemporaryValidationAllowed -or
    $contract.authority.runtimeRouteAllowed -or
    $contract.authority.uiControlAllowed -or
    $contract.authority.userContentAllowed -or
    $contract.authority.databaseOpenAllowed -or
    $contract.authority.databaseCreateAllowed -or
    $contract.authority.callerSelectedPathAllowed -or
    $contract.authority.persistentApplicationWriteAllowed -or
    $contract.authority.packageAdmissionAllowed -or
    $contract.authority.productionUseAllowed
) {
    throw 'unsafe-acl-contract'
}

$currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$systemSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')
$usersSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-32-545')
$expectedSids = @($currentSid.Value, $systemSid.Value)
$inheritance = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
$propagation = [System.Security.AccessControl.PropagationFlags]::None
$fullControl = [System.Security.AccessControl.FileSystemRights]::FullControl
$allow = [System.Security.AccessControl.AccessControlType]::Allow

function Get-RuleSid([System.Security.AccessControl.FileSystemAccessRule]$Rule) {
    return $Rule.IdentityReference.Translate(
        [System.Security.Principal.SecurityIdentifier]
    ).Value
}

function Assert-ExactAcl([string]$LiteralPath, [bool]$RequireProtected) {
    $acl = Get-Acl -LiteralPath $LiteralPath
    if ($RequireProtected -and -not $acl.AreAccessRulesProtected) {
        throw 'acl-inheritance-not-protected'
    }
    $rules = @($acl.Access)
    if ($rules.Count -ne 2) {
        throw 'unexpected-acl-rule-count'
    }
    $seen = @{}
    foreach ($rule in $rules) {
        $sid = Get-RuleSid $rule
        if ($sid -notin $expectedSids) {
            throw 'unexpected-acl-principal'
        }
        if (
            $rule.AccessControlType -ne $allow -or
            (($rule.FileSystemRights -band $fullControl) -ne $fullControl)
        ) {
            throw 'unexpected-acl-rights'
        }
        if ($seen.ContainsKey($sid)) {
            throw 'duplicate-acl-principal'
        }
        $seen[$sid] = $true
    }
    if ($seen.Count -ne 2) {
        throw 'missing-acl-principal'
    }
}

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$directory = Join-Path $tempRoot ('haven42-history-acl-' + [guid]::NewGuid().ToString('N'))
$created = $false
$unexpectedPrincipalRefused = $false
try {
    if (Test-Path -LiteralPath $directory) {
        throw 'temporary-directory-already-exists'
    }
    [System.IO.Directory]::CreateDirectory($directory) | Out-Null
    $created = $true
    $item = Get-Item -LiteralPath $directory -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'temporary-directory-is-reparse-point'
    }

    $directoryAcl = [System.Security.AccessControl.DirectorySecurity]::new()
    $directoryAcl.SetOwner($currentSid)
    $directoryAcl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @($currentSid, $systemSid)) {
        $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
            $sid, $fullControl, $inheritance, $propagation, $allow
        )
        [void]$directoryAcl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $directory -AclObject $directoryAcl
    Assert-ExactAcl -LiteralPath $directory -RequireProtected $true

    $keyPath = Join-Path $directory 'history-key.dpapi'
    $bytes = [byte[]](1..32)
    $stream = [System.IO.File]::Open(
        $keyPath,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    } finally {
        $stream.Dispose()
        [Array]::Clear($bytes, 0, $bytes.Length)
    }
    Assert-ExactAcl -LiteralPath $keyPath -RequireProtected $false

    $mutated = Get-Acl -LiteralPath $keyPath
    $extraRule = [System.Security.AccessControl.FileSystemAccessRule]::new(
        $usersSid,
        [System.Security.AccessControl.FileSystemRights]::Read,
        [System.Security.AccessControl.AccessControlType]::Allow
    )
    [void]$mutated.AddAccessRule($extraRule)
    Set-Acl -LiteralPath $keyPath -AclObject $mutated
    try {
        Assert-ExactAcl -LiteralPath $keyPath -RequireProtected $false
    } catch {
        if ($_.Exception.Message -ne 'unexpected-acl-rule-count' -and
            $_.Exception.Message -ne 'unexpected-acl-principal') {
            throw
        }
        $unexpectedPrincipalRefused = $true
    }
    if (-not $unexpectedPrincipalRefused) {
        throw 'unexpected-principal-was-accepted'
    }

    [ordered]@{
        schemaVersion = 1
        status = 'windows-synthetic-per-user-acl-passed'
        checks = [ordered]@{
            protectedDirectoryDacl = $true
            currentUserFullControl = $true
            systemFullControl = $true
            inheritedFileAclBounded = $true
            unexpectedPrincipalFailsClosed = $true
            freshDirectoryNotReparsePoint = $true
            callerPathAbsent = $true
            productionApplicationDirectoryProven = $false
        }
        authority = $contract.authority
    } | ConvertTo-Json -Depth 8 -Compress
} finally {
    if ($created -and (Test-Path -LiteralPath $directory)) {
        Remove-Item -LiteralPath $directory -Recurse -Force
    }
    if (Test-Path -LiteralPath $directory) {
        throw 'temporary-residue-detected'
    }
}
