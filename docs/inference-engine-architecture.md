# Inference Engine Architecture

Haven 42 separates what the user wants from how a model runs:

`capability -> provider contract -> inference engine -> hardware backend -> model artifact`

The capability registry can request text generation without assuming Ollama, llama.cpp, LM Studio, or a hardware vendor. A provider adapter exposes a bounded contract. Engine selection then considers the local operating system, accelerator, verified runtime, model format, and exact evidence cell. No successful result transfers automatically between engines, backends, GPUs, drivers, model revisions, contexts, concurrency levels, or workload lanes.

The machine-readable source is `config/inference-engine-registry.json`. Unknown combinations fail closed, silent CPU fallback is prohibited, and failed candidates leave documentation only.

The shared local-text discovery and invocation entry points implement this boundary for `ollama.local-text` and `llamacpp.local-text`. They normalize Ollama and OpenAI-compatible response shapes without treating protocol compatibility as evidence inheritance. Ollama passed a fresh live adapter probe and chat call. llama.cpp passed direct server discovery and invocation on the exact Linux NVIDIA/CUDA profile. A temporary lab-only Intel SYCL profile also passed discovery and invocation, but it is not committed as admitted because the pinned upstream suite was not fully green. Windows AMD/HIP retains bounded engine evidence only, and every selection still requires an exact admitted profile.

## Current Decisions

| Engine | Decision | Boundary |
| --- | --- | --- |
| Ollama | Validated exact profiles | Existing Linux NVIDIA/CUDA and Windows AMD/ROCm evidence only. |
| llama.cpp | CUDA and HIP validated; WSL2 DXG/HIP candidate; Vulkan failed | Linux NVIDIA CUDA and Windows AMD HIP passed their exact bounded engine cells. WSL2 Ubuntu 24.04 through `/dev/dxg` passed the same 11-model operational matrix on the exact RX 7800 XT profile, but remains candidate-only and does not establish native Linux AMD support. Vulkan failed the Windows AMD applicable-patch gate and remains documentation-only. |
| OpenVINO GenAI | Candidate | Exact Linux and Windows B580 GPU execution and cleanup passed. The Linux host is outside the documented support baseline, strict output behavior failed on both profiles, and provider/package gates are absent. |
| llama.cpp SYCL | Candidate | Exact Linux B580 functional, vision, pressure, adapter, and cleanup cells passed; 3 of 53 upstream tests failed, so the backend remains unselectable and unpackaged. |
| LM Studio | Optional external API | The end user installs it. Haven 42 may call its published loopback API but does not embed or redistribute it. |
| IPEX-LLM | Retired | Upstream was archived on 2026-01-28. Keep a documentation record only. |
| llama.cpp Metal | Partial physical-Mac evidence | Exact `b10520` lifecycle, full Metal offload, official-archive integrity, safe extraction, relocation, and dependency-free launch passed on an Apple M4 with 16 GB. The upstream executable is ad-hoc signed and rejected by Gatekeeper; Developer ID signing, notarization, a maintained coding surface, and product admission remain open. |

`Parked` remains the fail-closed status for an engine or backend that has not
yet earned executable candidate evidence. Moving one exact cell beyond parked
does not change any other engine, backend, hardware, or package status.

`oneAPI` is a compiler/runtime toolkit rather than a standalone inference engine. It may become a dependency of an admitted Intel backend, but it is not presented as a provider. OpenVINO GenAI remains a separate Intel-focused engine candidate. See `examples/intel-b580-inference-engine-validation.md` for the sanitized exact-host evidence and blockers.

## Operating-System Decision Matrix

Runtime selection is an exact-profile decision, not a GPU-name lookup. The
selection tuple includes operating system, architecture, CPU features,
accelerator vendor and model, driver, usable memory, backend, runtime version,
model artifact, and requested capability.

| Platform profile | Current direction | Important boundary |
| --- | --- | --- |
| Windows 11 x64 NVIDIA | Portable Ollama/CUDA | Current Alpha direction; validate consumer drivers, usable WDDM memory, lifecycle, and no silent CPU fallback. |
| Windows 11 x64 AMD | Portable Ollama/ROCm | Current Alpha direction; core and ROCm packages, supported GPU/driver, and exact model must pass together. |
| Windows 11 x64 Intel | Portable Ollama with experimental Vulkan only for the exact validated Arc B580 Alpha profile; otherwise CPU | The B580 Alpha cell proved nonzero GPU residency, but this evidence does not transfer to another Intel GPU or driver. Native llama.cpp SYCL failed its recorded model-load gate. |
| Windows x64 CPU-only | Portable Ollama with a smaller validated model | CPU features, RAM, thermals, and minimum usable token rate require native tier evidence. |
| Windows ARM64 | Future separate package | x64 evidence and dependencies do not transfer. |
| Linux NVIDIA | Ollama first; direct llama.cpp CUDA is an exact-profile option | Distribution, libc, driver, device permissions, suspend/resume, and portable user-process behavior remain gates. |
| Linux AMD | Ollama/ROCm first; llama.cpp HIP remains profile-specific | Kernel driver, ROCm version, device groups, and native-Linux evidence are required; WSL2 evidence does not transfer. |
| Linux Intel | Compare Ollama Vulkan, llama.cpp SYCL, and OpenVINO | Existing Intel results are candidate-only and cannot select a packaged runtime. |
| macOS Apple Silicon | Ollama Metal has exact qualification evidence; llama.cpp Metal and MLX remain bounded candidates | Exact M4 lifecycle evidence exists for all three routes. The direct llama.cpp archive is not a trusted public package, and MLX still lacks the production server and package boundaries required for novice use. Evidence does not yet grant an Apple default. |
| macOS Intel | CPU-only future consideration | Apple Silicon Metal evidence does not transfer; low performance may make the profile unsupported. |

Chat, Writing, and Summarization continue to use one provider-neutral text
contract. Ollama and llama.cpp can be separate providers, but Haven should not
run both for the same request. A verified Hugging Face GGUF can later be
imported into the managed Ollama runtime without admitting a direct llama.cpp
provider. Image, audio, speech, and video use separately admitted runtimes.

The default is the largest validated comfortable fit, with fallback only to a
smaller validated fit. Silent CPU fallback and unvalidated backend selection are
prohibited. Test results remain evidence; default runtime, model eligibility,
hardware routing, supported-platform, fallback, and beginner-flow changes need
explicit owner approval. See `DECISIONS.md` for the accepted governance record.

The development-only cross-accelerator manifest and sanitized completed baseline
are documented in `examples/cross-accelerator-model-validation.md`. Its runner
is offline during inference, listener-free, shell-free, hash-gated, and
full-offload-gated. Test artifacts and raw results remain outside the
repository. A completed cell never transfers evidence to another accelerator.
The WSL2 HIP mode is explicit and fail-closed: it requires the HIP backend, a
real non-symlink `/dev/dxg` character device, and a fixed child-process DXG
detection flag. It cannot be selected implicitly from inherited environment
state.

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
