# Optional LLM Routing Validation

## Scope

This sanitized record covers one bounded `qwen3.5:9b` structured-output routing request on Windows through a user-controlled local-network Ollama endpoint. The endpoint, routing text, raw response, and local paths are intentionally omitted.

## Result

An unambiguous summarization intent produced the registered `content.summarize` capability ID. Deterministic code reloaded the capability from the committed registry, exposed its configuration-required availability and policy, and kept `InvocationAllowed` false. The output stated that neither the prompt nor endpoint was persisted, and serialized output contained neither value.

Fixture tests also prove dry-run-first behavior and rejection of an invented capability ID. Cross-platform wrappers use native shell/Python command discovery. The model was unloaded after the live request; no model was pulled or deleted.

## Limits

- This is one advisory-routing result for one model and operating system, not broad natural-language classification accuracy.
- The result does not grant capability availability, permission, or workflow execution.
- Deterministic routing remains the default and fallback.
