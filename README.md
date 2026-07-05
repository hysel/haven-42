# Local Engineering Agent Pack

Local-first engineering assistant pack for developers, small teams, and enterprise groups that want repeatable AI-assisted review workflows and opinionated guidance for .NET and Clean Architecture repositories.

In plain terms: this repository gives an AI coding agent a ready-made set of prompts, rules, and templates so it can help review, plan, and safely improve software projects in a more consistent way.

Continue is the first supported agent surface because it is the current tested path for local Ollama workflows. The project is intentionally moving toward reusable agent assets that can also be validated with other open-source coding assistants over time.

## Purpose

The goal of this pack is to provide a reusable engineering assistant setup, starting with Continue, with workflows for repository discovery, implementation planning, code review, security review, architecture review, performance review, documentation, and product management.

It is designed for people who want AI support to follow consistent engineering standards instead of relying on ad hoc prompts, whether they are hobby developers, consultants, small teams, or enterprise engineering groups.

## Which Path Should I Use?

| If you want to... | Start here |
| --- | --- |
| Install the pack in a project | `Quick Start` |
| Pick the right local model | `docs/local-model-selection.md` |
| Evaluate newer model candidates | `docs/online-model-discovery.md` |
| Validate whether a model can use tools | `docs/model-tool-use-validation.md` |
| Automate local model preflight tests | `docs/local-agent-model-testing.md` |
| Test VS Code or VSCodium setup | `docs/editor-compatibility.md` |
| Let Continue edit files | `docs/tool-use-modes.md` and `docs/scoped-edits.md` |
| Use MCP tools | `docs/mcp-setup.md` and `docs/mcp-examples.md` |
| Validate this pack across repository types | `docs/multi-repository-validation.md` |
| Verify runtime model output | `docs/runtime-output-verification.md` |
| Compare other open-source agent surfaces | `docs/agent-surface-options.md` |
| Track multi-language support | `docs/language-support.md` |
| Generate local sample repositories | `docs/sample-repository-factory.md` |
| Validate this pack | `Quick Validation` |
| Fix setup problems | `Common Problems` and `docs/troubleshooting.md` |

## Quick Start

Use this path if you are new to Continue, Ollama, or command-line tools. The steps work on Windows, Linux, and macOS.

### 1. Install the basics

Install:

- Ollama: runs the local AI models.
- Node.js: lets you run the Continue CLI with `npx`.
- Continue for your editor: the extension you will use inside VS Code, VSCodium, or another supported editor.

Then open a terminal and check the tools:

Windows PowerShell:

```powershell
ollama --version
node --version
npx --version
```

Linux or macOS:

```bash
ollama --version
node --version
npx --version
```

### 2. Download example local models

The model names below are examples, not permanent requirements. Local model availability changes over time, and the best model depends on your RAM, VRAM, installed Ollama models, and whether you need Agent tools.

The committed config starts with a smaller sample model. If your machine can run a larger model, the hardware profile and install scripts can create a local-only config that selects a stronger installed model automatically.

The starter config also uses responsive defaults for local machines: `contextLength: 16384` and `maxTokens: 2048`. Increase those values only after the model feels reliable and you need deeper context for larger repositories.

Windows PowerShell:

```powershell
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

Linux or macOS:

```bash
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

Optional stronger models for high-resource machines after validation:

```bash
ollama pull devstral-small-2:24b
ollama pull qwen3-coder:30b
```

The model helper scripts use `config/model-recommendations.tsv` as the curated model priority list. You usually do not need to edit it during setup. Update it only after validating a better local model for your hardware and workflow.

Optional online model discovery is candidate research only. It should not
change the offline default setup, pull models automatically, or mark a model as
tool-safe without local validation. See `docs/online-model-discovery.md`.

To pull and preflight Agent model candidates through the Ollama API before
manual Continue Apply testing, use `docs/local-agent-model-testing.md`.

## Model Selection

If you are unsure which model fits your machine, run the hardware profile script:

Windows PowerShell:

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

Then use `docs/local-model-selection.md` to choose the final model. Treat the script recommendation as a starting point, not proof that the model is safe for approved edits. Use `docs/model-tool-use-validation.md` before trusting a model for Agent tools or approved write mode.

To install this pack and create a local-only config using the recommended installed model, use `--auto-model-config` with the install script.

### 3. Copy this pack into your project

Copy the `.continue` folder from this repository into the project you want to review.

Your project should then look like this:

