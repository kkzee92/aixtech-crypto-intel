"""Module entrypoint. v0.18 commands are handled here so they stay paper-only."""

from __future__ import annotations

import json
import sys

from crypto_intel.cli import main as cli_main
from crypto_intel.market import group_by_symbol, load_candles
from crypto_intel.models import Side
from crypto_intel.v18 import apply_v18, data_security_architecture, information_console
from crypto_intel.intel import inform


def _guarded_rows(fixture: str) -> list[dict[str, object]]:
    grouped = group_by_symbol(load_candles(fixture))
    benchmark = grouped.get("ETH-USD")
    rows = []
    for symbol, series in grouped.items():
        row = inform(series, benchmark=None if symbol == "ETH-USD" else benchmark)
        proposed = float(row["size_fraction"])
        side = Side(str(row["side"]))
        guarded = apply_v18(series, proposed_size=proposed, side=side)
        guarded["prior_size"] = proposed
        rows.append(guarded)
    return rows


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"v18", "console", "datasec"}:
        command = args[0]
        if command == "datasec":
            print(json.dumps(data_security_architecture(), indent=2))
            return 0
        if len(args) < 2:
            raise SystemExit(f"{command} requires a fixture path")
        rows = _guarded_rows(args[1])
        payload = information_console(rows) if command == "console" else rows
        print(json.dumps(payload, indent=2))
        return 0
    return cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
