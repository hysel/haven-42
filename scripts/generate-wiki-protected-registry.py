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
from dataclasses import dataclass, field
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
    match_mode: str = "case-sensitive"
    syntax: str = field(default="", compare=False)


@dataclass(frozen=True, order=True)
class MultiSourceContract:
    sources: tuple[str, ...]
    pattern: str
    test: str
    variable: str
    line: int
    match_mode: str = "case-sensitive"
    syntax: str = field(default="", compare=False)


@dataclass(frozen=True, order=True)
class GeneratedContentContract:
    source: str
    format_description: str
    test: str
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
    results: set[Binding] = set()
    for record in records:
        if not is_markdown_source(record["source"]):
            continue
        syntax = record.get("syntax", "powershell-content-expression")
        results.add(
            Binding(
                source=record["source"],
                pattern=record["pattern"],
                test=record["test"],
                variable=record["variable"],
                line=int(record["line"]),
                match_mode=record.get(
                    "matchMode",
                    "case-insensitive" if syntax.endswith(("imatch", "ilike")) else "case-sensitive",
                ),
                syntax=syntax,
            )
        )
    return results


SHELL_FUNCTION = re.compile(r"(?m)^(test_[A-Za-z0-9_]+)\(\)\s*\{")
SHELL_ASSIGNMENT = re.compile(
    r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)=[\"']\$REPO_ROOT/([^\"']+\.md)[\"']"
)
SHELL_GREP = re.compile(
    r"(?P<neg>!\s*)?grep\s+-(?P<options>[A-Za-z]*q[A-Za-z]*)\s+(?:--\s+)?"
    r"(?P<quote>[\"'])(?P<pattern>.*?)(?P=quote)\s+"
    r"(?P<tquote>[\"'])(?P<target>.*?)(?P=tquote)"
)
SHELL_PYTHON_HEREDOC = re.compile(
    r"(?m)^\s*python(?:3)?(?:\s+[^\n]*?)?\s+<<"
    r"(?P<delimiter>['\"]*(?P<tag>[A-Za-z_][A-Za-z0-9_]*)['\"]*)[^\n]*$"
)


def shell_contracts() -> tuple[set[Binding], set[MultiSourceContract]]:
    path = ROOT / "scripts" / "test-pack.shared.sh"
    text = path.read_text(encoding="utf-8")
    starts = list(SHELL_FUNCTION.finditer(text))
    results: set[Binding] = set()
    multi_source_results: set[MultiSourceContract] = set()
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
                    syntax="shell-grep-positive",
                )
            )
        for heredoc in SHELL_PYTHON_HEREDOC.finditer(body):
            body_start = heredoc.end() + (1 if body[heredoc.end() :].startswith("\n") else 0)
            terminator = re.search(
                rf"(?m)^\s*{re.escape(heredoc.group('tag'))}\s*$", body[body_start:]
            )
            if terminator is None:
                continue
            python_text = body[body_start : body_start + terminator.start()]
            try:
                tree = ast.parse(python_text, filename=str(path))
            except SyntaxError:
                continue
            line_offset = text.count("\n", 0, start.start() + body_start)
            bindings, multi_source = bindings_from_python_tree(
                tree,
                test_path="scripts/test-pack.shared.sh",
                fixed_test_name=start.group(1),
                line_offset=line_offset,
                variable_prefix="embedded-python:",
                initial_paths={"ROOT": "", "root": ""},
            )
            results.update(bindings)
            multi_source_results.update(multi_source)
    return results, multi_source_results


def shell_bindings() -> set[Binding]:
    return shell_contracts()[0]


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


def content_sources(
    node: ast.AST, paths: dict[str, str], contents: dict[str, frozenset[str]]
) -> frozenset[str]:
    if isinstance(node, ast.Name):
        return contents.get(node.id, frozenset())
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "read" and node.args:
            value = path_value(node.args[0], paths)
            return frozenset({value}) if value and is_markdown_source(value) else frozenset()
        if isinstance(node.func, ast.Attribute) and node.func.attr == "read_text":
            value = path_value(node.func.value, paths)
            return frozenset({value}) if value and is_markdown_source(value) else frozenset()
    referenced: set[str] = set()
    for name in ast.walk(node):
        if isinstance(name, ast.Name):
            referenced.update(contents.get(name.id, frozenset()))
    return frozenset(referenced)


