#!/usr/bin/env python3
"""Effect-free validation for future injected web-research transport receipts."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit


class TransportRejected(ValueError):
    pass


def _public_addresses(values: object) -> tuple[str, ...]:
    if not isinstance(values, list) or not values:
        raise TransportRejected("dns-answer-shape")
    result = []
    for value in values:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as error:
            raise TransportRejected("dns-answer-invalid") from error
        if not address.is_global:
            raise TransportRejected("dns-answer-not-public")
        result.append(address.compressed)
    if len(result) != len(set(result)):
        raise TransportRejected("dns-answer-duplicate")
    return tuple(sorted(result))


def validate_destination(url: object, fixed_host: str) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise TransportRejected("destination-shape")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise TransportRejected("destination-shape") from error
    if (
        parsed.scheme != "https"
        or parsed.hostname != fixed_host
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise TransportRejected("destination-not-allowlisted")
    try:
        ipaddress.ip_address(parsed.hostname)
    except ValueError:
        pass
    else:
        raise TransportRejected("destination-ip-literal")
    return url


def validate_resolution(
    host: object, fixed_host: str, preconnect: object, connected: object
) -> tuple[str, ...]:
    if host != fixed_host:
        raise TransportRejected("dns-host-not-allowlisted")
    first = _public_addresses(preconnect)
    second = _public_addresses(connected)
    if first != second:
        raise TransportRejected("dns-rebinding-detected")
    return first


def validate_receipt(receipt: object, maximum_bytes: int, timeout_seconds: int) -> bytes:
    if not isinstance(receipt, dict) or set(receipt) != {
        "status", "contentType", "contentEncoding", "elapsedMilliseconds",
        "redirects", "body"
    }:
        raise TransportRejected("receipt-shape")
    if receipt["status"] != 200:
        raise TransportRejected("http-status")
    if receipt["contentType"] != "application/json":
        raise TransportRejected("content-type")
    if receipt["contentEncoding"] not in (None, "identity"):
        raise TransportRejected("content-encoding")
    elapsed = receipt["elapsedMilliseconds"]
    if isinstance(elapsed, bool) or not isinstance(elapsed, int) or not 0 <= elapsed <= timeout_seconds * 1000:
        raise TransportRejected("response-time")
    if receipt["redirects"] != []:
        raise TransportRejected("redirect-not-allowed")
    body = receipt["body"]
    if not isinstance(body, bytes) or len(body) > maximum_bytes:
        raise TransportRejected("response-size")
    return body


if __name__ == "__main__":
    print("offline guard only; no DNS or network operation is implemented")
