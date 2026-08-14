# NVIDIA Quadro RTX 5000 model power validation

## What was tested

On August 14, 2026, Haven 42 measured one NVIDIA Quadro RTX 5000 with
16 GiB of graphics memory on Ubuntu 26.04 LTS. The exact test profile used:

- NVIDIA driver 595.84;
- the existing isolated Ollama 0.32.5 runtime;
- `qwen3.5:4b` with manifest digest
  `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`;
- a 120-second idle baseline followed by 300 seconds of deterministic Chat,
  Writing, and Summarization requests; and
- `nvidia-smi` graphics-board telemetry sampled every two seconds.

The run produced 129 successful requests: 43 for each task. It retained no
prompt, response, machine name, account, network address, or local path.

## Measured result

| Scope | Average | Peak | Energy |
| --- | ---: | ---: | ---: |
| Idle baseline | 20.041 W | — | — |
| Five-minute active workload | 151.060 W | 192.24 W | 12.595845 Wh |
| Idle-adjusted active workload | 131.018 W | — | 10.924745 Wh |

The model produced 16,512 output tokens at an average 55.007 tokens per
second and 1,310.909 output tokens per measured graphics-board watt-hour.
Peak reported graphics memory was 3,963 MiB, average GPU utilization was
53.75%, and peak graphics temperature was 71 °C.

| Task | Average board power | Peak board power | Output tokens per Wh |
| --- | ---: | ---: | ---: |
| Chat | 154.013 W | 188.58 W | 1,283.676 |
| Writing | 149.919 W | 190.52 W | 1,324.095 |
| Summarization | 149.308 W | 192.24 W | 1,326.475 |

## How to read this result

These are graphics-board readings, not whole-computer power. They exclude the
CPU, system memory, storage, cooling, display, and power-supply losses. The
figures apply only to this exact card, driver, operating system, runtime, model
artifact, and workload; they are not the card's universal power use.

The harness verified the exact runtime and model digest, required the provider
to be idle before the baseline, unloaded the model afterward, stopped only the
recorded Ollama process, confirmed loopback-port closure, removed the temporary
campaign files, and verified graceful VM shutdown. This evidence does not
change Haven 42's automatic model selection.

The complete sanitized record is
[`examples/fixtures/nvidia-quadro-rtx5000-qwen35-4b-energy.json`](https://github.com/hysel/haven-42/blob/main/examples/fixtures/nvidia-quadro-rtx5000-qwen35-4b-energy.json).
