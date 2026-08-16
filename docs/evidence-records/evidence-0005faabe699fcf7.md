# Windows conversation-history per-user ACL primitive

> Generated evidence page. The canonical machine-readable record is
> `evidence-0005faabe699fcf7` in `config/evidence-page-registry.json`.

## What this record says

A synthetic temporary directory passed 24 checks for protected inheritance, current-user and Local System full control, bounded inherited key-file rules, injected Users-group refusal, residue cleanup, and package exclusion; the production application directory, database, user content, runtime, UI, and package authority remain unadmitted.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Development Native |
| Area | Data Protection |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 development ACL proof |
| Surface version | 1 |
| Provider or runtime | Windows protected DACL |
| Operating system | Windows |
| Model | none |
| Operation | Protected Directory Inherited File Unexpected Principal Cleanup |

## Source evidence

[examples/windows-conversation-history-per-user-acl-validation.md](https://github.com/hysel/haven-42/blob/main/examples/windows-conversation-history-per-user-acl-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