def enclosing_function(parents: dict[ast.AST, ast.AST], node: ast.AST) -> str:
    cursor = parents.get(node)
    while cursor is not None:
        if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cursor.name
        cursor = parents.get(cursor)
    return "module"


def enclosing_loop_values(
    parents: dict[ast.AST, ast.AST],
    node: ast.AST,
    variable_name: str,
    string_collections: dict[str, tuple[str, ...]],
) -> list[str]:
    cursor = parents.get(node)
    while cursor is not None:
        if isinstance(cursor, (ast.For, ast.AsyncFor)) and isinstance(cursor.target, ast.Name):
            if cursor.target.id == variable_name:
                if isinstance(cursor.iter, (ast.Tuple, ast.List, ast.Set)):
                    return [
                        item.value
                        for item in cursor.iter.elts
                        if isinstance(item, ast.Constant) and isinstance(item.value, str)
                    ]
                if isinstance(cursor.iter, ast.Name):
                    return list(string_collections.get(cursor.iter.id, ()))
        cursor = parents.get(cursor)
    return []


def enclosing_generator_values(
    parents: dict[ast.AST, ast.AST], node: ast.AST, variable_name: str
) -> list[str]:
    """Resolve a generator target backed by an inline literal collection."""

    cursor = parents.get(node)
    while cursor is not None:
        if isinstance(cursor, ast.GeneratorExp):
            for comprehension in cursor.generators:
                if (
                    isinstance(comprehension.target, ast.Name)
                    and comprehension.target.id == variable_name
                    and isinstance(comprehension.iter, (ast.Tuple, ast.List, ast.Set))
                ):
                    return [
                        item.value
                        for item in comprehension.iter.elts
                        if isinstance(item, ast.Constant) and isinstance(item.value, str)
                    ]
        cursor = parents.get(cursor)
    return []


def expression_match_mode(node: ast.AST) -> str:
    """Identify source normalization that makes a membership check case-insensitive."""

    for child in ast.walk(node):
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr in {"lower", "casefold"}
            and not child.args
        ):
            return "case-insensitive"
    return "case-sensitive"


def normalized_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"lower", "casefold"}
        and not node.args
        and isinstance(node.func.value, ast.Name)
    ):
        return node.func.value.id
    return None


def source_contains_pattern(source: str, pattern: str, match_mode: str) -> bool:
    source_text = (ROOT / source).read_text(encoding="utf-8")
    normalized_text = " ".join(source_text.split())
    if match_mode == "case-insensitive":
        pattern = pattern.casefold()
        return pattern in source_text.casefold() or pattern in normalized_text.casefold()
    return pattern in source_text or pattern in normalized_text


def condition_memberships(
    condition: ast.AST,
    parents: dict[ast.AST, ast.AST],
    paths: dict[str, str],
    contents: dict[str, frozenset[str]],
    string_collections: dict[str, tuple[str, ...]],
) -> list[tuple[str, frozenset[str], str, int, str]]:
    """Return literal membership checks with their asserted source attribution."""

    results: list[tuple[str, frozenset[str], str, int, str]] = []
    for compare in ast.walk(condition):
        if not isinstance(compare, ast.Compare):
            continue
        if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.In):
            continue
        if len(compare.comparators) != 1:
            continue

        sources = content_sources(compare.comparators[0], paths, contents)
        if not sources:
            continue
        variable = ast.unparse(compare.comparators[0])
        patterns: list[str] = []
        if isinstance(compare.left, ast.Constant) and isinstance(compare.left.value, str):
            patterns = [compare.left.value]
        else:
            left_name = normalized_name(compare.left)
            if left_name is None:
                continue
            patterns = enclosing_loop_values(
                parents, compare, left_name, string_collections
            )
            if not patterns:
                patterns = enclosing_generator_values(parents, compare, left_name)
        match_mode = (
            "case-insensitive"
            if "case-insensitive"
            in {expression_match_mode(compare.left), expression_match_mode(compare.comparators[0])}
            else "case-sensitive"
        )
        for pattern in patterns:
            results.append((pattern, sources, variable, compare.lineno, match_mode))
    return results


