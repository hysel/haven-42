#!/usr/bin/env python3
import argparse, datetime, json, os, pathlib, re, urllib.request

parser = argparse.ArgumentParser(description="Plan or execute a session-bound local text capability through an admitted provider.")
parser.add_argument("--repo-root", required=True, help=argparse.SUPPRESS)
parser.add_argument("--provider-registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--engine-registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--capability-id", required=True, choices=["general.chat", "content.write", "content.summarize"])
parser.add_argument("--prompt", required=True)
parser.add_argument("--model", required=True)
parser.add_argument("--session-path", required=True)
parser.add_argument("--provider-id", default="ollama.local-text")
parser.add_argument("--runtime-base-url")
parser.add_argument("--ollama-base-url", help=argparse.SUPPRESS)
parser.add_argument("--engine-id")
parser.add_argument("--backend-id")
parser.add_argument("--hardware-profile")
parser.add_argument("--artifact-name", default="result.json")
parser.add_argument("--timeout-seconds", type=int, default=120)
parser.add_argument("--response-fixture-path")
parser.add_argument("--execute", action="store_true")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args()

providers = json.loads(pathlib.Path(args.provider_registry).read_text(encoding="utf-8"))["providers"]
provider = next((item for item in providers if item["id"] == args.provider_id), None)
if not provider or args.capability_id not in provider.get("capabilityIds", []): parser.error("Provider is unknown or does not support the requested capability.")
if provider["protocol"] not in {"ollama-chat", "openai-chat-completions"}: parser.error("Provider protocol is not supported by this adapter.")

selection = None
if provider["protocol"] == "openai-chat-completions":
    if not all([args.engine_id, args.backend_id, args.hardware_profile]): parser.error("OpenAI-compatible providers require --engine-id, --backend-id, and --hardware-profile.")
    registry = json.loads(pathlib.Path(args.engine_registry).read_text(encoding="utf-8"))
    engine = next((item for item in registry["engines"] if item["id"] == args.engine_id), None)
    backend = next((item for item in (engine or {}).get("backends", []) if item["id"] == args.backend_id), None)
    required_contract = provider.get("providerContract")
    admitted = bool(engine and engine.get("status") == "validated-exact-profile" and required_contract in engine.get("providerContracts", []) and backend and backend.get("status") == "validated-exact-profile" and args.hardware_profile in backend.get("profiles", []))
    if not admitted: parser.error("Engine, backend, and hardware profile are not an admitted exact profile for this provider.")
    selection = {"engineId": args.engine_id, "backendId": args.backend_id, "hardwareProfile": args.hardware_profile, "admission": "validated-exact-profile"}
elif any([args.engine_id, args.backend_id, args.hardware_profile]):
    parser.error("Explicit engine selection is only supported for engine-backed OpenAI-compatible providers.")

repo_root = pathlib.Path(args.repo_root).resolve()
session_path = pathlib.Path(args.session_path).resolve()
try:
    if os.path.commonpath([str(session_path), str(repo_root)]) == str(repo_root): parser.error("Provider sessions must stay outside the pack repository.")
except ValueError: pass
metadata_path = session_path / "session.json"
if not metadata_path.is_file(): parser.error(f"Session metadata is missing: {metadata_path}")
session = json.loads(metadata_path.read_text(encoding="utf-8"))
if session.get("capabilityId") != args.capability_id: parser.error("Session capability does not match the requested capability.")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\.json", args.artifact_name): parser.error("Artifact name must be a safe JSON filename.")
if not args.prompt.strip() or not args.model.strip(): parser.error("Prompt and model must not be empty.")
if args.apply and not args.execute: parser.error("--apply requires --execute.")
artifact_directory = (session_path / "artifacts").resolve()
artifact_path = (artifact_directory / args.artifact_name).resolve()
if os.path.commonpath([str(artifact_path), str(artifact_directory)]) != str(artifact_directory): parser.error("Artifact path escaped the session artifact directory.")
if args.apply and artifact_path.exists(): parser.error(f"Artifact already exists: {artifact_path}")

systems = {
    "general.chat": "Answer the user's general question clearly. Do not claim repository access or actions you did not perform.",
    "content.write": "Create the requested general-purpose content as clean Markdown. Do not claim external facts were verified unless the user supplied them.",
    "content.summarize": "Summarize only the material supplied by the user. Preserve uncertainty and do not invent missing facts. Return clean Markdown.",
}
content = None
provider_source = "not-executed"
if args.execute:
    if args.response_fixture_path:
        response = json.loads(pathlib.Path(args.response_fixture_path).read_text(encoding="utf-8"))
        provider_source = "validation-fixture"
    else:
        default_url = "http://127.0.0.1:11434" if provider["protocol"] == "ollama-chat" else "http://127.0.0.1:8080"
        base_url = args.runtime_base_url or args.ollama_base_url or default_url
        payload = {"model": args.model, "stream": False, "messages": [{"role": "system", "content": systems[args.capability_id]}, {"role": "user", "content": args.prompt}]}
        if provider["protocol"] == "ollama-chat": payload["options"] = {"temperature": 0.2}
        else: payload["temperature"] = 0.2
        suffix = "/api/chat" if provider["protocol"] == "ollama-chat" else "/v1/chat/completions"
        request = urllib.request.Request(base_url.rstrip("/") + suffix, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=args.timeout_seconds) as stream: response = json.loads(stream.read().decode())
        provider_source = provider["protocol"]
    if provider["protocol"] == "ollama-chat": content = str(response.get("message", {}).get("content", ""))
    else:
        choices = response.get("choices", [])
        content = str(choices[0].get("message", {}).get("content", "")) if choices else ""
    if not content.strip(): parser.error("Local text provider returned empty content.")

artifact_type = "chat-message" if args.capability_id == "general.chat" else "markdown-document"
artifact_content = {"role": "assistant", "text": content} if args.capability_id == "general.chat" else {"title": "Generated Writing" if args.capability_id == "content.write" else "Summary", "body": content}
provider_metadata = {"id": provider["id"], "model": args.model, "source": provider_source}
if selection: provider_metadata["runtimeSelection"] = selection
artifact = {
    "schemaVersion": 1, "artifactType": artifact_type, "status": "succeeded" if args.execute else "planned",
    "createdAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), "sourceCapabilityId": args.capability_id,
    "provider": provider_metadata, "content": artifact_content,
    "policy": {"localExecution": True, "externalProvider": False, "repositoryRead": False, "fileWrite": bool(args.apply), "networkAccess": bool(args.execute and not args.response_fixture_path), "modelDownload": False, "approvalRequired": bool(args.apply)}
}
if args.apply:
    artifact_directory.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
result = {"SchemaVersion": 1, "Kind": "local-text-capability", "Status": "succeeded" if args.execute else "planned", "CapabilityId": args.capability_id, "ProviderId": provider["id"], "Protocol": provider["protocol"], "RuntimeSelection": selection, "Model": args.model, "ArtifactPath": str(artifact_path), "ArtifactWritten": bool(args.apply), "NetworkUsed": bool(args.execute and not args.response_fixture_path), "PromptPersisted": False, "EndpointPersisted": False, "RepositoryRead": False, "Artifact": artifact}
if args.json: print(json.dumps(result, indent=2))
else:
    print(f"Capability: {args.capability_id}\nProvider: {provider['id']}\nStatus: {result['Status']}\nArtifact: {artifact_path}\nArtifact written: {bool(args.apply)}")
    if args.execute: print("\n" + content)
