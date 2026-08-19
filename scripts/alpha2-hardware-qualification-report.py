#!/usr/bin/env python3
"""Render human hardware evidence and a machine-readable failure triage bundle."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPARE_SPEC = importlib.util.spec_from_file_location(
    "hardware_cross_os_for_report",
    ROOT / "scripts/alpha2-hardware-cross-os-report.py",
)
assert COMPARE_SPEC and COMPARE_SPEC.loader
COMPARE = importlib.util.module_from_spec(COMPARE_SPEC)
COMPARE_SPEC.loader.exec_module(COMPARE)


def read_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError(f"unsafe input: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise ValueError(f"invalid input object: {path}")
    if value.get("kind", "").endswith("qualification-result"):
        for field in ("containsPrivateMachineIdentity", "containsNetworkIdentity", "containsRawPromptsOrResponses"):
            if value.get(field) is not False:
                raise ValueError(f"qualification input is not sanitized: {field}")
    return value


def markdown(value: Any) -> str:
    return " ".join(str(value).splitlines()).replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")


def failure_map(result: dict[str, Any]) -> dict[str, list[str]]:
    failed = result.get("coreTaskGate", {}).get("failed", {})
    if not isinstance(failed, dict):
        raise ValueError("invalid core failure map")
    return {str(model): [str(cell) for cell in cells] for model, cells in failed.items() if isinstance(cells, list)}


def build_triage(first: dict[str, Any], second: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    expected = COMPARE.build_comparison(first, second)
    if comparison != expected:
        raise ValueError("comparison does not match its qualification inputs")
    first_failures, second_failures = failure_map(first), failure_map(second)
    entries = []
    for cell in comparison.get("cells", []):
        model = cell["modelId"]
        if not cell.get("comparable"):
            classification = "not-run"
            next_action = "Wait for the missing evidence cell; do not infer an outcome."
        elif cell["first"] != cell["second"]:
            classification = "cross-os-outcome-divergence"
            next_action = "Reproduce with exact runtime, driver, prompt contract, and artifact bindings on both operating systems."
        elif cell["first"] == "failed":
            same_cells = first_failures.get(model, []) == second_failures.get(model, [])
            classification = "shared-failure-cell" if same_cells else "cross-os-failure-cell-divergence"
            next_action = "Inspect the shared model/task contract." if same_cells else "Compare the exact failed task cells before retesting."
        else:
            classification = "common-pass"
            next_action = "No failure triage required; retain exact-scope evidence boundaries."
        entries.append({
            "modelId": model, "classification": classification,
            "firstOutcome": cell["first"], "secondOutcome": cell["second"],
            "firstFailureCells": first_failures.get(model, []),
            "secondFailureCells": second_failures.get(model, []),
            "nextAction": next_action,
        })
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-hardware-failure-triage",
        "status": "complete" if comparison.get("status") == "complete" else "incomplete-local-review-only",
        "accelerator": comparison.get("accelerator"),
        "qualificationProfileId": comparison.get("qualificationProfileId"),
        "entries": entries,
        "automaticRetestAuthorized": False,
        "automaticSupportChangeAllowed": False,
    }


def power_lines(result: dict[str, Any]) -> list[str]:
    power = result.get("power", {})
    lines = [
        f"- Source and scope: {markdown(power.get('telemetrySource', 'not reported'))}; {markdown(power.get('scope', 'not reported'))}",
        f"- Samples: {markdown(power.get('sampleCount', power.get('telemetrySampleCount', 'not reported')))}",
        f"- Campaign average / peak: {markdown(power.get('averageWatts', 'not reported'))} W / {markdown(power.get('peakWatts', 'not reported'))} W",
        f"- Whole-system power included: {'yes' if power.get('includesCpuRamStorageCoolingDisplayOrPsuLosses') else 'no'}",
    ]
    return lines


def render_report(
    first: dict[str, Any], second: dict[str, Any], comparison: dict[str, Any], triage: dict[str, Any],
) -> str:
    complete = comparison.get("status") == "complete"
    first_os = first.get("environment", {}).get("operatingSystem", "First environment")
    second_os = second.get("environment", {}).get("operatingSystem", "Second environment")
    common = comparison.get("commonPasses", [])
    divergences = comparison.get("divergences", [])
    pending = comparison.get("pendingCells", [])
    lines = [
        "# Hardware qualification comparison",
        "",
        "> Engineering evidence. This page applies only to the exact hardware, operating",
        "> systems, drivers, runtime versions, artifacts, and qualification profile below.",
        "",
        f"**Evidence status:** {'complete exact-profile comparison' if complete else 'in progress; not publishable as final evidence'}",
        "",
        "## What was tested",
        "",
        f"- Accelerator: {markdown(comparison.get('accelerator'))}",
        f"- Qualification profile: `{markdown(comparison.get('qualificationProfileId'))}`",
        f"- First cell: {markdown(first_os)}; driver {markdown(first.get('environment', {}).get('driverVersion'))}; {markdown(first.get('runtime', {}).get('provider'))} {markdown(first.get('runtime', {}).get('version'))}",
        f"- Second cell: {markdown(second_os)}; driver {markdown(second.get('environment', {}).get('driverVersion'))}; {markdown(second.get('runtime', {}).get('provider'))} {markdown(second.get('runtime', {}).get('version'))}",
        "",
        "## Result summary",
        "",
        f"- Common task-gate passes: {len(common)}",
        f"- Observed cross-OS outcome divergences: {len(divergences)}",
        f"- Not-run comparison cells: {len(pending)}",
        "",
        "| Model | First cell | Second cell | Interpretation |",
        "| --- | --- | --- | --- |",
    ]
    triage_by_model = {entry["modelId"]: entry for entry in triage["entries"]}
    for cell in comparison.get("cells", []):
        entry = triage_by_model[cell["modelId"]]
        lines.append(
            f"| `{markdown(cell['modelId'])}` | `{markdown(cell['first'])}` | `{markdown(cell['second'])}` | {markdown(entry['classification'])} |"
        )
    lines.extend(["", f"## Power evidence: {markdown(first_os)}", "", *power_lines(first), "",
                  f"## Power evidence: {markdown(second_os)}", "", *power_lines(second), "",
                  "## Limits and decision", "",
                  "- A result is not inherited across operating systems, drivers, runtimes, editor surfaces, or accelerators.",
                  "- GPU-board telemetry is not a whole-system electricity measurement.",
                  "- This evidence does not authorize an automatic model default, support label, runtime change, or download.",
                  "- Failed and not-run cells remain visible and require explicit follow-up evidence.", "",
                  "## Privacy", "",
                  "The inputs declare that they contain no private machine identity, network identity, or raw prompts/responses.", ""])
    return "\n".join(lines)


def atomic_write(path: Path, text: str) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing symlink output: {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.is_symlink():
        raise ValueError(f"refusing symlink temporary output: {temporary}")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--triage-output", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true", help="local preview only")
    args = parser.parse_args()
    try:
        first, second, comparison = (read_object(path) for path in (args.first, args.second, args.comparison))
        if comparison.get("status") != "complete" and not args.allow_incomplete:
            raise ValueError("comparison is incomplete; use --allow-incomplete only for local review")
        triage = build_triage(first, second, comparison)
        report = render_report(first, second, comparison, triage)
        atomic_write(args.triage_output, json.dumps(triage, indent=2, ensure_ascii=False) + "\n")
        atomic_write(args.report_output, report)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
