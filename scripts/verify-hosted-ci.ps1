param(
    [string]$Repository,
    [string]$CommitSha,
    [string]$Workflow = "Validate Pack",
    [long]$RunId,
    [int]$DiscoveryTimeoutSeconds = 300,
    [int]$PollIntervalSeconds = 10
)

$ErrorActionPreference = "Stop"

$requiredJobs = @(
    "Wiki synchronization",
    "Windows PowerShell validation",
    "Linux script smoke tests",
    "macOS script smoke tests"
)

function Resolve-GhCommand {
    $command = Get-Command gh -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $fallback = Join-Path $env:ProgramFiles "GitHub CLI/gh.exe"
    if (Test-Path -LiteralPath $fallback) {
        return $fallback
    }

    throw "GitHub CLI was not found. Install gh and authenticate with 'gh auth login'."
}

function Invoke-Gh {
    param(
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    $output = & $script:ghCommand @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "gh $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = @($output)
        Text = ($output -join [Environment]::NewLine)
    }
}

function Write-State {
    param(
        [ValidateSet("Pushed", "CI running", "CI passed", "CI failed")]
        [string]$State,
        [string]$Sha,
        [string]$Url
    )

    Write-Host "State: $State"
    Write-Host "Commit: $Sha"
    if ($Url) {
        Write-Host "Run: $Url"
    }
}

$script:ghCommand = Resolve-GhCommand

Invoke-Gh -Arguments @("auth", "status") | Out-Null

if (-not $Repository) {
    $Repository = (Invoke-Gh -Arguments @("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")).Text.Trim()
}

if (-not $CommitSha) {
    $CommitSha = (& git rev-parse HEAD 2>&1 | Select-Object -First 1).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "CommitSha was not supplied and the current Git commit could not be resolved."
    }
}

if ($CommitSha -notmatch "^[0-9a-fA-F]{40}$") {
    throw "CommitSha must be a full 40-character Git commit SHA."
}

Write-State -State "Pushed" -Sha $CommitSha

if (-not $RunId) {
    $deadline = [DateTime]::UtcNow.AddSeconds($DiscoveryTimeoutSeconds)
    do {
        $runsJson = (Invoke-Gh -Arguments @(
            "run", "list",
            "--repo", $Repository,
            "--workflow", $Workflow,
            "--commit", $CommitSha,
            "--event", "push",
            "--limit", "20",
            "--json", "databaseId,headSha,status,conclusion,url,createdAt"
        )).Text
        $runs = @($runsJson | ConvertFrom-Json)
        $matchingRun = $runs |
            Where-Object { $_.headSha -eq $CommitSha } |
            Sort-Object createdAt -Descending |
            Select-Object -First 1

        if ($matchingRun) {
            $RunId = [long]$matchingRun.databaseId
            break
        }

        if ([DateTime]::UtcNow -lt $deadline) {
            Start-Sleep -Seconds $PollIntervalSeconds
        }
    } while ([DateTime]::UtcNow -lt $deadline)
}

if (-not $RunId) {
    Write-State -State "CI failed" -Sha $CommitSha
    throw "No '$Workflow' push run appeared for exact commit $CommitSha within $DiscoveryTimeoutSeconds seconds."
}

$initialView = (Invoke-Gh -Arguments @(
    "run", "view", "$RunId", "--repo", $Repository,
    "--json", "headSha,status,conclusion,url"
)).Text | ConvertFrom-Json

if ($initialView.headSha -ne $CommitSha) {
    Write-State -State "CI failed" -Sha $CommitSha -Url $initialView.url
    throw "Run $RunId belongs to $($initialView.headSha), not exact commit $CommitSha."
}

Write-State -State "CI running" -Sha $CommitSha -Url $initialView.url
$watch = Invoke-Gh -Arguments @("run", "watch", "$RunId", "--repo", $Repository, "--exit-status") -AllowFailure

$view = (Invoke-Gh -Arguments @(
    "run", "view", "$RunId", "--repo", $Repository,
    "--json", "headSha,status,conclusion,url,jobs"
)).Text | ConvertFrom-Json

$failureReasons = [System.Collections.Generic.List[string]]::new()
if ($view.headSha -ne $CommitSha) {
    $failureReasons.Add("Hosted run SHA '$($view.headSha)' does not match '$CommitSha'.")
}
if ($watch.ExitCode -ne 0) {
    $failureReasons.Add("gh run watch --exit-status returned $($watch.ExitCode).")
}
if ($view.status -ne "completed" -or $view.conclusion -ne "success") {
    $failureReasons.Add("Workflow status is '$($view.status)' with conclusion '$($view.conclusion)'.")
}

foreach ($requiredJob in $requiredJobs) {
    $job = @($view.jobs | Where-Object { $_.name -eq $requiredJob }) | Select-Object -First 1
    if (-not $job) {
        $failureReasons.Add("Required job '$requiredJob' was not present.")
    }
    elseif ($job.status -ne "completed" -or $job.conclusion -ne "success") {
        $failureReasons.Add("Required job '$requiredJob' ended with status '$($job.status)' and conclusion '$($job.conclusion)'.")
    }
}

if ($failureReasons.Count -gt 0) {
    Write-State -State "CI failed" -Sha $CommitSha -Url $view.url
    $failureReasons | ForEach-Object { Write-Host "ERROR $_" -ForegroundColor Red }
    Write-Host "Failed GitHub Actions logs:"
    $failedLogs = Invoke-Gh -Arguments @("run", "view", "$RunId", "--repo", $Repository, "--log-failed") -AllowFailure
    if ($failedLogs.Text) {
        Write-Host $failedLogs.Text
    }
    exit 1
}

Write-State -State "CI passed" -Sha $CommitSha -Url $view.url
Write-Host "Required jobs:"
$requiredJobs | ForEach-Object { Write-Host "- ${_}: success" }
