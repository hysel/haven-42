# Local Data Lifecycle

Haven 42 separates product-owned engine files from user-owned configuration, models, artifacts, and logs. Uninstall may remove the selected engine version and session temporary files; it does not remove user configuration, models, provider data, or generated artifacts by default.

Raw prompts, raw responses, endpoints, and secrets are not persisted by default. Credentials, if a future provider needs them, belong in the operating system credential store rather than repository or configuration files. Logs are local, bounded, and sanitized.
The local-web application holds its provider endpoint, discovered model names, per-capability model choices, request token, cleanup preference, and current chat, writing, or summarization task in process and browser memory only. Changing modes clears the visible task; New task also unloads the active model. Closing the process discards all runtime state and triggers cleanup. Browser assets and API responses use `Cache-Control: no-store`; the application adds no service worker, local storage, cookies, analytics, or crash upload.


Deletion is always previewed and scoped by data class. Cleanup after a test or failed operation may remove only data created by that run. Preexisting models and provider-owned data require explicit provider-specific confirmation. The result must say what was removed and whether recovery is possible.

Export is opt-in. It includes a manifest and integrity hashes, excludes secrets, and sanitizes machine-specific paths by default. The normative rules are in `config/local-data-lifecycle-contract.json`.