```text
your-project/
  .continue/
    config.yaml
    prompts/
    rules/
    agents/
    templates/
```

If your project already has a `.continue` folder, back it up first or compare the files before replacing anything.

### 4. Start Ollama

Make sure Ollama is running. To check it, run:

Windows PowerShell:

```powershell
ollama list
```

Linux or macOS:

```bash
ollama list
```

If the command shows your models, you are ready.

### 5. Open your project in Continue

Open the project you want to review, not this pack repository.

Continue should use the config file that now lives inside that project:

```text
.continue/config.yaml
```

Use the project-local copy of `.continue/config.yaml`. Do not point Continue at the original pack folder after you copy the pack into your project.

Quick checks:

- The editor file explorer shows your project files.
- Your project has `.continue/config.yaml`.
- Continue shows the local Ollama model from that config.
- Continue can see the prompts such as `repository-discovery` and `implementation-plan`.

If Continue does not show a model or prompts, make the copied `.continue/config.yaml` your active Continue config. Some editor setups use a global/default Continue config; in that case, copy this project's config into the default Continue config location or select it through your editor's Continue settings.

If you see duplicate rule warnings, you probably loaded the same rules from both the global Continue config and the project-local `.continue` folder. Keep only one active source of rules.

For VS Code, VSCodium, Agent mode, duplicate-rule, and CLI fallback checks, use `docs/editor-compatibility.md`.

### 6. Run a read-only prompt first

Start with one of these:

- `repository-discovery`
- `implementation-plan`
- `code-review`
- `documentation`
- `release-readiness`

Good first request:

```text
Run repository discovery for this project.
Do not modify files.

Identify:
1. The project type
2. The major files and folders
3. The current architecture
4. The main risks
5. The suggested next steps
```

## Using The Pack Day To Day

Use this flow after the pack is installed and Continue can see the model.

1. Start with read-only discovery or planning.
2. Review the response and check whether the assistant used real project evidence.
3. Ask for an implementation plan before approving changes.
4. Approve one small change at a time.
5. Run the smallest useful validation after each change.
6. Use `git status` to confirm exactly what changed.

Good day-to-day prompts:

```text
Create an implementation plan for this change.
Do not modify files yet.
List affected files, risks, tests, rollback, and definition of done.
```

```text
Review the current changes.
Focus on bugs, regressions, missing tests, security risks, and maintainability.
Do not modify files.
```

```text
Use approved write mode for this task only.
Edit only the files needed for the approved plan.
After editing, explain the diff and tell me what validation you ran.
```

In approved write mode, Continue should use edit/apply tools. If the assistant says it cannot directly edit files, only explains what it would do, or asks you to create files manually, write tools are not validated yet. Use the smoke test in `docs/tool-use-modes.md`.

For real code changes, also confirm the assistant can read file contents, not
just list files. If it cannot read the files it wants to change, stop and fix
tool access before approving implementation.

After any approved write, verify the diff yourself. If the assistant says it
changed a file but `git diff -- <file>` is empty, the write did not apply.

Before approving write mode, read:

- `docs/tool-use-modes.md`
- `docs/scoped-edits.md`
- `docs/approved-tool-backed-changes.md`
- `docs/model-tool-use-validation.md`

## Quick Validation

Run the validation script from this repository after copying or editing the pack.

Windows PowerShell:

```powershell
.\scripts\validate-pack.ps1
.\scripts\test-pack.ps1
```

Linux:

```bash
./scripts/validate-pack.linux.sh
./scripts/test-pack.linux.sh
```

macOS:

```bash
./scripts/validate-pack.macos.sh
./scripts/test-pack.macos.sh
```

The Linux and macOS validation scripts are native Bash scripts and do not require PowerShell.

## Install Or Update A Target Repository

Use the installer to copy this pack into the repository you want to review.

Windows PowerShell uses the parameter name `-TargetRepo`. Do not use
`-TargetRepository`; that is not a valid installer parameter.

Preview what would be copied:

Windows PowerShell:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project" -DryRun
```

Linux:

```bash
./scripts/install-continue-pack.linux.sh --target-repo /path/to/your-project --dry-run
```

macOS:

```bash
./scripts/install-continue-pack.macos.sh --target-repo /path/to/your-project --dry-run
```

Install or update the target repository:

Windows PowerShell:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project"
```

Create a local-only config with automatic model selection:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project" -AutoModelConfig
```

Create a local-only config with safer model lanes:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project" -ModelLanes
```

