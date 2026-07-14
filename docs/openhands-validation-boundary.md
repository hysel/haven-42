# OpenHands Validation Boundary

OpenHands is a platform-style agent. It is not treated as a simple local editor extension or CLI wrapper, so this pack must not generate an OpenHands install or configuration bundle yet.

## Allowed Validation Scope

Initial OpenHands validation may use only a disposable generated repository and a dedicated, isolated workspace. The test must use a read-only task first. A write-smoke task may follow only after the read-only result is recorded and the user approves the write.

The workspace must mount only the generated repository. It must not mount the user profile, SSH keys, cloud credentials, package-manager credentials, private source repositories, or unrelated host directories.

The validation environment must deny host shell escalation, privileged containers, Docker socket access, and unrestricted network access. A local Ollama endpoint may be allowlisted only when it contains no credentials and is reachable from the isolated environment.

## Required Evidence

Before OpenHands can move from `candidate` to `read-only validated`, record sanitized evidence of the platform version, operating system, model identifier, sandbox policy, mounted workspace scope, task text, changed-file result, and external verification commands.

Before any approved-write claim, the agent must pass read-only, plan, minimal write-smoke, and scoped-edit validation in the isolated workspace. Verify every result outside OpenHands with `git status --short`, `git diff --check`, direct file reads, and the generated sample's relevant test command.

## Explicitly Blocked

Do not use a real repository, a repository containing secrets, a host-wide workspace, interactive cloud credentials, browser session tokens, or a model endpoint that requires embedded credentials. Do not enable autonomous commits, pulls, pushes, package installation, or network egress as part of the first validation.

## Promotion Rule

This boundary only permits future generated-sample validation. It does not make OpenHands install, configuration, test, or approved-write support available. Those statuses may change only after repeatable evidence is added to the evidence catalog and the promotion gates are satisfied.