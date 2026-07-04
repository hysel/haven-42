# Local Model Selection

## Purpose

This guide helps users choose a candidate local Ollama model for Continue based on machine capacity and workflow risk.

The goal is not to chase the largest model. The goal is to choose the smallest reliable model that can complete the task safely.

## Starter Recommendation

The committed config uses a smaller starter example:

```text
qwen3.5:9b
```

This model name is an example, not a permanent requirement. It is a more realistic starting point for a home PC than a 30B-class model.

Also install the embedding model:

```text
nomic-embed-text
```

The committed starter config uses `contextLength: 16384` and `maxTokens: 2048` to keep local Agent responses more responsive on common home-PC setups. Treat larger values as an explicit tuning choice for larger repositories, not as the default starting point.

## Selection Inputs

Before choosing a model, check:

- System RAM
- GPU VRAM
- Whether Ollama is using CPU only or GPU acceleration
- Target repository size
- Required context length
- Whether the workflow needs tools
- Whether the workflow can modify files
- Risk level of the task

Larger models usually need more memory and respond more slowly, but they may follow tool and planning instructions better.

Use a larger coding model, such as `qwen3-coder:30b`, only when your hardware profile and read-only tool validation show that your setup can handle it.

For the validation checklist, use `docs/model-tool-use-validation.md`.

## Hardware Profile Helper

Use the helper script for your operating system to collect a sanitized local profile.

Run these commands from the root of this repository. The root is the folder that contains `README.md`, `docs/`, and `scripts/`.

Prerequisites:

- Windows: PowerShell.
- Linux: Bash.
- macOS: Bash or zsh running the shell script.
- Optional for all platforms: Ollama installed and available on `PATH`.
- Optional for NVIDIA GPUs: `nvidia-smi`.
- Optional for AMD GPUs on Linux: `rocm-smi`.
- Optional for Linux GPU fallback: `lspci`.

Windows:

```powershell
.\scripts\get-local-model-profile.windows.ps1
```

Linux:

```bash
./scripts/get-local-model-profile.linux.sh
```

macOS:

```bash
./scripts/get-local-model-profile.macos.sh
```

If Linux or macOS reports a permission error, run:

```bash
chmod +x scripts/get-local-model-profile.linux.sh
chmod +x scripts/get-local-model-profile.macos.sh
```

Then run the script again.

The helpers report:

- Platform and operating system summary
- PowerShell version
- System RAM
- CPU summary
- CPU architecture
- Linux platform notes for ARM, Jetson, or Tegra indicators when available
- GPU names and VRAM when available
- GPU vendor and memory type when available
- Ollama reachability
- Installed Ollama model names
- MLX tooling status on macOS
- MLX candidate recommendation on macOS when MLX tooling is detected
- A low, medium, or high resource candidate tier
- A recommended model from the installed Ollama models, or a model to pull and validate

It does not collect hostnames, IP addresses, usernames, local filesystem paths, secrets, or custom Ollama endpoint values.

## Automatic Local Config Selection

The install scripts can create a local-only Continue config that uses the model recommended by the hardware profile helper.

Windows PowerShell:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project" -AutoModelConfig
```

Use `-TargetRepo` in Windows PowerShell. `-TargetRepository` is not a valid
installer parameter.

If your editor loads the global Continue config instead of the project-local
config, combine local model selection with global config generation:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project" -AutoModelConfig -GlobalConfig
```

The generated global config omits `rules:` by default to prevent duplicate rule
warnings when the project-local `.continue` folder is also present.

Linux:

```bash
./scripts/install-continue-pack.linux.sh --target-repo /path/to/your-project --auto-model-config
```

macOS:

```bash
./scripts/install-continue-pack.macos.sh --target-repo /path/to/your-project --auto-model-config
```

This writes `.continue/config.local.yaml` in the target repository after installation. That file is local-only and should not be committed. It uses the profile script's recommended installed model when available, while the shared `.continue/config.yaml` remains a portable starter sample.

