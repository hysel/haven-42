param(
    [switch]$AsJson,
    [string]$ModelCatalogPath
)

$ErrorActionPreference = "Stop"

function Get-CommandOutput {
    param(
        [string]$Command,
        [string[]]$Arguments = @()
    )

    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        return @()
    }

    try {
        return & $Command @Arguments 2>$null
    }
    catch {
        return @()
    }
}

function Convert-BytesToGb {
    param([double]$Bytes)

    if (-not $Bytes -or $Bytes -le 0) {
        return $null
    }

    return [math]::Round($Bytes / 1GB, 1)
}

function Convert-MbToGb {
    param([double]$Mb)

    if (-not $Mb -or $Mb -le 0) {
        return $null
    }

    return [math]::Round($Mb / 1024, 1)
}

function Get-GpuVendor {
    param([string]$Name)

    if ($Name -match "(?i)nvidia") {
        return "NVIDIA"
    }

    if ($Name -match "(?i)(amd|radeon|advanced micro devices)") {
        return "AMD"
    }

    if ($Name -match "(?i)intel") {
        return "Intel"
    }

    if ($Name -match "(?i)apple") {
        return "Apple"
    }

    return "Unknown"
}

function Get-GpuMemoryType {
    param(
        [string]$Vendor,
        [Nullable[double]]$VramGb
    )

    if ($Vendor -eq "Intel") {
        return "shared or integrated"
    }

    if ($Vendor -eq "Apple") {
        return "unified"
    }

    if ($null -ne $VramGb) {
        return "dedicated"
    }

    return "unknown"
}

function Get-PlatformName {
    if ($IsWindows) {
        return "Windows"
    }

    if ($IsLinux) {
        return "Linux"
    }

    if ($IsMacOS) {
        return "macOS"
    }

    return "Unknown"
}

function Get-OperatingSystemSummary {
    if ($PSVersionTable.OS) {
        return $PSVersionTable.OS
    }

    return (Get-PlatformName)
}

function Get-SystemRamGb {
    if ($IsWindows) {
        try {
            $system = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
            return Convert-BytesToGb -Bytes ([double]$system.TotalPhysicalMemory)
        }
        catch {
            return $null
        }
    }

    if ($IsLinux -and (Test-Path -LiteralPath "/proc/meminfo")) {
        $memInfo = Get-Content -LiteralPath "/proc/meminfo" -ErrorAction SilentlyContinue
        $memTotal = $memInfo | Where-Object { $_ -match "^MemTotal:\s+(\d+)\s+kB" } | Select-Object -First 1
        if ($memTotal -match "^MemTotal:\s+(\d+)\s+kB") {
            return Convert-BytesToGb -Bytes ([double]$Matches[1] * 1024)
        }
    }

    if ($IsMacOS) {
        $memBytes = Get-CommandOutput -Command "sysctl" -Arguments @("-n", "hw.memsize") | Select-Object -First 1
        if ($memBytes -match "^\d+$") {
            return Convert-BytesToGb -Bytes ([double]$memBytes)
        }
    }

    return $null
}

function Get-CpuSummary {
    if ($IsWindows) {
        try {
            $cpu = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop | Select-Object -First 1
            if ($cpu) {
                return "$($cpu.Name.Trim()) ($($cpu.NumberOfLogicalProcessors) logical processors)"
            }
        }
        catch {
            return "Unknown"
        }
    }

    if ($IsLinux) {
        $lscpu = Get-CommandOutput -Command "lscpu"
        $model = ($lscpu | Where-Object { $_ -match "^Model name:\s+(.+)$" } | Select-Object -First 1)
        $cpus = ($lscpu | Where-Object { $_ -match "^CPU\(s\):\s+(.+)$" } | Select-Object -First 1)

        $modelText = if ($model -match "^Model name:\s+(.+)$") { $Matches[1].Trim() } else { "Unknown CPU" }
        $cpuText = if ($cpus -match "^CPU\(s\):\s+(.+)$") { $Matches[1].Trim() } else { "unknown" }
        return "$modelText ($cpuText logical processors)"
    }

    if ($IsMacOS) {
        $brand = Get-CommandOutput -Command "sysctl" -Arguments @("-n", "machdep.cpu.brand_string") | Select-Object -First 1
        $logical = Get-CommandOutput -Command "sysctl" -Arguments @("-n", "hw.logicalcpu") | Select-Object -First 1

        if (-not $brand) {
            $brand = Get-CommandOutput -Command "sysctl" -Arguments @("-n", "hw.model") | Select-Object -First 1
        }

        if ($brand) {
            return "$($brand.Trim()) ($logical logical processors)"
        }
    }

    return "Unknown"
}

