# Radeon RX 7800 XT Ollama 0.32.9 recertification

## What this record proves

On August 15–16, 2026, a Windows 11 development run exercised 17 exact,
manifest-pinned Ollama models on one Radeon RX 7800 XT with 16 GiB of graphics
memory. Each passing model ran for 30 minutes against deterministic Chat,
Writing, and Summarization controls. The runtime reported the ROCm backend and
at least 95% of every loaded model resident on the graphics card.

Fourteen models passed. Three models stopped at the mandatory Summarization
control, so they did not enter a soak and are not recommendation candidates.
This repeats the same three task-control failures seen in the earlier targeted
Ollama 0.32.9 retry.

The run was requested after a firmware rollback intended to address host
stability. The sanitized model files do not retain the firmware identifier,
driver version, computer identity, account name, network address, local path,
prompt, or response. This record therefore proves the exact model/runtime/GPU
outcomes below, but it does not independently attest the firmware or driver.

## Results

| Model | Result | Samples | Average speed | Peak GPU-resident memory | Boundary |
| --- | --- | ---: | ---: | ---: | --- |
| `gemma3:1b-it-q4_K_M` | Passed | 15 | 157.242 tok/s | 0.817 GiB | Full ROCm offload |
| `llama3.2:3b-instruct-q4_K_M` | Passed | 15 | 145.838 tok/s | 2.379 GiB | Full ROCm offload |
| `granite4.1:3b-q4_K_M` | Passed | 15 | 129.964 tok/s | 2.330 GiB | Full ROCm offload |
| `phi4-mini:3.8b-q4_K_M` | Passed | 15 | 123.575 tok/s | 2.876 GiB | Full ROCm offload |
| `nemotron-3-nano:4b` | Passed | 15 | 121.103 tok/s | 2.621 GiB | Full ROCm offload |
| `ministral-3:3b-instruct-2512-q4_K_M` | Did not pass | — | — | — | Summarization control failed before soak |
| `gemma3:4b-it-q4_K_M` | Passed | 15 | 108.943 tok/s | 2.678 GiB | Full ROCm offload |
| `gemma4:e2b-it-qat` | Passed | 15 | 123.425 tok/s | 1.537 GiB | Full ROCm offload |
| `qwen3.5:4b` | Passed | 15 | 99.511 tok/s | 2.913 GiB | Full ROCm offload |
| `granite4:7b-a1b-h` | Did not pass | — | — | — | Summarization control failed before soak |
| `gemma4:e4b-it-qat` | Passed | 14 | 92.202 tok/s | 2.874 GiB | Full ROCm offload |
| `granite4.1:8b-q4_K_M` | Passed | 15 | 73.041 tok/s | 5.488 GiB | Full ROCm offload |
| `ministral-3:8b-instruct-2512-q4_K_M` | Did not pass | — | — | — | Summarization control failed before soak |
| `qwen3.5:9b` | Passed | 15 | 69.638 tok/s | 5.113 GiB | Full ROCm offload |
| `gemma4:12b-it-qat` | Passed | 14 | 59.260 tok/s | 7.132 GiB | Full ROCm offload |
| `gemma3:12b-it-q4_K_M` | Passed | 14 | 50.408 tok/s | 7.492 GiB | Full ROCm offload |
| `phi4:14b-q4_K_M` | Passed | 14 | 50.624 tok/s | 9.066 GiB | Full ROCm offload |

The 14 passing rows contain at least four successful samples for each of Chat,
Writing, and Summarization. Sample count differences reflect the bounded
30-minute window; they are not quality scores.

## What remains open

- The test did not collect supported Windows AMD board-power telemetry. The
  earlier synchronized Qwen 3.5 9B Adrenalin record remains separate.
- Deterministic task controls prove bounded behavior, not comparative response
  quality. Blind human review is still required before selecting a task winner.
- Cancellation, interrupted download, low-resource recovery, sleep/wake,
  package lifecycle, and signed-release parity remain separate gates.
- No result changes an automatic model, runtime, support label, or release
  policy. The three failed models remain excluded from recommendation review
  for this exact route until a new pinned runtime/artifact test passes.

This page is a human-readable, content-free summary. The evidence catalog is
the machine-readable pointer for future update tooling.