def assertion_helper_names(tree: ast.AST) -> set[str]:
    """Find local helpers whose first argument is enforced with AssertionError."""

    names: set[str] = set()
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not function.args.args:
            continue
        condition_name = function.args.args[0].arg
        for branch in ast.walk(function):
            if not isinstance(branch, ast.If):
                continue
            if not (
                isinstance(branch.test, ast.UnaryOp)
                and isinstance(branch.test.op, ast.Not)
                and isinstance(branch.test.operand, ast.Name)
                and branch.test.operand.id == condition_name
            ):
                continue
            if any(
                isinstance(item, ast.Raise)
                and isinstance(item.exc, ast.Call)
                and isinstance(item.exc.func, ast.Name)
                and item.exc.func.id == "AssertionError"
                for item in ast.walk(branch)
            ):
                names.add(function.name)
                break
    return names


def bindings_from_python_tree(
    tree: ast.AST,
    *,
    test_path: str,
    fixed_test_name: str | None = None,
    line_offset: int = 0,
    variable_prefix: str = "",
    initial_paths: dict[str, str] | None = None,
) -> tuple[set[Binding], set[MultiSourceContract]]:
    results: set[Binding] = set()
    multi_source_results: set[MultiSourceContract] = set()
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    assertion_helpers = assertion_helper_names(tree)
    paths: dict[str, str] = dict(initial_paths or {"ROOT": ""})
    contents: dict[str, frozenset[str]] = {}

    assignments = sorted(
        (node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign))),
        key=lambda node: node.lineno,
    )
    string_collections: dict[str, tuple[str, ...]] = {}
    for assignment in assignments:
        targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
        if not isinstance(assignment.value, (ast.Tuple, ast.List, ast.Set)):
            continue
        values = tuple(
            item.value
            for item in assignment.value.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
        if len(values) != len(assignment.value.elts):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                string_collections[target.id] = values
    iteration_limit = len(assignments) + 1
    for _ in range(iteration_limit):
        changed = False
        for node in assignments:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                possible_path = path_value(value, paths)
                if possible_path and paths.get(target.id) != possible_path:
                    paths[target.id] = possible_path
                    changed = True
        if not changed:
            break
    else:
        raise RuntimeError(
            f"Path attribution did not converge for {test_path} after {iteration_limit} iterations."
        )

    for _ in range(iteration_limit):
        next_contents: dict[str, frozenset[str]] = {}
        for node in assignments:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                possible_contents = content_sources(value, paths, contents)
                if possible_contents:
                    next_contents[target.id] = possible_contents
        if next_contents == contents:
            break
        contents = next_contents
    else:
        raise RuntimeError(
            f"Content-source attribution did not converge for {test_path} after {iteration_limit} iterations."
        )

    for node in ast.walk(tree):
        candidates: list[tuple[str, frozenset[str], str, int, str]] = []
        syntax = ""
        if isinstance(node, ast.Assert):
            candidates = condition_memberships(
                node.test, parents, paths, contents, string_collections
            )
            syntax = "python-native-assert-membership"
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in assertion_helpers
            and node.args
        ):
            candidates = condition_memberships(
                node.args[0], parents, paths, contents, string_collections
            )
            syntax = "python-custom-helper-membership"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"assertIn", "assertRegex"} and len(node.args) >= 2:
                if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    sources = content_sources(node.args[1], paths, contents)
                    if sources:
                        candidates = [
                            (
                                node.args[0].value,
                                sources,
                                ast.unparse(node.args[1]),
                                node.lineno,
                                expression_match_mode(node.args[1]),
                            )
                        ]
                        syntax = f"python-unittest-{node.func.attr}"
        for pattern, sources, variable, line, match_mode in candidates:
            markdown_sources = tuple(sorted(source for source in sources if is_markdown_source(source)))
            matching_sources = tuple(
                source
                for source in markdown_sources
                if source_contains_pattern(source, pattern, match_mode)
            )
            if len(markdown_sources) > 1 and matching_sources:
                test_name = fixed_test_name or enclosing_function(parents, node)
                multi_source_results.add(
                    MultiSourceContract(
                        sources=markdown_sources,
                        pattern=pattern,
                        test=f"{test_path}::{test_name}",
                        variable=f"{variable_prefix}{variable}",
                        line=line + line_offset,
                        match_mode=match_mode,
                        syntax=(
                            f"shell-embedded-{syntax}"
                            if variable_prefix == "embedded-python:"
                            else syntax
                        ),
                    )
                )
                continue
            for source in matching_sources:
                test_name = fixed_test_name or enclosing_function(parents, node)
                results.add(
                    Binding(
                        source=source,
                        pattern=pattern,
                        test=f"{test_path}::{test_name}",
                        variable=f"{variable_prefix}{variable}",
                        line=line + line_offset,
                        match_mode=match_mode,
                        syntax=(
                            f"shell-embedded-{syntax}"
                            if variable_prefix == "embedded-python:"
                            else syntax
                        ),
                    )
                )
    return results, multi_source_results


