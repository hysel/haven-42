# Roadmap

## Status

The repository is in early implementation stage. Milestone 1, Milestone 2, Milestone 3, release hardening for version 0.1.3, CI validation for version 0.1.4, runtime validation tooling for version 0.1.5, Milestone 4 runtime validation and CI, Milestone 5 prompt quality hardening, and Milestone 6 applied tooling and adaptive models are complete. Broader multi-repository validation remains in the backlog.

## Stage Status

| Stage | Status | Summary |
| --- | --- | --- |
| Milestone 1: Minimum Usable Pack | Complete | Core configuration, rules, prompts, agents, templates, setup docs, and Continue/Ollama validation are complete. |
| Milestone 2: Enterprise Review Depth | Complete | Architecture, performance, documentation, reviewer, product, SonarQube, examples, validation checklists, and decision records are complete. |
| Milestone 3: Tooling And Integration | Complete | Troubleshooting guidance, MCP options research, SonarQube integration research, MCP setup docs, and compatibility notes are complete. |
| Release Hardening: 0.1.3 | Complete | Contributor guidance, release tagging guidance, validation automation, sanitized fixtures, and version updates are complete. |
| Milestone 4: Runtime Validation And CI | Complete | GitHub Actions validation, runtime validation tracking docs, context generation, sanitized fixture-based validation, and legacy migration validation notes are complete. |
| Milestone 5: Prompt Quality Hardening | Complete | Prompt-specific fixtures, pass/fail checks, local-model reliability guardrails, banned-output guidance, and stronger static validation are complete. |
| Milestone 6: Applied Tooling And Adaptive Models | Complete | Tool-use modes, approved write guidance, scoped edit guidance, model selection strategy, hardware profiling, model tiers, and local override safety guidance are complete. |
| Milestone 7: Cross-Platform Contributor Experience | Complete | Linux and macOS validation/test wrappers are available, and Linux wrapper execution is covered in CI. |

## Milestone 1: Minimum Usable Pack

Goal: Make the pack loadable, understandable, and useful for common enterprise engineering workflows.

Scope:

- Implement `.continue/config.yaml` for a basic Continue setup. Done.
- Define local-first model assumptions for Ollama. Done.
- Implement core rules. Done:
  - `general.md`
  - `git.md`
  - `dotnet.md`
  - `aspnetcore.md`
  - `clean-architecture.md`
  - `api.md`
  - `testing.md`
  - `logging.md`
  - `security.md`
  - `performance.md`
- Implement core prompts. Done:
  - `repository-discovery.md`
  - `implementation-plan.md`
  - `code-review.md`
  - `bug-investigation.md`
  - `security-review.md`
- Define primary agents. Done:
  - `senior-engineer.md`
  - `architect.md`
  - `security-engineer.md`
- Implement core templates. Done:
  - `Architecture.md`
  - `SecurityReview.md`
  - `PerformanceReview.md`
  - `AI.md`
- Update `README.md` with setup and usage instructions. Done.
- Statically validate local config file references. Done.
- Validate the pack in Continue CLI. Done.
- Validate model-backed prompt execution with Ollama. Done.
- Add example outputs for major workflows. Done.

Exit criteria:

- Continue can load the pack.
- A user can run repository discovery, implementation planning, code review, bug investigation, security review, architecture review, performance review, and documentation workflows.
- A user can run AI framework self-review, refactoring planning, product-management review, and release-readiness workflows.
- Rules and prompts are consistent with this repository's style guide.
- README instructions match tested behavior.

## Milestone 2: Enterprise Review Depth

Goal: Improve the quality and coverage of review workflows.

Scope:

- Add architecture review and performance review prompts. Done.
- Complete reviewer, performance, documentation, and product-manager agents. Done.
- Expand SonarQube guidance. Done.
- Add example review outputs. Done.
- Add validation checklists for prompt and rule changes. Done.
- Add decision records for major design choices. Done.

Exit criteria:

- Review outputs are consistent across architecture, security, code, and performance workflows.
- SonarQube findings can be incorporated manually in a documented way.
- The pack has examples that demonstrate expected usage.
- Prompt and rule changes have documented validation checklists.

## Milestone 3: Tooling And Integration

Goal: Connect the pack to richer repository and quality-system context.

Scope:

- Evaluate MCP servers for repository, filesystem, GitHub, issue tracking, and quality data. Done.
- Define a supported MCP integration path. Done.
- Explore SonarQube integration options. Done.
- Add troubleshooting documentation. Done.
- Add compatibility notes for Continue versions and local model choices. Done.

Exit criteria:

