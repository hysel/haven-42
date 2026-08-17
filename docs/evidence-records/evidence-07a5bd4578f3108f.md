# Radeon RX 5700 XT exact Ubuntu Vulkan profile

> Generated evidence page. The canonical machine-readable record is
> `evidence-07a5bd4578f3108f` in `config/evidence-page-registry.json`.

## What this record says

Nine profiles passed the required core gate, seven failed at least one required task contract, and three larger candidates were refused before download; current-boot CPU smoke, accelerator residency, cleanup, and one exact board-power profile passed, while final-profile full-memory and packaged lifecycle evidence remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Hardware Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 Alpha 2 qualification harness |
| Surface version | 0.4.0-alpha.2 |
| Provider or runtime | Ollama 0.32.13 Vulkan RADV |
| Operating system | Ubuntu 26.04 LTS |
| Model | 16 exact manifest-pinned model profiles |
| Operation | Admission Core Tasks Residency Stability Power |

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