function Get-NvidiaGpuProfiles {
    $rows = Get-CommandOutput -Command "nvidia-smi" -Arguments @("--query-gpu=name,memory.total", "--format=csv,noheader,nounits")
    $profiles = New-Object System.Collections.Generic.List[object]

    foreach ($row in $rows) {
        if ($row -match "^\s*(.+?)\s*,\s*(\d+)\s*$") {
            $profiles.Add([pscustomobject]@{
                Name = $Matches[1].Trim()
                VramGb = Convert-MbToGb -Mb ([double]$Matches[2])
                Source = "nvidia-smi"
                Vendor = "NVIDIA"
                MemoryType = "dedicated"
            })
        }
    }

    return $profiles
}

function Get-RocmGpuProfiles {
    $rows = Get-CommandOutput -Command "rocm-smi" -Arguments @("--showproductname", "--showmeminfo", "vram")
    $profilesByIndex = @{}

    foreach ($row in $rows) {
        if ($row -match "GPU\[(\d+)\].*?(Card series|Card model|Product Name|Marketing Name)\s*:\s*(.+)$") {
            $index = $Matches[1]
            if (-not $profilesByIndex.ContainsKey($index)) {
                $profilesByIndex[$index] = @{
                    Name = "AMD GPU $index"
                    VramGb = $null
                }
            }

            $profilesByIndex[$index].Name = $Matches[3].Trim()
        }

        if ($row -match "GPU\[(\d+)\].*?VRAM Total Memory.*?:\s*([0-9.]+)\s*(B|KB|MB|GB)?") {
            $index = $Matches[1]
            $value = [double]$Matches[2]
            $unit = $Matches[3]

            if (-not $profilesByIndex.ContainsKey($index)) {
                $profilesByIndex[$index] = @{
                    Name = "AMD GPU $index"
                    VramGb = $null
                }
            }

            if ($unit -eq "GB") {
                $profilesByIndex[$index].VramGb = $value
            } elseif ($unit -eq "MB") {
                $profilesByIndex[$index].VramGb = Convert-MbToGb -Mb $value
            } elseif ($unit -eq "KB") {
                $profilesByIndex[$index].VramGb = Convert-BytesToGb -Bytes ($value * 1024)
            } else {
                $profilesByIndex[$index].VramGb = Convert-BytesToGb -Bytes $value
            }
        }
    }

    $profiles = New-Object System.Collections.Generic.List[object]
    foreach ($key in ($profilesByIndex.Keys | Sort-Object)) {
        $profiles.Add([pscustomobject]@{
            Name = $profilesByIndex[$key].Name
            VramGb = $profilesByIndex[$key].VramGb
            Source = "rocm-smi"
            Vendor = "AMD"
            MemoryType = "dedicated"
        })
    }

    return $profiles
}

function Convert-RegistryString {
    param($Value)

    if ($Value -is [byte[]]) {
        return ([System.Text.Encoding]::Unicode.GetString($Value)).Trim([char]0).Trim()
    }

    if ($Value) {
        return ([string]$Value).Trim()
    }

    return $null
}

