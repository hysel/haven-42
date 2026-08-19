# llama.cpp b10375 Vulkan smoke on Radeon RX 5700 XT

> Generated evidence page. The canonical machine-readable record is
> `evidence-ded5fc576317be66` in `config/evidence-page-registry.json`.

## What this record says

The hash-pinned runtime identified the exact RX 5700 XT, offloaded 25 of 25 layers, returned the exact bounded response at 277.092 generated units per second, raised VRAM by 647102464 bytes, returned VRAM to baseline, left no process residue, and preserved the existing Ollama service; the full model ladder, server adapter, sustained operation, package lifecycle, Windows, ROCm, and automatic admission remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp CLI |
| Surface version | b10375 |
| Provider or runtime | Vulkan RADV |
| Operating system | Ubuntu 26.04 LTS |
| Model | Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| Operation | Device Discovery Single Turn Full Offload Vram Cleanup |

## Source evidence

[examples/amd-rx5700xt-ollama03213-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/amd-rx5700xt-ollama03213-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
