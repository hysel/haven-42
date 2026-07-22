# Windows AMD Image Provider Validation

## Exact-profile partial pass

The official ComfyUI AMD portable completed a disposable native Windows cell on 2026-07-22. This evidence narrows the remaining gate but does not ship or promote a Windows runtime or installer.

| Field | Value |
| --- | --- |
| OS / accelerator | Windows 11 x64; AMD Radeon RX 7800 XT 16 GB |
| ComfyUI | v0.28.0; commit `700821e1364eaab0e8f21c538a2131719fec57bf` |
| Portable SHA-256 | `824f70126a8733ce25cc5713d20dba91ddd9f27efd6ac04a6d4a57dbf09ecd3c` |
| Embedded runtime | Python 3.12.10; PyTorch 2.9.1+rocm7.2.1; HIP 7.2.53211 |
| Checkpoint SHA-256 | SDXL Base 1.0 `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b` |
| Generated artifact | 1024×1024 RGB PNG; 1,712,544 bytes; no PNG metadata keys |
| Generated SHA-256 | `629c0b19d2c1c4be445293065a613d9cef3014ce3b106a6944be09ea4ff0f403` |

The process bound only to loopback with browser auto-launch, metadata, custom nodes, and external API nodes disabled. Haven 42''s production `media.image.create` adapter produced its typed artifact without repository access or prompt/endpoint persistence. The PNG was nonblank and visual inspection matched the requested silver observatory, star field, cinematic style, and no-text constraint.

History and queues were empty after the run. The expected provider-retained PNG was identified, the exact process stopped, a clean restart returned the same version and AMD device, the second exact process stopped, the port closed, and all run-owned portable, model, provider-output, session, and artifact files were removed. No driver, service, startup item, firewall rule, or system Python changed.

Status remains `partial-pass`: cancellation under active diffusion, forced failure recovery, update/rollback, a consumer onboarding path, repeated-run stability, and installer behavior remain open. The upstream AMD portable is experimental, so Linux NVIDIA evidence and this cell must not be generalized to other AMD devices or operating systems.

Official sources: [ComfyUI release](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.28.0), [official AMD portable guidance](https://github.com/Comfy-Org/ComfyUI), and [SDXL Base 1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0).
