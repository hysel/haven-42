# Radeon RX 5700 XT Qwen 3.5 0.8B llama.cpp board power

> Generated evidence page. The canonical machine-readable record is
> `evidence-2aa29208b11bc71d` in `config/evidence-page-registry.json`.

## What this record says

The GPU-board sysfs sensor reported 6.448 W idle average, 167.242 W active average, 180 W peak, 27.931213 Wh active energy, and 5,476.311 generated units per Wh across 1,195 requests; all 25 layers were GPU-offloaded, VRAM returned exactly to baseline, cleanup and post-run health checks passed, and this is not whole-system wall power or a controlled comparison with the different-model Ollama profile.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Power Evidence |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 Linux AMD power profiler |
| Surface version | 1 |
| Provider or runtime | llama.cpp b10375 Vulkan RADV |
| Operating system | Ubuntu 26.04 LTS |
| Model | Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| Operation | Idle Active Peak Energy Throughput Full Offload Cleanup |

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
