# Capability Availability and Engineering Routing

Milestone 21 separates three decisions that must not be collapsed:

1. `resolve-capability` deterministically identifies what the user wants.
2. `discover-capability-availability` reports whether a validated provider is configured and reachable.
3. `resolve-engineering-route` maps engineering intent to existing workflow plans.

None of these commands invokes a provider or workflow. Availability is not permission.

## Provider discovery

Discovery is offline by default. It reads `config/capabilities.json` and `config/providers.json`, reports validated candidates, and does not expose or persist an endpoint.

```powershell
.\scripts\discover-capability-availability.ps1 -CapabilityId general.chat -AsJson
```

An explicit probe may check the Ollama tags endpoint for an already-installed model. It never pulls a model and its output contains neither the endpoint nor credentials.

```powershell
.\scripts\discover-capability-availability.ps1 -CapabilityId general.chat -Probe -Model <installed-model> -OllamaBaseUrl <runtime-url> -AsJson
```

Linux and macOS use `discover-capability-availability.linux.sh` and `.macos.sh`. They select `python3`, then `python`, and fail clearly when Python 3 is absent.

Bounded Windows live-probe evidence is recorded in [Capability Availability Validation](../examples/capability-availability-validation.md). Runtime state remains transient and configuration-dependent.

## Engineering routes

`config/engineering-routes.json` contains conservative intent groups whose workflow IDs must exist in `config/workflows.json`.

```powershell
.\scripts\resolve-engineering-route.ps1 -Text "review code" -AsJson
```

The result includes ordered workflow steps, safety levels, and OS-specific entry points. `InvocationAllowed` is always false. A caller must collect required repository paths and workflow arguments, disclose effects, and obtain approval where the selected workflow requires it.

General-purpose text validation never promotes an engineering workflow or model lane. Image generation remains `configuration-required` until a provider and adapter pass the same evidence gate.