After a model passes local validation, install it into one local-only profile
without changing committed shared config:

```powershell
.\scripts\install-validated-model.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -Model "devstral-small-2:24b" `
  -Profile plan-only
```

If your editor uses the global Continue config instead of the project-local
`.continue/config.yaml`, install the pack and update the global config with
absolute references to the target repository's installed prompts and docs:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project" -GlobalConfig
```

Generated global config omits `rules:` by default. This avoids duplicate rule
warnings when the opened project also has `.continue/rules`. Use the default
unless you are intentionally running from global config only.

For a local-network Ollama server, keep the endpoint out of committed project
files and pass it only when generating the global config:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -GlobalConfig `
  -GlobalConfigApiBase "http://127.0.0.1:11434"
```

For a global config that uses model lanes and a local-network Ollama server:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -ModelLanes `
  -GlobalConfig `
  -GlobalConfigApiBase "http://127.0.0.1:11434"
```

Only include rules in the global config when the editor will not also load the
project-local `.continue` folder:

```powershell
.\scripts\install-continue-pack.ps1 -TargetRepo "C:\path\to\your-project" -GlobalConfig -GlobalConfigIncludeRules
```

Linux:

```bash
./scripts/install-continue-pack.linux.sh --target-repo /path/to/your-project
```

Create a local-only config with automatic model selection:

```bash
./scripts/install-continue-pack.linux.sh --target-repo /path/to/your-project --auto-model-config
```

Create a local-only config with safer model lanes:

```bash
./scripts/install-continue-pack.linux.sh --target-repo /path/to/your-project --model-lanes
```

After a model passes local validation, install it into one local-only profile
without changing committed shared config:

```bash
./scripts/install-validated-model.linux.sh \
  --target-repo /path/to/your-project \
  --model devstral-small-2:24b \
  --profile plan-only
```

Update the global Continue config when the editor does not load the project-local
config:

```bash
./scripts/install-continue-pack.linux.sh --target-repo /path/to/your-project --global-config
```

macOS:

```bash
./scripts/install-continue-pack.macos.sh --target-repo /path/to/your-project
```

Create a local-only config with automatic model selection:

```bash
./scripts/install-continue-pack.macos.sh --target-repo /path/to/your-project --auto-model-config
```

Create a local-only config with safer model lanes:

```bash
./scripts/install-continue-pack.macos.sh --target-repo /path/to/your-project --model-lanes
```

After a model passes local validation, install it into one local-only profile
without changing committed shared config:

```bash
./scripts/install-validated-model.macos.sh \
  --target-repo /path/to/your-project \
  --model devstral-small-2:24b \
  --profile plan-only
```

Update the global Continue config when the editor does not load the project-local
config:

```bash
./scripts/install-continue-pack.macos.sh --target-repo /path/to/your-project --global-config
```

The installer:

- Copies the pack's `.continue` files into the target repository.
- Excludes local config overrides such as `.continue/config.local.yaml`.
- Backs up an existing target `.continue` folder before replacing it.
- Validates that copied config file references resolve.
- Can create `.continue/config.local.yaml` with the model recommended by the hardware profile helper.
- Can create `.continue/config.local.yaml` with three Agent model profiles: WRITE SAFE, PLAN ONLY, and DEEP REVIEW. By default, all three use the simple-hardware starter model, plus the separate embedding model.
- Can install a selected validated model into one local-only profile without changing committed shared config.
- Can update the global Continue config, with a backup, when an editor does not load project-local config files.
- Omits rules from generated global config by default to avoid duplicate rule warnings.
- Writes Windows global config file references as `file://C:/path/...` for VSCodium compatibility.
- Refuses to install into this pack repository itself.

Linux and macOS installer wrappers are native Bash scripts and do not require PowerShell.

## Common Problems

Use the detailed guides in `docs/`, starting with `docs/troubleshooting.md`.

