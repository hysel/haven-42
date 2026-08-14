#!/usr/bin/env python3
"""Deterministic, network-free checks for official rate snapshots."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/update-electricity-rate-snapshot.py"
COST_SCRIPT = ROOT / "scripts/calculate-model-energy-cost.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rate_updater", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_cost_module():
    spec = importlib.util.spec_from_file_location("rate_cost", COST_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    updater = load_module()
    cost = load_cost_module()
    eia = {"response": {"data": [{
        "period": "2026-05", "stateid": "NY", "stateDescription": "New York",
        "sectorid": "RES", "price": "29.93", "price-units": "cents per kilowatt-hour",
    }]}}
    parsed_eia = updater.parse_eia(eia, "US", "US-NY")
    assert parsed_eia["ratePerKwh"] == 0.2993 and parsed_eia["currency"] == "USD"

    eurostat = {
        "id": ["freq", "siec", "nrg_cons", "unit", "tax", "currency", "geo", "time"],
        "size": [1, 1, 1, 1, 1, 1, 1, 2],
        "dimension": {
            "nrg_cons": {"category": {"index": {"KWH2500-4999": 0}}},
            "unit": {"category": {"index": {"KWH": 0}}},
            "tax": {"category": {"index": {"I_TAX": 0}}},
            "currency": {"category": {"index": {"EUR": 0}}},
            "geo": {"category": {"index": {"DE": 0}}},
            "time": {"category": {"index": {"2025-S1": 0, "2025-S2": 1}}},
        },
        "value": {"0": 0.38, "1": 0.3869},
    }
    parsed_eurostat = updater.parse_eurostat(eurostat, "DE", "EUR", "KWH2500-4999", "I_TAX", None)
    assert parsed_eurostat["ratePerKwh"] == 0.3869 and parsed_eurostat["effectivePeriod"] == "2025-S2"

    assert "stateid%5D%5B%5D=NY" in updater.build_eia_url("US", "US-NY", "secret-key")
    assert "geo=DE" in updater.build_eurostat_url("DE", "EUR", "2025-S2", "KWH2500-4999", "I_TAX", None)

    profile = updater.make_profile(parsed_eurostat, "2026-08-13T12:00:00Z")
    assert profile["snapshotVersion"] == 1 and profile["estimateOnly"] is True
    assert profile["locationWasInferred"] is False and "secret-key" not in json.dumps(profile)

    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "rate.json"
        updater.write_profile(output, profile, False)
        assert json.loads(output.read_text(encoding="utf-8"))["ratePerKwh"] == 0.3869
        loaded = cost.load_rate_profile(output)
        assert loaded["sourceId"] == "eurostat-household-electricity"
        assert loaded["effectivePeriod"] == "2025-S2"
        try:
            updater.write_profile(output, profile, False)
        except updater.UpdateError:
            pass
        else:
            raise AssertionError("existing snapshots must require explicit replacement")

    contract = json.loads((ROOT / "config/electricity-rate-snapshot-contract.json").read_text(encoding="utf-8"))
    assert contract["requirements"]["apiCredentialsPersisted"] is False
    print("electricity-rate updater checks passed")


if __name__ == "__main__":
    main()
