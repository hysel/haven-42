# Test Tiers And Exact Content-Tree Receipts

Haven 42 separates routine checks from integration-heavy validation. The full cross-platform GitHub gate remains authoritative.

## Tiers

| Tier | Purpose | Typical contents |
| --- | --- | --- |
| `Fast` | Short local feedback while editing. | Schemas, required files, documentation contracts, safety invariants, and static workflow checks. |
| `Integration` | Exercise scripts that create disposable files or invoke child processes. | Installers, sample repositories, configuration generation, routing, artifacts, packaging plans, and wiki synchronization. |
| `Full` | Release and push confidence. | Every Fast and Integration check with per-test timing. This remains the GitHub Actions tier. |

Windows:

```powershell
.\scripts\test-pack.ps1 -Tier Fast
.\scripts\test-pack.ps1 -Tier Integration
.\scripts\test-pack.ps1 -Tier Full
```

Linux or macOS:

```bash
./scripts/test-pack.linux.sh --tier fast
./scripts/test-pack.linux.sh --tier integration
./scripts/test-pack.linux.sh --tier full
```

### Git Bash on Windows

The native-shell runner automatically resolves a locally installed Python 3 when Git Bash exposes it as `python`, `python.exe`, or the Windows `py -3` launcher instead of `python3`. The local-web Windows and shared launchers apply the same rule: finding a command name is insufficient; the candidate must successfully execute and identify itself as Python 3 before it is selected. This rejects stale Windows Store aliases and broken `py` launchers.

Source workflows also retain compatibility with the Python 3.9 interpreter bundled by supported macOS systems. A source scan rejects use of newer-only `zip(strict=)`, `Path.write_text(newline=)`, and `Path.stat(follow_symlinks=)` APIs in executable repository Python. Packaged builds continue to use the separately locked Python toolchain.

This compatibility step does not install software, download files, use `eval`, or permanently modify `PATH`. If no valid Python 3 command exists, the suite stops once with a clear prerequisite error instead of producing many misleading script failures. Hosted Linux and macOS jobs continue to use their native `python3` command.

The Full suite includes repository validation. Do not run `validate-pack` immediately before `test-pack` unless you need a separate validation result.

## Local Pre-Merge Readiness

During development, run the deterministic spot-mode check before choosing
focused tests:

```powershell
python scripts/check-pre-merge-readiness.py --mode spot
```

The check is read-only. It verifies the authoritative repository and origin,
requires a feature branch, rejects detached, behind, or divergent history,
detects unexpected ignored filenames that look sensitive, inventories every
tracked or non-ignored pending path, and maps that exact path set to reviewed
test commands from `config/pre-merge-readiness.json`. It never executes a
command from the configuration and never prints an ignored sensitive path.
The `repository-core` fallback prevents an unmapped change from bypassing
tests.

Spot mode intentionally accepts pending edits. After the complete change is
staged, its required zero-finding security review has been recorded, and Full
has written its exact-index receipt, `--mode commit` adds the same clean-tree
and Full-receipt check used by the pre-commit hook. Neither mode replaces the
security review, Full, hosted CI, or the existing pre-push protection.

## Timing

Each selected test reports elapsed time. The final summary records the tier, executed count, skipped count, and total duration. Use this output to move expensive tests into Integration or remove repeated process and fixture setup; do not weaken assertions merely to reduce time.

PowerShell repository-validation fixtures are created in the operating system's temporary directory from the current Git-tracked and non-ignored working files. This includes pending publishable edits while excluding ignored build output, lab evidence, privacy backups, and other local-only data. Fixture assembly rejects rooted paths, paths outside the approved roots, symbolic links, and junctions while allowing ordinary OneDrive cloud-file metadata. Tests that need only generated configuration use a smaller purpose-built fixture instead of copying the repository.

The direct PowerShell and shared-shell validators use that same Git-bounded
inventory for private-IP and likely-secret checks. They do not recursively
walk ignored `dist/local-review` or other local-only artifact trees, and they
reject symbolic links and junctions instead of following them while allowing
ordinary OneDrive cloud-file metadata.

## Exact Security-Review Receipt

`config/security-review-gate.json` makes a review mandatory when the staged
change has at least 10 files, at least 500 added-plus-deleted text lines, any
binary file, or a security-sensitive path. Review the complete staged diff. If
anything is found, stop, notify the repository owner, fix every finding, and
repeat the review. Never record a clean result while a finding remains.

After a zero-finding review and with the complete change staged, run:

```powershell
python scripts/security-review-gate.py --record-clean
```

The command refuses unstaged or untracked content and writes
`haven-42-security-review-v1` only inside `.git`. The receipt binds the clean
decision and change statistics to the exact staged index tree. Any subsequent
edit or staging change makes it stale. Smaller ordinary commits do not need a
receipt, but every enhancement still receives security checks appropriate to
its changed surface.

## Exact Full-Test Content-Tree Receipt

A successful Full run with no unstaged or untracked files writes schema-v3 `haven-42-test-receipt-v1` inside the repository's private `.git` directory. The tested content may be the clean `HEAD` tree or the exact staged index tree. The receipt records the current commit for diagnostics, the authoritative tested tree, its `head` or `index` source, tier, and runner. It is not committed or included in release packages.

The pre-commit hook rejects a commit unless:

- the complete intended change is staged with no unstaged or untracked files;
- a mandatory exact-tree security-review receipt exists and reports zero findings;
- the receipt schema and tier match;
- the receipt tree exactly matches the staged index; and
- when the sibling wiki clone is available, all mapped pages are synchronized
  with the native PowerShell or POSIX checker for the host platform.

The pre-push hook skips its duplicate local Full run only when:

- the working tree is clean;
- the receipt schema and tier match;
- the receipt tree exactly matches `HEAD`.

For the efficient safe path, review all roadmap milestones for claim drift,
synchronize mapped wiki pages, run spot-mode readiness and its focused tests,
then stage the complete change and confirm there are no unstaged or untracked
files. Complete the security review, record a clean receipt when required, run
Full without `-NoReceipt`, run commit-mode readiness, and commit without editing
the content. The pre-commit hook proves the reviewed and tested staged tree is
the commit tree; the resulting commit has that same tree, so pre-push reuses the
Full receipt. Any later content edit, partial staging, untracked file, missing
receipt, partial tier, or failed test blocks commit or causes pre-push to run
Full. GitHub Actions always runs Full independently and never trusts a local
receipt.

Use `-NoReceipt` or `--no-receipt` for ephemeral runners and hosted CI.

The recovered local-batch foundations are part of the existing focused and
Full pack paths. Their direct Python suites cover installer/updater simulation,
image/media/quantization candidates, temporary history, folder inspection,
complex documents, lexical/embedding/library boundaries, controlled research,
bare public-repository structure selection, and candidate agent-surface plans.
Every suite must keep inactive components absent from runtime and package
resources; a passing contract test cannot promote a feature.

## Live Tests

Model servers, agent surfaces, ComfyUI, and hardware validation remain separate explicit workflows. A Full pack test does not contact Ollama or another model provider unless a future test is deliberately classified and disclosed as live. Before every live phase, state whether the configured Ollama server is required.
