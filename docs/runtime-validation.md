# Runtime Validation

## Purpose

This document tracks runtime validation of the Continue Enterprise Engineering Pack against real repositories and realistic review inputs.

Runtime validation is different from static validation. Static validation checks repository invariants. Runtime validation checks whether the pack is useful, accurate, and ergonomic when used in Continue with real code.

Runtime validation also supports deterministic output verification. See `docs/runtime-output-verification.md` for filename-fidelity, unsafe migration-pattern, and lifecycle/support-claim checks.

## Current Status

A private .NET sample repository has been used for initial runtime validation.

The first headless validation attempt was invalid because the CLI captured tool-call JSON instead of final review output. A later context-file-based run produced readable final output for architecture review, which confirms that prompt validation can proceed when repository context is supplied directly.

The repository now includes sanitized fixtures for local prompt validation:

- `examples/fixtures/repository-context.md`
- `examples/fixtures/sonarqube-findings.md`
- `examples/fixtures/security-review-input.md`
- `examples/fixtures/performance-review-input.md`
- `examples/fixtures/release-readiness-input.md`
- `examples/fixtures/implementation-planning-quality-input.md`
- `examples/fixtures/documentation-review-quality-input.md`
- `examples/fixtures/legacy-dependency-migration-input.md`
- `examples/fixtures/release-readiness-quality-input.md`

Additional real-repository validation remains useful. The pack repository itself has now been used as a real validation target for the runtime runner, and the next useful validation target is an application repository with source code, tests, configuration, and meaningful runtime behavior.

## Validation Targets

Prefer repositories with:

- .NET or ASP.NET Core code
- Clean Architecture or layered architecture
- Meaningful tests
- API boundaries
- Logging, security, and performance concerns
- Optional SonarQube or static analysis findings

Do not record private repository names, customer names, internal hostnames, private issue links, secrets, or proprietary implementation details in this file.

## Runtime Validation Matrix

