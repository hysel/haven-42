# August 2026 local-model qualification

This report records how newly reviewed local models behaved on real Linux
accelerator hardware. It applies only to the tested configurations; it does
not mean that every model is ready for every computer or use case.

## How to read the result

- **Passed core qualification** means Chat, Writing, Summarization, model
  unload, accelerator residency, and a bounded 30-minute soak all passed.
- **Passed an additional capability** means that capability passed its own
  deterministic check. A core pass does not imply a vision, coding, reasoning,
  or tool-use pass.
- **Failed validation** means a required check failed. The harness stopped
  before the soak when a task gate failed.
- **Deferred** means the artifact could not be tested safely on available
  hardware or needs a separate license/platform review. Deferred is not a
  model failure.

No result changes an automatic model default. Raw prompts and responses are not
in the evidence. Tool arguments were validated but never executed.

## Exact test profiles

| Profile | Runtime | What it establishes |
| --- | --- | --- |
| Ubuntu Linux with two Tesla V100 32 GiB cards | Ollama 0.32.13, CUDA | Exact high-memory model behavior on this dual-card profile |
| Ubuntu 26.04 with Radeon RX 5700 XT 8 GiB | Ollama 0.32.13, Vulkan through RADV | Exact RDNA 1 behavior with fail-closed CPU-fallback protection |

The harness required immutable model manifests, a pinned runtime, confirmed
accelerator residency, three samples for each required task, an unload after
every sample, and at least 30 minutes for every model that reached the soak.
New cells also require Ollama to report equal total-model and GPU-resident byte
counts; partial offload does not pass this gate.

## Results

| Model and exact lane | Core result | Additional capability result |
| --- | --- | --- |
| Qwen 3.5 0.8B Q8_0 · RX 5700 XT Vulkan | Failed | Chat and Summarization passed with full GPU residency; Writing missed the required word-count range, so no soak ran. |
| Qwen 3.5 2B Q8_0 · RX 5700 XT Vulkan | Failed | Chat and Summarization passed with full GPU residency; Writing missed the required word-count range, so no soak ran. |
| Qwen 3.5 4B Q4_K_M · RX 5700 XT Vulkan | Passed | All three tasks, 42 soak samples, 42 unloads, full residency, and the 30-minute soak passed at 93.501 tokens/s average. |
| Qwen 3.6 27B Q4_K_M · dual V100 CUDA | Passed | All core gates and the 30-minute soak passed at 33.376 tokens/s average. |
| Qwen 3.6 35B-A3B Q4_K_M · dual V100 CUDA | Passed | All core gates and the 30-minute soak passed at 82.668 tokens/s average. |
| Qwen 3.8 27B Q4_K_M · dual V100 CUDA | Partial | Core and soak passed at 38.789 tokens/s; tools, thinking, and recovery passed, but the vision grounding contract failed. |
| Ornith 1.0 9B Q4_K_M · RX 5700 XT Vulkan | Passed | Core, 42 soak samples, full residency, coding, tools, and recovery passed; soak average was 61.112 tokens/s. |
| North Mini Code 1.0 30B-A3B Q4_K_M · dual V100 CUDA | Partial | Core and soak passed at 114.288 tokens/s; tools, long context, and recovery passed, but the coding JSON contract failed. |
| LFM 2.5 8B-A1B Q4_K_M · RX 5700 XT Vulkan | Failed | Full GPU residency was observed, but Chat, Writing, and Summarization missed their deterministic contracts; no soak ran and license review remains open. |
| Granite 4.1 30B Q4_K_M · dual V100 CUDA | Passed | Core, 39 soak samples, full residency, coding, tools, and recovery passed; soak average was 35.173 tokens/s. |
| MiniCPM-V 4.6 1B Q4_K_M · RX 5700 XT Vulkan | Failed | Full residency and timeout/recovery passed, but the base Chat and separate vision-grounding contracts failed; no core soak ran. |
| Nemotron 3 Nano Omni 33B Q4_K_M · dual V100 CUDA | Partial | Core, 33 soak samples, full residency, thinking, and recovery passed at 140.733 tokens/s; tools and vision failed their separate contracts and license review remains open. |
| Muse Glimmer 30B Q4_K_M · dual V100 CUDA | Failed | Chat passed, but Writing and Summarization failed; no soak or extended-capability promotion followed. |
| Nemotron 3.5 Lightning 30B-A3B Q4_K_M · dual V100 CUDA | Passed core | Core and soak passed at 78.317 tokens/s; remaining advertised capabilities were not completed in this campaign and license review remains open. |
| Nemotron 3.5 Lightning 30B-A3B Q8_0 · dual V100 CUDA | Passed core | Core and soak passed at 58.232 tokens/s; remaining advertised capabilities were not completed in this campaign and license review remains open. |

The MLX variants remain deferred until Apple Silicon is available. Nemotron
3.5 Lightning BF16 remains deferred because its 65.9 GB artifact does not leave
the required safety headroom on the 64 GiB aggregate-GPU profile. Deferred is
an admission decision, not a model failure.

## Boundaries that remain

- Results apply only to the exact operating system, runtime, backend, artifact,
  and hardware profile shown.
- A passing local endpoint is not packaged-app, installer, updater, human
  quality, accessibility, or production evidence.
- North Mini Code is also subject to Cohere's acceptable-use policy.
- LFM 2.5 and NVIDIA Nemotron 3 remain blocked from automatic promotion until
  their model-license reviews close.
- MLX artifacts need Apple Silicon and are deferred until that hardware lane is
  available. Oversized BF16 artifacts are deferred when the reviewed machine
  cannot retain the required safety headroom.

## Machine-readable evidence

Each model record identifies the exact canonical inventory and qualification
matrix generation. The combined summary records task, soak, extended-capability,
and full-residency results without host names, addresses, credentials, hardware
serials, or raw user content. The public evidence catalog is advisory input for
a future updater; by itself, it cannot install a runtime, download a model, or
change a default.
