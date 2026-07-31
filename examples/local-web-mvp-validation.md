# Local Web MVP Validation

## Validation Cell

| Field | Value |
| --- | --- |
| Date | 2026-07-23 |
| Application host | Windows x64 workstation |
| Provider | User-controlled trusted-LAN Ollama |
| Model | `qwen3.5:9b` |
| Capabilities | `general.chat`, `content.write`, `content.summarize` |
| Repository access | None |
| Application persistence | None |

The provider address, machine identity, prompt response, and hardware details were not recorded. This cell did not pull, delete, update, or reconfigure a model.

## Results

| Check | Result |
| --- | --- |
| Local server bound to loopback | Pass |
| Bundled browser page rendered in headless Chromium | Pass |
| Session bootstrap and request token | Pass |
| Trusted-LAN endpoint validation | Pass |
| Connection scope inferred without a user selector | Pass; private LAN |
| Ollama connection and version discovery | Pass |
| Installed-model discovery | Pass |
| Explicit model selection | Pass |
| Bounded chat returned non-empty content | Pass |
| Bounded writing returned a typed Markdown document | Pass |
| Bounded summarization returned a typed Markdown document | Pass |
| All response content excluded from validation output | Pass |
| Balanced model remained warm across active text capabilities | Pass |
| Explicit New task model cleanup | Pass |
| Application-reported model unload | Pass |
| Independent process-list cleanup after explicit/final cleanup | Pass; empty |

The offline integration suite separately covers Host, Origin, token, automatic local/LAN classification, public/unsafe endpoint rejection, unsafe discovered-model filtering, hostile recommendation-catalog rejection, remote assets, five truthful capability states, read-only health/evidence status, CSRF-protected readiness scans, exact in-memory snapshot binding, forged-hardware rejection, disabled setup planning, installed/uninstalled model labeling, capability-specific reset and ranking, per-capability model guidance, explicit model-switch confirmation, visible immediate and idle cleanup policies, compact provider-control contracts, stale-timer rejection, explicit cleanup, one bounded continuous conversation across all three admitted text capabilities, inert text/PNG attachment validation and provider disclosure, typed artifacts and events, unsupported-capability rejection, failed-reconnect authority clearing, provider/empty-response cleanup, accessibility contracts, and loopback-binding boundaries.

The dependency-free headless Chromium flow now contains 329 checks against an isolated loopback fake provider. It verifies dialog and step semantics, secure-bootstrap focus, the Guided read-only scan and disabled plan, the dedicated committed-evidence section, outcome totals, surface activity counts, no-live-validation disclosure, and fixed explicit-click wiki destination, return navigation, provider-step focus, exact wizard/workspace provider-control sizing and typography, capability-specific model readiness, visible-control focus trapping, unified chat handoff with no destructive text-mode tabs, continuous bounded messages across chat/writing/summarization requests, no-send model-switch disclosure, both keep-current and explicit-switch decisions, the native keyboard-operable attachment button, connected picker lifecycle and pointer state, task-time picker and screenshot-limit locking/restoration, advanced-only handling for an unknown installed model, installed/candidate labeling, capability reset and relevance ranking, visible cleanup-policy application, safe Markdown, composer-local bounded prompt recall, bounded session-only chat text sizing with visible scale and invalid-value rejection, bounded atomic mixed text/CSV/JSON/source-code/PNG selection through one type-restricted picker, structured-text syntax rejection, inert source-code preview, explicit shell/PowerShell rejection, attachment errors routed to an accessible compact alert inside Chat, screenshot default/maximum/unsafe-lowering controls, count, combined-pixel and duplicate rejection, one unified message composer containing the height-capped attachment toolbar, compact file chips, screenshot rows, prompt, errors, and Send control, synthetic clipboard-PNG paste, warned submit-confirmed private-network transfer, and typed no-file-written result rendering. It makes no request to a real model server and downloads no browser or test dependency. Full validation runs the source flow on Windows, Linux, and macOS, and the same flow targets each native packaged executable in the packaging matrix.

