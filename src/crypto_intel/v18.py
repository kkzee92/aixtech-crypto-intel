"""Version 0.18 participation guards, information console, and data-security plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The console is an offline information
packet. The data-security plane classifies research records and refuses secret,
wallet, and personal-data fields. Neither path can enable live trading.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.security import contains_secret

PARTICIPATION_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "close-location haircut when a long closes in the bottom quartile of the bar",
    AssetClass.LARGE_CAP_ALT.value: "climax-volume haircut when the last volume exceeds 3x the prior median",
    AssetClass.STABLECOIN.value: "peg-band straddle watch when the bar trades both sides of an 8 bp band",
    AssetClass.DEFI.value: "failed-break haircut when the high breaks the prior range and the close falls back inside",
    AssetClass.MEME.value: "one-bar climax veto when the range exceeds 12 percent and volume exceeds 3x median",
    AssetClass.L2.value: "lag haircut when the last three-bar return is negative",
    AssetClass.RWA.value: "identical-print veto when the last three closes are unchanged",
    AssetClass.PERPETUAL.value: "funding-flip haircut when funding changes sign and the new print is at least 3 bp",
}

CONSOLE_STAGES = (
    {"stage": "ingest_fixture", "network": False, "can_trade": False},
    {"stage": "classify", "network": False, "can_trade": False},
    {"stage": "participation_guard", "network": False, "can_trade": False},
    {"stage": "console", "network": False, "can_trade": False},
)

DATA_CLASSES = (
    {"field": "symbol_ohlcv", "class": "public-market", "retention": "research", "egress": "research_packet"},
    {"field": "funding_rate", "class": "public-market", "retention": "research", "egress": "research_packet"},
    {"field": "source_label", "class": "integrity", "retention": "research", "egress": "audit"},
    {"field": "read_only_key_name", "class": "secret-name", "retention": "zero", "egress": "refused"},
    {"field": "trade_or_withdrawal_key", "class": "secret", "retention": "zero", "egress": "refused"},
    {"field": "wallet_address", "class": "sensitive-identifier", "retention": "zero", "egress": "refused"},
    {"field": "email_phone_nric", "class": "personal", "retention": "zero", "egress": "refused"},
)

REFUSED_FIELDS = frozenset({"api_key", "secret", "seed", "private_key", "wallet", "email", "nric", "phone"})


def apply_v18(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Fourteenth-pass participation guard. Size cannot increase."""
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    size = proposed_size if side in {Side.LONG, Side.SHORT} else 0.0
    if asset_class is AssetClass.MAJOR:
        size, note = _major(candles, size, side)
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
        "guard": PARTICIPATION_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _range(bar: Candle) -> float:
    return max(bar.high - bar.low, 0.0)


def _major(candles: list[Candle], size: float, side: Side) -> tuple[float, str]:
    last = candles[-1]
    span = _range(last)
    if size > 0 and side is Side.LONG and span > 0 and (last.close - last.low) / span < 0.25:
        return size * 0.5, "major close-location haircut"
    return size, "major: close-location haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = [bar.volume for bar in candles[-7:-1]]
    baseline = median(prior) if prior else 0.0
    if size > 0 and baseline > 0 and candles[-1].volume > 3.0 * baseline:
        return size * 0.5, "large-cap alt climax-volume haircut"
    return size, "large-cap alt: climax-volume haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    last = candles[-1]
    if last.high > 1.0008 and last.low < 0.9992:
        return "stablecoin peg-band straddle watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    prior_high = max(bar.high for bar in candles[-6:-1])
    last = candles[-1]
    if size > 0 and last.high > prior_high and last.close <= prior_high:
        return size * 0.5, "defi failed-break haircut"
    return size, "defi: failed-break haircut not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = [bar.volume for bar in candles[-7:-1]]
    baseline = median(prior) if prior else 0.0
    last = candles[-1]
    wide = last.close > 0 and _range(last) / last.close > 0.12
    climax = baseline > 0 and last.volume > 3.0 * baseline
    if size > 0 and wide and climax:
        return 0.0, "meme one-bar climax veto"
    return size, "meme: one-bar climax veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    earlier = candles[-4].close
    if size > 0 and earlier > 0 and candles[-1].close / earlier - 1.0 < 0:
        return size * 0.5, "l2 lag haircut"
    return size, "l2: lag haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-3:]]
    if size > 0 and closes[0] == closes[1] == closes[2]:
        return 0.0, "rwa identical-print veto"
    return size, "rwa: identical-print veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].funding_rate
    current = candles[-1].funding_rate
    flipped = previous * current < 0 and abs(current) >= 0.0003
    if size > 0 and flipped:
        return size * 0.5, "perp funding-flip haircut"
    return size, "perp: funding-flip haircut not triggered"


def information_console(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline participation packet. A console row is not an order and cannot raise size."""
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
        "version": "0.18.0",
        "cadence": "offline research cycle; no socket",
        "inputs": ["synthetic_fixture", "injected_public_print"],
        "stages": list(CONSOLE_STAGES),
        "rows": rows,
        "class_counts": by_class,
        "haircut_count": len(haircuts),
        "flat_count": len(flat),
        "console_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def screen_record(record: dict[str, object]) -> dict[str, object]:
    """Refuse a research record that carries a secret, wallet, or personal-data field."""
    blocked = sorted(name for name in record if name.lower() in REFUSED_FIELDS or contains_secret(f"{name}={record[name]}"))
    return {
        "accepted": not blocked,
        "blocked_fields": blocked,
        "retention": "zero" if blocked else "research",
        "egress": "refused" if blocked else "research_packet",
        "stored": False if blocked else True,
        "can_trade": False,
        "can_enable_live": False,
    }


def data_security_architecture() -> dict[str, object]:
    """Data-security architecture for the paper information system. No execution zone."""
    return {
        "version": "0.18.0",
        "framework": "research data-security plane; not a MAS TRM, PDPA, SOC, NIST, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "zones": ["ingest", "research", "audit", "egress"],
        "classes": list(DATA_CLASSES),
        "controls": [
            {"name": "classification", "effect": "every exported field maps to a data class"},
            {"name": "zero_retention", "effect": "secrets, wallets, and personal data are not stored"},
            {"name": "egress_screen", "effect": "secret-like strings are blocked before a research packet leaves"},
            {"name": "key_separation", "effect": "market-read names cannot authorise trade or withdrawal"},
            {"name": "audit_chain", "effect": "paper decisions append to a hash chain"},
            {"name": "participation_guard", "effect": "asset-class guards can only shrink paper size"},
        ],
        "duties": [
            {"identity": "researcher", "can_emit_console": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_emit_console": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_emit_console": False, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_store_secret": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "a participation guard cannot raise a class size cap",
            "a console digest is an information artifact, not an order",
            "secret, wallet, and personal-data fields are refused at the record screen",
            "market-read credentials, if named, cannot authorise a trade or a withdrawal",
            "an automation runner cannot store a secret or enable live trading",
            "dual acknowledgement of a console digest cannot enable live trading",
            "trade keys, withdrawal keys, seeds, and personal data are refused and are not stored",
        ],
    }
