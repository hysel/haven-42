# SonarQube Review Workflow

## Purpose

Use this workflow when a team wants Continue to help triage SonarQube findings without integrating directly with the SonarQube API.

This is a manual workflow. Users copy or export findings from SonarQube, paste the relevant context into Continue, and ask for prioritized engineering review.

## When To Use

- A pull request or branch has SonarQube findings.
- A quality gate failed and needs triage.
- A team wants to separate release blockers from cleanup work.
- Findings need engineering judgment before remediation.

## What To Provide

Paste only the information needed for review:

- Project or service name
- Branch or pull request identifier
- Quality gate status
- Finding severity
- Finding type
- Rule key
- File path and line number
- SonarQube message
- Relevant code snippet
- Test coverage context, if available
- Any known false-positive or accepted-risk history

Do not paste secrets, tokens, credentials, customer data, private URLs, or full reports containing sensitive information.

## Suggested Prompt

```text
Use the SonarQube Review rule.

Triage the following SonarQube findings.

For each finding, classify it as:
- Release blocker
- Fix now
- Defer
- False positive
- Accepted risk
- Needs more context

For each finding include:
- Severity
- Evidence
- Impact
- Recommended action
- Test or validation step

Here are the findings:

<paste findings here>
```

## Triage Categories

### Release Blocker

Use when a finding creates likely exploitable security risk, correctness failure, data loss risk, production instability, or a failed quality gate that policy requires before release.

### Fix Now

Use when the finding is valid and should be fixed in the current change, but does not independently block release.

### Defer

Use when the finding is valid but low risk, outside the current change, or better handled in planned cleanup.

### False Positive

Use when the finding does not apply after reviewing code behavior and context.

### Accepted Risk

Use when the finding is valid but intentionally accepted by the team. Accepted risks should include an owner, reason, and review date.

### Needs More Context

Use when the pasted finding lacks enough code, runtime, ownership, or policy context to classify responsibly.

## Review Output

Use this structure:

```text
## Executive Summary

## Quality Gate Impact

## Findings

### Finding 1

- Classification:
- Severity:
- Rule:
- Location:
- Evidence:
- Impact:
- Recommendation:
- Validation:

## Release Recommendation

## Follow-up Work
```

## Validation Guidance

- Verify fixes with relevant unit, integration, or security tests.
- Rerun SonarQube after remediation.
- Document suppressions close to the code or in the review record.
- Avoid suppressing findings only to satisfy the quality gate.

## Limitations

- This workflow does not call SonarQube directly.
- Findings are only as complete as the pasted context.
- Continue output is advisory and requires human review.
- Large reports should be summarized or split by severity to stay within context limits.
