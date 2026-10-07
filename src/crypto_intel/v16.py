"""Version 0.16 correlation-break guards, information radar, and DLP plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The radar is an offline information
packet. The DLP plane refuses secret and personal-data egress. Neither path can
enable live trading.
"""

from __future__ import annotations

import hashlib
import re

from crypto_intel.models import AssetClass, Candle, Side

CORRELATION_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "whipsaw haircut when four returns alternate sign and each exceeds 0.5 percent",
    AssetClass.LARGE_CAP_ALT.value: "volume-divergence haircut when price rises and the last three volumes fall",
    AssetClass.STABLECOIN.value: "peg-persistence watch when four closes stay on one side of par; size stays zero",
    AssetClass.DEFI.value: "cascade veto when four returns share a sign and mean absolute return exceeds 4 percent",
    AssetClass.MEME.value: "participation-break haircut when three up closes arrive on falling volume",
    AssetClass.L2.value: "path-break haircut when the six-bar and three-bar returns disagree beyond 2 percent",
    AssetClass.RWA.value: "jump-cluster veto when three same-sign gaps each exceed 0.4 percent",
    AssetClass.PERPETUAL.value: "funding-divergence haircut when funding and six-bar drift disagree",
}

RADAR_STAGES = (
    {"stage": "ingest_fixture", "network": False, "can_trade": False},
    {"stage": "classify", "network": False, "can_trade": False},
    {"stage": "correlation_guard", "network": False, "can_trade": False},
    {"stage": "radar", "network": False, "can_trade": False},
)

_SECRET_EGRESS = re.compile(
    r"(?i)(api[_-]?key|secret|password|token|seed|private[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}"
)
_WALLET_EGRESS = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
_EMAIL_EGRESS = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_EGRESS = re.compile(r"(?:\+65[\s-]?)?[89]\d{7}")


def apply_v16(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Twelfth-pass correlation-break guard. Size cannot increase."""
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
        "guard": CORRELATION_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _returns(candles: list[Candle]) -> list[float]:
    closes = [bar.close for bar in candles]
    return [closes[index] / closes[index - 1] - 1.0 for index in range(1, len(closes)) if closes[index - 1]]


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    returns = _returns(candles)[-4:]
    if size <= 0 or len(returns) < 4:
        return size, "major: whipsaw haircut not triggered"
    alternating = all(returns[index] * returns[index + 1] < 0 for index in range(3))
    material = all(abs(value) > 0.005 for value in returns)
    if alternating and material:
        return size * 0.5, "major whipsaw haircut"
    return size, "major: whipsaw haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    prior = candles[-4].close
    volumes = [bar.volume for bar in candles[-3:]]
    rising = prior > 0 and last.close / prior - 1.0 > 0.01
    fading = volumes[0] > volumes[1] > volumes[2]
    if size > 0 and rising and fading:
        return size * 0.5, "large-cap alt volume-divergence haircut"
    return size, "large-cap alt: volume-divergence haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    closes = [bar.close for bar in candles[-4:]]
    same_side = all(value > 1.0 for value in closes) or all(value < 1.0 for value in closes)
    drifted = any(abs(value - 1.0) > 0.002 for value in closes)
    if same_side and drifted:
        return "stablecoin peg-persistence watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    returns = _returns(candles)[-4:]
    if size <= 0 or len(returns) < 4:
        return size, "defi: cascade veto not triggered"
    same_sign = all(value > 0 for value in returns) or all(value < 0 for value in returns)
    if same_sign and sum(abs(value) for value in returns) / 4 > 0.04:
        return 0.0, "defi cascade veto"
    return size, "defi: cascade veto not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-4:]]
    volumes = [bar.volume for bar in candles[-3:]]
    rising = closes[0] < closes[1] < closes[2] < closes[3]
    fading = volumes[0] > volumes[1] > volumes[2]
    if size > 0 and rising and fading:
        return size * 0.5, "meme participation-break haircut"
    return size, "meme: participation-break haircut not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles]
    if size <= 0 or closes[-6] <= 0 or closes[-3] <= 0:
        return size, "l2: path-break haircut not triggered"
    six = closes[-1] / closes[-6] - 1.0
    three = closes[-1] / closes[-3] - 1.0
    if six * three < 0 and abs(six) > 0.02 and abs(three) > 0.02:
        return size * 0.5, "l2 path-break haircut"
    return size, "l2: path-break haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    gaps = []
    for previous, current in zip(candles[-4:-1], candles[-3:], strict=False):
        if previous.close:
            gaps.append(current.open / previous.close - 1.0)
    if size > 0 and len(gaps) == 3:
        same_sign = all(value > 0 for value in gaps) or all(value < 0 for value in gaps)
        if same_sign and all(abs(value) > 0.004 for value in gaps):
            return 0.0, "rwa jump-cluster veto"
    return size, "rwa: jump-cluster veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles]
    funding = candles[-1].funding_rate
    if size <= 0 or closes[-6] <= 0:
        return size, "perp: funding-divergence haircut not triggered"
    drift = closes[-1] / closes[-6] - 1.0
    disagrees = funding * drift < 0 and abs(funding) >= 0.0004 and abs(drift) > 0.02
    if disagrees:
        return size * 0.5, "perp funding-divergence haircut"
    return size, "perp: funding-divergence haircut not triggered"


def information_radar(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline class-health packet. A radar row is not an order and cannot raise size."""
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
        "version": "0.16.0",
        "cadence": "offline research cycle; no socket",
        "inputs": ["synthetic_fixture", "injected_public_print"],
        "stages": list(RADAR_STAGES),
        "rows": rows,
        "class_counts": by_class,
        "haircut_count": len(haircuts),
        "flat_count": len(flat),
        "radar_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def scan_egress(text: str) -> dict[str, object]:
    """Refuse secret, wallet, email, or phone-like strings before any egress."""
    findings = []
    if _SECRET_EGRESS.search(text):
        findings.append("secret")
    if _WALLET_EGRESS.search(text):
        findings.append("wallet")
    if _EMAIL_EGRESS.search(text):
        findings.append("email")
    if _PHONE_EGRESS.search(text):
        findings.append("phone")
    return {
        "allowed": not findings,
        "findings": findings,
        "destination": "research_digest" if not findings else "blocked",
        "can_enable_live": False,
        "order_path": False,
    }


def dlp_plane() -> dict[str, object]:
    """Data-loss-prevention egress plane. No execution zone and no live path."""
    return {
        "version": "0.16.0",
        "framework": "research DLP egress plane; not a MAS TRM, PDPA, SOC, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "zones": ["research", "audit", "dlp"],
        "egress": {
            "allowed_destinations": ["local_research_digest"],
            "refused_destinations": ["exchange_order", "withdrawal", "public_issue", "chat_paste", "email"],
            "allowed_payloads": ["class_label", "size_fraction", "redacted_note", "radar_digest"],
            "refused_payloads": [
                "seed",
                "private_key",
                "trade_api_secret",
                "withdrawal_key",
                "wallet_address",
                "email",
                "phone",
                "nric",
            ],
            "retention_credentials": "zero",
            "retention_personal_data": "zero",
        },
        "duties": [
            {"identity": "researcher", "can_emit_digest": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_emit_digest": True, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_emit_digest": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "a correlation guard cannot raise a class size cap",
            "a radar digest is an information artifact, not an order",
            "secret, wallet, email, and phone-like strings are blocked before egress",
            "an automation runner cannot emit a digest or enable live trading",
            "no DLP exception can open an order or withdrawal path",
            "trade keys, withdrawal keys, seeds, and personal data are refused and are not stored",
        ],
    }
