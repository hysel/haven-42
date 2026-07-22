# Capability Availability Validation

## Scope

This sanitized record covers the read-only `ollama.local-text` availability probe with `qwen3.5:9b` on Windows through a user-controlled local-network Ollama endpoint. The endpoint and machine-specific paths are intentionally omitted.

## Result

The explicit probe called only Ollama's tags endpoint, found the already-installed model, and returned `available`. The result stated that no capability was invoked and no endpoint was persisted. The serialized output did not contain the runtime hostname, address, or port.

No model was run, loaded, pulled, unloaded, or deleted. Offline fixture tests cover installed and unprobed states, and the engineering route tests verify that every planned workflow exists while `InvocationAllowed` remains false.

The provider-neutral extension passed OpenAI-compatible `/v1/models` fixture mapping for the exact admitted Linux NVIDIA/CUDA llama.cpp profile and rejected a parked SYCL profile before network use. A fresh live Ollama probe on 2026-07-22 also returned `available` for an already-installed model without persisting its endpoint. Direct live llama.cpp discovery remains open.

## Limits

- This proves bounded provider discovery for one runtime, model, and operating system.
- It does not prove generation quality, ongoing runtime health, Linux/macOS network behavior, or permission to invoke a capability.
- Runtime availability is transient and must be rediscovered when a session is used.
