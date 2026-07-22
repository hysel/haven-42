# Hardware-Adaptive Model Quantization

Haven 42 treats quantization as an evidence-bound model lifecycle, not a bit-count shortcut. The preferred result is a trusted compatible pre-quantized artifact. Local conversion is proposed only when no trustworthy compatible artifact exists and the exact runtime, hardware, license, storage, and quality gates can be satisfied.

## Contracts

- `config/quantization-plan-contract.json` defines dry-run decisions: `existing-artifact`, `local-derivative`, or `no-safe-recommendation`.
- `config/quantized-artifact-manifest-contract.json` records immutable source identity, input and output hashes, pinned tools, the full recipe, runtime compatibility, exact evidence scope, activation, rollback, and cleanup state.
- `config/quantization-support-matrix.json` defines candidate format/runtime boundaries. It deliberately does not claim that equal bit counts or different accelerators are interchangeable.

Source weights and derivatives stay outside the application and repository. A conversion never overwrites its source. Moving branches, missing hashes, unknown licenses, unapproved calibration material, unsupported kernels, silent CPU fallback, and inadequate temporary storage all produce `no-safe-recommendation`.

## Planning Inputs

The local-only hardware profile must include operating system and architecture, accelerator vendor/model/runtime, usable dedicated or unified memory, system memory, CPU instruction support, driver/runtime versions, available storage, target context, concurrency, and workload lane. Hostnames, IP addresses, usernames, endpoints, serial numbers, local paths, and model files are not committed.

## Consent And Provenance

Before download or conversion, disclose immutable source, license and derivative rights, published hashes, download size, temporary and final storage, estimated memory and compute time, network use, calibration provenance/privacy, cleanup, and rollback. Private repositories, prompts, conversations, and user documents are not calibration data by default.

## Comparative Promotion Gates

Compare the candidate with its source or trusted baseline for cold-load time, first-token latency, token throughput, peak accelerator and system memory, disk use, accelerator confirmation, context stability, and concurrency. Quality checks cover general chat, summarization, tool calls, read-only engineering, and approved-write reliability when that lane is intended. A speed or memory improvement cannot compensate for unacceptable quality loss or malformed tool behavior.

Each model revision, recipe, runtime version, operating system, accelerator, context target, and operation is a separate evidence cell. Failed candidates leave a sanitized decision record only and ship no conversion harness, runtime configuration, artifact, or active catalog entry.

## Local Dry Run

Generate a local-only profile without contacting a model endpoint:

```powershell
.\scripts\get-quantization-profile.ps1 -ContextTokens 16384 -Concurrency 1 -WorkloadLane tool-use > quantization-profile.local.json
```

```bash
./scripts/get-quantization-profile.linux.sh --context-tokens 16384 --concurrency 1 --workload-lane tool-use > quantization-profile.local.json
```

The macOS wrapper has the same arguments. The profile contains useful hardware values, so keep it local even though it omits hostnames, addresses, usernames, serial numbers, endpoints, and paths.

Create a local request JSON containing `source`, `target`, `hardwareProfile`, optional `trustedArtifacts`, `storageEstimate`, and disclosures, then evaluate it without effects:

```powershell
.\scripts\plan-model-quantization.ps1 -RequestPath quantization-request.local.json
```

```bash
./scripts/plan-model-quantization.linux.sh --request quantization-request.local.json
```

The result always reports `network`, `downloads`, `writes`, `conversion`, and `activation` as false. A `local-derivative` result is only a proposal for a later approved and independently validated workflow.

## Validated Linux NVIDIA Cell

On 2026-07-22, the first disposable trusted-artifact comparison passed on Linux x64 with Ollama 0.32.1 and an NVIDIA 16 GB accelerator profile. The exact comparison used Qwen 3.5 9B, a 4,096-token context, concurrency one, and the official Ollama `Q4_K_M` and `Q8_0` artifacts. Ollama verified the downloaded Q8_0 artifact before use.

| Check | Q4_K_M | Q8_0 |
| --- | ---: | ---: |
| Reported model storage | 6.6 GB | 11 GB |
| Loaded accelerator memory | 5.6 GB | 9.2 GB |
| Cold total / load time | 10.26 s / 10.06 s | 10.17 s / 9.96 s |
| Warm bounded response | 0.92 s | 0.90 s |
| Warm generation rate | 79.61 tokens/s | 66.50 tokens/s |
| Required structured tool call | Pass | Pass |
| Bounded unified-diff engineering task | Pass | Pass |

