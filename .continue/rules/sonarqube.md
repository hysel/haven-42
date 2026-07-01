---
name: SonarQube Review
---

## Scope

Apply these standards when incorporating SonarQube findings into engineering review.

## Required Practices

- Treat SonarQube as a signal, not as a substitute for engineering judgment.
- Prioritize security vulnerabilities, correctness bugs, and maintainability issues that affect active code paths.
- Confirm whether a finding is true positive, false positive, accepted risk, or needs more context.
- Classify findings as release blocker, fix now, defer, false positive, accepted risk, or needs more context.
- Prefer fixes that improve design rather than suppressing warnings.
- Document suppressions with a clear reason when suppression is justified.
- Keep quality gate failures visible in review output.

## Avoid

- Mechanical changes that satisfy a rule while reducing clarity.
- Blanket suppressions.
- Ignoring new critical or blocker findings.
- Treating coverage percentage as the only quality measure.

## Review Checklist

- Which findings are release-blocking?
- Which findings are design symptoms?
- Which findings can be deferred safely?
- Which findings require more source context before classification?
- Which suppressions or accepted risks need an owner and review date?