## Model Lanes

For real work, it is safer to use different models for different risk levels
instead of giving every model permission to edit files.

Use model lanes when you want a local-only config with clear model routing:

| Lane | Purpose | Roles |
| --- | --- | --- |
| `1 - WRITE SAFE` | Small, validated edits after approval | `chat`, `edit`, `apply` |
| `2 - PLAN ONLY` | Implementation plans and scoped change proposals | `chat` |
| `3 - DEEP REVIEW` | Architecture, security, and maintainability reviews | `chat` |

The generated config also keeps `nomic-embed-text` as the embedding model. It
is not an Agent profile and does not receive `chat`, `edit`, or `apply` roles.

## Why These Profiles

These profiles are based on observed Continue Agent behavior, not only model
size or benchmark reputation.

| Profile | Model | Why it is used |
| --- | --- | --- |
| `1 - WRITE SAFE` | `qwen3.5:9b` | It produced the most reliable approved-write behavior in local testing. Use it for small, scoped edits after the editor Apply smoke test passes. |
| `2 - PLAN ONLY` | `devstral-small-2:24b` | It is useful for planning and reasoning, but it should stay chat-only until approved-write behavior is validated in the target editor. |
| `3 - DEEP REVIEW` | `qwen3-coder:30b` | It is useful for larger code review and architecture analysis, but write access is intentionally withheld because stronger analysis does not automatically mean safer patch application. |

Other tested models were removed from the generated profiles when they failed
tool support, produced raw tool-call text, leaked reasoning tags, behaved too
slowly for the workflow, or required unreliable multi-approval Apply behavior.

Treat these models as validated defaults for this pack, not permanent
requirements. If a newer local model performs better, add it only after
recording sanitized read, plan, and approved-write evidence.

Windows PowerShell:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project" -ModelLanes
```

Linux:

```bash
./scripts/install-continue-pack.linux.sh --target-repo /path/to/your-project --model-lanes
```

macOS:

```bash
./scripts/install-continue-pack.macos.sh --target-repo /path/to/your-project --model-lanes
```

If your editor uses the global Continue config, combine model lanes with global
config generation and pass the endpoint only at install time:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -ModelLanes `
  -GlobalConfig `
  -GlobalConfigApiBase "http://127.0.0.1:11434"
```

The generated lane model names are examples based on local validation. Keep
private endpoints and machine-specific changes in local or global config files,
not in committed shared config.

Only the WRITE SAFE lane should have `edit` and `apply` roles. If another model
later passes approved-write validation, update your local config intentionally
and record sanitized evidence with `examples/model-tool-use-validation.md`.

## How Model Recommendations Work

The helper scripts use a rule-based recommendation. They do not benchmark models, download models, query online model rankings, or prove that a model is safe for edits.

The process is:

1. Detect the local hardware profile.
2. Classify the machine as a low, medium, or high resource candidate.
3. Ask Ollama for the models installed on the local LLM server.
4. Read `config/model-recommendations.tsv`.
5. Scan rows for the detected tier from top to bottom.
6. Recommend the first installed model whose name matches the row pattern.
7. Use the tier fallback when no installed model matches.

In other words, the recommendation depends on both the local machine and the models available on the local Ollama server.

The catalog is an opinionated starting point. The "right" model still needs validation for the workflow you want to run. Before approved write mode, run the checklist in `docs/model-tool-use-validation.md` and confirm that the model can follow instructions, use tools when needed, avoid raw tool-call JSON, and produce evidence-based output.

When updating `config/model-recommendations.tsv`, remember that order matters. Put the preferred model patterns first within each tier, keep one fallback row per tier, and avoid machine-specific endpoints, local paths, or private model names.

For automation or sanitized notes, use JSON output.

Windows:

```powershell
.\scripts\get-local-model-profile.windows.ps1 -AsJson
```

