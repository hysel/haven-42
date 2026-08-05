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
from typing import Any, Callable


TRUST_SCOPES = {"loopback", "trusted-lan", "external"}
PROVIDER_AUTHENTICATION_MODES = {"none", "bearer", "x-api-key"}
MAX_PROVIDER_API_KEY_BYTES = 4096
MAX_JSON_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_RESPONSE_BYTES = 64 * 1024 * 1024


class ProviderSecurityError(ValueError):
    pass


class ProviderRequestCancelled(ProviderSecurityError):
    """Raised when the caller closes a bounded provider stream intentionally."""


def read_json_stream(
    request: urllib.request.Request,
    timeout: int,
    maximum_bytes: int,
    cancelled: Callable[[], bool],
    on_open: Callable[[Any], None],
    on_close: Callable[[], None],
) -> list[dict[str, Any]]:
    """Read bounded newline-delimited JSON without proxies or redirects."""
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or timeout < 1
        or timeout > 3600
        or isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or maximum_bytes < 1
        or maximum_bytes > MAX_IMAGE_RESPONSE_BYTES
    ):
        raise ProviderSecurityError("invalid-provider-io-bound")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    records: list[dict[str, Any]] = []
    total_bytes = 0
    try:
        with opener.open(request, timeout=timeout) as response:
            on_open(response)
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    if int(content_length) > maximum_bytes:
                        raise ProviderSecurityError("provider-response-too-large")
                except ValueError as error:
                    raise ProviderSecurityError("invalid-provider-content-length") from error
            while True:
                if cancelled():
                    raise ProviderRequestCancelled("provider-request-cancelled")
                line = response.readline(maximum_bytes - total_bytes + 1)
                if not line:
                    break
                total_bytes += len(line)
                if total_bytes > maximum_bytes:
                    raise ProviderSecurityError("provider-response-too-large")
                if not line.strip():
                    continue
                try:
                    value = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise ProviderSecurityError("invalid-provider-json") from error
                if not isinstance(value, dict):
                    raise ProviderSecurityError("provider-json-root-must-be-object")
                records.append(value)
    except urllib.error.HTTPError as error:
        if cancelled():
            raise ProviderRequestCancelled("provider-request-cancelled") from error
        raise ProviderSecurityError(f"provider-http-error-{error.code}") from error
    except (OSError, ValueError) as error:
        if cancelled():
            raise ProviderRequestCancelled("provider-request-cancelled") from error
        raise
    finally:
        on_close()
    if cancelled():
        raise ProviderRequestCancelled("provider-request-cancelled")
    if not records:
        raise ProviderSecurityError("invalid-provider-json")
    return records


class ProviderAuthentication:
    """Memory-only, fixed-header provider authentication without secret repr."""

    __slots__ = ("_mode", "_header_name", "_header_value")

    def __init__(self, mode: str, header_name: str | None, header_value: str | None):
        valid = (
            (mode == "none" and header_name is None and header_value is None)
            or (
                mode == "bearer"
                and header_name == "Authorization"
                and isinstance(header_value, str)
                and header_value.startswith("Bearer ")
                and 0 < len(header_value.removeprefix("Bearer ").encode("ascii", "ignore"))
                <= MAX_PROVIDER_API_KEY_BYTES
                and header_value.removeprefix("Bearer ").isascii()
                and all(0x21 <= ord(character) <= 0x7E for character in header_value.removeprefix("Bearer "))
            )
            or (
                mode == "x-api-key"
                and header_name == "X-API-Key"
                and isinstance(header_value, str)
                and 0 < len(header_value.encode("ascii", "ignore")) <= MAX_PROVIDER_API_KEY_BYTES
                and header_value.isascii()
                and all(0x21 <= ord(character) <= 0x7E for character in header_value)
            )
        )
        if not valid:
            raise ProviderSecurityError("invalid-provider-authentication-object")
        self._mode = mode
        self._header_name = header_name
        self._header_value = header_value

    @property
    def mode(self) -> str:
        return self._mode

    def __repr__(self) -> str:
        return f"ProviderAuthentication(mode={self.mode!r}, secret=<redacted>)"

    @property
    def configured(self) -> bool:
        return self.mode != "none"

    def request_headers(self) -> dict[str, str]:
        if self._header_name is None or self._header_value is None:
            return {}
        return {self._header_name: self._header_value}

    def public_summary(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "configured": self.configured,
            "persisted": False,
        }


