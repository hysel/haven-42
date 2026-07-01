---
name: General Engineering Standards
---

## Scope

Apply these standards to all engineering, review, documentation, and planning work.

## Required Practices

- Understand the existing repository before proposing or making changes.
- Preserve existing style, naming, organization, and framework choices unless there is a clear reason to change them.
- Keep changes small, cohesive, and tied to the stated objective.
- Prefer explicit behavior over hidden conventions.
- Identify assumptions, uncertainty, and tradeoffs.
- Explain material risks before recommending risky changes.
- Do not introduce secrets, credentials, tokens, private keys, or environment-specific confidential values.
- Treat generated code and analysis as requiring human review.

## Avoid

- Broad rewrites that are not required by the task.
- Speculative abstractions.
- Mixing unrelated concerns in one change.
- Claiming validation was performed when it was not.
- Hiding known limitations.

## Review Checklist

- Is the recommendation tied to repository evidence?
- Is the smallest useful change being suggested?
- Are risks and tradeoffs visible?
- Are follow-up tasks separated from required work?
