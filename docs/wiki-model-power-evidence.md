# Model Power and Electricity Evidence

This page explains what Haven 42 has measured so far and, just as importantly,
what those numbers do **not** mean. It is written for people deciding which
local model may fit their computer and electricity budget.

## Current measurements

| Graphics hardware | Exact model and runtime | What was measured | Result | Evidence status |
| --- | --- | --- | --- | --- |
| Two NVIDIA Tesla V100 32 GiB cards | Nemotron 3.5 Lightning 30B-A3B Q4_K_M · Ollama 0.32.9 | Combined board power during a five-minute three-task workload | 155.005 W average, 280.01 W peak, 12.932521 Wh | Exact-profile engineering evidence |
| Two NVIDIA Tesla V100 32 GiB cards | Nemotron 3.5 Lightning 30B-A3B Q8_0 · Ollama 0.32.9 | Combined board power during a five-minute three-task workload | 141.373 W average, 369.20 W peak, 11.852012 Wh | Exact-profile engineering evidence |
| One NVIDIA Tesla V100 32 GiB card | Qwen 3.5 4B Q4_K_M · Ollama 0.32.9 | Board power during a two-minute idle baseline and five-minute three-task workload | 152.509 W active average, 184.39 W peak, 12.777600 Wh; 121.941 W idle-adjusted average | Accepted exact-profile energy measurement |
| NVIDIA Quadro RTX 5000 16 GiB | Qwen 3.5 4B Q4_K_M · Ollama 0.32.5 | Board power during a two-minute idle baseline and five-minute three-task workload | 151.060 W active average, 192.24 W peak, 12.595845 Wh; 131.018 W idle-adjusted average | Accepted exact-profile energy measurement |
| Intel Arc B580 12 GiB | Granite 4.1 8B Q4_K_M · llama.cpp b10375 SYCL | Card energy during active inference; broader soak average includes idle time | 463.334 J active energy; 34.933 W broader-run average | Exact-profile engineering evidence |
| AMD Radeon RX 7800 XT 16 GiB | Qwen 3.5 9B Q4_K_M · Ollama 0.32.5 | Adrenalin GPU board power across a 30-minute soak | 40.084 W average, 261 W peak, 20.142 Wh; 15.882 W idle-adjusted average | Accepted exact-profile energy measurement |
| AMD Radeon RX 5700 XT 8 GiB | Llama 3.2 3B Q4_K_M · Ollama 0.32.13 Vulkan on Ubuntu 26.04 | Linux `power1_average` GPU-board sensor across two-minute idle, ten-minute active, and two-minute cooldown windows | 7.575 W idle average, 122.118 W active average, 242 W peak, 20.350129 Wh active; 2,134.188 output tokens/Wh | Exact-profile engineering evidence |
| NVIDIA GeForce RTX 3060 12 GiB | 19 exact artifacts · Ollama 0.32.14 CUDA on Ubuntu 26.04 | One-second GPU-board telemetry across pre-idle, 19 independent 30-minute mixed-task soaks, and post-idle | 13.962 W pre-idle average, 14.175 W post-idle average; model-window averages 23.577–32.876 W and peaks 56.54–139.18 W | Exact-profile engineering evidence |

## Measurement coverage

Every physical graphics-card model in the Alpha 2 certification inventory
must receive a reference measurement. Pending cards stay visible here so an
unmeasured card cannot be mistaken for a zero-power result or disappear from
the campaign. The machine-readable coverage source is
[`config/alpha-2-gpu-power-coverage.json`](https://github.com/hysel/haven-42/blob/main/config/alpha-2-gpu-power-coverage.json).

| Graphics hardware | Reference measurement | What remains |
| --- | --- | --- |
| GeForce GTX 1650 Super 4 GiB | Pending | Measure the fixed idle and active workload after the purchased card is installed. |
| GeForce RTX 3060 12 GiB | Measured | Separate Windows and Ubuntu 26.04 GPU-board records are available; another operating system, driver, runtime, or workload remains a separate cell. |
| Quadro RTX 5000 16 GiB | Measured | Add another exact-profile record when the model, runtime, driver, workload, or operating system changes. |
| Tesla V100 32 GiB | Measured | Single-card and two-card records are available and remain separate exact-profile measurements. |
| Radeon RX 5700 XT 8 GiB | Measured | The Ubuntu 26.04 Vulkan lane has a reference GPU-board measurement. Windows, ROCm, another driver, or another workload remains a separate cell. |
| Radeon RX 6800 non-XT 16 GiB | Pending | Measure the fixed workload after the purchased card is installed and its exact AMD route passes. |
| Radeon RX 7800 XT 16 GiB | Measured | Repeat only when a runtime, driver, workload, or measurement-method change requires a new exact-profile record. |
| Intel Arc B580 12 GiB | Measured | Add another exact-profile record when the runtime, driver, workload, or operating system changes. |

“Measured” means at least one exact-profile reference exists. It does not make
that number universal for every model, runtime, operating system, or driver.
Where practical, Haven 42 will also measure additional representative models
on the same card; those results remain separate exact-profile records.

## Why the rows should not be ranked directly

These are different models, runtimes, tasks, sampling windows, and graphics
cards. A lower number in this table does not automatically mean that a card or
model is more efficient. For example, the AMD full-soak average includes long
idle gaps and deliberate model unloads, while the Intel active-energy number
focuses on inference windows.

A fair comparison requires the same model artifact, quantization, runtime,
task set, context, sampling method, and test duration on each card. Haven 42
keeps every result tied to its exact profile instead of turning unrelated
measurements into a leaderboard.

## What is included

The listed values are graphics-board or graphics-package readings reported by
the vendor tool. They do not include:

- CPU and system memory;
- storage, fans, and cooling pumps;
- display power;
- power-supply conversion losses;
- the rest of the computer while it is idle.

A wall meter is required for a whole-computer measurement.

## Estimating electricity cost

Use the price per kWh from your own bill when possible. Haven 42 can also make
an explicitly selected estimate from U.S. EIA or Eurostat averages. It never
infers a country from an IP address or converts currencies silently.

The basic GPU-only calculation is:

`average GPU watts ÷ 1000 × hours per day × days × price per kWh`

An estimate is not a utility-bill prediction. Taxes, tiers, time-of-use rates,
fixed charges, and the rest of the computer may change the actual cost.

## Detailed records

- [NVIDIA V100 Nemotron evidence](NVIDIA-V100-Nemotron-Validation)
- [NVIDIA Tesla V100 single-card power evidence](NVIDIA-Tesla-V100-Single-Power-Validation)
- [NVIDIA Quadro RTX 5000 power evidence](NVIDIA-Quadro-RTX5000-Power-Validation)
- [Intel Arc B580 Granite evidence](Intel-B580-Granite41-8B-Validation)
- [AMD RX 7800 XT power evidence](Windows-AMD-RX7800XT-Power-Validation)
- [AMD RX 5700 XT Ubuntu qualification and power evidence](Eng-AMD-RX5700XT-Ollama-03213-Qualification)
- [Full model and hardware test status](Model-And-Hardware-Test-Status)

No measurement on this page changes Haven 42's automatic model selection.
Automatic recommendations require the remaining task, reliability, package,
and owner-approval gates.