- Integration paths are documented and reproducible.
- MCP support has clear setup instructions.
- SonarQube usage is no longer only conceptual.

## Release Hardening: 0.1.3

Goal: Prepare the repository for repeatable release validation and external contribution.

Scope:

- Add `CONTRIBUTING.md`. Done.
- Add release tagging guidance. Done.
- Add sample review fixtures. Done.
- Add validation automation. Done.
- Update pack version to `0.1.3`. Done.
- Remove completed license work from the backlog. Done.

Exit criteria:

- Release process is documented.
- A validation script can check core repository invariants.
- Sample fixtures are sanitized and reusable.
- Changelog records version `0.1.3`.
- The pack configuration version is `0.1.3`.

## Backlog

## Milestone 5: Prompt Quality Hardening

Goal: Improve prompt reliability by converting runtime validation failures into focused fixtures, pass/fail checks, and stronger prompt-specific guardrails.

Scope:

- Add prompt-specific quality fixtures for implementation planning, legacy dependency migration, documentation review, and release readiness. Done.
- Define pass/fail expectations for sensitive workflows. Done.
- Add validation guidance for local-model reliability issues. Done.
- Extend static validation for prompt frontmatter and required prompt metadata. Done.
- Add checks or review guidance for banned output patterns in high-risk workflows. Done.

Exit criteria:

- Sensitive prompts have explicit pass/fail expectations.
- Legacy dependency migration has a human-reviewed fallback path and a model reliability warning.
- Documentation and release-readiness prompts discourage shallow summaries and unsupported go recommendations.
- Validation catches missing prompt metadata and obvious workflow drift.

## Milestone 4: Runtime Validation And CI

Goal: Validate the pack continuously and exercise it against realistic repositories and review inputs.

Scope:

- Add CI automation for `scripts/validate-pack.ps1`. Done.
- Validate the pack against additional realistic fixture inputs. Done.
- Add more sample fixtures for security, performance, and release-readiness workflows. Done.
- Add project-specific MCP examples after real-world validation.
- Record runtime validation results in repository documentation. Done.
- Add runtime context generation for local-model validation. Done.
- Add legacy .NET dependency migration prompt and template. Done.

Exit criteria:

- CI runs validation on pushes and pull requests.
- Runtime validation gaps are documented.
- Additional fixtures cover the highest-value review workflows.
- Local-model validation limitations are documented where workflows fail guardrails.
- Optional MCP examples remain deferred until validated usage is available.

## Milestone 6: Applied Tooling And Adaptive Models

Goal: Make the pack more useful in real repositories by supporting controlled tool-enabled changes and local hardware-aware model selection.

Scope:

- Define safe tool-use modes for reviewed repositories, including read-only discovery, plan-only review, and approved write mode. Done.
- Document how Continue users can enable tool-backed project changes without weakening approval, validation, rollback, or git safety rules. Done.
- Add prompts or guidance for converting an approved plan into scoped edits in the target project. Done.
- Define a model-selection strategy based on local hardware signals such as available RAM, GPU VRAM, model size, context needs, and workflow risk. Done.
- Add a hardware-profile helper or documented command sequence for collecting local model-selection inputs. Done.
- Define recommended Ollama model tiers for low, medium, and high resource machines. Done.
- Keep machine-specific endpoints, model experiments, and hardware details out of committed shared config. Done.

Exit criteria:

- Users understand when the pack may read, plan, or modify a reviewed repository.
- Tool-enabled changes require explicit approval and include validation and rollback expectations.
- Local model recommendations are tied to hardware capacity and workflow risk.
- The default committed config remains portable and safe for local Ollama users.
- Documentation includes examples for selecting models without committing private machine details.

## Backlog

- Add project-specific MCP examples after real-world validation.
- Validate the pack against additional real repositories when suitable repositories are available.

## Milestone 7: Cross-Platform Contributor Experience

Goal: Make validation and test commands easier for contributors on Linux and macOS while keeping PowerShell as the canonical implementation.

Scope:

- Add Linux shell wrappers for validation and tests. Done.
- Add macOS shell wrappers for validation and tests. Done.
- Keep PowerShell validation and tests as the canonical implementation. Done.
- Add CI coverage for Linux wrapper execution. Done.
- Document cross-platform validation commands in the README. Done.

Exit criteria:

- Windows contributors can run PowerShell validation and tests directly.
- Linux contributors can run shell wrapper commands that call the canonical PowerShell scripts.
- macOS contributors can run shell wrapper commands that call the canonical PowerShell scripts.
- Missing `pwsh` produces a clear setup message instead of a confusing command-not-found failure.
- CI verifies wrapper behavior on Ubuntu.