| Problem | What to try first |
| --- | --- |
| Continue does not show a model | Confirm Continue is using `.continue/config.yaml`, then run `ollama list`. |
| Ollama connection error | Start Ollama and confirm `ollama list` works in a terminal. |
| The starter model is too slow or will not load | Run the hardware profile script and follow `docs/local-model-selection.md`. |
| `cn` is not recognized | Use `npx @continuedev/cli --config .continue/config.yaml` or install the Continue CLI globally. |
| The assistant prints raw JSON tool calls | Use a stronger tool-capable model or the runtime-context fallback in `docs/troubleshooting.md`. |
| The assistant creates a file in the wrong folder | Stop, check `git status --short --untracked-files=all`, remove only the wrong test artifact, and use the `PATH_AMBIGUOUS` guidance in `docs/troubleshooting.md`. |
| The Apply panel targets the wrong file | Do not click Apply; treat it as `APPLY_TARGET_MISMATCH` and use `docs/troubleshooting.md`. |
| The assistant prints `edit_file` but nothing changes | Treat it as `WRITE_NOT_APPLIED`; tool-call text is not proof that the file changed. |
| The assistant says it created and read back a file, but PowerShell or shell cannot find it | Treat it as `WRITE_NOT_APPLIED`; approved-write readiness requires external `git status` plus file existence/content checks. |
| Two approval prompts duplicate the same line | For existing-file validation, temporarily set `create_new_file` to Excluded, pre-create `continue-agent-write-test.md`, and approve only one edit diff. |
| The assistant says no file is open and asks for a path | Keep the repository folder open in the editor and use the `WORKSPACE_UNAVAILABLE` guidance in `docs/troubleshooting.md`. |
| Linux or macOS validation script is not executable | Run `chmod +x scripts/*.sh`, then rerun the wrapper script. |
| Duplicate rules appear in Continue | Regenerate the global config without `-GlobalConfigIncludeRules`; the default global config omits rules to avoid duplicates with project-local `.continue/rules`. |

## Beginner Safety Rules

- Start with review and planning prompts before asking for changes.
- Do not commit private IP addresses, tokens, local paths, or raw company code into this pack.
- Keep machine-specific settings in local files, not in `.continue/config.yaml`.
- Use `docs/local-config-safety.md` before adding local endpoints, model experiments, or hardware details.
- Treat AI output as a draft. Review it before changing code.
- Use `git status` before and after AI-assisted work so you know what changed.
- Use `docs/tool-use-modes.md` before asking the assistant to modify a reviewed project.
- Use `docs/scoped-edits.md` to turn an approved plan into one small, reviewable change at a time.
- When you name a file without a folder, the assistant should assume the currently opened repository folder first. If it creates a duplicate such as `src/README.md` instead of editing the existing `README.md`, treat that as a failed write test.
- If no file is open, the assistant should still try to discover the opened workspace with tools before asking you for a path.
- Before clicking Apply, confirm the Apply target is the same file the assistant read and said it would change.
- For existing-file write tests, exclude `create_new_file` and pre-create the target file so the assistant must use one edit path. Two approvals for the same target can duplicate content.
- Treat any validation answer that combines a failure signal with a successful status label as failed or limited; for example, `READ_TOOLS_UNAVAILABLE` cannot be `read-only tool validated`.

## Do Not Commit These

Keep these out of committed files:

- `.continue/config.local.yaml`
- Private IP addresses, internal hostnames, or local-network endpoints
- API keys, GitHub tokens, SonarQube tokens, or other secrets
- Usernames, home-directory paths, or machine-specific paths
- Raw runtime validation output
- Private repository names or customer names
- Hardware profiles that include sensitive machine details

Use `docs/local-config-safety.md` before adding local endpoints, model experiments, hardware details, or tool configuration.

## Intended Capabilities

- Local LLM support through Continue and Ollama
- Enterprise .NET and ASP.NET Core guidance
- Clean Architecture review and implementation support
- Repository discovery and system understanding workflows
- Code review, bug investigation, and implementation planning prompts
- Legacy .NET dependency migration planning for high-risk package-management changes
- Security, performance, and SonarQube-oriented review guidance
- Documentation and product-management assistant roles
- Reusable templates for architecture, AI, security, and performance artifacts
- Future MCP integration points for richer repository and tool context

## Repository Layout

```text
.continue/
  config.yaml
  agents/
  prompts/
  rules/
  templates/

docs/
examples/
scripts/
AI.md
ARCHITECTURE.md
CHANGELOG.md
CONTRIBUTING.md
DECISIONS.md
PROJECT.md
README.md
ROADMAP.md
STYLEGUIDE.md
TODO.md
```

### `.continue/config.yaml`

The Continue entry point. It defines local Ollama models, repository context providers, local rule files, local prompt files, and an empty MCP server list for future integrations.

### `.continue/agents`

Role-specific assistant definitions, including senior engineer, architect, security engineer, performance engineer, reviewer, documentation specialist, and product manager.

### `.continue/prompts`

