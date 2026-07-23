#!/usr/bin/env python3
import argparse, base64, datetime, json, os, pathlib, struct, sys, time, urllib.parse, urllib.request, uuid
from provider_security import MAX_IMAGE_RESPONSE_BYTES, MAX_JSON_RESPONSE_BYTES, ProviderSecurityError, prepare_artifact_directory, read_bounded, read_json, validate_base_url, write_new_file


def request_json(url, method="GET", payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
    return read_json(request, timeout, MAX_JSON_RESPONSE_BYTES)


def png_dimensions(data):
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Image provider did not return a valid PNG.")
    return struct.unpack(">II", data[16:24])


parser = argparse.ArgumentParser(description="Plan or execute session-bound local ComfyUI image generation.")
parser.add_argument("--repo-root", required=True, help=argparse.SUPPRESS)
parser.add_argument("--capability-id", default="media.image.create", choices=["media.image.create"])
prompt_group = parser.add_mutually_exclusive_group(required=True)
prompt_group.add_argument("--prompt")
prompt_group.add_argument("--prompt-file")
prompt_group.add_argument("--prompt-stdin", action="store_true")
parser.add_argument("--model", required=True)
parser.add_argument("--session-path", required=True)
parser.add_argument("--comfyui-base-url", default="http://127.0.0.1:8188")
parser.add_argument("--endpoint-trust-scope", choices=["loopback", "trusted-lan", "external"], default="loopback")
parser.add_argument("--artifact-name", default="image-result.json")
parser.add_argument("--image-name", default="generated-image.png")
parser.add_argument("--negative-prompt", default="text, watermark, logo, blurry, distorted")
parser.add_argument("--width", type=int, default=1024)
parser.add_argument("--height", type=int, default=1024)
parser.add_argument("--steps", type=int, default=20)
parser.add_argument("--cfg", type=float, default=7.0)
parser.add_argument("--seed", type=int, default=424242)
parser.add_argument("--timeout-seconds", type=int, default=300)
parser.add_argument("--maximum-image-bytes", type=int, default=MAX_IMAGE_RESPONSE_BYTES)
parser.add_argument("--response-fixture-path")
parser.add_argument("--execute", action="store_true")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args()
if args.prompt_file:
    args.prompt = pathlib.Path(args.prompt_file).read_text(encoding="utf-8")
elif args.prompt_stdin:
    args.prompt = sys.stdin.read(1024 * 1024 + 1)

repo_root = pathlib.Path(args.repo_root).resolve()
session_path_input = pathlib.Path(args.session_path)
session_path = session_path_input.resolve()
try:
    if os.path.commonpath([str(session_path), str(repo_root)]) == str(repo_root): parser.error("Provider sessions must stay outside the pack repository.")
except ValueError: pass
metadata_path = session_path / "session.json"
if not metadata_path.is_file(): parser.error(f"Session metadata is missing: {metadata_path}")
session = json.loads(metadata_path.read_text(encoding="utf-8"))
if session.get("capabilityId") != args.capability_id: parser.error("Session capability does not match the requested capability.")
import re
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\.json", args.artifact_name): parser.error("Artifact name must be a safe JSON filename.")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\.png", args.image_name): parser.error("Image name must be a safe PNG filename.")
if not args.prompt.strip() or len(args.prompt.encode("utf-8")) > 1024 * 1024: parser.error("Prompt must be from 1 byte through 1 MiB.")
if not args.model.strip() or len(args.model) > 256: parser.error("Model must be from 1 through 256 characters.")
if len(args.negative_prompt.encode("utf-8")) > 256 * 1024: parser.error("Negative prompt exceeds 256 KiB.")
if args.timeout_seconds < 1 or args.timeout_seconds > 3600: parser.error("Timeout must be from 1 through 3600 seconds.")
if args.maximum_image_bytes < 1 or args.maximum_image_bytes > MAX_IMAGE_RESPONSE_BYTES: parser.error("Maximum image size exceeds policy.")
if args.apply and not args.execute: parser.error("--apply requires --execute.")
if args.width < 64 or args.height < 64 or args.width > 2048 or args.height > 2048 or args.width % 8 or args.height % 8: parser.error("Image dimensions must be multiples of 8 from 64 through 2048.")
if args.steps < 1 or args.steps > 100: parser.error("Steps must be from 1 through 100.")

artifact_dir = (session_path / "artifacts").resolve()
artifact_path, image_path = (artifact_dir / args.artifact_name).resolve(), (artifact_dir / args.image_name).resolve()
for path in (artifact_path, image_path):
    if os.path.commonpath([str(path), str(artifact_dir)]) != str(artifact_dir): parser.error("Artifact path escaped the session artifact directory.")
    if args.apply and path.exists(): parser.error(f"Artifact already exists: {path}")

