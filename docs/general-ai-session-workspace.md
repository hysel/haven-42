# General AI Session Workspace

The first-run session command works without a repository, model, or provider. It shows the deterministic capability menu, routes a user goal, discloses availability and material effects, and plans a local artifact workspace. It never invokes the selected capability.

Windows:

```powershell
.\scripts\start-ai-session.ps1 -List
.\scripts\start-ai-session.ps1 -Text "summarize a document" -AsJson
.\scripts\start-ai-session.ps1 -CapabilityId "general.chat" -SessionId "my-session" -Apply -AsJson
```

Linux and macOS:

```bash
./scripts/start-ai-session.linux.sh --list
./scripts/start-ai-session.linux.sh --text "summarize a document" --json
./scripts/start-ai-session.linux.sh --capability-id general.chat --session-id my-session --apply --json
```

Use the `.macos.sh` entry point on macOS.

## Safe Defaults

- Without `-Apply` or `--apply`, the command is a dry-run plan and writes nothing.
- The default workspace is under the operating system's temporary directory, outside any repository.
- A custom workspace inside this pack repository is rejected.
- Session IDs accept only bounded filename-safe characters.
- Existing session directories are never overwritten.
- `session.json` records capability and contract IDs but not the user's prompt, endpoint, credentials, repository contents, or provider output.
- `artifacts/` starts empty. A later provider must disclose the exact artifact path and pass policy checks before writing.
- Ambiguous or unmatched intent does not create a workspace.

Creating a workspace is not permission to execute a provider, read a repository, call a network, or write a result artifact. Those effects remain separately gated.
