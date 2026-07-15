#!/usr/bin/env python3
"""Native onboarding report generator for Linux and macOS."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def command(workflow, platform, arguments=""):
    return "./" + workflow["entryPoints"][platform] + ((" " + arguments) if arguments else "")


def common(platform):
    return {
        "SchemaVersion": 1,
        "GeneratedAtUtc": datetime.now(timezone.utc).isoformat(),
        "Platform": platform,
        "SourceWorkflowRegistry": "config/workflows.json",
    }


def beginner(workflows, platform):
    definitions = [
        ("Check local setup health", "test-local-agent-health", "--target-repo <your-project-path> --skip-ollama --as-json", False),
        ("Profile local hardware and installed models", "profile-local-hardware", "--as-json", False),
        ("Generate evidence dashboard", "generate-evidence-dashboard", "--as-json", False),
        ("Generate model scorecard", "generate-model-scorecard", "--as-json", False),
        ("Generate model and config recommendation", "recommend-agent-config", "--model-profile-path runtime-validation-output/local-model-profile.json", False),
        ("Preview local-only Continue config", "apply-agent-config", "--target-repo <your-project-path> --dry-run", True),
        ("Preview pack install", "install-pack-assets", "--target-repo <your-project-path> --dry-run", True),
        ("Test local agent models", "test-local-agent-models", "--target-repo <your-project-path> --unload-after-each", False),
    ]
    steps = []
    for title, workflow_id, arguments, review in definitions:
        workflow = workflows[workflow_id]
        steps.append({"Title": title, "WorkflowId": workflow_id, "SafetyLevel": workflow["safetyLevel"],
                      "RequiresReviewBeforeApply": review, "Command": command(workflow, platform, arguments)})
    report = common(platform)
    report.update({"StepCount": len(steps), "Steps": steps})
    return report


def menu(workflows, solutions, platform):
    definitions = [
        ("First-Time Setup", "Start here", "get-beginner-setup-plan", "--as-json"),
        ("Health Check", "Check local setup", "test-local-agent-health", "--target-repo <your-project-path> --skip-ollama --as-json"),
        ("Model Choice", "Pick a local model", "recommend-agent-config", "--model-profile-path runtime-validation-output/local-model-profile.json"),
        ("Install Or Configure Agent", "Install assets", "install-pack-assets", "--target-repo <your-project-path> --dry-run"),
        ("Validate Model Or Agent", "Test before trust", "test-local-agent-models", "--target-repo <your-project-path> --unload-after-each"),
        ("Review Evidence", "Compare readiness", "generate-evidence-dashboard", "--as-json"),
        ("Cleanup Local Artifacts", "Clean local output", "cleanup-local-agent-artifacts", "--target-repo <your-project-path> --dry-run"),
        ("Release Readiness", "Validate the pack", "test-release-readiness", "--allow-dirty --as-json"),
    ]
    items = []
    for title, intent, workflow_id, arguments in definitions:
        workflow = workflows[workflow_id]
        items.append({"Title": title, "Intent": intent, "PrimaryWorkflowId": workflow_id,
                      "SafetyLevel": workflow["safetyLevel"], "Command": command(workflow, platform, arguments)})
    surfaces = [{"Name": item["name"], "ValidationLevel": item["currentValidationLevel"],
                 "InstallStatus": item["install"]["status"], "ConfigureStatus": item["configure"]["status"],
                 "TestStatus": item["test"]["status"]} for item in sorted(solutions["surfaces"], key=lambda item: item["name"])]
    report = common(platform)
    report.update({"SourceSolutionCatalog": "config/agent-surface-solutions.json", "MenuItemCount": len(items),
                   "MenuItems": items, "SurfaceCount": len(surfaces), "AgentSurfaces": surfaces})
    return report


def chooser(registry, platform):
    references = {"onboarding": "docs/agent-pack-menu.md", "model-selection": "docs/local-model-selection.md",
                  "validation": "docs/runtime-validation.md", "installation": "docs/shared-asset-installation.md"}
    items = []
    for workflow in sorted(registry["workflows"], key=lambda item: (item["category"], item["id"])):
        items.append({"Id": workflow["id"], "Name": workflow["name"], "Category": workflow["category"],
                      "SafetyLevel": workflow["safetyLevel"], "UiReady": bool(workflow["uiReady"]),
                      "Command": command(workflow, platform),
                      "Reference": references.get(workflow["category"], "docs/script-reference-appendix.md")})
    report = common(platform)
    report.update({"WorkflowCount": len(items), "UiReadyCount": sum(item["UiReady"] for item in items), "Workflows": items})
    return report


def markdown(view, report):
    if view == "beginner-plan":
        lines = ["# Beginner Setup Plan", "", "| Step | Workflow | Safety | Review |", "| --- | --- | --- | --- |"]
        for item in report["Steps"]:
            lines.append("| {} | {} | {} | {} |".format(item["Title"], item["WorkflowId"], item["SafetyLevel"], "yes" if item["RequiresReviewBeforeApply"] else "no"))
    elif view == "agent-menu":
        lines = ["# Agent Pack Menu", "", "| Action | Intent | Safety | Workflow |", "| --- | --- | --- | --- |"]
        for item in report["MenuItems"]:
            lines.append("| {} | {} | {} | {} |".format(item["Title"], item["Intent"], item["SafetyLevel"], item["PrimaryWorkflowId"]))
    else:
        lines = ["# Workflow Chooser", "", "| Category | Workflow | Safety | UI | Reference |", "| --- | --- | --- | --- | --- |"]
        for item in report["Workflows"]:
            lines.append("| {} | {} | {} | {} | {} |".format(item["Category"], item["Id"], item["SafetyLevel"], "yes" if item["UiReady"] else "no", item["Reference"]))
    return "\n".join(lines) + "\n"


parser = argparse.ArgumentParser()
parser.add_argument("view", choices=("beginner-plan", "agent-menu", "workflow-chooser"))
parser.add_argument("--platform", choices=("linux", "macos"), default="linux")
parser.add_argument("--output-path")
parser.add_argument("--markdown-output-path")
parser.add_argument("--as-json", action="store_true")
args = parser.parse_args()
registry = load("config/workflows.json")
workflows = {item["id"]: item for item in registry["workflows"]}
if args.view == "beginner-plan":
    result = beginner(workflows, args.platform)
elif args.view == "agent-menu":
    result = menu(workflows, load("config/agent-surface-solutions.json"), args.platform)
else:
    result = chooser(registry, args.platform)
encoded = json.dumps(result, indent=2) + "\n"
if args.output_path:
    output = Path(args.output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded, encoding="utf-8")
if args.markdown_output_path:
    output = Path(args.markdown_output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown(args.view, result), encoding="utf-8")
if args.as_json or not args.output_path:
    print(encoded, end="")
elif not args.markdown_output_path:
    print(markdown(args.view, result), end="")
