# Set Up Local Images

_Image support is still in development and works only with tested profiles._

Haven 42 can use a tested local image provider without sending the prompt to a
Haven 42 cloud service. The current path uses a separately managed Linux
ComfyUI/SDXL provider over loopback, so the connection stays on the same
computer.

## Check availability

1. Open **Images**.
2. Review the detected platform and provider status.
3. Continue only when Haven 42 identifies a tested profile or an existing
   provider that matches the tested setup.

An unavailable or unverified result is not an error. It means that setup does
not yet have enough evidence for Haven 42 to activate image generation.

## Connect an existing provider

Use the existing-provider path only for a ComfyUI service you manage. The
tested profile binds to loopback, uses the expected workflow and checkpoint,
and rejects redirects, public exposure, arbitrary custom nodes, and external
API nodes.

Review the endpoint, model, storage, retention, and provider-side output
behavior before generating an image. Haven 42 returns the resulting PNG to
browser memory, but the separately operated provider may keep its own output.

## Generate an image

1. Enter a prompt.
2. Review the selected provider and retention disclosure.
3. Submit the request.
4. Review or download the returned PNG.
5. Stop or clean up the provider according to its own documented controls when
   testing is finished.

## What Haven 42 does not do

Haven 42 does not silently install ComfyUI, download checkpoints, enable custom
nodes, modify a firewall, expose a public listener, or promote an unvalidated
hardware profile. Installer and lifecycle work remains simulation-only until
its separate security gates are complete.

For exact provider configuration, use [[ComfyUI Image Provider Setup|Eng-ComfyUI-Image-Provider-Setup]].
For engineering admission and lifecycle details, use
[[Image Provider Admission|Eng-Image-Provider-Admission]].
