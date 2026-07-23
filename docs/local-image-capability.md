# Local Image Capability

`comfyui.local-image` provides repository-free `media.image.create` through a user-controlled ComfyUI API. It is dry-run first, session-bound, and writes only after `--execute --apply` or `-Execute -Apply`.

The promoted workflow uses only built-in ComfyUI nodes: checkpoint loader, text encoders, empty latent image, sampler, VAE decode, and PNG save. Custom nodes and external API nodes are outside the validated boundary.

```powershell
.\scripts\start-ai-session.ps1 -CapabilityId media.image.create -WorkspaceRoot <outside-repo-path> -SessionId image -Apply
.\scripts\invoke-local-image-capability.ps1 -Prompt "..." -Model sd_xl_base_1.0.safetensors -SessionPath <session-path> -ComfyUiBaseUrl <runtime-url> -Execute -Apply -AsJson
```

Linux and macOS use the corresponding `.linux.sh` and `.macos.sh` entry points. The endpoint is runtime-only and never returned or persisted. The adapter validates PNG signatures and dimensions, emits an `image` typed artifact, clears ComfyUI history after retrieval, and discloses that ComfyUI retains its generated output on the provider host.

The validated service binds localhost only, is accessed through SSH tunneling, runs as a dedicated non-root account, disables image metadata, custom nodes, and external API nodes, and uses a pinned checkpoint with a verified checksum. Deployments must rediscover these runtime properties rather than inheriting them from evidence.

See [Local Image Capability Validation](../examples/local-image-capability-validation.md).

## Endpoint trust and bounded output

ComfyUI defaults to the `loopback` trust scope. A private LAN ComfyUI host requires explicit `-EndpointTrustScope trusted-lan` or `--endpoint-trust-scope trusted-lan`. Redirects are denied, response JSON is bounded to 8 MiB, images are bounded to 64 MiB, and artifacts are created exclusively without following links. Prefer prompt files or standard input for sensitive prompts. See `docs/provider-endpoint-security.md`.
