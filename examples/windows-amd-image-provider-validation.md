# Windows AMD Image Provider Validation

## Exact-profile partial pass

The official ComfyUI AMD portable completed disposable native Windows cells on 2026-07-22 and 2026-07-23. This evidence narrows the remaining gate but does not ship or promote a Windows runtime or installer.

| Field | Value |
| --- | --- |
| OS / accelerator | Windows 11 x64; AMD Radeon RX 7800 XT 16 GB |
| ComfyUI | v0.28.0; commit `700821e1364eaab0e8f21c538a2131719fec57bf` |
| Portable SHA-256 | `824f70126a8733ce25cc5713d20dba91ddd9f27efd6ac04a6d4a57dbf09ecd3c` |
| Embedded runtime | Python 3.12.10; PyTorch 2.9.1+rocm7.2.1; HIP 7.2.53211 |
| Checkpoint SHA-256 | SDXL Base 1.0 `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b` |
| 2026-07-23 generated artifact | 1024×1024 RGB PNG; 1,710,990 bytes; no PNG metadata keys |
| 2026-07-23 generated SHA-256 | `aae188ac7791318463dbad4531abbe6cd826aa05b8025a1968d01a2f823d14e2` |

The process bound only to loopback with browser auto-launch, metadata, custom nodes, and external API nodes disabled. Haven 42's production `media.image.create` adapter produced its typed artifact without repository access or prompt/endpoint persistence. The 2026-07-23 PNG was nonblank, spanned the full 0–255 range in every RGB channel, and had no PNG metadata keys.

Three sequential 512×512 eight-step production-adapter runs passed with distinct PNG hashes in 8.29 seconds cold, 2.32 seconds warm, and 2.29 seconds warm. A 100-step job entered the running queue, `/interrupt` produced an explicit `execution_interrupted` terminal record, no image was emitted, and the provider returned to idle. A missing-checkpoint workflow was rejected HTTP 400 and the provider remained healthy. A later 100-step active job was force-stopped by terminating only the verified run-owned PID; the port closed, the same pinned provider restarted, and a valid adapter generation passed immediately afterward.

History and queues were empty after cleanup. Four expected provider-retained PNGs were identified and removed, leaving zero Haven 42 provider copies. The exact process stopped, the port closed, and all run-owned portable, model, provider-output, session, artifact, download, and temporary harness files were removed. No driver, service, startup item, firewall rule, PATH entry, or system Python changed.

Status remains `partial-pass`. On 2026-07-23 the official GitHub release API reported v0.28.0 as the latest release and returned the same AMD asset SHA-256, so there is no newer immutable AMD release with which to perform a genuine update/rollback transition. Consumer onboarding and installer behavior also remain unadmitted. A synthetic version switch is not counted as evidence. The upstream AMD portable is experimental, so Linux NVIDIA evidence and this cell must not be generalized to other AMD devices or operating systems.

Official sources: [ComfyUI release](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.28.0), [official AMD portable guidance](https://github.com/Comfy-Org/ComfyUI), and [SDXL Base 1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0).
