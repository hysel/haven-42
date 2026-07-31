# Milestone 22 Admission Readiness

`config/milestone22-admission-readiness-contract.json` is the fail-closed source
of truth for the remaining Milestone 22 promotion gates. It separates work that
is already admitted for the unsigned browser/PyInstaller development package
from work that still requires an owner decision, external dependency, trusted
cryptographic identity, native evidence, or machine-effect approval.

Run the offline evaluator with:

```text
python scripts/evaluate-milestone22-admission.py
```

The evaluator reads only repository files. It does not contact a provider or
GitHub, inspect the host, create a process other than its own Python runtime,
write a file, sign or notarize an artifact, install software, activate an
update, execute a workflow, or modify a machine. Scenario claims and renderer
values cannot change gate state.

## Current Gates

| Gate | Current scope | State | What remains |
| --- | --- | --- | --- |
| Comparative model promotion | Exact Qwen adapter baseline only | Owner-deferred | Independent reviewers, criterion scoring, and license/platform reconciliation. End-user inconsistency reports may reopen the work. |
| Read-only validation integration | Readiness, provider health, model evidence, cleanup, and committed evidence | Development-admitted | Software execution and production lifecycle validation remain separate gates. |
| Tauri native runtime | Architecture and policy model only | Policy-blocked | Explicit owner reversal of the unadmitted decision, a reviewed published dependency resolution, actual native bridge tests, and exact-platform packages. |
| Production package promotion | Unsigned PyInstaller one-folder package with an inactive signing policy, confirmed repository-account MFA, and deterministic Windows identity metadata | External-blocked | An existing public release in the form to sign, provider acceptance and signing-service MFA, exact packaged-dependency license review, managed signing identity/custody, macOS notarization and physical-Mac evidence, clean lifecycle tests, and a production support policy. |
| Installer runtime | Simulation only | Security-blocked | Trusted package verification, canonical user-scoped paths, transactional rollback, and native install/upgrade/uninstall evidence. |
| Online updater activation | Offline policy and simulation only | Security-blocked | A real verifier and governed roots, canonical staging, atomic activation, and native interruption/rollback/retention evidence. |
| Executable composition | Planning, admission, and journal simulation only | Security-blocked | An engine-owned approval broker, authoritative journal, canonical grants/process allowlists, and native cancellation/recovery evidence. |

None of these blockers prevents continued use or testing of the unsigned
development package. The ledger therefore requires
`blocksUnsignedDevelopmentPackage: false` for every gate.

## Promotion Boundary

The ledger cannot promote itself. Every authority flag is fixed false:

- runtime authority;
- machine effects;
- online update activation;
- platform code signing and notarization;
- release publication;
- Tauri/Rust admission; and
- production-readiness claims.

The hostile self-test rejects missing or duplicated gates, unknown status
values, unsafe or missing evidence references, malformed blockers, any gate
that attempts to block the existing unsigned development package, unexpected
runtime admission, and every authority flag changed to true.

## Owner Decisions

The repository owner must explicitly approve each of the following before work
crosses the current boundary:

1. admitting Tauri/Rust or a source-built exception;
2. selecting and using signing or notarization identities;
3. testing installation, upgrade, rollback, or uninstall on a machine;
4. activating network update checks or downloads;
5. issuing real workflow approvals or executing effectful workflows; and
6. publishing or claiming production readiness.

An approval for one gate does not transfer to another gate.

## Signing Readiness

The public [code-signing policy](https://github.com/hysel/haven-42/wiki/Code-Signing-Policy), [privacy
policy](https://github.com/hysel/haven-42/blob/main/PRIVACY.md), and [SignPath eligibility
audit](signpath-eligibility-audit.md) prepare evidence without activating
signing. The Windows build now defines and verifies deterministic Haven 42
product, version, description, and filename metadata.

The audit remains external-blocked because the authoritative repository has no
published GitHub Release or downloadable release asset in the form proposed
for signing. The owner confirmed GitHub MFA is enabled on 2026-07-27;
signing-service MFA remains a future enrollment requirement. A final
exact-package dependency/license review also remains open. No application,
certificate, service configuration, signature, installer, notarization, or
public binary publication is authorized.