Linux:

```bash
./scripts/get-local-model-profile.linux.sh --json
```

macOS:

```bash
./scripts/get-local-model-profile.macos.sh --json
```

GPU detection is best-effort:

- NVIDIA GPUs use `nvidia-smi` when available.
- AMD GPUs on Linux use `rocm-smi` when available.
- AMD and other GPUs on Windows use display adapter registry data when available, then `dxdiag` for dedicated display memory.
- Intel GPUs are detected through platform display APIs or `lspci`; integrated/shared memory is reported as shared or unknown instead of dedicated VRAM.
- Windows falls back to `Win32_VideoController`.
- Linux falls back to `lspci` when available.
- macOS falls back to `system_profiler`.

On Linux, `Platform notes` will warn when `nvidia-smi`, `rocm-smi`, and `lspci` are all missing, or when detection tools are present but no GPU is found. This is common on minimal distributions, containers, hardened servers, and cloud images before GPU drivers or device passthrough are configured.

On Linux, `Platform notes` also warn when common container or LXC-style indicators are detected. In that case, treat RAM, GPU, and driver details as the capacity visible from inside that environment, not necessarily the physical host capacity.

If GPU VRAM is unknown, use the profile as a starting point and avoid high-risk tool-backed workflows until the model is validated.

## Reading The Output

Use the output as a guide, not as an automatic decision.

Important fields:

- `RAM`: Helps decide whether the machine can handle larger models.
- `Architecture`: Shows the normalized CPU architecture, such as `x64`, `arm64`, or `armv7`.
- `Platform notes`: On Linux, shows conservative notes for ARM, Jetson, or Tegra-style systems when indicators are visible.
- `GPU`: Shows detected GPU names and best-effort memory information.
- `Vendor`: Helps identify NVIDIA, AMD, Intel, Apple, or unknown GPU paths.
- `MemoryType`: Shows whether memory appears dedicated, shared/integrated, unified, or unknown.
- `Ollama`: Shows whether the helper can run `ollama list`.
- `Installed Ollama models`: Shows local model names only.
- `MLX tooling`: On macOS, shows whether common MLX commands or Python modules are visible to the current shell.
- `Platform notes`: On Linux, highlights ARM, Jetson/Tegra, missing GPU detection tools, no detected GPU, and container-style environments.
- `Recommendation tier`: A starting point for low, medium, or high resource guidance.
- `Recommended model`: The first installed model that matches the machine tier and workflow guidance, or a model to pull and test.
- `Recommended use`: How to use the recommended model safely.
- `Validation note`: What to verify before trusting the model for tool-backed or high-risk work.

The recommendation rules live in `config/model-recommendations.tsv`. Update that catalog when better local models are validated. The scripts can also use a local catalog file for private model names:

Windows:

```powershell
.\scripts\get-local-model-profile.windows.ps1 -ModelCatalogPath .\model-recommendations.local.tsv
```

Linux:

```bash
./scripts/get-local-model-profile.linux.sh --model-catalog ./model-recommendations.local.tsv
```

macOS:

```bash
./scripts/get-local-model-profile.macos.sh --model-catalog ./model-recommendations.local.tsv
```

Do not commit private internal model names unless they are safe for the public repository.

The shared `config/model-recommendations.tsv` catalog is for Ollama-discovered models. The macOS helper also reads `config/model-recommendations.mlx.tsv` for advanced Apple Silicon MLX candidates. MLX recommendations are reported separately from Ollama recommendations because MLX models are not discovered through `ollama list`.

Common results:

- `Unknown VRAM`: The OS did not expose reliable GPU memory. Do not assume the GPU can run large models.
- `shared or integrated`: Common for Intel integrated GPUs. Treat this as system-memory-backed, not dedicated model VRAM.
- `unified`: Common on Apple Silicon. Use total system memory and real-world model testing.
- `ollama command not found`: Ollama is not installed, not on `PATH`, or not visible to the current shell.
- `installed but not reachable or no models listed`: Ollama may not be running, or no models have been pulled.