function Get-WindowsRegistryGpuProfiles {
    $profiles = New-Object System.Collections.Generic.List[object]
    $registryRoot = "HKLM:\SYSTEM\CurrentControlSet\Control\Video"

    if (-not (Test-Path -LiteralPath $registryRoot)) {
        return $profiles
    }

    $seen = @{}

    try {
        $keys = Get-ChildItem -LiteralPath $registryRoot -Recurse -ErrorAction SilentlyContinue
        foreach ($key in $keys) {
            $properties = Get-ItemProperty -LiteralPath $key.PSPath -ErrorAction SilentlyContinue
            if (-not $properties) {
                continue
            }

            $memoryProperty = $properties.PSObject.Properties["HardwareInformation.qwMemorySize"]
            if (-not $memoryProperty -or -not $memoryProperty.Value) {
                continue
            }

            $adapterProperty = $properties.PSObject.Properties["HardwareInformation.AdapterString"]
            $chipProperty = $properties.PSObject.Properties["HardwareInformation.ChipType"]
            $adapterName = Convert-RegistryString -Value $adapterProperty.Value
            $chipName = Convert-RegistryString -Value $chipProperty.Value
            $name = if ($adapterName) { $adapterName } elseif ($chipName) { $chipName } else { "Windows display adapter" }
            $vramGb = Convert-BytesToGb -Bytes ([double]$memoryProperty.Value)
            $dedupeKey = "$name|$vramGb"

            if (-not $seen.ContainsKey($dedupeKey)) {
                $vendor = Get-GpuVendor -Name $name
                $profiles.Add([pscustomobject]@{
                    Name = $name
                    VramGb = $vramGb
                    Source = "Windows display registry"
                    Vendor = $vendor
                    MemoryType = Get-GpuMemoryType -Vendor $vendor -VramGb $vramGb
                })
                $seen[$dedupeKey] = $true
            }
        }
    }
    catch {
        return $profiles
    }

    return $profiles
}

function Get-PlatformGpuProfiles {
    $profiles = New-Object System.Collections.Generic.List[object]

    if ($IsWindows) {
        $registryProfiles = Get-WindowsRegistryGpuProfiles
        if ($registryProfiles.Count -gt 0) {
            return $registryProfiles
        }

        try {
            $controllers = Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop
            foreach ($controller in $controllers) {
                $adapterRam = $null
                if ($controller.AdapterRAM -and [double]$controller.AdapterRAM -gt 0) {
                    $adapterRamBytes = [double]$controller.AdapterRAM

                    if ($adapterRamBytes -lt 4290000000) {
                        $adapterRam = Convert-BytesToGb -Bytes $adapterRamBytes
                    }
                }

                $vendor = Get-GpuVendor -Name $controller.Name
                $profiles.Add([pscustomobject]@{
                    Name = $controller.Name
                    VramGb = $adapterRam
                    Source = "Win32_VideoController"
                    Vendor = $vendor
                    MemoryType = Get-GpuMemoryType -Vendor $vendor -VramGb $adapterRam
                })
            }
        }
        catch {
            return $profiles
        }
    }

    if ($IsLinux) {
        $gpuRows = Get-CommandOutput -Command "lspci" |
            Where-Object { $_ -match "(?i)(vga compatible controller|3d controller|display controller)" }

        foreach ($row in $gpuRows) {
            $name = ($row -replace "^\S+\s+", "").Trim()
            $vendor = Get-GpuVendor -Name $name
            $profiles.Add([pscustomobject]@{
                Name = $name
                VramGb = $null
                Source = "lspci"
                Vendor = $vendor
                MemoryType = Get-GpuMemoryType -Vendor $vendor -VramGb $null
            })
        }
    }

    if ($IsMacOS) {
        $displayInfo = Get-CommandOutput -Command "system_profiler" -Arguments @("SPDisplaysDataType")
        $currentName = $null

        foreach ($line in $displayInfo) {
            if ($line -match "^\s*Chipset Model:\s*(.+)$") {
                $currentName = $Matches[1].Trim()
            }

            if ($currentName -and $line -match "^\s*(VRAM|Total Number of Cores):\s*(.+)$") {
                $value = $Matches[2].Trim()
                $vram = $null

                if ($value -match "(\d+)\s*MB") {
                    $vram = Convert-MbToGb -Mb ([double]$Matches[1])
                } elseif ($value -match "(\d+)\s*GB") {
                    $vram = [double]$Matches[1]
                }

                $vendor = Get-GpuVendor -Name $currentName
                $profiles.Add([pscustomobject]@{
                    Name = $currentName
                    VramGb = $vram
                    Source = "system_profiler"
                    Vendor = $vendor
                    MemoryType = Get-GpuMemoryType -Vendor $vendor -VramGb $vram
                })

                $currentName = $null
            }
        }
    }

    return $profiles
}

