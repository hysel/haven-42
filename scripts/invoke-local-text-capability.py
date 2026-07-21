#!/usr/bin/env python3
import argparse, datetime, json, os, pathlib, urllib.request

parser = argparse.ArgumentParser(description="Plan or execute a session-bound local Ollama text capability.")
parser.add_argument("--repo-root", required=True, help=argparse.SUPPRESS)
parser.add_argument("--capability-id", required=True, choices=["general.chat", "content.write", "content.summarize"])
parser.add_argument("--prompt", required=True)
parser.add_argument("--model", required=True)
parser.add_argument("--session-path", required=True)
parser.add_argument("--ollama-base-url", default="http://127.0.0.1:11434")
parser.add_argument("--artifact-name", default="result.json")
parser.add_argument("--timeout-seconds", type=int, default=120)
parser.add_argument("--response-fixture-path")
parser.add_argument("--execute", action="store_true")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args()

repo_root = pathlib.Path(args.repo_root).resolve()
session_path = pathlib.Path(args.session_path).resolve()
try:
    if os.path.commonpath([str(session_path), str(repo_root)]) == str(repo_root): parser.error("Provider sessions must stay outside the pack repository.")
except ValueError: pass
metadata_path = session_path / "session.json"
if not metadata_path.is_file(): parser.error(f"Session metadata is missing: {metadata_path}")
session = json.loads(metadata_path.read_text(encoding="utf-8"))
if session.get("capabilityId") != args.capability_id: parser.error("Session capability does not match the requested capability.")
if not __import__("re").fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\.json", args.artifact_name): parser.error("Artifact name must be a safe JSON filename.")
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
        payload = json.dumps({"model": args.model, "stream": False, "messages": [{"role": "system", "content": systems[args.capability_id]}, {"role": "user", "content": args.prompt}], "options": {"temperature": 0.2}}).encode()
        request = urllib.request.Request(args.ollama_base_url.rstrip("/") + "/api/chat", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=args.timeout_seconds) as stream: response = json.loads(stream.read().decode())
        provider_source = "ollama-chat"
    content = str(response.get("message", {}).get("content", ""))
    if not content.strip(): parser.error("Local text provider returned empty content.")

artifact_type = "chat-message" if args.capability_id == "general.chat" else "markdown-document"
artifact_content = {"role": "assistant", "text": content} if args.capability_id == "general.chat" else {"title": "Generated Writing" if args.capability_id == "content.write" else "Summary", "body": content}
artifact = {
    "schemaVersion": 1, "artifactType": artifact_type, "status": "succeeded" if args.execute else "planned",
    "createdAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), "sourceCapabilityId": args.capability_id,
    "provider": {"id": "ollama.local-text", "model": args.model, "source": provider_source}, "content": artifact_content,
    "policy": {"localExecution": True, "externalProvider": False, "repositoryRead": False, "fileWrite": bool(args.apply), "networkAccess": bool(args.execute and not args.response_fixture_path), "modelDownload": False, "approvalRequired": bool(args.apply)}
}
if args.apply:
    artifact_directory.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
result = {"SchemaVersion": 1, "Kind": "local-text-capability", "Status": "succeeded" if args.execute else "planned", "CapabilityId": args.capability_id, "ProviderId": "ollama.local-text", "Model": args.model, "ArtifactPath": str(artifact_path), "ArtifactWritten": bool(args.apply), "NetworkUsed": bool(args.execute and not args.response_fixture_path), "PromptPersisted": False, "RepositoryRead": False, "Artifact": artifact}
if args.json: print(json.dumps(result, indent=2))
else:
    print(f"Capability: {args.capability_id}\nProvider: ollama.local-text\nStatus: {result['Status']}\nArtifact: {artifact_path}\nArtifact written: {bool(args.apply)}")
    if args.execute: print("\n" + content)
