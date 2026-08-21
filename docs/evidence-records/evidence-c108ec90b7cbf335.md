# Physical Apple M4 unsigned development update lifecycle

> Generated evidence page. The canonical machine-readable record is
> `evidence-c108ec90b7cbf335` in `config/evidence-page-registry.json`.

## What this record says

Two exact unsigned arm64 development apps passed bounded physical side-by-side staging, health-gated selection, injected-failure rollback, healthy reactivation, marker-owned uninstall, user-data preservation, and qualification cleanup. This is not the product updater and grants no signing, notarization, automatic-update, support, or release authority.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Physical Package Test |
| Area | Package Lifecycle |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 development lifecycle runner |
| Surface version | 1 |
| Provider or runtime | two exact self-contained arm64 app archives |
| Operating system | macOS 26.6.2 |
| Model | none |
| Operation | Side By Side Stage Health Select Injected Failure Rollback Reactivate Uninstall Preserve Cleanup |

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
