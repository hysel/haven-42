# Local Model Selection

## Purpose

This guide helps users choose a local Ollama model for Continue based on machine capacity and workflow risk.

The goal is not to chase the largest model. The goal is to choose the smallest reliable model that can complete the task safely.

## Default Recommendation

Use the committed default first when your machine can run it:

```text
qwen3-coder:30b
```

This is the current validated default for chat, edit, apply, and Agent tool workflows in this pack.

Also install the embedding model:

```text
nomic-embed-text
```

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
- GPU names and VRAM when available
- GPU vendor and memory type when available
- Ollama reachability
- Installed Ollama model names
- A low, medium, or high resource candidate tier

It does not collect hostnames, IP addresses, usernames, local filesystem paths, secrets, or custom Ollama endpoint values.

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
- AMD and other GPUs on Windows use display adapter registry data when available.
- Intel GPUs are detected through platform display APIs or `lspci`; integrated/shared memory is reported as shared or unknown instead of dedicated VRAM.
- Windows falls back to `Win32_VideoController`.
- Linux falls back to `lspci` when available.
- macOS falls back to `system_profiler`.

If GPU VRAM is unknown, use the profile as a starting point and avoid high-risk tool-backed workflows until the model is validated.

## Reading The Output

Use the output as a guide, not as an automatic decision.

Important fields:

- `RAM`: Helps decide whether the machine can handle larger models.
- `GPU`: Shows detected GPU names and best-effort memory information.
- `Vendor`: Helps identify NVIDIA, AMD, Intel, Apple, or unknown GPU paths.
- `MemoryType`: Shows whether memory appears dedicated, shared/integrated, unified, or unknown.
- `Ollama`: Shows whether the helper can run `ollama list`.
- `Installed Ollama models`: Shows local model names only.
- `Recommendation tier`: A starting point for low, medium, or high resource guidance.

Common results:

- `Unknown VRAM`: The OS did not expose reliable GPU memory. Do not assume the GPU can run large models.
- `shared or integrated`: Common for Intel integrated GPUs. Treat this as system-memory-backed, not dedicated model VRAM.
- `unified`: Common on Apple Silicon. Use total system memory and real-world model testing.
- `ollama command not found`: Ollama is not installed, not on `PATH`, or not visible to the current shell.
- `installed but not reachable or no models listed`: Ollama may not be running, or no models have been pulled.

After running the profile:

1. Compare the output to the hardware tiers below.
2. Start with read-only prompts.
3. Test tool execution before approved write mode.
4. Use smaller models for review-only work when hardware is limited.
5. Use the strongest validated local model for tool-backed edits and high-risk workflows.

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

- `qwen3-coder:30b` as the default coding and tool-capable model
- Agent mode after read-only tool validation
- Scoped approved edits
- Larger context windows when needed

Still required:

- Human review
- Validation
- Rollback plan
- Git diff review before commit

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

If you test a new model, record only sanitized results in committed docs:

- Model family and size
- Workflow tested
- Pass or fail
- Failure mode
- No private endpoint details

## Recommended Starting Flow

1. Start with the committed default model.
2. Run a read-only repository discovery prompt.
3. Test tool execution with a safe list-files request.
4. If tools work, try plan-only workflows.
5. If planning is reliable, approve one scoped edit.
6. Validate the edit.
7. Record sanitized findings if they change the pack guidance.

## When To Use A Smaller Model

Use a smaller model when:

- The machine cannot run the default model comfortably.
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
- `docs/tool-use-modes.md`
- `docs/approved-tool-backed-changes.md`
- `docs/scoped-edits.md`
- `docs/troubleshooting.md`