| Date | Repository Type | Model Setup | Workflows Run | Result | Follow-up |
| --- | --- | --- | --- | --- | --- |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | All Milestone 4 runtime workflows | Invalid run: CLI returned tool-call JSON instead of review outputs | Update runner guidance and rerun with a mode that permits read-only inspection. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Architecture review with supplied context file | Partial pass: final text was produced and identified useful high-level concerns, but source-level analysis remained shallow | Improve context generation and rerun repository discovery and architecture review. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Repository discovery with supplied context file | Partial pass: final text identified project type and basic improvement areas, but pasted output was incomplete | Capture complete output and improve source/test context depth. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Security review with supplied context file | Partial pass: final text identified dependency, configuration, and add-in security concerns, but findings remained generic | Improve source/config evidence and require confirmation before dependency-management claims. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Performance review with supplied context file | Partial pass: final text identified likely Excel add-in performance concerns, but included unverified assumptions | Add measurement evidence and richer source summaries before treating performance claims as findings. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Documentation review with supplied context file | Partial pass: final text summarized project/build documentation, but did not identify enough documentation gaps | Strengthen documentation prompt expectations and rerun with README/support context. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Release-readiness review with supplied context file | Partial pass: final text produced a conditional go recommendation, but lacked build/test/package evidence | Require explicit evidence before release recommendation. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Implementation plan with supplied context file | Partial pass: final text produced a migration plan, but included unsafe or unverified migration steps | Strengthen implementation-plan guidance around legacy project migrations. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Implementation plan rerun after guardrail update | Failed guardrail: output still proposed broad project-file rewrite and exposed project-specific details | Add stronger migration-specific prompt constraints. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Implementation plan second rerun after stronger guardrails | Failed guardrail: output became shorter but still gave a mechanical migration recipe | Add explicit no-mechanical-migration constraint or create a dedicated legacy migration workflow. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Legacy dependency migration prompt | Failed guardrail: output provided edit-ready PackageReference XML instead of a phased migration plan | Add forbidden response patterns and minimum acceptable plan requirements. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Legacy dependency migration prompt rerun with no-XML instruction | Failed guardrail: output still produced PackageReference XML and unsafe replacement instructions | Replace negative prompt constraints with a positive fixed checklist/template workflow. |
| 2026-07-02 | Private .NET sample repository | Ollama via local-network endpoint override | Template-driven legacy dependency migration prompt | Failed guardrail: output dumped project-file XML instead of filling the template | Use the fixed template as the human-reviewed path for this local model. |
| 2026-07-02 | Sanitized fixture suite | Static review and local-model validation guidance | Implementation planning, documentation review, legacy dependency migration, release readiness, security, performance, SonarQube, and repository context fixtures | Pass for milestone closure: fixtures now cover high-risk prompt-quality failure modes and are enforced by validation where applicable | Keep real-repository validation in backlog until another suitable repository is available. |
| 2026-07-02 | Private .NET sample repository | VSCodium Continue Agent mode with Ollama local-network endpoint override | Tool-enabled repository discovery setup | Partial pass: default config reached the model, but Agent mode printed raw JSON tool calls instead of executing tools; generated runtime context fallback produced a file-aware response | Document raw JSON tool-call failure, duplicate-rule causes, Windows `file://C:/...` path behavior, and context-file fallback. |
| 2026-07-02 | Private .NET sample repository | VSCodium Continue Agent mode with Ollama local-network endpoint override and `qwen3-coder:30b` | Tool-enabled repository discovery setup | Pass: switching to `qwen3-coder:30b` enabled tool execution where a previous small coder model produced raw JSON tool-call text | Update default model guidance for tool-enabled workflows and keep smaller models as context-file fallback candidates. |
| 2026-07-02 | Pack repository self-validation | Continue CLI through `npx @continuedev/cli` with generated runtime context | All runtime validation workflows | Partial pass: runner completed every workflow and produced final text instead of tool-call JSON, but several outputs were generic or mismatched to a configuration/documentation repository | Add prompt guidance for configuration-pack repositories, evidence discipline, and avoiding app-code recommendations when no application surface exists. |
| 2026-07-03 | Private .NET Framework Excel-DNA add-in repository | Continue CLI with local-network Ollama endpoint override and `qwen3-coder:30b` | All runtime validation workflows | Partial pass: all workflows completed with final text and no tool-call-only JSON, but several outputs remained generic or made claims that require source-level confirmation | Record sanitized findings, improve evidence discipline, and validate future prompt changes against this application-style repository. |
| 2026-07-05 | Private legacy .NET Framework Excel-DNA add-in repository category | Continue CLI with ignored local Ollama config and generated runtime context | Repository discovery, implementation planning, legacy dependency migration readiness | Partial pass: install and context generation worked, read-only outputs were final text, but discovery misstated a project filename and migration readiness included unsupported lifecycle and modernization claims | Keep as Milestone 13 category evidence; strengthen dependency-migration evidence rules before treating migration guidance as safe. |
| 2026-07-05 | Private legacy .NET Framework Excel-DNA add-in repository category | Continue CLI with ignored local Ollama config and generated runtime context | Repository discovery and legacy dependency migration rerun after prompt guardrails | Failed guardrail: the model still synthesized an incorrect project filename and made package/framework compatibility claims without supplied source evidence | Add deterministic output verification or a stricter template fallback for filename fidelity and lifecycle/support claims. |

## Workflow Checklist

Run these workflows during validation:

- [ ] Repository discovery
- [ ] Implementation planning
- [ ] Code review
- [ ] Architecture review
- [ ] Security review
- [ ] Performance review
- [ ] SonarQube review
- [ ] Release readiness

## What To Record

For each validation pass, record:

- Date
- Sanitized repository type
- Model setup, such as local Ollama model name
- Continue surface used, such as CLI or IDE extension
- Prompt or workflow used
- What worked well
- What was confusing
- Missing context or repeated assumptions
- Output quality issues
- Follow-up changes needed

## Acceptance Criteria

A runtime validation pass is useful when:

- The pack can be loaded in Continue.
- The selected local model can complete at least one review workflow.
- The output separates evidence from assumptions.
- The output identifies missing information instead of guessing.
- The workflow produces actionable next steps.
- Any pack gaps are recorded as follow-up work.

## Fixture-Based Smoke Validation

Use fixtures when a real repository is not available.

Suggested smoke tests:

