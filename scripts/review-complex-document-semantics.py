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
        return [("document-body", "word/document.xml")]
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
        return [
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
    return [("document-content", "content.xml")]


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
        for provenance, name in parts:
            try:
                root = ElementTree.fromstring(archive.read(name))
            except (KeyError, ElementTree.ParseError) as error:
                raise SemanticRejected("selected-xml-invalid") from error
            if depth(root) > LIMITS["maximumXmlNestingDepth"]:
                raise SemanticRejected("xml-depth-budget-exceeded")
            if any(
                local_name(element.tag) == "f"
                or any(local_name(attribute) == "formula" for attribute in element.attrib)
                for element in root.iter()
            ):
                raise SemanticRejected("formula-rejected")
            if format_id in {"docx", "xlsx", "pptx"}:
                values = [
                    element.text or ""
                    for element in root.iter()
                    if local_name(element.tag) == "t"
                ]
            else:
                values = [
                    "".join(element.itertext())
                    for element in root.iter()
                    if local_name(element.tag) in {"p", "h"}
                ]
            for raw in values:
                value = " ".join(raw.split())
                if not value:
                    continue
                if len(value) > LIMITS["maximumSegmentCharacters"]:
                    raise SemanticRejected("segment-character-budget-exceeded")
                output_characters += len(value)
                if output_characters > LIMITS["maximumOutputCharacters"]:
                    raise SemanticRejected("output-character-budget-exceeded")
                segments.append({"source": provenance, "text": value})
                if len(segments) > LIMITS["maximumTextSegments"]:
                    raise SemanticRejected("text-segment-budget-exceeded")
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
