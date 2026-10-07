"""Version 0.17 event-window guards, information beacon, and identity plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The beacon is an offline information
packet. The identity plane binds a research session to one role and refuses
standing trade credentials. Neither path can enable live trading.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

EVENT_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "range-expansion haircut when the last true range exceeds 2.5x the prior median",
    AssetClass.LARGE_CAP_ALT.value: "reversal-window haircut when the last return flips a material three-bar path",
    AssetClass.STABLECOIN.value: "wick-straddle watch when the last bar crosses both sides of a 15 bp peg band",
    AssetClass.DEFI.value: "thin-tape veto when volume drops below 40 percent of median and the bar moves 2 percent",
    AssetClass.MEME.value: "exhaustion haircut when three ranges expand and the last close falls",
    AssetClass.L2.value: "reopen-gap haircut when the open gaps more than 1.2 percent on below-median volume",
    AssetClass.RWA.value: "auction-window veto when two consecutive gaps each exceed 0.6 percent",
    AssetClass.PERPETUAL.value: "inventory-skew haircut when funding is extreme and the last range exceeds 1.5 percent",
}

BEACON_STAGES = (
    {"stage": "ingest_fixture", "network": False, "can_trade": False},
    {"stage": "classify", "network": False, "can_trade": False},
    {"stage": "event_guard", "network": False, "can_trade": False},
    {"stage": "beacon", "network": False, "can_trade": False},
)

REFUSED_SCOPES = frozenset({"trade", "withdraw", "seed", "private_key", "live"})
SESSION_ROLES = frozenset({"researcher", "auditor", "operator"})


def apply_v17(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Thirteenth-pass event-window guard. Size cannot increase."""
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
        "guard": EVENT_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _true_range(bar: Candle) -> float:
    return max(bar.high - bar.low, 0.0)


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = [_true_range(bar) for bar in candles[-7:-1]]
    last = _true_range(candles[-1])
    baseline = median(prior) if prior else 0.0
    if size > 0 and baseline > 0 and last > 2.5 * baseline:
        return size * 0.5, "major range-expansion haircut"
    return size, "major: range-expansion haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles]
    if size <= 0 or closes[-4] <= 0 or closes[-2] <= 0:
        return size, "large-cap alt: reversal-window haircut not triggered"
    path = closes[-2] / closes[-4] - 1.0
    last = closes[-1] / closes[-2] - 1.0
    if path * last < 0 and abs(path) > 0.015 and abs(last) > 0.015:
        return size * 0.5, "large-cap alt reversal-window haircut"
    return size, "large-cap alt: reversal-window haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    last = candles[-1]
    if last.high > 1.0015 and last.low < 0.9985:
        return "stablecoin wick-straddle watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = [bar.volume for bar in candles[-7:-1]]
    baseline = median(prior) if prior else 0.0
    previous = candles[-2].close
    last = candles[-1]
    moved = previous > 0 and abs(last.close / previous - 1.0) > 0.02
    thin = baseline > 0 and last.volume < 0.4 * baseline
    if size > 0 and moved and thin:
        return 0.0, "defi thin-tape veto"
    return size, "defi: thin-tape veto not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    ranges = [_true_range(bar) for bar in candles[-3:]]
    expanding = ranges[0] < ranges[1] < ranges[2]
    falling = candles[-1].close < candles[-2].close
    if size > 0 and expanding and falling:
        return size * 0.5, "meme exhaustion haircut"
    return size, "meme: exhaustion haircut not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    last = candles[-1]
    prior = [bar.volume for bar in candles[-7:-1]]
    baseline = median(prior) if prior else 0.0
    gap = previous > 0 and abs(last.open / previous - 1.0) > 0.012
    quiet = baseline > 0 and last.volume < baseline
    if size > 0 and gap and quiet:
        return size * 0.5, "l2 reopen-gap haircut"
    return size, "l2: reopen-gap haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    gaps = []
    for previous, current in zip(candles[-3:-1], candles[-2:], strict=False):
        if previous.close:
            gaps.append(abs(current.open / previous.close - 1.0))
    if size > 0 and len(gaps) == 2 and all(value > 0.006 for value in gaps):
        return 0.0, "rwa auction-window veto"
    return size, "rwa: auction-window veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    wide = last.close > 0 and _true_range(last) / last.close > 0.015
    extreme = abs(last.funding_rate) >= 0.0005
    if size > 0 and wide and extreme:
        return size * 0.5, "perp inventory-skew haircut"
    return size, "perp: inventory-skew haircut not triggered"


def information_beacon(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline event-window packet. A beacon row is not an order and cannot raise size."""
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
        "version": "0.17.0",
        "cadence": "offline research cycle; no socket",
        "inputs": ["synthetic_fixture", "injected_public_print"],
        "stages": list(BEACON_STAGES),
        "rows": rows,
        "class_counts": by_class,
        "haircut_count": len(haircuts),
        "flat_count": len(flat),
        "beacon_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def bind_session(*, role: str, scope: str, prior_role: str | None = None) -> dict[str, object]:
    """Bind one research session to one role. Cross-role reuse and trade scopes are refused."""
    refused = role not in SESSION_ROLES or scope in REFUSED_SCOPES or (prior_role is not None and prior_role != role)
    can_emit = role in {"researcher", "auditor"} and not refused and scope == "research_read"
    return {
        "role": role,
        "scope": scope,
        "bound": not refused,
        "ttl": "research_cycle",
        "reusable_across_roles": False,
        "can_emit_beacon": can_emit,
        "can_trade": False,
        "can_enable_live": False,
        "order_path": False,
        "standing_credential": False,
    }


def identity_plane() -> dict[str, object]:
    """Identity-bound research plane. No execution zone and no live path."""
    return {
        "version": "0.17.0",
        "framework": "research identity plane; not a MAS TRM, PDPA, SOC, NIST, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "zones": ["research", "audit", "identity"],
        "sessions": {
            "binding": "one role per session",
            "ttl": "research_cycle",
            "reusable_across_roles": False,
            "standing_credentials": "refused",
            "refused_scopes": sorted(REFUSED_SCOPES),
            "allowed_scopes": ["research_read", "audit_read"],
        },
        "duties": [
            {"identity": "researcher", "can_emit_beacon": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_emit_beacon": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_emit_beacon": False, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_mint_session": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "an event-window guard cannot raise a class size cap",
            "a beacon digest is an information artifact, not an order",
            "a session is bound to one role and cannot be reused across roles",
            "trade, withdrawal, seed, and live scopes are refused",
            "an automation runner cannot mint a session or enable live trading",
            "dual acknowledgement of a session digest cannot enable live trading",
            "trade keys, withdrawal keys, seeds, and personal data are refused and are not stored",
        ],
    }
