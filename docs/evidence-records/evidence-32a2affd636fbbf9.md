# Physical Apple M4 unattended synthetic Keychain lifecycle

> Generated evidence page. The canonical machine-readable record is
> `evidence-32a2affd636fbbf9` in `config/evidence-page-registry.json`.

## What this record says

The initial collision check passed, but macOS denied synthetic-item creation in the unattended SSH session. The runner retained no sensitive value or raw output and granted no package, encrypted-history, or production admission; interactive packaged-app testing remains required.

| Result | Value |
| --- | --- |
| Status | `failed-validation` |
| Validation method | Physical Source Test |
| Area | Data Protection |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 synthetic lifecycle runner |
| Surface version | 1 |
| Provider or runtime | Apple Keychain Services candidate |
| Operating system | macOS 26.6.2 |
| Model | fixed-validation-item |
| Operation | Collision Check Create Read Update Delete Absence Cleanup |

## Source evidence

[examples/macos-keychain-availability-boundary.md](https://github.com/hysel/haven-42/blob/main/examples/macos-keychain-availability-boundary.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
