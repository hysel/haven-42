#!/usr/bin/env python3
"""Hostile tests for offline inert research page-text extraction."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/offline_research_page_text.py"
SPEC = importlib.util.spec_from_file_location("page_text", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def rejects(content_type, data, reason: str) -> None:
    try:
        MODULE.extract(content_type, data)
    except MODULE.PageRejected as exc:
        assert str(exc) == reason, (str(exc), reason)
    else:
        raise AssertionError(f"accepted hostile page: {reason}")


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".", 1)[0])
    return result


def main() -> int:
    checks = 0
    plain = MODULE.extract("text/plain; charset=utf-8", b"First line\nSecond line")
    assert [value["text"] for value in plain["segments"]] == [
        "First line",
        "Second line",
    ]
    assert plain["networkUsed"] is False and plain["runtimeAdmissionGranted"] is False
    checks += 3
    html = MODULE.extract(
        "text/html",
        b"<main><h1>Title</h1><p>Safe <strong>fixture</strong><br>text.</p></main>",
    )
    assert [value["text"] for value in html["segments"]] == [
        "Title",
        "Safe fixture",
        "text.",
    ]
    assert html["remoteReferencesRetained"] is False
    checks += 2

    hostile = [
        ("application/pdf", b"%PDF", "content-type-not-allowlisted"),
        ("text/plain", b"", "page-byte-budget"),
        ("text/plain", b"x" * 262145, "page-byte-budget"),
        ("text/plain", b"a\x00b", "page-nul"),
        ("text/plain", b"\xff", "page-utf8"),
        ("text/html", b"<!doctype html><p>x</p>", "html-doctype"),
        ("text/html", b"<script>alert(1)</script>", "html-tag-not-allowlisted"),
        ("text/html", b"<iframe></iframe>", "html-tag-not-allowlisted"),
        ("text/html", b"<img src='https://tracker.invalid/x'>", "html-tag-not-allowlisted"),
        ("text/html", b"<svg><text>x</text></svg>", "html-tag-not-allowlisted"),
        ("text/html", b"<form><input></form>", "html-tag-not-allowlisted"),
        ("text/html", b"<p>unclosed", "html-structure"),
        ("text/html", b"<p></div>", "html-structure"),
        ("text/html", b"<?unsafe test?><p>x</p>", "html-processing-instruction"),
        ("text/html", b"<p>   </p>", "page-empty"),
    ]
    for content_type, data, reason in hostile:
        rejects(content_type, data, reason)
        checks += 1

    deep = ("<div>" * 65 + "x" + "</div>" * 65).encode()
    rejects("text/html", deep, "html-depth-budget")
    many = ("\n".join(f"line {index}" for index in range(501))).encode()
    rejects("text/plain", many, "page-segment-budget")
    checks += 2

    assert not any(MODULE.CONTRACT["authority"].values())
    assert imported_roots(PATH).isdisjoint(
        {"socket", "requests", "urllib", "http", "subprocess", "webbrowser"}
    )
    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css", ".json"}
    )
    assert "offline_research_page_text" not in runtime
    package_spec = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert package_spec.count('"offline_research_page_text"') == 1
    page_transport = (
        ROOT / "scripts/web_research_native_page_transport.py"
    ).read_text(encoding="utf-8")
    assert "import offline_research_page_text as PAGE_TEXT" in page_transport
    checks += 5
    print(f"Offline research page-text foundation passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
