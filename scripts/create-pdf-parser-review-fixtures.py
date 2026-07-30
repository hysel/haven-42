#!/usr/bin/env python3
"""Create deterministic inert PDF files for a future restricted-parser review."""

from __future__ import annotations

import hashlib
import json
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "dist" / "local-review" / "pdf-parser-hostile-corpus"


def is_linklike(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", lambda: False)
    return path.is_symlink() or is_junction()


def pdf(objects: list[bytes], trailer_extra: bytes = b"") -> bytes:
    data = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, value in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode("ascii"))
        data.extend(value)
        data.extend(b"\nendobj\n")
    xref_offset = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    data.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    data.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R ".encode("ascii"))
    data.extend(trailer_extra)
    data.extend(b">>\nstartxref\n")
    data.extend(str(xref_offset).encode("ascii"))
    data.extend(b"\n%%EOF\n")
    return bytes(data)


def base_objects(catalog_extra: bytes = b"", content: bytes = b"BT /F1 12 Tf 72 720 Td (Haven 42 fixture) Tj ET") -> list[bytes]:
    return [
        b"<< /Type /Catalog /Pages 2 0 R " + catalog_extra + b">>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]


def build_cases() -> dict[str, dict[str, object]]:
    safe = pdf(base_objects())
    encrypted_objects = base_objects() + [
        b"<< /Filter /Standard /V 1 /R 2 /O <00> /U <00> /P -4 >>",
    ]
    compressed = zlib.compress(b"A" * 1_000_000, level=9)
    cases: dict[str, dict[str, object]] = {
        "safe-text-only.pdf": {
            "category": "control",
            "expected": "candidate-only",
            "markers": ["%PDF-1.7", "Haven 42 fixture"],
            "bytes": safe,
        },
        "encrypted-standard.pdf": {
            "category": "encryption",
            "expected": "reject-encrypted",
            "markers": ["/Encrypt", "/Standard"],
            "bytes": pdf(encrypted_objects, b"/Encrypt 6 0 R "),
        },
        "javascript-name-tree.pdf": {
            "category": "active-content",
            "expected": "reject-javascript",
            "markers": ["/JavaScript", "/JS"],
            "bytes": pdf(base_objects(b"/Names << /JavaScript << /Names [(fixture) 6 0 R] >> >> ") + [
                b"<< /S /JavaScript /JS (app.alert\\(fixture\\)) >>",
            ]),
        },
        "open-action.pdf": {
            "category": "active-content",
            "expected": "reject-open-action",
            "markers": ["/OpenAction", "/GoTo"],
            "bytes": pdf(base_objects(b"/OpenAction 6 0 R ") + [
                b"<< /S /GoTo /D [3 0 R /Fit] >>",
            ]),
        },
        "launch-action.pdf": {
            "category": "active-content",
            "expected": "reject-launch-action",
            "markers": ["/Launch", "/OpenAction"],
            "bytes": pdf(base_objects(b"/OpenAction 6 0 R ") + [
                b"<< /S /Launch /F (blocked-fixture) >>",
            ]),
        },
        "submit-form-action.pdf": {
            "category": "active-content",
            "expected": "reject-submit-form",
            "markers": ["/SubmitForm", "/OpenAction"],
            "bytes": pdf(base_objects(b"/OpenAction 6 0 R ") + [
                b"<< /S /SubmitForm /F (https://invalid.example/) >>",
            ]),
        },
        "embedded-file.pdf": {
            "category": "embedded-content",
            "expected": "reject-embedded-file",
            "markers": ["/EmbeddedFiles", "/EmbeddedFile", "/Filespec"],
            "bytes": pdf(base_objects(b"/Names << /EmbeddedFiles << /Names [(fixture.txt) 6 0 R] >> >> ") + [
                b"<< /Type /Filespec /F (fixture.txt) /EF << /F 7 0 R >> >>",
                b"<< /Type /EmbeddedFile /Length 7 >>\nstream\nfixture\nendstream",
            ]),
        },
        "associated-file.pdf": {
            "category": "embedded-content",
            "expected": "reject-associated-file",
            "markers": ["/AF", "/Filespec", "/EmbeddedFile"],
            "bytes": pdf(base_objects(b"/AF [6 0 R] ") + [
                b"<< /Type /Filespec /F (fixture.txt) /AFRelationship /Data /EF << /F 7 0 R >> >>",
                b"<< /Type /EmbeddedFile /Length 7 >>\nstream\nfixture\nendstream",
            ]),
        },
        "external-uri.pdf": {
            "category": "external-reference",
            "expected": "reject-external-reference",
            "markers": ["/URI", "https://invalid.example/"],
            "bytes": pdf(base_objects() + [
                b"<< /S /URI /URI (https://invalid.example/) >>",
            ]),
        },
        "malformed-xref.pdf": {
            "category": "malformed-structure",
            "expected": "reject-malformed-xref",
            "markers": ["xref", "9999999999"],
            "bytes": safe.replace(b"0000000015 00000 n ", b"9999999999 00000 n ", 1),
        },
        "truncated-eof.pdf": {
            "category": "malformed-structure",
            "expected": "reject-truncated",
            "markers": ["startxref"],
            "bytes": safe[:-6],
        },
        "excessive-page-count.pdf": {
            "category": "resource-abuse",
            "expected": "reject-page-budget",
            "markers": ["/Count 1000000"],
            "bytes": pdf([
                b"<< /Type /Catalog /Pages 2 0 R >>",
                b"<< /Type /Pages /Kids [3 0 R] /Count 1000000 >>",
                *base_objects()[2:],
            ]),
        },
        "compressed-expansion.pdf": {
            "category": "resource-abuse",
            "expected": "reject-expansion-budget",
            "markers": ["/FlateDecode", "/Length"],
            "bytes": pdf(base_objects(content=compressed)[:3] + [
                b"<< /Length " + str(len(compressed)).encode("ascii") + b" /Filter /FlateDecode >>\nstream\n"
                + compressed + b"\nendstream",
                base_objects()[4],
            ]),
        },
        "recursive-object.pdf": {
            "category": "resource-abuse",
            "expected": "reject-recursion",
            "markers": ["/Next 6 0 R"],
            "bytes": pdf(base_objects(b"/Fixture 6 0 R ") + [
                b"<< /Next 6 0 R >>",
            ]),
        },
    }
    return cases


def manifest(cases: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "filename": filename,
            "category": case["category"],
            "expected": case["expected"],
            "sizeBytes": len(case["bytes"]),
            "sha256": hashlib.sha256(case["bytes"]).hexdigest(),
            "markers": case["markers"],
        }
        for filename, case in sorted(cases.items())
    ]


