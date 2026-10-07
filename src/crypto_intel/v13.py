"""Version 0.13 venue-fragmentation guards, information mesh, and resilience plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The resilience plane describes
research controls only. It does not create keys, backups of seeds, or an
execution path.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

FRAGMENT_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "venue-disagreement haircut when the last bar range exceeds 2.5x the prior median",
    AssetClass.LARGE_CAP_ALT.value: "listing-fragmentation haircut when price gaps on thin volume",
    AssetClass.STABLECOIN.value: "redemption-stress watch when the peg oscillates; size stays zero",
    AssetClass.DEFI.value: "oracle-gap veto when price jumps without participation",
    AssetClass.MEME.value: "exhaustion veto after a burst followed by three declining closes",
    AssetClass.L2.value: "sequencer-stall haircut when volume is busy and the print is frozen",
    AssetClass.RWA.value: "stale-attestation veto when the last three closes do not move",
    AssetClass.PERPETUAL.value: "funding-price disagreement haircut when funding and the last return oppose",
}

MESH_THRESHOLDS: dict[str, float] = {
    AssetClass.MAJOR.value: 0.06,
    AssetClass.LARGE_CAP_ALT.value: 0.08,
    AssetClass.STABLECOIN.value: 0.003,
    AssetClass.DEFI.value: 0.07,
    AssetClass.MEME.value: 0.12,
    AssetClass.L2.value: 0.07,
    AssetClass.RWA.value: 0.04,
    AssetClass.PERPETUAL.value: 0.06,
}

RESILIENCE_FUNCTIONS = (
    {"function": "identify", "control": "asset-class catalog, fixture label, and source attestation"},
    {"function": "protect", "control": "paper-only mode, secret refusal, and empty withdrawal allowlist"},
    {"function": "detect", "control": "feed jump, staleness, fragmentation guard, and mesh disagreement"},
    {"function": "respond", "control": "kill switch and incident note; response cannot enable live trading"},
    {"function": "recover", "control": "digest restore only; recovery cannot enable live trading"},
)

KEY_SCOPES = (
    {"scope": "market_read", "stored_in_tree": False, "can_trade": False, "can_withdraw": False},
    {"scope": "trade", "stored_in_tree": False, "can_trade": False, "can_withdraw": False, "refused": True},
    {"scope": "withdraw", "stored_in_tree": False, "can_trade": False, "can_withdraw": False, "refused": True},
)


def apply_v13(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Ninth-pass venue-fragmentation guard. Size cannot increase."""
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
        "guard": FRAGMENT_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _prior_median_volume(candles: list[Candle]) -> float:
    return float(median(bar.volume for bar in candles[-8:-1]))


def _prior_median_range(candles: list[Candle]) -> float:
    return float(median(bar.high - bar.low for bar in candles[-8:-1]))


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _prior_median_range(candles)
    last_range = candles[-1].high - candles[-1].low
    if size > 0 and base > 0 and last_range > 2.5 * base:
        return size * 0.5, "major venue-disagreement haircut"
    return size, "major: venue-disagreement haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    gap = abs(candles[-1].close / previous - 1.0) if previous else 0.0
    base = _prior_median_volume(candles)
    if size > 0 and base > 0 and gap > 0.04 and candles[-1].volume < base:
        return size * 0.5, "large-cap alt listing-fragmentation haircut"
    return size, "large-cap alt: listing-fragmentation haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    earlier = candles[-2].close - 1.0
    later = candles[-1].close - 1.0
    oscillating = earlier * later < 0 and abs(earlier) > 0.0015 and abs(later) > 0.0015
    if oscillating:
        return "stablecoin redemption-stress watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    jump = abs(candles[-1].close / previous - 1.0) if previous else 0.0
    base = _prior_median_volume(candles)
    if size > 0 and base > 0 and jump > 0.06 and candles[-1].volume < base:
        return 0.0, "defi oracle-gap veto"
    return size, "defi: oracle-gap veto not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    burst = False
    for index in range(-4, 0):
        previous = candles[index - 1].close
        if previous and candles[index].close / previous - 1.0 > 0.08:
            burst = True
            break
    declining = candles[-3].close > candles[-2].close > candles[-1].close
    if size > 0 and burst and declining:
        return 0.0, "meme exhaustion veto"
    return size, "meme: exhaustion veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    frozen = last.close > 0 and (last.high - last.low) / last.close < 0.0015
    base = _prior_median_volume(candles)
    if size > 0 and base > 0 and frozen and last.volume > 2.0 * base:
        return size * 0.5, "l2 sequencer-stall haircut"
    return size, "l2: sequencer-stall haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-3:]]
    if size > 0 and closes[0] == closes[1] == closes[2]:
        return 0.0, "rwa stale-attestation veto"
    return size, "rwa: stale-attestation veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    previous = candles[-2].close
    bar_return = (last.close / previous - 1.0) if previous else 0.0
    opposed = bar_return != 0 and last.funding_rate != 0 and (bar_return > 0) != (last.funding_rate > 0)
    if size > 0 and opposed and abs(last.funding_rate) > 0.0004 and abs(bar_return) > 0.015:
        return size * 0.5, "perp funding-price disagreement haircut"
    return size, "perp: funding-price disagreement haircut not triggered"


