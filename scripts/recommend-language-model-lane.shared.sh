#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_REPO=""; OPERATION="repository-discovery"; MATRIX_PATH="$REPO_ROOT/config/language-workflow-validation-matrix.json"
OPERATING_SYSTEM="$(uname -s)"; case "$OPERATING_SYSTEM" in Darwin) OPERATING_SYSTEM="macOS" ;; Linux) OPERATING_SYSTEM="Linux" ;; esac
SURFACE="Continue CLI"; SURFACE_VERSION="1.5.47"; PROVIDER="Ollama"; OUTPUT_PATH=""; AS_JSON=false
while [ "$#" -gt 0 ]; do case "$1" in
  --target-repo|-TargetRepo) TARGET_REPO="$2"; shift 2 ;;
  --operation|-Operation) OPERATION="$2"; shift 2 ;;
  --matrix-path|-MatrixPath) MATRIX_PATH="$2"; shift 2 ;;
  --operating-system|-OperatingSystem) OPERATING_SYSTEM="$2"; shift 2 ;;
  --surface|-Surface) SURFACE="$2"; shift 2 ;;
  --surface-version|-SurfaceVersion) SURFACE_VERSION="$2"; shift 2 ;;
  --provider|-Provider) PROVIDER="$2"; shift 2 ;;
  --output-path|-OutputPath) OUTPUT_PATH="$2"; shift 2 ;;
  --as-json|-AsJson) AS_JSON=true; shift ;;
  *) printf 'Unknown argument: %s\n' "$1" >&2; exit 1 ;;
esac; done
case "$OPERATION" in repository-discovery|implementation-plan|code-review|scoped-write) ;; *) printf 'Unsupported operation: %s\n' "$OPERATION" >&2; exit 1 ;; esac
[ -d "$TARGET_REPO" ] || { printf 'Target repository is required and must exist.\n' >&2; exit 1; }
[ -f "$MATRIX_PATH" ] || { printf 'Language workflow matrix does not exist: %s\n' "$MATRIX_PATH" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { printf 'python3 is required.\n' >&2; exit 1; }
PROFILE_JSON="$("$SCRIPT_DIR/get-project-profile.shared.sh" --target-repo "$TARGET_REPO" --as-json)"
python3 - "$MATRIX_PATH" "$OPERATION" "$OPERATING_SYSTEM" "$SURFACE" "$SURFACE_VERSION" "$PROVIDER" "$OUTPUT_PATH" "$AS_JSON" "$PROFILE_JSON" <<'PY'
import json, sys
from pathlib import Path
matrix=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")); operation, os_name, surface, version, provider, output, as_json=sys.argv[2:9]; profile=json.loads(sys.argv[9])
evidence_candidates=[matrix.get("latestValidation",{})]+matrix.get("nativeOperatingSystemEvidence",[])
evidence=next((item for item in evidence_candidates if item.get("surface")==surface and item.get("surfaceVersion")==version and item.get("provider")==provider and (item.get("operatingSystem")==os_name or item.get("operatingSystem","").startswith(os_name+" "))),None)
matches=evidence is not None
entries={x["rulePackId"]:x for x in matrix["entries"]}; lanes=[]; unavailable=[]
for pack in profile.get("SelectedRulePacks",[]):
 entry=entries.get(pack["Id"]); model=entry and entry.get("operationModels",{}).get(operation)
 if entry and matches and entry.get("operations",{}).get(operation)=="validated" and model: lanes.append({"RulePackId":pack["Id"],"Ecosystem":pack["Ecosystem"],"Operation":operation,"Model":model,"Status":"validated","EvidenceFiles":pack.get("Evidence",[]),"EvidenceDocument":evidence.get("evidenceDocument","")})
 else: unavailable.append({"RulePackId":pack["Id"],"Ecosystem":pack["Ecosystem"],"Reason":"EVIDENCE_CONTEXT_MISMATCH" if not matches else ("NO_MATRIX_ENTRY" if not entry else "OPERATION_NOT_VALIDATED")})
models=list(dict.fromkeys(x["Model"] for x in lanes))
result={"SchemaVersion":1,"Status":"validated-lane-available" if lanes else "no-validated-lane","Request":{"Operation":operation,"Surface":surface,"SurfaceVersion":version,"Provider":provider,"OperatingSystem":os_name},"Project":{"PrimaryEcosystem":profile["PrimaryEcosystem"],"Confidence":profile["Confidence"],"SelectedRulePackIds":profile.get("SelectedRulePackIds",[])},"Lanes":lanes,"Unavailable":unavailable,"ContinueModelProfiles":[{"Name":f"Validated {operation} lane - {x}","Model":x,"Roles":["chat","edit","apply"]} for x in models],"Limitation":"This recommendation selects evidence-backed lanes. Agent surfaces must still explicitly select a model or profile; runtime auto-switching is not assumed.","Evidence":{"Date":evidence.get("date") if evidence else None,"Document":evidence.get("evidenceDocument") if evidence else None,"ValidatedCells":evidence.get("validatedCells") if evidence else None,"FailedCells":evidence.get("failedCells") if evidence else None,"OperatingSystem":evidence.get("operatingSystem") if evidence else None},"Privacy":{"TargetPathRecorded":False,"FileContentsReadBySelector":False}}
text=json.dumps(result,indent=2)+"\n"
if output: p=Path(output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding="utf-8")
if as_json or not output: print(text,end="")
else: print("Language model lane status: "+result["Status"]+"\nRecommended models: "+(", ".join(models) or "none")+"\nRecommendation written to "+output)
PY
