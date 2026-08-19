# Radeon RX 5700 XT current-boot host stability

> Generated evidence page. The canonical machine-readable record is
> `evidence-27f4eaa91d0b896d` in `config/evidence-page-registry.json`.

## What this record says

The owner accepted the exact profile as operationally stable after disabling Global C-state control. The reviewed boot reported 78782 seconds uptime, zero failed units, and no matching machine-check, memory, GPU-reset, CPU-lockup, critical-thermal, or fatal-PCIe incident; the machine-reported boot had not yet reached 24 hours and the final-profile memory test remains open.

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
| Operation | Cpu Smoke Uptime Hardware Log Review Owner Acceptance |

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
