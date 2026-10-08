"""v0.22 depth-quality guards and a provenance plane.

Eighteenth pass. Guards can only shrink paper size. The provenance plane
records chain-of-custody for research fixtures. It stores no key material
and never opens an execution zone.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

DEPTH_NOTES = {
    AssetClass.MAJOR.value: "stop-run haircut when the last range is at least 2.5x the prior median",
    AssetClass.LARGE_CAP_ALT.value: "failed-auction haircut when the high breaks out and the close returns inside",
    AssetClass.STABLECOIN.value: "peg-persistence watch when two closes deviate by at least 20 bp",
    AssetClass.DEFI.value: "liquidity-vacuum haircut when volume halves and the range expands",
    AssetClass.MEME.value: "wash-print veto when a volume spike closes near the open",
    AssetClass.L2.value: "lead-reversal haircut when a positive three-bar lead fades",
    AssetClass.RWA.value: "thin-gap haircut when the open gaps at least 2 percent on light volume",
    AssetClass.PERPETUAL.value: "funding-flip veto when the funding sign changes on the last print",
}

DEPTH_BARS = {
    AssetClass.MAJOR.value: 6,
    AssetClass.LARGE_CAP_ALT.value: 5,
    AssetClass.STABLECOIN.value: 2,
    AssetClass.DEFI.value: 2,
    AssetClass.MEME.value: 6,
    AssetClass.L2.value: 6,
    AssetClass.RWA.value: 6,
    AssetClass.PERPETUAL.value: 2,
}

ALLOWED_LABELS = ("SYNTHETIC", "PUBLIC_READ")
CUSTODY_ZONES = ("collected", "reviewed", "published")
REFUSED_SCOPES = ("trade", "withdraw", "seed", "private_key", "api_key")
DATA_CLASSES = ("research_series", "audit_event", "public_redacted", "secret", "personal")


def apply_v22(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Eighteenth-pass depth guard. Size cannot increase."""
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
        "guard": DEPTH_NOTES[asset_class.value],
        "depth_bars": DEPTH_BARS[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    ranges = [bar.high - bar.low for bar in candles[-7:-1]]
    baseline = median(ranges) if ranges else 0.0
    last = candles[-1].high - candles[-1].low
    if baseline and last >= baseline * 2.5 and size > 0:
        return size * 0.5, "major stop-run: last range is at least 2.5x the prior median"
    return size, "major depth guard not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    prior_high = max(bar.high for bar in candles[-6:-1])
    last = candles[-1]
    if last.high > prior_high and last.close <= prior_high and size > 0:
        return size * 0.5, "large-cap failed auction: breakout high closed back inside"
    return size, "large-cap depth guard not triggered"


def _stable(candles: list[Candle]) -> str:
    latest = abs(candles[-1].close - 1.0)
    previous = abs(candles[-2].close - 1.0)
    if latest >= 0.002 and previous >= 0.002:
        return "stablecoin peg persistence: two closes deviate by at least 20 bp"
    return "stablecoin depth guard not triggered"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2]
    last = candles[-1]
    vacuum = previous.volume > 0 and last.volume <= previous.volume * 0.5
    expanded = (last.high - last.low) > (previous.high - previous.low)
    if vacuum and expanded and size > 0:
        return size * 0.5, "defi liquidity vacuum: volume halved while range expanded"
    return size, "defi depth guard not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    baseline = median(bar.volume for bar in candles[-7:-1])
    last = candles[-1]
    span = last.high - last.low
    body = abs(last.close - last.open)
    wash = baseline > 0 and last.volume >= baseline * 4 and span > 0 and body / span <= 0.15
    if wash and size > 0:
        return 0.0, "meme wash print: volume spike with close near open"
    return size, "meme depth guard not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    lead_base = candles[-7].close
    mid = candles[-4].close
    lead = mid / lead_base - 1.0 if lead_base else 0.0
    fade = candles[-1].close / mid - 1.0 if mid else 0.0
    if lead >= 0.02 and fade <= -0.01 and size > 0:
        return size * 0.5, "l2 lead reversal: positive three-bar lead followed by a fade"
    return size, "l2 depth guard not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = candles[-2].close
    gap = abs(candles[-1].open / prior - 1.0) if prior else 0.0
    baseline = median(bar.volume for bar in candles[-7:-1])
    if gap >= 0.02 and candles[-1].volume < baseline and size > 0:
        return size * 0.5, "rwa thin gap: open gaps at least 2 percent on below-median volume"
    return size, "rwa depth guard not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1].funding_rate
    previous = candles[-2].funding_rate
    if last * previous < 0 and size > 0:
        return 0.0, "perp funding flip: sign changed on the last print"
    return size, "perp depth guard not triggered"


