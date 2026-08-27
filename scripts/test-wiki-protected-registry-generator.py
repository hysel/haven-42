#!/usr/bin/env python3
"""Reverse-audit Python protected-string assertions against generated bindings."""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "generate-wiki-protected-registry.py"


def load_generator():
    specification = importlib.util.spec_from_file_location("wiki_registry_generator", GENERATOR_PATH)
    if specification is None or specification.loader is None:
        raise RuntimeError("Could not load protected-string registry generator")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def path_value(node: ast.AST, paths: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return paths.get(node.id)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = path_value(node.left, paths)
        right = path_value(node.right, paths)
        if left is not None and right is not None:
            return f"{left}/{right}".lstrip("/")
    return None


def source_values(
    node: ast.AST, paths: dict[str, str], contents: dict[str, frozenset[str]]
) -> frozenset[str]:
    if isinstance(node, ast.Name):
        return contents.get(node.id, frozenset())
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "read" and node.args:
            value = path_value(node.args[0], paths)
            return frozenset({value}) if value else frozenset()
        if isinstance(node.func, ast.Attribute) and node.func.attr == "read_text":
            value = path_value(node.func.value, paths)
            return frozenset({value}) if value else frozenset()
    referenced: set[str] = set()
    for name in ast.walk(node):
        if isinstance(name, ast.Name):
            referenced.update(contents.get(name.id, frozenset()))
    return frozenset(referenced)


def assertion_helpers(tree: ast.AST) -> set[str]:
    helpers: set[str] = set()
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) or not function.args.args:
            continue
        condition_name = function.args.args[0].arg
        for branch in ast.walk(function):
            if not isinstance(branch, ast.If):
                continue
            rejects_false = (
                isinstance(branch.test, ast.UnaryOp)
                and isinstance(branch.test.op, ast.Not)
                and isinstance(branch.test.operand, ast.Name)
                and branch.test.operand.id == condition_name
            )
            raises_assertion = any(
                isinstance(item, ast.Raise)
                and isinstance(item.exc, ast.Call)
                and isinstance(item.exc.func, ast.Name)
                and item.exc.func.id == "AssertionError"
                for item in ast.walk(branch)
            )
            if rejects_false and raises_assertion:
                helpers.add(function.name)
                break
    return helpers


def enclosing_function(parents: dict[ast.AST, ast.AST], node: ast.AST) -> str:
    cursor = parents.get(node)
    while cursor is not None:
        if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cursor.name
        cursor = parents.get(cursor)
    return "module"


def loop_strings(
    parents: dict[ast.AST, ast.AST],
    node: ast.AST,
    name: str,
    string_collections: dict[str, tuple[str, ...]],
) -> list[str]:
    cursor = parents.get(node)
    while cursor is not None:
        if (
            isinstance(cursor, (ast.For, ast.AsyncFor))
            and isinstance(cursor.target, ast.Name)
            and cursor.target.id == name
            and isinstance(cursor.iter, (ast.Tuple, ast.List, ast.Set))
        ):
            return [item.value for item in cursor.iter.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)]
        if (
            isinstance(cursor, (ast.For, ast.AsyncFor))
            and isinstance(cursor.target, ast.Name)
            and cursor.target.id == name
            and isinstance(cursor.iter, ast.Name)
        ):
            return list(string_collections.get(cursor.iter.id, ()))
        cursor = parents.get(cursor)
    return []


def generator_strings(parents: dict[ast.AST, ast.AST], node: ast.AST, name: str) -> list[str]:
    cursor = parents.get(node)
    while cursor is not None:
        if isinstance(cursor, ast.GeneratorExp):
            for comprehension in cursor.generators:
                if (
                    isinstance(comprehension.target, ast.Name)
                    and comprehension.target.id == name
                    and isinstance(comprehension.iter, (ast.Tuple, ast.List, ast.Set))
                ):
                    return [
                        item.value
                        for item in comprehension.iter.elts
                        if isinstance(item, ast.Constant) and isinstance(item.value, str)
                    ]
        cursor = parents.get(cursor)
    return []


def match_mode(node: ast.AST) -> str:
    return (
        "case-insensitive"
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr in {"lower", "casefold"}
            and not child.args
            for child in ast.walk(node)
        )
        else "case-sensitive"
    )


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


def source_matches(root: Path, source: str, pattern: str, mode: str) -> bool:
    text = (root / source).read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    if mode == "case-insensitive":
        return pattern.casefold() in text.casefold() or pattern.casefold() in normalized.casefold()
    return pattern in text or pattern in normalized


