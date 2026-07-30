#!/usr/bin/env python3
"""Review-only text semantics for already-inspected synthetic containers."""

from __future__ import annotations

from io import BytesIO
import importlib.util
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ElementTree
import zipfile


ROOT = Path(__file__).resolve().parent.parent
CONTRACT = json.loads(
    (ROOT / "config/complex-document-semantic-review.json").read_text(encoding="utf-8")
)
INSPECTOR_PATH = ROOT / "scripts/inspect-complex-document-container.py"
SPEC = importlib.util.spec_from_file_location("bounded_container_inspector", INSPECTOR_PATH)
INSPECTOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = INSPECTOR
SPEC.loader.exec_module(INSPECTOR)
LIMITS = CONTRACT["limits"]


class SemanticRejected(ValueError):
    pass


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def depth(root: ElementTree.Element) -> int:
    maximum = 0
    pending = [(root, 1)]
    while pending:
        node, value = pending.pop()
        maximum = max(maximum, value)
        pending.extend((child, value + 1) for child in node)
    return maximum


def selected_parts(names: list[str], format_id: str) -> list[tuple[str, str]]:
    if format_id == "docx":
        result = [("document-body", "word/document.xml")]
        patterns = (
            ("header", r"word/header[0-9]+\.xml"),
            ("footer", r"word/footer[0-9]+\.xml"),
            ("comments", r"word/comments\.xml"),
        )
        for kind, pattern in patterns:
            matches = sorted(
                value for value in names if re.fullmatch(pattern, value, re.I)
            )
            result.extend(
                (f"{kind}-{index}", name)
                for index, name in enumerate(matches, 1)
            )
        return result
    if format_id == "xlsx":
        return [
            (f"worksheet-{index}", name)
            for index, name in enumerate(
                sorted(
                    value
                    for value in names
                    if re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml", value, re.I)
                ),
                1,
            )
        ]
    if format_id == "pptx":
        slides = [
            (f"slide-{index}", name)
            for index, name in enumerate(
                sorted(
                    value
                    for value in names
                    if re.fullmatch(r"ppt/slides/slide[0-9]+\.xml", value, re.I)
                ),
                1,
            )
        ]
        notes = [
            (f"speaker-note-{index}", name)
            for index, name in enumerate(
                sorted(
                    value
                    for value in names
                    if re.fullmatch(r"ppt/notesSlides/notesSlide[0-9]+\.xml", value, re.I)
                ),
                1,
            )
        ]
        return slides + notes
    return [("document-content", "content.xml")]


def clean_text(raw: str) -> str:
    return " ".join(raw.split())


def append_segment(
    segments: list[dict[str, str]],
    source: str,
    kind: str,
    raw: str,
    output_characters: int,
) -> int:
    value = clean_text(raw)
    if not value:
        return output_characters
    if len(value) > LIMITS["maximumSegmentCharacters"]:
        raise SemanticRejected("segment-character-budget-exceeded")
    output_characters += len(value)
    if output_characters > LIMITS["maximumOutputCharacters"]:
        raise SemanticRejected("output-character-budget-exceeded")
    segments.append({"source": source, "kind": kind, "text": value})
    if len(segments) > LIMITS["maximumTextSegments"]:
        raise SemanticRejected("text-segment-budget-exceeded")
    return output_characters


def reject_unsafe_semantics(root: ElementTree.Element, format_id: str) -> None:
    if any(
        local_name(element.tag) == "f"
        or any(local_name(attribute) == "formula" for attribute in element.attrib)
        for element in root.iter()
    ):
        raise SemanticRejected("formula-rejected")
    if format_id == "docx" and any(
        local_name(element.tag) in {"ins", "del", "movefrom", "moveto"}
        for element in root.iter()
    ):
        raise SemanticRejected("tracked-change-rejected")


