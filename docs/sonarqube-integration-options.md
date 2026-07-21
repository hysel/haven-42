# SonarQube Integration Options

## Purpose

This document evaluates SonarQube integration paths for Haven 42.

The goal is to make SonarQube findings easier to use in AI-assisted review while preserving the pack's local-first posture, compatibility with Ollama-backed systems, and safe handling of enterprise quality data.

## Current Recommendation

Use a staged SonarQube integration model:

1. Keep the manual SonarQube review workflow as the default supported path.
2. Document Web API usage as the first automation path.
3. Treat SonarQube MCP as an optional future path after API-based usage is validated.
4. Do not commit SonarQube hostnames, project keys, tokens, or organization identifiers.
5. Keep `.continue/config.yaml` free of SonarQube-specific credentials and endpoints.

This keeps the pack useful for local Ollama users, self-hosted SonarQube users, SonarQube Cloud users, and teams that cannot expose quality-system data to agent tools.

## Supported Product Targets

The integration guidance should support:

- SonarQube Server
- SonarQube Community Build
- SonarQube Cloud

Project-specific differences should be documented as runtime configuration, not committed repository defaults.

## Integration Options

### Manual Paste Or Export

Use case:

- Triage a failed quality gate.
- Review a small set of findings.
- Classify findings before assigning remediation work.
- Use SonarQube data in Continue without any network integration.

Recommendation:

- Keep as the default workflow.
- Continue using `docs/sonarqube-review.md` and `examples/sonarqube-review.md`.
- Ask users to paste only the minimum finding context needed for review.

Strengths:

- Works offline after findings are copied.
- Does not require tokens or network access from Continue.
- Compatible with local Ollama and private repositories.
- Easiest path for regulated teams.

Limitations:

- Findings can be incomplete or stale.
- Large reports must be summarized.
- No automatic quality gate refresh.

### SonarQube Web API

Use case:

- Retrieve project measures.
- Retrieve quality gate status.
- Retrieve issues for a project, branch, or pull request.
- Build repeatable review inputs without giving Continue direct system access.

Recommendation:

- Use this as the first automation path.
- Prefer a small local script or documented command sequence over direct MCP integration at first.
- Keep credentials in environment variables.
- Generate summarized markdown or JSON review input that users can paste into Continue.

Useful data surfaces:

- Quality gate status
- Issues by severity, type, status, rule, file, and line
- Measures such as code smells, complexity, coverage, vulnerabilities, bugs, duplicated lines, and security hotspots
- Branch or pull request context where supported by the SonarQube edition and project setup

Security requirements:

- Use bearer-token authentication where supported.
- Use read-only user permissions for project data.
- Store tokens in environment variables or secret stores.
- Never commit tokens, internal hostnames, organization keys, or project keys.
- Avoid POST requests unless an operation clearly requires them.
- Avoid automation that changes issue status, suppresses findings, or marks false positives until governance is defined.

Local Ollama compatibility:

- API retrieval is independent from the model provider.
- The pack should still work when SonarQube API access is unavailable.
- Generated review input should be plain text or JSON so local models can process it without remote dependencies.

### SonarQube MCP Server

Use case:

- Let an MCP-capable agent retrieve SonarQube context directly.
- Search issues and quality data during an agent workflow.
- Connect SonarQube findings to code changes with less manual copying.

Recommendation:

- Treat as optional and experimental for this pack until validated with Continue and local Ollama.
- Prefer the official SonarQube MCP server over community alternatives.
- Do not enable it in the default `.continue/config.yaml`.
- Document it later in the MCP setup guide if it proves useful and safe.

Risks:

- Expands the agent tool boundary.
- Requires tokens and endpoint configuration.
- May expose sensitive quality data to a broader AI workflow.
- May differ across SonarQube Server, Community Build, and Cloud setups.
- Requires careful validation with Continue's MCP behavior.

### CI Artifact Integration

Use case:

