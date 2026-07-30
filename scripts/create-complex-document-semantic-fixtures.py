#!/usr/bin/env python3
"""Create deterministic semantic Office/OpenDocument review fixtures."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import warnings
import zipfile


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "dist/local-review/complex-document-semantic-corpus"
STAMP = (2026, 1, 1, 0, 0, 0)
DEFLATED = zipfile.ZIP_DEFLATED
STORED = zipfile.ZIP_STORED


def archive(entries: list[tuple[str, bytes, int]]) -> bytes:
    stream = BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(stream, "w") as output:
            for name, content, compression in entries:
                info = zipfile.ZipInfo(name, STAMP)
                info.compress_type = compression
                info.external_attr = 0o100600 << 16
                output.writestr(info, content)
    return stream.getvalue()


def opc(required: list[tuple[str, bytes, int]], extra=None) -> bytes:
    return archive(
        [
            ("[Content_Types].xml", b"<Types/>", DEFLATED),
            ("_rels/.rels", b"<Relationships/>", DEFLATED),
            *required,
            *(extra or []),
        ]
    )


def odf(media_type: bytes, content: bytes) -> bytes:
    return archive(
        [
            ("mimetype", media_type, STORED),
            ("content.xml", content, DEFLATED),
            ("META-INF/manifest.xml", b"<manifest/>", DEFLATED),
        ]
    )


def many_text(tag: str, count: int) -> bytes:
    return (
        f"<root xmlns:w='urn:w' xmlns:text='urn:text'>"
        + "".join(f"<{tag}>segment-{index}</{tag}>" for index in range(count))
        + "</root>"
    ).encode()


def cases() -> dict[str, bytes]:
    safe_docx = opc(
        [("word/document.xml", b"<w:document xmlns:w='urn:w'><w:t>Word review text</w:t></w:document>", DEFLATED)]
    )
    safe_xlsx = opc(
        [
            ("xl/workbook.xml", b"<workbook/>", DEFLATED),
            ("xl/worksheets/sheet1.xml", b"<worksheet><is><t>Sheet review text</t></is></worksheet>", DEFLATED),
        ]
    )
    safe_pptx = opc(
        [
            ("ppt/presentation.xml", b"<presentation/>", DEFLATED),
            ("ppt/slides/slide1.xml", b"<p:sld xmlns:p='urn:p' xmlns:a='urn:a'><a:t>Slide review text</a:t></p:sld>", DEFLATED),
        ]
    )
    safe_odt = odf(
        b"application/vnd.oasis.opendocument.text",
        b"<office:document xmlns:office='urn:office' xmlns:text='urn:text'><text:p>Writer review text</text:p></office:document>",
    )
    safe_ods = odf(
        b"application/vnd.oasis.opendocument.spreadsheet",
        b"<office:document xmlns:office='urn:office' xmlns:text='urn:text'><text:p>Calc review text</text:p></office:document>",
    )
    safe_odp = odf(
        b"application/vnd.oasis.opendocument.presentation",
        b"<office:document xmlns:office='urn:office' xmlns:text='urn:text'><text:p>Impress review text</text:p></office:document>",
    )
    many_slides = [
        (
            f"ppt/slides/slide{index}.xml",
            f"<s><t>slide-{index}</t></s>".encode(),
            DEFLATED,
        )
        for index in range(1, 66)
    ]
    return {
        "safe.docx": safe_docx,
        "safe.xlsx": safe_xlsx,
        "safe.pptx": safe_pptx,
        "safe.odt": safe_odt,
        "safe.ods": safe_ods,
        "safe.odp": safe_odp,
        "formula.xlsx": opc(
            [
                ("xl/workbook.xml", b"<workbook/>", DEFLATED),
                ("xl/worksheets/sheet1.xml", b"<worksheet><c><f>SUM(A1:A2)</f><v>3</v></c></worksheet>", DEFLATED),
            ]
        ),
        "formula.ods": odf(
            b"application/vnd.oasis.opendocument.spreadsheet",
            b"<office:document xmlns:office='urn:office' xmlns:table='urn:table' table:formula='of:=SUM([.A1:.A2])'/>",
        ),
        "segments.docx": opc([("word/document.xml", many_text("w:t", 1001), DEFLATED)]),
        "segments.odt": odf(
            b"application/vnd.oasis.opendocument.text", many_text("text:p", 1001)
        ),
        "parts.pptx": opc(
            [("ppt/presentation.xml", b"<presentation/>", DEFLATED)], many_slides
        ),
        "segments.odp": odf(
            b"application/vnd.oasis.opendocument.presentation",
            many_text("text:p", 1001),
        ),
    }


def generate() -> list[Path]:
    if OUTPUT.exists() and (
        OUTPUT.is_symlink()
        or (hasattr(OUTPUT, "is_junction") and OUTPUT.is_junction())
        or not OUTPUT.is_dir()
    ):
        raise RuntimeError("unsafe-output-directory")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    values = cases()
    if any(
        path.name not in values or not path.is_file() or path.is_symlink()
        for path in OUTPUT.iterdir()
    ):
        raise RuntimeError("unexpected-output-entry")
    result = []
    for name, content in values.items():
        path = OUTPUT / name
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise RuntimeError("unsafe-output-entry")
        path.write_bytes(content)
        result.append(path)
    return result


if __name__ == "__main__":
    print(f"Created {len(generate())} inert complex-document semantic fixtures.")
