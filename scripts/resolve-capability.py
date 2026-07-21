#!/usr/bin/env python3
import argparse
import json
import re


def public_capability(capability):
    return {
        "Id": capability["id"],
        "Name": capability["name"],
        "Category": capability["category"],
        "Modality": capability["modality"],
        "Description": capability["description"],
        "Availability": capability["availability"],
        "RepositoryMode": capability["repositoryMode"],
        "OutputArtifactTypes": capability["outputArtifactTypes"],
        "Policy": capability["policy"],
        "WorkflowSource": capability.get("workflowSource"),
    }


def normalize(value):
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


parser = argparse.ArgumentParser(description="Resolve ordinary-language intent through the deterministic capability registry.")
parser.add_argument("--registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--text")
parser.add_argument("--capability-id")
parser.add_argument("--list", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args()

with open(args.registry, encoding="utf-8") as stream:
    registry = json.load(stream)

if args.list:
    result = {
        "SchemaVersion": 1,
        "Kind": "capability-list",
        "SourceRegistry": "config/capabilities.json",
        "Capabilities": [public_capability(item) for item in registry["capabilities"]],
    }
else:
    selected = None
    candidates = []
    if args.capability_id:
        selected = next((item for item in registry["capabilities"] if item["id"] == args.capability_id), None)
        if selected is None:
            parser.error(f"Unknown capability id: {args.capability_id}")
        reason = "Explicit capability id selected."
    elif args.text:
        normalized = normalize(args.text)
        tokens = set(normalized.split())
        scored = []
        for capability in registry["capabilities"]:
            score = 0
            for phrase in capability["routing"]["phrases"]:
                normalized_phrase = normalize(phrase)
                if normalized_phrase in normalized:
                    score += 1000 + len(normalized_phrase)
            for keyword in capability["routing"]["keywords"]:
                if keyword.lower() in tokens:
                    score += 10
            if score:
                scored.append((score, capability))
        if scored:
            top_score = max(score for score, _ in scored)
            top = sorted((capability for score, capability in scored if score == top_score), key=lambda item: item["id"])
            if len(top) == 1:
                selected = top[0]
                reason = "Deterministic registry signals selected this capability."
            else:
                candidates = [public_capability(item) for item in top]
                reason = "Multiple capabilities received the same routing score; clarification is required."
        else:
            reason = "No deterministic registry signal matched; show the capability menu or ask a clarifying question."
    else:
        parser.error("Provide --text, --capability-id, or --list.")
    status = "selected" if selected else "needs-clarification" if candidates else "unmatched"
    result = {
        "SchemaVersion": 1,
        "Kind": "capability-routing",
        "Status": status,
        "SourceRegistry": "config/capabilities.json",
        "Selected": public_capability(selected) if selected else None,
        "Candidates": candidates,
        "InvocationAllowed": False,
        "Reason": reason,
    }

if args.json:
    print(json.dumps(result, indent=2))
elif result["Kind"] == "capability-list":
    for item in result["Capabilities"]:
        print(f'{item["Id"]}: {item["Name"]} [{item["Availability"]["state"]}]')
elif result["Status"] == "selected":
    print(f'Capability: {result["Selected"]["Id"]}')
    print(f'Availability: {result["Selected"]["Availability"]["state"]}')
    print("Auto invoke: no")
    print(f'Reason: {result["Reason"]}')
else:
    print(f'Routing status: {result["Status"]}')
    print(f'Reason: {result["Reason"]}')
    for item in result["Candidates"]:
        print(f'- {item["Id"]}: {item["Name"]}')
