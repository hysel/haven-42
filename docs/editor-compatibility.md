# Editor Compatibility

> **Legacy Continue evidence:** Continue is no longer an active Haven 42
> integration. Continue-specific instructions below are retained only to make
> historical results understandable; they are not a supported setup or future
> qualification path. New editor work must use a separately admitted surface.

> **Experimental contributor workflow:** Haven 42 does not currently ship or
> automatically install project-level Continue configuration for end users.
> VS Code and VSCodium testing found inconsistent workspace-config loading,
> unavailable edit tools, and an unintended out-of-scope write. The commands
> below are retained for isolated evidence collection only; they are not a
> novice setup path or an approved-write recommendation.

## Purpose

This page preserves the historical VS Code, VSCodium, and Continue CLI test
procedure so its sanitized results remain understandable. It is not a current
installation, configuration, repair, or qualification guide. For maintained
coding options, see `docs/agent-surface-solutions.md`.

The committed `.continue/config.yaml` is an internal validation fixture. It is
not shipped into end-user projects. Editor-specific paths, private endpoints,
and local model experiments stay in ignored test configuration.

## Historically Tested Surfaces

| Surface | What to expect | What to verify |
| --- | --- | --- |
| VS Code | Historical experimental contributor surface. | Earlier tests recorded whether Continue loaded the isolated config, used the exact selected model, and kept every approved edit in scope. |
| VSCodium | Historical experimental contributor surface; extension versions and command names differed. | Earlier tests recorded config loading, exact model identity, tool availability, and external diff results independently from VS Code. |
| Continue CLI | Historical fallback used to isolate editor behavior. | `npx -y @continuedev/cli@1.5.47 --config .continue/config.yaml` identifies the exact tested CLI. |

## Historical Isolated Test Config

The disposable contributor tests used this fixture layout:

```text
target-repository/
  .continue/
    config.yaml
```

The historical procedure avoided pointing Continue at the original pack repository after copying the fixture into a disposable target.

Keep local machine settings in ignored files such as:

```text
.continue/config.local.yaml
```

Do not commit:

- private Ollama endpoints
- local filesystem paths
- private model names
- tokens or API keys
- editor-specific absolute config paths

## Historical Setup Checks

The recorded preflight checked:

1. Open the target repository in the editor.
2. Confirm the editor file explorer shows the target repository files.
3. Confirm the target repository has `.continue/config.yaml`.
4. Confirm Continue shows the expected local model.
5. Confirm prompts such as `repository-discovery`, `implementation-plan`, and `code-review` are visible.
6. Confirm duplicate-rule warnings are not present.

If the model or prompts are missing, Continue may be using a global/default config instead of the project-local config.

## Historical Global Config Input

Some tested editor setups loaded the global Continue config instead of the
project-local `.continue/config.yaml`. The historical harness used the commands
below to create an isolated test input with absolute references. Do not use
them as current setup guidance.

Windows PowerShell:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -GlobalConfig
```

Linux:

```bash
./scripts/install-continue-pack.linux.sh --target-repo /path/to/your-project --global-config
```

macOS:

```bash
./scripts/install-continue-pack.macos.sh --target-repo /path/to/your-project --global-config
```

Generated global config omits `rules:` by default. This is intentional. It keeps
the global config from loading the same rules that the opened repository may
also load from `.continue/rules`.

The installer backs up the existing global config before replacing it. For
machine-specific endpoints, pass an API base only during global config
generation rather than committing it to the target repository:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -GlobalConfig `
  -GlobalConfigApiBase "http://127.0.0.1:11434"
```

Use the local endpoint value that applies to your machine. Do not commit private
IP addresses, internal hostnames, or tokens into shared config files.

Use `-GlobalConfigIncludeRules` only for a global-only setup where the editor
will not also load project-local `.continue/rules`.

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -GlobalConfig `
  -GlobalConfigIncludeRules
```

On Windows, the PowerShell installer writes absolute Continue file references in
the `file://C:/path/...` form because some VSCodium setups do not resolve
`file:///C:/path/...` correctly.

## Historical Terminal Preflight Checks

These commands do not prove that the editor UI loaded the project-local config. They only confirm that the editor command and Continue extension are visible from the current shell.

