# Set Up Continue In VS Code And VSCodium

## Who This Is For

Use this guide when you want to use Continue with this pack in Visual Studio
Code or VSCodium. It is written for a first setup on one computer and one
project. The primary instructions cover Windows, followed by a native macOS
VSCodium install path.

The safest first workflow is:

1. Install the pack into the project you want the agent to work on.
2. Let the installer generate your user-level Continue config.
3. Open that project in VS Code.
4. Prove that the agent can read files before allowing it to edit them.

This guide does not require a public AI service. It works with Ollama on the
same computer or an Ollama server you control.

## Before You Start

You need:

- VS Code installed.
- The Continue extension installed in VS Code.
- Ollama running and at least one chat model installed, or the address of an
  Ollama server you control.
- A clone of this Local Engineering Agent Pack.
- The path to the project you want Continue to inspect or change.

Open PowerShell in the Local Engineering Agent Pack folder before running the
commands below. Replace the example project path with your own project path.

```powershell
Set-Location "C:\path\to\local-engineering-agent-pack"
```

## No Project To Test Yet?

Create a disposable sample project instead of testing agent writes in a real
repository. The sample generator does not require Ollama or an editor.

Windows PowerShell:

```powershell
.\scripts\generate-sample-repositories.ps1
```

macOS:

```bash
./scripts/generate-sample-repositories.macos.sh
```

Linux:

```bash
./scripts/generate-sample-repositories.linux.sh
```

The smallest starting sample is:

```text
runtime-validation-output/sample-repositories/python-api
```

Use that path as `TargetRepo` or `--target-repo` in the installer commands.
The samples are disposable validation fixtures, not production starter
templates. See `docs/sample-repository-factory.md` for every available sample.

## Windows: Install And Configure Continue

### 1. Install The Continue Extension

1. Open VS Code.
2. Select **Extensions** in the left activity bar.
3. Search for `Continue`.
4. Install the Continue extension.
5. Close and reopen VS Code after the installation completes.

Do not configure prompts, rules, or paths in the extension yet. The pack
installer creates the config that points at the assets installed for your
project.

### 2. Check Your Local Model Service

For Ollama running on the same Windows computer, run:

```powershell
ollama list
Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version"
```

If both commands return results, Ollama is ready. The model name shown by
`ollama list` must match the `model:` value in your generated Continue config.

If Ollama runs on another computer, use that server's URL in the installer
command in the next step. Keep private addresses and tokens out of committed
project files.

### 3. Preview The Installation

First run a dry run. It shows what the installer will copy and which Continue
config it will update without changing files.

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -GlobalConfig `
  -GlobalConfigApiBase "http://127.0.0.1:11434" `
  -DryRun
```

For an Ollama server on another machine, replace only the API base value, for
example `http://your-ollama-server:11434`.

Read the dry-run output. It should identify your target project and the global
Continue config path. Stop here if the target path is not the project you mean
to configure.

### 4. Install The Pack And Generate The Active Config

Run the same command again without `-DryRun`:

```powershell
.\scripts\install-continue-pack.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -GlobalConfig `
  -GlobalConfigApiBase "http://127.0.0.1:11434"
```

The installer does four important things:

1. Copies the pack assets into `your-project\.continue`.
2. Backs up an existing `.continue` folder before replacing it.
3. Backs up the existing user-level Continue config before replacing it.
4. Generates absolute `file://` references so VS Code can find the prompts,
   templates, and docs installed for your project.

On Windows, the generated user-level config is normally:

```text
C:\Users\your-user\.continue\config.yaml
```

Do not replace it by copying `.continue\config.local.yaml` from a project.
That local override can contain relative paths that are only valid inside that
project's `.continue` folder.

### 5. Keep Duplicate Rule Warnings Away

The generated global config deliberately omits `rules:`. Continue can load the
project's rules from `your-project\.continue\rules` without loading the same
rules twice.

Do not add a `rules:` section to `C:\Users\your-user\.continue\config.yaml`
unless you are deliberately using a global-only setup. Adding it is the common
cause of warnings such as `Duplicate rules named "Security" detected.`

If you already see duplicate-rule warnings:

1. Close VS Code.
2. Re-run the installer command in step 4 without
   `-GlobalConfigIncludeRules`.
3. Reopen VS Code and open your target project.

See `docs/troubleshooting.md` for the safe checks if the warning remains.

### 6. Open The Correct Project In VS Code

1. In VS Code, select **File > Open Folder**.
2. Select `C:\path\to\your-project`, not the Local Engineering Agent Pack
   folder.
3. Confirm the Explorer shows the real files of the project you want to work
   on.
