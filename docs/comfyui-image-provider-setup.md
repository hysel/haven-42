# ComfyUI Image Provider Setup

This runbook reproduces the promoted local image-generation boundary used by `comfyui.local-image`. It documents the exact Linux configuration that passed live validation. Other operating systems, accelerators, ComfyUI releases, checkpoints, custom nodes, and external API nodes require their own evidence before promotion.

## Validated Profile

| Component | Validated value |
| --- | --- |
| Operating system | Ubuntu 24.04 LTS, x86-64 |
| ComfyUI | tag `v0.28.2`, commit `306af3a8771a8232d26bd20acbfc6b07f862ad2b` |
| Python | 3.12 virtual environment |
| PyTorch | `2.11.0+cu126` |
| GPU | NVIDIA Tesla V100 32 GB, compute capability 7.0 |
| Checkpoint | `sd_xl_base_1.0.safetensors` |
| Checkpoint SHA-256 | `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b` |
| Network | ComfyUI listens on `127.0.0.1:8188`; remote access uses SSH tunneling |

CUDA 13 removed Volta library support, so the validated V100 path intentionally uses the CUDA 12.6 PyTorch wheels. Do not replace this with a CUDA 13 wheel on Volta hardware. Current Turing or newer hardware may use a different evidence-gated profile.

## 1. Inventory The Host

Run these read-only commands on the proposed Linux host:

```bash
cat /etc/os-release
uname -a
nvidia-smi --query-gpu=index,name,memory.total,memory.free,driver_version,compute_cap --format=csv,noheader
free -h
df -h /
python3 --version
git --version
systemd-detect-virt || true
```

Confirm that the intended GPU is visible to the non-root service account and that the host has sufficient storage for Python packages, the checkpoint, generated outputs, and rollback copies. The validated installation consumed several gigabytes of Python/CUDA packages plus a 6.94 GB checkpoint.

## 2. Create Dedicated SSH Access

Generate a dedicated Ed25519 key on the operator workstation. Never copy or transmit the private key.

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519_comfyui" -N "" -C "comfyui-server-access"
```

As root on the server, create the restricted runtime account and authorize only the public half:

```bash
useradd --create-home --user-group --shell /bin/bash haven42-comfyui
install -d -m 700 -o haven42-comfyui -g haven42-comfyui /home/haven42-comfyui/.ssh
printf '%s\n' '<dedicated-public-key>' > /home/haven42-comfyui/.ssh/authorized_keys
chown haven42-comfyui:haven42-comfyui /home/haven42-comfyui/.ssh/authorized_keys
chmod 600 /home/haven42-comfyui/.ssh/authorized_keys
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Independently compare the server-console host fingerprint with the workstation scan before accepting it. Do not grant the runtime account unrestricted sudo or Docker access.

## 3. Install The Pinned Runtime

Log in as `haven42-comfyui`. Clone the immutable release tag, verify the resolved commit, and create an isolated environment:

```bash
git clone --branch v0.28.2 --depth 1 https://github.com/Comfy-Org/ComfyUI.git /home/haven42-comfyui/ComfyUI
git -C /home/haven42-comfyui/ComfyUI rev-parse HEAD

python3 -m venv /home/haven42-comfyui/ComfyUI/.venv
. /home/haven42-comfyui/ComfyUI/.venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0 \
  --index-url https://download.pytorch.org/whl/cu126
python -m pip install -r /home/haven42-comfyui/ComfyUI/requirements.txt
```

The resolved ComfyUI commit must be `306af3a8771a8232d26bd20acbfc6b07f862ad2b`. Dependency resolution failure is a stop condition; do not improvise unrecorded version substitutions.

## 4. Download And Verify SDXL

Download to a partial filename, verify the published digest, and admit the checkpoint only after the hash matches:

```bash
model_dir=/home/haven42-comfyui/ComfyUI/models/checkpoints
final_path="$model_dir/sd_xl_base_1.0.safetensors"
partial_path="$final_path.partial"
expected=31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b

mkdir -p "$model_dir"
rm -f "$partial_path"
curl --fail --location --retry 3 --retry-delay 5 \
  --output "$partial_path" \
  'https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors?download=true'
printf '%s  %s\n' "$expected" "$partial_path" | sha256sum --check --status
mv "$partial_path" "$final_path"
chmod 0644 "$final_path"
sha256sum "$final_path"
```

Review the SDXL Open RAIL++ license and model-card limitations before use. A mismatched digest must leave no admitted checkpoint.

## 5. Validate CUDA Before Starting ComfyUI

```bash
export CUDA_VISIBLE_DEVICES=0
/home/haven42-comfyui/ComfyUI/.venv/bin/python -c \
  'import torch; x=torch.arange(1024,device="cuda"); print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0), (x*x).sum().item())'
```

For the validated V100 profile, PyTorch must report CUDA 12.6, the selected Tesla V100, compute capability `(7, 0)`, and an architecture list containing `sm_70`.