Task-oriented workflows for repository discovery, implementation planning, legacy .NET dependency migration, code review, bug investigation, architecture review, security review, performance review, and documentation.

### `.continue/rules`

Reusable engineering standards for general development, Git, .NET, ASP.NET Core, APIs, Clean Architecture, testing, logging, security, performance, and SonarQube.

### `.continue/templates`

Output templates for durable engineering artifacts such as architecture notes, AI guidance, security reviews, performance reviews, and legacy .NET dependency migration plans.

### `examples`

Representative outputs for major workflows. These examples show expected structure, tone, and level of detail for repository discovery, implementation planning, code review, architecture review, security review, performance review, and release readiness.

### `docs`

Workflow documentation for enterprise review practices, including MCP research, setup guidance, workflow examples, SonarQube integration options, compatibility notes, the manual SonarQube review workflow, validation checklists, and troubleshooting guidance.

Use this folder for deeper instructions after the quick start. Important guides include local model selection, local Agent model testing, model tool-use validation, local model reliability, tool-use modes, scoped edits, validation, runtime validation, MCP setup, MCP examples, and troubleshooting.

### `scripts`

Repository validation automation for release checks and portable configuration invariants.

## Current Status

The repository contains an initial usable pack structure:

- `.continue/config.yaml` targets Continue `schema: v1`.
- Local-first Ollama model defaults are defined.
- Core rules, prompts, agents, and templates are implemented.
- Configured local rule and prompt file references have been statically checked.
- Continue CLI can load the pack configuration.
- Model-backed execution has been validated with a test-time Ollama endpoint override.
- MCP and SonarQube support are documented as optional integration paths, not default wired integrations.

Version `0.1.12` includes runtime validation tooling, prompt quality hardening, beginner setup guidance, tool-enabled workflow guidance, hardware-aware local model selection support, catalog-based model recommendations, local configuration safety guidance, ARM and Apple Silicon guidance, Linux/macOS runtime wrappers, cross-platform smoke tests, practical MCP examples, and improved README onboarding.

## Standard Usage

The standard workflow is:

1. Install or copy this pack into a repository that uses Continue.
2. Ensure Ollama is running with the configured models available.
3. Point Continue at `.continue/config.yaml`.
4. Use the included prompts for discovery, planning, review, security, architecture, performance, and documentation workflows.
5. Keep project-specific decisions in the top-level documentation files.

Starter local model assumptions:

- Chat/edit/apply/tool workflows: `qwen3.5:9b` as the current WRITE SAFE starter candidate
- Embeddings: `nomic-embed-text`
- Ollama endpoint: default local Ollama endpoint

For larger machines, higher-risk workflows, or Agent tool use, run the hardware profile helper and use `docs/local-model-selection.md` before changing models.

For Agent tools or approved write mode, also run the local model preflight in
`docs/local-agent-model-testing.md` and the read-only checklist in
`docs/model-tool-use-validation.md`. A hardware recommendation is only a
candidate until tool execution is validated in the editor or CLI surface you
plan to use.

For mixed-model workflows, use model profiles instead of giving every model
`edit` and `apply` roles. The simple-hardware default points all three Agent
profiles at `qwen3.5:9b`; only the `1 - WRITE SAFE` lane should have `chat`,
`edit`, and `apply`. Planning and review lanes should stay `chat` only, even if
you later upgrade them to heavier models.

For private endpoints, local model experiments, or machine-specific settings, use `docs/local-config-safety.md` before editing committed config files.

To collect a sanitized hardware profile for local model selection:

Windows PowerShell:

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

For detailed setup, script usage, model selection, troubleshooting, validation, and tool-use safety instructions, start in the `docs/` folder.

Example Ollama setup:

Windows PowerShell:

```powershell
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

Linux or macOS:

```bash
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

Optional Continue CLI usage with `npx`:

Windows PowerShell:

```powershell
npx @continuedev/cli --config .continue/config.yaml
```

Linux or macOS:

```bash
npx @continuedev/cli --config .continue/config.yaml
```

If the Continue CLI is installed globally, `cn` may also be available:

Windows PowerShell:

```powershell
cn --config .continue/config.yaml
```

Linux or macOS:

```bash
cn --config .continue/config.yaml
```

If PowerShell reports that `cn` is not recognized, use the `npx` command above or install the CLI globally:

Windows PowerShell:

```powershell
npm install -g @continuedev/cli
```

Linux or macOS:

