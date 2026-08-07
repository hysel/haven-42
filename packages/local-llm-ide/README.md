# Haven 42 Local LLM IDE Tools

This is the optional coding-tools package. You do not need it to use the
Haven 42 chat, writing, or summarization app.

It helps configure three tools to use an Ollama model you already run:

- **Continue** in VS Code or VSCodium
- **Aider** in a terminal
- **OpenCode** in a terminal or supported editor

The package does not install those tools, Ollama, models, Python, drivers, or
system services. The setup helper never downloads software. A configured tool
may manage its own dependencies when you later run it, so review that tool's
documentation. Every setup command shows a preview first and changes files
only when you add `--apply`.

## Download

Download these three files from the
[Local LLM IDE Tools development prerelease](https://github.com/hysel/haven-42/releases/tag/local-llm-ide-tools-v0.1.0-development):

- [Tools ZIP](https://github.com/hysel/haven-42/releases/download/local-llm-ide-tools-v0.1.0-development/haven42-local-llm-ide-tools-0.1.0-development.zip)
- [SHA-256 checksum](https://github.com/hysel/haven-42/releases/download/local-llm-ide-tools-v0.1.0-development/haven42-local-llm-ide-tools-0.1.0-development.zip.sha256)
- [Package manifest](https://github.com/hysel/haven-42/releases/download/local-llm-ide-tools-v0.1.0-development/haven42-local-llm-ide-tools-0.1.0-development.manifest.json)

This is an unsigned development package, not a production release. The
expected ZIP SHA-256 is:

```text
da12ab46c26aaf9ea4f4105b927345bfe3d0900a416591ba29b3a33edaf16644
```

On Windows, put the ZIP and checksum file in the same folder and run:

```powershell
$expected = (Get-Content .\haven42-local-llm-ide-tools-0.1.0-development.zip.sha256).Split()[0]
$actual = (Get-FileHash -Algorithm SHA256 .\haven42-local-llm-ide-tools-0.1.0-development.zip).Hash
$actual -eq $expected
```

The final command must show `True`. On Linux, run:

```bash
sha256sum -c haven42-local-llm-ide-tools-0.1.0-development.zip.sha256
```

On macOS, run:

```bash
shasum -a 256 -c haven42-local-llm-ide-tools-0.1.0-development.zip.sha256
```

The command must report `OK`. If verification fails, delete the files and do
not run the setup helper.

## Start

After verification, extract the ZIP and open a terminal in the extracted
`haven42-local-llm-ide-tools` folder. You do not need to clone the Haven 42
repository.

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

Preview adding the Haven 42 prompts and rules to a project:

```powershell
.\setup.ps1 install-continue --target C:\path\to\project
```

Run the same command with `--apply` after checking the preview. If the project
already has Continue settings, the command stops. Add `--replace` only when
you want Haven 42 to create a `.continue.haven42-backup` and update the files.

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