def main() -> int:
    cases = build_cases()
    allowed_root = (ROOT / "dist" / "local-review").resolve()
    resolved_output = OUTPUT.resolve()
    if not resolved_output.is_relative_to(allowed_root):
        raise RuntimeError("PDF review fixtures must remain under the ignored local-review directory.")
    for boundary in (ROOT / "dist", ROOT / "dist" / "local-review", OUTPUT):
        if boundary.exists() and is_linklike(boundary):
            raise RuntimeError("Refusing to write PDF review fixtures through a link or junction.")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected_names = set(cases) | {"MANIFEST.json"}
    unexpected = sorted(path.name for path in OUTPUT.iterdir() if path.name not in expected_names)
    if unexpected:
        raise RuntimeError(f"Refusing to mix unexpected files into the PDF review corpus: {', '.join(unexpected)}")
    for filename, case in cases.items():
        target = OUTPUT / filename
        if target.exists() and (is_linklike(target) or not target.is_file()):
            raise RuntimeError(f"Refusing to overwrite non-regular file: {filename}")
        target.write_bytes(case["bytes"])
    manifest_target = OUTPUT / "MANIFEST.json"
    if manifest_target.exists() and (is_linklike(manifest_target) or not manifest_target.is_file()):
        raise RuntimeError("Refusing to overwrite non-regular file: MANIFEST.json")
    manifest_target.write_text(
        json.dumps({"schemaVersion": 1, "status": "synthetic-inert-no-parser-executed", "cases": manifest(cases)}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Created {len(cases)} inert PDF review fixtures under {OUTPUT}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
