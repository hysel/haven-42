# llama.cpp b10375 Vulkan task and soak on Radeon RX 5700 XT

> Generated evidence page. The canonical machine-readable record is
> `evidence-2ee5449c5143bfd7` in `config/evidence-page-registry.json`.

## What this record says

The exact hash-pinned Windows runtime offloaded all 25 layers, passed nine of nine task-gate samples and 1,602 of 1,602 paced soak requests over 1,801 seconds, produced 31,506 completion units, and passed device proof and cleanup; Windows Ollama, packaged lifecycle, other models, and automatic admission remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp server |
| Surface version | b10375 |
| Provider or runtime | Vulkan AMD proprietary 26.7.1 |
| Operating system | Windows 10.0.26200.8973 |
| Model | Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| Operation | Chat Writing Summary Task Gate 30 Minute Soak Full Offload Cleanup |

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