After running the profile:

1. Compare the output to the hardware tiers below.
2. Review the recommended model.
3. Start with read-only prompts.
4. Test tool execution with `docs/model-tool-use-validation.md` before approved write mode.
5. Use smaller models for review-only work when hardware is limited.
6. Use the strongest validated local model for tool-backed edits and high-risk workflows.

Manual fallback commands:

```powershell
ollama list
```

Windows:

```powershell
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
Get-CimInstance Win32_Processor | Select-Object Name,NumberOfLogicalProcessors
Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM
```

Linux:

```bash
head -n 5 /proc/meminfo
lscpu
nvidia-smi
rocm-smi --showproductname --showmeminfo vram
lspci
```

macOS:

```bash
sysctl -n hw.memsize
sysctl -n machdep.cpu.brand_string
system_profiler SPDisplaysDataType
```

## Workflow Risk Levels

### Low Risk

Examples:

- Repository discovery
- Documentation summaries
- Explaining files
- Drafting checklists

Model guidance:

- Smaller coding models may be acceptable.
- Runtime-context workflows are acceptable if tools are unreliable.
- Human review is still required.

### Medium Risk

Examples:

- Implementation planning
- Code review
- Architecture review
- Performance triage

Model guidance:

- Prefer a stronger coding model.
- Require evidence, affected files, validation steps, and rollback steps.
- Retry with more context if the answer is generic.

### High Risk

Examples:

- Approved write mode
- Tool-backed edits
- Legacy dependency migration
- Security-sensitive recommendations
- Release-readiness decisions
- Authentication, authorization, CI, deployment, or production-data changes

Model guidance:

- Use only a model that has been validated with the exact Continue workflow.
- For tool-backed edits, verify that the model executes tools instead of printing raw JSON tool calls.
- Prefer plan-only first, then one scoped edit at a time.
- Stop if the model ignores boundaries or invents details.

## Hardware Tiers

These tiers are starting points. Exact performance depends on quantization, drivers, available memory, repository size, and what else is running.

### Low Resource

Typical machine:

- CPU-only or limited GPU
- Less than 16 GB system RAM
- Less than 8 GB VRAM

Recommended usage:

- Review-only workflows
- Documentation help
- Runtime-context workflows
- Small files and short prompts

Avoid:

- Approved write mode
- Large repository-wide context
- High-risk migrations
- Tool-heavy Agent workflows unless validated

### Medium Resource

Typical machine:

- 16-32 GB system RAM
- 8-16 GB VRAM, or strong CPU fallback

Recommended usage:

- Repository discovery
- Implementation planning
- Code review
- Documentation review
- Small approved edits after validation

Use caution with:

- Long context windows
- Large generated diffs
- Security-sensitive or release decisions

### High Resource

Typical machine:

- 32 GB or more system RAM
- 16 GB or more VRAM
- Enough headroom for editor, Ollama, build tools, and tests

Recommended usage:

- Larger coding models such as `qwen3-coder:30b`, when validated on the exact machine and editor setup
- Agent mode after read-only tool validation
- Scoped approved edits
- Larger context windows when needed

Still required:

- Human review
- Validation
- Rollback plan
- Git diff review before commit

## ARM And Apple Silicon Guidance

ARM machines need a slightly different mental model than traditional x64 workstations with dedicated GPU VRAM.

Apple Silicon:

- Apple Silicon Macs use unified memory, so system RAM and model memory share the same pool.
- A 16 GB Mac should be treated conservatively for coding-agent workflows, even if smaller models run well.
- A 32 GB or larger Mac is a better starting point for medium and larger coding models.
- Ollama with GGUF models remains the default beginner path because it is easy to install and works with this pack's default Continue setup.
- MLX models can perform well on Apple Silicon, but they are a separate serving path and should be treated as advanced setup.

