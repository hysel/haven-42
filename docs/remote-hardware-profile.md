# Remote Hardware Profile

## Purpose

Use this workflow when the editor machine is not the same machine that runs the local LLM server. Common examples are:

- Windows laptop to Linux Ollama server
- Linux workstation to Linux Ollama server
- macOS workstation to Linux Ollama server
- macOS workstation to macOS model host

The remote runner sends the existing local GPU/CPU profile script over SSH and runs it in memory on the remote host. It does not install files on the remote machine. The remote host still needs the normal local prerequisites for useful GPU detection, such as `bash`, optional `nvidia-smi`, optional `rocm-smi`, and optional Ollama.

## What It Collects

The remote profile output uses the same JSON shape as the local profile scripts:

- Platform and operating system summary
- System RAM
- CPU summary and architecture
- GPU names and detected VRAM
- GPU vendor and memory type when available
- Container/LXC notes when detected
- Ollama reachability from the remote host
- Installed Ollama model names from the remote host
- Model recommendation based on the remote host profile

The scripts do not include the SSH target, hostname, IP address, username, local paths, or secrets in the saved JSON report.

## Prerequisites

On the client machine:

- OpenSSH client available as `ssh`
- This pack repository checked out locally
- Key-based SSH recommended. The remote profile scripts run SSH in non-interactive mode by default so they fail clearly instead of hanging on password or host-key prompts. If you use interactive/password SSH, the scripts switch to copy-and-run mode with `scp` so the password prompt can use the console.

On the remote machine:

- SSH access
- Bash
- Optional: Ollama running if you want installed-model detection
- Optional: `nvidia-smi`, `rocm-smi`, or platform GPU tooling for VRAM detection

## SSH Preflight

Before running the remote profile script, verify SSH works by itself:

```powershell
ssh your-user@your-linux-host "echo remote-ok"
```

If this prompts to trust the host key, answer it there first. If it asks for a password, configure key-based SSH for automation or use the script's interactive override for a manual one-off test. Interactive mode uploads the profiler to `/tmp`, runs it, and removes it afterward.

## Windows Client To Linux Host

Run from the root of this pack repository:

```powershell
.\scripts\get-remote-model-profile.ps1 `
  -RemoteHost "your-linux-host" `
  -RemoteUser "your-user" `
  -RemotePlatform Linux `
  -TimeoutSeconds 60 `
  -OutputPath .\runtime-validation-output\remote-model-profile.json
```

With a non-default SSH port or identity file:

```powershell
.\scripts\get-remote-model-profile.ps1 `
  -RemoteHost "your-linux-host" `
  -RemoteUser "your-user" `
  -RemotePort 2222 `
  -IdentityFile "$HOME\.ssh\id_ed25519" `
  -RemotePlatform Linux `
  -TimeoutSeconds 60 `
  -OutputPath .\runtime-validation-output\remote-model-profile.json
```

## Linux Client To Linux Host

```bash
./scripts/get-remote-model-profile.linux.sh \
  --remote-host "your-linux-host" \
  --remote-user "your-user" \
  --remote-platform Linux \
  --timeout-seconds 60 \
  --output-path runtime-validation-output/remote-model-profile.json
```

## macOS Client To Linux Or macOS Host

Linux model host:

```bash
./scripts/get-remote-model-profile.macos.sh \
  --remote-host "your-linux-host" \
  --remote-user "your-user" \
  --remote-platform Linux \
  --timeout-seconds 60 \
  --output-path runtime-validation-output/remote-model-profile.json
```

macOS model host:

```bash
./scripts/get-remote-model-profile.macos.sh \
  --remote-host "your-mac-host" \
  --remote-user "your-user" \
  --remote-platform macOS \
  --timeout-seconds 60 \
  --output-path runtime-validation-output/remote-model-profile.json
```

## Progress Output

The remote profile scripts print numbered progress messages so you can tell where the run is spending time:

- `[1/6]` checks for local SSH tools.
- `[2/6]` confirms whether the Linux or macOS profile helper was selected.
- `[3/6]` prepares the SSH target and port.
- `[4/6]` shows whether the script is using non-interactive SSH streaming or interactive `scp` copy-and-run mode.
- `[5/6]` runs the remote GPU, CPU, VRAM, and Ollama detection.
- `[6/6]` validates the returned JSON and writes the output file.

If the script stops before `[5/6]`, the problem is usually local SSH tooling, host-key trust, credentials, or network access. If it reaches `[5/6]` but fails before `[6/6]`, check the remote host for `bash`, GPU tools, Ollama availability, or permissions.

## Use The Remote Profile For Model Testing

After the remote profile is written, pass it to the model test runner so model pulls are gated by the remote machine's detected VRAM:

Windows:

```powershell
.\scripts\test-local-agent-models.ps1 `
  -OllamaBaseUrl "http://127.0.0.1:11434" `
  -TargetRepo "C:\path\to\sample-repo" `
  -Models "qwen3.5:9b","devstral:24b","qwen3.5:35b" `
  -ModelProfilePath .\runtime-validation-output\remote-model-profile.json `
  -VramSelectionMode TotalDedicated `
  -PullMissing `
  -UnloadAfterEach
```

Linux or macOS:

```bash
./scripts/test-local-agent-models.linux.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "qwen3.5:9b,devstral:24b,qwen3.5:35b" \
  --model-profile-path runtime-validation-output/remote-model-profile.json \
  --vram-selection-mode TotalDedicated \
  --pull-missing \
  --unload-after-each
```

Use the Ollama base URL that is reachable from the machine running the test script. The remote profile describes the model host; it does not change network routing by itself.

## VRAM Selection Mode

`TotalDedicated` is the default. It sums visible dedicated or unknown GPU VRAM from the profile. This is useful for machines where Ollama can use the visible GPU capacity you intend to test.

`MaxDedicated` uses the largest single detected GPU. Use this when you want a conservative estimate or when the model runtime cannot reliably use multiple GPUs together.

Manual `AvailableVramGb` or `--available-vram-gb` still overrides the profile value for controlled tests.

## Troubleshooting

If the script appears stuck or reports that the SSH pipe was closed:

- Stop it with Ctrl+C if it is still running.
- Run the SSH preflight command above and resolve host-key, password, or key-permission prompts there.
- Use `-TimeoutSeconds 30` or `--timeout-seconds 30` while testing.
- Prefer key-based SSH. Non-interactive mode requires a key that works without a password prompt. If you need password SSH for testing, use `-AllowInteractiveSsh` or `--allow-interactive-ssh`; it uses `scp` copy-and-run mode so the password prompt can use the console. This mode requires `scp` and temporarily copies the profiler to the remote host instead of streaming it through SSH stdin.

If SSH works but the profile has no GPU VRAM:

- Confirm the remote host can run `nvidia-smi` or `rocm-smi` directly.
- Confirm the container or LXC environment can see the GPU devices.
- Confirm the SSH user has permission to run the GPU tooling.
- Try `VramSelectionMode MaxDedicated` for conservative tests.

If Ollama is listed as unreachable in the profile:

- Confirm Ollama is running on the remote host.
- Confirm the remote host can run `ollama list`.
- Remember that the profile checks Ollama from the remote host, not from the editor machine.
