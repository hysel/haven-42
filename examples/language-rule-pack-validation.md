# Language Rule Pack Validation Evidence

This file records sanitized validation evidence for optional language rule packs.

Do not include private repository names, private paths, private endpoints, usernames, hostnames, tokens, raw private source code, or raw transcripts.

## 2026-07-14 Medium Fixture And Matrix Static Validation

### Summary

- Validation type: Deterministic medium-fixture generation, project classification, evidence-path, and matrix schema validation
- Samples: `python-layered-api`, `typescript-service-medium`, `multi-language-platform`
- Rule packs covered: Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code
- Operations represented: repository discovery, implementation planning, code review, and scoped write
- Model/editor execution: Not run in this entry

### Result

The three medium-complexity fixtures generate on PowerShell and native-shell
paths. Deterministic tests verify that every matrix evidence file exists and
that project classification selects the expected optional rule pack without
recording local paths or reading file contents.

All operation cells remain `pending-model-validation`. This result proves
fixture and matrix readiness only; it does not promote editor/model behavior or
approved-write readiness. Scoped-write promotion still requires external Git
diff verification.

## 2026-07-08 Generated Sample Static Validation

### Summary

- Validation type: Generated sample repository static validation
- Repository categories: Python API sample, TypeScript frontend sample, Java/Spring API sample, Go service sample, Rust CLI sample, SQL migrations sample, Infrastructure as Code sample
- Operating system: Windows
- Editor surface: Not used for this evidence entry
- Continue version: Not used for this evidence entry
- Model: Not used for this evidence entry
- Provider: Not used for this evidence entry
- MCP state: Not used
- Pack version or commit: `0.2.0` development branch after optional Python, TypeScript, Java, Go, Rust, SQL, and Infrastructure as Code rule packs

### Scope

This pass validates that optional language rule packs line up with generated sample repository evidence and remain gated away from the default Continue config.

This pass does not prove editor/model behavior, implementation-planning quality, code-review quality, or approved-write readiness. Those require separate editor or CLI validation with saved sanitized output.

### Samples Checked

| Sample | Evidence files checked | Rule pack checked | Result |
| --- | --- | --- | --- |
| `python-api` | `SAMPLE-METADATA.md`, `README.md`, `pyproject.toml`, `app/main.py`, `tests/test_main.py` | `.continue/rule-packs/python.md` | Passed |
| `typescript-frontend` | `SAMPLE-METADATA.md`, `README.md`, `package.json`, `tsconfig.json`, `src/App.tsx`, `src/app.test.ts` | `.continue/rule-packs/typescript.md` | Passed |
| `java-spring-api` | `SAMPLE-METADATA.md`, `README.md`, `pom.xml`, `src/main/java`, `src/test/java` | `.continue/rule-packs/java.md` | Passed |
| `go-service` | `SAMPLE-METADATA.md`, `README.md`, `go.mod`, `cmd/server/main.go`, `internal/health/health_test.go` | `.continue/rule-packs/go.md` | Passed |
| `rust-cli` | `SAMPLE-METADATA.md`, `README.md`, `Cargo.toml`, `src/main.rs`, `tests/cli_smoke.rs` | `.continue/rule-packs/rust.md` | Passed |
| `sql-migrations` | `SAMPLE-METADATA.md`, `README.md`, `schema/*.sql`, `migrations/*.sql`, `seeds/*.sql` | `.continue/rule-packs/sql.md` | Passed |
| `iac-terraform-kubernetes` | `SAMPLE-METADATA.md`, `README.md`, `terraform/*.tf`, `k8s/*.yaml`, `.github/workflows/*.yml`, `Dockerfile` | `.continue/rule-packs/infrastructure-as-code.md` | Passed |

### Checks Performed

