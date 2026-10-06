"""Version 0.13 event guards and an information-system data-security plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The data-security plane describes
research zones only. It does not create keys or an execution path.
"""

from __future__ import annotations

import hashlib

from crypto_intel.models import AssetClass, Candle, Side

EVENT_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "failed-auction haircut when the close is in the bottom quarter of a wide bar",
    AssetClass.LARGE_CAP_ALT.value: "failed-follow-through haircut when an up bar is followed by a down close",
    AssetClass.STABLECOIN.value: "depeg-velocity watch; size stays zero",
    AssetClass.DEFI.value: "range-expansion haircut when the last bar range is at least twice the prior median",
    AssetClass.MEME.value: "exhaustion-wick veto when the upper wick dominates and the close is below the open",
    AssetClass.L2.value: "participation-fade haircut after a three percent move with thin last volume",
    AssetClass.RWA.value: "halted-print veto when four bars have almost no range",
    AssetClass.PERPETUAL.value: "funding-acceleration haircut when absolute funding rises across three bars",
}

FLOW_ZONES = (
    {"zone": "ingest", "holds": "synthetic or attested public prints", "network": "default deny", "can_trade": False},
    {"zone": "score", "holds": "paper signals and class guards", "network": "none", "can_trade": False},
    {"zone": "report", "holds": "redacted information rows", "network": "none", "can_trade": False},
    {"zone": "archive", "holds": "lineage digests only", "network": "none", "can_trade": False},
)

DATASEC_CONTROLS = (
    {"control": "purpose_binding", "rule": "every report is research_information, never an order"},
    {"control": "minimisation", "rule": "fixtures stay synthetic; personal data and wallets are refused"},
    {"control": "egress", "rule": "default deny; no order or withdrawal host is allowlisted"},
    {"control": "transit", "rule": "offline by default; a future read-only feed would require TLS and no trade scope"},
    {"control": "at_rest", "rule": "secrets are not stored, so there is no secret ciphertext to manage"},
    {"control": "backup", "rule": "archive zone keeps digests, not credentials"},
    {"control": "integrity", "rule": "hash-chained audit and lineage digest before a radar note"},
    {"control": "residency", "rule": "processing stays in-process; no personal-data export path"},
)


def apply_v13(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Apply the class event guard. Size cannot increase."""
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    size = max(proposed_size, 0.0)
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
    if side is Side.ALERT:
        size = 0.0
    return {
        "symbol": candles[-1].symbol,
        "asset_class": asset_class.value,
        "side": side.value if size > 0 and side is not Side.FLAT else Side.FLAT.value,
        "size_fraction": round(max(size, 0.0), 6),
        "note": note,
        "guard": EVENT_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _bar_range(candle: Candle) -> float:
    return max(candle.high - candle.low, 0.0)


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = _bar_range(last)
    if size > 0 and span > 0 and last.close <= last.low + 0.25 * span and span / last.close >= 0.015:
        return size * 0.5, "major failed-auction haircut"
    return size, "major: failed-auction haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    prior, last = candles[-2], candles[-1]
    failed = prior.close > prior.open and last.close < last.open
    if size > 0 and failed:
        return size * 0.5, "alt failed-follow-through haircut"
    return size, "alt: failed-follow-through haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    last = abs(candles[-1].close - 1.0)
    prior = abs(candles[-2].close - 1.0)
    if last > prior and last >= 0.0015:
        return "stablecoin depeg-velocity watch"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = sorted(_bar_range(bar) for bar in candles[-8:-1])
    median_range = prior[len(prior) // 2]
    if size > 0 and median_range > 0 and _bar_range(candles[-1]) >= 2.0 * median_range:
        return size * 0.5, "defi range-expansion haircut"
    return size, "defi: range-expansion haircut not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = _bar_range(last)
    wick = last.high - max(last.open, last.close)
    if size > 0 and span > 0 and wick / span >= 0.60 and last.close < last.open:
        return 0.0, "meme exhaustion-wick veto"
    return size, "meme: exhaustion-wick veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    move = abs(candles[-1].close / candles[-6].close - 1.0)
    base = sorted(bar.volume for bar in candles[-8:-1])[3]
    if size > 0 and move >= 0.03 and base > 0 and candles[-1].volume < 0.6 * base:
        return size * 0.5, "l2 participation-fade haircut"
    return size, "l2: participation-fade haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    quiet = all(_bar_range(bar) / bar.close < 0.0005 for bar in candles[-4:] if bar.close)
    if size > 0 and quiet:
        return 0.0, "rwa halted-print veto"
    return size, "rwa: halted-print veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    rates = [abs(bar.funding_rate) for bar in candles[-3:]]
    rising = rates[2] > rates[1] > rates[0] and rates[2] >= 0.0004
    if size > 0 and rising:
        return size * 0.5, "perp funding-acceleration haircut"
    return size, "perp: funding-acceleration haircut not triggered"


def information_radar(rows: list[dict[str, object]], *, fixture_label: str) -> dict[str, object]:
    """Offline event radar. It is an information artifact, not an order."""
    if not fixture_label or "SYNTHETIC" not in fixture_label.upper():
        raise ValueError("radar notes require a synthetic fixture label")
    haircuts = sum(1 for row in rows if "not triggered" not in str(row.get("note", "")))
    gross = round(sum(float(row.get("size_fraction", 0.0)) for row in rows), 6)
    material = "|".join(
        f"{fixture_label}:{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}:{row.get('note')}"
        for row in rows
    )
    return {
        "version": "0.13.0",
        "fixture_label": fixture_label,
        "symbols": len(rows),
        "event_notes": haircuts,
        "gross_paper_fraction": gross,
        "lineage_digest": hashlib.sha256(material.encode()).hexdigest(),
        "purpose": "research_information",
        "live_enabled": False,
        "order_path": False,
        "order_instruction": False,
        "can_increase_size": False,
        "paper_only": True,
    }


def data_security_plane() -> dict[str, object]:
    """Data-security architecture for the automated information system."""
    return {
        "version": "0.13.0",
        "framework": "research data-security plane for an automated information system; not a certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "purpose": "research_information",
        "flow_zones": list(FLOW_ZONES),
        "controls": list(DATASEC_CONTROLS),
        "data_classes_refused": ["seed", "private_key", "trade_api_secret", "withdrawal_key", "personal_data", "wallet"],
        "standing_privilege": False,
        "backup": "digest_only",
        "principles": [
            "an event guard cannot raise a class size cap",
            "a radar note is an information artifact, not an order",
            "ingest is default-deny and cannot open an order path",
            "secrets are refused, so they are not backed up",
            "no role gains standing privilege to trade or enable live trading",
        ],
    }
