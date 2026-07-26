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

The dependency-free headless Chromium flow now contains 237 checks against an isolated loopback fake provider. It verifies dialog and step semantics, secure-bootstrap focus, the Guided read-only scan and disabled plan, return navigation, provider-step focus, exact wizard/workspace provider-control sizing and typography, capability-specific model readiness, visible-control focus trapping, unified chat handoff with no destructive text-mode tabs, continuous bounded messages across chat/writing/summarization requests, no-send model-switch disclosure, both keep-current and explicit-switch decisions, the native keyboard-operable attachment button, connected picker lifecycle and pointer state, task-time picker locking and restoration, advanced-only handling for an unknown installed model, installed/candidate labeling, capability reset and relevance ranking, visible cleanup-policy application, safe Markdown, prompt recall, bounded atomic mixed text/PNG selection through one type-restricted picker, count and duplicate rejection, compact scroll-contained attachment layout that keeps the composer inside the chat panel, synthetic clipboard-PNG paste, warned submit-confirmed private-network transfer, and typed no-file-written result rendering. It makes no request to a real model server and downloads no browser or test dependency. The same flow can target the native packaged executable in each packaging job.

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

## Evidence Boundary

This promotes only the local-web text slice: sanitized status, explicit Ollama connection, installed-model selection, repository-free chat, writing, and summarization. It does not promote software workflows, image generation, persistence, remote browser access, model downloads, automatic updates, multi-user operation, native packaging, or another provider/model/hardware profile.
