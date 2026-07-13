param(
    [string[]]$Models = @(),
    [string]$TargetRepo,
    [string]$OutputPath,
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string]$AgentCommand = "aider",
    [string]$AgentArgumentsTemplate = '--set-env OLLAMA_API_BASE={OllamaBaseUrl} --read README.md --read pyproject.toml --read app/main.py --read app/settings.py --read tests/test_main.py --message "{Prompt}" --yes-always --no-auto-commits --no-gitignore --map-tokens 0 --input-history-file "{TempDir}\aider-input-history.txt" --chat-history-file "{TempDir}\aider-chat-history.md" --no-check-update --analytics-disable --no-auto-lint --no-auto-test --line-endings lf',
    [string]$WriteAgentArgumentsTemplate = '--set-env OLLAMA_API_BASE={OllamaBaseUrl} README.md --read pyproject.toml --read app/main.py --read app/settings.py --read tests/test_main.py --message "{Prompt}" --yes-always --no-auto-commits --no-gitignore --map-tokens 0 --input-history-file "{TempDir}\aider-input-history.txt" --chat-history-file "{TempDir}\aider-chat-history.md" --no-check-update --analytics-disable --no-auto-lint --no-auto-test --line-endings lf',
    [string]$ModelArgumentTemplate = '--model "ollama_chat/{Model}"',
    [int]$TimeoutSeconds = 600,
    [switch]$IncludeWriteSmoke,
    [switch]$AllowNonGeneratedTarget,
    [switch]$UnloadAfterEach,
    [switch]$DryRun
)

$scriptPath = Join-Path $PSScriptRoot "test-agent-cli-surface-models.ps1"
$arguments = @{
    SurfaceName = "Aider CLI"
    SurfaceKey = "aider-cli"
    Models = $Models
    TargetRepo = $TargetRepo
    OutputPath = $OutputPath
    OllamaBaseUrl = $OllamaBaseUrl
    AgentCommand = $AgentCommand
    AgentArgumentsTemplate = $AgentArgumentsTemplate
    WriteAgentArgumentsTemplate = $WriteAgentArgumentsTemplate
    ModelArgumentTemplate = $ModelArgumentTemplate
    InstallHint = "Install with pipx install aider-chat or pass the command override."
    TimeoutSeconds = $TimeoutSeconds
    IncludeWriteSmoke = $IncludeWriteSmoke
    AllowNonGeneratedTarget = $AllowNonGeneratedTarget
    UnloadAfterEach = $UnloadAfterEach
    DryRun = $DryRun
}

& $scriptPath @arguments
exit $LASTEXITCODE
