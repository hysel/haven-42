# SonarQube Findings Fixture

## Purpose

Use this sanitized fixture to test SonarQube review prompts and examples without exposing real project data.

## Input

Project: `sample-order-service`
Branch or PR: `feature/order-validation`
Quality Gate: Failed
Analysis Date: `2026-07-02`

Measures:

- Bugs: 1
- Vulnerabilities: 1
- Security Hotspots: 1
- Code Smells: 4
- Coverage: 72.4%
- Duplicated Lines: 1.8%

Findings:

- Severity: Blocker
  Type: Vulnerability
  Rule: `csharpsquid:S4792`
  File: `src/Api/Controllers/AuthController.cs`
  Line: 88
  Message: Sensitive token value may be written to logs.
  Status: Open
  Assignee: Unassigned
  Relevant Code: The log statement includes a request token property.

- Severity: Major
  Type: Code Smell
  Rule: `csharpsquid:S3776`
  File: `src/Application/Orders/OrderWorkflow.cs`
  Line: 142
  Message: Method has high cognitive complexity.
  Status: Open
  Assignee: Unassigned
  Relevant Code: The method combines validation, transition, notification, and persistence logic.

- Severity: Major
  Type: Bug
  Rule: `csharpsquid:S2259`
  File: `src/Infrastructure/Customers/CustomerClient.cs`
  Line: 51
  Message: Possible null reference dereference.
  Status: Open
  Assignee: Unassigned
  Relevant Code: The response object is dereferenced after a remote call.

## Expected Review Behavior

- Classify the token logging issue as a likely release blocker.
- Classify the complexity issue as fix now or defer depending on current change scope.
- Ask for more context before confirming the null-reference finding.
- Recommend rerunning SonarQube after remediation.
