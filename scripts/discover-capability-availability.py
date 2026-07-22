#!/usr/bin/env python3
import argparse, json, pathlib, urllib.request

parser = argparse.ArgumentParser(description="Discover configured capability providers without invoking a capability.")
parser.add_argument("--capability-registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--provider-registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--engine-registry", required=True, help=argparse.SUPPRESS)
parser.add_argument("--capability-id")
parser.add_argument("--provider-id", default="ollama.local-text")
parser.add_argument("--model")
parser.add_argument("--runtime-base-url")
parser.add_argument("--ollama-base-url", help=argparse.SUPPRESS)
parser.add_argument("--engine-id")
parser.add_argument("--backend-id")
parser.add_argument("--hardware-profile")
parser.add_argument("--probe", action="store_true")
parser.add_argument("--response-fixture-path")
parser.add_argument("--timeout-seconds", type=int, default=10)
parser.add_argument("--json", action="store_true")
args = parser.parse_args()

capabilities = json.loads(pathlib.Path(args.capability_registry).read_text(encoding="utf-8"))["capabilities"]
providers = json.loads(pathlib.Path(args.provider_registry).read_text(encoding="utf-8"))["providers"]
engines = json.loads(pathlib.Path(args.engine_registry).read_text(encoding="utf-8"))["engines"]
if args.capability_id:
    capabilities = [item for item in capabilities if item["id"] == args.capability_id]
    if not capabilities: parser.error(f"Unknown capability id: {args.capability_id}")

probe_result = None
if args.probe:
    provider = next((item for item in providers if item["id"] == args.provider_id), None)
    if provider is None: parser.error(f"Unknown provider id: {args.provider_id}")
    selection = None
    if provider["protocol"] == "openai-chat-completions":
        if not all([args.engine_id, args.backend_id, args.hardware_profile]): parser.error("OpenAI-compatible providers require --engine-id, --backend-id, and --hardware-profile.")
        engine = next((item for item in engines if item["id"] == args.engine_id), None)
        backend = next((item for item in (engine or {}).get("backends", []) if item["id"] == args.backend_id), None)
        admitted = bool(engine and engine.get("status") == "validated-exact-profile" and provider.get("providerContract") in engine.get("providerContracts", []) and backend and backend.get("status") == "validated-exact-profile" and args.hardware_profile in backend.get("profiles", []))
        if not admitted: parser.error("Engine, backend, and hardware profile are not an admitted exact profile for this provider.")
        selection = {"engineId": args.engine_id, "backendId": args.backend_id, "hardwareProfile": args.hardware_profile, "admission": "validated-exact-profile"}
    if not args.model: parser.error("--model is required with --probe.")
    try:
        if args.response_fixture_path:
            response = json.loads(pathlib.Path(args.response_fixture_path).read_text(encoding="utf-8")); source = "validation-fixture"
        else:
            default_url = "http://127.0.0.1:11434" if provider["protocol"] == "ollama-chat" else "http://127.0.0.1:8080"
            base_url = args.runtime_base_url or args.ollama_base_url or default_url
            suffix = "/api/tags" if provider["protocol"] == "ollama-chat" else "/v1/models"
            with urllib.request.urlopen(urllib.request.Request(base_url.rstrip("/") + suffix), timeout=args.timeout_seconds) as stream: response = json.load(stream)
            source = "ollama-tags" if provider["protocol"] == "ollama-chat" else "openai-models"
        records = response.get("models", []) if provider["protocol"] == "ollama-chat" else response.get("data", [])
        names = {item.get("name") or item.get("model") or item.get("id") for item in records}
        installed = args.model in names
        probe_result = {"providerId": provider["id"], "status": "available" if installed else "configuration-required", "modelInstalled": installed, "source": source, "runtimeSelection": selection}
    except Exception:
        probe_result = {"providerId": provider["id"], "status": "unavailable", "modelInstalled": False, "source": "health-discovery-failed", "runtimeSelection": selection}

items = []
for capability in capabilities:
    candidates = []
    for provider in providers:
        if capability["id"] in provider["capabilityIds"]:
            state = probe_result["status"] if probe_result and provider["id"] == probe_result["providerId"] else provider["defaultAvailability"]
            candidates.append({"Id": provider["id"], "Kind": provider["kind"], "Protocol": provider["protocol"], "ValidationStatus": provider["validationStatus"], "Availability": state})
    effective = capability["availability"]["state"]
    if candidates: effective = "available" if any(item["Availability"] == "available" for item in candidates) else candidates[0]["Availability"]
    items.append({"CapabilityId": capability["id"], "DeclaredAvailability": capability["availability"]["state"], "EffectiveAvailability": effective, "Providers": candidates})
result = {"SchemaVersion": 1, "Kind": "capability-availability", "ProbeUsed": args.probe, "EndpointPersisted": False, "CapabilityInvoked": False, "Items": items}
if probe_result: result["Probe"] = probe_result
if args.json: print(json.dumps(result, indent=2))
else:
    for item in items:
        print(f'{item["CapabilityId"]}: {item["EffectiveAvailability"]}')
        for provider in item["Providers"]: print(f'  - {provider["Id"]}: {provider["Availability"]} [{provider["ValidationStatus"]}]')
