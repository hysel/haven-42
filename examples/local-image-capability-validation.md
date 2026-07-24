# Local Image Capability Validation

## Scope

This sanitized record covers ComfyUI `v0.28.2`, PyTorch `2.11.0+cu126`, SDXL Base 1.0, and the `comfyui.local-image` adapter on Ubuntu Linux with an NVIDIA Tesla V100 32 GB. The server address, SSH identity, prompts, raw API history, local session paths, and generated images are intentionally omitted.

## Results

| Check | Result |
| --- | --- |
| Official immutable ComfyUI release | pinned commit and tag verified |
| PyTorch/CUDA compatibility | CUDA 12.6 `sm_70` tensor operation passed |
| SDXL checkpoint integrity | published SHA-256 matched before admission |
| Built-in API workflow | fixed-seed 1024×1024 generation passed |
| Visual grounding | requested object, setting, colors, and style were present |
| Service boundary | non-root, localhost-only, systemd hardening `4.7 OK` |
| Privacy | PNG metadata empty; prompt marker absent; API history cleared |
| Recovery | forced-process failure produced a new healthy systemd PID |
| Remote access | temporary SSH-tunneled API health check passed |
| Pack adapter | typed image artifact, PNG validation, sanitization, cleanup, and retention disclosure passed |

The adapter generated a valid 1024×1024 PNG through a temporary SSH tunnel, wrote only inside an approved disposable session, omitted prompt and endpoint values, and removed the local session and tunnel afterward. ComfyUI retains generated provider output, which the adapter reports explicitly.

On 2026-07-24, the local-web image boundary passed an additional live smoke
through a temporary pinned SSH tunnel and the existing non-root `haven42-comfyui`
account. The engine discovered the exact promoted checkpoint, generated one
bounded 512×512 PNG with a fixed one-step smoke profile, returned a typed
browser-memory image artifact, emitted accepted/progress/retention-warning/result
events, persisted neither prompt nor endpoint, wrote no client file, cleared
API history, authenticated shutdown, and closed the tunnel. The provider-side
output remains retained and was not destructively removed.

## Limits

- Evidence applies to this provider version, model, Linux runtime, GPU family, built-in workflow, and operation only.
- It does not validate custom nodes, external API nodes, image editing, arbitrary checkpoints, multi-GPU execution, macOS/Windows generation quality, or broad prompt quality.
- The SDXL model has documented composition, text, face, photorealism, and bias limitations and remains subject to its Open RAIL++ license.
- Runtime availability remains configuration-dependent and is not execution permission.
