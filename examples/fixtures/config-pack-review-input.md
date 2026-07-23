# Configuration Pack Review Fixture

## Purpose

Use this sanitized fixture to test whether review prompts adapt to a repository that is not an application codebase.

## Scenario

Repository type: Continue configuration, prompt, documentation, examples, and validation-script pack

The repository contains:

- `.continue/config.yaml`
- `.continue/prompts/*.md`
- `.continue/rules/*.md`
- `.continue/agents/*.md`
- `.continue/templates/*.md`
- `docs/*.md`
- `examples/*.md`
- `config/model-recommendations.tsv`
- `scripts/validate-pack.ps1`
- `scripts/test-pack.ps1`
- `.github/workflows/validate-pack.yml`

The repository does not contain:

- Web API controllers
- Authentication middleware
- Authorization policies
- Database access code
- Application service layers
- Runtime logging code
- Production deployment manifests

## Expected Review Behavior

Good review outputs should:

- First classify the repository as a configuration/documentation/prompt pack.
- Focus on prompt quality, rule consistency, local config safety, file references, validation scripts, fixtures, examples, CI, versioning, changelog, release process, and contributor setup.
- Separate confirmed evidence from assumptions.
- Treat absent application runtime surfaces as not applicable, not as defects.
- Avoid recommending authentication, authorization, API input validation, database controls, runtime logging, or web rate limiting unless the prompt is explicitly discussing a target application repository.

## Known Bad Recommendations

The following recommendations should fail this fixture unless backed by explicit evidence:

- Add authentication to protect repository access.
- Add authorization checks to API endpoints.
- Add database rollback scripts.
- Add structured logging to application services.
- Replace the documented `npx @continuedev/cli@1.5.47` fallback with `cn` only.
- Centralize duplicate configuration without naming duplicated files or settings.
