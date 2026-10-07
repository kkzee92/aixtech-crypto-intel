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
from crypto_intel.v14 import apply_v14, evidence_plane, information_watchtower
from crypto_intel.v15 import apply_v15, information_ledger, segregation_plane
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
    decay = sub.add_parser("v14", help="v0.14 per-class decay guard; size can only shrink")
    decay.add_argument("fixture")
    watch = sub.add_parser("watchtower", help="v0.14 offline information watchtower; never an order")
    watch.add_argument("fixture")
    sub.add_parser("evidence", help="v0.14 evidence plane; no execution zone")
    concentration = sub.add_parser("v15", help="v0.15 per-class concentration guard; size can only shrink")
    concentration.add_argument("fixture")
    ledger = sub.add_parser("ledger", help="v0.15 offline information ledger; never an order")
    ledger.add_argument("fixture")
    sub.add_parser("segregation", help="v0.15 segregation plane; no execution zone")
    return parser
