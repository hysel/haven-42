#!/usr/bin/env python3
"""Bounded official electricity-rate lookup for the local Haven 42 UI."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import re
import urllib.parse
import urllib.error
import urllib.request
from typing import Any, Callable


EIA_ENDPOINT = "https://api.eia.gov/v2/electricity/retail-sales/data/"
EUROSTAT_ENDPOINT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_pc_204"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024


class ElectricityRateError(ValueError):
    """The explicit rate request or official response was not safe to use."""


def _code(value: Any, pattern: str, error: str) -> str:
    if not isinstance(value, str):
        raise ElectricityRateError(error)
    normalized = value.strip().upper()
    if not re.fullmatch(pattern, normalized):
        raise ElectricityRateError(error)
    return normalized


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "Haven42-ElectricityEstimate/1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310: fixed HTTPS allowlist
            final_url = response.geturl()
            if not (final_url.startswith(EIA_ENDPOINT) or final_url.startswith(EUROSTAT_ENDPOINT)):
                raise ElectricityRateError("electricity-rate-redirect-rejected")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.URLError) as error:
        raise ElectricityRateError("electricity-rate-source-unavailable") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ElectricityRateError("electricity-rate-response-too-large")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ElectricityRateError("invalid-electricity-rate-response") from error
    if not isinstance(value, dict):
        raise ElectricityRateError("invalid-electricity-rate-response")
    return value


def _eia_url(state: str, api_key: str) -> str:
    query = [
        ("api_key", api_key), ("frequency", "monthly"), ("data[]", "price"),
        ("facets[sectorid][]", "RES"), ("facets[stateid][]", state),
        ("sort[0][column]", "period"), ("sort[0][direction]", "desc"),
        ("offset", "0"), ("length", "1"),
    ]
    return f"{EIA_ENDPOINT}?{urllib.parse.urlencode(query)}"


def _parse_eia(payload: dict[str, Any], state: str) -> dict[str, Any]:
    response = payload.get("response")
    rows = response.get("data") if isinstance(response, dict) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ElectricityRateError("invalid-electricity-rate-response")
    row = rows[0]
    if row.get("sectorid") != "RES" or row.get("stateid") != state:
        raise ElectricityRateError("electricity-rate-selection-mismatch")
    if row.get("price-units") != "cents per kilowatt-hour":
        raise ElectricityRateError("electricity-rate-unit-mismatch")
    try:
        rate = float(row["price"]) / 100
    except (KeyError, TypeError, ValueError) as error:
        raise ElectricityRateError("invalid-electricity-rate-response") from error
    if not 0 < rate <= 100:
        raise ElectricityRateError("invalid-electricity-rate-response")
    return {
        "sourceId": "eia-us-residential-average",
        "sourceName": "U.S. EIA residential electricity price",
        "countryCode": "US",
        "subdivisionCode": None if state == "US" else f"US-{state}",
        "currency": "USD",
        "ratePerKwh": round(rate, 6),
        "effectivePeriod": str(row.get("period", "")),
        "taxScope": "reported-residential-retail-price",
        "sourceUrl": "https://www.eia.gov/opendata/documentation.php",
    }


def _eurostat_url(country: str) -> str:
    query = [
        ("lang", "en"), ("nrg_cons", "KWH2500-4999"), ("unit", "KWH"),
        ("tax", "I_TAX"), ("currency", "NAC"), ("geo", country),
    ]
    return f"{EUROSTAT_ENDPOINT}?{urllib.parse.urlencode(query)}"


def _dimension_codes(payload: dict[str, Any], name: str) -> set[str]:
    dimension = payload.get("dimension", {}).get(name, {})
    category = dimension.get("category", {}) if isinstance(dimension, dict) else {}
    index = category.get("index") if isinstance(category, dict) else None
    if isinstance(index, dict):
        return set(index)
    if isinstance(index, list):
        return {str(value) for value in index}
    return set()


def _parse_eurostat(payload: dict[str, Any], country: str, currency: str) -> dict[str, Any]:
    expected = {
        "nrg_cons": "KWH2500-4999", "unit": "KWH", "tax": "I_TAX",
        "currency": "NAC", "geo": country,
    }
    if any(_dimension_codes(payload, name) != {value} for name, value in expected.items()):
        raise ElectricityRateError("electricity-rate-selection-mismatch")
    ids, sizes = payload.get("id"), payload.get("size")
    dimension, values = payload.get("dimension"), payload.get("value")
    if not isinstance(ids, list) or not isinstance(sizes, list) or not isinstance(dimension, dict):
        raise ElectricityRateError("invalid-electricity-rate-response")
    if "time" not in ids or len(ids) != len(sizes):
        raise ElectricityRateError("invalid-electricity-rate-response")
    time_index = dimension.get("time", {}).get("category", {}).get("index")
    if not isinstance(time_index, dict):
        raise ElectricityRateError("invalid-electricity-rate-response")
    time_size = int(sizes[ids.index("time")])
    periods = {int(position): period for period, position in time_index.items()}
    items = values.items() if isinstance(values, dict) else enumerate(values or [])
    candidates = []
    for position, raw_rate in items:
        period = periods.get(int(position) % time_size)
        if period and raw_rate is not None:
            try:
                rate = float(raw_rate)
            except (TypeError, ValueError) as error:
                raise ElectricityRateError("invalid-electricity-rate-response") from error
            if 0 < rate <= 100:
                candidates.append((period, rate))
    if not candidates:
        raise ElectricityRateError("invalid-electricity-rate-response")
    period, rate = max(candidates, key=lambda item: item[0])
    return {
        "sourceId": "eurostat-household-electricity",
        "sourceName": "Eurostat household electricity prices",
        "countryCode": country,
        "subdivisionCode": None,
        "currency": currency,
        "ratePerKwh": round(rate, 6),
        "effectivePeriod": period,
        "taxScope": "all-taxes-and-levies-included",
        "sourceUrl": "https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_204/default/table",
    }


def lookup_official_rate(
    request: dict[str, Any], *, fetch_json: Callable[[str], dict[str, Any]] = _fetch_json,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    if set(request) != {"source", "country", "currency", "region"}:
        raise ElectricityRateError("invalid-electricity-rate-fields")
    source = request.get("source")
    country = _code(request.get("country"), r"[A-Z]{2}", "invalid-electricity-country")
    currency = _code(request.get("currency"), r"[A-Z]{3}", "invalid-electricity-currency")
    region_value = request.get("region")
    if not isinstance(region_value, str):
        raise ElectricityRateError("invalid-electricity-region")
    region = region_value.strip().upper()
    if source == "eia":
        if country != "US" or currency != "USD" or (region and not re.fullmatch(r"[A-Z]{2}", region)):
            raise ElectricityRateError("invalid-eia-selection")
        api_key = (environment if environment is not None else os.environ).get("EIA_API_KEY", "").strip()
        if not api_key:
            raise ElectricityRateError("electricity-rate-api-key-unavailable")
        parsed = _parse_eia(fetch_json(_eia_url(region or "US", api_key)), region or "US")
    elif source == "eurostat":
        if region:
            raise ElectricityRateError("invalid-eurostat-selection")
        parsed = _parse_eurostat(fetch_json(_eurostat_url(country)), country, currency)
    else:
        raise ElectricityRateError("invalid-electricity-rate-source")
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schemaVersion": 1,
        "kind": "haven42-electricity-rate-profile",
        "sourceKind": "official-average",
        **parsed,
        "retrievedAt": retrieved,
        "estimateOnly": True,
        "locationWasInferred": False,
    }
