# GeForce GTX 1650 Super 4 GB Linux model qualification

On August 19, 2026, Haven 42 completed an engineering campaign on Ubuntu
26.04 using a GeForce GTX 1650 Super 4 GB, NVIDIA driver 610.43.02, CUDA,
and an isolated Ollama 0.32.14 runtime. The campaign checked eight exact
model artifacts selected for the new `cuda-4gib-system-16gib` profile.

This is exact-profile engineering evidence. It is not a blanket claim for
every GTX 1650 variant, operating system, driver, runtime, or computer, and
it does not change a Haven 42 automatic default or support label.

## What passed

Each passing model completed three samples apiece for Chat, Writing, and
Summarization, with unload checks after every sample. It then completed its
own 30-minute mixed-task soak.

| Exact candidate | Core task gate | 30-minute soak | Average GPU-board power | Observed peak |
| --- | --- | --- | ---: | ---: |
| Qwen 3.5 0.8B Q8 | Passed | Passed | 13.470 W | 60.67 W |
| Gemma 3 1B Q4 | Passed | Passed | 12.918 W | 65.68 W |
| Granite 4.1 3B Q4 | Passed | Passed | 15.030 W | 102.33 W |
| Llama 3.2 3B Q4 | Passed | Passed | 16.208 W | 103.74 W |
| MiniCPM V 4.6 1B Q4 | Passed | Passed | 12.585 W | 48.88 W |

## What was stopped

Qwen 3.5 2B Q8, Phi-4 Mini 3.8B Q4, and Ministral 3 3B Q4 reached the
first Chat sample but did not show full CUDA residency. The fail-closed
validator stopped each candidate before its remaining task samples and soak.
This is a 4 GB hardware-fit boundary, not evidence that those models are
generally defective. They remain candidates for hardware with more usable
GPU memory.

## Power scope

The campaign recorded 9,879 one-second `nvidia-smi` samples. Five minutes
before testing averaged 8.360 W and five minutes after testing averaged
8.203 W. The passing soak windows averaged 12.585–16.208 W and observed
peaks of 48.88–103.74 W.

These readings are GPU-board power, not wall power. They exclude the CPU,
RAM, storage, cooling, display, and power-supply losses. A model's 30-minute
window includes generation, unload checks, and idle time between samples, so
it should not be read as continuous maximum-load consumption.

## Reproducibility and privacy

The machine-readable result binds the exact inventory, qualification matrix,
validators, and executed campaign orchestrator by SHA-256. The public record
contains no host address, hostname, key, machine ID, PCI address, raw prompt,
or raw model response.

Remaining work includes packaged Haven 42 lifecycle validation, Windows on
this card, coding-agent surfaces, broader quality comparison, and testing on
other 4 GB NVIDIA variants.
