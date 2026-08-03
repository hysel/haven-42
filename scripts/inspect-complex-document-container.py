#!/usr/bin/env python3
"""Review-only bounded Office/OpenDocument ZIP/XML container inspection."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import PurePosixPath
import re
import xml.etree.ElementTree as ElementTree
import zipfile


class ContainerRejected(ValueError):
    pass


REQUIRED = {
    "docx": {"[Content_Types].xml", "_rels/.rels", "word/document.xml"},
    "xlsx": {"[Content_Types].xml", "_rels/.rels", "xl/workbook.xml"},
    "pptx": {"[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml"},
    "odt": {"mimetype", "content.xml", "META-INF/manifest.xml"},
    "ods": {"mimetype", "content.xml", "META-INF/manifest.xml"},
    "odp": {"mimetype", "content.xml", "META-INF/manifest.xml"},
}
ODF_TYPES = {
    "odt": b"application/vnd.oasis.opendocument.text",
    "ods": b"application/vnd.oasis.opendocument.spreadsheet",
    "odp": b"application/vnd.oasis.opendocument.presentation",
}
MAX_INPUT = 8_388_608
MAX_ENTRIES = 256
MAX_MEMBER = 2_097_152
MAX_EXPANDED = 8_388_608
MAX_RATIO = 20
MAX_XML = 1_048_576


def local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1].casefold()


def unsafe_reference(value: str, allow_fragment: bool) -> bool:
    candidate = value.strip()
    if not candidate:
        return True
    if any(ord(character) < 32 for character in candidate):
        return True
    if allow_fragment and candidate.startswith("#"):
        return False
    path = candidate.split("#", 1)[0].split("?", 1)[0]
    return (
        "%" in path
        or "\\" in path
        or path.startswith("/")
        or path.startswith("//")
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path) is not None
        or any(part == ".." for part in path.split("/"))
    )


def safe_name(name: str) -> str:
    parts = name.split("/")
    if (
        not name
        or "\x00" in name
        or "\\" in name
        or name.startswith("/")
        or name.endswith("/")
        or "//" in name
        or re.match(r"^[A-Za-z]:", name)
        or any(part in {"", ".", ".."} for part in parts)
        or PurePosixPath(name).is_absolute()
    ):
        raise ContainerRejected("unsafe-member-name")
    return name


def inspect(data: bytes, format_id: str) -> dict[str, object]:
    if format_id not in REQUIRED:
        raise ContainerRejected("unsupported-format")
    if not 1 <= len(data) <= MAX_INPUT or not data.startswith(b"PK\x03\x04"):
        raise ContainerRejected("invalid-container")
    try:
        archive = zipfile.ZipFile(BytesIO(data))
    except (zipfile.BadZipFile, OSError) as error:
        raise ContainerRejected("invalid-container") from error
    with archive:
        entries = archive.infolist()
        if not 1 <= len(entries) <= MAX_ENTRIES:
            raise ContainerRejected("entry-budget-exceeded")
        names: set[str] = set()
        expanded = 0
        for entry in entries:
            name = safe_name(entry.filename)
            identity = name.casefold()
            if identity in names:
                raise ContainerRejected("duplicate-member")
            names.add(identity)
            if entry.flag_bits & 1:
                raise ContainerRejected("encrypted-container")
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ContainerRejected("symlink-member")
            if entry.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                raise ContainerRejected("unsupported-compression")
            if entry.file_size > MAX_MEMBER:
                raise ContainerRejected("member-budget-exceeded")
            expanded += entry.file_size
            if expanded > MAX_EXPANDED:
                raise ContainerRejected("expanded-budget-exceeded")
            if entry.file_size > max(1, entry.compress_size) * MAX_RATIO:
                raise ContainerRejected("expansion-ratio-exceeded")
            lowered = name.casefold()
            if "vbaproject" in lowered or lowered.endswith((".docm", ".xlsm", ".pptm")):
                raise ContainerRejected("macro-content")
            if (
                "/embeddings/" in f"/{lowered}"
                or "/activex/" in f"/{lowered}"
                or lowered.startswith("customui/")
                or lowered.startswith("object ")
            ):
                raise ContainerRejected("embedded-object")
        if not {name.casefold() for name in REQUIRED[format_id]}.issubset(names):
            raise ContainerRejected("format-identity-mismatch")
        if format_id in ODF_TYPES:
            first = entries[0]
            if first.filename != "mimetype" or first.compress_type != zipfile.ZIP_STORED:
                raise ContainerRejected("odf-mimetype-placement")
            if archive.read(first) != ODF_TYPES[format_id]:
                raise ContainerRejected("format-identity-mismatch")
        for entry in entries:
            lowered = entry.filename.casefold()
            if not lowered.endswith((".xml", ".rels")):
                continue
            if entry.file_size > MAX_XML:
                raise ContainerRejected("xml-budget-exceeded")
            value = archive.read(entry)
            upper = value.upper()
            if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
                raise ContainerRejected("active-xml")
            if b"VBAPROJECT" in upper or b"MACROENABLED" in upper:
                raise ContainerRejected("macro-content")
            try:
                root = ElementTree.fromstring(value)
            except ElementTree.ParseError as error:
                raise ContainerRejected("malformed-xml") from error
            if lowered.endswith(".rels"):
                for element in root.iter():
                    attributes = {
                        local_name(key): item for key, item in element.attrib.items()
                    }
                    target = attributes.get("target")
                    if (
                        attributes.get("targetmode", "").strip().casefold() == "external"
                        or target is not None and unsafe_reference(target, False)
                    ):
                        raise ContainerRejected("external-relationship")
            if format_id in ODF_TYPES:
                for element in root.iter():
                    for key, target in element.attrib.items():
                        if local_name(key) == "href" and unsafe_reference(target, True):
                            raise ContainerRejected("external-relationship")
        return {
            "schemaVersion": 1,
            "status": "candidate-safe-metadata",
            "format": format_id,
            "entryCount": len(entries),
            "expandedBytes": expanded,
            "contentExtracted": False,
            "runtimeAdmissionGranted": False,
        }


if __name__ == "__main__":
    print(json.dumps({"status": "review-library-only", "runtimeAdmissionGranted": False}))
