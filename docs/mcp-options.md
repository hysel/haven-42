# MCP Options Research

## Purpose

This document evaluates Model Context Protocol options for the Continue Enterprise Engineering Pack.

The goal is to identify useful MCP integrations without compromising the pack's local-first posture, portability, or compatibility with Ollama-backed systems.

## Current Recommendation

Do not enable MCP servers by default in `.continue/config.yaml`.

Instead:

- Keep `mcpServers: []` in the default config.
- Document MCP as optional.
- Prefer local `stdio` MCP servers for first adoption.
- Treat GitHub and SonarQube MCP integrations as opt-in because they require credentials, network access, and stronger security review.
- Keep the pack fully usable with local Ollama and no MCP.

## Why Optional MCP

MCP can give Continue access to external tools, systems, and repositories, but each server expands the trust boundary. For an enterprise pack, the safest default is to keep the base configuration local-first and add integrations only when the user explicitly chooses them.

Continue supports MCP through `mcpServers`, and MCP works in agent mode. MCP servers can use local `stdio` transport or remote HTTP-style transports. Remote transports are useful, but they introduce additional network and authentication concerns.

## Local Ollama Compatibility

MCP does not require a cloud model.

The pack should continue to work with:

- Local Ollama on `127.0.0.1`
- Local-network Ollama endpoints used as machine-local overrides
- Self-hosted model endpoints
- No MCP servers enabled

Local model compatibility requirements:

- Do not require cloud-hosted LLMs for MCP workflows.
- Do not commit machine-specific model endpoints.
- Do not require GitHub, SonarQube, or internet access for core prompts.
- Keep repository discovery, planning, reviews, and examples usable without MCP.

## Candidate MCP Integrations

### Filesystem Or Repository Context

Use case:

- Read local files.
- Search project content.
- Inspect repository structure.

Recommendation:

- Defer for now.
- Continue already provides file, code, diff, and terminal context providers in this pack.
- Add a filesystem MCP only if it provides clear value beyond existing Continue context.

Security notes:

- Limit directory access to the active workspace.
- Do not grant access to the full user profile or system drive.
- Avoid write-capable filesystem tools by default.

### GitHub Context

Use case:

- Review pull requests.
- Inspect issues.
- Search repository metadata.
- Connect review workflows to GitHub discussion context.

Recommendation:

- Recommended as the first external MCP candidate, but opt-in only.
- Prefer GitHub's official MCP server or managed endpoint over deprecated community packages.
- Limit toolsets to the smallest set needed, such as repositories, issues, and pull requests.

Security notes:

- Use least-privilege tokens.
- Prefer fine-grained GitHub tokens.
- Never commit tokens or token examples with real values.
- Do not enable write-capable tools until read-only workflows are proven.

### SonarQube Context

Use case:

- Pull quality gate status.
- Inspect vulnerabilities, bugs, code smells, and coverage.
- Link findings to review workflows.

Recommendation:

- Keep manual paste/export workflow as the supported path for now.
- Research API or MCP integration separately.
- Do not add SonarQube MCP until authentication, authorization, and data sensitivity are documented.

Security notes:

- SonarQube findings may expose sensitive implementation details.
- Tokens should be scoped to read-only project analysis.
- Avoid exposing private project keys or internal hostnames in committed examples.

### Issue Tracker Or Project Management Context

Use case:

- Connect implementation planning to tickets, acceptance criteria, and release scope.

Recommendation:

- Not a first integration.
- Defer until GitHub and SonarQube paths are clear.

Security notes:

- Issue trackers often contain customer data, incident details, and private business context.
- Require explicit opt-in and data-handling guidance.

## Recommended First Path

1. Keep default config unchanged with `mcpServers: []`.
2. Add `docs/mcp-setup.md` with optional MCP setup guidance.
3. Start with a read-only GitHub MCP profile.
4. Document required environment variables and permissions.
5. Validate with local Ollama before recommending the integration.
6. Keep SonarQube MCP/API integration as a separate research task.

## Suggested Optional Config Shape

Example only. Do not add this to the default config until the integration is selected and validated.

```yaml
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

## Validation Checklist

- [ ] Continue loads the config with MCP disabled.
- [ ] Continue still works with local Ollama and no internet access for core workflows.
- [ ] Optional MCP setup is documented separately from the default config.
- [ ] Required secrets are environment-based and never committed.
- [ ] MCP tools are read-only where possible.
- [ ] MCP server permissions are scoped to the smallest useful surface.
- [ ] Prompt output identifies MCP-derived context separately from repository-local evidence.

## Decision

MCP support should be optional and documented, not enabled by default.

First candidate: GitHub MCP for read-only repository, issue, and pull request context.

Deferred:

- Filesystem MCP, because Continue already has local file/code/diff context.
- SonarQube MCP/API integration, pending separate integration research.
- Issue tracker integrations, pending stronger data-handling guidance.

## References

- Continue MCP deep dive: https://docs.continue.dev/customize/deep-dives/mcp
- Continue MCP servers docs: https://docs.continue.dev/customize/mcp-tools
- Model Context Protocol project: https://github.com/modelcontextprotocol
- MCP reference servers repository: https://github.com/modelcontextprotocol/servers
- GitHub MCP server: https://github.com/github/github-mcp-server
