# Qwen 3.8 27B native VS Code Chat read-only repository inspection

> Generated evidence page. The canonical machine-readable record is
> `evidence-cfa90771bd9c89a4` in `config/evidence-page-registry.json`.

## What this record says

The assistant grounded its answer in three exact fixture files, correctly explained the response and equality test, made no edits, and correctly declined to claim Git cleanliness without running a prohibited command; plan, review, terminal, write, and approved-write capabilities remain unproven.

| Result | Value |
| --- | --- |
| Status | `read-only-tool-validated` |
| Validation method | Generated Sample Editor Chat |
| Area | Agent Surface |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | VS Code native Chat + official Ollama extension |
| Surface version | 1.133.0 + 0.0.8 |
| Provider or runtime | Ollama |
| Operating system | Windows |
| Model | qwen3.8:27b |
| Operation | Read Files Follow Import Explain Test No Commands |

## Source evidence

[examples/native-vscode-chat-validation.md](https://github.com/hysel/haven-42/blob/main/examples/native-vscode-chat-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
