"""Version 0.8 asset-class overlays, offline schedule, and data plane.

Overlays can shrink or refuse a paper size. They cannot raise a class cap,
open a socket, store a secret, or place an order. The schedule is a declared
information cadence, not an exchange poller.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

OVERLAY_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "thin-liquidity haircut when the last volume is below half the prior median",
    AssetClass.LARGE_CAP_ALT.value: "close-location haircut when the close sits in the bottom quarter of the bar",
    AssetClass.STABLECOIN.value: "secondary peg watch; size stays zero inside or outside the band",
    AssetClass.DEFI.value: "volume-collapse halt when the last volume is below 30 percent of the prior median",
    AssetClass.MEME.value: "upper-wick veto when the wick is more than 60 percent of the bar range",
    AssetClass.L2.value: "fee-spike proxy haircut when the last range is more than 3x the prior median",
    AssetClass.RWA.value: "slow-confirmation veto when a long is not above the close three bars ago",
    AssetClass.PERPETUAL.value: "activity-spike haircut when volume is more than 3x the prior median",
}

# Declared information cadence. An external scheduler may call the CLI.
CADENCE_MINUTES: dict[str, int] = {
    AssetClass.MAJOR.value: 15,
    AssetClass.LARGE_CAP_ALT.value: 30,
    AssetClass.STABLECOIN.value: 5,
    AssetClass.DEFI.value: 30,
    AssetClass.MEME.value: 15,
    AssetClass.L2.value: 30,
    AssetClass.RWA.value: 240,
    AssetClass.PERPETUAL.value: 5,
}

DATA_CLASSES: tuple[dict[str, object], ...] = (
    {
        "name": "public_market",
        "examples": "symbol, OHLCV, funding",
        "retention_days": 400,
        "pii": False,
        "secret": False,
        "zone": "research",
    },
    {
        "name": "research_audit",
        "examples": "hash-chained events after redaction",
        "retention_days": 365,
        "pii": False,
        "secret": False,
        "zone": "audit",
    },
    {
        "name": "synthetic_fixture",
        "examples": "labelled candles",
        "retention_days": 3650,
        "pii": False,
        "secret": False,
        "zone": "research",
    },
    {
        "name": "restricted_ops",
        "examples": "kill-switch state, rotation date, scope name",
        "retention_days": 365,
        "pii": False,
        "secret": False,
        "zone": "control",
    },
)

REFUSED_CLASSES = ("trade_credential", "withdrawal_credential", "wallet_seed", "personal_data")

ZONES = ("research", "control", "audit")


def apply_v08(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Fourth-pass research overlay. Size cannot increase."""
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
        size, note = _rwa(candles, size, side)
    else:
        size, note = _perpetual(candles, size)
    size = min(size, proposed_size if proposed_size > 0 else 0.0)
    return {
        "symbol": candles[-1].symbol,
        "asset_class": asset_class.value,
        "side": side.value if size > 0 else Side.FLAT.value,
        "size_fraction": round(max(size, 0.0), 6),
        "note": note,
        "overlay": OVERLAY_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _prior_median(values: list[float]) -> float:
    return median(values) if values else 0.0


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _prior_median([candle.volume for candle in candles[-8:-1]])
    if base > 0 and candles[-1].volume < base * 0.5 and size > 0:
        return size * 0.5, "major thin-liquidity haircut"
    return size, "major: thin-liquidity haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = last.high - last.low
    if span <= 0 or size <= 0:
        return size, "large-cap alt: close-location haircut not triggered"
    location = (last.close - last.low) / span
    if location < 0.25:
        return size * 0.5, "large-cap alt close-location haircut"
    return size, "large-cap alt: close-location haircut not triggered"


def _stable(candles: list[Candle]) -> str:
    deviation = abs(candles[-1].close - 1.0)
    if deviation >= 0.002:
        return "stablecoin secondary peg watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _prior_median([candle.volume for candle in candles[-8:-1]])
    if base > 0 and candles[-1].volume < base * 0.3 and size > 0:
        return 0.0, "defi volume-collapse halt"
    return size, "defi: volume-collapse halt not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = last.high - last.low
    if span <= 0 or size <= 0:
        return size, "meme: upper-wick veto not triggered"
    wick = last.high - max(last.open, last.close)
    if wick / span > 0.60:
        return 0.0, "meme upper-wick veto"
    return size, "meme: upper-wick veto not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    def _range(candle: Candle) -> float:
        return (candle.high - candle.low) / candle.close if candle.close else 0.0

    base = _prior_median([_range(candle) for candle in candles[-8:-1]])
    last = _range(candles[-1])
    if base > 0 and last > base * 3.0 and size > 0:
        return size * 0.5, "l2 fee-spike proxy haircut"
    return size, "l2: fee-spike proxy haircut not triggered"


def _rwa(candles: list[Candle], size: float, side: Side) -> tuple[float, str]:
    if side is Side.LONG and size > 0 and candles[-1].close <= candles[-4].close:
        return 0.0, "rwa slow-confirmation veto"
    return size, "rwa: slow-confirmation veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _prior_median([candle.volume for candle in candles[-8:-1]])
    if base > 0 and candles[-1].volume > base * 3.0 and size > 0:
        return size * 0.5, "perp activity-spike haircut"
    return size, "perp: activity-spike haircut not triggered"


def schedule_manifest() -> dict[str, object]:
    """Declared cadence. This package does not poll an exchange."""
    return {
        "version": "0.8.0",
        "live_enabled": False,
        "network_default": False,
        "order_path": False,
        "cadence_minutes": dict(CADENCE_MINUTES),
        "runner": "external scheduler may invoke the CLI; no socket is opened here",
    }


def next_window(now_iso: str, asset_class: str) -> dict[str, object]:
    """Next declared information slot. Pure clock math, no network."""
    if asset_class not in CADENCE_MINUTES:
        raise ValueError(f"unknown asset class {asset_class}")
    stamp = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    minutes = CADENCE_MINUTES[asset_class]
    slot = (stamp.minute // minutes + 1) * minutes
    hour_add, minute = divmod(slot, 60)
    nxt = stamp.replace(minute=0, second=0, microsecond=0) + timedelta(hours=hour_add, minutes=minute)
    return {
        "asset_class": asset_class,
        "cadence_minutes": minutes,
        "next_iso": nxt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live_enabled": False,
        "order_path": False,
    }


def data_plane_report() -> dict[str, object]:
    """Defensive data-security architecture. Not a certification."""
    return {
        "version": "0.8.0",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "zones": list(ZONES),
        "data_classes": list(DATA_CLASSES),
        "refused_classes": list(REFUSED_CLASSES),
        "controls": [
            "classify before persist; personal data and seeds are refused",
            "encrypt research stores at rest with a key held outside this repository",
            "require TLS if a later deployment ever leaves the offline default",
            "hash-chain audit events after redaction",
            "egress allowlist remains market-read only",
            "dual control is required before any paper size cap can change",
            "retention clocks are class-specific; secrets have zero retention here",
        ],
        "crypto_expectation": "AES-256-GCM at rest and TLS in transit, keys outside git",
        "backup_scope": "synthetic fixtures and redacted audit only",
    }


def assert_data_class(name: str) -> str:
    """Refuse personal data, seeds, and trade credentials at the data plane."""
    normalized = name.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in REFUSED_CLASSES or any(token in normalized for token in ("seed", "nric", "wallet", "withdraw")):
        raise PermissionError("data class is refused on the information system")
    allowed = {str(row["name"]) for row in DATA_CLASSES}
    if normalized not in allowed:
        raise PermissionError("data class is outside the research allowlist")
    return normalized


def export_envelope(label: str, body: str) -> dict[str, object]:
    """Tamper-evident research export. Not a signature over an order."""
    if label not in {"SYNTHETIC", "PUBLIC_READ"}:
        raise ValueError("export requires a research label")
    digest = hashlib.sha256(f"{label}:{body}".encode()).hexdigest()
    return {
        "label": label,
        "digest": digest,
        "algorithm": "sha256",
        "live_enabled": False,
        "order_path": False,
    }
