# Laguna XS 2.1 Exact-Profile Validation

## Result

`laguna-xs-2.1:q4_K_M` passed the bounded 16-check Ollama provider-conformance cell on Linux with Ollama 0.32.1. This is exact provider evidence, not agent-surface approved-write evidence.

| Field | Value |
| --- | --- |
| OS and hardware | Linux x64; Tesla V100 32 GB / Quadro RTX 5000 16 GB / Tesla V100 32 GB |
| Manifest digest | `a8562dfd0cad8475148f5c7b8d896ce1c5e18231cfe973459a9a9627116c11fd` |
| Model artifact SHA-256 | `a8f5bb41671012c749cabaf6f643a1f414f17ea885124a169a9ab00da2453543` |
| Artifact size | 20,274,700,911 bytes |
| Context / concurrency | 4,096 / 1 |
| Cold load | 11,940.702 ms |
| First token after load | 324.739 ms |
| Prompt / generation throughput | 211.027 / 100.222 tokens/s |
| Loaded VRAM reported by Ollama | 20,295,922,482 bytes |

The cell covered health, discovery, exact output, general chat, writing, summarization, structured tools, repository-free read reasoning, implementation planning, a Git-applicable disposable patch, timeout, cancellation, sanitization, unload, and cleanup. The production local-text adapter also returned the exact requested marker without repository access or endpoint/prompt persistence.

The same finalized cell against the existing `qwen3.5:9b` baseline passed 15 of 16 checks and repeatedly answered the bounded arithmetic chat check incorrectly. Its cold load was 8,376.482 ms, first token 702.116 ms, generation 75.945 tokens/s, and loaded VRAM 5,578,413,833 bytes. Existing Windows/editor evidence for Qwen is not invalidated; this Linux provider cell is not promoted.

No endpoint, prompt, raw response, process list, or machine path was persisted. The Laguna model was newly downloaded for this validation and retained because its exact cell passed. License and redistribution notices must be reviewed before any model bundling; Haven 42 does not bundle the artifact.
