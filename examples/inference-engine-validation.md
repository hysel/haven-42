# Inference Engine Validation

## Windows AMD llama.cpp Backends

Validation ran on 2026-07-22 using Windows 11 x64, a Radeon RX 7800 XT 16 GB (`gfx1101`), llama.cpp build `10088` at commit `67b9b0e7f`, a 4,096-token context, and one server slot. HIP and Vulkan ran independently on loopback-only listeners against the identical model artifact.

Inputs were immutable and hash-verified before execution:

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| llama.cpp `b10088` Windows HIP archive | 320,093,780 | `e76bcdda1b7740c61f93deafb9f4f3dc5193f3334bd7a242a33822a163a887e5` |
| llama.cpp `b10088` Windows Vulkan archive | 33,290,390 | `ced37906bfa57dca6079b0e66163edc4f319b43ba8260bda5427fbd20a08324b` |
| `unsloth/Qwen3.5-9B-GGUF` Q4_K_M at revision `3885219b6810b007914f3a7950a8d1b469d598a5` | 5,680,522,464 | `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8` |

The model is an Apache-2.0 quantization of `Qwen/Qwen3.5-9B`. The llama.cpp release is MIT-licensed. No artifact is distributed by Haven 42.

| Check | HIP/ROCm | Vulkan |
| --- | ---: | ---: |
| Backend/device discovery | RX 7800 XT, `gfx1101` | RX 7800 XT, AMD proprietary Vulkan driver |
| Reported device memory | 16,368 MiB | 16,368 MiB |
| Server model-load time | 4.78 s | 6.05 s |
| Fixed 128-token prompt benchmark | 1,247.12 tokens/s | 1,362.02 tokens/s |
| Fixed 64-token generation benchmark | 69.88 tokens/s | 86.94 tokens/s |
| Exact bounded response | Pass | Pass |
| Required structured tool call and JSON arguments | Pass | Pass |
| Applicable one-word engineering patch | Pass | **Fail** |

The HIP patch changed only `False` to `True` in the supplied two-line function and passed `git apply --check`. Vulkan repeatedly produced a malformed hunk or an extraneous separator; the captured candidate failed `git apply --check` with a corrupt-patch result. Faster inference did not override the functional gate.

Decision for the Windows AMD comparison: admit llama.cpp HIP only for this exact backend evidence cell. Do not infer agent-surface approved-write readiness. Keep Vulkan documentation-only and ship no Vulkan installer, adapter, harness, runtime configuration, or active evidence-catalog entry. Intel SYCL and OpenVINO GenAI remain parked until representative Intel GPU hardware is available. Metal remains physical-Mac-last.

An initial attempt used the official Ollama Qwen 3.5 9B model blob pinned by digest. Upstream llama.cpp rejected it before inference because its Qwen 3.5 rope metadata had a different array layout. The blob was removed and is not treated as backend evidence; model-format compatibility must be proven per engine even when both engines use GGUF.

After validation, both listeners were stopped and the downloaded model, runtime archives, extracted binaries, logs, and patch fixture were removed. No application, service, startup entry, model, or runtime remained installed.

## Linux NVIDIA llama.cpp CUDA

Validation ran on 2026-07-22 using Linux x64, NVIDIA driver `580.159.04`, and a Quadro RTX 5000 16 GB with compute capability 7.5. CUDA device order was explicitly set to PCI bus order before selecting the GPU; without that setting, CUDA's default ordering selected a different device than the same numeric `nvidia-smi` index. The test did not begin until `llama-cli --list-devices` reported only the RTX 5000.

Upstream published no Linux CUDA binary for `b10088`, so the three required binaries were built non-root from exact commit `67b9b0e7f6ce45d929a4411907d3c48ec719e81c`. The disposable toolchain used SHA-verified micromamba `2.8.1-0`, CUDA NVCC `12.4.131`, CUDA runtime `12.4.127`, cuBLAS `12.4.5.8`, and Ninja `1.13.2`. The resolved package transaction carried per-package SHA-256 values. The build targeted only `sm_75`, disabled native CPU specialization and both source and prebuilt web UI assets, and did not require NCCL because the evidence cell was single-GPU.

The test reused the same revision-pinned Q4_K_M model and SHA-256 recorded above, with a 4,096-token context and one server slot.

| Check | Linux CUDA result |
| --- | ---: |
| Backend/device discovery | Quadro RTX 5000, compute capability 7.5 |
| Reported device memory | 15,927 MiB |
| Loaded GPU memory | 5,285 MiB |
| Server readiness | 3.68 s |
| Fixed 128-token prompt benchmark | 1,346.31 tokens/s |
| Fixed 64-token generation benchmark | 63.33 tokens/s |
| Exact bounded response, first / warm | 0.238 s / 0.130 s, Pass |
| Required structured tool call and JSON arguments | 0.849 s, Pass |
| Git-applicable one-word engineering patch | 1.296 s, Pass |

The generated patch changed only `False` to `True` and passed an external `git apply --check`. Decision: admit llama.cpp CUDA for this exact Linux NVIDIA profile as engine-level evidence. This does not establish agent-surface approved-write readiness, multi-GPU behavior, another NVIDIA architecture, a different driver/toolchain/model/context, or a consumer installation path.

The loopback server and SSH tunnel were stopped. The model, pinned source, CUDA environment, compiler caches, build outputs, logs, and patch fixture were removed. The existing Ollama and ComfyUI services remained active and unchanged, and no llama.cpp listener or installation remained.

### Direct provider-adapter gate

The same pinned Linux CUDA environment was rebuilt without embedded or prebuilt UI assets and launched with `--no-ui` on loopback. Haven 42's production discovery and invocation scripts reached it through a verified SSH tunnel. `/v1/models` discovery, exact engine/backend/hardware admission, the `llamacpp.local-text` provider, OpenAI-compatible chat-completions mapping, and exact requested output all passed. The adapter request completed in 5.953 seconds; the server recorded 258.57 prompt tokens/s and 62.34 generated tokens/s, with 5,279 MiB loaded on the RTX 5000. No artifact or endpoint was persisted.

This promotes the local-text adapter only for the exact Linux NVIDIA/CUDA evidence cell. Windows AMD/HIP retains engine-only evidence. The server, tunnel, model, source, toolchain, build output, caches, and logs were removed after the adapter run.
