# Compatibility Notes

## Purpose

This document records compatibility expectations for Continue, local models, Ollama, MCP, and SonarQube-related workflows.

## Continue

The pack targets Continue YAML configuration with:

```yaml
schema: v1
```

Compatibility expectations:

- Continue can load `.continue/config.yaml`.
- Local prompts, rules, agents, and templates are referenced by repository-relative paths.
- MCP remains optional and disabled by default.
- MCP workflows require Continue agent mode.

## Editor Surfaces

The pack should work in both VS Code and VSCodium when the Continue extension can load the project-local `.continue/config.yaml`.

Expected differences:

- VS Code usually installs extensions from Microsoft's Marketplace.
- VSCodium usually installs extensions from Open VSX.
- Continue extension versions may differ between the two editors.
- Command palette names and availability may differ by extension version.
- User/global Continue config locations can differ by editor and operating system.
- Marketplace, authentication, telemetry, GitHub, and MCP-related flows may behave differently.

Recommended setup:

- Prefer the project-local `.continue/config.yaml` after installing this pack into a target repository.
- Avoid loading the same rules from both a global Continue config and the project-local `.continue` folder.
- Record the editor name, Continue extension version, operating system, and model when debugging behavior.
- Validate Agent mode and tool execution separately in VS Code and VSCodium when a workflow depends on tools.
- Keep `npx @continuedev/cli --config .continue/config.yaml` as a fallback when editor behavior is unclear.

Known risk:

- Duplicate rule warnings usually mean the same rule files are being loaded from more than one config source.
- Raw JSON tool-call output usually indicates a model/tool-execution mismatch, not a file patch.

## Ollama And Local Models

Default model assumptions:

- Chat/edit/apply/tool workflows: `qwen3-coder:30b`
- Embeddings: `nomic-embed-text`

Expected local setup:

```powershell
ollama pull qwen3-coder:30b
ollama pull nomic-embed-text
```

Tool-use guidance:

- `qwen3-coder:30b` is the current validated default for Agent mode tool execution in the tested VSCodium, Continue, and Ollama setup.
- `qwen2.5-coder:7b` may still be useful as a lightweight chat or planning model, but it produced raw JSON tool-call text instead of executable tool calls in validation.
- When a model prints tool-call JSON instead of executing tools, use the runtime-context fallback workflow in `docs/troubleshooting.md`.
- Use `docs/local-model-selection.md` before changing the committed default model or recommending a different local model tier.

Endpoint guidance:

- Use Continue's default local Ollama behavior for committed config.
- Use custom `apiBase` values only as local machine overrides.
- Do not commit private IP addresses, local hostnames, VPN endpoints, or machine-specific ports.

## MCP

Default configuration:

```yaml
mcpServers: []
```

Compatibility expectations:

- The pack works without MCP.
- Optional MCP setup is documented separately.
- Local `stdio` MCP servers are preferred for first adoption.
- Remote MCP transports require additional security review.
- MCP-derived evidence should be identified separately in review output.

## SonarQube

Supported documentation targets:

- SonarQube Server
- SonarQube Community Build
- SonarQube Cloud

Compatibility expectations:

- Manual SonarQube triage works without API access.
- Web API automation uses environment variables and read-only access.
- SonarQube MCP remains optional until validated.
- SonarQube hostnames, project keys, organization keys, and tokens are not committed.

## Operating System

The pack is documentation and configuration heavy, so it should remain broadly portable.

Validated and documented command examples should include Windows PowerShell plus Linux and macOS shell variants where the commands differ.

When adding commands:

- Prefer cross-platform commands where practical.
- Label shell-specific examples.
- Avoid paths that depend on one user's home directory.

### Linux Distribution Assumptions

The Linux shell wrappers are intended to work on mainstream Linux distributions when these basics are available:

- `bash`
- standard POSIX-style shell utilities such as `cd`, `dirname`, `cat`, and `command`
- Bash-compatible shell execution