def attest_provenance(label: str, symbol: str, collector: str, reviewer: str) -> str:
    """Hash a research handoff. Refuses trade or secret scopes. Stores no key material."""
    if label not in ALLOWED_LABELS:
        raise ValueError("source label must be SYNTHETIC or PUBLIC_READ")
    blob = f"{collector} {reviewer}".lower()
    if any(token in blob for token in REFUSED_SCOPES):
        raise PermissionError("trade or secret scopes cannot attest provenance")
    material = f"{label}|{symbol}|{collector}|{reviewer}".encode()
    return hashlib.sha256(material).hexdigest()


def screen_handoff(data_class: str, zone: str) -> dict[str, object]:
    """Refuse secret, personal, and execution-zone handoffs. Cannot enable live trading."""
    blocked = data_class in {"secret", "personal", "trade_key"} or zone == "execution"
    return {
        "data_class": data_class,
        "zone": zone,
        "allowed": not blocked,
        "live_enabled": False,
        "order_path": False,
        "can_enable_live": False,
        "reason": "handoff refused for this class or zone" if blocked else "handoff stays inside the research chain",
    }


def custody_chain(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline digest of depth-guard notes. An information artifact, not an order."""
    material = "|".join(
        f"{row.get('symbol')}:{row.get('size_fraction')}:{row.get('note')}" for row in rows
    )
    return {
        "version": "0.22.0",
        "digest": hashlib.sha256(material.encode()).hexdigest(),
        "rows": len(rows),
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
    }


def provenance_plane() -> dict[str, object]:
    """Chain-of-custody plane. Rules only. No key material and no execution zone."""
    return {
        "version": "0.22.0",
        "framework": "research provenance plane; not a MAS TRM, PDPA, SOC, NIST, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "material_stored": False,
        "labels": list(ALLOWED_LABELS),
        "zones": list(CUSTODY_ZONES),
        "data_classes": list(DATA_CLASSES),
        "refused_scopes": list(REFUSED_SCOPES),
        "controls": [
            {"name": "label_allowlist", "effect": "only SYNTHETIC or PUBLIC_READ fixtures can be attested"},
            {"name": "scope_refusal", "effect": "trade, withdrawal, seed, private-key, and api-key scopes cannot attest"},
            {"name": "handoff_screen", "effect": "secret, personal, and execution-zone handoffs are refused"},
            {"name": "custody_digest", "effect": "depth-guard notes hash into an offline chain digest"},
            {"name": "depth_guard", "effect": "asset-class depth guards can only shrink paper size"},
        ],
        "duties": [
            {"identity": "collector", "can_attest": True, "can_trade": False, "can_enable_live": False},
            {"identity": "reviewer", "can_attest": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_attest": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_attest": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "a depth guard cannot raise a class size cap",
            "a provenance digest is an information artifact, not an order",
            "collector, reviewer, and auditor duties cannot trade or enable live trading",
            "secret and personal classes are not stored and cannot enter a published handoff",
            "trade, withdrawal, seed, and private-key scopes are refused",
            "an execution zone is not a custody zone",
            "there is still no execution zone",
        ],
    }
