# Project Detection

## Purpose

Project detection is the evidence step that comes before language-specific advice. Use it to identify the repository's primary ecosystem, framework, build system, test system, and confidence level before recommending architecture, security, testing, performance, or implementation changes.

If the repository evidence is incomplete, say `unconfirmed` instead of guessing.

## Classification Output

Every project-aware workflow should be able to state:

- Primary ecosystem or language
- Framework or runtime
- Package, dependency, or build system
- Test framework or test runner
- Deployment or packaging surface, when visible
- Confidence level: high, medium, low, or unconfirmed
- Evidence files used
- Unconfirmed assumptions

## Evidence Strength

| Evidence strength | Meaning | Examples |
| --- | --- | --- |
| Strong | Direct project or package metadata. | `.sln`, `.csproj`, `package.json`, `pyproject.toml`, `requirements.txt`, `pom.xml`, `build.gradle`, `go.mod`, `Cargo.toml`, `Dockerfile`, `terraform/*.tf`, migration scripts. |
| Medium | Source layout, imports, framework markers, or test files. | `src/App.tsx`, `tests/test_main.py`, `Controller.java`, `cmd/server/main.go`, `src/main.rs`, `*.test.ts`, `*.spec.ts`. |
| Weak | Naming conventions or README wording without matching files. | Folder names such as `api`, `frontend`, `service`, or broad README claims. |
| Unconfirmed | Expected files are absent or unreadable. | A model expects `package.json` but only saw `src/App.tsx`; a model expects `.csproj` but only saw a C# file. |

## Ecosystem Signals

| Ecosystem | Strong signals | Common supporting signals |
| --- | --- | --- |
| .NET / ASP.NET Core | `.sln`, `.slnx`, `.csproj`, `.fsproj`, `.vbproj`, `Directory.Build.*`, `packages.config`, `global.json` | `Program.cs`, `Startup.cs`, `appsettings*.json`, `Controllers/`, `*.cs`, `*.cshtml` |
| Python | `pyproject.toml`, `requirements*.txt`, `setup.py`, `poetry.lock`, `Pipfile` | `app/*.py`, `tests/test_*.py`, `pytest.ini`, `tox.ini`, imports such as FastAPI, Flask, Django |
| JavaScript / TypeScript | `package.json`, lock files, `tsconfig.json`, `vite.config.*`, `webpack.config.*`, `next.config.*` | `src/App.tsx`, `*.test.ts`, `*.spec.ts`, React/Vue/Svelte imports, `vitest`, `jest`, `playwright` |
| Java / Spring | `pom.xml`, `build.gradle`, `settings.gradle` | `src/main/java`, `src/test/java`, `application.properties`, Spring annotations |
| Go | `go.mod`, `go.sum` | `cmd/*/main.go`, `internal/`, `*_test.go` |
| Rust | `Cargo.toml`, `Cargo.lock` | `src/main.rs`, `src/lib.rs`, `tests/`, `benches/` |
| SQL / database | migration folders, `*.sql`, schema files, seed files | `migrations/`, `schema/`, `db/`, rollback scripts |
| Infrastructure as Code | `*.tf`, Kubernetes YAML, Helm charts, Dockerfiles, workflow files | `terraform/`, `k8s/`, `.github/workflows/`, `docker-compose*.yml` |
| Documentation or config pack | prompts, rules, templates, docs, examples, validation scripts | `.continue/`, `docs/`, `examples/`, script-only repositories |

## Detection Rules

- Use exact filenames from inspected files or supplied runtime context.
- Do not combine a basename from one file with an extension from another file.
- Do not infer a framework from one source file if package or project metadata is missing.
- Do not apply .NET-specific guidance unless .NET evidence is present.
- Do not apply frontend, Python, Java, Go, Rust, SQL, or IaC guidance unless matching evidence is present.
- If package metadata is present, prefer it over source-file guesses for framework, build, and test-runner claims.
- If package metadata is absent, label build and test systems as `unconfirmed` unless test files or documentation clearly identify them.
- If tools cannot read relevant project files, report `READ_TOOLS_UNAVAILABLE` instead of filling gaps with typical framework assumptions.


## Optional Language Rule Packs

Use `docs/project-profile-classification.md` to generate a machine-readable profile and `docs/language-rule-packs.md` to understand how optional language guidance is activated.

Current optional packs:

- `.continue/rule-packs/python.md`
- `.continue/rule-packs/typescript.md`
- `.continue/rule-packs/java.md`
- `.continue/rule-packs/go.md`
- `.continue/rule-packs/rust.md`
- `.continue/rule-packs/sql.md`
- `.continue/rule-packs/infrastructure-as-code.md`

These packs are supplemental. Their source files are not part of the default `.continue/config.yaml` rule list and must not be treated as globally active. Project-local installation copies only selected packs into `.continue/rules/active-language-<id>.md` after classification finds matching ecosystem evidence.
## Prompt Integration

Prompts that review, plan, or recommend changes should start with a short project classification pass before making stack-specific recommendations.

Recommended section:

```md
## Project Classification

- Primary ecosystem:
- Framework/runtime:
- Build/dependency system:
- Test system:
- Confidence:
- Evidence files:
- Unconfirmed assumptions:
```

For small outputs, this can be compressed into one paragraph, but the evidence and confidence should still be visible.

## Validation Expectations

Use generated sample repositories and real repositories to verify detection behavior.

Minimum checks:

- Python samples must not receive .NET-specific project-system advice.
- TypeScript samples must use `package.json` evidence before naming Vite, Vitest, Jest, npm, or build scripts.
- Java, Go, Rust, SQL, and Infrastructure as Code samples must use project metadata before naming frameworks, tools, deployment commands, or database engines.
- Documentation/config packs must not be treated as application codebases unless application files are present.
- Generic repositories with incomplete evidence must remain language-neutral.
