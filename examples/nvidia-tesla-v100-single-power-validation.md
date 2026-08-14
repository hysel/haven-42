# NVIDIA Tesla V100 single-card model power validation

## What was tested

On August 14, 2026, Haven 42 measured one NVIDIA Tesla V100-SXM2 with
32 GiB of graphics memory on Ubuntu 24.04.4 LTS. The exact profile used:

- NVIDIA driver 580.159.04;
- an isolated, loopback-only Ollama 0.32.9 runtime restricted to one V100;
- `qwen3.5:4b` Q4_K_M with manifest digest
  `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`;
- a 120-second idle baseline followed by about 302 seconds of deterministic
  Chat, Writing, and Summarization requests; and
- `nvidia-smi` graphics-board telemetry sampled every two seconds.

The residency check showed the model on the selected V100 before timing began.
The normal two-card service was not stopped or reconfigured, and the second
V100 was not part of this measurement.

## Measured result

| Scope | Average | Peak | Energy |
| --- | ---: | ---: | ---: |
| Idle baseline | 30.568 W | — | — |
| Active workload | 152.509 W | 184.39 W | 12.777600 Wh |
| Idle-adjusted active workload | 121.941 W | — | 10.216524 Wh |

The model produced 18,688 output tokens at an average 61.959 tokens per
second and 1,462.559 output tokens per measured graphics-board watt-hour.
Peak reported graphics memory was 4,179 MiB, average GPU utilization was
54.85%, and peak temperature was 68 °C.

| Task | Average board power | Peak board power | Output tokens per Wh |
| --- | ---: | ---: | ---: |
| Chat | 151.202 W | 181.67 W | 1,469.230 |
| Writing | 152.258 W | 180.83 W | 1,470.734 |
| Summarization | 156.166 W | 184.39 W | 1,429.944 |

## How to read this result

These are graphics-board readings, not whole-computer power. They exclude the
CPU, system memory, storage, cooling, display, and power-supply losses. The
figures apply only to this exact card, driver, operating system, runtime,
model artifact, and workload.

This result should not be ranked directly against the Quadro or dual-V100
records because their operating systems, drivers, runtimes, model artifacts,
or workloads differ. It closes the missing single-card V100 reference; it
does not make the earlier two-card measurements interchangeable with this one.

The harness verified the reviewed script hashes, exact runtime and model
digest, one-card residency, idle provider state, model unload, isolated-process
shutdown, loopback-port closure, and return to zero model memory on the tested
V100. No prompt, response, machine identity, account, network address, or local
path is included, and this evidence does not change automatic model selection.

The complete sanitized record is
[`examples/fixtures/nvidia-tesla-v100-qwen35-4b-single-energy.json`](https://github.com/hysel/haven-42/blob/main/examples/fixtures/nvidia-tesla-v100-qwen35-4b-single-energy.json).
