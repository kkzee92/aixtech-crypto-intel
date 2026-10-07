"""Standalone entry for the v0.18 information commands.

Paper research only. This module does not place orders.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from crypto_intel.cli import _guarded_rows
from crypto_intel.v18 import apply_v18, api_plane, information_wire


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="crypto-intel-v18", description="v0.18 paper information commands")
    sub = parser.add_subparsers(dest="command", required=True)
    micro = sub.add_parser("v18", help="per-class microstructure guard; size can only shrink")
    micro.add_argument("fixture")
    wire = sub.add_parser("wire", help="offline information wire; never an order")
    wire.add_argument("fixture")
    sub.add_parser("apiscope", help="API and data-security plane; no execution zone")
    args = parser.parse_args(argv)
    if args.command == "v18":
        print(json.dumps(_guarded_rows(args.fixture, apply_v18), indent=2))
        return 0
    if args.command == "wire":
        print(json.dumps(information_wire(_guarded_rows(args.fixture, apply_v18)), indent=2))
        return 0
    print(json.dumps(api_plane(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
