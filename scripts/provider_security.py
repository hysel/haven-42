#!/usr/bin/env python3
"""Shared provider endpoint, bounded-I/O, and exclusive artifact security."""

from __future__ import annotations

import ipaddress
import json
import os
import stat
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


TRUST_SCOPES = {"loopback", "trusted-lan", "external"}
MAX_JSON_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_RESPONSE_BYTES = 64 * 1024 * 1024


class ProviderSecurityError(ValueError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise ProviderSecurityError("provider-redirect-rejected")


def _unsafe_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return address.is_unspecified or address.is_multicast or address.is_link_local


def validate_base_url(value: str, trust_scope: str) -> dict[str, Any]:
    if trust_scope not in TRUST_SCOPES:
        raise ProviderSecurityError("invalid-endpoint-trust-scope")
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError as error:
        raise ProviderSecurityError("invalid-provider-url") from error
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
        raise ProviderSecurityError("invalid-provider-url")
    if trust_scope == "external" and parsed.scheme != "https":
        raise ProviderSecurityError("external-provider-requires-https")
    try:
        addresses = {ipaddress.ip_address(parsed.hostname)}
    except ValueError as error:
        raise ProviderSecurityError("provider-host-must-be-ip-literal") from error
    if not addresses or any(_unsafe_address(address) for address in addresses):
        raise ProviderSecurityError("unsafe-provider-address")
    if trust_scope == "loopback" and not all(address.is_loopback for address in addresses):
        raise ProviderSecurityError("loopback-provider-required")
    if trust_scope == "trusted-lan" and not all(address.is_private or address.is_loopback for address in addresses):
        raise ProviderSecurityError("trusted-lan-provider-required")
    if trust_scope == "external" and any(address.is_private or address.is_loopback for address in addresses):
        raise ProviderSecurityError("external-provider-must-resolve-publicly")
    host = parsed.hostname.lower()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    port = f":{parsed.port}" if parsed.port is not None else ""
    return {
        "baseUrl": f"{parsed.scheme}://{host}{port}",
        "trustScope": trust_scope,
        "executionLocation": {"loopback": "same-machine", "trusted-lan": "user-trusted-lan", "external": "external"}[trust_scope],
        "externalProvider": trust_scope == "external",
        "resolvedAddresses": tuple(sorted(str(address) for address in addresses)),
    }


def read_bounded(request: urllib.request.Request | str, timeout: int, maximum_bytes: int) -> bytes:
    if timeout < 1 or timeout > 3600 or maximum_bytes < 1:
        raise ProviderSecurityError("invalid-provider-io-bound")
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    if int(content_length) > maximum_bytes:
                        raise ProviderSecurityError("provider-response-too-large")
                except ValueError as error:
                    raise ProviderSecurityError("invalid-provider-content-length") from error
            data = response.read(maximum_bytes + 1)
    except urllib.error.HTTPError as error:
        raise ProviderSecurityError(f"provider-http-error-{error.code}") from error
    if len(data) > maximum_bytes:
        raise ProviderSecurityError("provider-response-too-large")
    return data


def read_json(request: urllib.request.Request | str, timeout: int, maximum_bytes: int = MAX_JSON_RESPONSE_BYTES) -> dict[str, Any]:
    try:
        value = json.loads(read_bounded(request, timeout, maximum_bytes).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProviderSecurityError("invalid-provider-json") from error
    if not isinstance(value, dict):
        raise ProviderSecurityError("provider-json-root-must-be-object")
    return value


def _is_reparse_or_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = path.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def prepare_artifact_directory(session_path: Path) -> Path:
    raw_session = session_path.absolute()
    if _is_reparse_or_link(raw_session):
        raise ProviderSecurityError("session-reparse-point-rejected")
    session = raw_session.resolve(strict=True)
    if _is_reparse_or_link(session):
        raise ProviderSecurityError("session-reparse-point-rejected")
    artifact_directory = session / "artifacts"
    if artifact_directory.exists() and _is_reparse_or_link(artifact_directory):
        raise ProviderSecurityError("artifact-directory-reparse-point-rejected")
    artifact_directory.mkdir(mode=0o700, parents=False, exist_ok=True)
    resolved = artifact_directory.resolve(strict=True)
    if resolved.parent != session or _is_reparse_or_link(artifact_directory):
        raise ProviderSecurityError("artifact-directory-escaped-session")
    return resolved


def write_new_file(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            path.unlink(missing_ok=True)
        finally:
            raise
    finally:
        os.close(descriptor)


def self_test() -> None:
    assert validate_base_url("http://127.0.0.1:11434", "loopback")["executionLocation"] == "same-machine"
    for value, scope in (("http://192.0.2.1", "loopback"), ("http://127.0.0.1", "external"), ("http://169.254.169.254", "trusted-lan"), ("http://user:pass@127.0.0.1", "loopback"), ("http://localhost:11434", "loopback")):
        try:
            validate_base_url(value, scope)
        except ProviderSecurityError:
            pass
        else:
            raise AssertionError((value, scope))
    with tempfile.TemporaryDirectory() as root:
        session = Path(root) / "session"
        session.mkdir()
        target = prepare_artifact_directory(session) / "result.bin"
        write_new_file(target, b"safe")
        assert target.read_bytes() == b"safe"
        try:
            write_new_file(target, b"overwrite")
        except FileExistsError:
            pass
        else:
            raise AssertionError("exclusive write must reject overwrite")
    print("Provider security self-test passed: 8 cases")


if __name__ == "__main__":
    self_test()
