# Sample Repository Factory

## Purpose

The sample repository factory creates local, disposable repositories for validating prompts, agent surfaces, language guidance, and approved-write behavior without needing private or customer repositories.

The generated repositories are intentionally small. They are not production templates and they do not install dependencies. Their purpose is to provide realistic file names, project markers, source files, tests, documentation, and configuration signals that an agent can inspect safely.

## Generated Samples

| Sample | Purpose |
| --- | --- |
| `python-api` | Python API-style repository with `pyproject.toml`, source, tests, and app configuration. |
| `typescript-frontend` | TypeScript frontend-style repository with package metadata, source, tests, and Vite config. |
| `node-service` | Node service-style repository with package metadata, service code, tests, and Dockerfile. |
| `java-spring-api` | Java/Spring-style repository with Maven metadata, application source, tests, and properties. |
| `go-service` | Go service-style repository with module metadata, HTTP entry point, and tests. |
| `rust-cli` | Rust CLI-style repository with Cargo metadata, source, and tests. |
| `iac-terraform-kubernetes` | Infrastructure sample with Terraform, Kubernetes manifest, and GitHub Actions workflow. |
| `sql-migrations` | SQL migration sample with schema, migration, seed data, and validation notes. |

## Windows

```powershell
.\scripts\generate-sample-repositories.ps1
```

Use a custom output directory:

```powershell
.\scripts\generate-sample-repositories.ps1 -OutputRoot .\runtime-validation-output\sample-repositories
```

Overwrite previously generated samples:

```powershell
.\scripts\generate-sample-repositories.ps1 -Force
```

List sample names without writing files:

```powershell
.\scripts\generate-sample-repositories.ps1 -List
```

## Linux

```bash
./scripts/generate-sample-repositories.linux.sh
```

## macOS

```bash
./scripts/generate-sample-repositories.macos.sh
```

## Validation Use

Recommended validation flow:

1. Generate samples into `runtime-validation-output/sample-repositories`.
2. Pick one sample repository.
3. Install or point the agent surface at that sample.
4. Run repository discovery.
5. Confirm the agent reports actual files from the sample.
6. Run implementation planning or code review.
7. Verify output with `docs/runtime-output-verification.md` where applicable.
8. Record sanitized evidence using `examples/multi-repository-validation.md` or `examples/sample-repository-factory-validation.md`.

## Guardrails

- Do not treat generated samples as production starter projects.
- Do not publish generated output as evidence of real-world language support by itself.
- Do not add secrets, private endpoints, customer names, or local machine paths to generated samples.
- Do not mark a language or agent surface validated until model output is reviewed and recorded.
## Evidence

Initial script-level validation evidence is recorded in `examples/sample-repository-factory-validation.md`. This evidence covers generation, installation, and runtime context creation for generated samples. Focused CLI evidence also records read-only repository-discovery validation against generated Python and TypeScript samples.

The first focused validation found and fixed two fixture-quality issues: generated PowerShell sample README content could leak factory script text when Markdown backticks were used in a double-quoted here-string, and runtime context generation could inherit parent repository git status when samples lived under ignored runtime output. Tests now cover both classes of regression.

This does not replace editor/model Agent validation or approved-write validation.
