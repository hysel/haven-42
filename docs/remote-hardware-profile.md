# Remote Hardware Profile

## Purpose

Use this workflow when your editor and local LLM server run on different machines. Common examples are:

- Windows laptop to Linux Ollama server
- Linux workstation to Linux Ollama server
- macOS workstation to Linux Ollama server
- macOS workstation to macOS model host

The remote runner sends the existing GPU/CPU profile script over SSH and runs it in memory on the remote host. It does not install files on the remote machine. The remote host still needs the usual tools for useful GPU detection: `bash`, optional `nvidia-smi`, optional `rocm-smi`, and optional Ollama.

## What It Collects

The remote profile uses the same JSON shape as the local scripts:

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
- Key-based SSH is recommended. The scripts use non-interactive SSH by default, so they fail instead of hanging on password or host-key prompts. With interactive/password SSH, they switch to copy-and-run mode with `scp` so the password prompt can use the console.

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

If this asks you to trust the host key, answer it here first. If it asks for a password, configure key-based SSH for automation or use the interactive override for a manual one-off test. Interactive mode uploads the profiler to `/tmp`, runs it, and removes it afterward.

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

After writing the remote profile, pass it to the model test runner so it can compare model requirements with the remote machine's detected VRAM:

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

`TotalDedicated` is the default. It sums visible dedicated or unknown GPU VRAM from the profile. Use it when Ollama can use the visible GPU capacity you intend to test.

`MaxDedicated` uses the largest detected GPU. Use it for a conservative estimate or when the runtime cannot reliably combine multiple GPUs.

Manual `AvailableVramGb` or `--available-vram-gb` still overrides the profile value for controlled tests.

## Troubleshooting

If the script appears stuck or reports that the SSH pipe was closed:

- Stop it with Ctrl+C if it is still running.
- Run the SSH preflight command above and resolve host-key, password, or key-permission prompts there.
- Use `-TimeoutSeconds 30` or `--timeout-seconds 30` while testing.
- Prefer key-based SSH. Non-interactive mode requires a key that works without a password prompt. For password SSH, use `-AllowInteractiveSsh` or `--allow-interactive-ssh`; it uses `scp` copy-and-run mode so the password prompt can use the console. This mode temporarily copies the profiler to the remote host instead of streaming it through SSH stdin.

If the server records repeated pre-authentication resets even though the same key
worked previously, check the client-side SSH agent before changing the server:

1. Run `ssh-add -l` on the client and confirm the intended key is available.
2. Retry with the intended identity and `IdentitiesOnly=yes` so unrelated keys are
   not offered.
3. Do **not** set `IdentityAgent=none` when the usable private key is held by the SSH
   agent. That option can leave the client able to offer the public key but unable to
   complete the signature, which looks like a server-side pre-authentication reset.
4. If needed, compare `ssh -G your-user@your-linux-host` between the working manual
   command and the automation command. Check identity-agent, identity-file,
   identities-only, host-key, and key-exchange settings before editing `sshd_config`.

An SSH client/version mismatch was not the cause of this observed failure. Restore a
known-working client identity path first; do not reinstall the server, replace host
keys, weaken authentication, or enable password login merely to work around a missing
client signature. Keep host addresses, account names, key names, fingerprints, and
server log excerpts out of committed qualification evidence.

If SSH works but the profile has no GPU VRAM:

- Confirm the remote host can run `nvidia-smi` or `rocm-smi` directly.
- Confirm the container or LXC environment can see the GPU devices.
- Confirm the SSH user has permission to run the GPU tooling.
- Try `VramSelectionMode MaxDedicated` for conservative tests.

If Ollama is listed as unreachable in the profile:

- Confirm Ollama is running on the remote host.
- Confirm the remote host can run `ollama list`.
- Remember that the profile checks Ollama from the remote host, not from the editor machine.
