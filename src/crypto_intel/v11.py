"""Version 0.11 session guards, information bulletin, and CSF control plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The CSF report is a defensive
control map, not a certification and not legal advice.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

SESSION_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "extension haircut when close is more than 8 percent above the 8-bar mean",
    AssetClass.LARGE_CAP_ALT.value: "gap haircut when the open gaps more than 6 percent from the prior close",
    AssetClass.STABLECOIN.value: "intrabar dispersion watch; size stays zero",
    AssetClass.DEFI.value: "range-expansion veto when the last bar range exceeds twice the prior median",
    AssetClass.MEME.value: "consecutive gap veto when the last two opens gap up more than 8 percent",
    AssetClass.L2.value: "stuck-print veto when the last three volumes are identical",
    AssetClass.RWA.value: "session-gap veto when the open gaps more than 4 percent from the prior close",
    AssetClass.PERPETUAL.value: "crowded-funding veto when funding and volume are both extended",
}

CSF_FUNCTIONS = (
    {
        "function": "govern",
        "control": "paper-only policy, human review, and a named owner for research parameters",
        "evidence": "AGENTS.md, review log, parameter digest",
    },
    {
        "function": "identify",
        "control": "asset-class catalog, data classification, and source attestation",
        "evidence": "catalog.py, classification.py, posture attestation",
    },
    {
        "function": "protect",
        "control": "least privilege, zero retention for credentials and personal data, egress allowlist",
        "evidence": "posture roles, cyber plane, PDPA tripwire",
    },
    {
        "function": "detect",
        "control": "feed jump and staleness checks, hash-chain verification, secret scan",
        "evidence": "quality.py, AuditLog.verify, gitleaks CI",
    },
    {
        "function": "respond",
        "control": "kill switch and incident playbook; recovery cannot enable live trading",
        "evidence": "cyber.incident_playbook",
    },
    {
        "function": "recover",
        "control": "redacted audit and synthetic fixtures only; secrets are not backed up",
        "evidence": "cyber plane backup rule",
    },
)


def apply_v11(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Seventh-pass session and structure guard. Size cannot increase."""
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
        "guard": SESSION_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _mean_close(candles: list[Candle]) -> float:
    window = candles[-8:]
    return sum(bar.close for bar in window) / len(window)


def _gap(current: Candle, previous: Candle) -> float:
    if previous.close == 0:
        return 0.0
    return abs(current.open - previous.close) / abs(previous.close)


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _mean_close(candles)
    if size > 0 and base > 0 and candles[-1].close > base * 1.08:
        return size * 0.5, "major extension haircut"
    return size, "major: extension haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    if size > 0 and _gap(candles[-1], candles[-2]) > 0.06:
        return size * 0.5, "large-cap alt gap haircut"
    return size, "large-cap alt: gap haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    last = candles[-1]
    if last.close > 0 and (last.high - last.low) / last.close >= 0.003:
        return "stablecoin intrabar dispersion watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = [bar.high - bar.low for bar in candles[-8:-1]]
    last_range = candles[-1].high - candles[-1].low
    base = float(median(prior)) if prior else 0.0
    if size > 0 and base > 0 and last_range > 2.0 * base:
        return 0.0, "defi range-expansion veto"
    return size, "defi: range-expansion veto not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    gap_one = _gap(candles[-1], candles[-2])
    gap_two = _gap(candles[-2], candles[-3])
    up = candles[-1].open > candles[-2].close and candles[-2].open > candles[-3].close
    if size > 0 and up and gap_one > 0.08 and gap_two > 0.08:
        return 0.0, "meme consecutive-gap veto"
    return size, "meme: consecutive-gap veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    volumes = [bar.volume for bar in candles[-3:]]
    if size > 0 and volumes[0] > 0 and volumes[0] == volumes[1] == volumes[2]:
        return 0.0, "l2 stuck-print veto"
    return size, "l2: stuck-print veto not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    if size > 0 and _gap(candles[-1], candles[-2]) > 0.04:
        return 0.0, "rwa session-gap veto"
    return size, "rwa: session-gap veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    base = float(median(bar.volume for bar in candles[-8:]))
    last = candles[-1]
    if size > 0 and abs(last.funding_rate) > 0.0015 and base > 0 and last.volume > 2.0 * base:
        return 0.0, "perp crowded-funding veto"
    return size, "perp: crowded-funding veto not triggered"


def information_bulletin(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline research bulletin. It is not an order and cannot raise size."""
    counts: Counter[str] = Counter(str(row.get("asset_class", "unknown")) for row in rows)
    gross = round(sum(float(row.get("size_fraction", 0.0)) for row in rows), 6)
    material = "|".join(f"{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}" for row in rows)
    return {
        "version": "0.11.0",
        "class_counts": dict(sorted(counts.items())),
        "gross_paper_fraction": gross,
        "bulletin_digest": hashlib.sha256(material.encode()).hexdigest(),
        "live_enabled": False,
        "order_path": False,
        "order_instruction": False,
        "can_increase_size": False,
        "paper_only": True,
    }


def csf_report() -> dict[str, object]:
    """NIST CSF-style control map for the paper research plane. No execution zone."""
    duties = (
        {"role": "researcher", "can_scan": True, "can_trade": False, "can_enable_live": False},
        {"role": "auditor", "can_scan": False, "can_trade": False, "can_enable_live": False},
        {"role": "operator", "can_scan": True, "can_trade": False, "can_enable_live": False},
    )
    return {
        "version": "0.11.0",
        "framework": "NIST CSF 2.0 style map; not a certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "functions": list(CSF_FUNCTIONS),
        "separation_of_duties": list(duties),
        "data_plane": {
            "allowed": ["synthetic_research", "attested_public_prints", "redacted_audit"],
            "refused": ["credential", "seed", "withdrawal_key", "personal_data"],
            "retention_credentials": "zero",
            "retention_personal_data": "zero",
        },
        "integrity": "hash-chained audit; a failed verify halts the research report",
        "residency": "this tree stores synthetic fixtures only",
        "principles": [
            "a session guard cannot raise a class size cap",
            "a bulletin is an information artifact, not an order",
            "no role can place an order or enable live trading",
            "credentials and personal data are refused, not encrypted in git",
        ],
    }
