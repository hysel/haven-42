#!/usr/bin/env python3
"""Calculate a plain-language electricity estimate from model energy evidence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
from typing import Any


class CostError(ValueError):
    """The cost estimate input is unsafe or incomplete."""


RATE_PROFILE_KIND = "haven42-electricity-rate-profile"
SOURCE_KINDS = {"manual-bill-rate", "official-average", "utility-tariff"}


def finite(value: Any, *, minimum: float = 0, maximum: float) -> float:
    if isinstance(value, bool):
        raise CostError("invalid-number")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise CostError("invalid-number") from error
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise CostError("invalid-number")
    return number


def load_evidence(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise CostError("unsafe-evidence-file")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CostError("invalid-evidence-file") from error
    if not isinstance(value, dict):
        raise CostError("invalid-evidence-file")
    evidence = value.get("evidence")
    metrics = value.get("metrics")
    if (
        value.get("schemaVersion") != 1
        or value.get("kind") != "haven42-model-energy-measurement"
        or value.get("outcome") != "passed"
        or not isinstance(metrics, dict)
        or evidence != {
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
            "containsProviderEndpoint": False,
            "automaticPromotionAllowed": False,
        }
    ):
        raise CostError("untrusted-energy-evidence")
    return value


def _short_text(value: Any, *, pattern: str, error: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise CostError(error)
    return value


def load_rate_profile(path: Path) -> dict[str, Any]:
    """Load one country-aware rate without making a network or location request."""
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 256 * 1024:
            raise CostError("unsafe-rate-profile")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CostError("invalid-rate-profile") from error
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise CostError("invalid-rate-profile")
    if value.get("kind") != RATE_PROFILE_KIND:
        raise CostError("invalid-rate-profile")
    if value.get("locationWasInferred") is not False:
        raise CostError("rate-profile-location-must-be-explicit")
    if value.get("estimateOnly") is not True:
        raise CostError("rate-profile-must-be-estimate-only")

    source_kind = _short_text(
        value.get("sourceKind"), pattern=r"[a-z][a-z0-9-]{1,39}",
        error="invalid-rate-source-kind",
    )
    if source_kind not in SOURCE_KINDS:
        raise CostError("invalid-rate-source-kind")
    source_id = _short_text(
        value.get("sourceId"), pattern=r"[a-z][a-z0-9-]{1,63}",
        error="invalid-rate-source-id",
    )
    country = _short_text(
        value.get("countryCode"), pattern=r"[A-Z]{2}", error="invalid-country-code",
    )
    currency = _short_text(
        value.get("currency"), pattern=r"[A-Z]{3}", error="invalid-currency",
    )
    subdivision = value.get("subdivisionCode")
    if subdivision is not None:
        _short_text(
            subdivision, pattern=country + r"-[A-Z0-9]{1,3}",
            error="invalid-subdivision-code",
        )
    effective_period = _short_text(
        value.get("effectivePeriod"), pattern=r"[0-9]{4}(?:-[0-9]{2}|-S[12])?",
        error="invalid-effective-period",
    )
    tax_scope = _short_text(
        value.get("taxScope"), pattern=r"[a-z][a-z0-9-]{1,47}",
        error="invalid-tax-scope",
    )
    display_places = value.get("currencyDecimalPlaces", 2)
    if isinstance(display_places, bool) or not isinstance(display_places, int) or not 0 <= display_places <= 4:
        raise CostError("invalid-currency-decimal-places")
    rate = finite(value.get("ratePerKwh"), maximum=10_000_000)

    source_url = value.get("sourceUrl")
    if source_kind == "manual-bill-rate":
        if source_id != "manual-user-entry" or source_url is not None:
            raise CostError("invalid-manual-rate-profile")
    else:
        if not isinstance(source_url, str) or not re.fullmatch(r"https://[^\s]{1,500}", source_url):
            raise CostError("invalid-official-rate-source-url")

    return {
        "sourceKind": source_kind,
        "sourceId": source_id,
        "countryCode": country,
        "subdivisionCode": subdivision,
        "currency": currency,
        "currencyDecimalPlaces": display_places,
        "ratePerKwh": rate,
        "effectivePeriod": effective_period,
        "taxScope": tax_scope,
        "sourceUrl": source_url,
        "estimateOnly": True,
        "locationWasInferred": False,
    }


def calculate(evidence: dict[str, Any], *, rate: float, hours: float, days: int,
              currency: str, additional_system_watts: float = 0,
              rate_profile: dict[str, Any] | None = None,
              currency_decimal_places: int = 2) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise CostError("invalid-currency")
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 366:
        raise CostError("invalid-days")
    if (
        isinstance(currency_decimal_places, bool)
        or not isinstance(currency_decimal_places, int)
        or not 0 <= currency_decimal_places <= 4
    ):
        raise CostError("invalid-currency-decimal-places")
    if rate_profile is not None:
        currency_decimal_places = rate_profile["currencyDecimalPlaces"]
    gpu_watts = finite(evidence["metrics"].get("loadAverageWatts"), maximum=2_000)
    extra_watts = finite(additional_system_watts, maximum=5_000)
    checked_rate = finite(rate, maximum=10_000_000)
    checked_hours = finite(hours, maximum=24)
    gpu_kwh = gpu_watts / 1000 * checked_hours * days
    total_kwh = (gpu_watts + extra_watts) / 1000 * checked_hours * days
    result = {
        "model": evidence["identity"].get("model"),
        "accelerator": evidence["environment"].get("acceleratorModel"),
        "averageMeasuredGpuWatts": round(gpu_watts, 3),
        "additionalEstimatedSystemWatts": round(extra_watts, 3),
        "usageHoursPerDay": round(checked_hours, 3),
        "billingDays": days,
        "electricityRatePerKwh": round(checked_rate, 6),
        "currency": currency,
        "estimatedGpuOnlyKwh": round(gpu_kwh, 6),
        "estimatedGpuOnlyCost": round(gpu_kwh * checked_rate, currency_decimal_places),
        "estimatedCombinedKwh": round(total_kwh, 6),
        "estimatedCombinedCost": round(total_kwh * checked_rate, currency_decimal_places),
        "combinedEstimateUsesOperatorProvidedSystemOverhead": extra_watts > 0,
        "currencyDecimalPlaces": currency_decimal_places,
    }
    if rate_profile is None:
        result["rateProvenance"] = {
            "sourceKind": "manual-bill-rate",
            "sourceId": "manual-user-entry",
            "countryCode": None,
            "subdivisionCode": None,
            "effectivePeriod": None,
            "taxScope": "user-entered-unknown",
            "sourceUrl": None,
            "estimateOnly": True,
            "locationWasInferred": False,
        }
    else:
        result["rateProvenance"] = {
            key: rate_profile[key]
            for key in (
                "sourceKind", "sourceId", "countryCode", "subdivisionCode",
                "effectivePeriod", "taxScope", "sourceUrl", "estimateOnly",
                "locationWasInferred",
            )
        }
    result["notAUtilityBillPrediction"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    rate_group = parser.add_mutually_exclusive_group(required=True)
    rate_group.add_argument("--rate", type=float, help="Electricity price per kWh from your bill")
    rate_group.add_argument(
        "--rate-profile", type=Path,
        help="Validated country-aware manual or official-average rate profile",
    )
    parser.add_argument("--hours-per-day", type=float, required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--currency-decimal-places", type=int, default=2)
    parser.add_argument("--additional-system-watts", type=float, default=0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        rate_profile = load_rate_profile(args.rate_profile) if args.rate_profile else None
        rate = rate_profile["ratePerKwh"] if rate_profile else args.rate
        currency = rate_profile["currency"] if rate_profile else args.currency
        result = calculate(
            load_evidence(args.evidence),
            rate=rate,
            hours=args.hours_per_day,
            days=args.days,
            currency=currency,
            additional_system_watts=args.additional_system_watts,
            rate_profile=rate_profile,
            currency_decimal_places=args.currency_decimal_places,
        )
    except (CostError, KeyError):
        # Evidence and rate profiles are private local inputs. Do not echo
        # exception text because parsers can include input values or paths.
        parser.error(
            "The cost input could not be validated. Check the evidence and rate-profile files."
        )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Model: {result['model']}")
        print(f"Graphics card: {result['accelerator']}")
        print(f"Measured graphics-card average: {result['averageMeasuredGpuWatts']} W")
        places = result["currencyDecimalPlaces"]
        print(
            f"Estimated graphics-card cost: {result['estimatedGpuOnlyCost']:.{places}f} "
            f"{result['currency']} for {result['billingDays']} days"
        )
        if result["combinedEstimateUsesOperatorProvidedSystemOverhead"]:
            print(
                f"Estimated combined cost: {result['estimatedCombinedCost']:.{places}f} "
                f"{result['currency']} (includes the system overhead you entered)"
            )
        else:
            print("This is a graphics-card-only estimate, not the whole computer bill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
