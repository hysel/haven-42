# Radeon RX 5700 XT Llama 3.2 3B board power

> Generated evidence page. The canonical machine-readable record is
> `evidence-9a9906ccfd247313` in `config/evidence-page-registry.json`.

## What this record says

The GPU-board sysfs sensor reported 7.575 W idle average, 122.118 W active average, 242 W peak, 20.350129 Wh active energy, and 2,134.188 generated units per Wh with verified unload; this is board-sensor evidence, not whole-system wall power.

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
| Provider or runtime | Ollama 0.32.13 Vulkan RADV |
| Operating system | Ubuntu 26.04 LTS |
| Model | llama3.2:3b-instruct-q4_K_M |
| Operation | Idle Active Peak Energy Throughput Unload |

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
