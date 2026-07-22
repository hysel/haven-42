# Inference Engine Architecture

Haven 42 separates what the user wants from how a model runs:

`capability -> provider contract -> inference engine -> hardware backend -> model artifact`

The capability registry can request text generation without assuming Ollama, llama.cpp, LM Studio, or a hardware vendor. A provider adapter exposes a bounded contract. Engine selection then considers the local operating system, accelerator, verified runtime, model format, and exact evidence cell. No successful result transfers automatically between engines, backends, GPUs, drivers, model revisions, contexts, concurrency levels, or workload lanes.

The machine-readable source is `config/inference-engine-registry.json`. Unknown combinations fail closed, silent CPU fallback is prohibited, and failed candidates leave documentation only.

The shared local-text discovery and invocation entry points implement this boundary for `ollama.local-text` and `llamacpp.local-text`. They normalize Ollama and OpenAI-compatible response shapes without treating protocol compatibility as evidence inheritance. Ollama passed a fresh live adapter probe and chat call. llama.cpp passed its first direct server discovery and invocation on the exact Linux NVIDIA/CUDA profile; Windows AMD/HIP retains bounded engine evidence only, and every selection still requires an exact admitted profile.

## Current Decisions

| Engine | Decision | Boundary |
| --- | --- | --- |
| Ollama | Validated exact profiles | Existing Linux NVIDIA/CUDA and Windows AMD/ROCm evidence only. |
| llama.cpp | CUDA and HIP validated; Vulkan failed | Linux NVIDIA CUDA and Windows AMD HIP passed their exact bounded engine cells. Vulkan failed the Windows AMD applicable-patch gate and remains documentation-only. |
| OpenVINO GenAI | Parked | Wait for representative Intel GPU hardware; ship no integration assets meanwhile. |
| llama.cpp SYCL | Parked | Wait for representative Intel GPU hardware. Current upstream SYCL scope is Intel hardware. |
| LM Studio | Optional external API | The end user installs it. Haven 42 may call its published loopback API but does not embed or redistribute it. |
| IPEX-LLM | Retired | Upstream was archived on 2026-01-28. Keep a documentation record only. |
| llama.cpp Metal | Parked | Physical-Mac validation remains the last hardware step. |

`oneAPI` is a compiler/runtime toolkit rather than a standalone inference engine. It may become a dependency of an admitted Intel backend, but it is not presented as a provider. OpenVINO GenAI remains a separate Intel-focused engine candidate.

## Admission Rules

An engine/backend profile becomes selectable only after its runtime and model inputs are pinned and hash-verified, accelerator use is confirmed, silent CPU fallback is excluded, bounded functional checks pass, cleanup is verified, and sanitized evidence is committed. Download or install effects require prior disclosure and approval. Runtime files and model weights remain outside the repository and application engine tree.

Retired, failed, and hardware-blocked candidates have no scripts, installers, harnesses, runtime configuration, or packaged binaries. Optional proprietary software is invoked only when the user installed it and only through a published API.

## Primary References

- [llama.cpp project and supported backends](https://github.com/ggml-org/llama.cpp)
- [llama.cpp SYCL backend](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md)
- [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
- [OpenVINO GenAI](https://github.com/openvinotoolkit/openvino.genai)
- [Intel IPEX-LLM archive](https://github.com/intel/ipex-llm)
- [LM Studio local server](https://lmstudio.ai/docs/developer/core/server)
