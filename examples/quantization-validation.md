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

Boundaries: this evidence does not validate local conversion, other model revisions, other GPUs, Windows, Apple Silicon, larger contexts, concurrency above one, broad conversational quality, long-document summarization, or agent-surface approved writes. Those require separate evidence cells.
