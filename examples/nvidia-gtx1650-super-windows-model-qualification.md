# GeForce GTX 1650 Super 4 GB Windows model qualification

On August 19–20, 2026, Haven 42 completed an engineering campaign on
Windows 11 using a GeForce GTX 1650 Super 4 GB, NVIDIA driver 610.88, CUDA,
and an isolated Ollama 0.32.14 runtime. The campaign checked the same eight
exact model artifacts used for the Ubuntu `cuda-4gib-system-16gib` campaign.

This is exact-profile engineering evidence. It is not a blanket claim for
every GTX 1650 variant, operating system, driver, runtime, or computer. It
does not change a Haven 42 automatic default or support label. It may be used
only to filter the model choices shown for this exact hardware, operating
system, and runtime profile.

## What passed

Each passing model completed three samples apiece for Chat, Writing, and
Summarization, with unload checks after every sample. It then completed its
own 30-minute mixed-task soak.

| Exact candidate | Core task gate | 30-minute soak | Average GPU-board power | Observed peak |
| --- | --- | --- | ---: | ---: |
| Qwen 3.5 0.8B Q8 | Passed | Passed | 13.843 W | 67.28 W |
| Gemma 3 1B Q4 | Passed | Passed | 13.264 W | 57.27 W |
| MiniCPM V 4.6 1B Q4 | Passed | Passed | 13.058 W | 50.35 W |

## What was stopped

Qwen 3.5 2B Q8, Granite 4.1 3B Q4, Phi-4 Mini 3.8B Q4, Llama 3.2 3B Q4,
and Ministral 3 3B Q4 reached the first Chat sample but did not show full
CUDA residency. The fail-closed validator stopped each candidate before its
remaining task samples and soak. This is a 4 GB Windows hardware-fit boundary,
not evidence that those models are generally defective. The same artifact
may have a different result on another operating system, driver, or GPU.

## Power scope

The campaign recorded 6,437 one-second `nvidia-smi` samples. Five minutes
before testing averaged 8.210 W and five minutes after testing averaged
8.170 W. Passing soak windows averaged 13.058–13.843 W and observed peaks
of 50.35–67.28 W.

These readings are GPU-board power, not wall power. They exclude the CPU,
RAM, storage, cooling, display, and power-supply losses. A model's 30-minute
window includes generation, unload checks, and idle time between samples, so
it should not be read as continuous maximum-load consumption.

## Reproducibility and privacy

The machine-readable result binds the exact inventory, qualification matrix,
and validators by SHA-256. The executed controller is retained outside the
repository because it contained private connection material; the public
record instead binds the sanitized telemetry and records the bounded event
times and protocol. No host address, hostname, key, machine ID, PCI address,
raw prompt, or raw model response is published.

Remaining work includes packaged Haven 42 lifecycle validation, coding-agent
surfaces, broader quality comparison, and testing on other 4 GB NVIDIA cards.