The Linux and macOS validation, test, install, runtime-context, and runtime-validation scripts are native Bash scripts. They do not require PowerShell on Linux and macOS systems.

The Linux hardware profile script is best effort and depends more heavily on local packages, drivers, and hardware:

- NVIDIA GPU details require `nvidia-smi`.
- AMD GPU details use `rocm-smi` when available.
- PCI fallback details use `lspci` when available.
- OS details usually come from `/etc/os-release` when present.
- ARM and Jetson-style systems may require additional detection logic.

Minimal distributions, containers, embedded devices, and locked-down servers may not include every optional detection command. In those cases, the script should still provide partial output and users should treat model recommendations as conservative starting points.

The Linux hardware profile reports platform notes when optional GPU detection tools are missing or when available tools do not find a GPU. Those notes are caution signals for driver, container, permission, or cloud image setup; they do not automatically mean the machine has no usable acceleration.

### Enterprise And Cloud Linux

Enterprise and cloud Linux images should be treated as supported targets when they provide `bash` and standard shell utilities.

Expected compatible families include:

- Ubuntu LTS and Debian-based images
- RHEL-family images such as Red Hat Enterprise Linux, Rocky Linux, AlmaLinux, Oracle Linux, and Fedora
- SUSE and openSUSE images
- Amazon Linux 2023
- Azure Linux or CBL-Mariner style images when Bash and standard shell utilities are available
- Google Cloud images based on Debian, Ubuntu, or RHEL-family distributions

Cloud and enterprise caveats:

- Minimal images may omit optional utilities such as `lspci`.
- GPU instances need vendor drivers before `nvidia-smi` or `rocm-smi` can report useful data.
- Hardened images may restrict package installation, shell execution, or PowerShell execution.
- Containers may hide host CPU, GPU, RAM, and driver details unless hardware is passed through.
- ARM cloud instances should be treated conservatively until model and tool execution are validated.

The support goal is portable setup, validation, and installation. Hardware profiling remains best effort because cloud images vary by provider, instance type, driver state, and hardening policy.

### Containers And LXC

Containers, LXC, and LXD environments need extra care because the visible hardware may not match the host machine.

Considerations:

- CPU, RAM, GPU, driver, and PCI information may reflect the container view rather than the physical host.
- GPU access usually requires explicit passthrough.
- NVIDIA container workloads commonly require NVIDIA Container Toolkit or equivalent runtime configuration.
- AMD ROCm container workloads require ROCm device access, permissions, and compatible host drivers.
- LXC and LXD may require explicit device passthrough for GPU devices such as `/dev/dri`, NVIDIA devices, or ROCm devices.
- Unprivileged containers may hide hardware details or block device access.
- `nvidia-smi`, `rocm-smi`, `lspci`, and `/proc/meminfo` may be unavailable or incomplete inside containers.
- Ollama may run on the host while Continue or validation scripts run inside a container; keep any host endpoint override local-only and out of committed config.
- File paths can differ when Continue runs on the host but tools or scripts run inside a container.

Treat hardware profile output from containers as container-visible capacity, not guaranteed host capacity. Use conservative model recommendations until GPU passthrough, memory limits, Ollama reachability, and tool execution are validated in the exact container setup.

## Line Endings

Git may report LF-to-CRLF normalization warnings on Windows.

These warnings do not automatically indicate a content problem, but contributors should avoid unrelated line-ending churn when editing files.

## Validation Checklist

- [ ] Continue loads `.continue/config.yaml`.
- [ ] VS Code or VSCodium is using the intended project-local config.
- [ ] Required prompt, rule, agent, and template files exist.
- [ ] Local Ollama models are available or documented as setup prerequisites.
- [ ] No committed machine-specific endpoint values are present.
- [ ] MCP remains disabled unless explicitly configured by the user.
- [ ] SonarQube guidance avoids committed secrets and private identifiers.