## 6. Install The Hardened Service

As root, create writable runtime directories:

```bash
install -d -o haven42-comfyui -g haven42-comfyui -m 0750 \
  /home/haven42-comfyui/ComfyUI/input \
  /home/haven42-comfyui/ComfyUI/output \
  /home/haven42-comfyui/ComfyUI/temp \
  /home/haven42-comfyui/ComfyUI/user \
  /home/haven42-comfyui/.cache
```

Create `/etc/systemd/system/comfyui.service`:

```ini
[Unit]
Description=ComfyUI Local Image Generation
Documentation=https://docs.comfy.org/
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=haven42-comfyui
Group=haven42-comfyui
WorkingDirectory=/home/haven42-comfyui/ComfyUI
Environment=HOME=/home/haven42-comfyui
Environment=PYTHONUNBUFFERED=1
Environment=CUDA_DEVICE_ORDER=PCI_BUS_ID
Environment=CUDA_VISIBLE_DEVICES=0
ExecStart=/home/haven42-comfyui/ComfyUI/.venv/bin/python /home/haven42-comfyui/ComfyUI/main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch --disable-metadata --disable-all-custom-nodes --disable-api-nodes
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
KillSignal=SIGINT
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/haven42-comfyui/ComfyUI/input
ReadWritePaths=/home/haven42-comfyui/ComfyUI/output
ReadWritePaths=/home/haven42-comfyui/ComfyUI/temp
ReadWritePaths=/home/haven42-comfyui/ComfyUI/user
ReadWritePaths=/home/haven42-comfyui/.cache
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
LockPersonality=true
RestrictSUIDSGID=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
CapabilityBoundingSet=

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
systemctl daemon-reload
systemctl enable --now comfyui.service
systemctl --no-pager --full status comfyui.service
systemd-analyze security comfyui.service --no-pager
```

Do not remove `--disable-metadata`, `--disable-all-custom-nodes`, or `--disable-api-nodes` without separate security and compatibility evidence.

## 7. Verify The Local API

```bash
ss -lntp | grep '127.0.0.1:8188'
curl --fail --silent http://127.0.0.1:8188/system_stats
curl --fail --silent http://127.0.0.1:8188/models/checkpoints
```

Reject any configuration listening on `0.0.0.0:8188` or `[::]:8188`. The checkpoint inventory must contain `sd_xl_base_1.0.safetensors`.

## 8. Access Through SSH Tunneling

From Windows:

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519_comfyui" `
  -o ExitOnForwardFailure=yes `
  -L 8188:127.0.0.1:8188 `
  -N haven42-comfyui@<server-host>
```

While the tunnel is open, the existing ComfyUI interface and API are available at `http://127.0.0.1:8188`. The server address and SSH paths are local configuration and must never be committed.

## 9. Validate The Pack Adapter

Create a session outside the pack repository, preview the planned writes, and execute only after review:

```powershell
.\scripts\start-ai-session.ps1 `
  -CapabilityId media.image.create `
  -WorkspaceRoot <outside-repository-workspace> `
  -SessionId image `
  -Apply

.\scripts\invoke-local-image-capability.ps1 `
  -Prompt "A concise test prompt" `
  -Model sd_xl_base_1.0.safetensors `
  -SessionPath <session-path> `
  -ComfyUiBaseUrl http://127.0.0.1:8188 `
  -AsJson

.\scripts\invoke-local-image-capability.ps1 `
  -Prompt "A concise test prompt" `
  -Model sd_xl_base_1.0.safetensors `
  -SessionPath <session-path> `
  -ComfyUiBaseUrl http://127.0.0.1:8188 `
  -Execute -Apply -AsJson
```

Confirm that the typed artifact reports `PromptPersisted: false`, `EndpointPersisted: false`, `RepositoryRead: false`, and `ProviderRetainedOutput: true`. ComfyUI keeps its provider-side output even after API history is cleared; include it in retention and cleanup policy.

## 10. Upgrade And Rollback Policy

- Never point the service at a moving branch or run an unattended `git pull`.
- Install a proposed ComfyUI release in a parallel directory and virtual environment.
- Re-run commit, dependency, CUDA, checkpoint, service, metadata, history, recovery, tunnel, visual, adapter, and cross-platform fixture gates.
- Update the evidence catalog and service path only after every required check passes.
- If validation fails, document the candidate but do not ship its scripts, templates, workflows, or configuration.
- Roll back by restoring the previous service file and pinned directory, running `systemctl daemon-reload`, and restarting the service.

Official references: [ComfyUI manual installation](https://docs.comfy.org/installation/manual_install), [ComfyUI server routes](https://docs.comfy.org/development/comfyui-server/comms_routes), [PyTorch previous versions](https://pytorch.org/get-started/previous-versions/), [CUDA 13 release notes](https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html), and [SDXL Base 1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0).
