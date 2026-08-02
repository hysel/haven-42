# Windows NVIDIA Image Provider Validation

## Exact-profile partial pass

An official ComfyUI NVIDIA portable completed a disposable native Windows validation on 2026-08-01. This evidence narrows the Milestone 23 gate; it does not ship a runtime, model, installer, or provider configuration and does not promote the profile for product use.

| Field | Value |
| --- | --- |
| OS / accelerator | Windows 11 x64; NVIDIA Quadro RTX 5000 16 GB |
| NVIDIA driver | 582.70; CUDA 13.0 reported by the driver |
| ComfyUI | v0.29.2 official NVIDIA portable |
| Portable SHA-256 | `e7a39a817002d85b4fb2d4f6bd176c10d104a0d04031f99b9d8b7b1fd920c6fc` |
| Embedded runtime | Python 3.13.14; PyTorch 2.13.0+cu130 |
| Checkpoint | SDXL Base 1.0 at revision `f298da3c058bd8f1f1c62f3ecfa775244a243897` |
| Checkpoint SHA-256 | `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b` |
| Baseline result | 1024×1024 RGB PNG; 1,310,898 bytes; SHA-256 `5643a6a1fdde3783bd10c554fc9bde491bea47860465f8dc24dee5919b31ed80` |

The archive and checkpoint were downloaded from their official sources, checked against exact expected sizes and SHA-256 digests, and placed in a user-local development directory. Archive members were validated before extraction, the extracted tree contained no reparse points, and no installer, administrator access, service, startup item, firewall rule, driver, system Python, or `PATH` change was used.

ComfyUI started with an explicit `127.0.0.1` listener and browser auto-launch, PNG metadata, custom nodes, and external API nodes disabled. The listener audit found one IPv4 loopback listener and no wildcard or LAN listener. PyTorch reported the Quadro RTX 5000 as `cuda:0`; silent CPU fallback was not observed.

Haven 42's production `media.image.create` adapter generated the baseline typed artifact. The PNG was 1024×1024 RGB, contained no metadata keys, had nonconstant channels spanning 0–255, and was written only inside the disposable session. The adapter reported same-machine execution, no repository read, no external provider, and no prompt or endpoint persistence.

Three sequential 512×512 eight-step adapter runs passed in 3.432, 3.412, and 3.448 seconds with distinct output hashes. A missing-checkpoint workflow was rejected with HTTP 400 and the provider remained healthy. A running 100-step job produced an explicit interruption record, emitted no image, and returned control to the provider. A second active 100-step job was stopped by terminating only the exact process created by the harness; port 8188 closed, the same pinned runtime restarted, and a 512×512 recovery generation passed in 7.728 seconds.

The queue and history were empty after cleanup. The exact provider process stopped and port 8188 closed. Run-owned output, input, temporary, user-data, session, artifact, log, transferred-source, harness, and report files were removed. The verified user-local runtime, checkpoint, and license were intentionally retained for later development testing; this is not an uninstall result.

## Security review

- All provider traffic remained same-machine and loopback-only; no Ollama, LAN provider, public bind, redirect, or credential was involved.
- The production adapter retained its bounded response, fixed built-in workflow, safe artifact naming, exclusive-write, and repository-exclusion controls.
- Generated PNGs contained no embedded workflow or prompt metadata. No generated image or raw provider log is committed.
- Process control was limited to the exact run-owned process object. No unrelated process was selected or terminated.
- Committed evidence contains no endpoint, account name, host name, key, fingerprint, machine path, prompt, or raw report.
- Runtime and model retention is explicit. Future cleanup must target only their reviewed user-local directory and requires a separate uninstall validation.

Status remains `partial-pass`. A genuine immutable update/rollback transition, consumer onboarding, lifecycle integration, idle shutdown, uninstall, package parity, and redistribution/license review remain open. The UI and provider registry therefore remain unchanged, and no production readiness is claimed.

Official sources: [ComfyUI v0.29.2](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.29.2), [ComfyUI portable guidance](https://docs.comfy.org/installation/comfyui_portable_windows), and [SDXL Base 1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/tree/f298da3c058bd8f1f1c62f3ecfa775244a243897).