1. Run repository discovery with `examples/fixtures/repository-context.md`.
2. Run SonarQube review with `examples/fixtures/sonarqube-findings.md`.
3. Run security review with `examples/fixtures/security-review-input.md`.
4. Run performance review with `examples/fixtures/performance-review-input.md`.
5. Run release readiness review with `examples/fixtures/release-readiness-input.md`.
6. Run implementation planning quality review with `examples/fixtures/implementation-planning-quality-input.md`.
7. Run documentation review quality review with `examples/fixtures/documentation-review-quality-input.md`.
8. Run legacy dependency migration quality review with `examples/fixtures/legacy-dependency-migration-input.md`.
9. Run release readiness quality review with `examples/fixtures/release-readiness-quality-input.md`.

Fixture validation does not replace future multi-repository validation, but it is sufficient for the current milestone when no additional suitable repository is available. It catches prompt drift, banned output patterns, and output-shape regressions without exposing private code.

## Automated Runtime Runner

Use the runtime validation script from the target repository to run all configured validation workflows and save raw outputs locally.

Example from the root of a target repository:

Windows:

```powershell
$Pack = "C:\path\to\continue-enterprise-engineering-pack"
& "$Pack\scripts\run-runtime-validation.ps1" -TargetRepo (Get-Location).Path
```

Linux:

```bash
PACK="/path/to/continue-enterprise-engineering-pack"
"$PACK/scripts/run-runtime-validation.linux.sh" --target-repo "$PWD"
```

macOS:

```bash
PACK="/path/to/continue-enterprise-engineering-pack"
"$PACK/scripts/run-runtime-validation.macos.sh" --target-repo "$PWD"
```

When using a local-only config file, pass an explicit config path. The runner resolves the path before changing into the target repository:

Windows:

```powershell
$Pack = "C:\path\to\continue-enterprise-engineering-pack"
$Config = "$Pack\.continue\config.local.yaml"
& "$Pack\scripts\run-runtime-validation.ps1" -TargetRepo (Get-Location).Path -ConfigPath $Config
```

Linux:

```bash
PACK="/path/to/continue-enterprise-engineering-pack"
CONFIG="$PACK/.continue/config.local.yaml"
"$PACK/scripts/run-runtime-validation.linux.sh" --target-repo "$PWD" --config-path "$CONFIG"
```

macOS:

```bash
PACK="/path/to/continue-enterprise-engineering-pack"
CONFIG="$PACK/.continue/config.local.yaml"
"$PACK/scripts/run-runtime-validation.macos.sh" --target-repo "$PWD" --config-path "$CONFIG"
```

To append a sanitized summary template to this document:

Windows:

```powershell
$Pack = "C:\path\to\continue-enterprise-engineering-pack"
& "$Pack\scripts\run-runtime-validation.ps1" -TargetRepo (Get-Location).Path -AppendSummary
```

Linux:

```bash
PACK="/path/to/continue-enterprise-engineering-pack"
"$PACK/scripts/run-runtime-validation.linux.sh" --target-repo "$PWD" --append-summary
```

macOS:

```bash
PACK="/path/to/continue-enterprise-engineering-pack"
"$PACK/scripts/run-runtime-validation.macos.sh" --target-repo "$PWD" --append-summary
```

The script writes raw outputs to `runtime-validation-output/`, which is ignored by git. Review and sanitize those outputs before copying any details into committed documentation.

## Runtime Context Generation

Use the runtime context generator when local model validation cannot rely on CLI tool execution.

Example from the root of a target repository:

Windows:

```powershell
$Pack = "C:\path\to\continue-enterprise-engineering-pack"
& "$Pack\scripts\generate-runtime-context.ps1" -TargetRepo (Get-Location).Path -OutputPath .\runtime-context.md
```

Linux:

```bash
PACK="/path/to/continue-enterprise-engineering-pack"
"$PACK/scripts/generate-runtime-context.linux.sh" --target-repo "$PWD" --output-path ./runtime-context.md
```

macOS:

```bash
PACK="/path/to/continue-enterprise-engineering-pack"
"$PACK/scripts/generate-runtime-context.macos.sh" --target-repo "$PWD" --output-path ./runtime-context.md
```

The generated context includes repository structure, project files, config file names, test-related files, top-level documentation excerpts, and selected project-file contents. Review the file before sharing or committing it.

