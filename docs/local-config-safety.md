# Local Config Safety

Use this guide when your Continue setup needs machine-specific values such as a local Ollama endpoint, model experiment, hardware note, or absolute path.

## Goal

Keep shared repository files portable and safe.

Do not commit:

- Private IP addresses
- Hostnames
- Usernames
- Local absolute paths
- API keys or tokens
- Raw hardware profile output
- Experimental model names that only work on one machine

## Safe Pattern

Use the committed config for defaults:

```text
.continue/config.yaml
```

Use a local-only file for your machine:

```text
.continue/config.local.yaml
```

This repository already ignores:

```text
.continue/config.local*.yaml
config/model-runtime-policy.local.json
```

That means local files such as these should not be committed:

```text
.continue/config.local.yaml
.continue/config.local.workstation.yaml
.continue/config.local.laptop.yaml
```

## What Goes In The Shared Config

Keep `.continue/config.yaml` generic:

- Use the default local Ollama endpoint when possible.
- Use model names that are documented for the pack.
- Reference only files that are part of the repository.
- Avoid personal paths like `C:\Users\name\...` or `/home/name/...`.

Good shared values:

```yaml
provider: ollama
model: qwen3.5:9b
```

Avoid shared values like:

```yaml
apiBase: http://your-local-ollama-host:11434
```

## What Goes In Local Config

Use local config for values that only apply to your machine:

- A LAN Ollama address
- A temporary test model
- Local MCP server paths
- Machine-specific endpoint overrides
- Private workspace paths

Example local-only setting:

```yaml
apiBase: http://your-private-ollama-address:11434
```

Do not copy that value back into committed docs or `.continue/config.yaml`.

## Model Residency Policy

Copy `config/model-runtime-policy.sample.json` to
`config/model-runtime-policy.local.json` to choose whether a local model is
unloaded after a run or remains loaded for interactive use. The default policy
unloads after a run and permits only one resident model. The model launchers
and direct model-check runners read Ollama's live resident-model list before
loading; they warn about an existing model and block a second model at the
configured limit.

## Before You Commit

Run:

```powershell
git status --short
git diff -- .continue docs README.md
```

Search for common private values. Replace the placeholder text with the patterns your team cares about:

```powershell
rg "PRIVATE_IP_PATTERN|LOCAL_USER_PATH_PATTERN|LOCAL_HOST_PATTERN" .
```

If the search finds a real private endpoint or local path in a committed file, remove it or replace it with a placeholder.

## Hardware Profile Output

The hardware profile scripts are designed to avoid hostnames, usernames, IP addresses, and local paths.

Still, review output before sharing it. Commit only sanitized summaries when they are useful for documentation.

Do not commit raw machine-specific output unless you have reviewed it and confirmed it contains no private details.

## Beginner Checklist

- Keep `.continue/config.yaml` generic.
- Put your machine settings in `.continue/config.local.yaml`.
- Check `git status --short` before committing.
- Check `git diff` before committing.
- Search for private IPs and local paths before pushing.
- When unsure, leave the local value out of the repository.
