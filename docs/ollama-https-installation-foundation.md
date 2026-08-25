# Ollama HTTPS installation foundation

Haven 42 does not currently install Ollama, a TLS gateway, or certificates.
This page records the requirements for a future installer. It does not modify
the machine.

Ollama exposes its API over HTTP and documents using a proxy when the service
must be reachable beyond its host. Setting an `https://` `OLLAMA_HOST` value
does not configure a certificate. The future private-network topology is:

```text
Haven 42 client -- HTTPS + authentication --> TLS gateway
                                              |
                                              +-- HTTP loopback --> Ollama
```

Ollama remains bound to `127.0.0.1`; only the reviewed gateway may listen on a
selected private interface. Same-device Haven 42 continues to use HTTP
loopback and does not need a certificate. Public exposure is not supported.
The gateway denies every route except the exact discovery, inference,
residency, and cleanup paths Haven 42 uses. It requires a generated Bearer or
X-API-Key credential, rate-limits failures, compares credentials in constant
time, strips the credential before forwarding to Ollama, and never logs request
bodies or authorization headers. TLS 1.3 is preferred and TLS 1.2 is the
minimum.

## Locally generated certificate option

The future guided installer must offer a locally generated certificate for
users who do not have an internal PKI. The preferred structure is a private
self-signed root with a leaf certificate; a directly trusted self-signed leaf
may also be supported. Haven 42 connects to IP literals, so the leaf must
contain the exact server IP in its Subject Alternative Name. A Common Name by
itself is insufficient.

The installer must never disable certificate or endpoint verification. It must
show the certificate fingerprint, require explicit trust approval, prefer a
per-user trust location, and request separate approval before any elevated
system trust-store change. Private keys must be non-exportable where the
platform permits, restricted to the owning account or gateway identity, and
never written to the repository, logs, evidence, or network.

Certificate creation, private-key creation, trust installation, listener or
firewall changes, service configuration, and removal are separately disclosed
machine effects. Uninstall and rollback may remove only keys, certificates,
trust entries, and gateway files recorded as owned by that exact transaction.

## Validation gates

Windows, Linux, and macOS are independent evidence cells. Each must cover
clean install, preservation of an existing Ollama setup, exact-IP SAN checks,
trusted handshake, rejection of unknown, expired, and wrong-IP certificates,
authenticated inference, gateway restart, rotation, upgrade rollback, exact
route rejection, authentication rate limiting, credential stripping, exact
uninstall, trust removal, and private-key cleanup. The gateway is separately
acquired and must pass immutable-version, integrity, publisher, license,
package-parity, and zero-finding security review gates.

The authoritative inactive contract is
`config/ollama-https-installation-contract.json`. Ollama's current official
transport guidance is in the [Ollama FAQ](https://docs.ollama.com/faq) and its
[upstream FAQ source](https://github.com/ollama/ollama/blob/main/docs/faq.mdx).
