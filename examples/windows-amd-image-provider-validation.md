# Windows AMD Image Provider Validation

## Exact-profile partial pass

The official ComfyUI AMD portable completed disposable native Windows cells on 2026-07-22 and 2026-07-23. These results narrow the remaining gate but do not ship or promote a Windows runtime or installer.

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

## Immutable side-by-side update and rollback pass

On 2026-08-03, official ComfyUI `v0.30.0` supplied a newer immutable AMD
portable. The v0.28.0 and v0.30.0 assets were downloaded from their exact
GitHub releases and matched the release API SHA-256 values:

| Version | Size | SHA-256 | Safe archive members |
| --- | ---: | --- | ---: |
| v0.28.0 | 1,762,815,561 bytes | `824f70126a8733ce25cc5713d20dba91ddd9f27efd6ac04a6d4a57dbf09ecd3c` | 66,726 |
| v0.30.0 | 1,781,518,314 bytes | `0f3816fa1149e5a739e4d095d7733bc4ea28b02c8872fadeb8f73b933b141568` | 67,178 |

Both pre-extraction reviews accepted only case-unique regular files and
directories and rejected absolute, drive, traversal, alternate-stream,
oversized-name, unsupported-type, and case-collision shapes. Neither extracted
tree contained a reparse point. Both embedded runtimes independently reported
the exact expected ComfyUI version, PyTorch `2.9.1+rocm7.2.1`, HIP
`7.2.53211-158bd99533`, and one RX 7800 XT. The same immutable SDXL checkpoint
was shared read-only after its exact digest passed again.

The v0.30.0 candidate started first through a non-administrator, run-owned
launcher with explicit loopback binding, disabled browser launch, metadata,
custom nodes, and API nodes, isolated directories, and an in-memory database.
The running service log confirmed HIP-backed `cuda:0` and the RX 7800 XT before
Haven 42's unmodified production adapter was called. A 512x512 RGB PNG passed
typed artifact policy, zero-metadata, and nonconstant-channel checks; provider
history cleanup, bounded idle stability, exact-process shutdown, and endpoint
closure passed.

Rollback then started the untouched v0.28.0 tree through the same boundary and
a fresh session. Runtime/service accelerator identity, production-adapter
generation, typed artifact and PNG checks, metadata/history cleanup, idle
stability, exact-process shutdown, and endpoint closure passed again. This is
exact transition evidence only for these two versions, this driver/runtime
family, and this RX 7800 XT. It does not admit automatic updates, another AMD
device, Linux AMD, an installer, or product integration.

Status remains `partial-pass`. The immutable update/rollback gap is closed for
this exact cell, while consumer onboarding, automatic idle shutdown, package
parity, dependency and redistribution review, and profile promotion remain
open. The side-by-side runtimes, model, and review sessions remain in ignored
local storage pending separately approved cleanup; no binary, image, prompt,
path, endpoint, account, host, PID, or raw log is committed.

Official sources: [ComfyUI v0.28.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.28.0), [ComfyUI v0.30.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.30.0), [official AMD portable guidance](https://github.com/Comfy-Org/ComfyUI), and [SDXL Base 1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/tree/f298da3c058bd8f1f1c62f3ecfa775244a243897).
