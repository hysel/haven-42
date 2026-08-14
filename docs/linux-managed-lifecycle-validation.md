# Linux managed local-AI lifecycle validation

_Last reviewed: August 13, 2026._

This record covers a source candidate for Haven 42 `0.4.0-alpha.2`. It is not
evidence for the published Alpha 1 package, and it does not claim that an Alpha
2 archive has passed the same flow.

The validation used the exact managed Ollama `0.32.5` runtime and the exact
Qwen 3.5 0.8B Q8 model selected by the Alpha 2 setup policy. Each operating
system was tested independently with an NVIDIA Quadro RTX 5000 through CUDA.

## What passed

Every row below passed:

- fresh marker-owned setup;
- exact runtime and model identity checks;
- a private local inference request using the GPU path;
- normal Haven 42 shutdown;
- process-tree and loopback-port closure;
- relaunch without downloading the verified files again; and
- marker-owned uninstall without deleting unrelated files.

Linux Mint also passed recovery from an interrupted, marker-owned setup
transaction. That recovery path was not deliberately induced on the other
distributions, so no recovery result is inherited by them.

| Operating system | Result | Additional boundary |
| --- | --- | --- |
| Ubuntu 26.04 LTS | Passed | Source candidate; packaged desktop flow remains open. |
| Ubuntu 24.04.4 LTS | Passed | Source candidate; packaged desktop flow remains open. |
| Debian 13 | Passed | Source candidate; packaged desktop flow remains open. |
| Linux Mint 22.3 | Passed | Interrupted-setup recovery also passed. |
| Pop!_OS 24.04 LTS | Passed | Includes the corrected system identity path; packaged repetition remains open. |
| Fedora 44 | Passed | Includes the durable completion-receipt ordering correction; packaged repetition remains open. |
| Bazzite 44 | Passed | Cleanup accepted Bazzite's canonical `/var/home` path without broadening deletion scope. |
| CachyOS rolling | Passed | The test launcher explicitly used Bash because the login shell was Fish. |
| Arch Linux rolling | Passed | The test launcher explicitly used Bash because the login shell was Fish. |

## Evidence handling

The native result files retain only the application version, backend, runtime
version, model identifier, stable check outcomes, and privacy flags. They
contain no prompt or response text, account name, hostname, address, key, VM
number, PCI address, or personal path. Private controller logs and deployment
details remain outside the repository.

Each row has a separate entry in `config/evidence-catalog.tsv`. The generated
`config/evidence-page-registry.json` preserves the operating-system boundary
for future compatibility checks. Those records are advisory inputs only: they
cannot install an update, change a model default, or promote a support label.

## What remains open

A fresh Linux Alpha 2 package must repeat this lifecycle on the intended
promotion profiles. Guided desktop setup, accessibility, cancellation during
active inference, attachment handling, support-report export, and a sustained
soak remain separate gates. Results from the Quadro RTX 5000 do not transfer
to another GPU, driver, runtime version, model, or operating system.
