# Optional LLM Intent Routing

Deterministic routing remains the default. Use the optional `suggest-capability-route` advisor when a request needs natural-language clarification.

The model receives only the user's routing text and a compact public capability list. Treat its result as untrusted: deterministic code rejects unknown IDs, reloads availability and policy from `config/capabilities.json`, and always emits `InvocationAllowed: false`.

```powershell
.\scripts\suggest-capability-route.ps1 -Text "help me understand this report" -Model <installed-model> -Execute -OllamaBaseUrl <runtime-url> -AsJson
```

Linux and macOS use the corresponding `.linux.sh` and `.macos.sh` wrappers. Without `-Execute` or `--execute`, the command is a no-network plan. Endpoints and prompts are not persisted or returned.

The result can be `suggested`, `needs-clarification`, `rejected`, or `planned`. A valid suggestion still does not grant execution permission. Discover runtime provider availability separately; the selected capability's normal boundary still governs repository access, file writes, network actions, downloads, external providers, and workflow approval.

This router does not read a repository, invoke a capability, invoke an engineering workflow, write an artifact, or promote model evidence across domains.

Bounded Windows live evidence and hostile-fixture coverage are recorded in [Optional LLM Routing Validation](https://github.com/hysel/haven-42/blob/main/examples/optional-llm-routing-validation.md).
