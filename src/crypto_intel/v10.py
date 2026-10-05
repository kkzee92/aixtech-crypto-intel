"""Version 0.10 liquidity guards and cyber data-security plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The security report is a defensive
architecture description, not a certification and not legal advice.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

LIQUIDITY_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "thin-book haircut when last volume is below half the 8-bar median",
    AssetClass.LARGE_CAP_ALT.value: "participation haircut when last volume exceeds 3x the 8-bar median",
    AssetClass.STABLECOIN.value: "peg consensus watch; size stays zero",
    AssetClass.DEFI.value: "wick-rejection veto when a wick is more than 60 percent of the bar",
    AssetClass.MEME.value: "volume-collapse veto when last volume is below 20 percent of the prior bar",
    AssetClass.L2.value: "own-median volume haircut below 40 percent of the 8-bar median",
    AssetClass.RWA.value: "print-count veto when the window has fewer than 10 bars",
    AssetClass.PERPETUAL.value: "funding-sign-flip veto across the last three bars",
}

DATA_CLASSES = (
    {"name": "public_market", "retention": "research window only", "storage": "synthetic or attested public prints"},
    {"name": "synthetic_research", "retention": "repository fixtures", "storage": "labelled SYNTHETIC"},
    {"name": "audit_redacted", "retention": "365 days if a later store exists", "storage": "hash chain, no secrets"},
    {"name": "credential", "retention": "zero", "storage": "refused; never written to git"},
    {"name": "personal_data", "retention": "zero", "storage": "refused; PDPA tripwire is not a legal programme"},
)

ZONES = ("untrusted_ingest", "quality", "research", "control", "audit", "secrets_boundary")


def apply_v10(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Sixth-pass liquidity and structure guard. Size cannot increase."""
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
        "guard": LIQUIDITY_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _median_volume(candles: list[Candle]) -> float:
    return float(median(bar.volume for bar in candles[-8:]))


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _median_volume(candles)
    if size > 0 and base > 0 and candles[-1].volume < 0.5 * base:
        return size * 0.5, "major thin-book haircut"
    return size, "major: thin-book haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _median_volume(candles)
    if size > 0 and base > 0 and candles[-1].volume > 3.0 * base:
        return size * 0.5, "large-cap alt participation haircut"
    return size, "large-cap alt: participation haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    deviation = abs(candles[-1].close - 1.0)
    if deviation >= 0.0015:
        return "stablecoin peg-consensus watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = last.high - last.low
    if size <= 0 or span <= 0:
        return size, "defi: wick-rejection veto not triggered"
    upper = last.high - max(last.open, last.close)
    lower = min(last.open, last.close) - last.low
    if max(upper, lower) / span > 0.60:
        return 0.0, "defi wick-rejection veto"
    return size, "defi: wick-rejection veto not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = candles[-2].volume
    if size > 0 and prior > 0 and candles[-1].volume < 0.20 * prior:
        return 0.0, "meme volume-collapse veto"
    return size, "meme: volume-collapse veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _median_volume(candles)
    if size > 0 and base > 0 and candles[-1].volume < 0.40 * base:
        return size * 0.5, "l2 own-median volume haircut"
    return size, "l2: own-median volume haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    if size > 0 and len(candles) < 10:
        return 0.0, "rwa print-count veto"
    return size, "rwa: print-count veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    window = [bar.funding_rate for bar in candles[-3:]]
    signs = {1 if rate > 0 else -1 if rate < 0 else 0 for rate in window}
    if size > 0 and 1 in signs and -1 in signs:
        return 0.0, "perp funding-sign-flip veto"
    return size, "perp: funding-sign-flip veto not triggered"


def information_pack(rows: list[dict[str, object]]) -> dict[str, object]:
    """Breadth haircut for an already-scored paper book. Size cannot increase."""
    directional = [row for row in rows if float(row.get("size_fraction", 0.0)) > 0]
    haircut = 0.75 if len(directional) >= 4 else 1.0
    packed = []
    for row in rows:
        prior = float(row.get("size_fraction", 0.0))
        packed.append(
            {
                "symbol": row.get("symbol"),
                "asset_class": row.get("asset_class"),
                "prior_size": prior,
                "size_fraction": round(prior * haircut, 6),
                "can_increase_size": False,
            }
        )
    gross = round(sum(float(item["size_fraction"]) for item in packed), 6)
    material = "|".join(f"{item['symbol']}:{item['size_fraction']}" for item in packed)
    return {
        "version": "0.10.0",
        "rows": packed,
        "breadth_haircut": haircut,
        "gross_paper_fraction": gross,
        "pack_digest": hashlib.sha256(material.encode()).hexdigest(),
        "live_enabled": False,
        "order_path": False,
        "order_instruction": False,
    }


def cyber_plane_report() -> dict[str, object]:
    """Defensive cyber and data-security architecture. No execution zone."""
    return {
        "version": "0.10.0",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "zones": list(ZONES),
        "data_classes": list(DATA_CLASSES),
        "key_separation": [
            {"key": "market_read", "scope": "public market data only", "can_trade": False, "rotation_days": 90},
            {"key": "audit_sign", "scope": "local hash chain", "can_trade": False, "rotation_days": 365},
            {"key": "break_glass", "scope": "research halt clear", "can_trade": False, "can_enable_live": False},
        ],
        "crypto_expectation": "AES-256-GCM at rest and TLS 1.2+ in transit; keys in an external store, never in git",
        "supply_chain": "dependencies pinned in requirements-dev.txt; no install-time network in the research path",
        "residency": "synthetic fixtures and redacted audit only; personal data refused",
        "backup": "synthetic fixtures and redacted audit only; secrets are not backed up because they are not stored",
        "principles": [
            "every fixture is untrusted until attested",
            "least privilege: scan is allowed, place_order is refused for every role",
            "credential and personal-data classes have zero retention",
            "a liquidity guard cannot raise a class size cap",
            "break-glass cannot enable live trading or a withdrawal path",
        ],
    }
