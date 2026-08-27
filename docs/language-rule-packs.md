# Language Rule Packs

> **Historical Continue evidence:** Continue is a legacy, evidence-only surface in
> Haven 42. The `.continue` paths on this page identify sanitized rule-pack fixtures
> used in earlier validation; they are not current setup or installation guidance.
> The evidence-gating rules remain applicable to maintained coding surfaces.

## Purpose

Language rule packs provide ecosystem-specific guidance without making a default
agent configuration noisy or wrong for every repository.

The historical Continue fixture loaded shared engineering rules plus evidence-gated .NET, ASP.NET Core, and API rules. Its optional language rule-pack sources lived under `.continue/rule-packs/`, and its project-local test installer copied only matching packs into `.continue/rules/active-language-<id>.md` after classification.

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

## Surface-Neutral Use

1. Run project classification using `docs/project-detection.md` or the scripts in `docs/project-profile-classification.md`.
2. Cite the files that prove the ecosystem.
3. Use the matching optional rule pack as supplemental guidance only when evidence is high or medium confidence.
4. Keep recommendations language-neutral when evidence is weak, missing, or unreadable.
5. Label unsupported framework, package-manager, and test-runner assumptions as `unconfirmed`.

## Default Config Behavior

Optional source rule packs are intentionally not referenced from the historical `.continue/config.yaml`. That fixture includes the shared rules and the evidence-gated .NET, ASP.NET Core, and API rules. Their file globs reduce irrelevant activation, while their evidence gates remain authoritative when repository classification is uncertain.

Keeping optional source packs out of a default configuration prevents Python, JavaScript/TypeScript, Java, Go, Rust, SQL, or infrastructure advice from being applied to unrelated repositories. The historical project-local installer created a sanitized profile and materialized only selected packs under `.continue/rules/`. Shared-assets evidence remained project-neutral and did not activate language packs.

## Validation Expectations

Before a language rule pack is promoted from optional to validated, test it against generated sample repositories and record sanitized evidence.

Current evidence:

- `examples/language-rule-pack-validation.md` records static generated-sample validation for the optional Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code rule packs.
- `examples/sample-repository-factory-validation.md` records generated sample factory and focused repository-discovery validation evidence.
- `config/language-workflow-validation-matrix.json` maps every optional rule pack to a medium-complexity fixture and the four required workflow operations.
- `docs/language-workflow-validation-matrix.md` defines the promotion gate and keeps unexecuted model/editor cells pending.

The static generated-sample validation confirms that the optional rule packs match generated sample repository evidence and stay out of the default config. It does not prove editor/model behavior, implementation-planning quality, code-review quality, or approved-write readiness.

Minimum validation:

- repository discovery identifies the ecosystem from exact inspected files
- implementation planning uses language-appropriate guidance without inventing frameworks
- code review avoids unrelated .NET or other ecosystem recommendations
- scoped write changes only the explicitly approved fixture files and is verified with an external Git diff
- output verification catches unsupported framework, toolchain, or filename claims
- documentation, TODO, roadmap, changelog, and wiki remain aligned
