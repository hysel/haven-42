#!/usr/bin/env python3
"""Review-only restricted pypdf worker. Not imported by the Haven runtime."""

from __future__ import annotations

import argparse
import base64
import binascii
import builtins
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import threading
from typing import Any
import warnings


EXPECTED_WHEEL_NAME = "pypdf-6.14.2-py3-none-any.whl"
EXPECTED_WHEEL_SHA256 = "3f07891af76dc002657e04993ab9b4de81de29f9013b9761d0b7968bff12e946"
EXPECTED_PYPDF_VERSION = "6.14.2"
MAXIMUM_SERIALIZED_REQUEST_BYTES = 22_371_000
MAXIMUM_INPUT_BYTES = 16_777_216
MAXIMUM_PAGES = 500
MAXIMUM_OBJECTS = 10_000
MAXIMUM_NESTING_DEPTH = 32
MAXIMUM_EXPANSION_RATIO = 20
MAXIMUM_EXPANDED_BYTES = 67_108_864
MAXIMUM_OUTPUT_CHARACTERS = 1_000_000
MAXIMUM_CPU_SECONDS = 10
MAXIMUM_MEMORY_BYTES = 536_870_912
ROOT_OBJECT_RECOVERY_LIMIT = 100

ACTIVE_KEYS = {
    "/AA",
    "/AcroForm",
    "/JS",
    "/JavaScript",
    "/Launch",
    "/OpenAction",
    "/RichMedia",
    "/SubmitForm",
    "/XFA",
}
ACTIVE_NAMES = {
    "/ImportData",
    "/JavaScript",
    "/Launch",
    "/Rendition",
    "/RichMedia",
    "/SubmitForm",
}
EMBEDDED_KEYS = {"/AF", "/EF", "/EmbeddedFile", "/EmbeddedFiles", "/Filespec"}
EMBEDDED_NAMES = {"/EmbeddedFile", "/Filespec"}
EXTERNAL_KEYS = {"/GoToR", "/URI"}
EXTERNAL_NAMES = {"/GoToR", "/URI"}