def python_contracts() -> tuple[set[Binding], set[MultiSourceContract]]:
    results: set[Binding] = set()
    multi_source_results: set[MultiSourceContract] = set()
    for path in sorted((ROOT / "scripts").glob("test-*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        bindings, multi_source = bindings_from_python_tree(
            tree, test_path=f"scripts/{path.name}"
        )
        results.update(bindings)
        multi_source_results.update(multi_source)
    return results, multi_source_results


def python_bindings() -> set[Binding]:
    return python_contracts()[0]


def generated_content_contracts() -> tuple[GeneratedContentContract, ...]:
    """Document dynamic source contracts that cannot be represented as fixed prose."""

    return (
        GeneratedContentContract(
            "examples/amd-rx6800-windows-model-qualification.md",
            "The report must contain the SHA-256 recorded for the raw telemetry provenance object.",
            "scripts/test-alpha2-amd-rx6800-windows-qualification-result.py::main",
            101,
        ),
        GeneratedContentContract(
            "docs/wiki-model-power-evidence.md",
            "For every hardware record, the page must contain `{model} {memoryGiB} GiB`.",
            "scripts/test-novice-experience.py::main",
            108,
        ),
        GeneratedContentContract(
            "docs/windows-alpha-release.md",
            "The page must contain the release tag and the candidate source commit, artifact name, byte length, and SHA-256 from the release record.",
            "scripts/test-windows-alpha-release-record.py::main",
            149,
        ),
        GeneratedContentContract(
            "docs/evidence-dashboard.md",
            "The summary table must contain `| Evidence records | {EvidenceCount} |` from the generated assurance report.",
            "scripts/test-pack.shared.sh::test_local_web_mvp",
            2620,
        ),
        GeneratedContentContract(
            "docs/evidence-dashboard.md",
            "The summary table must contain `| Distinct model-field values | {ModelCount} |` from the generated assurance report.",
            "scripts/test-pack.shared.sh::test_local_web_mvp",
            2621,
        ),
        GeneratedContentContract(
            "docs/evidence-dashboard.md",
            "The status table must contain one `| {Status} | {Count} |` row for every generated status-count record.",
            "scripts/test-pack.shared.sh::test_local_web_mvp",
            2623,
        ),
        GeneratedContentContract(
            "docs/evidence-dashboard.md",
            "The surface-readiness table must contain one `| {Name} |` row for every generated surface record.",
            "scripts/test-pack.shared.sh::test_local_web_mvp",
            2625,
        ),
    )


def render(
    bindings: Iterable[Binding],
    multi_source_contracts: Iterable[MultiSourceContract],
    generated_contracts: Iterable[GeneratedContentContract],
) -> str:
    bindings = set(bindings)
    multi_source_contracts = set(multi_source_contracts)
    generated_contracts = set(generated_contracts)
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
        "> `scripts/test-pack.shared.sh`, and every `scripts/test-*.py` file on 2026-08-26.",
        f"> The result contains {len(set(bindings))} verified source/test-pattern bindings across",
        f"> {len(grouped)} source groups. Every entry records the assertion variable and source line.",
        "",
        "### Covered assertion syntax",
        "",
        "The extractor recognizes every positive source-text contract currently used by the test pack:",
        "PowerShell content-variable and direct-inline `Get-Content` checks with `-match` or `-like`,",
        "PowerShell `.Contains(...)`, positive shell `grep`, Python assertions embedded in shell",
        "heredocs, Python native `assert ... in ...`, `unittest.assertIn`, `unittest.assertRegex`,",
        "and local custom assertion helpers that reject false membership checks. Loop-provided",
        "and generator-provided literals and `[regex]::Escape(...)` operands are expanded to",
        "their concrete patterns. Case-normalized comparisons are recorded as case-insensitive.",
        "Negative/absence assertions (`-notmatch`, `! grep`, `assertNotIn`, and `assertNotRegex`)",
        "are audited but intentionally excluded because they prohibit text rather than protect it.",
        "Other equality, numeric, exception, and mock-call assertions do not enforce source prose.",
        "",
    ]
    for (page, source), items in sorted(grouped.items(), key=lambda item: item[0]):
        lines.extend([f"### {page}", "", f"Source: `{source}`", ""])
        for item in sorted(set(items), key=lambda value: (value.pattern.lower(), value.test, value.line)):
            phrase = html.escape(item.pattern, quote=False)
            test = html.escape(item.test, quote=False)
            variable = html.escape(item.variable, quote=False)
            mode = "; case-insensitive" if item.match_mode == "case-insensitive" else ""
            lines.append(
                f"- <code>{phrase}</code> — <code>{test}</code>, "
                f"asserted against <code>{variable}</code> at line {item.line}{mode}"
            )
        lines.append("")
    lines.extend(
        [
            "### Multi-source protected strings — satisfy in any listed source",
            "",
            "These tests combine several Markdown sources before checking a phrase. The phrase must",
            "remain present in at least one listed source, but the test does not assign ownership to",
            "one specific file. Do not treat these as ordinary single-source bindings.",
            "",
        ]
    )
    for item in sorted(multi_source_contracts):
        phrase = html.escape(item.pattern, quote=False)
        sources = ", ".join(f"<code>{html.escape(source, quote=False)}</code>" for source in item.sources)
        test = html.escape(item.test, quote=False)
        mode = "case-insensitive; " if item.match_mode == "case-insensitive" else ""
        lines.append(
            f"- <code>{phrase}</code> — any of {sources}; {mode}<code>{test}</code>, line {item.line}"
        )
    lines.extend(
        [
            "",
            "## Generated-content contracts",
            "",
            "These checks protect generated values or document structure, not fixed prose. Editors may",
            "reword surrounding explanations, but must preserve the described output format and regenerate",
            "the page from its authoritative data when those values change.",
            "",
        ]
    )
    for item in sorted(generated_contracts):
        lines.append(
            f"- <code>{html.escape(item.source, quote=False)}</code> — "
            f"{html.escape(item.format_description, quote=False)} "
            f"(<code>{html.escape(item.test, quote=False)}</code>, line {item.line})"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument(
        "--style-guide",
        type=Path,
        help="Preserve the style guide preamble and replace its protected-string section",
    )
    args = parser.parse_args()
    shell_single, shell_multi = shell_contracts()
    python_single, python_multi = python_contracts()
    extracted = powershell_bindings() | shell_single | python_single
    multi_source = shell_multi | python_multi
    canonical: dict[tuple[str, str, str, str], Binding] = {}
    for item in extracted:
        key = (item.source, item.pattern, item.test, item.match_mode)
        if key not in canonical or item.line < canonical[key].line:
            canonical[key] = item
    bindings = set(canonical.values())
    generated = generated_content_contracts()
    rendered = render(bindings, multi_source, generated)
    if args.style_guide:
        style_text = args.style_guide.read_text(encoding="utf-8")
        marker = "## Protected strings — do not reword"
        preamble = style_text.split(marker, 1)[0].rstrip()
        rendered = f"{preamble}\n\n{rendered}" if preamble else rendered
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered)
    if args.json_output:
        with args.json_output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(
                    {
                        "bindings": [
                        {
                            "recordType": "single-source",
                            "source": item.source,
                            "pattern": item.pattern,
                            "test": item.test,
                            "variable": item.variable,
                            "line": item.line,
                            "matchMode": item.match_mode,
                            "syntax": item.syntax,
                        }
                        for item in sorted(bindings)
                        ],
                        "multiSourceContracts": [
                            {
                                "recordType": "multi-source",
                                "sources": list(item.sources),
                                "pattern": item.pattern,
                                "test": item.test,
                                "variable": item.variable,
                                "line": item.line,
                                "matchMode": item.match_mode,
                                "syntax": item.syntax,
                            }
                            for item in sorted(multi_source)
                        ],
                        "generatedContentContracts": [
                            {
                                "recordType": "generated-content",
                                "source": item.source,
                                "format": item.format_description,
                                "test": item.test,
                                "line": item.line,
                            }
                            for item in sorted(generated)
                        ],
                    },
                    indent=2,
                )
                + "\n"
            )
    print(
        json.dumps(
            {
                "bindings": len(bindings),
                "multiSourceContracts": len(multi_source),
                "generatedContentContracts": len(generated),
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
