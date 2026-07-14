#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_REPO=""
RULES_PATH="$REPO_ROOT/config/project-profile-rules.json"
OUTPUT_PATH=""
AS_JSON=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-repo|-TargetRepo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --rules-path|-RulesPath)
      RULES_PATH="$2"
      shift 2
      ;;
    --output-path|-OutputPath)
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --as-json|-AsJson)
      AS_JSON=true
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$TARGET_REPO" ] || [ ! -d "$TARGET_REPO" ]; then
  printf 'Target repository is required and must exist. Use --target-repo <path>.\n' >&2
  exit 1
fi
if [ ! -f "$RULES_PATH" ]; then
  printf 'Project profile rules do not exist: %s\n' "$RULES_PATH" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for project classification.\n' >&2
  exit 1
fi

python3 - "$TARGET_REPO" "$RULES_PATH" "$OUTPUT_PATH" "$AS_JSON" <<'PY'
import fnmatch
import json
import os
import sys
from pathlib import Path

target = Path(sys.argv[1]).resolve()
rules_path = Path(sys.argv[2])
output_path = Path(sys.argv[3]) if sys.argv[3] else None
as_json = sys.argv[4].lower() == "true"
rules = json.loads(rules_path.read_text(encoding="utf-8"))
ignored = set(rules.get("ignoredDirectories") or [])

files = []
for root, directories, names in os.walk(target, followlinks=False):
    directories[:] = sorted(directory for directory in directories if directory not in ignored)
    root_path = Path(root)
    for name in sorted(names):
        relative = (root_path / name).relative_to(target).as_posix()
        files.append({"Name": name, "RelativePath": relative})


def matches(file_info, pattern):
    candidate = file_info["RelativePath"] if "/" in pattern else file_info["Name"]
    return fnmatch.fnmatch(candidate.lower(), pattern.lower())


def collect(patterns, strength):
    found = []
    for file_info in files:
        for pattern in patterns or []:
            if matches(file_info, pattern):
                found.append({
                    "Path": file_info["RelativePath"],
                    "Strength": strength,
                    "Pattern": pattern,
                })
                break
    return found


detections = []
for ecosystem in rules.get("ecosystems") or []:
    strong = collect(ecosystem.get("strongPatterns"), "strong")
    supporting = collect(ecosystem.get("supportingPatterns"), "supporting")
    if not strong and not supporting:
        continue
    confidence = "high" if strong else "medium"
    score = len(strong) * 100 + len(supporting) * 10
    evidence_by_key = {}
    for item in strong + supporting:
        evidence_by_key[(item["Path"], item["Strength"])] = item
    evidence = sorted(evidence_by_key.values(), key=lambda item: (item["Path"], item["Strength"]))[:25]
    detections.append({
        "Id": ecosystem["id"],
        "DisplayName": ecosystem["displayName"],
        "Confidence": confidence,
        "Score": score,
        "StrongEvidenceCount": len(strong),
        "SupportingEvidenceCount": len(supporting),
        "Evidence": evidence,
        "RulePackId": ecosystem.get("rulePackId"),
        "RulePackPath": ecosystem.get("rulePackPath"),
    })

detections.sort(key=lambda item: (-item["Score"], item["Id"]))
minimum_confidence = rules.get("activationMinimumConfidence")
confidence_rank = {"unconfirmed": 0, "medium": 1, "high": 2}
if minimum_confidence not in {"high", "medium"}:
    raise SystemExit(f"Unsupported activationMinimumConfidence: {minimum_confidence}")
selected = []
for detection in detections:
    if not detection["RulePackId"] or confidence_rank[detection["Confidence"]] < confidence_rank[minimum_confidence]:
        continue
    rule_id = detection["RulePackId"]
    selected.append({
        "Id": rule_id,
        "SourcePath": detection["RulePackPath"],
        "ActivePath": f"rules/active-language-{rule_id}.md",
        "Ecosystem": detection["Id"],
        "Confidence": detection["Confidence"],
        "Evidence": sorted({item["Path"] for item in detection["Evidence"]}),
    })

profile = {
    "SchemaVersion": 1,
    "ClassificationMethod": "deterministic-file-signals",
    "ActivationMinimumConfidence": minimum_confidence,
    "PrimaryEcosystem": detections[0]["Id"] if detections else "unknown",
    "Confidence": detections[0]["Confidence"] if detections else "unconfirmed",
    "DetectedEcosystems": detections,
    "SelectedRulePackIds": [item["Id"] for item in selected],
    "SelectedRulePacks": selected,
    "Unconfirmed": [] if detections else ["No configured ecosystem signal matched an inspected file."],
    "Privacy": {
        "TargetPathRecorded": False,
        "FileContentsRead": False,
        "IgnoredDirectories": sorted(ignored),
    },
}

text = json.dumps(profile, indent=2)
if output_path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text + "\n", encoding="utf-8")

if as_json or not output_path:
    print(text)
else:
    print(f"Primary ecosystem: {profile['PrimaryEcosystem']}")
    print(f"Confidence: {profile['Confidence']}")
    print("Selected rule packs: " + (", ".join(profile["SelectedRulePackIds"]) or "none"))
    print(f"Project profile written to {output_path}")
PY
