# Agent CLI Surface Model Testing

## Purpose

Use this workflow to screen CLI-capable coding agent surfaces with the same disposable repository tests instead of maintaining separate full scripts for every agent plugin.

The shared harness supports:

- Aider CLI
- Roo Code CLI candidates
- Kilo Code CLI candidates
- OpenCode CLI

OpenHands is platform-style rather than a simple local CLI harness target, so it needs separate validation later.

## Current Boundary

These scripts are automation scaffolding. A dry run proves the harness wiring, not that a surface or model works.

A surface is not approved-write ready until it passes:

1. Read-only inspection against the intended repository or generated sample.
2. Disposable write-smoke validation, if the surface supports writes.
3. External verification with Git and direct file reads.
4. A realistic scoped edit in a disposable or explicitly approved repository.

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
| Roo Code | `scripts/test-roo-code-cli-models.ps1` | `scripts/test-roo-code-cli-models.linux.sh`, `scripts/test-roo-code-cli-models.macos.sh` | `roo-code` placeholder until confirmed |
| Kilo Code | `scripts/test-kilo-code-cli-models.ps1` | `scripts/test-kilo-code-cli-models.linux.sh`, `scripts/test-kilo-code-cli-models.macos.sh` | `kilo-code` placeholder until confirmed |
| OpenCode | `scripts/test-opencode-cli-models.ps1` | `scripts/test-opencode-cli-models.linux.sh`, `scripts/test-opencode-cli-models.macos.sh` | `opencode` |

For any surface whose CLI command or flags differ, pass command overrides rather than editing the harness.

## Dry Run Examples

```powershell
.\scripts\test-aider-cli-models.ps1 -Models "qwen3.5:9b" -DryRun
.\scripts\test-roo-code-cli-models.ps1 -Models "qwen3.5:9b" -DryRun
.\scripts\test-kilo-code-cli-models.ps1 -Models "qwen3.5:9b" -DryRun
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

For CLI flags that differ from the default wrapper:

```powershell
.\scripts\test-roo-code-cli-models.ps1 `
  -Models "qwen3.5:9b" `
  -AgentCommand "actual-command" `
  -AgentArgumentsTemplate 'actual flags with {Prompt}' `
  -ModelArgumentTemplate 'actual model flag with {Model}'
```

## Consolidation Direction

The long-term direction is a small set of shared engines plus optional thin wrappers, not a full duplicated script family for every agent plugin.

Keep the shared harness as the source of behavior. Surface-specific wrappers should only provide friendly defaults such as command names, model flags, and install hints. If wrapper count becomes hard to maintain, prefer a registry-driven dispatcher or a future web UI that calls the shared harness directly.

The planned web UI should call stable script entry points for hardware profiling, model discovery, model testing, configuration generation, and validation. It should not reimplement the business logic that already exists in scripts.
## Safety Rules

- Use generated sample repositories by default.
- Do not run write smoke tests against a real project unless explicitly approved.
- Keep `--no-auto-commits` or equivalent behavior where the CLI supports it.
- Use `-UnloadAfterEach` / `--unload-after-each` for remote or shared Ollama servers.
- Treat every model and surface combination as separate evidence.
- Do not commit raw output, private endpoints, local paths, usernames, tokens, or private repository names.
