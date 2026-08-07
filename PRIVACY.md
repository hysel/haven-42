# Privacy Policy

## Summary

Haven 42 is a local-first application. It contains no telemetry, analytics,
advertising, user account, or background data-collection service. The browser
interface is served only on IPv4 loopback and cannot be opened to a LAN
listener through application settings.

The program will not transfer information to another networked system unless
the user specifically requests or configures that operation.

## Information Kept In Memory

The current admitted browser runtime keeps provider settings, optional
provider API keys,
prompts,
conversation text, selected attachments, model responses, run metrics, and
generated image bytes in process or browser memory. It does not persist them as
Haven 42 configuration or conversation history. Closing Haven 42 clears that
state.

An API key is accepted only through the password field for a fixed Bearer or
X-API-Key mode. It is cleared from the visible field after connection, never
returned by the local API, and never written to Haven 42 configuration,
history, logs, evidence, or browser storage. A separately managed provider or
gateway may record authentication and request metadata under its own policy.

Provider software may have its own retention behavior. Haven 42 discloses known
provider-side image retention before generation and cannot promise deletion
from a separately operated provider.

## Browser Preferences

Haven 42 stores one small, versioned browser preference that records whether
the short help tour for Chat, Models, System, Technical details, and About has
been completed or dismissed. Each value is only `true` or `false`. This keeps a
finished tour from opening automatically on later visits while still allowing
the user to reopen it with the section's **Help** button.

This preference contains no prompt, response, attachment information, model,
provider address, API key, system detail, identity, or usage history. Skipping,
closing, or completing a tour records the same `true` value; partial progress
is not retained.

## User-Requested Network Operations

Network access occurs only for an explicit feature the user activates:

- connecting to a loopback or private-network Ollama endpoint selected by the
  user;
- sending a prompt or deliberately selected text/PNG attachment to that
  provider;
- explicitly searching the fixed public Ollama model catalog;
- connecting to the admitted loopback ComfyUI image provider;
- opening the fixed Haven 42 GitHub wiki link in the default browser; or
- developer and maintainer operations such as GitHub Actions, dependency
  acquisition, or repository synchronization outside the end-user runtime.

Haven 42 does not automatically download models, activate online updates,
submit crash reports, browse arbitrary websites, or send prompts to Haven 42's
maintainers.

## Files And Repositories

The chat attachment surface reads only files or clipboard images the user
explicitly selects within strict type and size limits. It sends no filesystem
path to the model provider. It does not scan folders, watch files, expand
archives, execute attachment content, or write temporary attachment files.

Development-only folder and history validators do not change that product
behavior. Folder validation inspects only an operator-specified test directory
under strict limits and emits metadata without absolute paths or content. The
SQLite validator creates fixed synthetic records only in its own temporary
directory and deletes the database, backup, and sidecars. Neither component is
connected to the browser runtime or included as an active storage feature.

Plan-only software workflows do not read a repository or start a process from
the browser runtime. Separate developer scripts may read a repository only
when their operator explicitly selects and runs them under their documented
scope.

## Installation And Removal

The unsigned development package is portable and has no installer. It does not
request administrator access or add a service, driver, firewall rule, startup
entry, global Python runtime, or automatic updater. To remove it, close Haven
42 and delete the extracted application directory.

Provider software, models, exported downloads, and user-created files are
owned separately and are not removed automatically.

## Security And Public Evidence

Committed evidence is sanitized to exclude private endpoints, user paths,
credentials, prompts, model responses, local identities, and machine-specific
details. Public-history privacy validation runs before push and in GitHub
Actions.

Report a suspected privacy or security issue using the private process in the
[security policy](https://github.com/hysel/haven-42/security/policy). Do not
include credentials, private prompts, or personal files in a public issue.

## Future Features

Persistent conversation storage, online updates, installers, controlled web
research, and additional providers remain separately gated. Before activation,
each feature requires an updated privacy review, explicit user controls,
retention and deletion behavior, security testing, and documentation.
The disabled research query prototype uses injected fixtures only and performs
no network request.
