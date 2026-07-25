# Local Data Lifecycle

Haven 42 separates product-owned engine files from user-owned configuration, models, artifacts, and logs. Uninstall may remove the selected engine version and session temporary files; it does not remove user configuration, models, provider data, or generated artifacts by default.

Raw prompts, raw responses, endpoints, and secrets are not persisted by default. Credentials, if a future provider needs them, belong in the operating system credential store rather than repository or configuration files. Logs are local, bounded, and sanitized.
The local-web application holds its readiness snapshot, zero-effect setup plan, provider endpoint, discovered model names, per-capability model choices, request token, cleanup preference, prompt-recall limit, bounded prompt-recall entries, and current chat, writing, or summarization task in process and browser memory only. Prompt recall defaults to 20 entries and may be changed to 50 or 100 for the current process; consecutive duplicates are suppressed. Changing modes or providers and New task clear the visible task and prompt recall; New task also unloads the active model. Closing the process discards all runtime state and triggers cleanup. A readiness snapshot expires for planning and is never written automatically. Browser assets and API responses use `Cache-Control: no-store`; the application adds no service worker, local storage, session storage, IndexedDB, cookies, analytics, or crash upload.


Deletion is always previewed and scoped by data class. Cleanup after a test or failed operation may remove only data created by that run. Preexisting models and provider-owned data require explicit provider-specific confirmation. The result must say what was removed and whether recovery is possible.

Export is opt-in. It includes a manifest and integrity hashes, excludes secrets, and sanitizes machine-specific paths by default. The normative rules are in `config/local-data-lifecycle-contract.json`.
