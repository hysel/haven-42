# Radeon RX 6800 Ubuntu model qualification

On August 22, 2026, Haven 42 tested a Radeon RX 6800 non-XT 16 GB on Ubuntu
26.04 with the RADV Vulkan driver from Mesa 26.0.8 and an isolated Ollama
0.32.14 runtime.

This result applies only to the exact operating system, runtime, model
artifacts, and graphics profile recorded here. It does not establish Windows
support, every RX 6800 board, ROCm behavior, packaged Haven 42 lifecycle, or an
automatic model choice.

## Results

Every candidate ran three checks each for Chat, Writing, and Summarization.
Each model that passed all three gates then completed its own 30-minute
mixed-task soak with a verified unload after every response.

| Exact candidate | Task gate | 30-minute soak | Samples passed | Average speed |
| --- | --- | --- | ---: | ---: |
| Llama 3.2 3B Q4_K_M | Passed | Passed | 39 | 175.317 tokens/s |
| Gemma 4 E2B QAT | Passed | Passed | 36 | 165.463 tokens/s |
| Granite 4.1 3B Q4_K_M | Passed | Passed | 42 | 156.402 tokens/s |
| Phi-4 Mini 3.8B Q4_K_M | Passed | Passed | 39 | 150.489 tokens/s |
| Gemma 3 4B Q4_K_M | Passed | Passed | 36 | 133.619 tokens/s |
| Gemma 4 E4B QAT | Passed | Passed | 36 | 106.934 tokens/s |
| Granite 4.1 8B Q4_K_M | Passed | Passed | 39 | 83.352 tokens/s |
| Qwen 3.5 9B Q4_K_M | Passed | Passed | 36 | 72.401 tokens/s |
| Gemma 4 12B QAT | Passed | Passed | 36 | 57.679 tokens/s |
| Gemma 3 12B Q4_K_M | Passed | Passed | 36 | 53.806 tokens/s |
| Gemma 3 1B Q4_K_M | Failed Summarization contract | Not run | — | — |
| Ministral 3 3B Q4_K_M | Failed Writing contract | Not run | — | — |
| Ministral 3 8B Q4_K_M | Failed Writing and Summarization contracts | Not run | — | — |

The failure labels describe deterministic Haven 42 task contracts, not a claim
that the model cannot generate text. Failed candidates did not enter soak and
cannot be promoted from this result.

## Telemetry scope

The test retained 3,830 five-second Linux AMD telemetry samples across the base
and 16 GB expansion phases. The observed sensor peak was 208 W, and the highest
reported temperature was 43 °C.

The campaign did not include the standardized idle windows required for Haven
42's end-user electricity-cost evidence. These readings therefore remain
engineering telemetry and are not fed into the cost estimator. They are GPU
board or package sensor readings, not wall power, and exclude the CPU, RAM,
storage, cooling, displays, and power-supply losses.

## Privacy and reproducibility

The machine-readable result binds the exact runtime, model manifests,
qualification matrices, validators, orchestrator, and telemetry streams by
SHA-256. It contains no address, hostname, account name, key, machine ID, raw
prompt, or raw model response.

Windows qualification, comparative human quality review, coding-agent surfaces,
packaged setup and recovery, and a controlled power rerun with the standard idle
baseline remain open. No automatic default or support label changed.
