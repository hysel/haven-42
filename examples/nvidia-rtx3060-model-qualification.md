# NVIDIA GeForce RTX 3060 12 GB model qualification

## What this evidence answers

On August 17–18, 2026, Haven 42 tested 19 exact local model artifacts on one
Windows 11 computer with an NVIDIA GeForce RTX 3060 12 GB. The run used NVIDIA
driver 610.88 and an isolated, loopback-only Ollama 0.32.14 candidate runtime.

This is engineering evidence for that exact configuration. It does not make
Ollama 0.32.14 the managed default, certify every RTX 3060 computer, or prove
the same behavior on Linux, another driver, another model digest, VS Code, or
VSCodium.

## Result at a glance

- All 19 exact artifacts passed identity and download checks.
- Fourteen models passed the required Chat, Writing, and Summarization gates.
- Those same 14 models passed independent 30-minute soaks.
- Five models failed a required task contract and were not allowed into soak.
- One model, Granite 4.1 8B Q4, passed the complete OpenCode 1.18.11
  disposable-repository workflow screen.
- No coding-agent recommendation was granted because Granite still lacks the
  remaining policy gates and editor surfaces require separate evidence.
- NVIDIA board telemetry was sampled 39,327 times. It does not measure the
  whole computer or wall-socket electricity use.

## Core task and soak outcomes

| Exact candidate | Core task gate | 30-minute soak | Average generation | Peak GPU memory |
| --- | --- | --- | ---: | ---: |
| Qwen 3.5 2B Q8 | Passed | Passed, 132 samples | 116.75 tok/s | 2.30 GiB |
| Qwen 3.5 4B Q4 | Passed | Passed, 129 samples | 84.23 tok/s | 3.11 GiB |
| Qwen 3.5 9B Q4 | Passed | Passed, 126 samples | 56.26 tok/s | 5.34 GiB |
| Gemma 3 4B Q4 | Passed | Passed, 129 samples | 97.98 tok/s | 2.82 GiB |
| Gemma 3 12B Q4 | Passed | Passed, 120 samples | 41.33 tok/s | 7.50 GiB |
| Gemma 4 E2B QAT | Passed | Passed, 126 samples | 95.60 tok/s | 1.67 GiB |
| Gemma 4 E4B QAT | Passed | Passed, 123 samples | 72.29 tok/s | 3.01 GiB |
| Gemma 4 12B QAT | Passed | Passed, 126 samples | 43.00 tok/s | 7.42 GiB |
| Granite 4.1 3B Q4 | Passed | Passed, 147 samples | 105.67 tok/s | 2.72 GiB |
| Granite 4.1 8B Q4 | Passed | Passed, 138 samples | 60.77 tok/s | 6.22 GiB |
| Phi 4 Mini 3.8B Q4 | Passed | Passed, 141 samples | 114.02 tok/s | 3.45 GiB |
| Llama 3.2 3B Q4 | Passed | Passed, 141 samples | 130.84 tok/s | 2.89 GiB |
| Ornith 1.0 9B Q4 | Passed | Passed, 132 samples | 58.12 tok/s | 5.19 GiB |
| MiniCPM V4.6 1B Q4 | Passed | Passed, 135 samples | 229.78 tok/s | 0.72 GiB |

Every soak sample passed its bounded request and unload checks. A soak pass
means the model remained stable under this synthetic workload; it is not a
human quality score.

## Models stopped before soak

| Candidate | Why it stopped |
| --- | --- |
| Qwen 3.5 0.8B Q8 | Writing missed the required word-count range. |
| Gemma 3 1B Q4 | Summarization omitted required facts. |
| Ministral 3 3B Q4 | Writing returned more than one sentence. |
| Ministral 3 8B Q4 | Writing and Summarization returned more than one sentence. |
| LFM 2.5 8B-A1B Q4 | Chat, Writing, and Summarization missed their exact contracts. |

These negative results matter. A model can run quickly and still be a poor
automatic choice if it does not reliably follow the requested task format.

## Coding-agent screen

OpenCode 1.18.11 ran against generated disposable repositories. The harness
checked repository reading, a specifically approved README write, a
two-file scoped edit, the external Git diff, unexpected files, exit and timeout
behavior, and model unload. Raw prompts, responses, paths, and private
endpoints were not retained.

| Outcome | Models |
| --- | --- |
| Read, approved write, and scoped edit passed | Granite 4.1 8B Q4 |
| Read and scoped edit passed; approved write failed | Gemma 4 12B QAT |
| At least one required workflow gate failed | All other 17 candidates |

Granite 4.1 8B remains a coding-agent candidate, not a recommendation. Its
remaining structured code, tool-contract, recovery, and editor-specific cells
must pass. Ornith separately passed structured coding, tool calling, and
failure recovery, but its OpenCode write/edit workflow failed. MiniCPM passed
failure recovery but failed synthetic red/blue vision grounding.

## Graphics-board power observations

The logger recorded one-second `nvidia-smi` board readings during every soak
and five-minute idle windows before and after the test. Idle averaged 22.116 W.

| Model | Mixed-task average | Observed peak | Board energy over soak |
| --- | ---: | ---: | ---: |
| Qwen 3.5 2B Q8 | 28.09 W | 73.64 W | 14.06 Wh |
| Qwen 3.5 4B Q4 | 29.52 W | 83.33 W | 14.76 Wh |
| Qwen 3.5 9B Q4 | 31.11 W | 97.28 W | 15.56 Wh |
| Gemma 3 4B Q4 | 28.52 W | 77.92 W | 14.26 Wh |
| Gemma 3 12B Q4 | 33.54 W | 140.06 W | 16.77 Wh |
| Gemma 4 E2B QAT | 27.45 W | 61.41 W | 13.73 Wh |
| Gemma 4 E4B QAT | 29.27 W | 73.04 W | 14.63 Wh |
| Gemma 4 12B QAT | 31.33 W | 104.40 W | 15.79 Wh |
| Granite 4.1 3B Q4 | 25.55 W | 96.52 W | 12.78 Wh |
| Granite 4.1 8B Q4 | 29.24 W | 97.28 W | 14.62 Wh |
| Phi 4 Mini 3.8B Q4 | 26.61 W | 69.96 W | 13.30 Wh |
| Llama 3.2 3B Q4 | 27.39 W | 83.79 W | 13.73 Wh |
| Ornith 1.0 9B Q4 | 30.60 W | 103.56 W | 15.30 Wh |
| MiniCPM V4.6 1B Q4 | 25.36 W | 51.53 W | 12.68 Wh |

The soak deliberately unloads after each request and waits 30 seconds before
the next sample. Its average power therefore represents this conservative
mixed-task lifecycle, not continuous maximum-throughput generation. These are
GPU-board readings, not wall power: CPU, memory, storage, cooling, display, and
power-supply losses are excluded.

## What remains open

- Complete the coding policy cells for Granite 4.1 8B.
- Validate native VS Code and VSCodium surfaces separately.
- Run the packaged Haven 42 beginner workflow on this hardware.
- Review model licenses and redistribution terms before promotion.
- Decide runtime admission, automatic defaults, and selection policy only in
  separate owner-approved changes.

The machine-readable summary is
[`config/alpha-2-nvidia-rtx3060-qualification-result.json`](https://github.com/hysel/haven-42/blob/main/config/alpha-2-nvidia-rtx3060-qualification-result.json).
