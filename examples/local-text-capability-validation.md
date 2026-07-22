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

A fresh provider-neutral regression run on 2026-07-22 used an already-installed smaller Ollama model. Model discovery returned `available`, chat returned nonempty content, network use was disclosed, no artifact was written, and endpoint persistence remained false. Windows and shared Linux/macOS fixtures also passed the OpenAI-compatible llama.cpp response mapping and rejected non-admitted engine profiles. That fixture result is contract evidence, not a direct live llama.cpp server result.

## Limits

- This is transport, grounding, artifact, and safety-boundary evidence for one model and operating system.
- It does not prove broad writing quality, long-context summarization, factual correctness beyond supplied material, Linux/macOS model behavior, or engineering write readiness.
- Runtime availability still requires an endpoint, installed model, health discovery, and user-approved execution.
- Cross-platform fixture and wrapper tests validate adapter contracts without inheriting this Windows model result.
- llama.cpp CUDA and HIP engine evidence does not by itself promote the new HTTP adapter; a direct server run remains required for `live-validated` adapter status.