function Get-GpuProfiles {
    $nvidiaProfiles = Get-NvidiaGpuProfiles
    if ($nvidiaProfiles.Count -gt 0) {
        return $nvidiaProfiles
    }

    $rocmProfiles = Get-RocmGpuProfiles
    if ($rocmProfiles.Count -gt 0) {
        return $rocmProfiles
    }

    return Get-PlatformGpuProfiles
}

function Get-OllamaModels {
    $rows = Get-CommandOutput -Command "ollama" -Arguments @("list")
    $models = New-Object System.Collections.Generic.List[string]

    foreach ($row in ($rows | Select-Object -Skip 1)) {
        if ($row -match "^\s*(\S+)") {
            $models.Add($Matches[1])
        }
    }

    return $models | Sort-Object -Unique
}

function Get-OllamaStatus {
    if (-not (Get-Command "ollama" -ErrorAction SilentlyContinue)) {
        return "ollama command not found"
    }

    $rows = Get-CommandOutput -Command "ollama" -Arguments @("list")
    if ($rows -and $rows.Count -gt 0) {
        return "reachable"
    }

    return "installed but not reachable or no models listed"
}

function Get-RecommendationTier {
    param(
        [Nullable[double]]$RamGb,
        [object[]]$GpuProfiles
    )

    $maxVram = $null
    $knownVram = $GpuProfiles |
        Where-Object { $null -ne $_.VramGb } |
        ForEach-Object { [double]$_.VramGb }

    if ($knownVram) {
        $maxVram = ($knownVram | Measure-Object -Maximum).Maximum
    }

    if ($RamGb -ge 32 -and (($maxVram -and $maxVram -ge 16) -or -not $maxVram)) {
        return "High resource candidate"
    }

    if (($RamGb -ge 16 -and $RamGb -lt 32) -or ($maxVram -and $maxVram -ge 8)) {
        return "Medium resource candidate"
    }

    return "Low resource candidate"
}

function Find-InstalledModel {
    param(
        [string[]]$Models,
        [string[]]$Patterns
    )

    foreach ($pattern in $Patterns) {
        $match = $Models | Where-Object { $_ -match $pattern } | Select-Object -First 1
        if ($match) {
            return $match
        }
    }

    return $null
}

