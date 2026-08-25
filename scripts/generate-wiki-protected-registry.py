#!/usr/bin/env python3
"""Generate wiki protected-string bindings with assertion-to-source attribution."""

from __future__ import annotations

import argparse
import ast
import csv
import html
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
WIKI_MAP = ROOT / "config" / "wiki-sync.tsv"


@dataclass(frozen=True, order=True)
class Binding:
    source: str
    pattern: str
    test: str
    variable: str
    line: int


def wiki_pages() -> dict[str, str]:
    with WIKI_MAP.open(encoding="utf-8", newline="") as handle:
        return {row["source"]: row["page"] for row in csv.DictReader(handle, delimiter="\t")}


def is_markdown_source(source: str) -> bool:
    return source.lower().endswith(".md") and (ROOT / source).is_file()


def powershell_bindings() -> set[Binding]:
    helper = ROOT / "scripts" / "extract-powershell-protected-bindings.ps1"
    completed = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(helper),
            "-Path",
            str(ROOT / "scripts" / "test-pack.ps1"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    records = json.loads(completed.stdout or "[]")
    if isinstance(records, dict):
        records = [records]
    return {
        Binding(
            source=record["source"],
            pattern=record["pattern"],
            test=record["test"],
            variable=record["variable"],
            line=int(record["line"]),
        )
        for record in records
        if is_markdown_source(record["source"])
    }


SHELL_FUNCTION = re.compile(r"(?m)^(test_[A-Za-z0-9_]+)\(\)\s*\{")
SHELL_ASSIGNMENT = re.compile(
    r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)=[\"']\$REPO_ROOT/([^\"']+\.md)[\"']"
)
SHELL_GREP = re.compile(
    r"(?P<neg>!\s*)?grep\s+-(?P<options>[A-Za-z]*q[A-Za-z]*)\s+(?:--\s+)?"
    r"(?P<quote>[\"'])(?P<pattern>.*?)(?P=quote)\s+"
    r"(?P<tquote>[\"'])(?P<target>.*?)(?P=tquote)"
)


def shell_bindings() -> set[Binding]:
    path = ROOT / "scripts" / "test-pack.shared.sh"
    text = path.read_text(encoding="utf-8")
    starts = list(SHELL_FUNCTION.finditer(text))
    results: set[Binding] = set()
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        body = re.sub(
            r"\\\r?\n",
            lambda match: " " * len(match.group(0)),
            text[start.start() : end],
        )
        variables = {match.group(1): match.group(2) for match in SHELL_ASSIGNMENT.finditer(body)}
        for match in SHELL_GREP.finditer(body):
            if match.group("neg"):
                continue
            target = match.group("target")
            source = None
            if target.startswith("$REPO_ROOT/"):
                source = target[len("$REPO_ROOT/") :]
            elif re.fullmatch(r"\$[A-Za-z_][A-Za-z0-9_]*", target):
                source = variables.get(target[1:])
            if not source or not is_markdown_source(source):
                continue
            absolute_offset = start.start() + match.start()
            line = text.count("\n", 0, absolute_offset) + 1
            results.add(
                Binding(
                    source=source,
                    pattern=match.group("pattern"),
                    test=f"scripts/test-pack.shared.sh::{start.group(1)}",
                    variable=target,
                    line=line,
                )
            )
    return results


def path_value(node: ast.AST, paths: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return paths.get(node.id)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = path_value(node.left, paths)
        right = path_value(node.right, paths)
        if left is None or right is None:
            return None
        return f"{left}/{right}".lstrip("/")
    return None


def content_source(node: ast.AST, paths: dict[str, str], contents: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return contents.get(node.id)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "read" and node.args:
            value = path_value(node.args[0], paths)
            return value if value and is_markdown_source(value) else None
        if isinstance(node.func, ast.Attribute) and node.func.attr == "read_text":
            value = path_value(node.func.value, paths)
            return value if value and is_markdown_source(value) else None
    referenced = {contents[name.id] for name in ast.walk(node) if isinstance(name, ast.Name) and name.id in contents}
    return next(iter(referenced)) if len(referenced) == 1 else None


def enclosing_function(parents: dict[ast.AST, ast.AST], node: ast.AST) -> str:
    cursor = parents.get(node)
    while cursor is not None:
        if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cursor.name
        cursor = parents.get(cursor)
    return "module"


def enclosing_loop_values(
    parents: dict[ast.AST, ast.AST], node: ast.AST, variable_name: str
) -> list[str]:
    cursor = parents.get(node)
    while cursor is not None:
        if isinstance(cursor, (ast.For, ast.AsyncFor)) and isinstance(cursor.target, ast.Name):
            if cursor.target.id == variable_name and isinstance(cursor.iter, (ast.Tuple, ast.List, ast.Set)):
                values = []
                for item in cursor.iter.elts:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        values.append(item.value)
                return values
        cursor = parents.get(cursor)
    return []


def python_bindings() -> set[Binding]:
    results: set[Binding] = set()
    for path in sorted((ROOT / "scripts").glob("test-*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        paths: dict[str, str] = {"ROOT": ""}
        contents: dict[str, str] = {}

        assignments = sorted(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.Assign, ast.AnnAssign))
            ),
            key=lambda node: node.lineno,
        )
        changed = True
        while changed:
            changed = False
            for node in assignments:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                value = node.value
                for target in targets:
                    if not isinstance(target, ast.Name):
                        continue
                    possible_path = path_value(value, paths)
                    if (
                        possible_path
                        and possible_path.lower().endswith(".md")
                        and paths.get(target.id) != possible_path
                    ):
                        paths[target.id] = possible_path
                        changed = True
                    possible_content = content_source(value, paths, contents)
                    if possible_content and contents.get(target.id) != possible_content:
                        contents[target.id] = possible_content
                        changed = True

        test_path = f"scripts/{path.name}"
        for node in ast.walk(tree):
            pattern = None
            source = None
            variable = ""
            patterns: list[str] = []
            if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
                compare = node.test
                if len(compare.ops) == 1 and isinstance(compare.ops[0], ast.In) and len(compare.comparators) == 1:
                    if isinstance(compare.left, ast.Constant) and isinstance(compare.left.value, str):
                        patterns = [compare.left.value]
                        source = content_source(compare.comparators[0], paths, contents)
                        variable = ast.unparse(compare.comparators[0])
                    elif isinstance(compare.left, ast.Name):
                        patterns = enclosing_loop_values(parents, node, compare.left.id)
                        source = content_source(compare.comparators[0], paths, contents)
                        variable = ast.unparse(compare.comparators[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"assertIn", "assertRegex"} and len(node.args) >= 2:
                    if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        patterns = [node.args[0].value]
                        source = content_source(node.args[1], paths, contents)
                        variable = ast.unparse(node.args[1])
            if patterns and source and is_markdown_source(source):
                source_text = (ROOT / source).read_text(encoding="utf-8")
                for pattern in patterns:
                    if pattern in source_text or pattern in " ".join(source_text.split()):
                        results.add(
                            Binding(
                                source=source,
                                pattern=pattern,
                                test=f"{test_path}::{enclosing_function(parents, node)}",
                                variable=variable,
                                line=node.lineno,
                            )
                        )
    return results


def render(bindings: Iterable[Binding]) -> str:
    pages = wiki_pages()
    grouped: dict[tuple[str, str], list[Binding]] = {}
    for binding in bindings:
        page = pages.get(binding.source, f"Repository-only: {binding.source}")
        grouped.setdefault((page, binding.source), []).append(binding)

    lines = [
        "## Protected strings — do not reword",
        "",
        "Some repository tests treat the following text as an interface contract. A voice or",
        "structure edit must preserve these substrings or test patterns exactly. If behavior",
        "changes, update the implementation, source page, and enforcing test together; do not",
        "silently rewrite one side. Patterns below are shown exactly as the tests search for them,",
        "so a backslash may be a regular-expression escape rather than visible wiki text.",
        "",
        "> Regenerated with assertion-to-source dataflow attribution from `scripts/test-pack.ps1`,",
        "> `scripts/test-pack.shared.sh`, and every `scripts/test-*.py` file on 2026-08-25.",
        f"> The result contains {len(set(bindings))} verified source/test-pattern bindings across",
        f"> {len(grouped)} source groups. Every entry records the assertion variable and source line.",
        "",
    ]
    for (page, source), items in sorted(grouped.items(), key=lambda item: item[0]):
        lines.extend([f"### {page}", "", f"Source: `{source}`", ""])
        for item in sorted(set(items), key=lambda value: (value.pattern.lower(), value.test, value.line)):
            phrase = html.escape(item.pattern, quote=False)
            test = html.escape(item.test, quote=False)
            variable = html.escape(item.variable, quote=False)
            lines.append(
                f"- <code>{phrase}</code> — <code>{test}</code>, "
                f"asserted against <code>{variable}</code> at line {item.line}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    extracted = powershell_bindings() | shell_bindings() | python_bindings()
    canonical: dict[tuple[str, str, str], Binding] = {}
    for item in extracted:
        key = (item.source, item.pattern, item.test)
        if key not in canonical or item.line < canonical[key].line:
            canonical[key] = item
    bindings = set(canonical.values())
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render(bindings))
    if args.json_output:
        with args.json_output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(
                    [
                        {
                            "source": item.source,
                            "pattern": item.pattern,
                            "test": item.test,
                            "variable": item.variable,
                            "line": item.line,
                        }
                        for item in sorted(bindings)
                    ],
                    indent=2,
                )
                + "\n"
            )
    print(json.dumps({"bindings": len(bindings), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
