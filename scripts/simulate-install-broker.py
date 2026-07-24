#!/usr/bin/env python3
"""Validate a simulated installation request without machine effects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from system_readiness import ReadinessError, simulate_install_request


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the non-installing Haven 42 broker simulator.")
    parser.add_argument("--request-path", required=True)
    args = parser.parse_args()
    try:
        request = json.loads(Path(args.request_path).read_text(encoding="utf-8"))
        print(json.dumps(simulate_install_request(request), indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ReadinessError) as error:
        print(f"Installation simulation rejected input: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
