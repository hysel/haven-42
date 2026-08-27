#!/usr/bin/env python3
"""Verify Windows and Linux Alpha 2 packets share one exact source commit."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("candidate-verifier-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WINDOWS = load_module(
    "windows_alpha2_candidate_pair",
    ROOT / "scripts" / "build-windows-alpha2-candidate.py",
)
LINUX = load_module(
    "linux_alpha2_candidate_pair",
    ROOT / "scripts" / "build-linux-alpha2-candidate.py",
)


def verify_pair(
    windows_directory: Path,
    linux_directory: Path,
    expected_commit: str | None = None,
) -> dict[str, object]:
    windows = WINDOWS.verify(windows_directory.resolve())
    linux = LINUX.verify(linux_directory.resolve())
    source_commit = windows.get("sourceCommit")
    if (
        not FULL_COMMIT.fullmatch(str(source_commit))
        or linux.get("sourceCommit") != source_commit
    ):
        raise ValueError("candidate-source-commit-mismatch")
    if expected_commit is not None and (
        not FULL_COMMIT.fullmatch(expected_commit) or expected_commit != source_commit
    ):
        raise ValueError("candidate-unexpected-source-commit")
    if windows.get("knownLimitations") != linux.get("knownLimitations"):
        raise ValueError("candidate-known-limitations-mismatch")
    if (
        windows.get("platform") != "windows-x64"
        or linux.get("platform") != "linux-x64"
        or windows.get("version") != "0.4.0-alpha.2"
        or linux.get("version") != "0.4.0-alpha.2"
        or windows.get("nativeValidationRequired") is not True
        or linux.get("nativeValidationRequired") is not True
        or any(item.get("publicReleaseAllowed") is not False for item in (windows, linux))
        or any(item.get("distributionAuthorized") is not False for item in (windows, linux))
        or any(item.get("productionReady") is not False for item in (windows, linux))
    ):
        raise ValueError("candidate-pair-authority-invalid")
    return {
        "schemaVersion": 1,
        "kind": "alpha2-cross-platform-candidate-pair-verification",
        "version": "0.4.0-alpha.2",
        "sourceCommit": source_commit,
        "candidates": [
            {
                "platform": windows["platform"],
                "archive": windows["archive"],
                "knownLimitations": windows["knownLimitations"],
            },
            {
                "platform": linux["platform"],
                "archive": linux["archive"],
                "knownLimitations": linux["knownLimitations"],
            },
        ],
        "sameSourceCommit": True,
        "candidatePairReadyForNativeValidation": True,
        "nativeValidationComplete": False,
        "publicationAllowed": False,
        "productionReady": False,
    }


def safe_output(value: str) -> Path:
    output = Path(value).resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError("output-must-remain-inside-repository") from error
    if output.exists() and (output.is_symlink() or not output.is_file()):
        raise ValueError("unsafe-output-path")
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windows", required=True)
    parser.add_argument("--linux", required=True)
    parser.add_argument("--expected-commit")
    parser.add_argument("--output")
    args = parser.parse_args()
    report = verify_pair(
        Path(args.windows),
        Path(args.linux),
        args.expected_commit,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        safe_output(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