VS Code-compatible builds:

```powershell
code --version
code --list-extensions --show-versions | Select-String -Pattern "continue" -CaseSensitive:$false
```

VSCodium:

```powershell
codium --version
codium --list-extensions --show-versions | Select-String -Pattern "continue" -CaseSensitive:$false
```

Linux or macOS:

```bash
code --version
code --list-extensions --show-versions | grep -i continue
codium --version
codium --list-extensions --show-versions | grep -i continue
```

If `code` or `codium` is not on `PATH`, use the editor UI to confirm the installed Continue extension version instead.

Record sanitized terminal preflight results in `examples/editor-surface-validation.md` only when they change shared guidance.

## Historical Duplicate Rule Findings

Duplicate rule warnings usually mean the same rule files are loaded from two places:

- global Continue config
- project-local `.continue/config.yaml`

Common warning examples:

```text
Duplicate rules named "API Design" detected.
Duplicate rules named "Clean Architecture" detected.
Duplicate rules named "Security" detected.
```

The recorded recovery procedure was:

1. Choose one active source of rules.
2. Prefer the project-local `.continue/config.yaml` for repositories using this pack.
3. Regenerate the global Continue config without `-GlobalConfigIncludeRules`.
4. Remove any stale `rules:` block from the global Continue config if it was created by an older installer.
5. Reload the editor window.
6. Reopen Continue and confirm the warnings are gone.

## Historical Read-Only Editor Test

### Project-language prerequisites

Editor language extensions improve diagnostics, navigation, and test discovery,
but they are not evidence that Continue can read or edit repository files. For
example, the Microsoft Python extension is recommended for a Python project;
basic Continue file-tool validation must still work without it.

Future setup should detect the opened project's language tooling, distinguish
required tools from recommendations, explain the reason for each suggestion,
and ask before installation. Record the exact accepted extension version in
surface evidence. If the user declines, retain a manual test command and do not
misclassify missing optional tooling as a model failure.

Use this first test in VS Code or VSCodium:

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

Expected result:

- The response references real files from the opened repository.
- The response does not say it lacks filesystem access.
- The response does not print raw JSON tool calls as the final answer.
- No files are modified.

## Historical Agent Tool Test

This cell was run only after the read-only editor test worked.

Use Agent mode and ask:

```text
List the top-level files in this repository.
Do not modify files.
Summarize what each important file is for.
```

Expected result:

- Continue executes a read/list tool or otherwise inspects the opened repository.
- The final answer summarizes actual files.
- The final answer does not only print tool-call JSON such as `{"name":"ls","arguments":...}`.
- The final answer does not only print tool-call markup such as `<function=ls> <parameter=dirPath> . </tool_call>`.

If Agent mode prints raw JSON or tool-call markup instead of executing tools, treat that model/editor setup as not tool-validated. Use runtime context fallback from `docs/runtime-validation.md` or switch to a model already validated for tool use.

Use `docs/model-tool-use-validation.md` for the full validation checklist and `examples/model-tool-use-validation.md` for sanitized evidence.

## Historical CLI Fallback

The test campaign used this CLI fallback when the editor did not clearly show
which config was active:

Windows PowerShell:

```powershell
npx -y @continuedev/cli@1.5.47 --config .continue/config.yaml --readonly -p "Reply OK"
```

Linux or macOS:

```bash
npx -y @continuedev/cli@1.5.47 --config .continue/config.yaml --readonly -p "Reply OK"
```

If the CLI loads the config but the editor does not, the issue is likely editor config selection, extension version, or global config precedence.

## Historical Test Record

When testing an editor surface, record:

- editor name: VS Code or VSCodium
- editor version
- Continue extension version
- operating system
- model name
- provider: Ollama, OpenAI-compatible local endpoint, or other
- whether `.continue/config.yaml` loaded
- whether duplicate-rule warnings appeared
- whether read-only repository discovery worked
- whether Agent mode executed tools
- whether any fallback was needed

Keep private endpoints, usernames, local paths, private repository names, and raw transcripts out of committed notes.

See `examples/editor-surface-validation.md` for the current sanitized editor-surface evidence record.
