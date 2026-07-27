#!/usr/bin/env python3
"""Build the shared evidence dashboard and bounded local-web assurance view."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_PATH = ROOT / "config" / "evidence-catalog.tsv"
SURFACE_MATRIX_PATH = ROOT / "config" / "agent-surface-capabilities.json"
SURFACE_SOLUTIONS_PATH = ROOT / "config" / "agent-surface-solutions.json"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
ACTIVITY_STATUSES = {"supported", "validated", "planned", "scaffolded", "blocked", "retired"}
SOLUTION_STATUSES = {"supported", "validated", "planned", "scaffolded", "blocked", "retired"}


class EvidenceDashboardError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceDashboardError("evidence-configuration-unavailable") from error
    if not isinstance(value, dict):
        raise EvidenceDashboardError("evidence-configuration-invalid")
    return value


def _load_evidence(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise EvidenceDashboardError("evidence-catalog-unavailable") from error
    required = {
        "schema_version", "area", "subject", "surface", "surface_version",
        "provider", "os", "model", "operation", "validation_mode", "status",
        "evidence", "notes",
    }
    if set(reader.fieldnames or ()) != required or not rows:
        raise EvidenceDashboardError("evidence-catalog-invalid")
    if any(set(row) != required or row["schema_version"] != "2" for row in rows):
        raise EvidenceDashboardError("evidence-catalog-invalid")
    return rows


def _count_rows(rows: list[dict[str, str]], field: str, name: str) -> list[dict[str, Any]]:
    counts = Counter(row[field] for row in rows)
    return [
        {name: value, "Count": count}
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _validate_surface_matrix(value: dict[str, Any]) -> list[dict[str, Any]]:
    surfaces = value.get("surfaces")
    if value.get("schemaVersion") != 1 or not isinstance(surfaces, list):
        raise EvidenceDashboardError("surface-matrix-invalid")
    result = []
    seen: set[str] = set()
    for surface in surfaces:
        if not isinstance(surface, dict):
            raise EvidenceDashboardError("surface-matrix-invalid")
        surface_id = surface.get("id")
        activities = surface.get("activities")
        if (
            not isinstance(surface_id, str)
            or not IDENTIFIER.fullmatch(surface_id)
            or surface_id in seen
            or not isinstance(surface.get("name"), str)
            or not isinstance(surface.get("type"), str)
            or not isinstance(surface.get("currentValidationLevel"), str)
            or not isinstance(surface.get("supportTier"), str)
            or not isinstance(activities, dict)
        ):
            raise EvidenceDashboardError("surface-matrix-invalid")
        statuses = []
        for activity in activities.values():
            if not isinstance(activity, dict) or activity.get("status") not in ACTIVITY_STATUSES:
                raise EvidenceDashboardError("surface-matrix-invalid")
            statuses.append(activity["status"])
        seen.add(surface_id)
        result.append({
            "Id": surface_id,
            "Name": surface["name"],
            "Type": surface["type"],
            "SupportTier": surface["supportTier"],
            "ValidationLevel": surface["currentValidationLevel"],
            "ActivityCount": len(statuses),
            "SupportedActivities": statuses.count("supported"),
            "ValidatedActivities": statuses.count("validated"),
            "PlannedActivities": statuses.count("planned"),
            "ScaffoldedActivities": statuses.count("scaffolded"),
            "BlockedActivities": statuses.count("blocked"),
        })
    return sorted(result, key=lambda item: item["Name"])


def _validate_surface_solutions(value: dict[str, Any]) -> list[dict[str, Any]]:
    surfaces = value.get("surfaces")
    if value.get("schemaVersion") != 1 or not isinstance(surfaces, list):
        raise EvidenceDashboardError("surface-solutions-invalid")
    result = []
    seen: set[str] = set()
    for surface in surfaces:
        if not isinstance(surface, dict):
            raise EvidenceDashboardError("surface-solutions-invalid")
        surface_id = surface.get("id")
        operations = {}
        for operation in ("install", "configure", "test"):
            record = surface.get(operation)
            if not isinstance(record, dict) or record.get("status") not in SOLUTION_STATUSES:
                raise EvidenceDashboardError("surface-solutions-invalid")
            operations[operation] = record
        if (
            not isinstance(surface_id, str)
            or not IDENTIFIER.fullmatch(surface_id)
            or surface_id in seen
            or not isinstance(surface.get("name"), str)
            or not isinstance(surface.get("type"), str)
            or not isinstance(surface.get("currentValidationLevel"), str)
        ):
            raise EvidenceDashboardError("surface-solutions-invalid")
        seen.add(surface_id)
        result.append({
            "Id": surface_id,
            "Name": surface["name"],
            "Type": surface["type"],
            "ValidationLevel": surface["currentValidationLevel"],
            "InstallStatus": operations["install"]["status"],
            "ConfigureStatus": operations["configure"]["status"],
            "TestStatus": operations["test"]["status"],
            "InstallSolution": operations["install"].get("solution"),
            "ConfigureSolution": operations["configure"].get("solution"),
            "TestSolution": operations["test"].get("solution"),
            "InstallBlockedReason": operations["install"].get("blockedReason"),
            "ConfigureBlockedReason": operations["configure"].get("blockedReason"),
            "TestBlockedReason": operations["test"].get("blockedReason"),
        })
    return sorted(result, key=lambda item: item["Name"])


def build_evidence_dashboard(
    evidence_path: Path = EVIDENCE_PATH,
    surface_matrix_path: Path = SURFACE_MATRIX_PATH,
    surface_solutions_path: Path = SURFACE_SOLUTIONS_PATH,
) -> dict[str, Any]:
    rows = _load_evidence(evidence_path)
    surfaces = _validate_surface_matrix(_load_json(surface_matrix_path))
    solutions = _validate_surface_solutions(_load_json(surface_solutions_path))
    ignored_models = {"", "N/A", "local Ollama config"}
    models = sorted({
        model.strip()
        for row in rows
        for model in row["model"].split(",")
        if model.strip() not in ignored_models
    })
    return {
        "SchemaVersion": 2,
        "GeneratedAtUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "SourceEvidenceCatalog": "config/evidence-catalog.tsv",
        "SourceSurfaceMatrix": "config/agent-surface-capabilities.json",
        "SourceSurfaceSolutions": "config/agent-surface-solutions.json",
        "EvidenceCount": len(rows),
        "SurfaceCount": len(surfaces),
        "SurfaceSolutionCount": len(solutions),
        "ModelCount": len(models),
        "StatusCounts": _count_rows(rows, "status", "Status"),
        "AreaCounts": _count_rows(rows, "area", "Area"),
        "SurfaceEvidenceCounts": _count_rows(rows, "surface", "Surface"),
        "OperationCounts": _count_rows(rows, "operation", "Operation"),
        "ValidationModeCounts": _count_rows(rows, "validation_mode", "ValidationMode"),
        "Models": models,
        "SurfaceReadiness": surfaces,
        "SurfaceSolutionReadiness": solutions,
    }


def build_public_assurance_summary(
    evidence_path: Path = EVIDENCE_PATH,
    surface_matrix_path: Path = SURFACE_MATRIX_PATH,
    surface_solutions_path: Path = SURFACE_SOLUTIONS_PATH,
) -> dict[str, Any]:
    report = build_evidence_dashboard(
        evidence_path,
        surface_matrix_path,
        surface_solutions_path,
    )
    status_counts = [
        {"status": item["Status"], "count": item["Count"]}
        for item in report["StatusCounts"]
    ]
    surfaces = []
    solutions = {item["Id"]: item for item in report["SurfaceSolutionReadiness"]}
    for item in report["SurfaceReadiness"]:
        solution = solutions.get(item["Id"])
        if solution is None:
            raise EvidenceDashboardError("surface-catalog-mismatch")
        surfaces.append({
            "id": item["Id"],
            "name": item["Name"],
            "supportTier": item["SupportTier"],
            "validationLevel": item["ValidationLevel"],
            "supportedActivities": item["SupportedActivities"],
            "validatedActivities": item["ValidatedActivities"],
            "blockedActivities": item["BlockedActivities"],
            "installStatus": solution["InstallStatus"],
            "configureStatus": solution["ConfigureStatus"],
            "testStatus": solution["TestStatus"],
        })
    return {
        "schemaVersion": 1,
        "kind": "read-only-assurance-summary",
        "status": "ready",
        "sources": {
            "evidenceCatalog": report["SourceEvidenceCatalog"],
            "surfaceMatrix": report["SourceSurfaceMatrix"],
            "surfaceSolutions": report["SourceSurfaceSolutions"],
        },
        "evidence": {
            "recordCount": report["EvidenceCount"],
            "modelCount": report["ModelCount"],
            "statusCounts": status_counts,
        },
        "surfaces": surfaces,
        "disclosures": {
            "committedSanitizedEvidenceOnly": True,
            "liveValidationPerformed": False,
            "providerContacted": False,
            "repositoryInspected": False,
            "productionReadinessClaimed": False,
        },
        "effects": {
            "networkAccess": False,
            "processCreation": False,
            "filesystemWrite": False,
            "repositoryRead": False,
            "providerInvocation": False,
            "machineModification": False,
        },
    }


def dashboard_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Evidence Dashboard",
        "",
        "Generated from `config/evidence-catalog.tsv`, `config/agent-surface-capabilities.json`, and `config/agent-surface-solutions.json`.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Evidence rows | {report['EvidenceCount']} |",
        f"| Agent surfaces | {report['SurfaceCount']} |",
        f"| Models with evidence | {report['ModelCount']} |",
        "",
        "## Evidence Status",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {item['Status']} | {item['Count']} |" for item in report["StatusCounts"])
    lines.extend([
        "",
        "## Agent Surfaces",
        "",
        "| Surface | Validation level | Supported | Validated | Planned | Scaffolded | Blocked |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    lines.extend(
        f"| {item['Name']} | {item['ValidationLevel']} | {item['SupportedActivities']} | "
        f"{item['ValidatedActivities']} | {item['PlannedActivities']} | "
        f"{item['ScaffoldedActivities']} | {item['BlockedActivities']} |"
        for item in report["SurfaceReadiness"]
    )
    lines.extend([
        "",
        "## Install Configure Test",
        "",
        "| Surface | Install | Configure | Test | Validation |",
        "| --- | --- | --- | --- | --- |",
    ])
    lines.extend(
        f"| {item['Name']} | {item['InstallStatus']} | {item['ConfigureStatus']} | "
        f"{item['TestStatus']} | {item['ValidationLevel']} |"
        for item in report["SurfaceSolutionReadiness"]
    )
    lines.extend(["", "## Models", "", "| Model |", "| --- |"])
    lines.extend(f"| {model} |" for model in report["Models"])
    return "\n".join(lines) + "\n"


def _write(path: str | None, value: str) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-catalog-path", "-EvidenceCatalogPath", default=str(EVIDENCE_PATH))
    parser.add_argument("--surface-matrix-path", "-SurfaceMatrixPath", default=str(SURFACE_MATRIX_PATH))
    parser.add_argument("--surface-solution-path", "-SurfaceSolutionPath", default=str(SURFACE_SOLUTIONS_PATH))
    parser.add_argument("--output-path", "-OutputPath")
    parser.add_argument("--markdown-output-path", "-MarkdownOutputPath")
    parser.add_argument("--as-json", "-AsJson", action="store_true")
    args = parser.parse_args()
    report = build_evidence_dashboard(
        Path(args.evidence_catalog_path),
        Path(args.surface_matrix_path),
        Path(args.surface_solution_path),
    )
    serialized = json.dumps(report, indent=2) + "\n"
    markdown = dashboard_markdown(report)
    _write(args.output_path, serialized)
    _write(args.markdown_output_path, markdown)
    print(serialized if args.as_json or args.output_path else markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