4. Open Continue with `Ctrl+L`.
5. Use the config selector and gear beside **Local Config** to confirm that
   Continue is using your user-level config.

The config selector is more reliable than assuming a command named "Open
Config" exists in every Continue version. If the model or prompts do not
appear after installation, run **Developer: Reload Window** from the VS Code
Command Palette, then reopen Continue.

At this point, Continue should show an Ollama chat model and the prompt list
should include workflows such as `repository-discovery` and
`implementation-plan`.

### 7. Run A Safe Read Test

Use Continue Agent mode. Paste this prompt exactly:

```text
Use tools to inspect the repository root.

Do not modify files.
Do not guess.

If tools are unavailable, say: TOOLS_UNAVAILABLE.

Return only the actual top-level file and folder names you inspected.
```

Pass criteria:

- The response names real files from the project open in VS Code.
- Continue shows a read or list tool action.
- The final response is not raw tool-call JSON or markup.
- No files change.

If the assistant prints text such as `<function=ls>` or a JSON object instead
of running a tool, do not click Apply. That model is not tool-validated in
your editor setup. Follow `docs/model-tool-use-validation.md` before trying
approved writes.

### 8. Run A Controlled Write Test

Only do this after the read test passes. Use a disposable test project or a
temporary branch. First record the current repository state:

```powershell
Set-Location "C:\path\to\your-project"
git status --short --branch
```

If you have unrelated changes, commit or stash them before this test. Then use
Continue Agent mode and paste:

```text
Use approved write mode for this smoke test only.

Create a file named continue-agent-write-test.md in the opened repository root with exactly this content:

Continue Agent write test passed.

Do not modify any other files.
Do not create the file under src, docs, Properties, or any other subfolder.
After editing, report the changed file and stop.
Do not commit.
```

Approve the file creation once only after checking that the target shown by
Continue is `continue-agent-write-test.md` in the repository root. Then verify
outside Continue:

```powershell
git status --short
Test-Path .\continue-agent-write-test.md
Get-Content .\continue-agent-write-test.md
git diff --check
```

The test passes only when the file exists on disk, contains exactly the one
expected line, and `git diff --check` reports no whitespace errors. A model
claiming it edited a file is not proof by itself.

Clean up the disposable test file when finished:

```powershell
Remove-Item .\continue-agent-write-test.md
```

### 9. Use The Pack Safely

For normal work, begin in read-only or plan-only mode. When you are ready to
make a real scoped change, use the workflow in `docs/tool-use-modes.md` and
verify the result with `git diff` before committing.

## Multiple Projects On One Computer

The basic global-config command in this guide points Continue at the assets
installed for one target project. Re-run the installer when you switch the
active project, or use `docs/shared-asset-installation.md` for the advanced
centralized shared-assets setup.

Do not hand-edit the generated absolute `file://` prompt, template, and doc
paths merely to switch projects. Regenerating the config preserves backups and
checks the references.

## macOS: Install And Configure Continue In VSCodium

Use this native macOS path when Continue and VSCodium are installed on a Mac.
The scripts use Bash and do not require PowerShell.

### 1. Get The Pack On The Mac

In Terminal, clone the pack once into a stable location:

```bash
git clone https://github.com/hysel/local-engineering-agent-pack.git
cd local-engineering-agent-pack
```

If Git is not available, install the macOS Command Line Tools first:

```bash
xcode-select --install
```

### 2. Bootstrap A New Mac

Treat a newly created Mac as an empty host. Install the pack-managed MLX
runtime before profiling or configuring Continue:

```bash
cd ~/local-engineering-agent-pack
./scripts/bootstrap-macos-agent-host.sh --install --with-mlx
```

This installs only the local MLX prerequisites. It does not install Ollama or
download a model. If you already ran this command on the current machine, the
helper reports the available tools instead of requiring a different setup path.
Every replacement or newly provisioned Mac starts at step 1 again; do not reuse
paths, models, or configuration assumptions from an earlier instance.

### 3. Choose The Mac Model Host

Run the Mac hardware profile before generating the Continue config:

```bash
./scripts/get-local-model-profile.macos.sh
```

If it reports installed Ollama models, use the normal Ollama instructions in
the Windows section with the macOS installer. If it reports **MLX tooling:
detected** but no Ollama models, use the MLX route below. Do not configure an
MLX model as an Ollama model.

Start the recommended MLX server in a separate Terminal window. Use the exact
model named by the profile's `MLX recommendation`; the first start downloads
it, so leave this window running. For example, a 16 GB Apple Silicon host is
normally assigned `mlx-community/Qwen3.5-4B-4bit`:

