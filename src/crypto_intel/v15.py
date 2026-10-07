"""Version 0.15 concentration guards, information ledger, and segregation plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The ledger is an offline information
packet. The segregation plane describes research controls only.
"""

from __future__ import annotations

import hashlib

from crypto_intel.models import AssetClass, Candle, Side

CONCENTRATION_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "open-gap haircut when a 1.5 percent gap closes further from the prior close",
    AssetClass.LARGE_CAP_ALT.value: "failed-expansion haircut when ranges widen and close returns inside the prior bar",
    AssetClass.STABLECOIN.value: "premium-persistence watch when a close stays beyond 50 bp; size stays zero",
    AssetClass.DEFI.value: "unlock-window veto when three closes fall and three ranges expand",
    AssetClass.MEME.value: "climax veto when volume exceeds 4x the prior median and the close is in the lower range",
    AssetClass.L2.value: "sequencer-stall haircut when three closes are unchanged and volume declines",
    AssetClass.RWA.value: "oracle-gap veto when the open jumps more than 1.5 percent from the prior close",
    AssetClass.PERPETUAL.value: "crowded-expansion haircut when ranges widen and funding agrees with the paper side",
}

LEDGER_STAGES = (
    {"stage": "ingest_fixture", "network": False, "can_trade": False},
    {"stage": "classify", "network": False, "can_trade": False},
    {"stage": "concentration_guard", "network": False, "can_trade": False},
    {"stage": "attest", "network": False, "can_trade": False},
    {"stage": "append_ledger", "network": False, "can_trade": False},
)


