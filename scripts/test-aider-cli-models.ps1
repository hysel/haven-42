param(
    [string[]]$Models = @(),
    [string]$TargetRepo,
    [string]$OutputPath,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$AgentCommand,
    [string]$AgentArgumentsTemplate,
    [string]$WriteAgentArgumentsTemplate,
    [string]$ModelArgumentTemplate,
    [int]$TimeoutSeconds = 600,
    [switch]$IncludeWriteSmoke,
    [switch]$AllowNonGeneratedTarget,
    [switch]$UnloadAfterEach,
    [switch]$DryRun
)

$scriptPath = Join-Path $PSScriptRoot "test-agent-cli-surface-models.ps1"
$arguments = @{
    SurfaceKey = "aider-cli"
    Models = $Models
    TargetRepo = $TargetRepo
    OutputPath = $OutputPath
    OllamaBaseUrl = $OllamaBaseUrl
    AgentCommand = $AgentCommand
    AgentArgumentsTemplate = $AgentArgumentsTemplate
    WriteAgentArgumentsTemplate = $WriteAgentArgumentsTemplate
    ModelArgumentTemplate = $ModelArgumentTemplate
    TimeoutSeconds = $TimeoutSeconds
    IncludeWriteSmoke = $IncludeWriteSmoke
    AllowNonGeneratedTarget = $AllowNonGeneratedTarget
    UnloadAfterEach = $UnloadAfterEach
    DryRun = $DryRun
}

& $scriptPath @arguments
exit $LASTEXITCODE
