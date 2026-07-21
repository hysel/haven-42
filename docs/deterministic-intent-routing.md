# Deterministic Intent Routing

The capability resolver selects a capability from explicit IDs or conservative registry phrases and keywords. It does not call an LLM, provider, model server, workflow, or repository.

Windows:

```powershell
.\scripts\resolve-capability.ps1 -Text "help me review code" -AsJson
.\scripts\resolve-capability.ps1 -CapabilityId "general.chat" -AsJson
.\scripts\resolve-capability.ps1 -List -AsJson
```

Linux:

```bash
./scripts/resolve-capability.linux.sh --text "help me review code" --json
./scripts/resolve-capability.linux.sh --capability-id general.chat --json
./scripts/resolve-capability.linux.sh --list --json
```

macOS uses `scripts/resolve-capability.macos.sh` with the same native arguments.

## Routing Rules

1. An exact capability ID wins.
2. Registered multi-word phrases score above individual keywords.
3. A unique highest score selects one capability.
4. A tied highest score returns `needs-clarification` with candidates.
5. No match returns `unmatched` so the caller can show the deterministic menu or ask a bounded question.

Every routing result returns `InvocationAllowed: false`. A later orchestration layer must independently resolve availability, provider configuration, policy, filesystem scope, network effects, artifact location, and approvals.

An optional future LLM router may suggest capability IDs or clarification questions, but its result must pass this same registry and policy boundary. It cannot create capabilities, promote availability, or authorize execution.
