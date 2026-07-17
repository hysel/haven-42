# macOS Agent Host Bootstrap

Use this helper on a native macOS host when you need a local Ollama, MLX, and
Continue CLI validation environment. It supports Apple Silicon and Intel Macs.

The script is intentionally opt-in: its default mode only reports available
tools. `--install` may install Homebrew and Node.js. `--with-ollama` may also
install Ollama through Homebrew. `--with-mlx` installs a dedicated Homebrew
Python 3.12 virtual environment with `mlx-lm`. It never pulls a model or edits
a project.

## Check The Host

```bash
./scripts/bootstrap-macos-agent-host.sh
```

## Install Required Tools

```bash
./scripts/bootstrap-macos-agent-host.sh --install --with-ollama
```

For an Apple Silicon MLX runtime instead of, or alongside, Ollama:

```bash
./scripts/bootstrap-macos-agent-host.sh --install --with-mlx
```

The helper intentionally uses Homebrew Python 3.12. The macOS-provided Python
can be older and may resolve an `mlx-lm` version that does not support current
model architectures such as Qwen 3.5.

After installation, start the Ollama service, pull a model suitable for the
available unified memory, and profile the host:

```bash
brew services start ollama
ollama pull qwen3.5:9b
./scripts/get-local-model-profile.macos.sh --json
```

On Apple Silicon Homebrew is normally installed under `/opt/homebrew`. For
non-interactive SSH commands, ensure that directory is on `PATH`:

```bash
export PATH=/opt/homebrew/bin:$PATH
```

The profile script reports detected MLX tooling separately. Ollama models use
Ollama's Metal backend; do not pull an MLX-specific model unless you are also
setting up and validating an MLX serving runtime.

## MLX Local Server And Continue CLI

MLX is an Apple Silicon serving path. Run it only on the loopback interface:

```bash
MODEL='mlx-community/Qwen3.5-9B-OptiQ-4bit'
"$HOME/.local-engineering-agent-pack-mlx/bin/mlx_lm.server" \
  --model "$MODEL" --host 127.0.0.1 --port 8080
```

`mlx_lm.server` is intended for local development and performs only basic
security checks. Do not expose this example port to a network. A Continue CLI
config for this endpoint uses the OpenAI provider, an `apiBase` ending in
`/v1`, and a local placeholder API key:

```yaml
models:
  - name: Local MLX validation
    provider: openai
    model: mlx-community/Qwen3.5-9B-OptiQ-4bit
    apiBase: http://127.0.0.1:8080/v1
    apiKey: local
    roles: [chat, edit, apply]
    capabilities: [tool_use]
```

The model above passed direct OpenAI-compatible tool-call validation plus
Continue CLI read tooling and a disposable single-file write smoke test on an
Apple Silicon host. This does not promote it to editor Agent or multi-language
matrix support; repeat validation for every surface and workflow you intend to
use.

## Generate Continue Config For The MLX Server

Do not put an MLX model name in an Ollama Continue config. After the MLX server
is running, use the macOS installer with `--mlx-config`. It reads the separate
MLX recommendation from the host profile, writes a local-only OpenAI-compatible
model block, and generates the global Continue config with the correct asset
references:

```bash
./scripts/install-continue-pack.macos.sh \
  --target-repo /path/to/your-project \
  --global-config \
  --mlx-config \
  --mlx-api-base http://127.0.0.1:8080/v1
```

Use `--dry-run` first. The installer intentionally does not pull or start an
MLX model; start the loopback-only server above before opening Continue.

## VSCodium And Continue Editor Validation

The editor test requires an interactive macOS desktop session. Install
VSCodium with Homebrew, then open it once from the desktop so macOS completes
its first-run checks:

```bash
brew install --cask vscodium
codium --version
```

Install Continue through VSCodium's Extensions view when it is available. If
the extension catalog does not offer Continue, download the current Continue
VSIX from the official Continue release path, then choose **Extensions**,
**...**, and **Install from VSIX...** in VSCodium. Open a disposable generated
sample repository, configure a loopback-only MLX endpoint in a local Continue
configuration, and restart VSCodium.

Run a read-only smoke prompt first: ask the agent to read `README.md` and
return its first heading. Then run a one-file write smoke prompt that appends a
unique marker to `README.md`. Approve exactly one edit, verify the changed file
and `git diff --check` in the terminal, then restore the disposable fixture.
Record the editor version, Continue version, model, provider, OS, and whether
the editor showed a single correctly targeted apply action. Do not treat CLI
evidence as editor Agent evidence.

## Continue CLI Smoke Test

Create a local config that targets the local Ollama service, then run a small
matrix slice on disposable fixtures:

```bash
./scripts/run-language-workflow-matrix.macos.sh \
  --ecosystems python \
  --operations repository-discovery,scoped-write \
  --read-config .continue/config.local.yaml \
  --write-config .continue/config.local.yaml \
  --unload-after-run
```

The runner rejects a preloaded Ollama server by default and verifies that it
unloads the tested model after the run. A passing read-only cell does not make
approved writes safe: retain the per-surface, per-model, per-OS evidence gate.