Windows ARM:

- Windows ARM local LLM acceleration varies by device, driver, runtime, and model provider.
- Treat Windows ARM as conservative until the exact model, Continue setup, and tool execution path are validated.
- CPU-only operation may work for review and planning, but tool-backed edits should wait for a successful read-only tool test.

Linux ARM:

- Linux ARM ranges from small boards to cloud ARM instances to Jetson-style devices.
- Generic Linux ARM systems should be treated as conservative unless GPU acceleration is known to work.
- NVIDIA Jetson and other ARM GPU paths may need platform-specific drivers and detection logic before recommendations can be trusted.
- The Linux helper reports platform notes when it sees ARM architecture, `/etc/nv_tegra_release`, or Jetson/Tegra/NVIDIA device-tree indicators.
- Jetson/Tegra detection is a caution signal only; it does not prove CUDA, JetPack, Ollama acceleration, or container device access is working.

Architecture should not automatically increase trust in a model recommendation. Use the profile output to understand the machine, then validate the actual model and workflow.

Architecture does not currently change recommendation tiering. This is intentional. `arm64` can describe very different machines, including Apple Silicon Macs, Windows ARM laptops, Linux cloud instances, and Jetson-style devices. The pack treats architecture as context and warning evidence, while memory capacity, detected GPU details, installed Ollama models, and workflow validation remain the safer recommendation inputs.

## Ollama, GGUF, And MLX

Ollama usually runs GGUF-style local models and exposes an Ollama-compatible local API. This is the default path for the pack.

MLX is a separate Apple Silicon-focused model runtime. MLX models are not discovered by `ollama list`, and the hardware profile scripts should not treat MLX-hosted models as Ollama-installed models.

The macOS helper reports MLX tooling separately when it can detect common commands or Python modules such as:

- `mlx-lm`
- `mlx_lm.generate`
- `mlx_lm.chat`
- `mlx_lm.server`
- Python modules named `mlx_lm` or `mlx`

Detection means the tooling is visible to the current shell. It does not prove that an MLX model is installed, loaded, served through an API, or compatible with Continue.

When MLX tooling is detected, the macOS helper also reports a separate MLX recommendation from `config/model-recommendations.mlx.tsv`. This recommendation is a candidate, not a verified installed model. It does not replace the Ollama recommendation and it does not change the default beginner setup path.

If you want to use MLX with Continue:

- Run an MLX-compatible local server that exposes an OpenAI-compatible API.
- Configure Continue locally to use that endpoint.
- Keep the endpoint, model names, and machine-specific settings out of committed config.
- Run the same read-only tool validation before using Agent mode or approved write mode.

Do not add MLX-only model names to `config/model-recommendations.tsv`. Use `config/model-recommendations.mlx.tsv` for MLX candidate guidance. If future providers are added, prefer provider-specific catalogs or a richer provider-aware schema instead of mixing discovery mechanisms in one file.

## Unified, Shared, And Dedicated Memory

Memory type changes how model recommendations should be read.

Dedicated VRAM:

- Common on NVIDIA and many AMD desktop/server GPUs.
- The model can use GPU memory without taking the same pool as system RAM.
- Still leave headroom for the OS, editor, Ollama, build tools, and tests.

Unified memory:

- Common on Apple Silicon.
- CPU, GPU, OS, editor, and model all share one memory pool.
- Treat total RAM as shared capacity, not as dedicated model memory.

Shared or integrated memory:

- Common on Intel integrated GPUs and some low-power systems.
- GPU memory may be borrowed from system RAM.
- Treat this as a conservative signal for local model size.

Unknown memory:

- The script could not determine reliable memory details.
- Start with smaller models and validate before using tools or write mode.

## Model Capability Checklist

Before using a model for tool-backed work, test it with a safe prompt:

```text
Use tools to list the repository files. Do not modify files.
```

