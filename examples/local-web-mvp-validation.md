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

The offline integration suite separately passed 59 security and behavior checks covering Host, Origin, token, automatic local/LAN classification, public/unsafe endpoint rejection, remote assets, per-capability model selection, model-switch cleanup, immediate and idle cleanup modes, stale-timer rejection, explicit cleanup, all three admitted text capabilities, typed response kinds, single-input enforcement, unsupported-capability rejection, failed-reconnect authority clearing, provider/empty-response cleanup, and loopback-binding boundaries.

## Evidence Boundary

This promotes only the local-web text slice: sanitized status, explicit Ollama connection, installed-model selection, repository-free chat, writing, and summarization. It does not promote software workflows, image generation, persistence, remote browser access, model downloads, automatic updates, multi-user operation, native packaging, or another provider/model/hardware profile.
