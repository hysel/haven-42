# Connection Security

Haven 42 can connect to Ollama here or on another computer you manage. The
address determines which safety rules apply.

## Ollama on this computer

Use `http://127.0.0.1:11434` for a normal Ollama connection on this computer.
`127.0.0.1` is a loopback address, which means the traffic stays on this
computer.

## Ollama on another computer

Use the server's numeric private-network address. Haven 42 warns when the
connection uses unencrypted HTTP because another device on the network could
observe or change that traffic. Use a trusted HTTPS endpoint or a loopback
tunnel when the conversation is sensitive.

The current release blocks public server addresses, credentials in the
address, unsupported hostnames, and unexpected redirects.

## A server that requires an API key

Open **Advanced connection settings** and choose the mode required by the
server:

- **Bearer token** sends an `Authorization` bearer token.
- **X-API-Key** sends an `X-API-Key` value.

Leave **Automatic · Recommended** selected unless your server requires a
specific mode. An authenticated server on another computer must use HTTPS. Haven 42 keeps the key in memory for
the current session, clears the visible field after connection, and does not
write the key to its settings, logs, status, or evidence.

Never put an API key, private server address, prompt, or response in a public
issue.

## What Haven 42 checks

- The address is in the selected same-computer or private-network scope.
- The connection does not inherit an unexpected proxy.
- Redirects cannot move the request to another server.
- Response type and size are bounded before use.
- A failed address, certificate, or response check stops the request.

For protocol rules and future HTTPS-gateway design, see [[Provider Endpoint
Security|Eng-Provider-Endpoint-Security]].
