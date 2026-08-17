# Radeon RX 5700 XT current-boot host stability

> Generated evidence page. The canonical machine-readable record is
> `evidence-30fc24f8aa3ddc2b` in `config/evidence-page-registry.json`.

## What this record says

The exact current boot completed 5,122,375 work units with zero detected machine-check, ECC, GPU-reset, CPU-lockup, thermal, or fatal-PCIe incidents; this is bounded engineering evidence and not a substitute for the still-open final-profile full-memory test.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Development Native |
| Area | Hardware Stability |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 Linux host-stability harness |
| Surface version | 1 |
| Provider or runtime | Linux kernel and amdgpu |
| Operating system | Ubuntu 26.04 LTS |
| Model | no-model |
| Operation | 600 Second Four Worker Cpu Smoke And Hardware Log Review |

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