- Generated multi-language samples from the sample repository factory.
- Confirmed each sample includes clear project metadata and ecosystem-specific project files.
- Confirmed the Python rule pack requires Python evidence such as `pyproject.toml` and uses `unconfirmed` for unsupported assumptions.
- Confirmed the TypeScript rule pack requires JavaScript/TypeScript evidence such as `package.json` and `tsconfig.json` and uses `unconfirmed` for unsupported assumptions.
- Confirmed the Java rule pack requires Java evidence such as `pom.xml` or Gradle metadata and uses `unconfirmed` for unsupported assumptions.
- Confirmed the Go rule pack requires Go evidence such as `go.mod` and uses `unconfirmed` for unsupported assumptions.
- Confirmed the Rust rule pack requires Rust evidence such as `Cargo.toml` and uses `unconfirmed` for unsupported assumptions.
- Confirmed the SQL rule pack requires database evidence such as `*.sql`, schema folders, or migration folders and uses `unconfirmed` for unsupported assumptions.
- Confirmed the Infrastructure as Code rule pack requires IaC evidence such as Terraform, Kubernetes, Docker, workflow, or cloud deployment files and uses `unconfirmed` for unsupported assumptions.
- Confirmed `.continue/config.yaml` does not globally load `.continue/rule-packs/`.
- Confirmed prompts and agents point to `docs/language-rule-packs.md` for evidence-gated supplemental guidance.

### Results

1. The generated Python sample provides enough repository evidence for the optional Python rule pack to be considered applicable during Python-specific review, planning, or discovery workflows.
2. The generated TypeScript sample provides enough repository evidence for the optional TypeScript rule pack to be considered applicable during TypeScript-specific review, planning, or discovery workflows.
3. The generated Java, Go, Rust, SQL, and Infrastructure as Code samples provide enough static evidence for their optional rule packs to be considered applicable during controlled generated-sample workflows.
4. The default pack remains language-neutral because optional rule packs are not globally loaded.
5. The rule packs are ready for controlled generated-sample workflows, but not yet promoted to fully validated language support.

### Remaining Validation

- Run implementation-planning validation against generated language samples.
- Run code-review validation against generated language samples.
- Run editor/model read-only validation with exact file evidence.
- Run approved-write validation only after read-only validation and current-folder path resolution pass.

### Sanitization Checklist

- [x] No private repository names.
- [x] No private local paths.
- [x] No private endpoints, IP addresses, or hostnames.
- [x] No usernames.
- [x] No tokens or secrets.
- [x] No raw private source code.
- [x] No raw transcripts.
- [x] No customer, employer, or internal project identifiers.

## 2026-07-14 Continue CLI Medium-Fixture Matrix Validation

### Summary

- Validation type: Model-backed language/workflow matrix validation
- Surface: Continue CLI `1.5.47`
- Operating system: Windows
- Provider: Ollama-compatible local endpoint; endpoint omitted
- Model: `qwen3.5:9b`
- Fixtures: `python-layered-api`, `typescript-service-medium`, `multi-language-platform`
- Raw output: Ignored runtime output only
- Model unload: Confirmed after the run

### Results

| Ecosystem | Discovery | Planning | Review | Scoped write |
| --- | --- | --- | --- | --- |
| Python | Validated | Validated | Validated | Validated |
| JavaScript / TypeScript | Validated | Validated | Validated | Failed |
| Java | Validated | Failed | Failed | Failed |
| Go | Validated | Validated | Failed | Failed |
| Rust | Validated | Validated | Validated | Failed |
| SQL | Validated | Validated | Validated | Failed |
| Infrastructure as Code | Validated | Validated | Validated | Failed |

Historical result: 19 validated cells and 9 failed cells out of 28.

### Acceptance Checks

- Read-only cells had to return final text and cite operation-specific fixture paths.
- Scoped writes had to change exactly one approved existing file, append exactly one required marker, pass `git diff --check`, survive external content verification, and return sanitized final output.
- Every fixture was restored to a clean Git baseline after validation.
- The Ollama process list was empty after the runner unloaded the model.

### Failure Signals

- `EMPTY_OUTPUT`
- `EXPECTED_FILE_MISSING`
- `CLI_EXIT_1`
- `WRITE_MARKER_MISMATCH`
- `WRITE_FINAL_LINE_MISMATCH`

The Java and Go review responses contained useful findings but did not cite the required full repository paths, so deterministic filename-fidelity gates rejected them. A controlled retry showed that the TypeScript write changed the approved file but placed the marker inline rather than as the required final line and returned no final output; the other five non-Python writes failed external verification. All six remain failed because promotion requires both verified change and sanitized final output.

### Interpretation

- Python is the first medium fixture with complete Continue CLI evidence across all four required operations for this exact surface, model, provider, and operating system.
- Read-only behavior is substantially stronger than scoped-write behavior across the remaining language packs.
- This evidence does not transfer write readiness to another model, operating system, editor surface, or agent plugin.

