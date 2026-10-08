"""v0.21 calendar and session guards, plus a data-residency plane.

Seventeenth pass. Guards can only shrink paper size. The research clock is an
offline information artifact. The residency plane describes encryption and
cross-border rules. It never stores key material and never opens an execution zone.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

CALENDAR_NOTES = {
    AssetClass.MAJOR.value: "session-gap haircut when the open is at least 1.5 percent from the prior close",
    AssetClass.LARGE_CAP_ALT.value: "beta-shock haircut when two same-sign jumps end with a 6 percent bar",
    AssetClass.STABLECOIN.value: "peg-acceleration watch when deviation rises by at least 15 bp",
    AssetClass.DEFI.value: "volume air-pocket haircut when price rises 3 percent on thin volume",
    AssetClass.MEME.value: "wick-rejection veto when the upper wick is more than twice the body",
    AssetClass.L2.value: "lead-fade haircut when a three-bar lead is followed by a negative three-bar return",
    AssetClass.RWA.value: "stale-print haircut when three closes are identical",
    AssetClass.PERPETUAL.value: "basis-stress veto when funding sign disagrees with a 3 percent drift",
}

FRESHNESS_BARS = {
    AssetClass.MAJOR.value: 2,
    AssetClass.LARGE_CAP_ALT.value: 4,
    AssetClass.STABLECOIN.value: 1,
    AssetClass.DEFI.value: 4,
    AssetClass.MEME.value: 1,
    AssetClass.L2.value: 4,
    AssetClass.RWA.value: 12,
    AssetClass.PERPETUAL.value: 2,
}

REGIONS = ("SG", "EU", "US-research")
DATA_CLASSES = ("research_series", "audit_event", "public_redacted", "secret", "personal")
REFUSED_SCOPES = ("trade", "withdraw", "seed", "private_key", "api_key")
KEY_ROLES = ("data_encryption", "audit_sign", "break_glass")


def apply_v21(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Seventeenth-pass calendar guard. Size cannot increase."""
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
        "guard": CALENDAR_NOTES[asset_class.value],
        "freshness_bars": FRESHNESS_BARS[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = candles[-2].close
    gap = abs(candles[-1].open / prior - 1.0) if prior else 0.0
    if gap >= 0.015 and size > 0:
        return size * 0.5, "major session gap: open is at least 1.5 percent from the prior close"
    return size, "major calendar guard not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1].close / candles[-2].close - 1.0 if candles[-2].close else 0.0
    prior = candles[-2].close / candles[-3].close - 1.0 if candles[-3].close else 0.0
    shock = abs(last) >= 0.06 and last * prior > 0 and abs(prior) >= 0.03
    if shock and size > 0:
        return size * 0.5, "large-cap beta shock: two same-sign jumps, last at least 6 percent"
    return size, "large-cap calendar guard not triggered"


def _stable(candles: list[Candle]) -> str:
    previous = abs(candles[-2].close - 1.0)
    current = abs(candles[-1].close - 1.0)
    if current - previous >= 0.0015:
        return "stablecoin peg acceleration: deviation increased by at least 15 bp; size stays zero"
    return "stablecoin calendar guard not triggered; size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    base = float(median(bar.volume for bar in candles[-8:])) or 1.0
    move = candles[-1].close / candles[-4].close - 1.0 if candles[-4].close else 0.0
    if move >= 0.03 and candles[-1].volume < base * 0.5 and size > 0:
        return size * 0.5, "defi volume air-pocket: price up 3 percent on volume below half the median"
    return size, "defi calendar guard not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    body = abs(last.close - last.open)
    upper = last.high - max(last.open, last.close)
    if body > 0 and upper > body * 2 and last.close >= last.open:
        return 0.0, "meme wick rejection: upper wick more than twice the body"
    return size, "meme calendar guard not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    lead = candles[-4].close / candles[-7].close - 1.0 if candles[-7].close else 0.0
    fade = candles[-1].close / candles[-4].close - 1.0 if candles[-4].close else 0.0
    if lead > 0.02 and fade < 0 and size > 0:
        return size * 0.5, "l2 lead fade: prior three-bar lead followed by a negative three-bar return"
    return size, "l2 calendar guard not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-3:]]
    if closes[0] == closes[1] == closes[2] and size > 0:
        return size * 0.5, "rwa stale print: three identical closes"
    return size, "rwa calendar guard not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    drift = candles[-1].close / candles[-6].close - 1.0 if candles[-6].close else 0.0
    funding = candles[-1].funding_rate
    disagreed = (funding > 0 and drift <= -0.03) or (funding < 0 and drift >= 0.03)
    if disagreed:
        return 0.0, "perp basis stress: funding sign disagrees with a 3 percent drift"
    return size, "perp calendar guard not triggered"


def research_clock(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline research clock. A clock packet is not an order and cannot raise size."""
    material = "|".join(
        f"{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}:{row.get('note')}" for row in rows
    )
    digest = hashlib.sha256(material.encode()).hexdigest()
    haircuts = [row for row in rows if "not triggered" not in str(row.get("note", ""))]
    return {
        "version": "0.21.0",
        "cadence": "offline research cycle; no socket",
        "freshness_bars": dict(FRESHNESS_BARS),
        "rows": rows,
        "haircut_count": len(haircuts),
        "clock_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def screen_transfer(data_class: str, origin: str, destination: str) -> dict[str, object]:
    """Decide whether a research record may cross a residency boundary."""
    if data_class not in DATA_CLASSES:
        raise ValueError("unknown data class")
    if origin not in REGIONS or destination not in REGIONS:
        raise ValueError("region must be SG, EU, or US-research")
    cross_border = origin != destination
    blocked = data_class in {"secret", "personal", "research_series", "audit_event"} and cross_border
    return {
        "data_class": data_class,
        "origin": origin,
        "destination": destination,
        "allowed": not blocked,
        "encrypt_at_rest": data_class != "public_redacted",
        "can_trade": False,
        "can_enable_live": False,
        "reason": "cross-border transfer refused for this class" if blocked else "transfer stays inside the allowlist",
    }


def data_residency_plane() -> dict[str, object]:
    """Data-residency and encryption plane. Rules only. No key material and no execution zone."""
    return {
        "version": "0.21.0",
        "framework": "research residency plane; not a MAS TRM, PDPA, SOC, NIST, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "material_stored": False,
        "regions": list(REGIONS),
        "data_classes": list(DATA_CLASSES),
        "refused_scopes": list(REFUSED_SCOPES),
        "key_roles": list(KEY_ROLES),
        "controls": [
            {"name": "region_allowlist", "effect": "records may only be labelled SG, EU, or US-research"},
            {"name": "encryption_at_rest", "effect": "research series, audit events, secrets, and personal data require encryption"},
            {"name": "key_separation", "effect": "data encryption, audit sign, and break-glass keys are distinct and cannot trade"},
            {"name": "cross_border_block", "effect": "secret, personal, research, and audit classes cannot leave the origin region"},
            {"name": "calendar_guard", "effect": "asset-class calendar guards can only shrink paper size"},
        ],
        "duties": [
            {"identity": "researcher", "can_emit_clock": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_emit_clock": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_emit_clock": False, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_store_secret": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "a calendar guard cannot raise a class size cap",
            "a research-clock digest is an information artifact, not an order",
            "encryption, audit, and break-glass keys are separated and none can trade",
            "secret and personal classes are not stored and cannot cross a region boundary",
            "trade, withdrawal, seed, and private-key scopes are refused",
            "a region transfer cannot enable live trading",
            "there is still no execution zone",
        ],
    }