image_bytes = None
provider_source = "not-executed"
provider_retained_output = False
endpoint_policy = {"trustScope": "not-used", "executionLocation": "not-executed", "externalProvider": False}
if args.execute:
    if args.response_fixture_path:
        fixture = json.loads(pathlib.Path(args.response_fixture_path).read_text(encoding="utf-8"))
        if fixture.get("status") != "success" or not fixture.get("completed"): parser.error("Image validation fixture did not report success.")
        image_bytes = base64.b64decode(fixture["imageBase64"], validate=True)
        provider_source = "validation-fixture"
    else:
        try:
            endpoint_policy = validate_base_url(args.comfyui_base_url, args.endpoint_trust_scope)
        except ProviderSecurityError as error:
            parser.error(str(error))
        node_prefix = "haven-42/" + uuid.uuid4().hex
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {"seed": args.seed, "steps": args.steps, "cfg": args.cfg, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": args.model}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": args.width, "height": args.height, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": args.prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": args.negative_prompt, "clip": ["4", 1]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": node_prefix, "images": ["8", 0]}},
        }
        base_url = endpoint_policy["baseUrl"]
        prompt_id = request_json(base_url + "/prompt", "POST", {"prompt": workflow, "client_id": "haven-42"}, args.timeout_seconds)["prompt_id"]
        deadline, image_info = time.monotonic() + args.timeout_seconds, None
        while time.monotonic() < deadline:
            history = request_json(base_url + "/history/" + urllib.parse.quote(prompt_id), timeout=args.timeout_seconds)
            job = history.get(prompt_id)
            if job and job.get("outputs"):
                if job.get("status", {}).get("status_str") != "success": raise RuntimeError("ComfyUI image job did not succeed.")
                image_info = job["outputs"]["9"]["images"][0]
                break
            time.sleep(1)
        if not image_info: raise TimeoutError("Timed out waiting for the ComfyUI image job.")
        query = urllib.parse.urlencode({"filename": image_info["filename"], "subfolder": image_info.get("subfolder", ""), "type": image_info["type"]})
        try:
            image_bytes = read_bounded(base_url + "/view?" + query, args.timeout_seconds, args.maximum_image_bytes)
        except ProviderSecurityError as error:
            parser.error(str(error))
        try: request_json(base_url + "/history", "POST", {"clear": True}, args.timeout_seconds)
        except Exception: pass
        provider_source, provider_retained_output = "comfyui-api", True

width, height = (args.width, args.height) if image_bytes is None else png_dimensions(image_bytes)
artifact = {"schemaVersion": 1, "artifactType": "image", "status": "succeeded" if args.execute else "planned", "createdAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), "sourceCapabilityId": args.capability_id, "provider": {"id": "comfyui.local-image", "model": args.model, "source": provider_source, "trustScope": endpoint_policy["trustScope"], "executionLocation": endpoint_policy["executionLocation"]}, "content": {"path": args.image_name, "mediaType": "image/png", "width": width, "height": height, "seed": args.seed}, "policy": {"localExecution": endpoint_policy["executionLocation"] == "same-machine", "externalProvider": endpoint_policy["externalProvider"], "repositoryRead": False, "fileWrite": bool(args.apply), "networkAccess": bool(args.execute and not args.response_fixture_path), "modelDownload": False, "approvalRequired": bool(args.apply), "providerRetainedOutput": provider_retained_output}}
if args.apply:
    try:
        artifact_dir = prepare_artifact_directory(session_path_input)
        artifact_path, image_path = artifact_dir / args.artifact_name, artifact_dir / args.image_name
        write_new_file(image_path, image_bytes)
        try:
            write_new_file(artifact_path, (json.dumps(artifact, indent=2) + "\n").encode("utf-8"))
        except Exception:
            image_path.unlink(missing_ok=True)
            raise
    except (OSError, ProviderSecurityError) as error:
        parser.error(f"artifact-write-rejected: {error}")
result = {"SchemaVersion": 1, "Kind": "local-image-capability", "Status": "succeeded" if args.execute else "planned", "CapabilityId": args.capability_id, "ProviderId": "comfyui.local-image", "Model": args.model, "ArtifactPath": str(artifact_path), "ImagePath": str(image_path), "ArtifactWritten": bool(args.apply), "ImageWritten": bool(args.apply), "NetworkUsed": bool(args.execute and not args.response_fixture_path), "PromptPersisted": False, "EndpointPersisted": False, "RepositoryRead": False, "ProviderRetainedOutput": provider_retained_output, "Artifact": artifact}
if args.json: print(json.dumps(result, indent=2))
else: print(f"Capability: {args.capability_id}\nProvider: comfyui.local-image\nStatus: {result['Status']}\nImage: {image_path}\nArtifact: {artifact_path}\nFiles written: {bool(args.apply)}")