Use this fallback when Agent mode prints raw JSON tool calls instead of executing tools. Attach the generated file with `@Files` and instruct the model:

```text
Using the attached runtime-context.md, run repository discovery.
Do not use tools.
Do not output JSON.
Do not modify files.
```

## Deferred Runtime Validation Work

- Validate against additional application repositories when suitable repositories are available.
- Add project-specific MCP examples after validated real-world usage.
- Revalidate legacy dependency migration with a stronger model or a context file that summarizes project-file risks instead of including raw XML.

## 2026-07-05 Multi-Repository Validation: Legacy .NET Category

Repository category: Private legacy .NET Framework Excel-DNA add-in repository
Model setup: Ignored local Ollama config with generated runtime context
Continue surface: Continue CLI through `npx @continuedev/cli`
Pack commit: `453e01c`

### Setup

- The target repository was checked for a clean git tree before installation.
- Previous untracked local validation artifacts were stashed before the run.
- The latest pack was installed into the target repository with model lanes enabled.
- The installer generated a local-only `.continue/config.local.yaml` with WRITE SAFE, PLAN ONLY, and DEEP REVIEW profiles.
- Runtime context was generated into the pack repository's ignored `runtime-validation-output/` folder.
- Raw prompt outputs remained in ignored local runtime output files and were not committed.

### Workflows Run

- Repository discovery, read-only CLI run with supplied context.
- Implementation planning, plan-only CLI run with supplied context.
- Legacy .NET dependency migration readiness, read-only CLI run with supplied context.

### Result

Partial pass.

Install, context generation, and CLI prompt execution worked. The model produced final text instead of raw tool-call output for all three focused workflows.

The run is not a clean pass because output quality still had evidence problems:

- Repository discovery correctly identified the repository category as a .NET Framework Excel-DNA add-in, but misstated at least one project filename.
- Implementation planning produced a useful high-level configuration-management plan, but some claims need source-level confirmation before being treated as findings.
- Legacy dependency migration readiness stayed in final text and avoided direct XML output in the previewed section, but included broad modernization guidance and an unsupported .NET Framework lifecycle claim.

### What Worked

- Fresh install into a target repository succeeded after stashing prior local artifacts.
- Model lanes config generation worked in the target repository.
- Generated runtime context identified solution, project, package, configuration, documentation, and source-file signals.
- The workflows produced final text with no raw JSON tool-call output.
- The run produced useful category-level evidence for Milestone 13.

### Gaps

- The generated context included the newly installed `.continue` folder as untracked status, which is expected after install but should be clearly interpreted during validation.
- Repository discovery needs stronger filename fidelity checks before its output is considered validated.
- Legacy migration guidance still needs stronger evidence discipline around framework support, Excel-DNA compatibility, and migration sequencing.
- Plan-only validation should continue to require rollback, baseline build, package output, and Excel load validation before any dependency migration is attempted.

### Follow-up

- Add stricter prompt guidance or validation fixtures for legacy dependency migration lifecycle claims.
- Consider adding a filename-fidelity check to future evidence review for repository discovery.
- Run the same Milestone 13 flow against at least two additional repository categories before closing the milestone.
- Keep all raw outputs local and ignored unless a sanitized excerpt is intentionally added.

## 2026-07-03 Private Excel-DNA Add-In Runtime Validation

Repository type: Private .NET Framework Excel-DNA add-in repository
Model setup: Local-network Ollama endpoint override with `qwen3-coder:30b`
Continue surface: Continue CLI through `npx @continuedev/cli` with generated runtime context

### Workflows Run

- Repository discovery
- Architecture review
- Code review
- Implementation planning
- Bug investigation
- Security review
- Performance review
- Documentation review
- AI framework self-review
- Refactoring planning
- Product review
- Release readiness

### Result

Partial pass.

All runtime validation workflows completed and produced final text. None of the workflow outputs were raw tool-call-only JSON. This validates the context-file runtime path against an application-style repository that includes project files, add-in configuration, package references, source code, and build assets.

The strongest outputs were repository discovery, documentation review, release-readiness review, and code/security review. They identified the repository as a .NET Framework Excel-DNA add-in, recognized package-management and Excel-DNA packaging concerns, and called out missing tests, setup documentation, release evidence, and credential/input-handling risks.

