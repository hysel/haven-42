# Language Rule Packs

## Purpose

Language rule packs provide ecosystem-specific guidance without making the default pack noisy or wrong for every repository.

The default `.continue/config.yaml` loads only shared engineering rules. Optional language rule packs live under `.continue/rule-packs/` and should be used only after project detection confirms matching repository evidence.

## Current Optional Packs

| Rule pack | Status | Evidence required before use |
| --- | --- | --- |
| `.continue/rule-packs/python.md` | Static generated-sample validation recorded | Python project metadata such as `pyproject.toml`, `requirements*.txt`, `setup.py`, `poetry.lock`, `Pipfile`, `pytest.ini`, `tox.ini`, or inspected Python package/source files. |
| `.continue/rule-packs/typescript.md` | Static generated-sample validation recorded | JavaScript/TypeScript metadata such as `package.json`, lock files, `tsconfig.json`, frontend/build configs, or inspected `*.ts` / `*.tsx` source and test files. |
| `.continue/rule-packs/java.md` | Static generated-sample validation recorded | Java project metadata such as `pom.xml`, `build.gradle`, `settings.gradle`, wrapper scripts, `src/main/java`, `src/test/java`, or inspected Java source and test files. |
| `.continue/rule-packs/go.md` | Static generated-sample validation recorded | Go project metadata such as `go.mod`, `go.sum`, `cmd/`, `internal/`, `pkg/`, or inspected `*.go` / `*_test.go` files. |
| `.continue/rule-packs/rust.md` | Static generated-sample validation recorded | Rust project metadata such as `Cargo.toml`, `Cargo.lock`, `src/main.rs`, `src/lib.rs`, workspace crates, or inspected Rust source and test files. |
| `.continue/rule-packs/sql.md` | Static generated-sample validation recorded | SQL/database evidence such as migration folders, schema folders, `*.sql`, seed files, database changelog files, or inspected database ownership docs. |
| `.continue/rule-packs/infrastructure-as-code.md` | Static generated-sample validation recorded | IaC evidence such as Terraform/OpenTofu files, Kubernetes manifests, Helm charts, Dockerfiles, Compose files, workflow files, cloud deployment templates, or inspected infrastructure docs. |

## How Agents Should Use Them

1. Run project classification using `docs/project-detection.md`.
2. Cite the files that prove the ecosystem.
3. Use the matching optional rule pack as supplemental guidance only when evidence is high or medium confidence.
4. Keep recommendations language-neutral when evidence is weak, missing, or unreadable.
5. Label unsupported framework, package-manager, and test-runner assumptions as `unconfirmed`.

## Default Config Behavior

Optional rule packs are intentionally not referenced from `.continue/config.yaml`.

This prevents every installed pack from globally applying Python or TypeScript advice to .NET, SQL, infrastructure, documentation, or mixed repositories. If a future installer profile enables language packs automatically, it must do so through explicit profile selection and evidence-gated documentation.

## Validation Expectations

Before a language rule pack is promoted from optional to validated, test it against generated sample repositories and record sanitized evidence.

Current evidence:

- `examples/language-rule-pack-validation.md` records static generated-sample validation for the optional Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code rule packs.
- `examples/sample-repository-factory-validation.md` records generated sample factory and focused repository-discovery validation evidence.

The static generated-sample validation confirms that the optional rule packs match generated sample repository evidence and stay out of the default config. It does not prove editor/model behavior, implementation-planning quality, code-review quality, or approved-write readiness.

Minimum validation:

- repository discovery identifies the ecosystem from exact inspected files
- implementation planning uses language-appropriate guidance without inventing frameworks
- code review avoids unrelated .NET or other ecosystem recommendations
- output verification catches unsupported framework, toolchain, or filename claims
- documentation, TODO, roadmap, changelog, and wiki remain aligned
