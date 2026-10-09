"""Module entrypoint. Late-version commands stay paper-only."""

from __future__ import annotations

import json
import sys

from crypto_intel.cli import main as cli_main
from crypto_intel.intel import inform
from crypto_intel.market import group_by_symbol, load_candles
from crypto_intel.models import Side
from crypto_intel.v18 import apply_v18, data_security_architecture, information_console
from crypto_intel.v21 import apply_v21, data_residency_plane, research_clock
from crypto_intel.v22 import apply_v22, kill_chain_architecture, liquidity_desk


def _rows(fixture: str, guard) -> list[dict[str, object]]:
    grouped = group_by_symbol(load_candles(fixture))
    benchmark = grouped.get("ETH-USD")
    rows = []
    for symbol, series in grouped.items():
        row = inform(series, benchmark=None if symbol == "ETH-USD" else benchmark)
        proposed = float(row["size_fraction"])
        side = Side(str(row["side"]))
        guarded = guard(series, proposed_size=proposed, side=side)
        guarded["prior_size"] = proposed
        rows.append(guarded)
    return rows


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    handled = {"v18", "console", "datasec", "v21", "clock", "residency", "v22", "desk", "killchain"}
    if args and args[0] in handled:
        command = args[0]
        if command == "datasec":
            print(json.dumps(data_security_architecture(), indent=2))
            return 0
        if command == "residency":
            print(json.dumps(data_residency_plane(), indent=2))
            return 0
        if command == "killchain":
            print(json.dumps(kill_chain_architecture(), indent=2))
            return 0
        if len(args) < 2:
            raise SystemExit(f"{command} requires a fixture path")
        if command in {"v18", "console"}:
            rows = _rows(args[1], apply_v18)
            payload = information_console(rows) if command == "console" else rows
        elif command in {"v22", "desk"}:
            rows = _rows(args[1], apply_v22)
            payload = liquidity_desk(rows) if command == "desk" else rows
        else:
            rows = _rows(args[1], apply_v21)
            payload = research_clock(rows) if command == "clock" else rows
        print(json.dumps(payload, indent=2))
        return 0
    return cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