Q4_K_M is the preferred existing artifact for this exact cell: it preserved the tested functional behavior, used 3.6 GB less loaded accelerator memory, required about 4.4 GB less model storage, and generated about 19.7% more tokens per second. This is selection evidence, not local-conversion evidence. It does not transfer to another model revision, runtime, accelerator, context, concurrency level, or workload lane.

The Q8_0 candidate was stopped and removed after the comparison; the original Q4_K_M model remained installed. No endpoint, hostname, IP address, GPU UUID, local path, prompt content, or model file is part of the committed evidence. See `examples/quantization-validation.md` for the sanitized decision record.

## Validated Windows AMD Cell

On 2026-07-22, a second disposable comparison passed on Windows 11 x64 with Ollama 0.32.1, its packaged ROCm 7.1 backend, and a Radeon RX 7800 XT 16 GB `gfx1101` profile. The runtime archives were checked against the SHA-256 digests published with the Ollama release. Both official Qwen 3.5 9B artifacts used all 34 model layers on the GPU at a 4,096-token context and concurrency one.

| Check | Q4_K_M | Q8_0 |
| --- | ---: | ---: |
| Reported model storage | 6.6 GB | 11 GB |
| Loaded accelerator memory | 5.6 GB | 9.2 GB |
| Cold total / load time | 9.32 s / 9.12 s | 11.81 s / 11.58 s |
| Warm bounded response | 0.63 s | 0.67 s |
| Warm generation rate | 71.99 tokens/s | 58.41 tokens/s |
| Required structured tool call | Pass | Pass |
| Bounded unified-diff engineering task | Pass | Pass |

Q4_K_M is also preferred for this exact Windows AMD cell: it used 3.6 GB less loaded accelerator memory, required about 4.4 GB less model storage, loaded faster, and generated about 23.2% more tokens per second while retaining the tested functional behavior.

An initial Q4_K_M sample was invalidated because another GPU-heavy application was running; throughput rose from 7.65 to 71.99 tokens per second after that application closed. Hardware-adaptive validation must therefore disclose competing GPU workloads, start from an idle accelerator where practical, and repeat anomalous measurements before recording a recommendation.

The temporary loopback server, verified standalone runtime, ROCm package, both model artifacts, logs, and pointer file were removed after validation. No service, startup entry, application installation, model, or temporary listener remained. This evidence does not transfer to Vulkan, another AMD GPU or driver, another model or runtime, larger contexts, higher concurrency, long-document quality, or agent-surface approved writes.

## Inference Engine And Backend Boundary

Quantization compatibility is also engine-specific. A separate Windows AMD test used the same revision-pinned Q4_K_M GGUF with llama.cpp `b10088`. HIP passed backend discovery, bounded text, required tool calling, a Git-applicable engineering patch, and cleanup. Vulkan delivered higher fixed-benchmark throughput but produced malformed patches that failed `git apply --check`, so it was not promoted. An official Ollama GGUF blob was also rejected by upstream llama.cpp because its Qwen 3.5 metadata layout differed. Equal model family, quantization label, and container format do not establish cross-engine compatibility.

The same revision-pinned Q4_K_M artifact then passed an independent Linux NVIDIA llama.cpp CUDA cell on a Quadro RTX 5000 16 GB. The source-built `b10088` runtime used a pinned non-root CUDA 12.4 toolchain, explicit PCI-bus device ordering, an `sm_75` single-GPU build, a 4,096-token context, and concurrency one. It used 5,285 MiB loaded GPU memory, generated 63.33 tokens per second in the fixed benchmark, and passed bounded text, required tool calling, a Git-applicable patch, and cleanup. This evidence does not transfer to the earlier Ollama comparison or another CUDA profile.

See `config/inference-engine-registry.json`, `docs/inference-engine-architecture.md`, and `examples/inference-engine-validation.md`. Intel SYCL and OpenVINO GenAI are parked until representative Intel GPU hardware is available; they have no shipped executable integration assets.
