# Capability Registry

`config/capabilities.json` is the provider-neutral intent layer above `config/workflows.json`. It describes what a user wants; provider adapters and engineering workflows describe how an available capability is executed.

The initial registry contains:

| Capability | Repository | Initial availability | Execution boundary |
| --- | --- | --- | --- |
| `general.chat` | none | `configuration-required` | Live-validated local text adapter; runtime model discovery required |
| `content.write` | none | `configuration-required` | Live-validated local text adapter and approved artifact path; runtime model discovery required |
| `content.summarize` | none | `configuration-required` | Live-validated local text adapter and approved artifact path; runtime model discovery required |
| `media.image.create` | none | `configuration-required` | Future evidence-gated image provider and approved artifact path |
| `engineering.software-work` | optional | `available` | Existing workflow registry and dispatcher |
| `setup.local-ai` | optional | `available` | Existing setup, health, model, and configuration workflows |

## Availability States

- `available`: the underlying execution boundary exists, but action-specific policy and approval checks still apply.
- `configuration-required`: the capability is known but no promoted provider/configuration can execute it yet.
- `unavailable`: the current platform or environment cannot provide the capability.
- `blocked`: policy or a required safety boundary prevents execution.
- `failed`: the configured provider or execution boundary failed validation or execution.

Availability is not permission. A selected capability must still resolve its provider or workflow, disclose effects, validate policy, and obtain any required approval.

## Policy Metadata

Every capability declares repository mode, artifact types, provider kinds, and whether it may read a repository, write files, use a network, download models, call an external provider, or require approval. Provider-dependent and workflow-dependent values must be resolved before execution; they are never treated as permission.

Engineering requests continue through `config/workflows.json`. General chat success cannot promote a model or agent surface for engineering writes.

Use `discover-capability-availability` to derive runtime availability without persisting provider endpoints. Use `resolve-engineering-route` to turn an engineering capability into a non-invoking workflow plan. See [Capability Availability and Engineering Routing](capability-availability-and-engineering-routing.md).

## Maintenance

- Keep IDs stable and provider-neutral.
- Add provider adapters only after their own evidence and admission gates pass.
- Reference only artifact IDs defined in `config/typed-artifact-contract.json`.
- Do not put endpoints, credentials, local paths, model-server addresses, or provider secrets in the registry.
- Add deterministic routing phrases conservatively and test ambiguous wording.