- Use SonarQube results already produced by CI.
- Avoid direct API calls from developer machines.
- Review quality gate output from build logs or exported artifacts.

Recommendation:

- Useful for enterprises with strict network boundaries.
- Defer detailed setup until the API path is documented.
- Keep artifacts sanitized before adding them to Continue context.

Strengths:

- Uses existing CI permissions.
- Avoids local tokens.
- Produces repeatable review inputs.

Limitations:

- Artifact shape varies by CI provider.
- May not include enough issue detail.
- Can lag behind current branch state.

## Recommended First Automation Path

Create a future `docs/sonarqube-api-workflow.md` that documents a manual command-driven process:

1. User sets environment variables locally:
   - `SONARQUBE_URL`
   - `SONARQUBE_TOKEN`
   - `SONARQUBE_PROJECT_KEY`
2. User runs read-only API requests for:
   - Quality gate status
   - Open issues
   - Key measures
3. User saves or copies a sanitized summary.
4. User invokes the SonarQube review workflow in Continue.
5. Continue classifies findings and recommends remediation.
6. User reruns SonarQube after changes.

This path gives the team automation without giving the AI assistant broad live access to SonarQube.

## Example Review Input Shape

Use this kind of sanitized input for Continue:

```text
Project:
Branch or PR:
Quality Gate:
Analysis Date:

Measures:
- Bugs:
- Vulnerabilities:
- Security Hotspots:
- Code Smells:
- Coverage:
- Duplicated Lines:

Findings:
- Severity:
  Type:
  Rule:
  File:
  Line:
  Message:
  Status:
  Assignee:
  Relevant Code:
```

## Configuration Principles

- Keep SonarQube configuration outside `.continue/config.yaml` until a specific integration is selected.
- Use environment variables for local scripts and optional MCP configuration.
- Keep sample hostnames generic.
- Keep sample project keys generic.
- Include a sanitization step before findings are pasted into Continue.
- Separate SonarQube-derived evidence from repository-local evidence in review output.

## Security Considerations

- SonarQube findings may reveal vulnerable code paths, dependency risks, file names, internal architecture, and compliance gaps.
- Tokens must be least-privilege and revocable.
- Token expiration should be tracked where the platform exposes expiration metadata.
- Automated workflows should start as read-only.
- Findings marked false positive or accepted risk should require human approval.
- Logs must not include tokens, private URLs, project keys, or full API responses from sensitive projects.

## Performance Considerations

- Large projects can produce more findings than a model context can handle.
- API workflows should filter by severity, status, branch, pull request, and changed files where possible.
- Summaries should group findings by release impact instead of dumping complete reports.
- SonarQube Cloud API usage must account for rate limiting.
- Repeated API calls should be avoided during agent loops.

## Validation Checklist

- [ ] Manual SonarQube review still works without API access.
- [ ] API examples use placeholder endpoints and environment variables only.
- [ ] No tokens, private URLs, organization keys, or project keys are committed.
- [ ] Quality gate status can be represented in review input.
- [ ] Findings can be grouped by severity and release impact.
- [ ] Local Ollama can process the generated review input.
- [ ] Optional MCP usage is kept out of the default config.
- [ ] Any future automation is read-only by default.

## Decision

SonarQube support should remain manual-first, with the Web API as the first documented automation path.

The SonarQube MCP server is promising, but it should remain optional until it is validated with Continue, local Ollama, and enterprise token-handling expectations.

## References

- SonarQube Server Web API: https://docs.sonarsource.com/sonarqube-server/extension-guide/web-api
- SonarQube Cloud Web API: https://docs.sonarsource.com/sonarqube-cloud/appendices/web-api
- SonarQube Server token management: https://docs.sonarsource.com/sonarqube-server/2026.2/user-guide/managing-tokens
- SonarQube Cloud token management: https://docs.sonarsource.com/sonarqube-cloud/managing-your-account/managing-tokens
- SonarQube MCP Server: https://docs.sonarsource.com/sonarqube-mcp-server
