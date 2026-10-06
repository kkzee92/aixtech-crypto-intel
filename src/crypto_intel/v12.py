"""Version 0.12 basis and inventory guards, plus a custody data-security plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The custody plane describes research
zones only. It does not create keys, allowlists, or an execution path.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

BASIS_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "basis-instability haircut when funding flips sign across the last three bars",
    AssetClass.LARGE_CAP_ALT.value: "thin-participation haircut when the last volume is below half the prior median",
    AssetClass.STABLECOIN.value: "persistent-depeg watch; size stays zero",
    AssetClass.DEFI.value: "inventory-unwind veto when four closes trend more than 10 percent",
    AssetClass.MEME.value: "wash-print veto when volume spikes and the bar barely moves",
    AssetClass.L2.value: "imbalance haircut when the bar is wide and volume is below the median",
    AssetClass.RWA.value: "unusual-print veto when volume is more than three times the median",
    AssetClass.PERPETUAL.value: "crowded-basis haircut when funding and three-bar drift share a sign",
}

ZONES = (
    {"zone": "research_hot", "holds": "ephemeral desk notes", "retention": "session", "can_trade": False},
    {"zone": "research_warm", "holds": "synthetic fixtures", "retention": "repository", "can_trade": False},
    {"zone": "research_cold", "holds": "signed digests only", "retention": "audit", "can_trade": False},
)

TRM_DOMAINS = (
    {"domain": "governance", "control": "paper-only policy and a named owner for research parameters"},
    {"domain": "asset_management", "control": "asset-class catalog and fixture source attestation"},
    {"domain": "access_control", "control": "researcher, auditor, and operator cannot trade or enable live trading"},
    {"domain": "cryptography", "control": "no seeds or private keys in this tree; digests are sha256 only"},
    {"domain": "data", "control": "credentials and personal data are refused; fixtures are synthetic"},
    {"domain": "change_management", "control": "parameter digest changes require a recorded human review"},
    {"domain": "incident", "control": "kill switch and playbook; recovery cannot enable live trading"},
    {"domain": "cyber_hygiene", "control": "secret scan, PDPA tripwire, and hash-chain verification"},
)


def apply_v12(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Eighth-pass basis and inventory guard. Size cannot increase."""
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
        "guard": BASIS_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _prior_median_volume(candles: list[Candle]) -> float:
    return float(median(bar.volume for bar in candles[-8:-1]))


def _funding_flipped(candles: list[Candle]) -> bool:
    rates = [bar.funding_rate for bar in candles[-3:]]
    signs = [1 if rate > 0 else -1 if rate < 0 else 0 for rate in rates]
    return 1 in signs and -1 in signs


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    if size > 0 and _funding_flipped(candles):
        return size * 0.5, "major basis-instability haircut"
    return size, "major: basis-instability haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _prior_median_volume(candles)
    if size > 0 and base > 0 and candles[-1].volume < 0.5 * base:
        return size * 0.5, "large-cap alt thin-participation haircut"
    return size, "large-cap alt: thin-participation haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    deviations = [abs(bar.close - 1.0) for bar in candles[-3:]]
    if all(deviation > 0.002 for deviation in deviations):
        return "stablecoin persistent-depeg watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-4:]]
    rising = closes[0] < closes[1] < closes[2] < closes[3]
    move = (closes[-1] / closes[0] - 1.0) if closes[0] else 0.0
    if size > 0 and rising and move > 0.10:
        return 0.0, "defi inventory-unwind veto"
    return size, "defi: inventory-unwind veto not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _prior_median_volume(candles)
    last = candles[-1]
    quiet = last.open > 0 and abs(last.close - last.open) / last.open < 0.01
    if size > 0 and base > 0 and last.volume > 8.0 * base and quiet:
        return 0.0, "meme wash-print veto"
    return size, "meme: wash-print veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    base = _prior_median_volume(candles)
    wide = last.close > 0 and (last.high - last.low) / last.close > 0.05
    if size > 0 and base > 0 and wide and last.volume < base:
        return size * 0.5, "l2 imbalance haircut"
    return size, "l2: imbalance haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _prior_median_volume(candles)
    if size > 0 and base > 0 and candles[-1].volume > 3.0 * base:
        return 0.0, "rwa unusual-print veto"
    return size, "rwa: unusual-print veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    earlier = candles[-4].close
    drift = last.close - earlier
    same_sign = drift != 0 and last.funding_rate != 0 and (drift > 0) == (last.funding_rate > 0)
    if size > 0 and same_sign and abs(last.funding_rate) > 0.0005:
        return size * 0.5, "perp crowded-basis haircut"
    return size, "perp: crowded-basis haircut not triggered"


def information_desk(rows: list[dict[str, object]], *, fixture_label: str) -> dict[str, object]:
    """Offline desk note with a lineage digest. It is not an order."""
    if not fixture_label or "SYNTHETIC" not in fixture_label.upper():
        raise ValueError("desk notes require a synthetic fixture label")
    gross = round(sum(float(row.get("size_fraction", 0.0)) for row in rows), 6)
    material = "|".join(
        f"{fixture_label}:{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}" for row in rows
    )
    return {
        "version": "0.12.0",
        "fixture_label": fixture_label,
        "gross_paper_fraction": gross,
        "lineage_digest": hashlib.sha256(material.encode()).hexdigest(),
        "live_enabled": False,
        "order_path": False,
        "order_instruction": False,
        "can_increase_size": False,
        "paper_only": True,
    }


def custody_plane() -> dict[str, object]:
    """Research custody and data-security plane. No keys and no execution zone."""
    signers = (
        {"role": "researcher", "can_sign_digest": True, "can_trade": False, "can_enable_live": False},
        {"role": "auditor", "can_sign_digest": True, "can_trade": False, "can_enable_live": False},
        {"role": "operator", "can_sign_digest": False, "can_trade": False, "can_enable_live": False},
    )
    return {
        "version": "0.12.0",
        "framework": "research custody plane; MAS TRM-style map, not a certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "withdrawal_allowlist": [],
        "withdrawal_allowlist_immutable": True,
        "zones": list(ZONES),
        "trm_domains": list(TRM_DOMAINS),
        "separation_of_duties": list(signers),
        "quorum": {"acknowledgements_required": 2, "can_enable_live": False},
        "data_plane": {
            "allowed": ["synthetic_research", "attested_public_prints", "redacted_audit"],
            "refused": ["seed", "private_key", "trade_api_secret", "withdrawal_key", "personal_data"],
            "retention_credentials": "zero",
            "retention_personal_data": "zero",
        },
        "principles": [
            "a basis guard cannot raise a class size cap",
            "a desk note is an information artifact, not an order",
            "the withdrawal allowlist in this tree is empty and immutable",
            "an operator cannot sign a research digest",
            "two acknowledgements still cannot enable live trading",
        ],
    }
