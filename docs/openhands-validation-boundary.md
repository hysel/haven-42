# OpenHands Validation Boundary

OpenHands is a platform-style agent. It is not treated as a simple local editor extension or CLI wrapper, so this pack must not generate an OpenHands install or configuration bundle yet.

## Allowed Validation Scope

Initial OpenHands validation may use only a disposable generated repository and a dedicated, isolated workspace. The test must use a read-only task first. A write-smoke task may follow only after the read-only result is recorded and the user approves the write.

The workspace must mount only the generated repository. It must not mount the user profile, SSH keys, cloud credentials, package-manager credentials, private source repositories, or unrelated host directories.

The validation environment must deny host shell escalation, privileged containers, Docker socket access, and unrestricted network access. A local Ollama endpoint may be allowlisted only when it contains no credentials and is reachable from the isolated environment.

## Execution Architecture

The first eligible implementation must use a rootless, disposable container or equivalently isolated runtime. Direct host execution, privileged containers, hosted workspaces containing user data, and mounting the Docker socket are unsupported.

The runtime contract must provide:

- One generated repository mounted at one documented workspace path.
- Read-only mounting for the first gate, followed by an explicitly approved repository-only read/write mount for later gates.
- A non-root runtime identity with no host user-profile mapping.
- No inherited environment variables except an explicit allowlist containing non-secret runtime settings.
- Deny-by-default network policy with, at most, one credential-free model endpoint allowlist entry.
- Disposable runtime state destroyed after external evidence is collected.

## Credential Boundary

Do not inject Git credentials, SSH agents, SSH keys, cloud credentials, package-registry tokens, browser cookies, editor sessions, or host keychains. The first adapter must reject credential-bearing model endpoint URLs and must not persist prompts, transcripts, or provider configuration outside ignored local validation output.

## Adapter Contract

Before OpenHands can receive an install, configure, or test entry point, an adapter design must define deterministic `Plan`, isolated `Configure`, `Health`, and generated-sample `Test` behavior. It must expose the runtime image/version, workspace mount mode, network policy, provider endpoint type, intended writes, cleanup result, and external verification result without recording private paths or endpoint values.

## Required Evidence

Before OpenHands can move from `candidate` to `read-only validated`, record sanitized evidence of the platform version, operating system, model identifier, sandbox policy, mounted workspace scope, task text, changed-file result, and external verification commands.

Before any approved-write claim, the agent must pass read-only, plan, minimal write-smoke, and scoped-edit validation in the isolated workspace. Verify every result outside OpenHands with `git status --short`, `git diff --check`, direct file reads, and the generated sample's relevant test command.

## Explicitly Blocked

Do not use a real repository, a repository containing secrets, a host-wide workspace, interactive cloud credentials, browser session tokens, or a model endpoint that requires embedded credentials. Do not enable autonomous commits, pulls, pushes, package installation, or network egress as part of the first validation.

## Promotion Rule

This boundary only permits future generated-sample validation. It does not make OpenHands install, configuration, test, or approved-write support available. Those statuses may change only after repeatable evidence is added to the evidence catalog and the promotion gates are satisfied.

OpenHands remains a candidate and is excluded from the default setup menu. The defined boundary closes the architecture decision; implementation and evidence remain future candidate expansion rather than Milestone 17 or 19 supported-surface completion work.
