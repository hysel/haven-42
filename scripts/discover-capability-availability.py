#!/usr/bin/env python3
import argparse
import json
import urllib.request


parser = argparse.ArgumentParser(description="Discover configured capability providers without invoking a capability.")
parser.add_argument("--capability-registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--provider-registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--capability-id")
parser.add_argument("--provider-id", default="ollama.local-text")
parser.add_argument("--model")
parser.add_argument("--ollama-base-url", default="http://127.0.0.1:11434")
parser.add_argument("--probe", action="store_true")
parser.add_argument("--response-fixture-path")
parser.add_argument("--timeout-seconds", type=int, default=10)
parser.add_argument("--json", action="store_true")
args = parser.parse_args()

with open(args.capability_registry, encoding="utf-8") as stream:
    capabilities = json.load(stream)["capabilities"]
with open(args.provider_registry, encoding="utf-8") as stream:
    providers = json.load(stream)["providers"]

if args.capability_id:
    capabilities = [item for item in capabilities if item["id"] == args.capability_id]
    if not capabilities:
        parser.error(f"Unknown capability id: {args.capability_id}")

probe_result = None
if args.probe:
    provider = next((item for item in providers if item["id"] == args.provider_id), None)
    if provider is None:
        parser.error(f"Unknown provider id: {args.provider_id}")
    if provider["protocol"] != "ollama-chat":
        parser.error("The selected provider does not support Ollama health discovery.")
    if not args.model:
        parser.error("--model is required with --probe.")
    try:
        if args.response_fixture_path:
            with open(args.response_fixture_path, encoding="utf-8") as stream:
                response = json.load(stream)
            source = "validation-fixture"
        else:
            request = urllib.request.Request(args.ollama_base_url.rstrip("/") + "/api/tags")
            with urllib.request.urlopen(request, timeout=args.timeout_seconds) as stream:
                response = json.load(stream)
            source = "ollama-tags"
        names = {item.get("name") or item.get("model") for item in response.get("models", [])}
        installed = args.model in names
        probe_result = {"providerId": provider["id"], "status": "available" if installed else "configuration-required", "modelInstalled": installed, "source": source}
    except Exception:
        probe_result = {"providerId": provider["id"], "status": "unavailable", "modelInstalled": False, "source": "health-discovery-failed"}

items = []
for capability in capabilities:
    candidates = []
    for provider in providers:
        if capability["id"] in provider["capabilityIds"]:
            state = provider["defaultAvailability"]
            if probe_result and provider["id"] == probe_result["providerId"]:
                state = probe_result["status"]
            candidates.append({"Id": provider["id"], "Kind": provider["kind"], "ValidationStatus": provider["validationStatus"], "Availability": state})
    effective = capability["availability"]["state"]
    if candidates:
        effective = "available" if any(item["Availability"] == "available" for item in candidates) else candidates[0]["Availability"]
    items.append({"CapabilityId": capability["id"], "DeclaredAvailability": capability["availability"]["state"], "EffectiveAvailability": effective, "Providers": candidates})

result = {"SchemaVersion": 1, "Kind": "capability-availability", "ProbeUsed": args.probe, "EndpointPersisted": False, "CapabilityInvoked": False, "Items": items}
if probe_result:
    result["Probe"] = probe_result
if args.json:
    print(json.dumps(result, indent=2))
else:
    for item in items:
        print(f'{item["CapabilityId"]}: {item["EffectiveAvailability"]}')
        for provider in item["Providers"]:
            print(f'  - {provider["Id"]}: {provider["Availability"]} [{provider["ValidationStatus"]}]')
