# Provider Endpoint Security

Haven 42 treats every model or media endpoint as a network trust boundary, even when the service is privately operated. Provider adapters enforce these rules before live network access.

## Trust scopes

- `loopback` is the default and accepts only explicit loopback IP literals.
- `trusted-lan` must be selected explicitly for a private-network server. The endpoint must use an explicit private or loopback IP literal. This scope does not mean “same machine,” and output reports it honestly as network execution.
- `external` requires HTTPS and an explicit public IP literal. Credentials in URLs, fragments, queries, redirects, link-local, multicast, and unspecified addresses are rejected. Hostnames are denied to prevent time-of-check/time-of-use DNS rebinding until a pinned-resolution transport is admitted.

For the private Ollama server used during project validation, add `-EndpointTrustScope trusted-lan` on PowerShell or `--endpoint-trust-scope trusted-lan` on Linux/macOS. Never commit its address.

## Data and file controls

Text JSON responses are limited to 8 MiB and image payloads to 64 MiB by default. Redirects are disabled. JSON roots and image signatures are validated before use. Artifacts use exclusive creation, refuse symlinks/reparse points, receive restrictive file permissions where supported, and are never silently overwritten.

Prompts should use standard input or a prompt file so private text does not appear in child-process command lines. The compatibility `--prompt` argument remains available for direct interactive use but should not be used for sensitive content.

## Security invariants

- A fixture never proves that a live endpoint is trusted.
- Advanced settings can narrow an admitted scope, but cannot bypass endpoint validation or response limits.
- Provider URLs, prompts, credentials, private paths, and raw responses do not belong in committed evidence.
- A DNS or address classification failure denies the request.
