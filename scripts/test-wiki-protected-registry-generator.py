#!/usr/bin/env python3
"""Reverse-audit Python protected-string assertions against generated bindings."""

from __future__ import annotations

import ast
import importlib.util
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


def loop_strings(parents: dict[ast.AST, ast.AST], node: ast.AST, name: str) -> list[str]:
    cursor = parents.get(node)
    while cursor is not None:
        if (
            isinstance(cursor, (ast.For, ast.AsyncFor))
            and isinstance(cursor.target, ast.Name)
            and cursor.target.id == name
            and isinstance(cursor.iter, (ast.Tuple, ast.List, ast.Set))
        ):
            return [
                item.value
                for item in cursor.iter.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
        cursor = parents.get(cursor)
    return []


def expected_python_bindings(
    generator,
) -> tuple[set[object], list[str], int, int, set[str]]:
    expected: set[object] = set()
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
                elif isinstance(compare.left, ast.Name):
                    patterns = loop_strings(parents, compare, compare.left.id)
                if not sources:
                    continue
                for source in sources:
                    if not generator.is_markdown_source(source):
                        continue
                    source_text = (ROOT / source).read_text(encoding="utf-8")
                    for pattern in patterns:
                        if pattern not in source_text and pattern not in " ".join(source_text.split()):
                            continue
                        expected.add(
                            generator.Binding(
                                source=source,
                                pattern=pattern,
                                test=f"{test_path}::{enclosing_function(parents, assertion)}",
                                variable=ast.unparse(compare.comparators[0]),
                                line=compare.lineno,
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
                    source_text = (ROOT / source).read_text(encoding="utf-8")
                    if pattern not in source_text and pattern not in " ".join(source_text.split()):
                        continue
                    expected.add(
                        generator.Binding(
                            source=source,
                            pattern=pattern,
                            test=f"{test_path}::{enclosing_function(parents, assertion)}",
                            variable=ast.unparse(assertion.args[1]),
                            line=assertion.lineno,
                        )
                    )
    return expected, unresolved, helper_calls, helper_memberships, helper_files


def main() -> int:
    generator = load_generator()
    actual = generator.python_bindings()
    expected, unresolved, helper_calls, helper_memberships, helper_files = expected_python_bindings(generator)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected or unresolved:
        for label, values in (("MISSING", missing), ("UNEXPECTED", unexpected), ("UNRESOLVED", unresolved)):
            for value in values:
                print(f"{label}: {value}")
        return 1
    print(
        "Protected-string Python reverse audit passed: "
        f"{len(actual)} bindings, {helper_calls} custom assertion-helper calls in "
        f"{len(helper_files)} files, {helper_memberships} helper membership operands, 0 unresolved"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