### What Worked

- The runner completed all workflows with the local-network Ollama config.
- The model produced final text instead of tool-call JSON.
- Repository discovery correctly recognized the Excel-DNA add-in shape and major build/dependency assets.
- Documentation review produced useful onboarding, build, debugging, testing, and deployment documentation gaps.
- Release readiness correctly treated missing tests, documentation, rollback guidance, and security evidence as blockers.
- Code and security review identified high-value risk areas such as credential handling, external API calls, input validation, local data storage, logging, dependencies, and missing tests.

### Gaps

- Some outputs still included generic recommendations that need source-level confirmation before being treated as findings.
- Repository discovery incorrectly stated that top-level documentation was absent, despite documentation files existing in the target repository.
- Some reviews inferred implementation details from package references and file names rather than confirmed source evidence.
- The implementation-plan workflow produced a plausible audit-logging plan, but the scenario was generic and not strongly grounded in actual write-operation evidence.
- Security findings need sharper evidence labels so suspected risks are not presented as confirmed vulnerabilities unless the source context proves them.

### Follow-up

- Strengthen review prompts to require explicit evidence labels for source-level claims.
- Improve generated runtime context to summarize top-level documentation presence more clearly.
- Add or update fixtures for application repositories where package references imply risks but source evidence is limited.
- Rerun targeted code/security/release-readiness validation after prompt changes.
- Defer project-specific MCP examples until at least one validated workflow benefits from live repository/file context beyond generated context.

## 2026-07-02 Pack Repository Self-Validation

Repository type: Public configuration, documentation, and validation-script repository
Model setup: Default pack config through Continue CLI
Continue surface: Continue CLI through `npx @continuedev/cli` with generated runtime context

### Workflows Run

- Repository discovery
- Architecture review
- Code review
- Implementation planning
- Bug investigation
- Security review
- Performance review
- Documentation review
- AI framework self-review
- Refactoring planning
- Product review
- Release readiness

### Result

Partial pass.

The runtime runner completed every configured workflow and generated final text outputs. None of the workflow outputs were tool-call-only JSON. This validates the runner path, generated runtime context path, and basic prompt invocation path against this repository.

The output quality was mixed. Several workflows produced the requested section structure, but multiple reviews treated this repository like an application codebase instead of a configuration/documentation pack. Some outputs recommended authentication, authorization, input validation, structured logging, or dependency controls without first establishing an application runtime surface. The code review also flagged the documented `npx @continuedev/cli` fallback as a problem even though it is intentionally documented for users who do not have `cn` installed.

### What Worked

- The runtime runner completed all workflows.
- Generated runtime context was accepted by the prompts.
- Outputs were final review text rather than raw tool-call requests.
- Repository discovery, architecture review, AI self-review, documentation review, and product review produced usable high-level structure.
- The run exposed prompt-quality gaps that were not visible from static validation alone.

### Gaps

- Some prompts did not adapt well to a repository whose primary assets are prompts, rules, documentation, config, and validation scripts.
- Several findings were generic and not tied to evidence from the generated context.
- Security and architecture reviews sometimes recommended application-layer controls that do not apply directly to this repository.
- Refactoring guidance suggested centralizing duplicate configuration without identifying specific duplicated config.
- Release-readiness output was conservative, but some blocking issues were generic and did not acknowledge the existing release docs, CI, changelog, and rollback guidance.

### Follow-up

- Add or update prompt guidance for configuration-pack repositories.
- Strengthen evidence requirements so reviews label unsupported claims as assumptions.
- Add a prompt-quality fixture for non-application repositories.
- Consider adding validation checks for known bad recommendations, such as replacing the documented `npx @continuedev/cli` fallback with `cn` only.
- Validate next against an application repository before creating project-specific MCP examples.

## 2026-07-02 Validation Notes

Repository type: Private .NET sample repository
Model setup: Ollama through local-network endpoint override
Continue surface: Continue CLI through `npx @continuedev/cli`
Raw output location: ignored local `runtime-validation-output/` folder

### Result

Invalid runtime validation run.