def information_mesh(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline source-agreement mesh. A disagreement can only shrink paper size."""
    contested: list[dict[str, object]] = []
    adjusted: list[dict[str, object]] = []
    for row in rows:
        asset_class = str(row.get("asset_class", ""))
        primary = float(row.get("primary_close", 0.0))
        secondary = float(row.get("secondary_close", primary))
        disagreement = abs(primary - secondary) / primary if primary else 0.0
        threshold = MESH_THRESHOLDS.get(asset_class, 0.06)
        proposed = float(row.get("size_fraction", 0.0))
        size = proposed * 0.5 if disagreement > threshold else proposed
        size = min(size, proposed if proposed > 0 else 0.0)
        item = {
            "symbol": row.get("symbol"),
            "asset_class": asset_class,
            "disagreement": round(disagreement, 6),
            "threshold": threshold,
            "contested": disagreement > threshold,
            "size_fraction": round(max(size, 0.0), 6),
            "prior_size": proposed,
        }
        adjusted.append(item)
        if item["contested"]:
            contested.append({"symbol": item["symbol"], "disagreement": item["disagreement"]})
    material = "|".join(
        f"{item['symbol']}:{item['asset_class']}:{item['disagreement']}:{item['size_fraction']}" for item in adjusted
    )
    return {
        "version": "0.13.0",
        "sources": ["primary_fixture", "secondary_injected"],
        "network": False,
        "rows": adjusted,
        "contested": contested,
        "mesh_digest": hashlib.sha256(material.encode()).hexdigest(),
        "live_enabled": False,
        "order_path": False,
        "order_instruction": False,
        "can_increase_size": False,
        "paper_only": True,
    }


def resilience_plane() -> dict[str, object]:
    """Research cyber-resilience plane. No keys, no seed backup, no execution zone."""
    roles = (
        {"role": "researcher", "can_read_mesh": True, "can_trade": False, "can_enable_live": False},
        {"role": "auditor", "can_read_mesh": True, "can_trade": False, "can_enable_live": False},
        {"role": "operator", "can_read_mesh": False, "can_trade": False, "can_enable_live": False},
    )
    return {
        "version": "0.13.0",
        "framework": "research cyber-resilience plane; ICT-style map, not a certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "functions": list(RESILIENCE_FUNCTIONS),
        "key_scopes": list(KEY_SCOPES),
        "data_residency": {
            "allowed": ["research_repository"],
            "refused": ["personal_data_region", "production_custody", "exchange_account"],
        },
        "backup": {
            "contents": ["parameter_digest", "mesh_digest", "redacted_audit"],
            "immutable": True,
            "seed_backup": False,
            "can_restore_live_trading": False,
        },
        "severity": ["info", "watch", "high", "halt"],
        "separation_of_duties": list(roles),
        "quorum": {"acknowledgements_required": 2, "can_enable_live": False},
        "data_plane": {
            "allowed": ["synthetic_research", "attested_public_prints", "redacted_audit"],
            "refused": ["seed", "private_key", "trade_api_secret", "withdrawal_key", "personal_data"],
            "retention_credentials": "zero",
            "retention_personal_data": "zero",
        },
        "principles": [
            "a fragmentation guard cannot raise a class size cap",
            "a mesh disagreement can only shrink paper size",
            "a mesh note is an information artifact, not an order",
            "trade and withdrawal key scopes are refused and are not stored",
            "backup restore cannot enable live trading",
            "an operator cannot read the mesh or enable live trading",
        ],
    }
