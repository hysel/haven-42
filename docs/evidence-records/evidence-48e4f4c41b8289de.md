# Ornith 10 9B Q4 on Radeon RX 5700 XT

> Generated evidence page. The canonical machine-readable record is
> `evidence-48e4f4c41b8289de` in `config/evidence-page-registry.json`.

## What this record says

The exact artifact passed the required core gate, 42 soak samples at a measured output rate of 61.112 per second, coding, tool-use, recovery, full GPU residency, and unload checks on the exact 8 GiB profile; packaged lifecycle, human-quality review, and automatic admission remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama |
| Surface version | 0.32.13 |
| Provider or runtime | Ollama Vulkan RADV |
| Operating system | Ubuntu 26.04 LTS |
| Model | ornith-10:9b-q4_K_M |
| Operation | Chat Writing Summary Soak Coding Tools Recovery Residency |

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
