# Troubleshooting

## Purpose

Use this guide when the Continue Enterprise Engineering Pack does not load, prompts do not appear, or local model execution fails.

## Quick Checks

Run these checks from the repository root:

```powershell
git status --short --branch
Test-Path .continue/config.yaml
npx -y @continuedev/cli --help
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
npx -y @continuedev/cli --config .continue/config.yaml --readonly -p "Reply OK"
```

Fixes:

- Run the command from the repository root.
- Use an absolute config path if relative resolution is unclear.
- Check YAML indentation.
- Confirm `name`, `version`, and `schema` are present.

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

Expected models:

```powershell
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

Fixes:

- Pull the missing model.
- Update `.continue/config.yaml` only when changing the pack default.
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