def expected_python_bindings(
    generator,
) -> tuple[set[object], set[object], list[str], int, int, set[str]]:
    expected: set[object] = set()
    expected_multi: set[object] = set()
    unresolved: list[str] = []
    helper_calls = 0
    helper_memberships = 0
    helper_files: set[str] = set()
    for path in sorted((ROOT / "scripts").glob("test-*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        helpers = assertion_helpers(tree)
        paths: dict[str, str] = {"ROOT": ""}
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
            if len(values) == len(assignment.value.elts):
                for target in targets:
                    if isinstance(target, ast.Name):
                        string_collections[target.id] = values
        for _ in range(len(assignments) + 1):
            changed = False
            for assignment in assignments:
                targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
                for target in targets:
                    if not isinstance(target, ast.Name):
                        continue
                    candidate_path = path_value(assignment.value, paths)
                    if candidate_path and paths.get(target.id) != candidate_path:
                        paths[target.id] = candidate_path
                        changed = True
            if not changed:
                break

        for _ in range(len(assignments) + 1):
            next_contents: dict[str, frozenset[str]] = {}
            for assignment in assignments:
                targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
                for target in targets:
                    if not isinstance(target, ast.Name):
                        continue
                    candidate_sources = source_values(assignment.value, paths, contents)
                    if candidate_sources:
                        next_contents[target.id] = candidate_sources
            if next_contents == contents:
                break
            contents = next_contents

        test_path = f"scripts/{path.name}"
        for assertion in ast.walk(tree):
            condition = None
            if isinstance(assertion, ast.Assert):
                condition = assertion.test
            elif (
                isinstance(assertion, ast.Call)
                and isinstance(assertion.func, ast.Name)
                and assertion.func.id in helpers
                and assertion.args
            ):
                condition = assertion.args[0]
                helper_calls += 1
                helper_files.add(test_path)
            if condition is None:
                continue
            condition_compares = [
                compare
                for compare in ast.walk(condition)
                if isinstance(compare, ast.Compare)
                and len(compare.ops) == 1
                and isinstance(compare.ops[0], ast.In)
                and len(compare.comparators) == 1
            ]
            if (
                isinstance(assertion, ast.Call)
                and isinstance(assertion.func, ast.Name)
                and assertion.func.id in helpers
            ):
                helper_memberships += len(condition_compares)
            for compare in condition_compares:
                sources = source_values(compare.comparators[0], paths, contents)
                patterns: list[str] = []
                if isinstance(compare.left, ast.Constant) and isinstance(compare.left.value, str):
                    patterns = [compare.left.value]
                else:
                    left_name = normalized_name(compare.left)
                    if left_name is None:
                        continue
                    patterns = loop_strings(
                        parents, compare, left_name, string_collections
                    )
                    if not patterns:
                        patterns = generator_strings(parents, compare, left_name)
                if not sources:
                    continue
                markdown_sources = tuple(sorted(source for source in sources if generator.is_markdown_source(source)))
                mode = (
                    "case-insensitive"
                    if "case-insensitive"
                    in {match_mode(compare.left), match_mode(compare.comparators[0])}
                    else "case-sensitive"
                )
                for pattern in patterns:
                    matching_sources = tuple(
                        source for source in markdown_sources if source_matches(ROOT, source, pattern, mode)
                    )
                    if len(markdown_sources) > 1 and matching_sources:
                        expected_multi.add(
                            generator.MultiSourceContract(
                                sources=markdown_sources,
                                pattern=pattern,
                                test=f"{test_path}::{enclosing_function(parents, assertion)}",
                                variable=ast.unparse(compare.comparators[0]),
                                line=compare.lineno,
                                match_mode=mode,
                            )
                        )
                        continue
                    for source in matching_sources:
                        expected.add(
                            generator.Binding(
                                source=source,
                                pattern=pattern,
                                test=f"{test_path}::{enclosing_function(parents, assertion)}",
                                variable=ast.unparse(compare.comparators[0]),
                                line=compare.lineno,
                                match_mode=mode,
                            )
                        )
            if (
                isinstance(assertion, ast.Call)
                and isinstance(assertion.func, ast.Attribute)
                and assertion.func.attr in {"assertIn", "assertRegex"}
                and len(assertion.args) >= 2
                and isinstance(assertion.args[0], ast.Constant)
                and isinstance(assertion.args[0].value, str)
            ):
                for source in source_values(assertion.args[1], paths, contents):
                    if not generator.is_markdown_source(source):
                        continue
                    pattern = assertion.args[0].value
                    mode = match_mode(assertion.args[1])
                    if not source_matches(ROOT, source, pattern, mode):
                        continue
                    expected.add(
                        generator.Binding(
                            source=source,
                            pattern=pattern,
                            test=f"{test_path}::{enclosing_function(parents, assertion)}",
                            variable=ast.unparse(assertion.args[1]),
                            line=assertion.lineno,
                            match_mode=mode,
                        )
                    )
    return expected, expected_multi, unresolved, helper_calls, helper_memberships, helper_files


def main() -> int:
    generator = load_generator()
    shell_text = (ROOT / "scripts" / "test-pack.shared.sh").read_text(encoding="utf-8")
    heredoc_starts = [
        line
        for line in shell_text.splitlines()
        if re.match(r"^\s*python(?:3)?\b.*<<", line)
    ]
    heredoc_matches = list(generator.SHELL_PYTHON_HEREDOC.finditer(shell_text))
    if len(heredoc_matches) != len(heredoc_starts) or not any(
        match.group("delimiter") == "''PY''" for match in heredoc_matches
    ):
        print(
            "HEREDOC INVENTORY MISMATCH: "
            f"{len(heredoc_matches)} extracted vs {len(heredoc_starts)} present; "
            "shell quote-concatenation coverage missing"
        )
        return 1
    actual, actual_multi = generator.python_contracts()
    expected, expected_multi, unresolved, helper_calls, helper_memberships, helper_files = expected_python_bindings(generator)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    missing_multi = sorted(expected_multi - actual_multi)
    unexpected_multi = sorted(actual_multi - expected_multi)
    if missing or unexpected or missing_multi or unexpected_multi or unresolved:
        for label, values in (
            ("MISSING", missing),
            ("UNEXPECTED", unexpected),
            ("MISSING MULTI-SOURCE", missing_multi),
            ("UNEXPECTED MULTI-SOURCE", unexpected_multi),
            ("UNRESOLVED", unresolved),
        ):
            for value in values:
                print(f"{label}: {value}")
        return 1
    all_bindings = (
        generator.powershell_bindings()
        | generator.shell_bindings()
        | actual
    )
    required = {
        (
            "docs/product-ui-first-slice.md",
            "What do you want to do?",
            "scripts/test-pack.shared.sh::test_product_ui_first_slice",
            "shell-embedded-python-native-assert-membership",
        ),
        (
            "docs/progressive-onboarding.md",
            "Advanced mode is control, not a bypass",
            "scripts/test-pack.ps1::product UI first slice is registry-backed and fail closed",
            "powershell-inline-imatch",
        ),
        (
            "README.md",
            "[code signing policy](code-signing-policy.md)",
            "scripts/test-code-signing-readiness.py::main",
            "python-custom-helper-membership",
        ),
        (
            "docs/writing-model-evaluation.md",
            "No candidate under comparative evaluation in this document is a product default",
            "scripts/test-pack.shared.sh::test_local_web_mvp",
            "shell-embedded-python-native-assert-membership",
        ),
    }
    observed = {(item.source, item.pattern, item.test, item.syntax) for item in all_bindings}
    absent = sorted(required - observed)
    if absent:
        for value in absent:
            print(f"MISSING CROSS-LANGUAGE PATTERN: {value}")
        return 1
    required_multi = {
        (
            ("AI.md", "CONTRIBUTING.md", "STYLEGUIDE.md"),
            "novice-first",
            "scripts/test-novice-experience.py::main",
            "case-insensitive",
        ),
        (
            ("AI.md", "CONTRIBUTING.md", "STYLEGUIDE.md"),
            "clearly labelled **Advanced**",
            "scripts/test-novice-experience.py::main",
            "case-insensitive",
        ),
        (
            ("AI.md", "CONTRIBUTING.md", "STYLEGUIDE.md"),
            "plain language",
            "scripts/test-novice-experience.py::main",
            "case-insensitive",
        ),
    }
    observed_multi = {
        (item.sources, item.pattern, item.test, item.match_mode) for item in actual_multi
    }
    absent_multi = sorted(required_multi - observed_multi)
    if absent_multi:
        for value in absent_multi:
            print(f"MISSING MULTI-SOURCE CONTRACT: {value}")
        return 1
    generated = generator.generated_content_contracts()
    if len(generated) != 7:
        print(f"GENERATED-CONTENT CONTRACT COUNT MISMATCH: expected 7, got {len(generated)}")
        return 1
    syntax_inventory = {item.syntax for item in all_bindings}
    required_syntax = {
        "python-native-assert-membership",
        "python-custom-helper-membership",
        "shell-grep-positive",
        "shell-embedded-python-native-assert-membership",
        "powershell-variable-imatch",
        "powershell-variable-ilike",
        "powershell-variable-contains",
        "powershell-inline-imatch",
    }
    missing_syntax = sorted(required_syntax - syntax_inventory)
    if missing_syntax:
        print("MISSING ASSERTION SYNTAX: " + ", ".join(missing_syntax))
        return 1
    print(
        "Protected-string Python reverse audit passed: "
        f"{len(actual)} bindings, {len(actual_multi)} multi-source contracts, "
        f"{len(generated)} generated-content contracts, {helper_calls} custom assertion-helper calls in "
        f"{len(helper_files)} files, {helper_memberships} helper membership operands, 0 unresolved; "
        f"cross-language inventory covers {len(syntax_inventory)} extracted syntax categories"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
