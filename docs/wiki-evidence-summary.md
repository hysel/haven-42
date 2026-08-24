# Evidence Dashboard

_A readable summary of committed, sanitized test results._

Each result shows what was tested under a recorded configuration. It is not
usage analytics, a quality ranking, or proof that every machine will behave the
same way.

## Portable application

- Source and packaged browser behavior are compared.
- Native development packages are built and smoke-tested on Windows, Linux, and
  macOS GitHub runners.
- Packages are checked for loopback binding, safe browser launch, constrained
  shutdown, hostile resources, relocation, archive integrity, checksums,
  dependency inventory, notices, SBOM, and unsigned provenance.
- Public-history privacy and CodeQL checks run in hosted automation.

## Providers and hardware

Committed results include exact, scope-limited runs involving Ollama text,
ComfyUI/SDXL images, and selected inference engines across NVIDIA, AMD, and
Intel hardware. A hardware result applies only to its recorded operating
system, driver, runtime, model revision, quantization, and operation.

WSL2 AMD/HIP results are tracked separately from native Linux AMD results.
Passing through `/dev/dxg` confirms only the exact Windows-hosted WSL2 profile;
it does not validate a native Linux driver, desktop, package, or lifecycle.

Unverified hardware and provider combinations remain selectable only where the
product explicitly labels them as advanced or unavailable. A test result never
grants permission to install software or modify a machine.

## Security and privacy

- The browser server is IPv4 loopback-only.
- Attachments are bounded, treated as inert data, and never executed.
- Provider endpoints are allowlisted by scope and redirects are blocked.
- Committed evidence excludes private endpoints, user paths, prompts, responses,
  credentials, and local identities.
- These results do not enable signing, notarization, installers, production
  releases, or online updates.

## Read the detailed records

- [[Evidence Record Index|Evidence-Record-Index]]
- [[Engineering Evidence Dashboard|Engineering-Evidence-Dashboard]]
- [[Evidence Catalog|Evidence-Catalog]]
- [[Capability Evidence Contract|Capability-Evidence-Contract]]
- [[Test Tiers|Test-Tiers]]
- [[Hosted CI Verification|Hosted-CI-Verification]]