def docx_values(root: ElementTree.Element, provenance: str):
    if provenance.startswith("comments-"):
        for index, comment in enumerate(
            (value for value in root.iter() if local_name(value.tag) == "comment"), 1
        ):
            text = "".join(
                value.text or ""
                for value in comment.iter()
                if local_name(value.tag) == "t"
            )
            yield f"{provenance}:{index}", "comment-text", text
        return
    kind = "paragraph-text"
    if provenance.startswith("header-"):
        kind = "header-text"
    elif provenance.startswith("footer-"):
        kind = "footer-text"
    for index, paragraph in enumerate(
        (value for value in root.iter() if local_name(value.tag) == "p"), 1
    ):
        text = "".join(
            value.text or ""
            for value in paragraph.iter()
            if local_name(value.tag) == "t"
        )
        in_table = any(
            local_name(ancestor.tag) == "tc"
            for ancestor in root.iter()
            if paragraph in list(ancestor)
        )
        yield (
            f"{provenance}:paragraph-{index}",
            "table-cell-text" if in_table else kind,
            text,
        )


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    except ElementTree.ParseError as error:
        raise SemanticRejected("selected-xml-invalid") from error
    reject_unsafe_semantics(root, "xlsx")
    if depth(root) > LIMITS["maximumXmlNestingDepth"]:
        raise SemanticRejected("xml-depth-budget-exceeded")
    return [
        "".join(
            element.text or ""
            for element in item.iter()
            if local_name(element.tag) == "t"
        )
        for item in root.iter()
        if local_name(item.tag) == "si"
    ]


def xlsx_values(root: ElementTree.Element, provenance: str, shared: list[str]):
    for index, cell in enumerate(
        (value for value in root.iter() if local_name(value.tag) == "c"), 1
    ):
        reference = cell.attrib.get("r") or f"cell-{index}"
        cell_type = cell.attrib.get("t", "")
        if cell_type == "s":
            raw_index = next(
                (
                    value.text
                    for value in cell
                    if local_name(value.tag) == "v"
                ),
                None,
            )
            try:
                shared_index = int(raw_index or "")
                if shared_index < 0:
                    raise ValueError
                text = shared[shared_index]
            except (ValueError, IndexError):
                raise SemanticRejected("shared-string-index-invalid")
            yield f"{provenance}!{reference}", "shared-string", text
            continue
        if cell_type == "inlineStr":
            text = "".join(
                value.text or ""
                for value in cell.iter()
                if local_name(value.tag) == "t"
            )
            yield f"{provenance}!{reference}", "inline-string", text
            continue
        text = next(
            (
                value.text or ""
                for value in cell
                if local_name(value.tag) == "v"
            ),
            "",
        )
        yield f"{provenance}!{reference}", "literal-cell-value", text


def generic_values(root: ElementTree.Element, provenance: str, format_id: str):
    if format_id == "pptx":
        kind = (
            "speaker-note-text"
            if provenance.startswith("speaker-note-")
            else "shape-text"
        )
        for index, element in enumerate(
            (value for value in root.iter() if local_name(value.tag) == "t"), 1
        ):
            yield f"{provenance}:text-{index}", kind, element.text or ""
        return
    for index, element in enumerate(
        (
            value
            for value in root.iter()
            if local_name(value.tag) in {"p", "h"}
        ),
        1,
    ):
        kind = "heading-text" if local_name(element.tag) == "h" else "paragraph-text"
        yield (
            f"{provenance}:{kind}-{index}",
            kind,
            "".join(element.itertext()),
        )


def extract(data: bytes, format_id: str) -> dict[str, object]:
    try:
        INSPECTOR.inspect(data, format_id)
    except INSPECTOR.ContainerRejected as error:
        raise SemanticRejected(f"container-{error}") from error
    with zipfile.ZipFile(BytesIO(data)) as archive:
        parts = selected_parts(archive.namelist(), format_id)
        if not 1 <= len(parts) <= LIMITS["maximumSelectedXmlParts"]:
            raise SemanticRejected("selected-part-budget-exceeded")
        segments: list[dict[str, str]] = []
        output_characters = 0
        shared = shared_strings(archive) if format_id == "xlsx" else []
        for provenance, name in parts:
            try:
                root = ElementTree.fromstring(archive.read(name))
            except (KeyError, ElementTree.ParseError) as error:
                raise SemanticRejected("selected-xml-invalid") from error
            if depth(root) > LIMITS["maximumXmlNestingDepth"]:
                raise SemanticRejected("xml-depth-budget-exceeded")
            reject_unsafe_semantics(root, format_id)
            if format_id == "docx":
                values = docx_values(root, provenance)
            elif format_id == "xlsx":
                values = xlsx_values(root, provenance, shared)
            else:
                values = generic_values(root, provenance, format_id)
            for source, kind, raw in values:
                output_characters = append_segment(
                    segments, source, kind, raw, output_characters
                )
        return {
            "schemaVersion": 1,
            "status": "review-only-semantic-text",
            "format": format_id,
            "segments": segments,
            "contentCharacters": output_characters,
            "runtimeAdmissionGranted": False,
            "providerPayloadAllowed": False,
        }


if __name__ == "__main__":
    print(json.dumps({"status": "review-library-only", "runtimeAdmissionGranted": False}))
