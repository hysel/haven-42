# Provider Endpoint Security

Every model or media endpoint is a network trust boundary, even when the service is privately operated. Haven 42's provider adapters enforce these rules before live network access.

## Trust scopes

- `loopback` is the default and accepts only explicit loopback IP literals.
- `trusted-lan` must be selected explicitly for a private-network server. The endpoint must use an explicit private or loopback IP literal. This scope does not mean “same machine,” and output reports it honestly as network execution.
- `external` requires HTTPS and an explicit public IP literal. Credentials in URLs, fragments, queries, redirects, link-local, multicast, and unspecified addresses are rejected. Hostnames are denied to prevent time-of-check/time-of-use DNS rebinding until a pinned-resolution transport is admitted.

For the private Ollama server used during project validation, add `-EndpointTrustScope trusted-lan` on PowerShell or `--endpoint-trust-scope trusted-lan` on Linux/macOS. Never commit its address.

## Authenticated Ollama endpoints

The browser application supports two fixed, opt-in authentication modes for an
existing Ollama endpoint:

- **Bearer token** sends `Authorization: Bearer <key>`.
- **X-API-Key** sends `X-API-Key: <key>`.

The browser defaults to **Automatic (Recommended)**, which
uses the normal unauthenticated Ollama loopback behavior. Bearer and X-API-Key
are advanced choices for endpoints whose operator explicitly requires them.
A future managed HTTPS gateway must select its configured mode during setup so
the end user is not expected to choose a header format.

Haven 42 never accepts a caller-defined header name, credentials in the URL,
or authentication through a query string. The key must be visible ASCII with
no whitespace or control characters and is limited to 4,096 bytes. Redirects
and inherited proxies remain disabled, so the header is sent only to the exact
validated IP-literal endpoint and admitted Ollama paths.

Keys used with a private-network endpoint require HTTPS. HTTP authentication
is admitted only for same-machine loopback because a key sent over private-LAN
HTTP could be observed or changed in transit. The HTTPS server certificate
must be trusted by the operating system and valid for the literal IP address.

The key remains only in browser and Haven service process memory. It is never
returned in status or error responses, logged, committed, written to Haven 42
configuration, or included in evidence. After a successful connection the
password field is cleared; leaving it blank during a same-endpoint settings
change reuses the current in-memory key. Changing the endpoint or
authentication mode requires entering a key again. Closing Haven 42 clears the
session key.

A future managed Ollama setup will not treat an `https://` listener value as
proof that Ollama natively manages TLS. For private-network use, the planned
topology keeps Ollama on HTTP loopback behind a separately reviewed HTTPS
gateway. It supports an explicitly trusted locally generated certificate only
after exact-IP SAN, key protection, trust, rotation, negative-handshake, and
uninstall-cleanup gates pass. See
[Ollama HTTPS installation foundation](https://github.com/hysel/haven-42/blob/main/docs/ollama-https-installation-foundation.md).

## Post-quantum readiness

HTTPS is not currently labeled post-quantum secure. The exact client and
server runtime, negotiated key-establishment group, and certificate signature
must be observed before such a claim. The inactive PQC readiness contract lists
hybrid `X25519MLKEM768` only as a candidate; it does not change TLS policy or
permit silent downgrade. See
[Post-quantum cryptography readiness](https://github.com/hysel/haven-42/blob/main/docs/post-quantum-cryptography-readiness.md).

## Data and file controls

Text JSON responses are limited to 8 MiB and image payloads to 64 MiB by default. Redirects and inherited OS/environment proxies are disabled, so a user-approved IP-literal provider connection cannot be silently routed through an intermediary. JSON roots and image signatures are validated before use. Artifacts use exclusive creation, refuse symlinks/reparse points, receive restrictive file permissions where supported, and are never silently overwritten.

Prompts should use standard input or a prompt file so private text does not appear in child-process command lines. The compatibility `--prompt` argument remains available for direct interactive use but should not be used for sensitive content.

## Security invariants

- A fixture never proves that a live endpoint is trusted.
- Advanced settings can narrow an admitted scope, but cannot bypass endpoint validation or response limits.
- Provider URLs, prompts, credentials, private paths, and raw responses do not belong in committed evidence.
- Authentication headers are fixed by the selected mode and never supplied by a model or arbitrary renderer input.
- A DNS or address classification failure denies the request.
