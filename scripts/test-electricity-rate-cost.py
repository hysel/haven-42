#!/usr/bin/env python3
"""Checks for country-neutral, privacy-preserving electricity estimates."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/calculate-model-energy-cost.py"
CONTRACT = ROOT / "config/electricity-rate-estimate-contract.json"
SOURCES = ROOT / "config/electricity-rate-source-registry.json"


def load_module():
    specification = importlib.util.spec_from_file_location("electricity_cost", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def refused(callback, message: str) -> None:
    try:
        callback()
    except Exception as error:
        assert str(error) == message, (str(error), message)
    else:
        raise AssertionError(f"expected refusal: {message}")


def profile(**changes):
    value = {
        "schemaVersion": 1,
        "kind": "haven42-electricity-rate-profile",
        "sourceKind": "official-average",
        "sourceId": "eurostat-household-electricity",
        "countryCode": "DE",
        "subdivisionCode": None,
        "currency": "EUR",
        "currencyDecimalPlaces": 2,
        "ratePerKwh": 0.4,
        "effectivePeriod": "2025-S2",
        "taxScope": "including-all-taxes",
        "sourceUrl": "https://ec.europa.eu/eurostat/",
        "estimateOnly": True,
        "locationWasInferred": False,
    }
    value.update(changes)
    return value


def main() -> int:
    module = load_module()
    evidence = {
        "identity": {"model": "fixture:1b"},
        "environment": {"acceleratorModel": "Fixture GPU"},
        "metrics": {"loadAverageWatts": 100},
    }

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "rate.json"
        path.write_text(json.dumps(profile()), encoding="utf-8")
        loaded = module.load_rate_profile(path)
        assert loaded["countryCode"] == "DE"
        assert loaded["currency"] == "EUR"
        estimate = module.calculate(
            evidence, rate=loaded["ratePerKwh"], hours=2, days=30,
            currency=loaded["currency"], rate_profile=loaded,
        )
        assert estimate["estimatedGpuOnlyKwh"] == 6
        assert estimate["estimatedGpuOnlyCost"] == 2.4
        assert estimate["rateProvenance"] == {
            "sourceKind": "official-average",
            "sourceId": "eurostat-household-electricity",
            "countryCode": "DE",
            "subdivisionCode": None,
            "effectivePeriod": "2025-S2",
            "taxScope": "including-all-taxes",
            "sourceUrl": "https://ec.europa.eu/eurostat/",
            "estimateOnly": True,
            "locationWasInferred": False,
        }
        assert estimate["notAUtilityBillPrediction"] is True

        # Large-denomination currencies and zero-decimal display are valid.
        path.write_text(json.dumps(profile(
            sourceKind="manual-bill-rate",
            sourceId="manual-user-entry",
            countryCode="JP",
            currency="JPY",
            currencyDecimalPlaces=0,
            ratePerKwh=31,
            effectivePeriod="2026-08",
            taxScope="user-entered-bill-rate",
            sourceUrl=None,
        )), encoding="utf-8")
        loaded = module.load_rate_profile(path)
        assert loaded["currencyDecimalPlaces"] == 0
        assert loaded["ratePerKwh"] == 31
        estimate = module.calculate(
            evidence, rate=loaded["ratePerKwh"], hours=1, days=1,
            currency=loaded["currency"], rate_profile=loaded,
        )
        assert estimate["currencyDecimalPlaces"] == 0
        assert estimate["estimatedGpuOnlyCost"] == 3

        path.write_text(json.dumps(profile(locationWasInferred=True)), encoding="utf-8")
        refused(
            lambda: module.load_rate_profile(path),
            "rate-profile-location-must-be-explicit",
        )
        path.write_text(json.dumps(profile(estimateOnly=False)), encoding="utf-8")
        refused(
            lambda: module.load_rate_profile(path),
            "rate-profile-must-be-estimate-only",
        )
        path.write_text(json.dumps(profile(countryCode="DEU")), encoding="utf-8")
        refused(lambda: module.load_rate_profile(path), "invalid-country-code")
        path.write_text(json.dumps(profile(currency="EURO")), encoding="utf-8")
        refused(lambda: module.load_rate_profile(path), "invalid-currency")
        path.write_text(json.dumps(profile(sourceUrl="http://example.test/rate")), encoding="utf-8")
        refused(
            lambda: module.load_rate_profile(path),
            "invalid-official-rate-source-url",
        )

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["privacy"]["automaticIpGeolocationAllowed"] is False
    assert contract["calculation"]["currencyConversionAllowed"] is False
    assert contract["calculation"]["wholeComputerClaimRequiresWallMeasurement"] is True
    registry = json.loads(SOURCES.read_text(encoding="utf-8"))
    assert registry["defaultSourceId"] == "manual-user-entry"
    assert registry["automaticLocationDetection"] is False
    ids = {source["id"] for source in registry["sources"]}
    assert ids == {
        "manual-user-entry",
        "eia-us-residential-average",
        "eurostat-household-electricity",
        "openei-us-utility-rate",
    }
    assert next(
        source for source in registry["sources"]
        if source["id"] == "manual-user-entry"
    )["coverage"] == "worldwide"

    source = SCRIPT.read_text(encoding="utf-8")
    assert "geolocation" not in source.casefold()
    assert "currency conversion" not in source.casefold()
    print("country-neutral electricity-cost checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
