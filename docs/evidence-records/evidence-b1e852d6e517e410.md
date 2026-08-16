# Gemma 3 1B Q4 on Ollama 0.32.13 Linux CUDA

> Generated evidence page. The canonical machine-readable record is
> `evidence-b1e852d6e517e410` in `config/evidence-page-registry.json`.

## What this record says

The exact artifact passed all nine task cells, 42 soak samples, matching unload proofs, and bounded accelerator-residency reporting on the exact dual-V100 review profile; physical 16 GiB hardware, package lifecycle, recovery, energy, human quality, and automatic admission remain open.

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
| Provider or runtime | Ollama |
| Operating system | Ubuntu 24.04.4 |
| Model | gemma3:1b-it-q4_K_M |
| Operation | Chat Writing Summary Soak |

## Source evidence

[examples/nvidia-v100-ollama03213-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/nvidia-v100-ollama03213-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
