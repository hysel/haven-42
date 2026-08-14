#!/usr/bin/env python3
"""Network-free checks for the local electricity estimate service and UI."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from electricity_rate_service import ElectricityRateError, lookup_official_rate  # noqa: E402


def main() -> None:
    eia_payload = {"response": {"data": [{
        "period": "2026-05", "stateid": "NY", "stateDescription": "New York",
        "sectorid": "RES", "price": "29.93", "price-units": "cents per kilowatt-hour",
    }]}}
    seen_urls: list[str] = []

    def eia_fetch(url: str):
        seen_urls.append(url)
        return eia_payload

    eia = lookup_official_rate(
        {"source": "eia", "country": "US", "currency": "USD", "region": "NY"},
        fetch_json=eia_fetch,
        environment={"EIA_API_KEY": "test-secret"},
    )
    assert eia["ratePerKwh"] == 0.2993 and eia["subdivisionCode"] == "US-NY"
    assert eia["locationWasInferred"] is False and eia["estimateOnly"] is True
    assert "test-secret" in seen_urls[0] and "test-secret" not in str(eia)

    eurostat_payload = {
        "id": ["nrg_cons", "unit", "tax", "currency", "geo", "time"],
        "size": [1, 1, 1, 1, 1, 2],
        "dimension": {
            "nrg_cons": {"category": {"index": {"KWH2500-4999": 0}}},
            "unit": {"category": {"index": {"KWH": 0}}},
            "tax": {"category": {"index": {"I_TAX": 0}}},
            "currency": {"category": {"index": {"NAC": 0}}},
            "geo": {"category": {"index": {"DE": 0}}},
            "time": {"category": {"index": {"2025-S1": 0, "2025-S2": 1}}},
        },
        "value": {"0": 0.38, "1": 0.3869},
    }
    eurostat = lookup_official_rate(
        {"source": "eurostat", "country": "DE", "currency": "EUR", "region": ""},
        fetch_json=lambda _url: eurostat_payload,
        environment={},
    )
    assert eurostat["ratePerKwh"] == 0.3869 and eurostat["effectivePeriod"] == "2025-S2"
    assert eurostat["currency"] == "EUR"

    for hostile in (
        {"source": "eia", "country": "CA", "currency": "USD", "region": ""},
        {"source": "eurostat", "country": "DE", "currency": "EUR", "region": "BE"},
        {"source": "other", "country": "US", "currency": "USD", "region": ""},
    ):
        try:
            lookup_official_rate(hostile, fetch_json=lambda _url: {}, environment={})
        except ElectricityRateError:
            pass
        else:
            raise AssertionError("unsupported or mismatched rate selection must stop")

    html = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    app = (ROOT / "web/static/app.js").read_text(encoding="utf-8")
    assert 'id="energy-estimator-panel"' in html
    assert "This estimates graphics-card electricity only" in html
    assert "Use the price from my electricity bill · most accurate" in html
    assert "Use an average U.S. household price" in html
    assert "Use an average European household price" in html
    assert "Your electricity-bill information stays private" in html
    assert "does not save, upload, or add that price or your usage values to troubleshooting logs" in html
    assert "contacts the named statistics service, but never sends your bill price" in html
    assert "location is never inferred" in app
    assert "state.electricityRateProfile = null" in app
    assert 'id="energy-country" autocomplete="country"' in html
    assert '<option value="US" data-currency="USD" selected>United States — USD</option>' in html
    assert '<option value="DE" data-currency="EUR">Germany — EUR</option>' in html
    assert "Another country — enter currency below" in html
    assert "EUROSTAT_COUNTRIES" in app and '"PL"' in app
    assert "selected?.dataset.currency" in app
    assert 'byId("energy-currency").value = currency || ""' in app
    assert "filterEnergyCountries(source)" in app
    assert 'id="rail-cost-estimate"' in html and 'id="rail-cost-value"' in html
    assert 'id="energy-pin-status" type="checkbox"' in html
    assert 'id="status-energy-widget"' in html
    assert 'id="status-energy-kwh"' in html and 'id="status-energy-cost"' in html
    assert "The widget stays visible while Haven 42 is open" in html
    assert "function syncEnergyStatusWidget()" in app
    assert "state.energyEstimate = Object.freeze" in app
    assert 'byId("status-energy-remove").addEventListener("click"' in app
    assert "/api/electricity-rate" in app
    assert "automatic model" not in html.lower() or "does not detect your location or change your model choice" in html
    print("electricity-rate UI service checks passed")


if __name__ == "__main__":
    main()
