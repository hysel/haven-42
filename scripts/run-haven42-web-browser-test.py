#!/usr/bin/env python3
"""Launch the source browser fixture with process-isolated diagnostics."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))
import server as haven_web  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="haven42-browser-diagnostics-") as temporary:
        state = haven_web.HavenState(
            diagnostic_root=Path(temporary) / "Haven42-Logs",
        )
        try:
            app = haven_web.HavenWebServer(("127.0.0.1", 0), state)
        except OSError as error:
            state.diagnostics.close()
            print(f"Could not start Haven 42 local web test server: {error}", file=sys.stderr)
            return 1
        print(f"Haven 42 is available at {app.expected_origin}", flush=True)
        try:
            app.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
        finally:
            app.shutdown()
            app.server_close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
