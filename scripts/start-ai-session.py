#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import uuid


def is_within(child, parent):
    try:
        return os.path.commonpath([str(child), str(parent)]) == str(parent)
    except ValueError:
        return False


parser = argparse.ArgumentParser(description="Show the deterministic capability menu or plan a repository-optional AI session workspace.")
parser.add_argument("--repo-root", required=True, help=argparse.SUPPRESS)
parser.add_argument("--text")
parser.add_argument("--capability-id")
parser.add_argument("--list", action="store_true")
parser.add_argument("--workspace-root")
parser.add_argument("--session-id")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args()

repo_root = pathlib.Path(args.repo_root).resolve()
registry_path = repo_root / "config" / "capabilities.json"
with registry_path.open(encoding="utf-8") as stream:
    registry = json.load(stream)

if args.list:
    items = []
    for number, capability in enumerate(registry["capabilities"], start=1):
        items.append({
            "Number": number,
            "Id": capability["id"],
            "Name": capability["name"],
            "Description": capability["description"],
            "Availability": capability["availability"]["state"],
            "RepositoryMode": capability["repositoryMode"],
            "Policy": capability["policy"],
            "OutputArtifactTypes": capability["outputArtifactTypes"],
        })
    result = {"SchemaVersion": 1, "Kind": "capability-menu", "SourceRegistry": "config/capabilities.json", "Items": items}
else:
    if not args.text and not args.capability_id:
        parser.error("Provide --text, --capability-id, or --list.")
    resolver = repo_root / "scripts" / "resolve-capability.py"
    command = [sys.executable, str(resolver), "--registry", str(registry_path), "--json"]
    command += ["--capability-id", args.capability_id] if args.capability_id else ["--text", args.text]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode:
        parser.error(completed.stderr.strip() or "Capability routing failed.")
    routing = json.loads(completed.stdout)
    if routing["Status"] != "selected":
        result = {
            "SchemaVersion": 1,
            "Kind": "ai-session-plan",
            "Status": routing["Status"],
            "Routing": routing,
            "WorkspaceCreated": False,
            "CapabilityInvoked": False,
            "Reason": "A unique capability is required before a session workspace can be planned.",
        }
    else:
        workspace_root = pathlib.Path(args.workspace_root or pathlib.Path(tempfile.gettempdir()) / "local-engineering-agent-pack" / "sessions").resolve()
        if is_within(workspace_root, repo_root):
            parser.error(f"Session workspaces must stay outside the pack repository: {workspace_root}")
        session_id = args.session_id or f"session-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        if not __import__("re").fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", session_id):
            parser.error("Session id must contain 1-64 safe filename characters and start with a letter or number.")
        session_path = (workspace_root / session_id).resolve()
        if not is_within(session_path, workspace_root):
            parser.error("Resolved session path escaped the workspace root.")
        metadata_path = session_path / "session.json"
        artifact_path = session_path / "artifacts"
        selected = routing["Selected"]
        metadata = {
            "schemaVersion": 1,
            "sessionId": session_id,
            "status": "planned",
            "createdAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "capabilityId": selected["Id"],
            "capabilityAvailability": selected["Availability"]["state"],
            "repositoryMode": selected["RepositoryMode"],
            "artifactDirectory": "artifacts",
            "sourceCapabilityRegistry": "config/capabilities.json",
            "sourceArtifactContract": "config/typed-artifact-contract.json",
        }
        if args.apply:
            if session_path.exists():
                parser.error(f"Session path already exists: {session_path}")
            artifact_path.mkdir(parents=True)
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        result = {
            "SchemaVersion": 1,
            "Kind": "ai-session-plan",
            "Status": "created" if args.apply else "planned",
            "SessionId": session_id,
            "WorkspaceRoot": str(workspace_root),
            "SessionPath": str(session_path),
            "IntendedWrites": [str(metadata_path), str(artifact_path)],
            "WorkspaceCreated": bool(args.apply),
            "CapabilityInvoked": False,
            "Capability": selected,
            "Disclosures": {
                "RepositoryMode": selected["RepositoryMode"],
                "Availability": selected["Availability"]["state"],
                "Policy": selected["Policy"],
                "ArtifactPathDisclosedBeforeWrite": True,
            },
        }

if args.json:
    print(json.dumps(result, indent=2))
elif result["Kind"] == "capability-menu":
    print("What would you like to do?")
    for item in result["Items"]:
        print(f'{item["Number"]}. {item["Name"]} [{item["Availability"]}] - {item["Id"]}')
    print("Use --text or --capability-id to create a session plan.")
elif result["Status"] in ("planned", "created"):
    print(f'Session: {result["SessionId"]}')
    print(f'Capability: {result["Capability"]["Id"]} [{result["Capability"]["Availability"]["state"]}]')
    print(f'Workspace: {result["SessionPath"]}')
    print(f'Mode: {result["Status"]}')
    print("Capability invoked: no")
else:
    print(f'Routing status: {result["Status"]}')
    print(result["Reason"])
