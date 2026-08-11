#!/usr/bin/env python3
"""Test the effect-free Alpha 2 Linux campaign contract and planner."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/plan-alpha2-linux-long-term-validation.py"
CONTRACT = ROOT / "config/alpha-2-linux-long-term-validation.json"
SPEC = importlib.util.spec_from_file_location("alpha2_linux_long_term", RUNNER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.add(node.module.split(".", 1)[0])
    return values


def rejected(contract: dict, expected_text: str) -> None:
    try:
        MODULE.validate_contract(contract)
    except MODULE.ContractError as exc:
        assert expected_text in str(exc), str(exc)
    else:
        raise AssertionError("Unsafe contract was accepted.")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    MODULE.validate_contract(contract)
    summary = MODULE.describe(contract)
    checks = 1
    assert summary["targetCount"] == 9
    assert summary["cpuTaskCount"] == 45
    assert summary["nvidiaTaskCount"] == 27
    assert summary["modelTaskCount"] == 57
    assert summary["modelSampleCount"] == 171
    assert summary["promotionCandidates"] == ["ubuntu-26-04-gnome", "bazzite-kde"]
    checks += 6

    forbidden_imports = {
        "asyncio",
        "http",
        "paramiko",
        "requests",
        "shutil",
        "socket",
        "subprocess",
        "urllib",
    }
    assert imported_roots(RUNNER).isdisjoint(forbidden_imports)
    source = RUNNER.read_text(encoding="utf-8")
    assert all(token not in source for token in ("shell=True", "os.system", "Popen("))
    checks += 2

    changed = copy.deepcopy(contract)
    changed["safety"]["proxmoxControlAllowed"] = True
    rejected(changed, "safety policy")
    changed = copy.deepcopy(contract)
    changed["safety"]["maximumConcurrentGpuOwners"] = 2
    rejected(changed, "safety policy")
    changed = copy.deepcopy(contract)
    changed["targets"][1]["nvidiaLane"] = "promotion-candidate"
    rejected(changed, "Only Ubuntu 26.04 and Bazzite")
    changed = copy.deepcopy(contract)
    changed["targets"][0]["id"] = "../../host"
    rejected(changed, "safe id")
    changed = copy.deepcopy(contract)
    changed["requiredChecks"].remove("privacy")
    rejected(changed, "validation coverage")
    changed = copy.deepcopy(contract)
    changed["stages"][3]["maximumMinutes"] = 100000
    rejected(changed, "unsafe time limit")
    changed = copy.deepcopy(contract)
    changed["release"] = "latest"
    rejected(changed, "bound to Alpha 2")
    changed = copy.deepcopy(contract)
    changed["modelValidation"]["constraints"]["comparisonEvidenceMayPromote"] = True
    rejected(changed, "reviewed selector policy")
    changed = copy.deepcopy(contract)
    changed["modelValidation"]["constraints"]["protectedProviderDownloadsAllowed"] = True
    rejected(changed, "reviewed selector policy")
    changed = copy.deepcopy(contract)
    changed["modelValidation"]["lanes"][1]["targetScope"] = "all-linux-targets"
    rejected(changed, "lanes changed")
    changed = copy.deepcopy(contract)
    changed["modelValidation"]["selectorPolicyCanonicalSha256"] = "0" * 64
    rejected(changed, "reviewed selector policy")
    changed = copy.deepcopy(contract)
    changed["modelValidation"]["deferredHardwareTiers"][0]["minimumSystemMemoryGiB"] = 16
    rejected(changed, "Deferred hardware tiers")
    changed = copy.deepcopy(contract)
    changed["unexpected"] = True
    rejected(changed, "schemaVersion")
    checks += 13

    with tempfile.TemporaryDirectory() as temporary:
        malformed = Path(temporary) / "contract.json"
        malformed.write_text("{", encoding="utf-8")
        try:
            MODULE.load_contract(malformed)
        except MODULE.ContractError as exc:
            assert "Cannot read campaign contract" in str(exc)
        else:
            raise AssertionError("Malformed JSON was accepted.")
    checks += 1

    combined = json.dumps(contract) + source
    assert "192.168." not in combined
    assert "SHA256:" not in combined
    assert "hostpci" not in combined
    assert "QuadroRTX5000" not in combined
    checks += 4
    print(f"Alpha 2 Linux long-term plan passed {checks} offline safety checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