NO_PROVIDER_AUTHENTICATION = ProviderAuthentication("none", None, None)


def validate_provider_authentication(
    mode: object,
    api_key: object,
    endpoint_policy: dict[str, Any],
) -> ProviderAuthentication:
    if not isinstance(mode, str) or mode not in PROVIDER_AUTHENTICATION_MODES:
        raise ProviderSecurityError("invalid-provider-authentication-mode")
    if not isinstance(api_key, str):
        raise ProviderSecurityError("invalid-provider-api-key")
    if mode == "none":
        if api_key:
            raise ProviderSecurityError("unexpected-provider-api-key")
        return NO_PROVIDER_AUTHENTICATION
    try:
        encoded = api_key.encode("ascii")
    except UnicodeEncodeError as error:
        raise ProviderSecurityError("invalid-provider-api-key") from error
    if (
        not encoded
        or len(encoded) > MAX_PROVIDER_API_KEY_BYTES
        or api_key != api_key.strip()
        or any(byte < 0x21 or byte > 0x7E for byte in encoded)
    ):
        raise ProviderSecurityError("invalid-provider-api-key")
    if (
        endpoint_policy.get("trustScope") != "loopback"
        and not str(endpoint_policy.get("baseUrl", "")).startswith("https://")
    ):
        raise ProviderSecurityError("authenticated-provider-requires-https")
    if mode == "bearer":
        return ProviderAuthentication(mode, "Authorization", f"Bearer {api_key}")
    return ProviderAuthentication(mode, "X-API-Key", api_key)


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


def validate_local_base_url(value: str) -> dict[str, Any]:
    """Validate and classify a loopback or private-LAN provider URL."""
    try:
        return validate_base_url(value, "loopback")
    except ProviderSecurityError as error:
        if str(error) != "loopback-provider-required":
            raise
    return validate_base_url(value, "trusted-lan")


def read_bounded(request: urllib.request.Request | str, timeout: int, maximum_bytes: int) -> bytes:
    if timeout < 1 or timeout > 3600 or maximum_bytes < 1:
        raise ProviderSecurityError("invalid-provider-io-bound")
    # Provider traffic must go directly to the user-approved IP literal. Inheriting
    # an OS or environment proxy could disclose private prompts and attachments to
    # an unrelated intermediary.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
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
    loopback = validate_base_url("http://127.0.0.1:11434", "loopback")
    assert loopback["executionLocation"] == "same-machine"
    validated_auth = validate_provider_authentication("bearer", "synthetic-fixture", loopback)
    assert validated_auth.request_headers() == {"Authorization": "Bearer synthetic-fixture"}
    assert "synthetic-fixture" not in repr(validated_auth)
    assert validated_auth.public_summary() == {"mode": "bearer", "configured": True, "persisted": False}
    try:
        ProviderAuthentication("bearer", "X-Arbitrary-Header", "synthetic-fixture")
    except ProviderSecurityError:
        pass
    else:
        raise AssertionError("arbitrary authentication header was accepted")
    trusted_http = validate_base_url("http://[fd00::1]:11434", "trusted-lan")
    for mode, key, policy in (
        ("unknown", "synthetic-fixture", loopback),
        ("none", "synthetic-fixture", loopback),
        ("bearer", "line\nbreak", loopback),
        ("x-api-key", "synthetic-fixture", trusted_http),
    ):
        try:
            validate_provider_authentication(mode, key, policy)
        except ProviderSecurityError:
            pass
        else:
            raise AssertionError((mode, policy["trustScope"]))
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
    print("Provider security self-test passed: 16 cases")


if __name__ == "__main__":
    self_test()
