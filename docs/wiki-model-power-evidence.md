# Model Power and Electricity Evidence

This page explains what Haven 42 has measured so far and, just as importantly,
what those numbers do **not** mean. It is written for people deciding which
local model may fit their computer and electricity budget.

## Current measurements

| Graphics hardware | Exact model and runtime | What was measured | Result | Evidence status |
| --- | --- | --- | --- | --- |
| Two NVIDIA Tesla V100 32 GiB cards | Nemotron 3.5 Lightning 30B-A3B Q4_K_M · Ollama 0.32.9 | Combined board power during a five-minute three-task workload | 155.005 W average, 280.01 W peak, 12.932521 Wh | Exact-profile engineering evidence |
| Two NVIDIA Tesla V100 32 GiB cards | Nemotron 3.5 Lightning 30B-A3B Q8_0 · Ollama 0.32.9 | Combined board power during a five-minute three-task workload | 141.373 W average, 369.20 W peak, 11.852012 Wh | Exact-profile engineering evidence |
| Intel Arc B580 12 GiB | Granite 4.1 8B Q4_K_M · llama.cpp b10375 SYCL | Card energy during active inference; broader soak average includes idle time | 463.334 J active energy; 34.933 W broader-run average | Exact-profile engineering evidence |
| AMD Radeon RX 7800 XT 16 GiB | Qwen 3.5 9B Q4_K_M · Ollama 0.32.5 | Adrenalin GPU board power across a 30-minute soak | 40.084 W average, 261 W peak, 20.142 Wh; 15.882 W idle-adjusted average | Accepted exact-profile energy measurement |

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
- [Intel Arc B580 Granite evidence](Intel-B580-Granite41-8B-Validation)
- [AMD RX 7800 XT power evidence](Windows-AMD-RX7800XT-Power-Validation)
- [Full model and hardware test status](Model-And-Hardware-Test-Status)

No measurement on this page changes Haven 42's automatic model selection.
Automatic recommendations require the remaining task, reliability, package,
and owner-approval gates.