The runner successfully executed each workflow command, but the captured outputs were tool-call requests rather than completed review responses. Examples included requests to list files, read README/config files, inspect git changes, and ask clarifying questions.

### What Worked

- The local test config reached the Ollama server.
- The runtime runner produced one output file per workflow.
- Raw outputs stayed in the ignored `runtime-validation-output/` folder.
- The failed run exposed a CLI execution-mode issue that should be fixed before treating runtime validation as complete.

### Gaps

- Headless `--readonly` mode did not produce final review text for this run.
- The generated summary draft used literal placeholder paths in some rows.
- The run did not produce enough evidence to evaluate prompt quality.

### Follow-up

- Update the runtime runner to flag tool-call-only output.
- Rerun against the same repository using a CLI mode that allows read-only inspection and final response generation.
- Record only sanitized findings after a successful rerun.


## 2026-07-02 Partial Architecture Review

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Architecture review

### What Worked

- The workflow produced final text instead of tool-call JSON when repository context was supplied directly.
- The output identified the repository as a .NET Framework desktop integration/add-in style project.
- The output recognized legacy package-management and build-configuration concerns.
- The output called out dependency review, security review, performance review, and test coverage as relevant follow-up areas.
- The output recognized that more source, dependency, configuration, and test context was needed for a deeper review.

### Gaps

- The output was useful but still too shallow to count as full architecture validation.
- The supplied context did not include enough source implementation detail to evaluate coupling, cohesion, dependency direction, or test seams.
- The review did not produce a useful architecture diagram or risk-ranked improvement plan.
- The review stayed at project/dependency/build level and did not deeply evaluate runtime boundaries or design structure.

### Follow-up

- Use the runtime context generator for your operating system to build richer supplied context.
- Rerun repository discovery and architecture review with the generated context.
- Add a short sanitized source summary to the runtime context when source code cannot be committed into validation notes.
- Update the runtime runner or guidance so local Ollama validation does not rely on CLI tool execution.

## 2026-07-02 Partial Repository Discovery

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Repository discovery

### What Worked

- The workflow produced final text instead of tool-call JSON when repository context was supplied directly.
- The output identified the repository as a .NET Framework desktop integration/add-in style project.
- The output recognized dependency-management, build-configuration, debugging, compatibility, testing, security, and performance concerns.
- The output reached a clear conclusion instead of stopping at a tool request.

### Gaps

- The pasted output was incomplete, so the full repository-discovery structure could not be validated.
- The review stayed mostly at project configuration and dependency level.
- The output did not provide a complete repository structure, current architecture map, or risk-ranked next-step plan.
- The generated context still needs richer source and test summaries.

### Follow-up

- Rerun repository discovery and capture the complete output.
- Improve generated context with sanitized source summaries and test coverage signals.
- Compare the rerun output against the expected repository-discovery format.

## 2026-07-02 Partial Security Review

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Security review

### What Worked

- The workflow produced final text instead of tool-call JSON when repository context was supplied directly.
- The output identified relevant security review areas for a .NET Framework desktop integration/add-in style project.
- The output called out dependency hygiene, external HTTP client usage, JSON handling, local data storage, add-in trust boundary concerns, debug/build configuration, and configuration-file secrets.
- The recommendations were directionally useful: update dependencies, avoid hardcoded secrets, review add-in behavior, disable debug-only production behavior, and perform code/security testing.

### Gaps

- The findings were mostly generic and did not include source-level evidence.
- The output did not clearly separate confirmed facts from assumptions.
- The dependency-management comments need confirmation from actual project files before being treated as findings.
- The review did not identify concrete trust boundaries, data flows, sensitive data types, or validation points.

### Follow-up

- Improve generated context with sanitized summaries of external API calls, local data storage, configuration usage, and add-in entry points.
- Update security-review runtime guidance to require confirmed evidence for dependency-management claims.
- Rerun security review with richer context and record only confirmed, sanitized findings.

## 2026-07-02 Partial Performance Review

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Performance review

### What Worked

- The workflow produced final text instead of tool-call JSON when repository context was supplied directly.
- The output identified relevant performance areas for a .NET Framework desktop integration/add-in style project.
- The output called out dependency loading, network operations, JSON processing, local data access, resource disposal, profiling, and package-management modernization as relevant review areas.
- The recommendations were directionally useful for a desktop add-in that may interact with external services and local data.

