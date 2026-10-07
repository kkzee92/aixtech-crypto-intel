"""Command line for the paper research system."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from crypto_intel.automation import pipeline_manifest
from crypto_intel.briefing import build_brief
from crypto_intel.catalog import parameter_digest
from crypto_intel.controls import control_report
from crypto_intel.cross_asset import apply_cross_overlay, basket_report
from crypto_intel.cyber import incident_playbook, key_ceremony, research_packet
from crypto_intel.engine import backtest, run_once
from crypto_intel.enhance import apply_class_enhancement
from crypto_intel.intel import inform
from crypto_intel.market import group_by_symbol, load_candles
from crypto_intel.models import ExecutionMode, Side
from crypto_intel.posture import Role, allow, attest_source, feed_status, mode_status
from crypto_intel.relative import major_relative
from crypto_intel.scorecard import score_book
from crypto_intel.security import AuditLog
from crypto_intel.sleeves import apply_sleeve
from crypto_intel.supply import architecture_report
from crypto_intel.threats import threat_report
from crypto_intel.v08 import apply_v08, data_plane_report, schedule_manifest
from crypto_intel.v09 import apply_v09, research_cycle, zero_trust_report
from crypto_intel.v10 import apply_v10, cyber_plane_report, information_pack
from crypto_intel.v11 import apply_v11, csf_report, information_bulletin
from crypto_intel.v12 import apply_v12, custody_plane, information_desk
from crypto_intel.v13 import apply_v13, information_mesh, resilience_plane
from crypto_intel.walkforward import split_walkforward


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
    brief = sub.add_parser("brief", help="asset-class information brief with regime and cost")
    brief.add_argument("fixture")
    posture = sub.add_parser("posture", help="security control snapshot for a fixture")
    posture.add_argument("fixture")
    score = sub.add_parser("scorecard", help="paper scorecard by asset class on a synthetic fixture")
    score.add_argument("fixture")
    sub.add_parser("controls", help="defensive control catalog and parameter digest")
    intel = sub.add_parser("intel", help="v0.4 quality, confirmation, and vol-targeted paper report")
    intel.add_argument("fixture")
    cross = sub.add_parser("cross", help="v0.5 cross-asset spillover, contagion, and major relative sleeve")
    cross.add_argument("fixture")
    sub.add_parser("threats", help="STRIDE control map for the paper information system")
    walk = sub.add_parser("walkforward", help="chronological paper split for one symbol")
    walk.add_argument("fixture")
    walk.add_argument("--symbol", required=True)
    enhance = sub.add_parser("enhance", help="v0.6 per-class research overlay; size can only shrink")
    enhance.add_argument("fixture")
    sub.add_parser("cyber", help="v0.6 key-scope policy, ceremony checklist, incident playbook")
    sub.add_parser("pipeline", help="v0.7 offline information-pipeline manifest")
    sleeve = sub.add_parser("sleeve", help="v0.7 per-class sleeve; size can only shrink")
    sleeve.add_argument("fixture")
    sub.add_parser("supply", help="v0.7 data-flow, role, and supply-chain snapshot")
    overlay = sub.add_parser("v08", help="v0.8 per-class overlay; size can only shrink")
    overlay.add_argument("fixture")
    sub.add_parser("dataplane", help="v0.8 data-plane architecture; no execution zone")
    sub.add_parser("schedule", help="v0.8 offline information cadence")
    guard = sub.add_parser("v09", help="v0.9 per-class guard; size can only shrink")
    guard.add_argument("fixture")
    sub.add_parser("zerotrust", help="v0.9 zero-trust research plane; no execution zone")
    alerts = sub.add_parser("alerts", help="v0.9 information alerts; never an order")
    alerts.add_argument("fixture")
    liquidity = sub.add_parser("v10", help="v0.10 per-class liquidity guard; size can only shrink")
    liquidity.add_argument("fixture")
    pack = sub.add_parser("pack", help="v0.10 information pack; breadth haircut cannot raise size")
    pack.add_argument("fixture")
    sub.add_parser("cyberplane", help="v0.10 cyber and data-security plane; no execution zone")
    session = sub.add_parser("v11", help="v0.11 per-class session guard; size can only shrink")
    session.add_argument("fixture")
    bulletin = sub.add_parser("bulletin", help="v0.11 information bulletin; never an order")
    bulletin.add_argument("fixture")
    sub.add_parser("csf", help="v0.11 NIST CSF-style control map; no execution zone")
    basis = sub.add_parser("v12", help="v0.12 per-class basis guard; size can only shrink")
    basis.add_argument("fixture")
    desk = sub.add_parser("desk", help="v0.12 information desk; never an order")
    desk.add_argument("fixture")
    sub.add_parser("custody", help="v0.12 custody and data-security plane; no execution zone")
    fragment = sub.add_parser("v13", help="v0.13 per-class fragmentation guard; size can only shrink")
    fragment.add_argument("fixture")
    mesh = sub.add_parser("mesh", help="v0.13 information mesh; disagreement can only shrink size")
    mesh.add_argument("fixture")
    sub.add_parser("resilience", help="v0.13 cyber-resilience plane; no execution zone")
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


def posture(fixture: str) -> dict[str, object]:
    path_text = Path(fixture).read_text(encoding="utf-8")
    payload = json.loads(path_text)
    digest = attest_source(str(payload.get("label")), path_text)
    grouped = group_by_symbol(load_candles(fixture))
    first = next(iter(grouped.values()))
    previous = first[-2].close if len(first) > 1 else None
    feed = feed_status(first[-1].close, previous, age_seconds=0)
    mode = mode_status(ExecutionMode.PAPER)
    return {
        "source_attestation": digest,
        "label": payload.get("label"),
        "paper_only": mode.ok,
        "feed": feed.detail,
        "feed_ok": feed.ok,
        "researcher_can_scan": allow(Role.RESEARCHER, "scan"),
        "operator_can_trade": allow(Role.OPERATOR, "place_order"),
        "live_enabled": False,
    }


def _guarded_rows(fixture: str, apply) -> list[dict[str, object]]:
    grouped = group_by_symbol(load_candles(fixture))
    benchmark = grouped.get("ETH-USD")
    rows = []
    for symbol, series in grouped.items():
        row = inform(series, benchmark=None if symbol == "ETH-USD" else benchmark)
        proposed = float(row["size_fraction"])
        side = Side(str(row["side"]))
        guarded = apply(series, proposed_size=proposed, side=side)
        guarded["prior_size"] = proposed
        rows.append(guarded)
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
    if args.command == "brief":
        grouped = group_by_symbol(load_candles(args.fixture))
        print(json.dumps(build_brief(grouped), indent=2))
        return 0
    if args.command == "posture":
        print(json.dumps(posture(args.fixture), indent=2))
        return 0
    if args.command == "scorecard":
        grouped = group_by_symbol(load_candles(args.fixture))
        print(json.dumps(score_book(grouped), indent=2))
        return 0
    if args.command == "controls":
        print(json.dumps(control_report(), indent=2))
        return 0
    if args.command == "intel":
        grouped = group_by_symbol(load_candles(args.fixture))
        benchmark = grouped.get("ETH-USD")
        rows = [
            inform(series, benchmark=None if symbol == "ETH-USD" else benchmark) for symbol, series in grouped.items()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    if args.command == "cross":
        grouped = group_by_symbol(load_candles(args.fixture))
        report = basket_report(grouped)
        benchmark = grouped.get("ETH-USD")
        rows = []
        for symbol, series in grouped.items():
            row = inform(series, benchmark=None if symbol == "ETH-USD" else benchmark)
            rows.append(apply_cross_overlay(row, report))
        relative = None
        if "BTC-USD" in grouped and "ETH-USD" in grouped:
            relative = major_relative(grouped["BTC-USD"], grouped["ETH-USD"])
        print(json.dumps({"basket": report, "relative": relative, "rows": rows}, indent=2))
        return 0
    if args.command == "threats":
        print(json.dumps(threat_report(), indent=2))
        return 0
    if args.command == "walkforward":
        grouped = group_by_symbol(load_candles(args.fixture))
        if args.symbol not in grouped:
            raise SystemExit(f"unknown symbol {args.symbol}")
        print(json.dumps(split_walkforward(grouped[args.symbol]), indent=2))
        return 0
    if args.command == "enhance":
        grouped = group_by_symbol(load_candles(args.fixture))
        benchmark = grouped.get("ETH-USD")
        rows = []
        for symbol, series in grouped.items():
            row = inform(series, benchmark=None if symbol == "ETH-USD" else benchmark)
            proposed = float(row["size_fraction"])
            side = Side(str(row["side"]))
            enhanced = apply_class_enhancement(
                series,
                proposed_size=proposed,
                side=side,
                benchmark=None if symbol == "ETH-USD" else benchmark,
            )
            enhanced["prior_size"] = proposed
            rows.append(enhanced)
        print(json.dumps(rows, indent=2))
        return 0
    if args.command == "cyber":
        print(
            json.dumps(
                {
                    "ceremony": key_ceremony(),
                    "incident": incident_playbook(),
                    "packet": research_packet(parameter_digest(), "SYNTHETIC"),
                },
                indent=2,
            )
        )
        return 0
    if args.command == "pipeline":
        print(json.dumps(pipeline_manifest(), indent=2))
        return 0
    if args.command == "supply":
        print(json.dumps(architecture_report(), indent=2))
        return 0
    if args.command == "schedule":
        print(json.dumps(schedule_manifest(), indent=2))
        return 0
    if args.command == "dataplane":
        print(json.dumps(data_plane_report(), indent=2))
        return 0
    if args.command == "v08":
        print(json.dumps(_guarded_rows(args.fixture, apply_v08), indent=2))
        return 0
    if args.command == "sleeve":
        grouped = group_by_symbol(load_candles(args.fixture))
        benchmark = grouped.get("ETH-USD")
        rows = []
        for symbol, series in grouped.items():
            row = inform(series, benchmark=None if symbol == "ETH-USD" else benchmark)
            proposed = float(row["size_fraction"])
            side = Side(str(row["side"]))
            sleeved = apply_sleeve(
                series,
                proposed_size=proposed,
                side=side,
                benchmark=None if symbol == "ETH-USD" else benchmark,
            )
            sleeved["prior_size"] = proposed
            rows.append(sleeved)
        print(json.dumps(rows, indent=2))
        return 0
    if args.command == "zerotrust":
        print(json.dumps(zero_trust_report(), indent=2))
        return 0
    if args.command == "alerts":
        grouped = group_by_symbol(load_candles(args.fixture))
        rows = []
        for series in grouped.values():
            last = series[-1]
            deviation = abs(last.close - 1.0) if last.asset_class.value == "stablecoin" else 0.0
            rows.append({"asset_class": last.asset_class.value, "deviation": deviation, "stress": False})
        print(json.dumps(research_cycle(rows), indent=2))
        return 0
    if args.command == "v09":
        grouped = group_by_symbol(load_candles(args.fixture))
        benchmark = grouped.get("ETH-USD")
        rows = []
        for symbol, series in grouped.items():
            row = inform(series, benchmark=None if symbol == "ETH-USD" else benchmark)
            proposed = float(row["size_fraction"])
            side = Side(str(row["side"]))
            guarded = apply_v09(
                series,
                proposed_size=proposed,
                side=side,
                benchmark=None if symbol == "ETH-USD" else benchmark,
            )
            guarded["prior_size"] = proposed
            rows.append(guarded)
        print(json.dumps(rows, indent=2))
        return 0
    if args.command == "v10":
        print(json.dumps(_guarded_rows(args.fixture, apply_v10), indent=2))
        return 0
    if args.command == "pack":
        print(json.dumps(information_pack(_guarded_rows(args.fixture, apply_v10)), indent=2))
        return 0
    if args.command == "cyberplane":
        print(json.dumps(cyber_plane_report(), indent=2))
        return 0
    if args.command == "v11":
        print(json.dumps(_guarded_rows(args.fixture, apply_v11), indent=2))
        return 0
    if args.command == "bulletin":
        print(json.dumps(information_bulletin(_guarded_rows(args.fixture, apply_v11)), indent=2))
        return 0
    if args.command == "csf":
        print(json.dumps(csf_report(), indent=2))
        return 0
    if args.command == "v12":
        print(json.dumps(_guarded_rows(args.fixture, apply_v12), indent=2))
        return 0
    if args.command == "desk":
        payload = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        label = str(payload.get("label", ""))
        print(json.dumps(information_desk(_guarded_rows(args.fixture, apply_v12), fixture_label=label), indent=2))
        return 0
    if args.command == "custody":
        print(json.dumps(custody_plane(), indent=2))
        return 0
    if args.command == "v13":
        print(json.dumps(_guarded_rows(args.fixture, apply_v13), indent=2))
        return 0
    if args.command == "mesh":
        grouped = group_by_symbol(load_candles(args.fixture))
        rows = []
        for symbol, series in grouped.items():
            last = series[-1]
            prior = series[-2].close if len(series) > 1 else last.close
            rows.append(
                {
                    "symbol": symbol,
                    "asset_class": last.asset_class.value,
                    "primary_close": last.close,
                    "secondary_close": prior,
                    "size_fraction": 0.0,
                }
            )
        print(json.dumps(information_mesh(rows), indent=2))
        return 0
    if args.command == "resilience":
        print(json.dumps(resilience_plane(), indent=2))
        return 0
    grouped = group_by_symbol(load_candles(args.fixture))
    if args.symbol not in grouped:
        raise SystemExit(f"unknown symbol {args.symbol}")
    print(json.dumps(backtest(grouped[args.symbol]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
