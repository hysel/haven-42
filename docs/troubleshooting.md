# Troubleshooting

## Purpose

Use this guide when Haven 42 does not load, prompts do not appear, or local model execution fails.

## Quick Checks

Run these checks from the repository root:

```powershell
git status --short --branch
Test-Path .continue/config.yaml
npx -y @continuedev/cli@1.5.47 --help
```

If using Ollama locally:

```powershell
ollama list
Invoke-RestMethod -Uri http://127.0.0.1:11434/ -Method Get
```

If using Ollama on another host, replace the URL with your local override endpoint.

## Continue Config Does Not Load

Symptoms:

- Continue reports a config parsing error.
- Continue cannot find `.continue/config.yaml`.
- CLI output includes `ENOENT`.

Checks:

```powershell
Test-Path .continue/config.yaml
npx -y @continuedev/cli@1.5.47 --config .continue/config.yaml --readonly -p "Reply OK"
```

Fixes:

- Run the command from the repository root.
- Use an absolute config path if relative resolution is unclear.
- Check YAML indentation.
- Confirm `name`, `version`, and `schema` are present.

For editor-specific checks in VS Code or VSCodium, use `docs/editor-compatibility.md`.

## `cn` Is Not Recognized

Symptoms:

- PowerShell reports `cn: The term 'cn' is not recognized`.

Meaning:

The Continue CLI global command is not installed on `PATH`.

Checks:

```powershell
Get-Command cn -ErrorAction SilentlyContinue
npx -y @continuedev/cli@1.5.47 --version
```

Fixes:

- Use the CLI through `npx`:

```powershell
npx -y @continuedev/cli@1.5.47 --config .continue/config.yaml
```

- Or install the CLI globally:

```powershell
npm install -g @continuedev/cli@1.5.47
```

After global installation, close and reopen PowerShell before retrying `cn`.

## Local File References Do Not Resolve

Symptoms:

- Rules or prompts are missing.
- Continue loads the config but expected workflows are unavailable.

Checks:

```powershell
$base = Resolve-Path .continue
$refs = Select-String -Path .continue\config.yaml -Pattern 'uses: file://(.+)$' | ForEach-Object { $_.Matches[0].Groups[1].Value }
$missing = @()
foreach ($ref in $refs) {
  if ($ref.StartsWith('./')) {
    $path = Join-Path $base $ref.Substring(2)
  } else {
    $path = $ref
  }
  if (-not (Test-Path -LiteralPath $path)) {
    $missing += $path
  }
}
$missing
```

Fixes:

- Keep referenced prompt and rule files under `.continue`.
- Use lower-case kebab-case filenames for prompts.
- Keep `file://./...` references aligned with paths relative to `.continue/config.yaml`.

## Windows Absolute `file://` Paths Fail

Symptoms:

- Continue reports paths such as `C:\C:\path\to\project`.
- Continue reports duplicated path segments such as `prompts\prompts`.
- Continue reports `ENOENT` for files that exist.

Meaning:

Some Windows and VSCodium setups may resolve `file:///C:/...` incorrectly.

Fixes:

- Use this local-only Windows path style:

```yaml
uses: file://C:/Users/your-user/source/your-project/.continue/prompts/repository-discovery.md
```

- Avoid this style if it produces `C:\C:\...` paths:

```yaml
uses: file:///C:/Users/your-user/source/your-project/.continue/prompts/repository-discovery.md
```

- Keep these absolute paths out of committed shared config.

## Duplicate Rules

Symptoms:

- Continue reports duplicate rules with names such as `API Design`, `.NET Engineering`, `Security`, or `Testing`.

Common causes:

- The same rules are loaded from both the default user config and the workspace `.continue` folder.
- Backup or disabled config files still end in `.yaml`.
- The workspace has more than one active config file.

Fixes:

- Keep only one active config source for rules.
- Regenerate the global config with the current installer. By default, global config generation omits `rules:` so project-local `.continue/rules` does not load twice.
- If the default user config references workspace rules, remove or rename workspace config files so they do not end in `.yaml`.
- If Continue auto-loads `.continue/rules`, remove any stale explicit `rules:` block from the default user config.
- Rename local backup files to extensions such as `.bak` instead of `.yaml`.

Useful checks:

```powershell
Get-ChildItem "$env:USERPROFILE\.continue" -Force -File -Filter "*.yaml"
Get-ChildItem ".continue" -Force -File -Filter "*.yaml"
Select-String -Path "$env:USERPROFILE\.continue\config.yaml" -Pattern "^rules:|file://.*rules"
```

Expected default result after using `-GlobalConfig`: no `rules:` matches in the
global config. Use `-GlobalConfigIncludeRules` only for a global-only setup where
the editor will not also load project-local rules.

## Agent Mode Prints JSON Tool Calls

Symptoms:

- Agent mode prints output like:

```json
{"name":"ls","arguments":{"dirPath":".","recursive":true}}
```

- Or Agent mode prints tool-call markup like:

```text
<function=ls> <parameter=dirPath> . </tool_call>
```

- Clicking Apply returns `could not resolve filepath to apply changes`.

Meaning:

The model produced a tool-call-shaped message, but Continue did not execute it as a tool call. The JSON or markup is not a patch and should not be applied.

Fixes:

- Do not click Apply on raw JSON or markup tool-call text.
- Confirm the Continue surface is Agent mode.
- Try a stronger or more tool-compatible model.
- Use `@Files`, selected text, active-file context, or a generated runtime context file as a fallback.

Fallback:

Windows:

```powershell
$Pack = "C:\path\to\haven-42"
& "$Pack\scripts\generate-runtime-context.ps1" -TargetRepo (Get-Location).Path -OutputPath .\runtime-context.md
```

Linux:

```bash
PACK="/path/to/haven-42"
"$PACK/scripts/generate-runtime-context.linux.sh" --target-repo "$PWD" --output-path ./runtime-context.md
```

macOS:

```bash
PACK="/path/to/haven-42"
"$PACK/scripts/generate-runtime-context.macos.sh" --target-repo "$PWD" --output-path ./runtime-context.md
```

Then attach `runtime-context.md` with `@Files` and ask the model not to use tools or output JSON.

## Agent Says It Cannot Edit Files

Symptoms:

- The user approves implementation.
- The assistant responds with wording like:

```text
Since I can't directly edit files in this environment, here is the code you can add...
```

Expected behavior:

- In approved write mode, Continue should use edit/apply tools to modify the scoped files.
- If write tools are not available in the selected editor surface, the assistant should say `WRITE_TOOLS_UNAVAILABLE` and stop.

What to check:

1. Confirm you are in Agent mode, not plain chat.
2. Confirm the active model has `chat`, `edit`, and `apply` roles in the active Continue config.
3. Confirm the active config is the global config or the project config you intended, not an older stale config.
4. Run the approved-write smoke test from `docs/tool-use-modes.md`.
5. If the smoke test fails, keep the model at read-only or plan-only status for that editor surface.

Do not treat pasted code as an implemented change. The assistant must either edit the files through Continue or clearly report that write tools are unavailable.

## Agent Lists Files But Cannot Read Or Edit Them

Symptoms:

- The assistant can list directories or top-level files.
- It fails or stalls when reading source/config files.
- It then says it will make an "informed" or "typical" change based on the project type.
- It proposes code or configuration without citing observed file content.

Expected behavior:

- The assistant must read the exact files it plans to change before editing.
- If it cannot read those files, it should say `READ_TOOLS_UNAVAILABLE` and stop.
- Listing files alone is not enough for approved write mode.

What to check:

1. Confirm the opened editor workspace is the target repository root.
2. Confirm the active Continue config is the regenerated global config or the intended project-local config.
3. Confirm the model has `chat`, `edit`, and `apply` roles.
4. Run a read-content test on a harmless file:

```text
Use tools to read README.md.
Do not modify files.
Return the first heading only.
If you cannot read the file, say READ_TOOLS_UNAVAILABLE.
```

5. If the read-content test fails, do not run approved write mode yet.

Do not accept implementation based on "typical .NET project" or similar
language. The model must base code/config edits on file evidence.

If the assistant reports both `README read: no` and
`Failure signal: READ_TOOLS_UNAVAILABLE`, the status is not read-only tool
validated. Record it as read-only listing only or failed read-content
validation.

## Agent Claims A Change But Git Diff Is Empty

Symptoms:

- The assistant says it changed a file.
- The assistant says it created and read back a file.
- The assistant prints `edit_file` or another edit-shaped tool call.
- `git status --short` does not show that file as modified or untracked.
- `git diff -- <file>` is empty.
- Reading the file does not show the requested content.
- `Test-Path` or `Get-ChildItem -Recurse` cannot find the file the assistant
  claims it created.

Expected behavior:

- After approved write mode, the assistant should verify changed content or a
  non-empty diff before claiming success.
- Approved-write readiness must be confirmed by an external shell or git check
  after the assistant reports success. Assistant-only readback is not enough.
- If no changed content or diff exists, it should say `WRITE_NOT_APPLIED`.
- Printed edit-call text is not proof that a file changed.

What to check:

1. Confirm you accepted any Continue edit/apply prompt in the editor UI.
2. Run:

```powershell
git status --short
Test-Path .\continue-agent-write-test.md
Get-ChildItem -Path . -Recurse -Filter continue-agent-write-test.md -Force | Select-Object FullName
git diff --check
git diff -- README.md
```

3. If the target file has no diff, or a requested new file cannot be found from
   the shell, treat the implementation attempt as failed.
4. Rerun with a narrower prompt that explicitly requires diff verification.

Do not commit or continue with follow-up code changes until the diff proves the
requested change was actually applied.

## Duplicate Approval Prompts Or Duplicate Content

Symptoms:

- Continue shows both a create-file prompt and an edit-file prompt for the same
  smoke-test target.
- Clicking both approvals appends or duplicates the requested line.
- The final file contains `Continue Agent write test passed.` more than once.

Expected behavior:

- Existing-file write validation should use one edit path.
- `create_new_file` should be Excluded during existing-file validation.
- `edit_existing_file` or `single_find_and_replace` can remain Ask First.
- The target file should be pre-created with harmless content before the test.

What to check:

1. In Continue built-in tools, temporarily set `create_new_file` to Excluded.
2. Pre-create the smoke-test file:

```powershell
Set-Content .\continue-agent-write-test.md "before"
```

3. Ask the assistant to replace the existing file content, not create a file.
4. Approve only one Apply diff for `continue-agent-write-test.md`.
5. Verify the content from a normal terminal:

```powershell
Get-Content .\continue-agent-write-test.md
```

If two approval paths appear, stop and record `DUPLICATE_APPROVALS`. If the
content is duplicated, record `DUPLICATE_CONTENT`. Do not mark the model
approved-write ready until a single-approval existing-file edit passes.

## Agent Creates A File In The Wrong Folder

Symptoms:

- The user asks to edit an existing file such as `README.md`.
- The assistant creates a new file such as `src/README.md` or `docs/README.md`.
- The root file is unchanged, or `git diff -- README.md` is empty.

Expected behavior:

- Unqualified file names should resolve from the opened repository root or
  current folder first.
- The assistant should inspect the current folder before creating a new file.
- If the correct target cannot be proven, the assistant should say
  `PATH_AMBIGUOUS` and stop before editing.

What to check:

```powershell
git status --short --untracked-files=all
git diff -- README.md
Get-ChildItem -Force
```

If a wrong-path file was created during a test and it is safe to remove, delete
only that test artifact:

```powershell
Remove-Item .\src\README.md
```

If the `src` folder is now empty and was created only by the failed test, remove
it too:

```powershell
if (-not (Get-ChildItem .\src -Force -ErrorAction SilentlyContinue)) {
  Remove-Item .\src -Recurse
}
```

Rerun the test with a prompt that requires current-folder path resolution and
diff verification before claiming success.

## Agent Says No File Is Open And Asks For A Path

Symptoms:

- The assistant says the current working directory is not explicitly set.
- The assistant says no files are open.
- The assistant asks the user to specify the path to `README.md` before trying
  repository tools.

Expected behavior:

- The assistant should use list/read tools against `.` to discover the opened
  workspace before asking for a path.
- If discovery fails because Continue cannot see the workspace, the assistant
  should say `WORKSPACE_UNAVAILABLE`.
- If discovery succeeds but more than one target is plausible, the assistant
  should say `PATH_AMBIGUOUS`.

What to check:

1. Confirm the editor opened the repository folder, not only an individual file.
2. Confirm Agent mode is active.
3. Ask for a read-only workspace discovery test:

```text
Use tools to list the files in the opened repository folder.
Do not modify files.
If you cannot discover the workspace with tools, say WORKSPACE_UNAVAILABLE.
Return only the top-level names you inspected.
```

If that test fails, fix the editor workspace or Continue config before approved
write mode.

## Apply Target Does Not Match The Requested File

Symptoms:

- The assistant reads one file, such as `README.md`.
- The Continue Apply panel targets a different file, such as `src/main.py`.
- The assistant claims the requested file changed even though the apply target
  is unrelated.

Expected behavior:

- Do not click Apply.
- The assistant should say `APPLY_TARGET_MISMATCH` and stop.
- The assistant should not claim success unless the diff changes the requested
  file.

What to check:

```powershell
git status --short --untracked-files=all
git diff -- README.md
git diff -- src/main.py
```

If an unrelated test file was created and it is safe to remove, delete only that
artifact:

```powershell
Remove-Item .\src\main.py -ErrorAction SilentlyContinue
```

Do not use approved write mode for real project changes until the model can keep
the read target, apply target, and reported changed file aligned.

## Ollama Is Not Reachable

Symptoms:

- Continue returns `Connection error`.
- `ollama` is not found on `PATH`.
- `127.0.0.1:11434` does not accept connections.

Checks:

```powershell
Get-Command ollama -ErrorAction SilentlyContinue
Test-NetConnection -ComputerName 127.0.0.1 -Port 11434
Invoke-RestMethod -Uri http://127.0.0.1:11434/ -Method Get
```

Fixes:

- Start Ollama.
- Install Ollama if it is missing.
- Confirm the configured model exists with `ollama list`.
- If Ollama runs on another host, use a local `apiBase` override for testing. Do not commit private network addresses.

## Model Is Missing

Symptoms:

- Continue loads the config but model execution fails.
- Ollama reports that the model is not found.

Checks:

```powershell
ollama list
```

Example models:

```powershell
ollama pull qwen3.5:9b
ollama pull nomic-embed-text
```

Fixes:

- Pull the missing model.
- Use `docs/local-model-selection.md` or `--auto-model-config` to choose a local model for your machine.
- Keep machine-specific model experiments out of committed config unless they are intended defaults.

## Prompts Do Not Appear

Symptoms:

- A prompt file exists but is not invokable.
- Continue does not show a configured workflow.

Checks:

- Confirm the prompt is referenced in `.continue/config.yaml`.
- Confirm frontmatter starts on the first line.
- Confirm `name`, `description`, and `invokable: true` are present.
- Confirm the filename matches the config reference.

Fixes:

- Normalize prompt frontmatter.
- Use lower-case kebab-case prompt names.
- Rerun Continue after changing config or prompt files.

## Rules Do Not Seem To Apply

Symptoms:

- Assistant output ignores expected standards.
- Review output does not reflect `.continue/rules`.

Checks:

- Confirm each rule is referenced in `.continue/config.yaml`.
- Confirm rule frontmatter starts on the first line.
- Confirm the rule is broad and reusable rather than too task-specific.

Fixes:

- Make the relevant prompt explicitly reference the rule conceptually.
- Keep rule language concise and enforceable.
- Add an example output that demonstrates the expected behavior.

## Remote Ollama Endpoint Overrides

The committed config should remain portable and should not include private IP addresses.

For local testing, users may add an `apiBase` value to their local working copy:

```yaml
apiBase: http://your-ollama-host:11434
```

Before committing, verify private addresses are not included:

```powershell
rg -n "apiBase|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\."
```

## Git Shows Line Ending Warnings

Symptoms:

- Git reports `LF will be replaced by CRLF`.

Meaning:

This is usually a Windows line-ending warning, not a content failure.

Checks:

```powershell
git diff --check
```

Fixes:

- Treat `git diff --check` errors as actionable.
- Treat plain LF-to-CRLF warnings as informational unless the repository adopts stricter line-ending rules.

## Validation Before Committing

Run:

```powershell
git status --short --branch
git diff --check
```

Then verify:

- No private endpoints are committed.
- `.continue/config.yaml` has the intended version.
- Local `file://` references resolve.
- README, ROADMAP, TODO, and CHANGELOG match the actual state.
