#!/usr/bin/env python3
"""Generate review-only pypdf compliance evidence outside the package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "config" / "pdf-parser-prospective-package-evidence.json"
LOCK = ROOT / "config" / "pdf-parser-artifact-lock.json"
WHEEL = ROOT / "dist" / "local-review" / "pdf-parser-candidate" / "pypdf-6.14.2-py3-none-any.whl"
OUTPUT = ROOT / "dist" / "local-review" / "pdf-parser-prospective-package-evidence"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(64 * 1024):
            value.update(chunk)
    return value.hexdigest()


def write_exact(path: Path, data: bytes) -> None:
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise RuntimeError("unsafe-output-entry")
    path.write_bytes(data)


def generate() -> dict[str, str]:
    plan = load(PLAN)
    lock = load(LOCK)
    if (
        plan["status"] != "prospective-evidence-dependency-not-admitted"
        or any(plan["generation"].values())
        or any(plan["authority"].values())
    ):
        raise RuntimeError("unsafe-prospective-plan")
    if WHEEL.is_symlink() or not WHEEL.is_file():
        raise RuntimeError("candidate-artifact-unavailable")
    if (
        WHEEL.stat().st_size != lock["artifact"]["sizeBytes"]
        or digest_file(WHEEL) != lock["artifact"]["sha256"]
    ):
        raise RuntimeError("candidate-artifact-mismatch")
    if OUTPUT.exists() and (
        OUTPUT.is_symlink()
        or (hasattr(OUTPUT, "is_junction") and OUTPUT.is_junction())
        or not OUTPUT.is_dir()
    ):
        raise RuntimeError("unsafe-output-directory")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    allowed = {"dependency-inventory.json", "THIRD-PARTY-NOTICES.txt", "sbom.cdx.json"}
    if any(path.name not in allowed or not path.is_file() for path in OUTPUT.iterdir()):
        raise RuntimeError("unexpected-output-entry")

    with zipfile.ZipFile(WHEEL) as archive:
        license_bytes = archive.read(lock["license"]["path"])
    if digest(license_bytes) != lock["license"]["sha256"]:
        raise RuntimeError("candidate-license-mismatch")

    component = plan["component"]
    inventory = {
        "schemaVersion": 1,
        "status": "review-only-not-package-evidence",
        "components": [{
            "name": component["name"],
            "version": component["version"],
            "scope": "candidate-only",
            "artifact": component["artifact"],
            "sha256": component["artifactSha256"],
            "mandatoryDependencies": [],
            "extrasSelected": [],
            "packageIncluded": False,
            "runtimeAdmitted": False,
        }],
    }
    notices = (
        f"{plan['thirdPartyNoticePlan']['heading']}\n\n"
        + "\n".join(plan["thirdPartyNoticePlan"]["copyrightNotices"])
        + "\n\n"
        + license_bytes.decode("utf-8").rstrip()
        + "\n"
    )
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": "urn:uuid:00000000-0000-4000-8000-000000000042",
        "version": 1,
        "metadata": {
            "properties": [
                {"name": "haven42:evidence-status", "value": "review-only-not-package-evidence"},
                {"name": "haven42:runtime-admitted", "value": "false"},
            ]
        },
        "components": [{
            "type": component["type"],
            "name": component["name"],
            "version": component["version"],
            "purl": component["purl"],
            "scope": "excluded",
            "hashes": [{"alg": "SHA-256", "content": component["artifactSha256"]}],
            "licenses": [{"license": {"id": component["license"]}}],
            "properties": [
                {"name": "haven42:review-status", "value": plan["sbomPlan"]["reviewStatusProperty"]},
                {"name": "haven42:package-included", "value": "false"},
            ],
        }],
    }
    outputs = {
        "dependency-inventory.json": (json.dumps(inventory, indent=2) + "\n").encode(),
        "THIRD-PARTY-NOTICES.txt": notices.encode(),
        "sbom.cdx.json": (json.dumps(sbom, indent=2) + "\n").encode(),
    }
    for name, data in outputs.items():
        write_exact(OUTPUT / name, data)
    return {name: digest(data) for name, data in outputs.items()}


if __name__ == "__main__":
    values = generate()
    print(f"Generated {len(values)} review-only prospective evidence files; package admission remains false.")
