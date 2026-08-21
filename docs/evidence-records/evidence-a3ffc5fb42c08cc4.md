# Physical Apple M4 Alpha 2 portable development package

> Generated evidence page. The canonical machine-readable record is
> `evidence-a3ffc5fb42c08cc4` in `config/evidence-page-registry.json`.

## What this record says

The native arm64 modified-source-snapshot package passed parity and lifecycle tests on a physical Apple M4 Mac. Its ad-hoc signature structure verifies, but it is not Developer ID signed or notarized and Gatekeeper rejects it; public release and automatic-update admission remain false.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Physical Package Test |
| Area | Package Parity |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 portable package |
| Surface version | 0.4.0-alpha.2 |
| Provider or runtime | Self-contained PyInstaller runtime |
| Operating system | macOS 26.6.2 |
| Model | none |
| Operation | Source Package Parity Relocation Read Only Recovery Lifecycle Port Authority Hostile Environment Integrity |

## Source evidence

[docs/portable-development-package.md](https://github.com/hysel/haven-42/blob/main/docs/portable-development-package.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
