# Quantization Validation Evidence

## Linux NVIDIA Ollama Trusted-Artifact Comparison

- Date: 2026-07-22
- Validation mode: disposable local-endpoint comparison
- Platform: Linux x64
- Accelerator profile: NVIDIA 16 GB, full GPU residency confirmed
- Runtime: Ollama 0.32.1
- Model revision: Qwen 3.5 9B official Ollama artifacts
- Context and concurrency: 4,096 tokens, one request
- Baseline: Q4_K_M, artifact ID prefix `6488c96fa5fa`
- Candidate: Q8_0, artifact ID prefix `441ec31e4d2a`

Both artifacts returned the required bounded response, emitted the required structured tool call with valid arguments, and produced a syntactically bounded unified diff containing the requested guard and unchanged nonzero behavior. Ollama reported 100% GPU execution for both.

Q4_K_M used 5.6 GB loaded accelerator memory and generated 79.61 tokens/s in the warm bounded check. Q8_0 used 9.2 GB and generated 66.50 tokens/s. Cold loading and the bounded warm response were effectively similar for this sample. The engineering task was a functional comparison only because the Q4_K_M run included a model reload.

Decision: retain Q4_K_M for this exact profile and do not activate Q8_0. Q4_K_M preserved the tested functional behavior with lower storage and memory use and higher generation throughput. The downloaded Q8_0 candidate was stopped and removed, and the prior Q4_K_M artifact remained installed.

Boundaries: this Linux evidence does not validate local conversion, other model revisions, other GPUs, Windows, Apple Silicon, larger contexts, concurrency above one, broad conversational quality, long-document summarization, or agent-surface approved writes. Those require separate evidence cells.

## Windows AMD Ollama Trusted-Artifact Comparison

- Date: 2026-07-22
- Validation mode: disposable standalone local-endpoint comparison
- Platform: Windows 11 x64
- Accelerator profile: Radeon RX 7800 XT 16 GB, `gfx1101`
- Driver: AMD display driver 32.0.31021.5001
- Runtime: Ollama 0.32.1 with packaged ROCm 7.1 backend
- Model revision: Qwen 3.5 9B official Ollama artifacts
- Context and concurrency: 4,096 tokens, one request
- Baseline: Q4_K_M, artifact ID prefix `6488c96fa5fa`
- Candidate: Q8_0, artifact ID prefix `441ec31e4d2a`

The official standalone Windows and AMD ROCm archives matched the SHA-256 digests published in the Ollama 0.32.1 release metadata. Backend discovery selected ROCm and the `gfx1101` device. Both artifacts offloaded all 34 model layers, reported 100% GPU execution, returned the required bounded responses, emitted the required structured tool call with valid arguments, and produced the required unified diff.

| Check | Q4_K_M | Q8_0 |
| --- | ---: | ---: |
| Loaded size | 5.6 GB | 9.2 GB |
| Cold total / load | 9.32 s / 9.12 s | 11.81 s / 11.58 s |
| Warm bounded response | 0.63 s | 0.67 s |
| Warm generation | 71.99 tokens/s | 58.41 tokens/s |
| Clean engineering patch generation | 66.64 tokens/s | 53.76 tokens/s |
| Structured tool call and engineering patch | Pass | Pass |

Decision: prefer Q4_K_M for this exact profile. It retained the tested functional behavior while loading faster, using less storage and accelerator memory, and generating about 23.2% more tokens per second in the matched warm check.

One initial Q4_K_M performance sample was excluded because a game was using the GPU. The measured warm rate was 7.65 tokens per second with that competing workload and 71.99 tokens per second after it closed. This cell demonstrates that background accelerator use must be controlled or disclosed and anomalous results must be repeated.

Cleanup: the loopback-only server was stopped, port closure was verified, and approximately 22.0 GB of temporary archives, runtime libraries, models, logs, and pointers were permanently removed. No Ollama installation, service, startup entry, model, or test directory remains.

Boundaries: this Windows AMD evidence does not validate Vulkan, another AMD GPU or driver, Windows NVIDIA or Intel, local conversion, other models, larger contexts, concurrency above one, long-document quality, or agent-surface approved writes.
