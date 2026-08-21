#!/usr/bin/env python3
"""Hostile tests for the sanitized llama.cpp distribution result validator."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-alpha2-macos-llamacpp-distribution-result.py"
RESULT = ROOT / "config" / "alpha-2-apple-m4-llamacpp-b10520-distribution-result.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    validator = load(VALIDATOR, "llamacpp_distribution_validator")
    runner = validator.load_runner()
    value = json.loads(RESULT.read_text(encoding="utf-8"))
    validator.validate(value, runner)
    checks = 1
    mutations = (
        lambda item: item.__setitem__("status", "passed"),
        lambda item: item["officialRelease"].__setitem__("assetSha256", "0" * 64),
        lambda item: item["archive"].__setitem__("safePaths", False),
        lambda item: item["runtime"].__setitem__("relocatedLaunchPassed", False),
        lambda item: item["runtime"].__setitem__("runtimeLaunchRequiresSystemPython", True),
        lambda item: item["platformTrust"].__setitem__("publicDistributionTrusted", True),
        lambda item: item["authority"].__setitem__("runtimeAdmissionGranted", True),
    )
    for mutate in mutations:
        candidate = copy.deepcopy(value)
        mutate(candidate)
        try:
            validator.validate(candidate, runner)
        except validator.ResultError:
            checks += 1
        else:
            raise AssertionError("Unsafe distribution evidence was accepted.")
    print(f"Apple llama.cpp distribution result validator tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
