# GitHub Repository Policy

`config/github-repository-policy.json` is the reviewable source of truth for Haven 42 repository governance. `scripts/verify-github-repository-policy.py` checks committed workflow structure offline; `--live` additionally compares the authoritative GitHub repository settings through GitHub CLI.

The privacy gate scans reachable Git history plus every tracked or untracked
non-ignored working-tree file. This catches pending evidence before staging or
commit while preserving ignored local review/build directories outside the
public-repository scope.

## Required Pull Request Gate

`main` requires a current branch and these uniquely named checks:

- Public repository privacy
- Wiki synchronization
- Windows PowerShell validation
- Linux script smoke tests
- macOS script smoke tests
- Windows portable package
- Linux portable package
- macOS portable package
- CodeQL Python analysis

Portable jobs use one immutable GitHub-owned `setup-python` action commit and
one exact Python 3.14.6 patch version across all three native runners. This
keeps runtime, SBOM, notice, and component evidence from drifting with runner
image defaults.

The three package jobs live in `Validate Pack` beside repository validation so one exact-SHA workflow and the existing hosted verifier cover the complete cross-platform gate. CodeQL remains a separate least-privilege security workflow.

`Attest unsigned development artifacts` is intentionally not a pull-request
required check. It is skipped for pull requests and runs only on a push to
`main` after all three package jobs succeed. This prevents untrusted
pull-request code from receiving OIDC or attestation-write authority while
still binding the resulting main-branch unsigned archives to their hosted
build.

## Merge And Branch Rules

`main` requires linear history, successful strict status checks, conversation resolution, administrator enforcement, and stale-review dismissal. Force pushes and deletion are disabled. Merge commits are disabled at repository level because they conflict with linear history; squash and rebase remain available, and merged branches are deleted automatically.

The repository currently has one eligible CODEOWNER. GitHub does not allow an author to approve their own pull request, so a mandatory approval would block solo maintenance without adding independent review. Required approval count and CODEOWNER review therefore remain zero; all security-sensitive files stay mapped in CODEOWNERS, and independent review is required when another eligible maintainer is available.

## Actions Rules

Actions receive read-only default workflow permission and cannot approve pull requests. Only GitHub-owned actions are admitted, and GitHub enforces full-length commit-SHA pinning. Workflows independently declare minimum permissions and disable persisted checkout credentials.

Dependabot checks GitHub Actions weekly. The CodeQL `init` and `analyze`
sub-actions are grouped so they cannot propose incompatible scanner versions
in separate pull requests.

The isolated attestation job adds only `actions: read`, `contents: read`,
`id-token: write`, `attestations: write`, and `artifact-metadata: write`.
Repository contents, packages, releases, pull requests, deployments, and
administration remain non-writable. The static verifier rejects attestation on
`pull_request_target`, moving action tags, registry publication, Release-like
write permissions, incomplete native artifact coverage, or drift from
`config/github-repository-policy.json`.

## Efficient Local-to-Hosted Flow

1. Make the complete local change and synchronize the wiki before opening the PR.
2. Run `python scripts/check-pre-merge-readiness.py --mode spot` and the focused commands it reports.
3. Stage every intended repository file; leave no unstaged or untracked files.
4. Review the complete staged diff for security. Any finding stops the flow:
   notify the repository owner, fix every finding, and repeat the review.
5. With zero findings, run `python scripts/security-review-gate.py --record-clean`.
   Large, binary, and security-sensitive changes receive an exact staged-tree
   receipt under `.git`; the pre-commit hook fails closed if it is missing or stale.
6. Run Full without `-NoReceipt`. Schema-v3 records the exact staged index tree.
7. Run the readiness command with `--mode commit`, then commit without editing that content. Pre-push sees the identical `HEAD` tree and skips a duplicate Full run.
8. Push, open the PR, and monitor the nine required checks.
9. Fix only evidence-backed failures. A new content tree requires new security-review and Full receipts and a new hosted run.

The readiness command uses only the local Git object database and working tree;
it does not fetch, push, contact GitHub, or trust a stale receipt. A branch that
is behind or divergent from the locally recorded `origin/main` fails with an
actionable state name. Fetch deliberately and rerun instead of allowing the
check to make an undisclosed network change.

Wiki CI retries a bounded number of times and fast-forwards its disposable clone between attempts. This absorbs short cross-repository propagation races; it does not permit persistent wiki drift.
