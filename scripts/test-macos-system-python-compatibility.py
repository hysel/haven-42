#!/usr/bin/env python3
"""Keep source workflows compatible with the Python 3.9 bundled by macOS."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "scripts", ROOT / "packages", ROOT / "web")


def incompatible_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    failures: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        keywords = {keyword.arg for keyword in node.keywords if keyword.arg is not None}
        if isinstance(node.func, ast.Name) and node.func.id == "zip" and "strict" in keywords:
            failures.append(f"{path.relative_to(ROOT)}:{node.lineno}: zip(strict=) requires Python 3.10")
        if isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "lstat"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "entry"
            ):
                failures.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: os.DirEntry has no lstat method"
                )
            if node.func.attr == "write_text" and "newline" in keywords:
                failures.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: Path.write_text(newline=) requires Python 3.10"
                )
            if node.func.attr == "stat" and "follow_symlinks" in keywords:
                failures.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: Path.stat(follow_symlinks=) requires Python 3.10"
                )
            if node.func.attr == "extractall" and "filter" in keywords:
                failures.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: tarfile.extractall(filter=) requires Python 3.12"
                )
    return failures


def main() -> int:
    files = sorted(path for root in SOURCE_ROOTS for path in root.rglob("*.py"))
    failures = [failure for path in files for failure in incompatible_calls(path)]
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(f"macOS system Python compatibility passed for {len(files)} Python files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
