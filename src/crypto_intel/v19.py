"""Version 0.19 microstructure guards, information tape, and secrets lifecycle.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The tape is an offline information
packet. The secrets lifecycle names scopes and rotation windows only. It does
not generate, store, or load key material.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.security import contains_secret

MICROSTRUCTURE_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "gap-and-fail haircut when a gap above 1.5 percent closes back through the open",
    AssetClass.LARGE_CAP_ALT.value: "upper-wick haircut when the wick is more than half the bar",
    AssetClass.STABLECOIN.value: "peg-velocity watch when four-bar absolute deviation sums above 30 bp",
    AssetClass.DEFI.value: "volume-price divergence haircut when price rises and volume falls for three bars",
    AssetClass.MEME.value: "upper-wick veto when the wick is more than 55 percent of the range",
    AssetClass.L2.value: "range-dispersion haircut when the last range exceeds twice the median range",
    AssetClass.RWA.value: "session-gap haircut when the open gaps more than 2 percent from the prior close",
    AssetClass.PERPETUAL.value: "funding-price disagreement haircut when negative funding meets a 3 percent rise",
}

TAPE_STAGES = (
    {"stage": "ingest_fixture", "network": False, "can_trade": False},
    {"stage": "classify", "network": False, "can_trade": False},
    {"stage": "microstructure_guard", "network": False, "can_trade": False},
    {"stage": "tape", "network": False, "can_trade": False},
)

ROTATION_DAYS = {
    "market_read": 90,
    "audit_sign": 180,
    "break_glass": 30,
}

REFUSED_SCOPES = frozenset({"trade", "withdraw", "withdrawal", "transfer", "order", "seed", "private_key"})


def apply_v19(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Fifteenth-pass microstructure guard. Size cannot increase."""
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
        "guard": MICROSTRUCTURE_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _span(bar: Candle) -> float:
    return max(bar.high - bar.low, 0.0)


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    last = candles[-1]
    if previous <= 0 or size <= 0:
        return size, "major: gap-and-fail haircut not triggered"
    gap = last.open / previous - 1.0
    failed = gap > 0.015 and last.close < last.open
    if failed:
        return size * 0.5, "major gap-and-fail haircut"
    return size, "major: gap-and-fail haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = _span(last)
    wick = last.high - max(last.open, last.close)
    if size > 0 and span > 0 and wick / span > 0.50:
        return size * 0.5, "large-cap alt upper-wick haircut"
    return size, "large-cap alt: upper-wick haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    deviations = [abs(bar.close - 1.0) for bar in candles[-4:]]
    if sum(deviations) > 0.003:
        return "stablecoin peg-velocity watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    earlier = candles[-4].close
    rising = earlier > 0 and candles[-1].close / earlier - 1.0 > 0.02
    volumes = [bar.volume for bar in candles[-3:]]
    fading = volumes[0] > volumes[1] > volumes[2]
    if size > 0 and rising and fading:
        return size * 0.5, "defi volume-price divergence haircut"
    return size, "defi: volume-price divergence haircut not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = _span(last)
    wick = last.high - max(last.open, last.close)
    if size > 0 and span > 0 and wick / span > 0.55:
        return 0.0, "meme upper-wick veto"
    return size, "meme: upper-wick veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    ranges = [_span(bar) for bar in candles[-7:-1]]
    baseline = median(ranges) if ranges else 0.0
    if size > 0 and baseline > 0 and _span(candles[-1]) > 2.0 * baseline:
        return size * 0.5, "l2 range-dispersion haircut"
    return size, "l2: range-dispersion haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    if previous <= 0 or size <= 0:
        return size, "rwa: session-gap haircut not triggered"
    gap = abs(candles[-1].open / previous - 1.0)
    if gap > 0.02:
        return size * 0.5, "rwa session-gap haircut"
    return size, "rwa: session-gap haircut not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    earlier = candles[-6].close
    rise = earlier > 0 and candles[-1].close / earlier - 1.0 > 0.03
    if size > 0 and candles[-1].funding_rate < 0 and rise:
        return size * 0.5, "perp funding-price disagreement haircut"
    return size, "perp: funding-price disagreement haircut not triggered"


def information_tape(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline microstructure packet. A tape row is not an order and cannot raise size."""
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
        "version": "0.19.0",
        "cadence": "offline research cycle; no socket",
        "inputs": ["synthetic_fixture", "injected_public_print"],
        "stages": list(TAPE_STAGES),
        "rows": rows,
        "class_counts": by_class,
        "haircut_count": len(haircuts),
        "flat_count": len(flat),
        "tape_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def scope_decision(name: str, age_days: int) -> dict[str, object]:
    """Classify a credential name. Refused scopes cannot be rotated into use."""
    if contains_secret(name) or any(marker in name.lower() for marker in REFUSED_SCOPES):
        return {
            "name": "refused",
            "accepted": False,
            "rotate": False,
            "reason": "trade, withdrawal, seed, or secret-like names are out of scope",
            "can_trade": False,
            "can_enable_live": False,
        }
    scope = next((item for item in ROTATION_DAYS if item in name.lower()), None)
    if scope is None:
        return {
            "name": name,
            "accepted": False,
            "rotate": False,
            "reason": "scope must be market_read, audit_sign, or break_glass",
            "can_trade": False,
            "can_enable_live": False,
        }
    limit = ROTATION_DAYS[scope]
    return {
        "name": name,
        "scope": scope,
        "accepted": True,
        "rotate": age_days >= limit,
        "rotation_days": limit,
        "age_days": age_days,
        "material_stored": False,
        "can_trade": False,
        "can_enable_live": False,
    }


def acknowledge_rotation(roles: set[str]) -> dict[str, object]:
    """Two-person acknowledgement of a rotation. It cannot enable live trading."""
    ready = {"researcher", "auditor"} <= roles
    return {
        "acknowledged": ready,
        "required": ["researcher", "auditor"],
        "can_trade": False,
        "can_enable_live": False,
        "can_store_secret": False,
    }


def secrets_lifecycle() -> dict[str, object]:
    """Secrets-lifecycle plane. Names and windows only. No key material and no execution zone."""
    return {
        "version": "0.19.0",
        "framework": "research secrets lifecycle; not a MAS TRM, PDPA, SOC, NIST, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "material_stored": False,
        "zones": ["name", "scope", "rotate", "revoke", "audit"],
        "rotation_days": dict(ROTATION_DAYS),
        "refused_scopes": sorted(REFUSED_SCOPES),
        "controls": [
            {"name": "scope_allowlist", "effect": "only market_read, audit_sign, and break_glass names are allowed"},
            {"name": "rotation_window", "effect": "read 90 days, audit-sign 180 days, break-glass 30 days"},
            {"name": "zero_material", "effect": "this plane never generates or stores key bytes"},
            {"name": "dual_acknowledgement", "effect": "researcher and auditor must both acknowledge a rotation"},
            {"name": "microstructure_guard", "effect": "asset-class guards can only shrink paper size"},
        ],
        "duties": [
            {"identity": "researcher", "can_emit_tape": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_emit_tape": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_emit_tape": False, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_store_secret": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "a microstructure guard cannot raise a class size cap",
            "a tape digest is an information artifact, not an order",
            "trade, withdrawal, seed, and private-key scopes are refused",
            "rotation acknowledgement cannot enable live trading",
            "an automation runner cannot store a secret or mint a credential",
            "market-read names cannot authorise a trade or a withdrawal",
            "personal data and wallet addresses stay on the zero-retention path",
        ],
    }
