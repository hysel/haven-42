#!/usr/bin/env python3
"""Generate one human-readable wiki page per sanitized evidence claim."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "config" / "evidence-catalog.tsv"
DEFAULT_CONTRACT = ROOT / "config" / "capability-evidence-contract.json"
DEFAULT_REGISTRY = ROOT / "config" / "evidence-page-registry.json"
DEFAULT_PAGES = ROOT / "docs" / "evidence-records"
DEFAULT_INDEX = ROOT / "docs" / "wiki-evidence-record-index.md"
DEFAULT_WIKI_MAP = ROOT / "config" / "wiki-sync.tsv"
REPOSITORY_URL = "https://github.com/hysel/haven-42"
GENERATED_SOURCE_PREFIX = "docs/evidence-records/"
INDEX_SOURCE = "docs/wiki-evidence-record-index.md"


class EvidencePageError(RuntimeError):
    pass


def json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidencePageError(f"JSON object expected: {path}")
    return value


def read_catalog(path: Path, expected_columns: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames != expected_columns:
            raise EvidencePageError("evidence catalog columns do not match the contract")
        rows = []
        for number, row in enumerate(reader, 2):
            normalized = {name: str(row.get(name, "")).strip() for name in expected_columns}
            if any(not normalized[name] for name in expected_columns):
                raise EvidencePageError(f"evidence catalog row {number} contains an empty field")
            if any("\n" in value or "\r" in value or "\t" in value for value in normalized.values()):
                raise EvidencePageError(f"evidence catalog row {number} contains unsafe whitespace")
            rows.append(normalized)
    if not rows:
        raise EvidencePageError("evidence catalog is empty")
    return rows


def record_id(row: dict[str, str]) -> str:
    # Keep the page URL stable when a status or explanatory note is refined.
    # A different capability scope or source-evidence path remains a different
    # evidence record.
    identity = {
        name: row[name]
        for name in (
            "schema_version", "area", "subject", "surface", "surface_version",
            "provider", "os", "model", "operation", "validation_mode", "evidence",
        )
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "evidence-" + hashlib.sha256(encoded).hexdigest()[:16]


def markdown_text(value: str) -> str:
    return value.replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")


def display(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").strip().title()


def source_url(path: str) -> str:
    safe = "/".join(part for part in path.split("/") if part not in {"", ".", ".."})
    return f"{REPOSITORY_URL}/blob/main/{safe}"


def page_text(item: dict[str, Any]) -> str:
    row = item["claim"]
    title = markdown_text(row["subject"])
    return f"""# {title}

> Generated evidence page. The canonical machine-readable record is
> `{item['id']}` in `config/evidence-page-registry.json`.

## What this record says

{markdown_text(row['notes'])}

| Result | Value |
| --- | --- |
| Status | `{markdown_text(row['status'])}` |
| Validation method | {markdown_text(display(row['validation_mode']))} |
| Area | {markdown_text(display(row['area']))} |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | {markdown_text(row['surface'])} |
| Surface version | {markdown_text(row['surface_version'])} |
| Provider or runtime | {markdown_text(row['provider'])} |
| Operating system | {markdown_text(row['os'])} |
| Model | {markdown_text(row['model'])} |
| Operation | {markdown_text(display(row['operation']))} |

## Source evidence

