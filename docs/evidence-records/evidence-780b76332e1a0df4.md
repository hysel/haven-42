# Windows conversation-history synthetic key protection

> Generated evidence page. The canonical machine-readable record is
> `evidence-780b76332e1a0df4` in `config/evidence-page-registry.json`.

## What this record says

A synthetic 32-byte key passed a current-user DPAPI round trip and 16 security checks with tamper refusal, mutable buffer wiping, and package exclusion; no database, persistent key, user content, runtime route, UI, package, or production authority is admitted.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Development Native |
| Area | Data Protection |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 development key adapter |
| Surface version | 1 |
| Provider or runtime | Windows DPAPI current user |
| Operating system | Windows |
| Model | none |
| Operation | Wrap Unwrap Synthetic Key |

## Source evidence

[examples/windows-conversation-history-dpapi-validation.md](https://github.com/hysel/haven-42/blob/main/examples/windows-conversation-history-dpapi-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