For a local user review, run
`python scripts/create-source-attachment-review-fixtures.py`. The generator
creates sanitized admitted `.py`/`.tsx` examples, inert intentionally blocked
`.sh`/`.ps1` examples, and a review checklist under
`dist/local-review/source-attachment-ui`. It refuses to overwrite the known
files unless `--force` is supplied. Its automated test creates the same set in
an isolated temporary directory, verifies the bounded UTF-8 contents and
overwrite behavior, and leaves no repository artifact.

## Unified Conversation User Review

A Windows source-runtime/default-browser review confirmed that ordinary chat,
writing, and summarization requests remained visible in one continuous
conversation. The reviewer configured a different installed task model and
confirmed both **Keep current model** and **Switch model** paths worked without
clearing the conversation or sending before the decision. The review used only
memory-held configuration and messages. Secure application shutdown then
reported both shutdown acceptance and verified model cleanup, and the loopback
listener stopped. Endpoint and host details are intentionally omitted.

This is user-interface acceptance evidence, not comparative model-quality,
cross-platform clipboard, packaged-native, or production-release evidence.

## Native Windows Clipboard Screenshot Cell

| Field | Value |
| --- | --- |
| Date | 2026-07-25 |
| Application host | Windows x64 workstation |
| UI | Source local-web application in the user’s default browser |
| Provider | User-controlled trusted-LAN Ollama |
| Model | Installed `qwen3.5:9b`; Ollama declared `vision` capability |
| Screenshot content retained | No |
| Endpoint or machine identity retained | No |

The user created a native Windows screenshot, pasted it into the Haven 42 page,
and confirmed that the bounded screenshot preview appeared correctly. The user
then sent the screenshot through the warned private-network flow and judged the
model’s description acceptable. No model was downloaded or changed. After the
review, an independent Ollama process-list check identified the tested model,
an exact unload request was issued, and a second process-list check verified
that `qwen3.5:9b` was no longer resident.

This is one source-runtime Windows/default-browser/user-review cell. It does not
claim packaged-executable parity, another Windows browser, Linux or macOS native
clipboard behavior, broad vision quality, OCR accuracy, or promotion of a
vision-model recommendation. The screenshot, response, private endpoint,
browser identity, hardware identity, and machine-local paths are intentionally
excluded.

## Native Ubuntu Attachment And Clipboard Cell

| Field | Value |
| --- | --- |
| Date | 2026-07-30 |
| Application host | Ubuntu x86_64 desktop VM in a real graphical session |
| UI | Source and unsigned PyInstaller one-folder package in default Firefox |
| Source commit | `515379a05d549d1a76b3c30b3e6cd15580d9827e` |
| Hosted artifact | `haven42-Linux-X64-unsigned-development` from run `30482923868` |
| Provider use | Version/connection setup only; no prompt or attachment sent |
| Clipboard content retained | No |
| Endpoint or machine identity retained | No |

The user confirmed automatic Firefox launch, loopback serving, the
private-network HTTP warning, and native clipboard screenshot admission through
the PNG path in both source and the exact post-merge unsigned Linux package.
The same review passed mixed `.txt`/`.md`/`.csv`/`.json`/PNG browsing, inert
previews without local paths, the two-screenshot default, the advanced
four-screenshot limit, atomic rejection of excess items and unsafe limit
lowering, compact composer-preserving layout, individual removal, clear-all,
New-task cleanup, normal shutdown, and loopback port release. The artifact
checksums and repository artifact verifier passed before extraction.

No chat Send action occurred, no selected content crossed to the provider, and
Haven 42 did not intentionally load a model. This is one physical Ubuntu
desktop/default-Firefox source-and-package cell. It does not claim physical
macOS clipboard behavior, another Linux browser or distribution, broad vision
quality, persistence, signing, installer behavior, or production readiness.
Screenshots, selected file contents, private endpoints, usernames, local paths,
and machine identifiers are intentionally excluded.

## Evidence Boundary

This promotes only the local-web text slice: sanitized status, explicit Ollama connection, installed-model selection, repository-free chat, writing, and summarization. It does not promote software workflows, image generation, persistence, remote browser access, model downloads, automatic updates, multi-user operation, native packaging, or another provider/model/hardware profile.
