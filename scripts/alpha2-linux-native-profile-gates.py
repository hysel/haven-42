#!/usr/bin/env python3
"""Report exact Linux package admission prerequisites before native execution.

This tool is effect-free. It does not contact a machine, run a process, download a
runtime, or change selection policy. It ensures every campaign target has an exact
OS identity, a supported system CA layout, and an explicit model-evidence outcome.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PLANNER = _load(
    "alpha2_linux_long_term_planner",
    ROOT / "scripts/plan-alpha2-linux-long-term-validation.py",
)
LINUX = _load("alpha2_linux_admission", ROOT / "scripts/linux_alpha.py")
SETUP = _load("alpha2_linux_setup", ROOT / "scripts/linux_alpha_setup.py")

CA_PATH_BY_FAMILY = {
    "debian": Path("/etc/ssl/certs/ca-certificates.crt"),
    "fedora": Path("/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem"),
    "arch": Path("/etc/ssl/certs/ca-certificates.crt"),
}


class GateError(ValueError):
    """The reviewed native profile matrix is incomplete or inconsistent."""


def _snapshot(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "platform": {
            "operatingSystem": "linux",
            "architecture": "x86_64",
            "logicalProcessors": 8,
            "systemMemoryGiB": 15.5,
            "availableStorageGiB": 40,
            "distributionId": target["distributionId"],
            "distributionVersion": target["distributionVersion"],
            "libcFamily": "glibc",
            "libcVersion": "2.39",
        },
        "accelerators": [{
            "vendor": "NVIDIA",
            "model": "Reviewed 16 GiB NVIDIA profile",
            "memoryGiB": 16,
            "source": "nvidia-smi",
            "driverVersion": "review-required-on-machine",
        }],
    }


def build_report() -> dict[str, Any]:
    contract = PLANNER.load_contract(PLANNER.DEFAULT_CONTRACT)
    allowed_ca_paths = set(SETUP.SYSTEM_CA_BUNDLE_CANDIDATES)
    profiles: list[dict[str, Any]] = []
    for target in contract["targets"]:
        ca_path = CA_PATH_BY_FAMILY[target["caTrustFamily"]]
        if ca_path not in allowed_ca_paths:
            raise GateError(f"missing-ca-path-for-{target['id']}")
        snapshot = _snapshot(target)
        hardware = LINUX.evaluate_hardware(snapshot)
        if hardware["operatingSystemId"] != target["operatingSystemId"]:
            raise GateError(f"os-identity-drift-for-{target['id']}")
        if hardware["decision"] != "candidate":
            raise GateError(f"synthetic-hardware-gate-failed-for-{target['id']}")
        selection = LINUX.select_model(snapshot)
        evidence_ready = selection["automaticExecutionAllowed"] is True
        profiles.append({
            "targetId": target["id"],
            "operatingSystemId": target["operatingSystemId"],
            "caTrustFamily": target["caTrustFamily"],
            "caTrustPathAllowlisted": True,
            "glibcMinimum": hardware["runtimeCompatibility"]["effectiveMinimumVersion"],
            "backendMode": hardware["managedBackendCandidate"],
            "modelEvidenceGate": "ready" if evidence_ready else "qualification-required",
            "selectedModelId": (
                selection["selected"]["id"] if evidence_ready else None
            ),
            "nativeManagedSetupReady": evidence_ready,
        })
    ready = sum(item["nativeManagedSetupReady"] for item in profiles)
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-linux-native-profile-gates",
        "release": contract["release"],
        "targetCount": len(profiles),
        "readyCount": ready,
        "qualificationRequiredCount": len(profiles) - ready,
        "allProfilesReady": ready == len(profiles),
        "profiles": profiles,
        "effects": {
            "networkContacted": False,
            "processStarted": False,
            "fileWritten": False,
            "selectionPolicyChanged": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-ready", action="store_true",
        help="Exit nonzero unless every exact OS profile has admitted model evidence.",
    )
    arguments = parser.parse_args()
    try:
        report = build_report()
    except (GateError, PLANNER.ContractError, LINUX.LinuxAlphaError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["allProfilesReady"] or not arguments.require_ready else 3


if __name__ == "__main__":
    raise SystemExit(main())
