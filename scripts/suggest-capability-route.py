#!/usr/bin/env python3
import argparse
import json
import re
import urllib.request


parser = argparse.ArgumentParser(description="Ask an optional LLM for an untrusted capability suggestion without invoking it.")
parser.add_argument("--registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--text", required=True)
parser.add_argument("--model", required=True)
parser.add_argument("--ollama-base-url", default="http://127.0.0.1:11434")
parser.add_argument("--response-fixture-path")
parser.add_argument("--execute", action="store_true")
parser.add_argument("--timeout-seconds", type=int, default=60)
parser.add_argument("--json", action="store_true")
args = parser.parse_args()
with open(args.registry, encoding="utf-8") as stream:
    capabilities = json.load(stream)["capabilities"]
by_id = {item["id"]: item for item in capabilities}

suggestion = None
provider_source = "not-executed"
parse_error = False
if args.execute:
    allowed = [{"id": item["id"], "name": item["name"], "description": item["description"]} for item in capabilities]
    system = "Suggest exactly one capability ID from the supplied registry, or request clarification. Return JSON only. Never claim an action was invoked. Registry: " + json.dumps(allowed, separators=(",", ":"))
    if args.response_fixture_path:
        with open(args.response_fixture_path, encoding="utf-8") as stream:
            response = json.load(stream)
        provider_source = "validation-fixture"
    else:
        schema = {"type": "object", "properties": {"capabilityId": {"type": ["string", "null"]}, "needsClarification": {"type": "boolean"}, "clarificationQuestion": {"type": ["string", "null"]}}, "required": ["capabilityId", "needsClarification", "clarificationQuestion"]}
        body = json.dumps({"model": args.model, "stream": False, "format": schema, "messages": [{"role": "system", "content": system}, {"role": "user", "content": args.text}], "options": {"temperature": 0}}).encode("utf-8")
        request = urllib.request.Request(args.ollama_base_url.rstrip("/") + "/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=args.timeout_seconds) as stream:
            response = json.load(stream)
        provider_source = "ollama-chat"
    raw = str(response.get("message", {}).get("content", ""))
    try:
        suggestion = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        try:
            suggestion = json.loads(match.group(0)) if match else None
        except json.JSONDecodeError:
            suggestion = None
        parse_error = suggestion is None

suggested_id = suggestion.get("capabilityId") if isinstance(suggestion, dict) else None
selected = by_id.get(suggested_id)
needs_clarification = bool(suggestion.get("needsClarification")) if isinstance(suggestion, dict) else False
if not args.execute:
    status, reason = "planned", "Execution is required before asking the optional LLM for a suggestion."
elif parse_error:
    status, reason = "rejected", "The LLM response was not valid routing JSON."
elif suggested_id and selected is None:
    status, reason = "rejected", "The LLM suggested an ID outside the committed capability registry."
elif needs_clarification or selected is None:
    status, reason = "needs-clarification", "The LLM requested clarification; no capability was selected."
else:
    status, reason = "suggested", "The LLM suggestion matched a committed capability; deterministic availability and policy checks still apply."

public = None if selected is None else {"Id": selected["id"], "Name": selected["name"], "Availability": selected["availability"], "RepositoryMode": selected["repositoryMode"], "Policy": selected["policy"]}
result = {"SchemaVersion": 1, "Kind": "llm-capability-suggestion", "Status": status, "ProviderSource": provider_source, "Selected": public, "ClarificationQuestion": suggestion.get("clarificationQuestion") if isinstance(suggestion, dict) and needs_clarification else None, "RegistryValidated": selected is not None, "ExecutionEligible": bool(selected and selected["availability"]["state"] == "available"), "InvocationAllowed": False, "PromptPersisted": False, "EndpointPersisted": False, "Reason": reason}
if args.json:
    print(json.dumps(result, indent=2))
else:
    print(f'Status: {status}')
    if public:
        print(f'Suggested capability: {public["Id"]}')
    if result["ClarificationQuestion"]:
        print(f'Clarification: {result["ClarificationQuestion"]}')
    print("Auto invoke: no")