### Sanitization Checklist

- [x] No private repository names or source code.
- [x] No private local paths.
- [x] No endpoints, IP addresses, hostnames, or usernames.
- [x] No tokens or secrets.
- [x] No raw transcripts.

## Evidence: 2026-07-15 Composite Language-Aware Matrix

- Surface: Continue CLI `1.5.47` on Windows
- Provider: Ollama-compatible local endpoint; endpoint omitted
- Models: `devstral-small-2:24b` and `qwen3.5:35b`
- Fixtures: `python-layered-api`, `typescript-service-medium`, and `multi-language-platform`
- Raw output: ignored runtime output only
- Model unload: verified after each run

`devstral-small-2:24b` passed 27 of 28 cells, failing only TypeScript scoped
write. `qwen3.5:35b` passed 27 of 28 cells, failing only Rust scoped write.
The combined operation lanes validate all 28 cells: Devstral Small 2 is the
default model and Qwen 3.5 35B is the TypeScript scoped-write override.
Each promoted scoped-write cell changed only its approved file, passed
`git diff --check`, ended with the exact marker line, and returned final text.

## Evidence: 2026-07-15 Native macOS Python Smoke

- Surface: Continue CLI `1.5.47`
- Operating system: native Apple Silicon macOS
- Provider: local Ollama; endpoint omitted
- Model: `qwen3.5:9b`
- Fixture: `python-layered-api`
- Raw output: ignored runtime output only
- Model unload: verified after the run

| Operation | Result | Promotion meaning |
| --- | --- | --- |
| Python repository discovery | Validated | Read-only evidence for this exact surface, model, and OS. |
| Python implementation plan | Validated | Read-only evidence for this exact surface, model, and OS. |
| Python code review | Validated | Read-only evidence for this exact surface, model, and OS. |
| Python scoped write | Validated | Changed only the approved file, passed exact-marker and Git checks, returned structured output, and unloaded the model. |

The runner initially exposed three portable-host defects: a missing local
Ollama default when `apiBase` is omitted, a relative config path after changing
to a fixture directory, and Bash 3.2 incompatibility. It also exposed a
headless-output gap and an ambiguous marker prompt. Structured JSON output and
an isolated marker line fixed those issues. The native macOS Python slice was
the first validated slice; the remaining language packs were tested later.

## Evidence: 2026-07-16 Native macOS TypeScript Tooling Blocker

- Surface: Continue CLI `1.5.47`
- Operating system: native Apple Silicon macOS, 16 GB unified memory
- Provider: local Ollama; endpoint omitted
- Model: `qwen3.5:9b`
- Fixture: `typescript-service-medium`
- Operation: code review
- Model unload: verified after every run

The first retest named the expected files but admitted it had not read them.
The matrix runner now rejects that output with `UNREAD_SOURCE_CLAIM`. After the
prompt explicitly required read tools, the model returned `TOOLS_UNAVAILABLE`.
This is a safe failed-model-validation result, not language-rule-pack evidence.
Do not promote JavaScript/TypeScript or any other macOS language pack for this
Qwen 3.5 9B surface/model lane from filename-only output.

## Evidence: 2026-07-17 Native macOS Complete Matrix

- Surface: Continue CLI `1.5.47`
- Operating system: native Apple Silicon macOS
- Provider: local Ollama; endpoint omitted
- Model: `devstral-small-2:24b`
- Fixtures: generated medium-complexity Python, TypeScript, Java, Go, Rust,
  SQL, and Infrastructure as Code samples
- Raw output: ignored runtime output only
- Model unload: verified after every bounded ecosystem run

| Ecosystem | Discovery | Planning | Review | Scoped write |
| --- | --- | --- | --- | --- |
| Python | Validated | Validated | Validated | Validated |
| JavaScript / TypeScript | Validated | Validated | Validated | Validated |
| Java | Validated | Validated | Validated | Validated |
| Go | Validated | Validated | Validated | Validated |
| Rust | Validated | Validated | Validated | Validated |
| SQL | Validated | Validated | Validated | Validated |
| Infrastructure as Code | Validated | Validated | Validated | Validated |

Every scoped-write cell changed only its approved file and passed the external
diff and exact-marker checks. This promotes the complete matrix for this exact
Continue CLI, Ollama, model, and native macOS combination. It does not promote
editor-extension behavior or weaker model lanes.
