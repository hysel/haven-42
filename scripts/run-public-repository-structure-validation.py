#!/usr/bin/env python3
"""Run bounded read-only structure selection against approved bare repositories."""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = ROOT / "scripts/validate-public-repository-candidate.py"
SPEC = importlib.util.spec_from_file_location("public_candidate_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)
CONTRACT = json.loads((ROOT / "config/public-repository-structure-validation.json").read_text(encoding="utf-8"))
RULES = json.loads((ROOT / "config/project-profile-rules.json").read_text(encoding="utf-8"))


class StructureValidationError(ValueError):
    pass


def paths_for(repository: Path, commit: str) -> list[str]:
    raw = VALIDATOR._git(repository, "ls-tree", "-rz", "-r", "--name-only", commit)
    try:
        paths = [value.decode("utf-8", errors="strict") for value in raw.split(b"\0") if value]
    except UnicodeError as error:
        raise StructureValidationError("tree-path-encoding") from error
    if len(paths) > 20000 or paths != sorted(paths):
        raise StructureValidationError("tree-path-boundary")
    return paths


def matches(path: str, pattern: str) -> bool:
    normalized = path.casefold()
    candidate = pattern.casefold()
    return fnmatch.fnmatchcase(normalized, candidate) or fnmatch.fnmatchcase(Path(normalized).name, candidate)


def detect(paths: list[str]) -> list[dict]:
    result = []
    for rule in RULES["ecosystems"]:
        strong = sorted(path for path in paths if any(matches(path, pattern) for pattern in rule["strongPatterns"]))
        supporting = sorted(path for path in paths if any(matches(path, pattern) for pattern in rule["supportingPatterns"]))
        if strong or supporting:
            result.append({
                "ecosystem": rule["id"],
                "confidence": "high" if len(strong) >= 2 else "medium" if strong else "low",
                "strongMatchCount": len(strong),
                "supportingMatchCount": len(supporting),
                "reportedMatches": (strong + supporting)[:CONTRACT["limits"]["maximumReportedPaths"]],
                "rulePackId": rule["rulePackId"],
            })
    return sorted(result, key=lambda item: (-item["strongMatchCount"], -item["supportingMatchCount"], item["ecosystem"]))


def validate(candidate_id: str, repository: Path) -> dict:
    base = VALIDATOR.inspect(candidate_id, repository)
    paths = paths_for(repository.resolve(), base["commit"])
    detections = detect(paths)
    expected = CONTRACT["expected"].get(candidate_id)
    if not detections or detections[0]["ecosystem"] != expected or detections[0]["confidence"] == "low":
        raise StructureValidationError("expected-ecosystem-not-detected")
    result = {
        "schemaVersion": 1,
        "status": "read-only-public-structure-validation-passed",
        "candidateId": candidate_id,
        "commit": base["commit"],
        "projectDetection": detections,
        "runtimeContextPlan": {
            "ecosystem": expected,
            "reportedPathCount": sum(len(item["reportedMatches"]) for item in detections),
            "contentIncluded": False,
            "localPathIncluded": False
        },
        "workflowSelection": CONTRACT["selectedWorkflows"],
        "languageRuleSelection": [item["rulePackId"] for item in detections if item["rulePackId"]],
        "remediationTemplates": [],
        "effects": CONTRACT["effects"],
        "authority": CONTRACT["authority"],
    }
    encoded = json.dumps(result, sort_keys=True).encode("utf-8")
    if len(encoded) > CONTRACT["limits"]["maximumEvidenceBytes"]:
        raise StructureValidationError("evidence-size")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        output.relative_to(VALIDATOR.REVIEW_ROOT)
    except ValueError as error:
        raise SystemExit("Output must stay under ignored public-repository review storage.") from error
    if output.exists() or output.is_symlink():
        raise SystemExit("Output already exists.")
    value = validate(args.candidate, args.repository)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"candidateId": value["candidateId"], "status": value["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