[{markdown_text(row['evidence'])}]({source_url(row['evidence'])})

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
"""


def build_items(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    items = []
    seen: set[str] = set()
    for row in rows:
        identifier = record_id(row)
        if identifier in seen:
            raise EvidencePageError("duplicate evidence rows are not allowed")
        seen.add(identifier)
        page_name = f"Evidence-Record-{identifier.removeprefix('evidence-')}.md"
        items.append({
            "id": identifier,
            "claim": row,
            "sourceEvidence": row["evidence"],
            "page": {
                "repositorySource": f"docs/evidence-records/{identifier}.md",
                "wikiPage": page_name,
                "title": row["subject"],
            },
        })
    return sorted(items, key=lambda item: (item["claim"]["area"], item["claim"]["subject"], item["id"]))


def registry_value(catalog: Path, contract: Path, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "haven42-evidence-page-registry",
        "sourceCatalog": "config/evidence-catalog.tsv",
        "sourceContract": "config/capability-evidence-contract.json",
        "catalogSha256": hashlib.sha256(catalog.read_bytes()).hexdigest(),
        "recordCount": len(items),
        "futureAutomaticUpdateUse": {
            "mode": "advisory-evidence-input-only",
            "automaticUpdateActivationAuthorized": False,
            "automaticModelPromotionAuthorized": False,
            "requiresExactCapabilityKeyMatch": True,
            "requiresSignedUpdateMetadata": True,
            "requiresCompatibilityPreflight": True,
            "requiresPostUpdateHealthCheck": True,
            "requiresAutomaticRollback": True,
            "requiresUserPolicy": True,
        },
        "records": items,
    }


def index_text(items: list[dict[str, Any]]) -> str:
    lines = [
        "# Evidence Record Index",
        "",
        "This index gives every sanitized evidence claim its own page. Each page",
        "states exactly what was tested, what passed or remains limited, and what",
        "must not be inferred from the result.",
        "",
        "The pages are generated from `config/evidence-catalog.tsv`. Do not edit",
        "them by hand; update the catalog and run the generator.",
        "",
    ]
    current = None
    for item in items:
        row = item["claim"]
        if row["area"] != current:
            current = row["area"]
            lines.extend([f"## {display(current)}", "", "| Evidence | Status | Tested environment |", "| --- | --- | --- |"])
        wiki_slug = item["page"]["wikiPage"].removesuffix(".md")
        environment = f"{row['os']} · {row['provider']} · {row['model']}"
        lines.append(
            f"| [{markdown_text(row['subject'])}]({REPOSITORY_URL}/wiki/{wiki_slug}) "
            f"| `{markdown_text(row['status'])}` | {markdown_text(environment)} |"
        )
    lines.extend([
        "",
        "## Automatic-update boundary",
        "",
        "`config/evidence-page-registry.json` is the machine-readable input reserved",
        "for future update compatibility checks. Its records are advisory evidence",
        "only and cannot activate an update or change a model default.",
        "",
    ])
    return "\n".join(lines)


def wiki_map_text(path: Path, items: list[dict[str, Any]]) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "source\tpage\ttitle":
        raise EvidencePageError("wiki map header is invalid")
    retained = [
        line for line in lines[1:]
        if line and not line.startswith(GENERATED_SOURCE_PREFIX) and not line.startswith(INDEX_SOURCE + "\t")
    ]
    generated = [f"{INDEX_SOURCE}\tEvidence-Record-Index.md\tEvidence Record Index"]
    generated.extend(
        f"{item['page']['repositorySource']}\t{item['page']['wikiPage']}\t{item['claim']['subject']}"
        for item in items
    )
    return "\n".join([lines[0], *retained, *generated]) + "\n"


def expected_outputs(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[Path, str]]:
    contract = json_object(args.contract)
    columns = contract.get("columns")
    if not isinstance(columns, list) or not all(isinstance(value, str) for value in columns):
        raise EvidencePageError("evidence contract columns are invalid")
    rows = read_catalog(args.catalog, columns)
    items = build_items(rows)
    outputs = {
        args.registry: json.dumps(registry_value(args.catalog, args.contract, items), indent=2) + "\n",
        args.index: index_text(items),
        args.wiki_map: wiki_map_text(args.wiki_map, items),
    }
    outputs.update({args.root / item["page"]["repositorySource"]: page_text(item) for item in items})
    return items, outputs


def generate(args: argparse.Namespace) -> None:
    items, outputs = expected_outputs(args)
    if args.check:
        expected_pages = {path for path in outputs if path.parent == args.pages}
        actual_pages = set(args.pages.glob("evidence-*.md")) if args.pages.is_dir() else set()
        stale = [path for path, content in outputs.items() if not path.is_file() or path.read_text(encoding="utf-8") != content]
        if stale or actual_pages != expected_pages:
            names = ", ".join(str(path) for path in stale[:5]) or "generated page set"
            raise EvidencePageError(f"generated evidence documentation is stale: {names}")
        print(f"Verified {len(items)} current evidence pages and the future-update registry.")
        return
    args.pages.mkdir(parents=True, exist_ok=True)
    for old in args.pages.glob("evidence-*.md"):
        if old.is_file() and not old.is_symlink():
            old.unlink()
    for destination, content in outputs.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    print(f"Generated {len(items)} evidence pages and the future-update registry.")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--root", type=Path, default=ROOT)
    value.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    value.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    value.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    value.add_argument("--pages", type=Path, default=DEFAULT_PAGES)
    value.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    value.add_argument("--wiki-map", type=Path, default=DEFAULT_WIKI_MAP)
    value.add_argument("--check", action="store_true", help="Fail when committed generated outputs are stale")
    return value


if __name__ == "__main__":
    generate(parser().parse_args())
