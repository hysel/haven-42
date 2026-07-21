#!/usr/bin/env python3
import argparse
import json
import re


def normalize(value):
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


parser = argparse.ArgumentParser(description="Select an engineering workflow plan without invoking it.")
parser.add_argument("--routes", required=True, help=argparse.SUPPRESS)
parser.add_argument("--workflows", required=True, help=argparse.SUPPRESS)
parser.add_argument("--text")
parser.add_argument("--route-id")
parser.add_argument("--json", action="store_true")
args = parser.parse_args()
with open(args.routes, encoding="utf-8") as stream:
    routes = json.load(stream)["routes"]
with open(args.workflows, encoding="utf-8") as stream:
    workflows = {item["id"]: item for item in json.load(stream)["workflows"]}

selected = None
ties = []
if args.route_id:
    selected = next((item for item in routes if item["id"] == args.route_id), None)
    if selected is None:
        parser.error(f"Unknown route id: {args.route_id}")
elif args.text:
    normalized = normalize(args.text)
    tokens = set(normalized.split())
    scored = []
    for route in routes:
        score = sum(1000 + len(normalize(phrase)) for phrase in route["phrases"] if normalize(phrase) in normalized)
        score += sum(10 for keyword in route["keywords"] if keyword.lower() in tokens)
        if score:
            scored.append((score, route))
    if scored:
        top_score = max(score for score, _ in scored)
        top = sorted((route for score, route in scored if score == top_score), key=lambda item: item["id"])
        selected = top[0] if len(top) == 1 else None
        ties = [item["id"] for item in top] if len(top) > 1 else []
else:
    parser.error("Provide --text or --route-id.")

steps = []
if selected:
    for workflow_id in selected["workflowIds"]:
        workflow = workflows.get(workflow_id)
        if workflow is None:
            parser.error(f"Route references unknown workflow: {workflow_id}")
        steps.append({"WorkflowId": workflow_id, "Name": workflow["name"], "SafetyLevel": workflow["safetyLevel"], "EntryPoints": workflow["entryPoints"]})
result = {"SchemaVersion": 1, "Kind": "engineering-route", "Status": "selected" if selected else "needs-clarification" if ties else "unmatched", "SelectedRouteId": selected["id"] if selected else None, "CapabilityId": selected["capabilityId"] if selected else None, "RequiresRepository": selected["requiresRepository"] if selected else None, "Steps": steps, "Candidates": ties, "InvocationAllowed": False, "Reason": "Deterministic route selected; review inputs and approval boundaries before invoking any workflow." if selected else "A unique engineering route could not be selected."}
if args.json:
    print(json.dumps(result, indent=2))
elif selected:
    print(f'Route: {selected["id"]}')
    for step in steps:
        print(f'- {step["WorkflowId"]} [{step["SafetyLevel"]}]')
    print("Auto invoke: no")
else:
    print(f'Routing status: {result["Status"]}')
    for item in ties:
        print(f'- {item}')
