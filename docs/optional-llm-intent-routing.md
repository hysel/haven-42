# Optional LLM Intent Routing

Deterministic routing remains the default. `suggest-capability-route` is an optional advisory layer for requests that benefit from natural-language clarification.

The model receives only the user's routing text and a compact public capability list. Its result is untrusted. Deterministic code rejects unknown IDs, reloads availability and policy from `config/capabilities.json`, and always emits `InvocationAllowed: false`.

```powershell
.\scripts\suggest-capability-route.ps1 -Text "help me understand this report" -Model <installed-model> -Execute -OllamaBaseUrl <runtime-url> -AsJson
```

Linux and macOS use the corresponding `.linux.sh` and `.macos.sh` wrappers. Without `-Execute` or `--execute`, the command is a no-network plan. Endpoints and prompts are not persisted or returned.

The result can be `suggested`, `needs-clarification`, `rejected`, or `planned`. A valid suggestion still does not grant execution permission. Runtime provider availability must be discovered separately, and any repository access, file write, network action, download, external provider, or workflow approval is enforced by the selected capability's normal boundary.

This router does not read a repository, invoke a capability, invoke an engineering workflow, write an artifact, or promote model evidence across domains.

Bounded Windows live evidence and hostile-fixture coverage are recorded in [Optional LLM Routing Validation](../examples/optional-llm-routing-validation.md).
