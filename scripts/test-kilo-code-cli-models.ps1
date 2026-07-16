param(
    [string[]]$Models = @(),
    [string]$TargetRepo,
    [string]$OutputPath,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$AgentCommand,
    [string]$AgentArgumentsTemplate,
    [string]$ModelArgumentTemplate,
    [string]$KiloConfigPath,
    [int]$TimeoutSeconds = 600,
    [switch]$IncludeWriteSmoke,
    [switch]$IncludeScopedEdit,
    [switch]$AllowNonGeneratedTarget,
    [switch]$UnloadAfterEach,
    [switch]$DryRun
)

$scriptPath = Join-Path $PSScriptRoot "test-agent-cli-surface-models.ps1"
$arguments = @{
    SurfaceKey = "kilo-code-cli"
    Models = $Models
    TargetRepo = $TargetRepo
    OutputPath = $OutputPath
    OllamaBaseUrl = $OllamaBaseUrl
    TimeoutSeconds = $TimeoutSeconds
    IncludeWriteSmoke = $IncludeWriteSmoke
    IncludeScopedEdit = $IncludeScopedEdit
    AllowNonGeneratedTarget = $AllowNonGeneratedTarget
    UnloadAfterEach = $UnloadAfterEach
    DryRun = $DryRun
}
if ($PSBoundParameters.ContainsKey("KiloConfigPath")) { $arguments.AgentConfigPath = $KiloConfigPath }

foreach ($optionalArgument in @("AgentCommand", "AgentArgumentsTemplate", "ModelArgumentTemplate")) {
    if ($PSBoundParameters.ContainsKey($optionalArgument)) {
        $arguments[$optionalArgument] = Get-Variable -Name $optionalArgument -ValueOnly
    }
}

& $scriptPath @arguments
exit $LASTEXITCODE