### Gaps

- The output included unverified assumptions about build efficiency, runtime acceptability, target environment, and compiler settings.
- The review did not include measured performance evidence.
- The review did not identify concrete hot paths, API call patterns, Excel interaction costs, data volume risks, or local storage query behavior.
- The supplied context still lacks enough source implementation detail to validate performance findings.

### Follow-up

- Improve generated context with sanitized summaries of Excel entry points, external API calls, local data access, loops over worksheet ranges, and resource-disposal patterns.
- Add runtime evidence where possible, such as build time, startup time, API call volume, and large workbook behavior.
- Update performance-review guidance to distinguish measured facts from likely risks when context is sparse.

## 2026-07-02 Partial Documentation Review

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Documentation review

### What Worked

- The workflow produced final text instead of tool-call JSON when repository context was supplied directly.
- The output summarized the repository purpose, technology target, dependency model, build properties, bootstrapper packages, debug configuration, and packaging flow.
- The output recognized that the project has specific build/debug/distribution concerns because it is a desktop add-in style project.

### Gaps

- The output mostly restated discovered configuration rather than reviewing documentation quality.
- The review did not identify concrete missing docs, onboarding gaps, operational guidance, troubleshooting needs, or support handoff risks.
- The output made a broad "best practices" conclusion without enough evidence.
- The supplied context needs richer README/support/release documentation signals.

### Follow-up

- Rerun documentation review with explicit instructions to identify missing or weak documentation, not only summarize existing configuration.
- Improve generated context with README excerpts, support/security docs, release notes, and setup instructions where available.
- Update the documentation prompt if it continues to summarize instead of evaluate.

## 2026-07-02 Partial Release-Readiness Review

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Release readiness

### What Worked

- The workflow produced final text instead of tool-call JSON when repository context was supplied directly.
- The output identified release-relevant areas for a desktop add-in style project: dependencies, build configuration, debug configuration, and packaging.
- The output produced a conditional release recommendation rather than a hard go.
- The recommendations included dependency verification, build validation, debug configuration review, and packaging validation.

### Gaps

- The release recommendation was too optimistic for the available evidence.
- The output did not require concrete build results, test results, packaged artifact validation, rollback guidance, or known-issues review before release.
- The review did not distinguish internal validation readiness from production release readiness.
- The supplied context lacked CI results, test status, release notes, installation validation, and distribution requirements.

### Follow-up

- Update release-readiness guidance to require explicit evidence before any go recommendation.
- Improve generated context with build/test/package status when available.
- Rerun release-readiness review after recording build output, package output, test status, and installation validation.

## 2026-07-02 Partial Implementation Plan

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Implementation plan

### What Worked

- The workflow produced final text instead of tool-call JSON when repository context was supplied directly.
- The output identified the requested dependency-management migration objective.
- The output included basic validation steps such as building, testing, cleanup, and committing changes.

### Gaps

- The plan included unsafe or questionable migration advice, including temporarily renaming the project file.
- The plan implied an SDK-style project conversion without enough evidence that this is safe for a legacy desktop add-in project.
- The plan did not identify Excel-DNA packaging/build-target risks as first-class migration risks.
- The plan did not include a rollback strategy beyond generic backup/commit advice.
- The plan did not call out the need to validate add-in packaging output and runtime loading in Excel after migration.

### Follow-up

- Strengthen the implementation-plan prompt to require safer legacy project migration planning.
- Add guidance to avoid unsupported project-file renames unless a tool explicitly requires them.
- Require migration plans to preserve existing project style unless an SDK-style conversion is explicitly selected and validated.
- Rerun the implementation plan with instructions to consider Excel-DNA build targets, packaging output, and rollback.

## 2026-07-02 Implementation Plan Rerun

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Implementation plan rerun after prompt guardrail update

### Result

Failed guardrail validation.

The rerun produced final text, but it still proposed a broad project-file rewrite and included project-specific file/package details. It improved slightly by avoiding the earlier temporary project-file rename, but it still treated package-management migration too mechanically for a legacy desktop add-in style project.

### Gaps

