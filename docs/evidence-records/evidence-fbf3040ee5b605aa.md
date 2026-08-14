# Read-only install profile

> Generated evidence page. The canonical machine-readable record is
> `evidence-fbf3040ee5b605aa` in `config/evidence-page-registry.json`.

## What this record says

Generates local config without edit/apply roles and is covered by PowerShell and Bash tests.

| Result | Value |
| --- | --- |
| Status | `validated-by-tests` |
| Validation method | Automated Tests |
| Area | Installer Profile |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Installer scripts |
| Surface version | pack-tests |
| Provider or runtime | N/A |
| Operating system | Cross-platform |
| Model | N/A |
| Operation | Install Read Only |

## Source evidence

[scripts/test-pack.ps1](https://github.com/hysel/haven-42/blob/main/scripts/test-pack.ps1)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
