"""v0.23 flow and provenance guards, plus a data-flow security plane.

Nineteenth pass. Guards can only shrink paper size. The information bus is an
offline artifact. The data-flow plane separates ingest, research, audit, and
egress. It never stores key material and never opens an execution zone.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

FLOW_NOTES = {
    AssetClass.MAJOR.value: "vol-spike haircut when the last range is at least twice the prior median range",
    AssetClass.LARGE_CAP_ALT.value: "failed follow-through haircut on a down close with range above 2 percent",
    AssetClass.STABLECOIN.value: "peg-velocity watch when the absolute deviation increases by at least 15 bp",
    AssetClass.DEFI.value: "oracle-gap haircut when the open gaps at least 2.5 percent from the prior close",
    AssetClass.MEME.value: "exhaustion-wick veto when the upper wick is at least 55 percent of the range",
    AssetClass.L2.value: "fee-spike haircut when volume is at least twice the median and the range exceeds 3 percent",
    AssetClass.RWA.value: "stale-nav haircut when the last three closes are identical",
    AssetClass.PERPETUAL.value: "carry-squeeze veto when funding is negative and the three-bar rise exceeds 3 percent",
}

ZONES = ("ingest", "research", "audit", "egress")
ALLOWED_FLOWS = {
    ("ingest", "research"),
    ("research", "audit"),
    ("research", "egress"),
    ("audit", "audit"),
}
BLOCKED_CLASSES = {"secret", "personal", "wallet", "trade_key"}


def apply_v23(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Nineteenth-pass flow guard. Size cannot increase."""
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    size = proposed_size if side in {Side.LONG, Side.SHORT} else 0.0
    if asset_class is AssetClass.MAJOR:
        size, note = _major(candles, size)
    elif asset_class is AssetClass.LARGE_CAP_ALT:
        size, note = _alt(candles, size)
    elif asset_class is AssetClass.STABLECOIN:
        size, note = 0.0, _stable(candles)
    elif asset_class is AssetClass.DEFI:
        size, note = _defi(candles, size)
    elif asset_class is AssetClass.MEME:
        size, note = _meme(candles, size)
    elif asset_class is AssetClass.L2:
        size, note = _l2(candles, size)
    elif asset_class is AssetClass.RWA:
        size, note = _rwa(candles, size)
    else:
        size, note = _perpetual(candles, size)
    size = min(size, proposed_size if proposed_size > 0 else 0.0)
    return {
        "symbol": candles[-1].symbol,
        "asset_class": asset_class.value,
        "side": side.value if size > 0 else Side.FLAT.value,
        "size_fraction": round(max(size, 0.0), 6),
        "note": note,
        "guard": FLOW_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _range_pct(candle: Candle) -> float:
    if not candle.close:
        return 0.0
    return (candle.high - candle.low) / candle.close


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = [_range_pct(bar) for bar in candles[-8:-1]]
    base = float(median(prior)) if prior else 0.0
    last = _range_pct(candles[-1])
    if base > 0 and last >= base * 2.0 and size > 0:
        return size * 0.5, "major vol spike: last range at least twice the prior median range"
    return size, "major flow guard not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    previous = candles[-2]
    if last.close < previous.close and _range_pct(last) >= 0.02 and size > 0:
        return size * 0.5, "alt failed follow-through: close below prior close and range above 2 percent"
    return size, "alt flow guard not triggered"


def _stable(candles: list[Candle]) -> str:
    previous = abs(candles[-2].close - 1.0)
    current = abs(candles[-1].close - 1.0)
    if current - previous >= 0.0015:
        return "stable peg velocity: deviation increased by at least 15 bp"
    return "stable flow guard not triggered"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    if previous and abs(candles[-1].open / previous - 1.0) >= 0.025 and size > 0:
        return size * 0.5, "defi oracle-gap proxy: open gap at least 2.5 percent"
    return size, "defi flow guard not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = last.high - last.low
    if span <= 0 or size <= 0:
        return size, "meme flow guard not triggered"
    wick = (last.high - max(last.open, last.close)) / span
    if wick >= 0.55:
        return 0.0, "meme exhaustion wick: upper wick at least 55 percent of range"
    return size, "meme flow guard not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    base = float(median(bar.volume for bar in candles[-8:-1])) or 1.0
    last = candles[-1]
    if last.volume >= base * 2.0 and _range_pct(last) >= 0.03 and size > 0:
        return size * 0.5, "l2 fee-spike proxy: volume at least twice the median and range above 3 percent"
    return size, "l2 flow guard not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-3:]]
    if len(set(closes)) == 1 and size > 0:
        return size * 0.5, "rwa stale nav: three identical closes"
    return size, "rwa flow guard not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    start = candles[-4].close
    rise = candles[-1].close / start - 1.0 if start else 0.0
    if candles[-1].funding_rate < 0 and rise > 0.03 and size > 0:
        return 0.0, "perp carry squeeze: negative funding and three-bar rise above 3 percent"
    return size, "perp flow guard not triggered"


def information_bus(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline information bus. A bus packet is not an order and cannot raise size."""
    material = "|".join(
        f"{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}:{row.get('note')}" for row in rows
    )
    digest = hashlib.sha256(material.encode()).hexdigest()
    triggered = [row for row in rows if "not triggered" not in str(row.get("note", ""))]
    gross = round(sum(float(row.get("size_fraction") or 0.0) for row in rows), 6)
    return {
        "version": "0.23.0",
        "cadence": "offline information bus; no socket",
        "rows": rows,
        "triggered_count": len(triggered),
        "gross_paper_size": gross,
        "bus_digest": digest,
        "zones": list(ZONES),
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def screen_flow(origin: str, destination: str, data_class: str) -> dict[str, object]:
    """Least-privilege data-flow check. Execution is not a destination."""
    if origin not in ZONES or destination not in ZONES:
        raise ValueError("unknown data-flow zone")
    if data_class not in {"public_market", "research_internal", "audit", "secret", "personal", "wallet", "trade_key"}:
        raise ValueError("unknown data class")
    blocked_class = data_class in BLOCKED_CLASSES and destination == "egress"
    allowed_pair = (origin, destination) in ALLOWED_FLOWS and not blocked_class
    if data_class == "audit" and destination != "audit":
        allowed_pair = False
    return {
        "origin": origin,
        "destination": destination,
        "data_class": data_class,
        "allowed": allowed_pair,
        "can_trade": False,
        "can_enable_live": False,
        "reason": "flow refused" if not allowed_pair else "research flow stays inside the paper plane",
    }


def data_flow_plane() -> dict[str, object]:
    """Cyber and data-security flow plane. Rules only. No execution zone."""
    return {
        "version": "0.23.0",
        "framework": "research data-flow plane; not a NIST, ISO, SOC, or PDPA certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "material_stored": False,
        "zones": list(ZONES),
        "blocked_classes_on_egress": sorted(BLOCKED_CLASSES),
        "controls": [
            {"name": "flow_guard", "effect": "asset-class flow guards can only shrink paper size"},
            {"name": "information_bus", "effect": "the bus publishes a provenance digest, not an order"},
            {"name": "zone_screen", "effect": "secret, wallet, personal, and trade-key classes cannot reach egress"},
            {"name": "no_execution_zone", "effect": "execution is not a zone and cannot be enabled"},
        ],
        "duties": [
            {"identity": "researcher", "can_emit_bus": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_emit_bus": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_emit_bus": False, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_store_secret": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "a flow guard cannot raise a class size cap",
            "an information-bus digest is an information artifact, not an order",
            "secret, personal, wallet, and trade-key classes cannot cross to egress",
            "audit records stay in the audit zone",
            "there is still no execution zone",
        ],
    }
