param(
    [string]$OllamaBaseUrl = "http://127.0.0.1:11434",
    [string[]]$Models = @(
        "qwen3.5:9b",
        "devstral-small-2:24b",
        "qwen3-coder:30b"
    ),
    [int]$TimeoutSeconds = 600
)

$ErrorActionPreference = "Stop"

function ConvertTo-SafeBaseUrl {
    param([string]$Value)

    return $Value.TrimEnd("/")
}

function Invoke-OllamaPull {
    param([string]$Model)

    $uri = "$(ConvertTo-SafeBaseUrl $OllamaBaseUrl)/api/pull"
    $body = @{
        model = $Model
        stream = $false
    } | ConvertTo-Json -Depth 5

    Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json" -TimeoutSec $TimeoutSeconds | Out-Null
}

foreach ($model in ($Models | Select-Object -Unique)) {
    if ([string]::IsNullOrWhiteSpace($model)) {
        continue
    }

    Write-Host "Pulling $model"
    Invoke-OllamaPull -Model $model.Trim()
    Write-Host "Pulled $model"
}

Write-Host "Model pull complete."
