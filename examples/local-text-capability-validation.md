# Local Text Capability Validation

## Scope

This sanitized record covers the `ollama.local-text` adapter with `qwen3.5:9b` on Windows through a user-controlled local-network Ollama endpoint. The endpoint, prompts, raw responses, and temporary paths are intentionally omitted.

## Results

| Capability | Transport | Grounding signal | Typed artifact | Repository read | Sanitization | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `general.chat` | nonempty live response | exact bounded response token retained | `chat-message` | no | prompt and endpoint absent | pass |
| `content.write` | nonempty live response | requested Markdown heading and statement retained | `markdown-document` | no | prompt and endpoint absent | pass |
| `content.summarize` | nonempty live response | both supplied facts retained | `markdown-document` | no | prompt and endpoint absent | pass |

The adapter wrote only explicitly approved artifacts inside disposable session workspaces. The workspaces were removed and the model was unloaded after validation. No model was pulled or deleted.

A fresh provider-neutral regression run on 2026-07-22 used an already-installed smaller Ollama model. Model discovery returned `available`, chat returned nonempty content, network use was disclosed, no artifact was written, and endpoint persistence remained false. Windows and shared Linux/macOS fixtures also passed the OpenAI-compatible llama.cpp response mapping and rejected non-admitted engine profiles.

A separate direct llama.cpp run used pinned build `b10088` at commit `67b9b0e7f6ce45d929a4411907d3c48ec719e81c`, the exact Linux NVIDIA/CUDA RTX 5000 profile, and revision-pinned Qwen 3.5 9B Q4_K_M. Haven 42 discovery returned `available`, exact-profile admission passed, and the shared invocation adapter returned the exact requested content `HAVEN42_LLAMACPP_ADAPTER_OK` through the `openai-chat-completions` transport. The 5.953-second request included 50 prompt tokens at 258.57 tokens/s and 351 generation tokens at 62.34 tokens/s. Network use was disclosed, endpoint persistence and artifact writes remained false, the server used 5,279 MiB on the selected GPU, and the loopback server, SSH tunnel, model, source, toolchain, build, caches, and logs were removed afterward.

A fresh 2026-08-04 Ollama 0.32.5 regression probe against the installed exact
`qwen3.5:9b` digest passed 15 of 16 bounded provider-conformance checks,
including discovery, exact output, writing, summarization, structured tool
calling, read-only engineering, planning, Git-applicable patch, timeout,
cancellation, sanitization, and cleanup. The simple general-chat check failed,
so this run is non-promoting and does not replace earlier exact-profile
evidence. The selected model was independently confirmed absent from the
running-model list afterward; no endpoint, prompt, raw response, or machine
path was persisted.

The sanitized run recorded a 9,785.808 ms cold load, 720.059 ms first token,
272.554 prompt tokens/s, and 76.062 generation tokens/s. These exact-cell
metrics are diagnostic only and do not change the non-promoting decision.

## Limits

- This is transport, grounding, artifact, and safety-boundary evidence for one model and operating system.
- It does not prove broad writing quality, long-context summarization, factual correctness beyond supplied material, Linux/macOS model behavior, or engineering write readiness.
- Runtime availability still requires an endpoint, installed model, health discovery, and user-approved execution.
- Cross-platform fixture and wrapper tests validate adapter contracts without inheriting this Windows model result.
- The direct llama.cpp adapter result promotes only the exact Linux NVIDIA/CUDA profile. Windows AMD/HIP remains engine-evidence-only until its own direct adapter run passes.
