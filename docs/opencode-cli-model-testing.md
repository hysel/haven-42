# OpenCode CLI Model Testing

## Status

OpenCode has a documented non-interactive CLI contract and a local Ollama
provider format. The pack supplies a local-only configuration generator and a
disposable test wrapper. Partial generated-sample evidence is recorded in
[OpenCode validation evidence](../examples/opencode-validation.md). Devstral
Small 2 24B has passed read-only, write-smoke, and constrained scoped-edit
validation on the generated sample. Keep the surface at candidate status until
explicitly approved non-generated repository validation passes.

## Plan And Install

Use the unified adapter to inspect the planned install without changing the
machine:

~~~powershell
.\scripts\setup-agent-surface.ps1 -Surface opencode -Action Plan
.\scripts\setup-agent-surface.ps1 -Surface opencode -Action Install -DryRun
~~~

The live install command is `npm install -g opencode-ai`. Remove `-DryRun`
only when you want to install the CLI.

## Generate A Local-Only Ollama Config

The adapter creates `.opencode.local.json` in the target repository and adds
that filename to the repository-local Git exclude list. It configures the
documented Ollama-compatible `/v1` provider endpoint and the model identifier
as `ollama/<model>`. Do not commit the generated file when it contains a
private endpoint.

~~~powershell
.\scripts\setup-agent-surface.ps1 `
  -Surface opencode `
  -Action Configure `
  -TargetRepo C:/path/to/project `
  -Model qwen3.5:9b `
  -OllamaBaseUrl http://your-local-ollama-host:11434
~~~

Launch OpenCode for that shell session with:

~~~powershell
$env:OPENCODE_CONFIG = '.opencode.local.json'
opencode
~~~

The native Linux/macOS adapter has the same behavior:

~~~bash
./scripts/setup-agent-surface.linux.sh \
  --surface opencode \
  --action Configure \
  --target-repo /path/to/project \
  --model qwen3.5:9b \
  --ollama-base-url http://your-local-ollama-host:11434

OPENCODE_CONFIG=.opencode.local.json opencode
~~~

## Disposable Validation

After OpenCode is installed and configured, use only the generated sample for
the first test:

~~~powershell
.\scripts\test-opencode-cli-models.ps1 `
  -Models qwen3.5:9b `
  -IncludeWriteSmoke `
  -UnloadAfterEach `
  -OllamaBaseUrl http://your-local-ollama-host:11434
~~~

The wrapper uses OpenCode's documented `opencode run --auto` command and
`ollama/<model>` selector. Automatic approval is limited to the generated
disposable sample by the harness. It verifies the write externally, restores the
generated fixture, and unloads the tested model. A passing generated-sample
run does not approve writes in a real project.

Use `-IncludeScopedEdit` with the generated Python sample to reproduce the
scoped-edit gate. The harness permits only `app/settings.py` and
`tests/test_main.py`, checks the expected validation marker in both files,
restores the fixture, and still does not approve real-project writes.

## Official References

- [OpenCode CLI](https://opencode.ai/docs/cli/)
- [OpenCode configuration](https://opencode.ai/docs/config/)
- [OpenCode providers and Ollama](https://opencode.ai/docs/providers/)
