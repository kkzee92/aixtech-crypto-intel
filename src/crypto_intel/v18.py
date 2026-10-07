"""v0.18 microstructure guards, information wire, and API data-security plane.

Fourteenth-pass research overlay. Size cannot increase. No order path.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

GUARD_NOTES = {
    AssetClass.MAJOR.value: "spread-proxy haircut when the last bar range exceeds 1.5 percent on below-median volume",
    AssetClass.LARGE_CAP_ALT.value: "failed-hold veto when the prior bar cleared the five-bar high and the last close fell back through it",
    AssetClass.STABLECOIN.value: "widening-peg watch when three deviations from 1.0 are strictly increasing. Size stays zero",
    AssetClass.DEFI.value: "dislocation veto when the last open-to-close move exceeds 4 percent",
    AssetClass.MEME.value: "blow-off veto when volume exceeds 4x the median and the bar closes down",
    AssetClass.L2.value: "sequencer-gap haircut when the open gaps more than 2 percent from the prior close",
    AssetClass.RWA.value: "too-fast veto when the four-bar move exceeds 3 percent",
    AssetClass.PERPETUAL.value: "funding-acceleration haircut when funding moves more than 8 bps versus three bars ago",
}

WIRE_STAGES = (
    {"stage": "ingest_fixture", "network": False, "can_trade": False},
    {"stage": "classify", "network": False, "can_trade": False},
    {"stage": "microstructure_guard", "network": False, "can_trade": False},
    {"stage": "wire", "network": False, "can_trade": False},
)

ALLOWED_SCOPES = frozenset({"market_read", "public_ticker"})
REFUSED_SCOPES = frozenset({"trade", "withdraw", "transfer", "seed", "private_key", "live", "order"})


def apply_v18(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Fourteenth-pass microstructure guard. Size cannot increase."""
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
        "guard": GUARD_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = (last.high - last.low) / last.close if last.close else 0.0
    baseline = median(c.volume for c in candles[-8:-1])
    if span > 0.015 and last.volume < baseline:
        return size * 0.5, "spread-proxy haircut: wide bar on below-median volume"
    return size, "spread-proxy not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    prior_high = max(c.close for c in candles[-7:-2])
    cleared = candles[-2].close > prior_high
    failed = candles[-1].close < prior_high
    if cleared and failed:
        return 0.0, "failed-hold veto: breakout did not hold the prior high"
    return size, "failed-hold not triggered"


def _stable(candles: list[Candle]) -> str:
    deviations = [abs(c.close - 1.0) for c in candles[-3:]]
    if deviations[0] < deviations[1] < deviations[2] and deviations[2] >= 0.002:
        return "widening-peg watch: three increasing deviations. size stays zero"
    return "stablecoin monitor only. size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    move = abs(last.close / last.open - 1.0) if last.open else 0.0
    if move > 0.04:
        return 0.0, "dislocation veto: open-to-close move above 4 percent"
    return size, "dislocation not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    baseline = median(c.volume for c in candles[-8:-1]) or 1.0
    if last.volume > baseline * 4 and last.close < last.open:
        return 0.0, "blow-off veto: volume spike and down close"
    return size, "blow-off not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    gap = abs(candles[-1].open / candles[-2].close - 1.0) if candles[-2].close else 0.0
    if gap > 0.02:
        return size * 0.5, "sequencer-gap haircut: open gap above 2 percent"
    return size, "sequencer-gap not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    move = abs(candles[-1].close / candles[-4].close - 1.0) if candles[-4].close else 0.0
    if move > 0.03:
        return 0.0, "too-fast veto: four-bar move above 3 percent"
    return size, "too-fast not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    delta = abs(candles[-1].funding_rate - candles[-4].funding_rate)
    if delta > 0.0008:
        return size * 0.5, "funding-acceleration haircut: funding moved more than 8 bps"
    return size, "funding-acceleration not triggered"


def information_wire(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline information wire. No socket and no order instruction."""
    material = "|".join(
        f"{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}:{row.get('note')}" for row in rows
    )
    digest = hashlib.sha256(material.encode()).hexdigest()
    haircuts = [row for row in rows if "not triggered" not in str(row.get("note", ""))]
    return {
        "version": "0.18.0",
        "cadence": "offline research cycle; no socket",
        "inputs": ["synthetic_fixture", "injected_public_print"],
        "stages": list(WIRE_STAGES),
        "rows": rows,
        "haircut_count": len(haircuts),
        "wire_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def api_plane() -> dict[str, object]:
    """API and data-security plane for a research information system. No execution zone."""
    return {
        "version": "0.18.0",
        "framework": "research API plane; not a MAS TRM, PDPA, SOC, NIST, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "zones": ["research", "market-data", "audit"],
        "scopes": {
            "allowed": sorted(ALLOWED_SCOPES),
            "refused": sorted(REFUSED_SCOPES),
            "withdrawal_allowlist": [],
            "read_key_can_sign": False,
            "standing_trade_credential": False,
        },
        "data": {
            "order_intent": "not stored",
            "trade_credential": "never stored",
            "wallet_address": "do not fixture",
            "personal_data": "do not collect",
            "oracle_note": "DeFi and RWA dislocation notes are research flags, not oracle attestations",
        },
        "duties": [
            {"identity": "researcher", "can_read_market": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_read_market": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_read_market": False, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_call_exchange": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "a microstructure guard cannot raise a class size cap",
            "a wire digest is an information artifact, not an order",
            "only market-read and public-ticker scopes are discussable",
            "trade, withdrawal, transfer, seed, and live scopes are refused",
            "the withdrawal allowlist is empty",
            "a read key cannot sign and cannot be reused as a trade key",
            "an automation runner cannot call an exchange or enable live trading",
        ],
    }