Good result:

- Continue runs the tool.
- The assistant returns a normal text summary.

Bad result:

```json
{"name":"ls","arguments":{"dirPath":".","recursive":true}}
```

If the model prints raw JSON instead of executing the tool, do not use that model for approved write mode.

## Choosing By Task

Use this matrix as a default:

| Task | Suggested model posture |
| --- | --- |
| Discovery or summary | Any locally reliable coding model with enough context |
| Documentation drafting | Small or medium model is acceptable with review |
| Implementation planning | Prefer stronger coding model and require validation/rollback sections |
| Code review | Prefer stronger coding model and require file-specific findings |
| Architecture/security/performance review | Prefer stronger model; require evidence and assumptions |
| Tool-backed edits | Use validated tool-capable model only |
| Dependency migration or release readiness | Use strongest available model plus human review and fixed templates |

## Recommended Model Tiers

The helper scripts use `config/model-recommendations.tsv` when selecting an installed model.

| Resource tier | Preferred installed models | Best use |
| --- | --- | --- |
| High | `qwen3.5:9b`, `devstral-small-2:24b`, `qwen3-coder:30b` | WRITE SAFE edits after validation, PLAN ONLY workflows, and DEEP REVIEW workflows |
| Medium | `qwen3.5:9b`, `devstral-small-2:24b`, `qwen3-coder:30b` only when local hardware can run it acceptably | Keep write access limited to the validated WRITE SAFE profile |
| Low | `qwen3.5:9b` after latency and write validation are acceptable; otherwise use read-only or plan-only workflows | Focused context, one scoped edit at a time, and no approved writes until validation passes |

These recommendations are intentionally conservative. A model is not approved for tool-backed edits until it successfully runs a read-only tool test in Continue and the result is recorded using the validation evidence template.

## Context Length Guidance

Use only the context needed for the task.

For small tasks:

- Current file
- Related files
- Existing tests
- Relevant docs

For larger reviews:

- Generate `runtime-context.md`
- Attach selected files
- Ask the model to state unknowns

Avoid sending an entire large repository when a focused slice is enough. More context can make local models slower and less precise.

## Local Override Safety

Keep the committed config portable.

Do not commit:

- Private IP addresses
- Private hostnames
- VPN endpoints
- Machine-specific ports
- Experimental model names that only exist on one machine
- Hardware notes that identify a private workstation

Use ignored local config files for machine-specific changes:

```text
.continue/config.local.yaml
```

If you test a new model, record only sanitized results using `examples/model-tool-use-validation.md`:

- Model family and size
- Workflow tested
- Pass or fail
- Failure mode
- No private endpoint details

## Recommended Starting Flow

1. Start with the committed starter model or the model selected by `--auto-model-config`.
2. Run a read-only repository discovery prompt.
3. Test tool execution with `docs/model-tool-use-validation.md`.
4. If tools work, try plan-only workflows.
5. If planning is reliable, approve one scoped edit.
6. Validate the edit.
7. Record sanitized findings if they change the pack guidance.

## When To Use A Smaller Model

Use a smaller model when:

- The machine cannot run the starter model comfortably.
- The workflow is read-only.
- The task is summarization or documentation drafting.
- The user can provide a focused context file.
- The result will be reviewed before action.

Do not use a smaller unvalidated model for high-risk tool-backed changes.

## When To Upgrade The Model

Use a stronger model when:

- The response is generic or shallow.
- The model ignores "plan only" or "do not modify files."
- The model invents package versions, file paths, test results, or endpoints.
- The model prints raw JSON tool calls.
- The task touches security, dependency management, release readiness, or production behavior.

## Related Docs

- `docs/local-model-reliability.md`
- `docs/model-tool-use-validation.md`
- `docs/tool-use-modes.md`
- `docs/approved-tool-backed-changes.md`
- `docs/scoped-edits.md`
- `docs/troubleshooting.md`