```bash
npm install -g @continuedev/cli
```

Runtime status:

- Continue CLI config loading was validated with `npx @continuedev/cli`.
- Continue initialized the config, model, MCP, system-message, and file-index services.
- Model-backed execution was validated using a local-network Ollama endpoint as a test-time override.
- A prompt-file smoke test completed successfully.
- Representative workflow examples are available in `examples/`.

## Examples

- `examples/repository-discovery.md`
- `examples/implementation-plan.md`
- `examples/code-review.md`
- `examples/architecture-review.md`
- `examples/security-review.md`
- `examples/performance-review.md`
- `examples/release-readiness.md`
- `examples/sonarqube-review.md`
- `examples/editor-surface-validation.md`
- `examples/model-tool-use-validation.md`
- `examples/multi-repository-validation.md`
- `examples/fixtures/repository-context.md`
- `examples/fixtures/security-review-input.md`
- `examples/fixtures/performance-review-input.md`
- `examples/fixtures/release-readiness-input.md`
- `examples/fixtures/sonarqube-findings.md`

## Workflow Docs

- `docs/sonarqube-review.md`
- `docs/sonarqube-integration-options.md`
- `docs/mcp-options.md`
- `docs/mcp-setup.md`
- `docs/mcp-examples.md`
- `docs/compatibility.md`
- `docs/validation-checklists.md`
- `docs/troubleshooting.md`
- `docs/tool-use-modes.md`
- `docs/approved-tool-backed-changes.md`
- `docs/scoped-edits.md`
- `docs/local-config-safety.md`
- `docs/local-model-selection.md`
- `docs/online-model-discovery.md`
- `docs/multi-repository-validation.md`
- `docs/runtime-output-verification.md`
- `docs/model-tool-use-validation.md`
- `docs/local-model-reliability.md`
- `docs/banned-output-patterns.md`
- `docs/release.md`
- `docs/runtime-validation.md`
- `docs/prompt-quality.md`

## Validation

Run the local validation script before release-oriented changes:

```powershell
.\scripts\validate-pack.ps1
```

Run the automated pack tests:

```powershell
.\scripts\test-pack.ps1
```

On Linux:

```bash
./scripts/validate-pack.linux.sh
./scripts/test-pack.linux.sh
```

On macOS:

```bash
./scripts/validate-pack.macos.sh
./scripts/test-pack.macos.sh
```

The Linux and macOS scripts are native Bash scripts. They do not require PowerShell.

The script checks the configured version, required files, local `.continue` file references, default MCP posture, and obvious committed private endpoints or secrets.

For runtime validation against a target repository, run the command for your operating system.

Windows:

```powershell
$Pack = "C:\path\to\local-engineering-agent-pack"
& "$Pack\scripts\run-runtime-validation.ps1" -TargetRepo (Get-Location).Path
```

Linux:

```bash
PACK="/path/to/local-engineering-agent-pack"
"$PACK/scripts/run-runtime-validation.linux.sh" --target-repo "$PWD"
```

macOS:

```bash
PACK="/path/to/local-engineering-agent-pack"
"$PACK/scripts/run-runtime-validation.macos.sh" --target-repo "$PWD"
```

Raw runtime outputs are written to an ignored local folder and should be reviewed before any sanitized summary is committed.

To generate a context file without relying on Continue tool execution, run the command for your operating system.

Windows:

```powershell
$Pack = "C:\path\to\local-engineering-agent-pack"
& "$Pack\scripts\generate-runtime-context.ps1" -TargetRepo (Get-Location).Path -OutputPath .\runtime-context.md
```

Linux:

```bash
PACK="/path/to/local-engineering-agent-pack"
"$PACK/scripts/generate-runtime-context.linux.sh" --target-repo "$PWD" --output-path ./runtime-context.md
```

macOS:

```bash
PACK="/path/to/local-engineering-agent-pack"
"$PACK/scripts/generate-runtime-context.macos.sh" --target-repo "$PWD" --output-path ./runtime-context.md
```

## Design Principles

- Prefer local-first operation for private enterprise codebases.
- Make prompts repeatable, reviewable, and version-controlled.
- Keep rules explicit enough to guide AI output without hiding engineering judgment.
- Optimize for .NET, ASP.NET Core, Clean Architecture, secure APIs, and maintainable services.
- Treat AI output as engineering assistance that still requires human review.

## Roadmap

See `ROADMAP.md`.

## License

MIT License. See `LICENSE`.