```bash
MODEL='mlx-community/Qwen3.5-4B-4bit'
"$HOME/.local-engineering-agent-pack-mlx/bin/mlx_lm.server" \
  --model "$MODEL" --host 127.0.0.1 --port 8080
```

In a second Terminal window, confirm the loopback-only endpoint responds:

```bash
curl --fail --silent http://127.0.0.1:8080/v1/models
```

### 4. Preview The macOS Install

If you generated the sample above, set the target variable first:

```bash
TARGET_REPO="$PWD/runtime-validation-output/sample-repositories/python-api"
```

Otherwise, set `TARGET_REPO` to the project you will open in VSCodium:

```bash
TARGET_REPO="$HOME/path/to/your-project"
```

Then preview the install:

```bash
./scripts/install-continue-pack.macos.sh \
  --target-repo "$TARGET_REPO" \
  --global-config \
  --mlx-config \
  --mlx-api-base "http://127.0.0.1:8080/v1" \
  --dry-run
```

Check that the reported target project is correct. The installer should also
report the global Continue config it would update.

### 5. Install And Generate The macOS Config

Run the same command without `--dry-run`:

```bash
./scripts/install-continue-pack.macos.sh \
  --target-repo "$TARGET_REPO" \
  --global-config \
  --mlx-config \
  --mlx-api-base "http://127.0.0.1:8080/v1"
```

This creates or updates the project `.continue` folder and a local-only
OpenAI-compatible MLX model config. The generated global Continue config uses
that model config and is normally written to:

```text
~/.continue/config.yaml
```

It backs up existing configuration before replacement and omits global rules by
default to prevent duplicate-rule warnings.

### 6. Prepare A Disposable Editor Test

The commands below automate the safe setup work: they create the sample,
install the Continue configuration, prepare Python tests, and establish a Git
baseline. They do not start an MLX server or operate the VSCodium approval UI.

For a constrained Apple Silicon host, use the MLX model named by the profile.
On a 16 GB host, the pack selects
`mlx-community/Qwen3.5-4B-4bit`.

```bash
cd ~/local-engineering-agent-pack

./scripts/generate-sample-repositories.macos.sh --force

TARGET_REPO="$PWD/runtime-validation-output/sample-repositories/python-api"

./scripts/install-continue-pack.macos.sh \
  --target-repo "$TARGET_REPO" \
  --global-config \
  --mlx-config \
  --mlx-api-base "http://127.0.0.1:8080/v1"

cd "$TARGET_REPO"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip pytest
python -m pytest

printf 'before\n' > continue-agent-write-test.md
git init -q
git add .
git -c user.name="Validation User" \
  -c user.email="validation@example.invalid" \
  commit -qm "Initial editor validation fixture"
```

The generated fixture ignores the virtual environment and Python caches. The
baseline commit makes the post-edit check deterministic. Run this only in the
generated sample: `--force` replaces all generated samples in the output
folder.

### 7. Open And Test In VSCodium

1. Fully quit and reopen VSCodium.
2. Select **File > Open Folder** and open the target project, not the pack.
3. Open Continue and use its config selector/gear beside **Local Config** to
   confirm `~/.continue/config.yaml` is active.
4. Run the read-only test in the Windows section above.
5. Run this existing-file write test only after the read-only test passes:

```text
Use approved write mode for this smoke test only.

Edit the existing file continue-agent-write-test.md in the opened repository root.
Replace its entire content with exactly:

Continue Agent write test passed.

Do not modify any other files.
Do not create a new file.
Do not append.
Use one edit tool call.
Stop after the first Apply diff.
Do not commit.
```

   Approve only the one edit and save the file if VSCodium shows it as unsaved.
   Then run these macOS terminal checks afterward:

```bash
git status --short
git diff -- continue-agent-write-test.md
git diff --check
cat ./continue-agent-write-test.md
```

6. For a real scoped code change, run the relevant command directly after
   inspecting the diff. For the generated Python sample:

```bash
python -m app.main
python -m pytest
git diff --check
```

When finished, leave the environment with `deactivate`. Remove the disposable
fixture or environment only when you no longer need it.

For native Apple Silicon and MLX model-host setup, see
`docs/macos-agent-host-bootstrap.md`.

## Need More Help?

- `docs/editor-compatibility.md`: VS Code, VSCodium, duplicate-rule, and CLI
  fallback details.
- `docs/troubleshooting.md`: config paths, missing references, and tool-call
  failures.
- `docs/local-model-selection.md`: choose a model for your hardware.
- `docs/model-tool-use-validation.md`: determine whether a model can safely
  use tools before approved writes.

For Linux, use the equivalent native installer listed in the README and the
platform-specific setup sections in `docs/editor-compatibility.md`.
