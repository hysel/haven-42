#!/usr/bin/env python3
"""Create deterministic inert Office/OpenDocument container review fixtures."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import warnings
import zipfile


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "dist" / "local-review" / "complex-document-hostile-corpus"
STAMP = (2026, 1, 1, 0, 0, 0)


def archive(entries: list[tuple]) -> bytes:
    stream = BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(stream, "w") as output:
            for value in entries:
                name, content, compression = value[:3]
                info = zipfile.ZipInfo(name, STAMP)
                info.compress_type = compression
                info.external_attr = value[3] if len(value) == 4 else 0o100600 << 16
                output.writestr(info, content)
    return stream.getvalue()


def docx(extra: list[tuple[str, bytes, int]] | None = None) -> bytes:
    entries = [
        ("[Content_Types].xml", b"<Types/>", zipfile.ZIP_DEFLATED),
        ("_rels/.rels", b"<Relationships/>", zipfile.ZIP_DEFLATED),
        ("word/document.xml", b"<w:document xmlns:w='urn:w'><w:t>safe</w:t></w:document>", zipfile.ZIP_DEFLATED),
    ]
    return archive(entries + (extra or []))


def odt(extra: list[tuple[str, bytes, int]] | None = None, mimetype: bytes = b"application/vnd.oasis.opendocument.text") -> bytes:
    entries = [
        ("mimetype", mimetype, zipfile.ZIP_STORED),
        ("content.xml", b"<office:document xmlns:office='urn:office'>safe</office:document>", zipfile.ZIP_DEFLATED),
        ("META-INF/manifest.xml", b"<manifest/>", zipfile.ZIP_DEFLATED),
    ]
    return archive(entries + (extra or []))


def encrypted_flag(data: bytes) -> bytes:
    value = bytearray(data)
    local = value.find(b"PK\x03\x04")
    central = value.find(b"PK\x01\x02")
    if local < 0 or central < 0:
        raise RuntimeError("fixture-zip-structure")
    value[local + 6:local + 8] = (int.from_bytes(value[local + 6:local + 8], "little") | 1).to_bytes(2, "little")
    value[central + 8:central + 10] = (int.from_bytes(value[central + 8:central + 10], "little") | 1).to_bytes(2, "little")
    return bytes(value)


def cases() -> dict[str, bytes]:
    rel = b"<Relationships><Relationship TargetMode='External' Target='https://example.invalid'/></Relationships>"
    return {
        "safe.docx": docx(),
        "safe.odt": odt(),
        "traversal.docx": docx([("../escape.xml", b"x", zipfile.ZIP_DEFLATED)]),
        "duplicate.docx": docx([("word/document.xml", b"duplicate", zipfile.ZIP_DEFLATED)]),
        "macro.docx": docx([("word/vbaProject.bin", b"macro", zipfile.ZIP_DEFLATED)]),
        "external.docx": docx([("word/_rels/document.xml.rels", rel, zipfile.ZIP_DEFLATED)]),
        "embedded.docx": docx([("word/embeddings/object1.bin", b"object", zipfile.ZIP_DEFLATED)]),
        "activex.docx": docx([("word/activeX/activeX1.bin", b"control", zipfile.ZIP_DEFLATED)]),
        "symlink.docx": docx([("word/link.xml", b"target", zipfile.ZIP_STORED, 0o120777 << 16)]),
        "malformed-xml.docx": docx([("word/styles.xml", b"<styles>", zipfile.ZIP_DEFLATED)]),
        "encrypted.docx": encrypted_flag(docx()),
        "expansion.docx": docx([("word/large.xml", b"A" * 200_000, zipfile.ZIP_DEFLATED)]),
        "doctype.odt": odt([("styles.xml", b"<!DOCTYPE x [<!ENTITY y 'z'>]><x>&y;</x>", zipfile.ZIP_DEFLATED)]),
        "external.odt": odt([("styles.xml", b"<x xmlns:xlink='urn:xlink' xlink:href='https://example.invalid'/>", zipfile.ZIP_DEFLATED)]),
        "embedded.odt": odt([("Object 1/content.xml", b"<object/>", zipfile.ZIP_DEFLATED)]),
        "mimetype-confusion.odt": odt(mimetype=b"application/vnd.oasis.opendocument.spreadsheet"),
    }


def generate() -> list[Path]:
    if OUTPUT.exists() and (
        OUTPUT.is_symlink()
        or (hasattr(OUTPUT, "is_junction") and OUTPUT.is_junction())
        or not OUTPUT.is_dir()
    ):
        raise RuntimeError("unsafe-output-directory")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected = set(cases())
    if any(path.name not in expected or not path.is_file() or path.is_symlink() for path in OUTPUT.iterdir()):
        raise RuntimeError("unexpected-output-entry")
    paths = []
    for name, content in cases().items():
        path = OUTPUT / name
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise RuntimeError("unsafe-output-entry")
        path.write_bytes(content)
        paths.append(path)
    return paths


if __name__ == "__main__":
    print(f"Created {len(generate())} inert complex-document review fixtures.")
