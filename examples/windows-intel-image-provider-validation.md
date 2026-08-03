# Windows Intel Image Provider Validation

## Exact-profile partial pass

The official ComfyUI `v0.30.0` Intel portable completed a disposable native
Windows validation on 2026-08-03. This evidence narrows the Milestone 23 gate;
it does not ship or promote a runtime, model, installer, provider profile, or
product configuration.

| Field | Value |
| --- | --- |
| OS / accelerator | Windows 11 x64; Intel Arc B580 12 GB |
| Intel driver | `32.0.101.8864`; Microsoft Windows Hardware Compatibility Publisher signature |
| ComfyUI | `v0.30.0` official Intel portable |
| Portable size / SHA-256 | 1,698,493,396 bytes; `3fc6b62317c8aae50f43296762929a3808615ae891900587218d00234d366135` |
| Embedded runtime | Python 3.13.14; PyTorch `2.13.0+xpu` |
| Checkpoint | SDXL Base 1.0 at revision `f298da3c058bd8f1f1c62f3ecfa775244a243897` |
| Checkpoint SHA-256 | `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b` |

## Immutable update and rollback transition

An additional native cell exercised the official ComfyUI `v0.29.2` Intel
portable as an immutable rollback target, then selected the untouched
`v0.30.0` candidate again. The `v0.29.2` release asset was 1,690,682,182
bytes with SHA-256
`045e859a7a6d827373ae527628c63739a87d6269fe5127cb075854c84e40f124`.
Pre-extraction inspection accepted 64,596 case-unique regular-file or
directory members, and the extracted tree contained no reparse points.

The rollback runtime reported ComfyUI `0.29.2`, PyTorch `2.13.0+xpu`, and one
exact Intel Arc B580 XPU. Using the same verified checkpoint and unchanged
production adapter, it generated three valid, distinct, metadata-free PNGs,
rejected an invalid workflow, remained healthy after rejection, cancelled an
active job without emitting an image, returned its queue to idle, cleared
history, and closed the exact owned process and listener. The first generation
took 145.413 seconds including cold initialization; the next two took 2.221
and 1.261 seconds.

The forward-selection check then probed exact ComfyUI `0.30.0`, confirmed the
same XPU, generated one fresh production-adapter image, and again closed the
owned process and listener. Both portable trees remained side by side; no
archive, runtime, model, service, driver, firewall rule, system Python, or
global setting was replaced.

The archive came from the immutable official GitHub release and matched its
GitHub-provided digest. Pre-extraction review accepted 64,617 case-unique
regular-file or directory members and rejected absolute, drive, traversal,
alternate-stream, oversized-name, unsupported-type, and case-collision shapes.
The extracted tree contained no reparse points. The checkpoint came from the
immutable official model revision and matched the previously validated exact
digest.

The embedded runtime reported ComfyUI `0.30.0`, one available XPU device, and
the exact Intel Arc B580 identity. The provider startup record separately
confirmed the XPU device, preventing the runtime probe from being treated as
proof of service execution. A non-administrator PowerShell 5.1 harness started
only the run-owned process with an explicit `127.0.0.1:8188` listener, disabled
browser launch, PNG metadata, custom nodes, and API nodes, isolated
input/output/temp/user directories, and an in-memory database. No installer,
administrator access, service, startup item, firewall rule, driver, system
Python, or `PATH` change was used.

Haven 42's unmodified production adapter generated valid 512x512 RGB PNGs.
Typed artifact policy, same-machine/loopback scope, metadata exclusion, and
nonconstant image-channel checks passed. Three fresh eight-step runs with
distinct seeds produced three distinct hashes. A missing-checkpoint workflow
was rejected with HTTP 400 and provider health remained available.

A 100-step job was observed in the running queue before `/interrupt` was sent.
The final history contained an explicit `execution_interrupted` record, no
image was emitted, the queue returned idle, and history cleanup passed. A
separate active 100-step job was stopped by terminating only the exact
run-owned provider PID; the listener closed, the same pinned XPU runtime
restarted, and a fresh production-adapter recovery generation passed. Every
bounded run ended with exact-process shutdown and endpoint closure.

## Security and admission boundary

- All provider traffic remained same-machine and loopback-only. No Ollama,
  LAN provider, public bind, redirect, or credential was involved.
- The production adapter retained bounded responses, fixed built-in workflow,
  safe artifact naming, exclusive writes, and repository exclusion.
- Generated PNGs contained no embedded workflow or prompt metadata. No image,
  prompt, endpoint, account, host, PID, path, raw report, or provider log is
  committed.
- Process control was bound to the exact process created by the harness. No
  unrelated process was selected or terminated.
- The provider history and queue were cleared, but the candidate runtime,
  checkpoint, and review-owned session directories remain in user-local test
  storage pending separately approved destructive cleanup.

Status is `partial-pass`. The immutable Intel update/rollback transition is
complete. Automatic idle shutdown, complete cleanup and uninstall,
source/package parity, dependency and redistribution review, consumer
onboarding, and UI integration remain open. No Intel image profile is
promoted, and no production readiness is claimed.

Official sources: [ComfyUI v0.30.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.30.0), [ComfyUI portable guidance](https://docs.comfy.org/installation/comfyui_portable_windows), and [SDXL Base 1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/tree/f298da3c058bd8f1f1c62f3ecfa775244a243897).
