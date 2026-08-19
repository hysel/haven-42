# Haven 42 Local LLM IDE Tools

This is the optional coding-tools package. You do not need it to use the
Haven 42 chat, writing, or summarization app.

It helps configure two tools to use an Ollama model you already run:

- **Aider** in a terminal
- **OpenCode** in a terminal or supported editor

Continue in VS Code and VSCodium is legacy and evidence-only. This package does
not copy `.continue/config.yaml`, write global Continue settings, advertise
Continue setup, or provide a future requalification path. Controlled testing
found inconsistent workspace configuration loading, unavailable edit tools,
and an unintended write during a multi-file request. Sanitized historical
records remain in the source repository so readers can understand that result.

The package does not install those tools, Ollama, models, Python, drivers, or
system services. The setup helper never downloads software. A configured tool
may manage its own dependencies when you later run it, so review that tool's
documentation. Every setup command shows a preview first and changes files
only when you add `--apply`.

## Availability

The earlier `0.1.0-development` package is retired because it included the
unreliable Continue project bundle. Do not use it for a new setup. The corrected
`0.1.1-development` package remains source-only until its package tests and
release review pass; no new public download is claimed here.

## Start

This section applies after a contributor builds the source package or after a
future reviewed `0.1.1-development` download is published. Verify its checksum,
extract the ZIP, and open a terminal in the extracted
`haven42-local-llm-ide-tools` folder.

Open PowerShell in this folder on Windows:

```powershell
.\setup.ps1 status
```

On Linux or macOS:

```bash
./setup.sh status
```

The status command explains what the package can configure and does not change
your project.

## Continue

There is no end-user Continue install command. Do not copy the repository's
`.continue` folder into a personal project and do not replace global Continue
settings based on this package. The repository's Continue material is retained
only as historical evidence and must not be presented as a supported setup or
testing path.

## Aider or OpenCode

The model must already exist in Ollama. Preview an Aider configuration:

```powershell
.\setup.ps1 configure aider --target C:\path\to\project --model qwen3.5:9b
```

For OpenCode, replace `aider` with `opencode`. Add `--apply` when the preview
is correct. Generated settings use local-only filenames; review your
`.gitignore` before committing other project changes.

To use Ollama on another computer, replace `PRIVATE-IP` below with that
computer's private network address:

```text
--ollama-url http://PRIVATE-IP:11434
```

Plain HTTP is not encrypted. Use it only on a network you trust. Public
addresses, credentials in URLs, queries, fragments, and arbitrary hostnames
are rejected.

## Safety

- Preview is the default.
- Existing settings are not replaced without `--replace`.
- Replaced settings are backed up first.
- Symbolic-link destinations are rejected.
- The package writes only inside the project folder you select.
- No prompts, code, addresses, or model names are sent to Haven 42.

## Build from source

Contributors can reproduce the development ZIP from a clean Haven 42 checkout:

```text
python packages/local-llm-ide/build.py
```

The builder writes the ZIP, checksum, and manifest under
`dist/local-llm-ide`.
