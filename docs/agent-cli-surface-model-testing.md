# Agent CLI Surface Model Testing

## Purpose

Use this workflow to screen CLI-capable coding agent surfaces with the same disposable repository tests instead of maintaining separate full scripts for every agent plugin.

The shared harness supports:

- Aider CLI
- Roo Code CLI historical compatibility only
- OpenCode CLI

OpenHands is platform-style rather than a simple local CLI harness target, so it needs separate validation later.

## Current Boundary

These scripts are automation scaffolding. A dry run proves the harness wiring, not that a surface or model works.

Roo Code is historical only: its upstream project is archived and the extension is shut down, so do not use its wrapper for new validation. OpenCode's documented `run`, provider/model, and local config contracts are reflected in the scaffold, and Devstral Small 2 24B has passed generated-sample read, write-smoke, and constrained scoped-edit checks. OpenCode still needs explicitly approved non-generated repository validation. Use command overrides for experiments, but do not promote wrappers to real-project approved-write readiness from disposable evidence alone.

A surface is not approved-write ready until it passes:

1. Read-only inspection against the intended repository or generated sample.
2. Disposable write-smoke validation, if the surface supports writes.
3. External verification with Git and direct file reads.
4. A realistic scoped edit in a disposable or explicitly approved repository.

The shared harness supports the fourth gate for the generated Python sample
through `-IncludeScopedEdit` / `--include-scoped-edit`. It requires an exact
two-file change to `app/settings.py` and `tests/test_main.py`, verifies both
files externally, checks whitespace, and restores the disposable fixture. It
does not permit a non-generated target unless the caller explicitly opts in.

## Shared Scripts

Windows PowerShell:

```powershell
.\scripts\test-agent-cli-surface-models.ps1 `
  -SurfaceName "Aider CLI" `
  -SurfaceKey "aider-cli" `
  -AgentCommand "aider" `
  -AgentArgumentsTemplate '--message "{Prompt}" --yes-always --no-auto-commits' `
  -ModelArgumentTemplate '--model "ollama_chat/{Model}"' `
  -Models "qwen3.5:9b" `
  -DryRun
```

Linux/macOS:

```bash
./scripts/test-agent-cli-surface-models.linux.sh \
  --surface-name "Aider CLI" \
  --surface-key aider-cli \
  --agent-command aider \
  --agent-arguments-template '--message "{Prompt}" --yes-always --no-auto-commits' \
  --model-argument-template '--model "ollama_chat/{Model}"' \
  --models qwen3.5:9b \
  --dry-run
```

Use the `.macos.sh` wrapper on macOS.

## Thin Surface Wrappers

| Surface | Windows | Linux/macOS wrappers | Default command assumption |
| --- | --- | --- | --- |
| Aider CLI | `scripts/test-aider-cli-models.ps1` | `scripts/test-aider-cli-models.linux.sh`, `scripts/test-aider-cli-models.macos.sh` | `aider` |
| Roo Code | Historical wrapper only | Historical wrapper only | Upstream retired; do not install or validate for new setups. |
| OpenCode | `scripts/test-opencode-cli-models.ps1` | `scripts/test-opencode-cli-models.linux.sh`, `scripts/test-opencode-cli-models.macos.sh` | `opencode run --auto --model "ollama/{Model}" "{Prompt}"` for generated-sample validation only; generate `.opencode.local.json` with the unified adapter and use `OPENCODE_CONFIG`. |

For any active surface whose CLI command or flags differ, pass command overrides rather than editing the harness.

## Dry Run Examples

```powershell
.\scripts\test-aider-cli-models.ps1 -Models "qwen3.5:9b" -DryRun
.\scripts\test-opencode-cli-models.ps1 -Models "qwen3.5:9b" -DryRun
```

Dry run reports are written under `runtime-validation-output/` and should not be committed.

## Live Test Examples

Use live tests only after the CLI command is installed and the model server is available.

```powershell
.\scripts\test-aider-cli-models.ps1 `
  -Models "qwen3.5:9b" `
  -UnloadAfterEach `
  -OllamaBaseUrl "http://127.0.0.1:11434"
```

For a generated Python scoped-edit test:

```powershell
.\scripts\test-opencode-cli-models.ps1 `
  -Models "devstral-small-2:24b" `
  -IncludeWriteSmoke `
  -IncludeScopedEdit `
  -UnloadAfterEach
```

For a maintained successor or any active surface whose CLI flags differ from a verified default:

```powershell
.\scripts\test-agent-cli-surface-models.ps1 `
  -SurfaceName "Successor Name" `
  -SurfaceKey "successor-cli" `
  -Models "qwen3.5:9b" `
  -AgentCommand "actual-command" `
  -AgentArgumentsTemplate 'actual flags with {Prompt}' `
  -ModelArgumentTemplate 'actual model flag with {Model}'
```

## Consolidation Direction

The long-term direction is a small set of shared engines plus optional thin wrappers, not a full duplicated script family for every agent plugin.

Keep the shared harness as the source of behavior. Surface-specific wrappers should only provide friendly defaults such as command names, model flags, and install hints. If wrapper count becomes hard to maintain, prefer a registry-driven dispatcher or a future web UI that calls the shared harness directly.

The planned starter-toolkit web UI should call stable script entry points for hardware profiling, model discovery, model testing, configuration generation, installation, and validation. It should not reimplement the business logic that already exists in scripts. The UI should make evidence visible by separating tested, passed, failed, and recommended-only states before applying changes.

## Safety Rules

- Use generated sample repositories by default.
- Do not run write smoke tests against a real project unless explicitly approved.
- Keep `--no-auto-commits` or equivalent behavior where the CLI supports it.
- Use `-UnloadAfterEach` / `--unload-after-each` for remote or shared Ollama servers.
- Treat every model and surface combination as separate evidence.
- Do not commit raw output, private endpoints, local paths, usernames, tokens, or private repository names.
## Confirmed Command Boundaries

- **OpenCode:** The official CLI documents `opencode run "{Prompt}"` for non-interactive use. Its model identifier is `provider_id/model_id`; a local Ollama setup needs a local-only `opencode.json` custom provider using the Ollama `/v1` endpoint. Do not commit that endpoint or any credentials.
- **Roo Code:** The upstream project is archived and the extension is shut down. Do not add new integration, configuration, or live-validation work; retain historical metadata only.
