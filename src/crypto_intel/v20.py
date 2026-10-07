"""v0.20 inventory-age guards and disclosure-boundary plane.

Sixteenth pass. Guards can only shrink paper size. The disclosure plane
publishes research, audit, or public briefs. It never stores key material
and never opens an execution zone.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.security import redact

INVENTORY_NOTES = {
    AssetClass.MAJOR.value: "participation drought when the last three volumes are below 60 percent of the median",
    AssetClass.LARGE_CAP_ALT.value: "failed follow-through when the close is below the prior three-bar midpoint",
    AssetClass.STABLECOIN.value: "peg-persistence watch when two closes deviate by at least 20 bp",
    AssetClass.DEFI.value: "jump-without-range haircut when price moves 4 percent inside a 1 percent bar",
    AssetClass.MEME.value: "climax-fade veto when a burst bar closes down on falling volume",
    AssetClass.L2.value: "stall haircut when three closes are flat and volume is collapsing",
    AssetClass.RWA.value: "smoothness-break haircut when the last range exceeds three times the median",
    AssetClass.PERPETUAL.value: "funding-flip veto when the last two funding prints change sign",
}

DISPATCH_STAGES = (
    {"stage": "ingest_fixture", "network": False, "can_trade": False},
    {"stage": "inventory_guard", "network": False, "can_trade": False},
    {"stage": "zone_screen", "network": False, "can_trade": False},
    {"stage": "dispatch", "network": False, "can_trade": False},
)

ZONES = ("research_internal", "audit", "public_brief")
REFUSED_ZONE_TOKENS = ("trade", "withdraw", "seed", "private_key", "api_key")


def apply_v20(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Sixteenth-pass inventory-age guard. Size cannot increase."""
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
        "guard": INVENTORY_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _volume_median(candles: list[Candle]) -> float:
    return float(median(bar.volume for bar in candles[-8:])) or 1.0


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _volume_median(candles)
    drought = all(bar.volume < base * 0.6 for bar in candles[-3:])
    if drought and size > 0:
        return size * 0.5, "major participation drought: last three volumes below 60 percent of median"
    return size, "major inventory guard not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    midpoint = sum(bar.close for bar in candles[-4:-1]) / 3.0
    if candles[-1].close < midpoint and size > 0:
        return size * 0.5, "large-cap failed follow-through: close below prior three-bar midpoint"
    return size, "large-cap inventory guard not triggered"


def _stable(candles: list[Candle]) -> str:
    deviations = [abs(bar.close - 1.0) for bar in candles[-2:]]
    if all(deviation >= 0.002 for deviation in deviations):
        return "stablecoin peg-persistence watch: two closes at least 20 bp off peg; size stays zero"
    return "stablecoin inventory guard not triggered; size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    move = abs(last.close / candles[-4].close - 1.0) if candles[-4].close else 0.0
    bar_range = (last.high - last.low) / last.close if last.close else 0.0
    if move >= 0.04 and bar_range < 0.01 and size > 0:
        return size * 0.5, "defi jump-without-range: 4 percent move inside a 1 percent bar"
    return size, "defi inventory guard not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    burst = last.high / candles[-4].close - 1.0 if candles[-4].close else 0.0
    fade = last.close < last.open and last.volume < candles[-2].volume
    if burst >= 0.15 and fade:
        return 0.0, "meme climax fade: burst then down close on falling volume"
    return size, "meme inventory guard not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-3:]]
    flat = max(closes) / min(closes) - 1.0 < 0.002 if min(closes) else False
    collapsing = candles[-1].volume < candles[-3].volume * 0.5
    if flat and collapsing and size > 0:
        return size * 0.5, "l2 stall: three flat closes and collapsing volume"
    return size, "l2 inventory guard not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    ranges = [bar.high - bar.low for bar in candles[-8:-1]]
    typical = float(median(ranges)) or 1.0
    if candles[-1].high - candles[-1].low > typical * 3 and size > 0:
        return size * 0.5, "rwa smoothness break: last range above three times the median"
    return size, "rwa inventory guard not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].funding_rate
    current = candles[-1].funding_rate
    flipped = previous * current < 0
    if flipped:
        return 0.0, "perp funding flip: last two funding prints changed sign"
    return size, "perp inventory guard not triggered"


def information_dispatch(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline inventory packet. A dispatch row is not an order and cannot raise size."""
    material = "|".join(
        f"{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}:{row.get('note')}" for row in rows
    )
    digest = hashlib.sha256(material.encode()).hexdigest()
    haircuts = [row for row in rows if "not triggered" not in str(row.get("note", ""))]
    flat = [row for row in rows if float(row.get("size_fraction", 0.0)) == 0.0]
    by_class: dict[str, int] = {}
    for row in rows:
        key = str(row.get("asset_class", "unknown"))
        by_class[key] = by_class.get(key, 0) + 1
    return {
        "version": "0.20.0",
        "cadence": "offline research cycle; no socket",
        "inputs": ["synthetic_fixture", "injected_public_print"],
        "stages": list(DISPATCH_STAGES),
        "rows": rows,
        "class_counts": by_class,
        "haircut_count": len(haircuts),
        "flat_count": len(flat),
        "dispatch_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def screen_zone(zone: str, text: str) -> dict[str, object]:
    """Screen a brief before it crosses a disclosure boundary."""
    if zone not in ZONES:
        raise ValueError("zone must be research_internal, audit, or public_brief")
    lowered = text.lower()
    blocked = any(token in lowered for token in REFUSED_ZONE_TOKENS)
    public = zone == "public_brief"
    return {
        "zone": zone,
        "allowed": not blocked,
        "redacted": redact(text) if public or blocked else text,
        "size_included": not public,
        "can_trade": False,
        "can_enable_live": False,
        "reason": "refused token in brief" if blocked else "zone screen passed",
    }


def disclosure_boundary() -> dict[str, object]:
    """Disclosure-boundary plane. Zones and rules only. No key material and no execution zone."""
    return {
        "version": "0.20.0",
        "framework": "research disclosure boundary; not a MAS TRM, PDPA, SOC, NIST, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "material_stored": False,
        "zones": list(ZONES),
        "refused_tokens": list(REFUSED_ZONE_TOKENS),
        "controls": [
            {"name": "zone_allowlist", "effect": "briefs may only be research_internal, audit, or public_brief"},
            {"name": "public_minimisation", "effect": "a public brief drops paper size and is redacted"},
            {"name": "credential_block", "effect": "trade, withdrawal, seed, private-key, and api-key tokens are blocked"},
            {"name": "inventory_guard", "effect": "asset-class inventory guards can only shrink paper size"},
            {"name": "digest", "effect": "dispatch digest covers symbol, class, size, and note; it is not an order"},
        ],
        "duties": [
            {"identity": "researcher", "can_emit_dispatch": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_emit_dispatch": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_emit_dispatch": False, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_store_secret": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "an inventory guard cannot raise a class size cap",
            "a dispatch digest is an information artifact, not an order",
            "a public brief cannot carry paper size or a credential name",
            "trade, withdrawal, seed, and private-key tokens are refused at the boundary",
            "an automation runner cannot store a secret or mint a credential",
            "crossing a disclosure zone cannot enable live trading",
            "personal data and wallet addresses stay on the zero-retention path",
        ],
    }
