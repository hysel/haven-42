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

Decision: admit llama.cpp HIP only for this exact backend evidence cell. Do not infer agent-surface approved-write readiness. Keep Vulkan documentation-only and ship no Vulkan installer, adapter, harness, runtime configuration, or active evidence-catalog entry. Intel SYCL and OpenVINO GenAI remain parked until representative Intel GPU hardware is available. Metal remains physical-Mac-last.

An initial attempt used the official Ollama Qwen 3.5 9B model blob pinned by digest. Upstream llama.cpp rejected it before inference because its Qwen 3.5 rope metadata had a different array layout. The blob was removed and is not treated as backend evidence; model-format compatibility must be proven per engine even when both engines use GGUF.

After validation, both listeners were stopped and the downloaded model, runtime archives, extracted binaries, logs, and patch fixture were removed. No application, service, startup entry, model, or runtime remained installed.