def apply_v15(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Eleventh-pass concentration guard. Size cannot increase."""
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
        size, note = _perpetual(candles, size, side)
    size = min(size, proposed_size if proposed_size > 0 else 0.0)
    return {
        "symbol": candles[-1].symbol,
        "asset_class": asset_class.value,
        "side": side.value if size > 0 else Side.FLAT.value,
        "size_fraction": round(max(size, 0.0), 6),
        "note": note,
        "guard": CONCENTRATION_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _prior_median_volume(candles: list[Candle]) -> float:
    volumes = sorted(bar.volume for bar in candles[-8:-1])
    return volumes[len(volumes) // 2]


def _bar_range(bar: Candle) -> float:
    return bar.high - bar.low


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    last = candles[-1]
    if previous <= 0 or size <= 0:
        return size, "major: open-gap haircut not triggered"
    gap = last.open / previous - 1.0
    extended = (last.close - previous) * gap > 0 and abs(last.close / previous - 1.0) > abs(gap)
    if abs(gap) > 0.015 and extended:
        return size * 0.5, "major open-gap haircut"
    return size, "major: open-gap haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    ranges = [_bar_range(bar) for bar in candles[-3:]]
    widening = ranges[0] < ranges[1] < ranges[2]
    prior = candles[-2]
    last = candles[-1]
    inside = prior.low <= last.close <= prior.high
    if size > 0 and widening and inside:
        return size * 0.5, "large-cap alt failed-expansion haircut"
    return size, "large-cap alt: failed-expansion haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    premium = any(abs(bar.close - 1.0) > 0.005 for bar in candles[-3:])
    if premium:
        return "stablecoin premium-persistence watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-3:]]
    ranges = [_bar_range(bar) for bar in candles[-3:]]
    falling = closes[0] > closes[1] > closes[2]
    expanding = ranges[0] < ranges[1] < ranges[2]
    if size > 0 and falling and expanding:
        return 0.0, "defi unlock-window veto"
    return size, "defi: unlock-window veto not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = _bar_range(last)
    base = _prior_median_volume(candles)
    location = (last.close - last.low) / span if span else 1.0
    if size > 0 and base > 0 and last.volume > 4.0 * base and location < 0.4:
        return 0.0, "meme climax veto"
    return size, "meme: climax veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-3:]]
    volumes = [bar.volume for bar in candles[-3:]]
    stalled = closes[0] == closes[1] == closes[2]
    fading = volumes[0] > volumes[1] > volumes[2]
    if size > 0 and stalled and fading:
        return size * 0.5, "l2 sequencer-stall haircut"
    return size, "l2: sequencer-stall haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    last = candles[-1]
    if previous <= 0 or size <= 0:
        return size, "rwa: oracle-gap veto not triggered"
    gap = abs(last.open / previous - 1.0)
    if gap > 0.015:
        return 0.0, "rwa oracle-gap veto"
    return size, "rwa: oracle-gap veto not triggered"


def _perpetual(candles: list[Candle], size: float, side: Side) -> tuple[float, str]:
    ranges = [_bar_range(bar) for bar in candles[-3:]]
    expanding = ranges[0] < ranges[1] < ranges[2]
    funding = candles[-1].funding_rate
    agrees = (side is Side.LONG and funding > 0.0004) or (side is Side.SHORT and funding < -0.0004)
    if size > 0 and expanding and agrees:
        return size * 0.5, "perp crowded-expansion haircut"
    return size, "perp: crowded-expansion haircut not triggered"


def information_ledger(rows: list[dict[str, object]], *, previous_digest: str = "") -> dict[str, object]:
    """Offline hash-chained information packet. A digest is not an order."""
    material = (
        previous_digest
        + "|"
        + "|".join(
            f"{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}:{row.get('note')}" for row in rows
        )
    )
    digest = hashlib.sha256(material.encode()).hexdigest()
    halted = [row for row in rows if float(row.get("size_fraction", 0.0)) == 0.0]
    return {
        "version": "0.15.0",
        "cadence": "offline research cycle; no socket",
        "inputs": ["synthetic_fixture", "injected_public_print"],
        "stages": list(LEDGER_STAGES),
        "rows": rows,
        "flat_count": len(halted),
        "previous_digest": previous_digest,
        "ledger_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def segregation_plane() -> dict[str, object]:
    """Research segregation and data-minimisation plane. No keys and no execution zone."""
    duties = (
        {
            "identity": "researcher",
            "can_read_research": True,
            "can_append_audit": False,
            "can_trade": False,
            "can_enable_live": False,
        },
        {
            "identity": "auditor",
            "can_read_research": True,
            "can_append_audit": True,
            "can_trade": False,
            "can_enable_live": False,
        },
        {
            "identity": "automation_runner",
            "can_read_research": False,
            "can_append_audit": False,
            "can_trade": False,
            "can_enable_live": False,
        },
    )
    return {
        "version": "0.15.0",
        "framework": "research segregation plane; not a MAS TRM, PDPA, SOC, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "zones": ["research", "audit", "automation"],
        "duties": list(duties),
        "data_classes": {
            "allowed": ["synthetic_research", "attested_public_prints", "redacted_audit"],
            "refused": [
                "seed",
                "private_key",
                "trade_api_secret",
                "withdrawal_key",
                "personal_data",
                "customer_wallet",
            ],
            "purpose": "paper research digest only",
            "retention_credentials": "zero",
            "retention_personal_data": "zero",
            "minimisation": "store digests and class labels, not raw secrets or identity fields",
        },
        "segregation": {
            "researcher_can_clear_halt": False,
            "automation_can_write_audit": False,
            "auditor_can_place_order": False,
            "dual_control_can_enable_live": False,
        },
        "automation": {
            "network": False,
            "can_open_socket": False,
            "can_place_order": False,
            "can_enable_live": False,
        },
        "principles": [
            "a concentration guard cannot raise a class size cap",
            "a ledger digest is an information artifact, not an order",
            "an automation runner cannot read research records or enable live trading",
            "a researcher cannot append the audit log or clear a halt",
            "dual control of a research digest cannot enable live trading",
            "trade keys, withdrawal keys, seeds, and personal data are refused and are not stored",
        ],
    }
