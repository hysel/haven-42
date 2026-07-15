# macOS Agent Host Bootstrap

Use this helper on a native macOS host when you need a local Ollama and
Continue CLI validation environment. It supports Apple Silicon and Intel Macs.

The script is intentionally opt-in: its default mode only reports available
tools. `--install` may install Homebrew and Node.js. `--with-ollama` may also
install Ollama through Homebrew. It never pulls a model or edits a project.

## Check The Host

```bash
./scripts/bootstrap-macos-agent-host.sh
```

## Install Required Tools

```bash
./scripts/bootstrap-macos-agent-host.sh --install --with-ollama
```

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