- The output still implied SDK-style conversion without an explicit user request.
- The output still included a large project-file example instead of a safe plan.
- The output did not sufficiently separate PackageReference migration from SDK-style migration.
- The output did not protect custom build targets, packaging behavior, and runtime loading as first-class risks.

### Follow-up

- Add stronger implementation-plan guardrails for legacy project migrations.
- Require plans to avoid full rewritten project-file examples unless explicitly requested.
- Rerun after prompt/rule updates and check whether the output preserves project style and focuses on phased validation.

## 2026-07-02 Implementation Plan Second Rerun

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Implementation plan second rerun after stronger prompt guardrails

### Result

Failed guardrail validation.

The rerun no longer included a full project-file rewrite, but it still produced a generic mechanical migration recipe. It recommended removing the legacy package file and adding package reference nodes without first requiring inventory of package build assets, custom targets, native assets, generated packaging output, or runtime loading behavior.

### Gaps

- The output still treated dependency migration as a simple file-edit task.
- The output did not require a branch-based phased migration.
- The output did not protect package-provided build targets and packaging behavior.
- The output did not include adequate rollback or runtime validation.

### Follow-up

- Add an explicit no-mechanical-migration constraint for custom MSBuild and add-in projects.
- Consider adding a dedicated legacy dependency migration prompt if the general implementation-plan prompt remains too broad.
- Rerun once more and verify that the plan starts with inventory, risk classification, phased migration, validation, and rollback.

## 2026-07-02 Legacy Dependency Migration Prompt Validation

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Legacy .NET dependency migration

### Result

Failed guardrail validation.

The dedicated workflow produced final text, but it still provided direct edit instructions and a complete PackageReference replacement block. That is not acceptable for a legacy desktop/add-in style project because it bypasses inventory, build asset analysis, packaging validation, runtime loading validation, and rollback planning.

### Gaps

- The output was an implementation recipe rather than a migration plan.
- The output included edit-ready XML that could encourage unsafe project-file changes.
- The output did not require baseline restore/build/package/runtime validation before edits.
- The output did not separate package-management migration from project-system migration risk.

### Follow-up

- Add explicit forbidden response patterns to the dedicated prompt.
- Require a minimum acceptable phased plan.
- Rerun the dedicated prompt and verify it avoids XML replacement blocks and starts with evidence gathering.

## 2026-07-02 Legacy Dependency Migration Prompt Rerun

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file  

### Workflows Run

- Legacy .NET dependency migration rerun with explicit no-XML instruction

### Result

Failed guardrail validation.

The rerun explicitly requested a plan only, with no XML and no direct edit instructions. The output still produced a complete PackageReference-style XML block and recommended deleting the legacy package file before proving restore, build, package, runtime loading, and rollback behavior.

### Gaps

- The model ignored explicit no-XML and no-direct-edit instructions.
- The output introduced an unsafe replacement strategy using a shared build props file.
- The output again treated the migration as a mechanical dependency declaration rewrite.
- The output continued to assume command-line restore behavior without confirming project-system support.

### Follow-up

- Stop relying on negative prompt constraints for this local model and workflow.
- Add a positive fixed checklist/template for legacy dependency migration planning.
- Validate the template-driven workflow instead of asking the model to invent migration steps.

## 2026-07-02 Template-Driven Legacy Dependency Migration Validation

Repository type: Private .NET sample repository  
Model setup: Ollama through local-network endpoint override  
Continue surface: Continue CLI with supplied runtime context file and fixed template  

### Workflows Run

- Legacy .NET dependency migration with fixed template

### Result

Failed guardrail validation.

The workflow was instructed to use the fixed template, avoid XML, and avoid direct edit instructions. The output still returned a project-file XML dump instead of filling the template with a phased migration plan.

### Gaps

- The local model did not follow the template instruction for this workflow.
- The output exposed project-file details instead of producing a sanitized planning artifact.
- Additional negative constraints are unlikely to fix this behavior reliably for this local model.

### Follow-up

- Treat the fixed `LegacyDotNetDependencyMigration` template as the safe human-reviewed path for this workflow.
- Do not rely on this local model to generate legacy dependency migration plans without human review.
- Validate this workflow later with a stronger model or with a narrower context that excludes raw project-file XML.
