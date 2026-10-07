"""Version 0.14 decay guards, information watchtower, and evidence plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The watchtower is an offline
information packet. The evidence plane describes research controls only.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

DECAY_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "participation-decay haircut when the last three volumes fall and the last return is still directional",
    AssetClass.LARGE_CAP_ALT.value: "failed-follow-through haircut when a material prior move is retraced by more than half",
    AssetClass.STABLECOIN.value: "depeg-persistence watch when the last three closes stay beyond 20 bp on one side; size stays zero",
    AssetClass.DEFI.value: "liquidity-vacuum veto when volume collapses and the bar range expands",
    AssetClass.MEME.value: "wick-rejection veto after an up bar when the upper wick is more than twice the body",
    AssetClass.L2.value: "bridge-flow haircut when volume spikes and the print barely moves",
    AssetClass.RWA.value: "attestation-gap veto when the last print is flat and volume is thin",
    AssetClass.PERPETUAL.value: "funding-persistence haircut when crowded funding and the last return extend together",
}

AUTOMATION_STAGES = (
    {"stage": "ingest_fixture", "network": False, "can_trade": False},
    {"stage": "classify", "network": False, "can_trade": False},
    {"stage": "decay_guard", "network": False, "can_trade": False},
    {"stage": "attest", "network": False, "can_trade": False},
    {"stage": "publish_digest", "network": False, "can_trade": False},
)

DETECTION_CASES = (
    {"use_case": "secret_like_string", "action": "refuse_and_redact", "can_enable_live": False},
    {"use_case": "size_increase_attempt", "action": "clamp_to_prior", "can_enable_live": False},
    {"use_case": "live_mode_request", "action": "permission_error", "can_enable_live": False},
    {"use_case": "feed_jump", "action": "class_guard_or_halt", "can_enable_live": False},
    {"use_case": "withdrawal_path", "action": "refuse", "can_enable_live": False},
)


def apply_v14(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Tenth-pass decay guard. Size cannot increase."""
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
        "guard": DECAY_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _prior_median_volume(candles: list[Candle]) -> float:
    return float(median(bar.volume for bar in candles[-8:-1]))


def _prior_median_range(candles: list[Candle]) -> float:
    return float(median(bar.high - bar.low for bar in candles[-8:-1]))


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    volumes = [bar.volume for bar in candles[-3:]]
    declining = volumes[0] > volumes[1] > volumes[2]
    previous = candles[-2].close
    bar_return = (candles[-1].close / previous - 1.0) if previous else 0.0
    if size > 0 and declining and abs(bar_return) > 0.01:
        return size * 0.5, "major participation-decay haircut"
    return size, "major: participation-decay haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    base = candles[-3].close
    mid = candles[-2].close
    prior_move = (mid / base - 1.0) if base else 0.0
    last_move = (candles[-1].close / mid - 1.0) if mid else 0.0
    retraced = prior_move * last_move < 0 and abs(last_move) > 0.5 * abs(prior_move)
    if size > 0 and abs(prior_move) > 0.03 and retraced:
        return size * 0.5, "large-cap alt failed-follow-through haircut"
    return size, "large-cap alt: failed-follow-through haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    deviations = [bar.close - 1.0 for bar in candles[-3:]]
    persistent = all(item > 0.002 for item in deviations) or all(item < -0.002 for item in deviations)
    if persistent:
        return "stablecoin depeg-persistence watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    base_volume = _prior_median_volume(candles)
    base_range = _prior_median_range(candles)
    last = candles[-1]
    thin = base_volume > 0 and last.volume < 0.4 * base_volume
    wide = base_range > 0 and (last.high - last.low) > 2.0 * base_range
    if size > 0 and thin and wide:
        return 0.0, "defi liquidity-vacuum veto"
    return size, "defi: liquidity-vacuum veto not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    body = abs(last.close - last.open)
    upper = last.high - max(last.open, last.close)
    prior_up = candles[-2].close > candles[-3].close
    rejected = last.close < last.open and body > 0 and upper > 2.0 * body
    if size > 0 and prior_up and rejected:
        return 0.0, "meme wick-rejection veto"
    return size, "meme: wick-rejection veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    base = _prior_median_volume(candles)
    quiet = last.close > 0 and (last.high - last.low) / last.close < 0.003
    if size > 0 and base > 0 and last.volume > 3.0 * base and quiet:
        return size * 0.5, "l2 bridge-flow haircut"
    return size, "l2: bridge-flow haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    base = _prior_median_volume(candles)
    flat = last.open == last.close
    if size > 0 and base > 0 and last.volume < 0.1 * base and flat:
        return 0.0, "rwa attestation-gap veto"
    return size, "rwa: attestation-gap veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    fundings = [bar.funding_rate for bar in candles[-3:]]
    crowded_long = all(item > 0.0005 for item in fundings)
    crowded_short = all(item < -0.0005 for item in fundings)
    previous = candles[-2].close
    bar_return = (candles[-1].close / previous - 1.0) if previous else 0.0
    extending = (crowded_long and bar_return > 0.015) or (crowded_short and bar_return < -0.015)
    if size > 0 and extending:
        return size * 0.5, "perp funding-persistence haircut"
    return size, "perp: funding-persistence haircut not triggered"


def information_watchtower(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline automation packet. A digest is not an order."""
    halted = [row for row in rows if float(row.get("size_fraction", 0.0)) == 0.0 and row.get("side") == "flat"]
    material = "|".join(
        f"{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}:{row.get('note')}" for row in rows
    )
    return {
        "version": "0.14.0",
        "cadence": "offline research cycle; no socket",
        "inputs": ["synthetic_fixture", "injected_public_print"],
        "stages": list(AUTOMATION_STAGES),
        "rows": rows,
        "flat_count": len(halted),
        "watch_digest": hashlib.sha256(material.encode()).hexdigest(),
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def evidence_plane() -> dict[str, object]:
    """Research evidence and data-security plane. No keys and no execution zone."""
    identities = (
        {"identity": "researcher", "can_read_evidence": True, "can_trade": False, "can_enable_live": False},
        {"identity": "auditor", "can_read_evidence": True, "can_trade": False, "can_enable_live": False},
        {"identity": "automation_runner", "can_read_evidence": False, "can_trade": False, "can_enable_live": False},
    )
    return {
        "version": "0.14.0",
        "framework": "research evidence plane; not a SOC certification or legal opinion",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "zones": ["research", "audit", "automation"],
        "identities": list(identities),
        "detection": list(DETECTION_CASES),
        "evidence": {
            "contents": ["watch_digest", "parameter_digest", "redacted_audit"],
            "immutable": True,
            "seed_backup": False,
            "secret_material": False,
            "can_restore_live_trading": False,
        },
        "data_plane": {
            "allowed": ["synthetic_research", "attested_public_prints", "redacted_audit"],
            "refused": ["seed", "private_key", "trade_api_secret", "withdrawal_key", "personal_data"],
            "retention_credentials": "zero",
            "retention_personal_data": "zero",
            "encryption_expectation": "operator-held at rest; keys are not in this tree",
        },
        "automation": {
            "network": False,
            "can_open_socket": False,
            "can_place_order": False,
            "can_enable_live": False,
        },
        "principles": [
            "a decay guard cannot raise a class size cap",
            "a watchtower digest is an information artifact, not an order",
            "an automation runner cannot read evidence or enable live trading",
            "detection actions cannot enable live trading",
            "evidence restore cannot enable live trading",
            "trade and withdrawal secrets are refused and are not stored",
        ],
    }
