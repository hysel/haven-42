Set-StrictMode -Version Latest

function Import-OnboardingJson {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required onboarding catalog was not found: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-OnboardingWorkflow {
    param([Parameter(Mandatory)][object]$Registry, [Parameter(Mandatory)][string]$Id)
    $matches = @($Registry.workflows | Where-Object { $_.id -eq $Id })
    if ($matches.Count -ne 1) { throw "Workflow not found or not unique: $Id" }
    return $matches[0]
}

function Get-OnboardingScriptCommand {
    param(
        [Parameter(Mandatory)][object]$Workflow,
        [Parameter(Mandatory)][ValidateSet("windows", "linux", "macos")][string]$Platform,
        [string]$Arguments = ""
    )
    $entry = $Workflow.entryPoints.$Platform
    if ([string]::IsNullOrWhiteSpace($entry)) { throw "Workflow $($Workflow.id) does not support $Platform." }
    if ($Platform -eq "windows") {
        $path = ".\" + ($entry -replace "/", "\")
        if ($entry -match "\.ps1$") { return "pwsh -NoProfile -ExecutionPolicy Bypass -File $path $Arguments".Trim() }
        return "$path $Arguments".Trim()
    }
    return "./$entry $Arguments".Trim()
}

function Write-OnboardingReport {
    param(
        [Parameter(Mandatory)][object]$Report,
        [Parameter(Mandatory)][scriptblock]$MarkdownRenderer,
        [string]$OutputPath,
        [string]$MarkdownOutputPath,
        [switch]$AsJson
    )
    $json = $Report | ConvertTo-Json -Depth 20
    $markdown = & $MarkdownRenderer $Report
    foreach ($path in @($OutputPath, $MarkdownOutputPath)) {
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        $parent = Split-Path -Parent $path
        if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    }
    if ($OutputPath) { $json | Set-Content -LiteralPath $OutputPath -Encoding utf8 }
    if ($MarkdownOutputPath) { $markdown | Set-Content -LiteralPath $MarkdownOutputPath -Encoding utf8 }
    if ($AsJson -or $OutputPath) { return $json }
    return $markdown
}

Export-ModuleMember -Function Import-OnboardingJson, Get-OnboardingWorkflow, Get-OnboardingScriptCommand, Write-OnboardingReport
