#!/usr/bin/env python3
"""Fetch one explicitly selected official electricity rate into local JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


PROFILE_KIND = "haven42-electricity-rate-profile"
EIA_ENDPOINT = "https://api.eia.gov/v2/electricity/retail-sales/data/"
EUROSTAT_ENDPOINT = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "nrg_pc_204"
)
MAX_RESPONSE_BYTES = 5 * 1024 * 1024


class UpdateError(ValueError):
    """A safe, user-actionable updater failure."""


def _code(value: str, pattern: str, label: str) -> str:
    normalized = value.strip().upper()
    if not re.fullmatch(pattern, normalized):
        raise UpdateError(f"{label} has an unsupported format")
    return normalized


def _positive_decimal(value: Any, label: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise UpdateError(f"{label} is not numeric") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise UpdateError(f"{label} must be greater than zero")
    return parsed


def build_eia_url(country: str, subdivision: str | None, api_key: str) -> str:
    if country != "US":
        raise UpdateError("the EIA adapter only supports country US")
    state_id = "US"
    if subdivision:
        subdivision = _code(subdivision, r"US-[A-Z]{2}", "subdivision code")
        state_id = subdivision.split("-", 1)[1]
    query = [
        ("api_key", api_key), ("frequency", "monthly"), ("data[]", "price"),
        ("facets[sectorid][]", "RES"), ("facets[stateid][]", state_id),
        ("sort[0][column]", "period"), ("sort[0][direction]", "desc"),
        ("offset", "0"), ("length", "1"),
    ]
    return f"{EIA_ENDPOINT}?{urllib.parse.urlencode(query)}"


def build_eurostat_url(
    country: str, currency: str, period: str | None, consumption_band: str,
    tax_code: str, dataset_region: str | None,
) -> str:
    region = _code(dataset_region or country, r"[A-Z]{2}", "Eurostat region code")
    query = [
        ("lang", "en"), ("nrg_cons", consumption_band), ("unit", "KWH"), ("tax", tax_code),
        ("currency", currency), ("geo", region),
    ]
    if period:
        query.append(("time", period))
    return f"{EUROSTAT_ENDPOINT}?{urllib.parse.urlencode(query)}"


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "Haven42-RateUpdater/1"}, method="GET"
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310: fixed HTTPS allowlist
        final_url = response.geturl()
        if not (final_url.startswith(EIA_ENDPOINT) or final_url.startswith(EUROSTAT_ENDPOINT)):
            raise UpdateError("official source redirected outside its allowed endpoint")
        payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise UpdateError("official source response exceeded the safety limit")
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateError("official source did not return valid JSON") from exc
    if not isinstance(value, dict):
        raise UpdateError("official source returned an unexpected JSON shape")
    return value


def parse_eia(payload: dict[str, Any], country: str, subdivision: str | None) -> dict[str, Any]:
    response = payload.get("response")
    rows = response.get("data") if isinstance(response, dict) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise UpdateError("EIA did not return exactly one latest residential rate")
    row = rows[0]
    if row.get("sectorid") != "RES" or row.get("price-units") != "cents per kilowatt-hour":
        raise UpdateError("EIA returned an unexpected sector or price unit")
    expected_state = "US" if not subdivision else subdivision.split("-", 1)[1]
    if row.get("stateid") != expected_state:
        raise UpdateError("EIA returned a different region than requested")
    rate = _positive_decimal(row.get("price"), "EIA price") / Decimal("100")
    return {
        "countryCode": country, "subdivisionCode": subdivision, "currency": "USD",
        "ratePerKwh": float(rate), "effectivePeriod": str(row.get("period", "")),
        "taxScope": "reported-residential-retail-price",
        "sourceId": "eia-us-residential-average",
        "sourceUrl": "https://www.eia.gov/opendata/documentation.php",
        "selection": {"sector": "residential", "regionName": row.get("stateDescription")},
    }


def _jsonstat_period_value(payload: dict[str, Any]) -> tuple[str, Any]:
    ids, sizes = payload.get("id"), payload.get("size")
    dimensions, values = payload.get("dimension"), payload.get("value")
    if not isinstance(ids, list) or not isinstance(sizes, list) or not isinstance(dimensions, dict):
        raise UpdateError("Eurostat returned an unexpected JSON-stat shape")
    if "time" not in ids or len(ids) != len(sizes):
        raise UpdateError("Eurostat response has no usable time dimension")
    if any(int(size) != 1 for axis, size in zip(ids, sizes) if axis != "time"):
        raise UpdateError("Eurostat returned more than one value for a requested filter")
    category = dimensions.get("time", {}).get("category", {})
    index = category.get("index") if isinstance(category, dict) else None
    if not isinstance(index, dict):
        raise UpdateError("Eurostat time index is missing")
    by_position = {int(position): period for period, position in index.items()}
    time_size = int(sizes[ids.index("time")])
    candidates: list[tuple[str, Any]] = []
    value_items = values.items() if isinstance(values, dict) else enumerate(values or [])
    for flat_position, value in value_items:
        if value is None:
            continue
        period = by_position.get(int(flat_position) % time_size)
        if period:
            candidates.append((period, value))
    if not candidates:
        raise UpdateError("Eurostat returned no rate for the selected filters")
    return max(candidates, key=lambda item: item[0])


def _jsonstat_dimension_codes(payload: dict[str, Any], name: str) -> set[str]:
    dimension = payload.get("dimension", {}).get(name, {})
    category = dimension.get("category", {}) if isinstance(dimension, dict) else {}
    index = category.get("index") if isinstance(category, dict) else None
    if isinstance(index, dict):
        return set(index)
    if isinstance(index, list):
        return {str(value) for value in index}
    return set()


def parse_eurostat(
    payload: dict[str, Any], country: str, currency: str, consumption_band: str,
    tax_code: str, dataset_region: str | None,
) -> dict[str, Any]:
    expected = {
        "nrg_cons": consumption_band,
        "unit": "KWH",
        "tax": tax_code,
        "currency": currency,
        "geo": dataset_region or country,
    }
    for dimension, selected_code in expected.items():
        if _jsonstat_dimension_codes(payload, dimension) != {selected_code}:
            raise UpdateError(f"Eurostat returned a different {dimension} selection than requested")
    period, raw_rate = _jsonstat_period_value(payload)
    rate = _positive_decimal(raw_rate, "Eurostat price")
    return {
        "countryCode": country, "subdivisionCode": None, "currency": currency,
        "ratePerKwh": float(rate), "effectivePeriod": period,
        "taxScope": "all-taxes-and-levies-included" if tax_code == "I_TAX" else tax_code,
        "sourceId": "eurostat-household-electricity",
        "sourceUrl": "https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_204/default/table",
        "selection": {"consumptionBand": consumption_band, "datasetRegion": dataset_region or country, "taxCode": tax_code},
    }


def make_profile(parsed: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1, "snapshotVersion": 1, "kind": PROFILE_KIND,
        "sourceKind": "official-average", **parsed, "retrievedAt": retrieved_at,
        "estimateOnly": True, "locationWasInferred": False,
    }


def write_profile(path: Path, profile: dict[str, Any], replace: bool) -> None:
    if path.exists() and not replace:
        raise UpdateError("output already exists; use --replace to replace that exact file")
    if path.is_symlink() or (path.parent.exists() and path.parent.is_symlink()):
        raise UpdateError("output path must not be a symbolic link")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(profile, stream, indent=2, sort_keys=True)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=("eia", "eurostat"))
    parser.add_argument("--country", required=True, help="Explicit ISO 3166-1 alpha-2 country code")
    parser.add_argument("--subdivision", help="Explicit ISO 3166-2 code; EIA supports US states")
    parser.add_argument("--currency", help="Explicit ISO 4217 source currency; required for Eurostat")
    parser.add_argument("--period", help="Optional exact Eurostat half-year, such as 2025-S2")
    parser.add_argument("--dataset-region", help="Explicit Eurostat geo code when it differs from ISO alpha-2")
    parser.add_argument("--consumption-band", default="KWH2500-4999")
    parser.add_argument("--tax-code", default="I_TAX")
    parser.add_argument("--api-key-env", default="EIA_API_KEY")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        country = _code(args.country, r"[A-Z]{2}", "country code")
        subdivision = args.subdivision.upper() if args.subdivision else None
        retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if args.source == "eia":
            if args.currency and args.currency.upper() != "USD":
                raise UpdateError("EIA source currency is USD")
            api_key = os.environ.get(args.api_key_env, "").strip()
            if not api_key:
                raise UpdateError(f"set the {args.api_key_env} environment variable to an EIA API key")
            parsed = parse_eia(fetch_json(build_eia_url(country, subdivision, api_key)), country, subdivision)
        else:
            if subdivision:
                raise UpdateError("the Eurostat adapter accepts a country/geo selection, not a subdivision")
            if not args.currency:
                raise UpdateError("--currency is required for Eurostat; no currency is inferred")
            currency = _code(args.currency, r"[A-Z]{3}", "currency")
            consumption_band = _code(args.consumption_band, r"KWH[0-9]+-[0-9]+", "consumption band")
            if args.tax_code != "I_TAX":
                raise UpdateError("Alpha 2 supports only Eurostat I_TAX (all taxes and levies included)")
            if args.period and not re.fullmatch(r"[0-9]{4}-S[12]", args.period):
                raise UpdateError("Eurostat period must look like 2025-S2")
            url = build_eurostat_url(country, currency, args.period, consumption_band, args.tax_code, args.dataset_region)
            parsed = parse_eurostat(fetch_json(url), country, currency, consumption_band, args.tax_code, args.dataset_region)
        write_profile(args.output.resolve(), make_profile(parsed, retrieved_at), args.replace)
        print(f"Saved official rate snapshot to {args.output}")
        return 0
    except (OSError, UpdateError, urllib.error.URLError) as exc:
        print(f"Rate update stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
