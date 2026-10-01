"""Command line for the paper research system."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from crypto_intel.engine import backtest, run_once
from crypto_intel.market import group_by_symbol, load_candles
from crypto_intel.security import AuditLog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="crypto-intel", description="Paper-only crypto information system")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="score the latest bar of each synthetic series")
    scan.add_argument("fixture")
    demo = sub.add_parser("demo", help="scan plus a paper backtest of the first series")
    demo.add_argument("fixture")
    bt = sub.add_parser("backtest", help="paper backtest one symbol")
    bt.add_argument("fixture")
    bt.add_argument("--symbol", required=True)
    return parser


def scan(fixture: str) -> list[dict[str, object]]:
    grouped = group_by_symbol(load_candles(fixture))
    audit = AuditLog()
    rows: list[dict[str, object]] = []
    benchmark = grouped.get("ETH-USD")
    for symbol, series in grouped.items():
        _, fill = run_once(series, audit=audit, benchmark=benchmark if symbol != "ETH-USD" else None)
        rows.append(
            {
                "symbol": symbol,
                "asset_class": fill.asset_class.value,
                "side": fill.side.value,
                "size_fraction": fill.size_fraction,
                "reason": fill.reason,
                "mode": fill.mode.value,
            }
        )
    if not audit.verify():
        raise RuntimeError("audit chain failed verification")
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"scan", "demo"}:
        rows = scan(args.fixture)
        print(json.dumps(rows, indent=2))
        if args.command == "demo":
            grouped = group_by_symbol(load_candles(args.fixture))
            first = next(iter(grouped.values()))
            print(json.dumps(backtest(first), indent=2))
        return 0
    grouped = group_by_symbol(load_candles(args.fixture))
    if args.symbol not in grouped:
        raise SystemExit(f"unknown symbol {args.symbol}")
    print(json.dumps(backtest(grouped[args.symbol]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
