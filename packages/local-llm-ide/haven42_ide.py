#!/usr/bin/env python3
"""Small, dependency-free setup helper for Haven 42 IDE tools."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Optional
from urllib.parse import urlsplit


PACKAGE_ROOT = Path(__file__).resolve().parent
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
PRIVATE_IPV6_NETWORK = ipaddress.ip_network("fc00::/7")


class SetupError(ValueError):
    """A short error that can be shown directly to the user."""


def safe_target(value: str) -> Path:
    target = Path(value).expanduser()
    if not target.exists() or not target.is_dir() or target.is_symlink():
        raise SetupError("Choose an existing folder that is not a symbolic link.")
    resolved = target.resolve()
    if (
        resolved == PACKAGE_ROOT
        or PACKAGE_ROOT in resolved.parents
        or resolved in PACKAGE_ROOT.parents
    ):
        raise SetupError("Choose your project folder, not the IDE tools package folder.")
    return resolved


def safe_model(value: str) -> str:
    if not MODEL_PATTERN.fullmatch(value):
        raise SetupError("The model name contains unsupported characters.")
    return value


def is_local_or_private(address) -> bool:
    """Accept loopback and exact RFC 1918/ULA ranges without broad is_private rules."""
    if address.is_loopback:
        return True
    if address.version == 6:
        return address in PRIVATE_IPV6_NETWORK
    number = int(address)
    first_octet = number >> 24
    first_twelve_bits = number >> 20
    first_two_octets = number >> 16
    return (
        first_octet == 10
        or first_twelve_bits == 0xAC1
        or first_two_octets == 0xC0A8
    )


def safe_ollama_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise SetupError("Enter a valid Ollama address.") from error
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise SetupError(
            "Use a plain HTTP or HTTPS Ollama address without a password, path, query, or fragment."
        )
    if port is not None and not 1 <= port <= 65535:
        raise SetupError("The Ollama port must be between 1 and 65535.")
    hostname = parsed.hostname.casefold().rstrip(".")
    if hostname == "localhost":
        pass
    else:
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError as error:
            raise SetupError(
                "Use localhost or a private-network IP address for Ollama."
            ) from error
        if not is_local_or_private(address):
            raise SetupError("Public Ollama addresses are not accepted by this package.")
    host = f"[{hostname}]" if ":" in hostname else hostname
    authority = host if port is None else f"{host}:{port}"
    return f"{parsed.scheme}://{authority}"


def file_digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def verify_package(package_root: Path = PACKAGE_ROOT) -> None:
    manifest_path = package_root / "MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SetupError("The package manifest is missing or unreadable. Download the package again.") from error
    records = manifest.get("files")
    if manifest.get("schemaVersion") != 1 or not isinstance(records, list) or not 1 <= len(records) <= 512:
        raise SetupError("The package manifest is invalid. Download the package again.")
    expected: dict[str, tuple[int, str]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise SetupError("The package manifest contains an invalid file record.")
        relative = record.get("path")
        size = record.get("sizeBytes")
        digest = record.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or not isinstance(size, int)
            or not 0 <= size <= 5 * 1024 * 1024
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or relative in expected
        ):
            raise SetupError("The package manifest contains an unsafe file record.")
        expected[relative] = (size, digest)
    actual: dict[str, Path] = {}
    for path in sorted(package_root.rglob("*")):
        if path == manifest_path:
            continue
        if path.is_symlink():
            raise SetupError("The package contains an unsafe symbolic link.")
        if path.is_file():
            relative = path.relative_to(package_root).as_posix()
            actual[relative] = path
    if set(actual) != set(expected):
        raise SetupError("The package file list does not match its manifest.")
    for relative, path in actual.items():
        size, expected_digest = expected[relative]
        if path.stat().st_size != size or file_digest(path) != expected_digest:
            raise SetupError(f"Package integrity check failed for {relative}.")


def ensure_safe_destination(path: Path, target: Path) -> None:
    # A dangling link reports exists() == False even though writes through it
    # can escape the selected project. Check the link itself first.
    if path.is_symlink():
        raise SetupError(f"Refusing to replace symbolic link: {path.name}")
    try:
        path.resolve().relative_to(target)
    except ValueError as error:
        raise SetupError("A setup destination escaped the selected project folder.") from error


def aider_config(model: str, endpoint: str) -> str:
    return "\n".join(
        (
            "# Local Haven 42 settings. Do not commit this file.",
            f"model: ollama_chat/{model}",
            "set-env:",
            f"  - OLLAMA_API_BASE={endpoint}",
            "auto-commits: false",
            "dirty-commits: false",
            "gitignore: false",
            "check-update: false",
            "analytics-disable: true",
            "map-tokens: 0",
            "line-endings: platform",
            "",
        )
    )


def opencode_config(model: str, endpoint: str) -> str:
    base = endpoint if endpoint.endswith("/v1") else f"{endpoint}/v1"
    return json.dumps(
        {
            "$schema": "https://opencode.ai/config.json",
            "model": f"ollama/{model}",
            "provider": {
                "ollama": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "Ollama (local)",
                    "options": {"baseURL": base},
                    "models": {model: {"name": f"{model} (local)"}},
                }
            },
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def configure_tool(
    tool: str,
    target: Path,
    model: str,
    endpoint: str,
    apply: bool,
    replace: bool,
) -> list[str]:
    names = {"aider": ".aider.conf.local.yml", "opencode": ".opencode.local.json"}
    output = target / names[tool]
    ensure_safe_destination(output, target)
    if output.exists() and not replace:
        raise SetupError(f"{output.name} already exists. Use --replace after reviewing it.")
    backup = output.with_name(f"{output.name}.haven42-backup")
    actions = [f"Write local {tool} settings to {output}"]
    if output.exists():
        ensure_safe_destination(backup, target)
        if backup.exists():
            raise SetupError(f"{backup.name} already exists. Move it first.")
        actions.insert(0, f"Back up the current settings to {backup}")
    if not apply:
        return actions
    if output.exists():
        shutil.copy2(output, backup)
    content = aider_config(model, endpoint) if tool == "aider" else opencode_config(model, endpoint)
    temporary = output.with_name(f".{output.name}.haven42-new")
    ensure_safe_destination(temporary, target)
    if temporary.exists():
        raise SetupError(f"Temporary setup file already exists: {temporary.name}")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(output)
    return actions


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Set up local Ollama settings for Aider or OpenCode."
    )
    commands = result.add_subparsers(dest="command")
    commands.add_parser("status", help="Show what this package can configure.")
    configure = commands.add_parser("configure", help="Create local Aider or OpenCode settings.")
    configure.add_argument("tool", choices=("aider", "opencode"))
    configure.add_argument("--target", required=True, help="Existing project folder.")
    configure.add_argument("--model", required=True, help="Installed Ollama model name.")
    configure.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    configure.add_argument("--apply", action="store_true", help="Make the displayed changes.")
    configure.add_argument("--replace", action="store_true", help="Back up and update existing settings.")
    return result


def show_status() -> None:
    print("Haven 42 Local LLM IDE Tools")
    print("- Continue: legacy evidence only; this package does not configure or support it")
    print("- Aider: local Ollama configuration")
    print("- OpenCode: local Ollama configuration")
    print("This package does not install an IDE, Ollama, models, or drivers.")


def main(argv: Optional[list[str]] = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        verify_package()
        if arguments.command in {None, "status"}:
            show_status()
            return 0
        target = safe_target(arguments.target)
        actions = configure_tool(
            arguments.tool,
            target,
            safe_model(arguments.model),
            safe_ollama_url(arguments.ollama_url),
            arguments.apply,
            arguments.replace,
        )
    except (OSError, SetupError) as error:
        print(f"Setup stopped: {error}", file=sys.stderr)
        return 2
    print("Changes made:" if arguments.apply else "Preview only; nothing was changed:")
    for action in actions:
        print(f"- {action}")
    if not arguments.apply:
        print("Run the same command with --apply when the plan looks right.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
