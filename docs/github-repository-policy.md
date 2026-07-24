# GitHub Repository Policy

`config/github-repository-policy.json` is the reviewable source of truth for Haven 42 repository governance. `scripts/verify-github-repository-policy.py` checks committed workflow structure offline; `--live` additionally compares the authoritative GitHub repository settings through GitHub CLI.

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

The three package jobs live in `Validate Pack` beside repository validation so one exact-SHA workflow and the existing hosted verifier cover the complete cross-platform gate. CodeQL remains a separate least-privilege security workflow.

## Merge And Branch Rules

`main` requires linear history, successful strict status checks, conversation resolution, administrator enforcement, and stale-review dismissal. Force pushes and deletion are disabled. Merge commits are disabled at repository level because they conflict with linear history; squash and rebase remain available, and merged branches are deleted automatically.

The repository currently has one eligible CODEOWNER. GitHub does not allow an author to approve their own pull request, so a mandatory approval would block solo maintenance without adding independent review. Required approval count and CODEOWNER review therefore remain zero; all security-sensitive files stay mapped in CODEOWNERS, and independent review is required when another eligible maintainer is available.

## Actions Rules

Actions receive read-only default workflow permission and cannot approve pull requests. Only GitHub-owned actions are admitted, and GitHub enforces full-length commit-SHA pinning. Workflows independently declare minimum permissions and disable persisted checkout credentials.

## Efficient Local-to-Hosted Flow

1. Make the complete change and synchronize the wiki before opening the PR.
2. Stage every intended repository file; leave no unstaged or untracked files.
3. Run Full without `-NoReceipt`. Schema-v3 records the exact staged index tree.
4. Commit without editing that content. Pre-push sees the identical `HEAD` tree and skips a duplicate Full run.
5. Push, open the PR, and monitor the nine required checks.
6. Fix only evidence-backed failures. A new content tree requires a new Full receipt and hosted run.

Wiki CI retries a bounded number of times and fast-forwards its disposable clone between attempts. This absorbs short cross-repository propagation races; it does not permit persistent wiki drift.