function Get-ModelRecommendation {
    param(
        [string]$Tier,
        [string[]]$Models,
        [string]$CatalogPath
    )

    $tierName = if ($Tier -match "^High") { "High" } elseif ($Tier -match "^Medium") { "Medium" } else { "Low" }
    $fallback = $null

    if (Test-Path -LiteralPath $CatalogPath) {
        $rows = Get-Content -LiteralPath $CatalogPath
        foreach ($row in $rows) {
            if (-not $row -or $row.StartsWith("#")) {
                continue
            }

            $parts = $row -split "\|", 5
            if ($parts.Count -lt 5 -or $parts[0] -ne $tierName) {
                continue
            }

            $pattern = $parts[1]
            $fallbackModel = $parts[2]
            $use = $parts[3]
            $validation = $parts[4]

            if ($pattern) {
                $model = Find-InstalledModel -Models $Models -Patterns @("(?i)$pattern")
                if ($model) {
                    return [pscustomobject]@{
                        PrimaryModel = $model
                        Use = $use
                        Validation = $validation
                    }
                }
            } elseif (-not $fallback) {
                $fallback = [pscustomobject]@{
                    PrimaryModel = $fallbackModel
                    Use = $use
                    Validation = $validation
                }
            }
        }
    }

    if ($fallback) {
        return $fallback
    }

    return [pscustomobject]@{
        PrimaryModel = "qwen3-coder:30b"
        Use = "Validate the model against the target workflow before relying on it."
        Validation = "Run read-only discovery and tool-call validation before approved write mode."
    }
}

if (-not $ModelCatalogPath) {
    $ModelCatalogPath = Join-Path (Split-Path -Parent $PSScriptRoot) "config/model-recommendations.tsv"
}

$gpuProfiles = @(Get-GpuProfiles)
$ramGb = Get-SystemRamGb
$ollamaModels = @(Get-OllamaModels)
$recommendationTier = Get-RecommendationTier -RamGb $ramGb -GpuProfiles $gpuProfiles
$modelRecommendation = Get-ModelRecommendation -Tier $recommendationTier -Models $ollamaModels -CatalogPath $ModelCatalogPath

$profile = [pscustomobject]@{
    GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm"
    Platform = Get-PlatformName
    OperatingSystem = Get-OperatingSystemSummary
    PowerShellVersion = $PSVersionTable.PSVersion.ToString()
    SystemRamGb = $ramGb
    Cpu = Get-CpuSummary
    Gpus = $gpuProfiles
    OllamaStatus = Get-OllamaStatus
    OllamaModels = $ollamaModels
    RecommendationTier = $recommendationTier
    ModelRecommendation = $modelRecommendation
}

if ($AsJson) {
    $profile | ConvertTo-Json -Depth 5
    return
}

Write-Host "Local Model Profile" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated: $($profile.GeneratedAt)"
Write-Host "Platform: $($profile.Platform)"
Write-Host "OS: $($profile.OperatingSystem)"
Write-Host "PowerShell: $($profile.PowerShellVersion)"
Write-Host "RAM: $(if ($profile.SystemRamGb) { "$($profile.SystemRamGb) GB" } else { "Unknown" })"
Write-Host "CPU: $($profile.Cpu)"
Write-Host ""
Write-Host "GPU:"
if ($profile.Gpus.Count -gt 0) {
    foreach ($gpu in $profile.Gpus) {
        $vram = if ($null -ne $gpu.VramGb) { "$($gpu.VramGb) GB" } else { "Unknown VRAM" }
        Write-Host "- $($gpu.Name) ($vram, $($gpu.Source), $($gpu.Vendor), $($gpu.MemoryType))"
    }
} else {
    Write-Host "- Not detected"
}

Write-Host ""
Write-Host "Ollama: $($profile.OllamaStatus)"
if ($profile.OllamaModels.Count -gt 0) {
    Write-Host "Installed Ollama models:"
    foreach ($model in $profile.OllamaModels) {
        Write-Host "- $model"
    }
} else {
    Write-Host "Installed Ollama models: None detected"
}

Write-Host ""
Write-Host "Recommendation tier: $($profile.RecommendationTier)"
Write-Host "Recommended model: $($profile.ModelRecommendation.PrimaryModel)"
Write-Host "Recommended use: $($profile.ModelRecommendation.Use)"
Write-Host "Validation note: $($profile.ModelRecommendation.Validation)"
Write-Host ""
Write-Host "Use docs/local-model-selection.md to choose the final model. This helper does not collect hostnames, IP addresses, usernames, or local paths."