class WorkerRejection(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def apply_posix_limits() -> None:
    if os.name == "nt":
        return
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (MAXIMUM_CPU_SECONDS, MAXIMUM_CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (MAXIMUM_MEMORY_BYTES, MAXIMUM_MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))


def deny_effect(*_args: Any, **_kwargs: Any) -> Any:
    raise PermissionError("effect-denied")


def install_effect_guards() -> None:
    socket.socket = deny_effect
    socket.create_connection = deny_effect
    subprocess.Popen = deny_effect
    subprocess.run = deny_effect
    subprocess.call = deny_effect
    subprocess.check_call = deny_effect
    subprocess.check_output = deny_effect
    os.system = deny_effect
    os.popen = deny_effect
    builtins.open = deny_effect
    io.open = deny_effect
    os.open = deny_effect
    tempfile.NamedTemporaryFile = deny_effect
    tempfile.TemporaryFile = deny_effect
    tempfile.TemporaryDirectory = deny_effect
    tempfile.mkstemp = deny_effect
    tempfile.mkdtemp = deny_effect


def import_exact_parser(wheel: Path):
    wheel = wheel.resolve(strict=True)
    if wheel.name != EXPECTED_WHEEL_NAME or not wheel.is_file() or wheel.is_symlink():
        raise WorkerRejection("artifact-identity-mismatch")
    if wheel.stat().st_size != 349_514 or sha256_file(wheel) != EXPECTED_WHEEL_SHA256:
        raise WorkerRejection("artifact-digest-mismatch")
    sys.path.insert(0, str(wheel))
    import pypdf

    if pypdf.__version__ != EXPECTED_PYPDF_VERSION:
        raise WorkerRejection("parser-version-mismatch")
    return pypdf


def parse_request() -> bytes:
    serialized = sys.stdin.buffer.read(MAXIMUM_SERIALIZED_REQUEST_BYTES + 1)
    if len(serialized) > MAXIMUM_SERIALIZED_REQUEST_BYTES:
        raise WorkerRejection("request-too-large")
    try:
        request = json.loads(serialized)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkerRejection("invalid-request") from error
    if (
        not isinstance(request, dict)
        or set(request) != {"documentBase64", "operation", "schemaVersion"}
        or request["schemaVersion"] != 1
        or request["operation"] != "extract-text"
        or not isinstance(request["documentBase64"], str)
    ):
        raise WorkerRejection("invalid-request")
    try:
        data = base64.b64decode(request["documentBase64"], validate=True)
    except (ValueError, binascii.Error) as error:
        raise WorkerRejection("invalid-document-encoding") from error
    if not 1 <= len(data) <= MAXIMUM_INPUT_BYTES:
        raise WorkerRejection("input-size-rejected")
    if not data.startswith(b"%PDF-"):
        raise WorkerRejection("invalid-pdf-signature")
    return data


def content_reason(key_or_name: str) -> str | None:
    if key_or_name in ACTIVE_KEYS or key_or_name in ACTIVE_NAMES:
        return "active-content-rejected"
    if key_or_name in EMBEDDED_KEYS or key_or_name in EMBEDDED_NAMES:
        return "embedded-content-rejected"
    if key_or_name in EXTERNAL_KEYS or key_or_name in EXTERNAL_NAMES:
        return "external-reference-rejected"
    return None


def validate_classic_xref(data: bytes) -> None:
    start_match = re.search(rb"startxref\s+([0-9]+)\s+%%EOF\s*$", data)
    if start_match is None:
        raise WorkerRejection("malformed-pdf-rejected")
    xref_offset = int(start_match.group(1))
    if xref_offset >= len(data) or not data[xref_offset:].startswith(b"xref"):
        raise WorkerRejection("malformed-pdf-rejected")
    xref_match = re.match(rb"xref\r?\n0 ([0-9]+)\r?\n", data[xref_offset:])
    if xref_match is None:
        raise WorkerRejection("malformed-pdf-rejected")
    entry_count = int(xref_match.group(1))
    if not 1 <= entry_count <= MAXIMUM_OBJECTS + 1:
        raise WorkerRejection("object-budget-exceeded")
    cursor = xref_offset + xref_match.end()
    for identifier in range(entry_count):
        line_end = data.find(b"\n", cursor)
        if line_end < 0:
            raise WorkerRejection("malformed-pdf-rejected")
        line = data[cursor:line_end].rstrip(b"\r")
        entry = re.fullmatch(rb"([0-9]{10}) ([0-9]{5}) ([nf]) ", line)
        if entry is None:
            raise WorkerRejection("malformed-pdf-rejected")
        offset = int(entry.group(1))
        generation = int(entry.group(2))
        state = entry.group(3)
        if identifier == 0:
            if state != b"f":
                raise WorkerRejection("malformed-pdf-rejected")
        elif state == b"n":
            header = f"{identifier} {generation} obj".encode("ascii")
            if offset >= len(data) or not data[offset:].startswith(header):
                raise WorkerRejection("malformed-pdf-rejected")
        cursor = line_end + 1
    if not data[cursor:].startswith(b"trailer"):
        raise WorkerRejection("malformed-pdf-rejected")


def inspect_pdf(reader: Any, input_size: int, pypdf: Any) -> tuple[int, int]:
    object_count = sum(len(section) for section in reader.xref.values())
    if object_count > MAXIMUM_OBJECTS:
        raise WorkerRejection("object-budget-exceeded")
    try:
        pages_root = reader.root_object["/Pages"].get_object()
        declared_pages = pages_root.get("/Count", 0)
    except Exception as error:
        raise WorkerRejection("invalid-page-tree") from error
    if isinstance(declared_pages, bool) or not isinstance(declared_pages, int):
        raise WorkerRejection("invalid-page-tree")
    if not 0 <= declared_pages <= MAXIMUM_PAGES:
        raise WorkerRejection("page-budget-exceeded")

    pending: list[tuple[Any, int, tuple[int, int] | None]] = []
    for generation, identifiers in reader.xref.items():
        for identifier in identifiers:
            if identifier:
                pending.append((pypdf.generic.IndirectObject(identifier, generation, reader), 0, None))
    seen: set[tuple[int, int]] = set()
    expanded_bytes = 0
    visited = 0
    while pending:
        value, depth, owner = pending.pop()
        if depth > MAXIMUM_NESTING_DEPTH:
            raise WorkerRejection("nesting-budget-exceeded")
        if isinstance(value, pypdf.generic.IndirectObject):
            identity = (value.idnum, value.generation)
            if owner == identity:
                raise WorkerRejection("recursive-object-rejected")
            if identity in seen:
                continue
            seen.add(identity)
            try:
                value = value.get_object()
            except Exception as error:
                raise WorkerRejection("invalid-object-reference") from error
            owner = identity
        visited += 1
        if visited > MAXIMUM_OBJECTS * 8:
            raise WorkerRejection("object-graph-budget-exceeded")
        if isinstance(value, pypdf.generic.DictionaryObject):
            for key, child in value.items():
                reason = content_reason(str(key))
                if reason:
                    raise WorkerRejection(reason)
                pending.append((child, depth + 1, owner))
            if isinstance(value, pypdf.generic.StreamObject):
                try:
                    stream_data = value.get_data()
                except Exception as error:
                    raise WorkerRejection("stream-decode-rejected") from error
                expanded_bytes += len(stream_data)
                if (
                    expanded_bytes > MAXIMUM_EXPANDED_BYTES
                    or expanded_bytes > input_size * MAXIMUM_EXPANSION_RATIO
                ):
                    raise WorkerRejection("expansion-budget-exceeded")
        elif isinstance(value, pypdf.generic.ArrayObject):
            pending.extend((child, depth + 1, owner) for child in value)
        elif isinstance(value, pypdf.generic.NameObject):
            reason = content_reason(str(value))
            if reason:
                raise WorkerRejection(reason)
    return object_count, expanded_bytes


def extract_text(data: bytes, pypdf: Any) -> dict[str, Any]:
    validate_classic_xref(data)
    try:
        reader = pypdf.PdfReader(
            io.BytesIO(data),
            strict=True,
            root_object_recovery_limit=ROOT_OBJECT_RECOVERY_LIMIT,
        )
    except Exception as error:
        raise WorkerRejection("malformed-pdf-rejected") from error
    if reader.is_encrypted:
        raise WorkerRejection("encrypted-content-rejected")
    object_count, expanded_bytes = inspect_pdf(reader, len(data), pypdf)
    try:
        page_count = len(reader.pages)
    except Exception as error:
        raise WorkerRejection("invalid-page-tree") from error
    if page_count > MAXIMUM_PAGES:
        raise WorkerRejection("page-budget-exceeded")
    text_parts: list[str] = []
    characters = 0
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as error:
            raise WorkerRejection("text-extraction-rejected") from error
        characters += len(text)
        if characters > MAXIMUM_OUTPUT_CHARACTERS:
            raise WorkerRejection("output-budget-exceeded")
        text_parts.append(text)
    return {
        "schemaVersion": 1,
        "status": "candidate-output",
        "text": "\n".join(text_parts),
        "pageCount": page_count,
        "objectCount": object_count,
        "expandedBytes": expanded_bytes,
        "parser": {"package": "pypdf", "version": EXPECTED_PYPDF_VERSION},
        "effects": {
            "networkUsed": False,
            "filesystemReadAfterImport": False,
            "filesystemWritePerformed": False,
            "temporaryFileWritten": False,
            "childProcessStarted": False,
            "runtimeAdmissionGranted": False,
        },
    }


def emit(value: dict[str, Any]) -> None:
    serialized = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > 2_097_152:
        serialized = json.dumps({
            "schemaVersion": 1,
            "status": "rejected",
            "reason": "serialized-output-too-large",
            "runtimeAdmissionGranted": False,
        }, separators=(",", ":"))
    sys.stdout.write(serialized)
    sys.stdout.flush()


def effect_guard_probe() -> dict[str, Any]:
    probes = {
        "network": lambda: socket.socket(),
        "filesystemBuiltins": lambda: builtins.open("blocked", "wb"),
        "filesystemOs": lambda: os.open("blocked", os.O_WRONLY | os.O_CREAT),
        "temporaryFile": lambda: tempfile.NamedTemporaryFile(),
        "childProcess": lambda: subprocess.Popen([sys.executable, "-c", "pass"]),
        "shell": lambda: os.system("blocked"),
    }
    denied: dict[str, bool] = {}
    for name, probe in probes.items():
        try:
            probe()
        except PermissionError:
            denied[name] = True
        else:
            denied[name] = False
    return {
        "schemaVersion": 1,
        "status": "effect-guard-probe",
        "denied": denied,
        "runtimeAdmissionGranted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--self-test-hang", action="store_true")
    parser.add_argument("--self-test-crash", action="store_true")
    parser.add_argument("--self-test-stdout-flood", action="store_true")
    parser.add_argument("--self-test-stderr-flood", action="store_true")
    parser.add_argument("--self-test-effects", action="store_true")
    args = parser.parse_args()
    if args.self_test_hang:
        threading.Event().wait()
        return 0
    if args.self_test_crash:
        os._exit(23)
    if args.self_test_stdout_flood:
        while True:
            sys.stdout.buffer.write(b"x" * 65_536)
            sys.stdout.buffer.flush()
    if args.self_test_stderr_flood:
        while True:
            sys.stderr.buffer.write(b"x" * 65_536)
            sys.stderr.buffer.flush()
    if args.wheel is None:
        parser.error("--wheel is required")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    logging.disable(logging.CRITICAL)
    warnings.simplefilter("error")
    try:
        apply_posix_limits()
        pypdf = import_exact_parser(args.wheel)
        install_effect_guards()
        if args.self_test_effects:
            emit(effect_guard_probe())
            return 0
        data = parse_request()
        emit(extract_text(data, pypdf))
    except WorkerRejection as error:
        emit({
            "schemaVersion": 1,
            "status": "rejected",
            "reason": str(error),
            "runtimeAdmissionGranted": False,
        })
    except BaseException:
        emit({
            "schemaVersion": 1,
            "status": "error",
            "reason": "worker-failure",
            "runtimeAdmissionGranted": False,
        })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
