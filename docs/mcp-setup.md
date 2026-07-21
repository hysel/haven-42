# Optional MCP Setup

## Purpose

This document explains how to add optional Model Context Protocol integrations to Haven 42.

MCP is not required for the pack. The default configuration intentionally keeps `mcpServers: []` so the pack remains portable, local-first, and compatible with Ollama-backed systems.

## Default Position

Do not enable MCP in `.continue/config.yaml` by default.

Use MCP only when a team explicitly chooses an integration, understands the data boundary, and can provide the required credentials safely.

## Recommended First MCP Integration

Use GitHub MCP as the first external MCP candidate.

Why GitHub first:

- Repository, issue, and pull request context maps directly to engineering workflows.
- The integration can start as read-only.
- GitHub has an official MCP server.
- It is easier to validate than broad filesystem, database, or quality-system integrations.

Keep SonarQube MCP separate until the SonarQube Web API path is validated and the team is comfortable with token handling.

## Setup Pattern

Prefer a separate local MCP configuration file under `.continue/mcpServers/` instead of editing the default pack config.

Example local file:

```text
.continue/mcpServers/github-mcp.yaml
```

Example shape:

```yaml
name: GitHub MCP
version: 0.0.1
schema: v1
mcpServers:
  - name: GitHub
    type: stdio
    command: docker
    args:
      - run
      - -i
      - --rm
      - -e
      - GITHUB_PERSONAL_ACCESS_TOKEN
      - ghcr.io/github/github-mcp-server
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: ${{ secrets.GITHUB_PERSONAL_ACCESS_TOKEN }}
```

Do not commit local MCP server files that contain organization-specific setup unless the values are fully generic and safe for reuse.

## Required Local Setup

Before enabling GitHub MCP:

1. Confirm Continue is using agent mode for MCP workflows.
2. Confirm Docker or another supported container runtime is installed.
3. Create a least-privilege GitHub token.
4. Store the token in a local secret mechanism or environment variable.
5. Limit repository access to the smallest useful scope.
6. Validate the pack still works with MCP disabled.

## Local Ollama Compatibility

MCP does not require a cloud model.

The pack should continue to work with:

- Local Ollama on the default endpoint
- Local-network Ollama endpoints configured only as machine-local overrides
- Self-hosted OpenAI-compatible model endpoints
- No MCP servers enabled

Validation requirement:

- Run at least one repository-discovery or review prompt with MCP disabled.
- Run the same workflow with GitHub MCP enabled.
- Confirm the model still uses local Ollama for chat/edit behavior.

## Security Requirements

- Use read-only access first.
- Use fine-grained tokens where possible.
- Do not commit tokens, private repository names, organization names, or internal hostnames.
- Do not pass tokens directly in command arguments if they may be saved in shell history.
- Review MCP-derived output as external tool output, not as trusted fact.
- Avoid enabling write-capable tools until governance is defined.

## Recommended Validation Prompt

Use a small, low-risk request first:

```text
Use GitHub MCP only to summarize the open pull requests for this repository.
Do not modify issues, pull requests, files, branches, labels, or repository settings.
Identify which information came from GitHub MCP.
```

Then validate:

- No write operations were attempted.
- The response identifies MCP-derived context.
- The model did not require a cloud LLM.
- The pack still works after removing or disabling the MCP server file.

## Troubleshooting

If MCP tools do not appear:

- Confirm the MCP file is under `.continue/mcpServers/`.
- Confirm the file includes `name`, `version`, and `schema`.
- Confirm Continue is running in agent mode.
- Confirm Docker can pull and run the MCP server image.
- Confirm the token environment variable is available to Continue.
- Restart Continue after adding or changing MCP configuration.

If local Ollama stops responding:

- Disable MCP and confirm Ollama works with the base pack.
- Check whether the MCP server is consuming excessive resources.
- Confirm the model endpoint was not changed in `.continue/config.yaml`.

## References

- Continue MCP deep dive: https://docs.continue.dev/customize/deep-dives/mcp
- Continue MCP server docs: https://docs.continue.dev/customize/mcp-tools
- GitHub MCP server: https://github.com/github/github-mcp-server
- MCP options research: `docs/mcp-options.md`
