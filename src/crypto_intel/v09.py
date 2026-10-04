"""Version 0.9 class guards, alert routing, and zero-trust research plane.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The security report is a defensive
control description, not a certification and not legal advice.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from crypto_intel.models import AssetClass, Candle, Side

GUARD_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "drawdown-cluster haircut after five negative closes",
    AssetClass.LARGE_CAP_ALT.value: "idiosyncratic gap veto above 6 percent",
    AssetClass.STABLECOIN.value: "tertiary peg watch; size stays zero",
    AssetClass.DEFI.value: "bar-range stress halt above 5 percent",
    AssetClass.MEME.value: "three-bar chase veto above 25 percent",
    AssetClass.L2.value: "benchmark-lag haircut above 4 percent",
    AssetClass.RWA.value: "stale-print veto when the last gap exceeds 36 hours",
    AssetClass.PERPETUAL.value: "extreme-funding veto above 20 bps absolute",
}

TRUST_ZONES = ("untrusted_input", "research", "control", "audit")

CONTROL_FAMILIES: tuple[dict[str, str], ...] = (
    {"family": "identify", "control": "classify inputs before they enter research"},
    {"family": "protect", "control": "no secrets in git; market-read scope only; no execution zone"},
    {"family": "detect", "control": "hash-chained audit, source attestation, class alert router"},
    {"family": "respond", "control": "research halt and dual-control clear; cannot enable live trading"},
    {"family": "recover", "control": "restore from synthetic fixtures and redacted audit only"},
)

SEVERITY = ("info", "watch", "research_halt")


def apply_v09(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
    benchmark: list[Candle] | None = None,
) -> dict[str, object]:
    """Fifth-pass research guard. Size cannot increase."""
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
        size, note = _l2(candles, size, benchmark)
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
    window = candles[-5:]
    falling = all(window[index].close < window[index - 1].close for index in range(1, len(window)))
    if falling and size > 0:
        return size * 0.5, "major drawdown-cluster haircut"
    return size, "major: drawdown-cluster haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    if previous <= 0 or size <= 0:
        return size, "large-cap alt: idiosyncratic gap veto not triggered"
    gap = abs(candles[-1].open - previous) / previous
    if gap > 0.06:
        return 0.0, "large-cap alt idiosyncratic gap veto"
    return size, "large-cap alt: idiosyncratic gap veto not triggered"


def _stable(candles: list[Candle]) -> str:
    deviation = abs(candles[-1].close - 1.0)
    if deviation >= 0.001:
        return "stablecoin tertiary peg watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    if last.close <= 0 or size <= 0:
        return size, "defi: bar-range stress halt not triggered"
    span = (last.high - last.low) / last.close
    if span > 0.05:
        return 0.0, "defi bar-range stress halt"
    return size, "defi: bar-range stress halt not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    start = candles[-4].close
    if start <= 0 or size <= 0:
        return size, "meme: chase veto not triggered"
    move = candles[-1].close / start - 1.0
    rising = candles[-1].close > candles[-2].close > candles[-3].close
    if rising and move > 0.25:
        return 0.0, "meme three-bar chase veto"
    return size, "meme: chase veto not triggered"


def _l2(candles: list[Candle], size: float, benchmark: list[Candle] | None) -> tuple[float, str]:
    if benchmark is None or len(benchmark) < 6 or size <= 0:
        return size, "l2: benchmark-lag haircut not triggered"
    if candles[-6].close <= 0 or benchmark[-6].close <= 0:
        return size, "l2: benchmark-lag haircut not triggered"
    own = candles[-1].close / candles[-6].close - 1.0
    bench = benchmark[-1].close / benchmark[-6].close - 1.0
    if own < bench - 0.04:
        return size * 0.5, "l2 benchmark-lag haircut"
    return size, "l2: benchmark-lag haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    if size <= 0:
        return size, "rwa: stale-print veto not triggered"
    gap = _hours_between(candles[-2].timestamp, candles[-1].timestamp)
    if gap > 36:
        return 0.0, "rwa stale-print veto"
    return size, "rwa: stale-print veto not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    if size > 0 and abs(candles[-1].funding_rate) > 0.002:
        return 0.0, "perp extreme-funding veto"
    return size, "perp: extreme-funding veto not triggered"


def _hours_between(start: str, end: str) -> float:
    left = _parse(start)
    right = _parse(end)
    return (right - left).total_seconds() / 3600.0


def _parse(stamp: str) -> datetime:
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def route_alert(asset_class: str, *, deviation: float = 0.0, stress: bool = False) -> dict[str, object]:
    """Information alert. Never an order instruction."""
    if asset_class not in GUARD_NOTES:
        raise ValueError(f"unknown asset class {asset_class}")
    if asset_class == AssetClass.STABLECOIN.value and deviation >= 0.005:
        severity = "research_halt"
        message = "stablecoin depeg watch for the research book"
    elif stress:
        severity = "watch"
        message = "class stress; directional research stands aside"
    elif asset_class == AssetClass.STABLECOIN.value and deviation >= 0.001:
        severity = "watch"
        message = "stablecoin tertiary peg watch"
    else:
        severity = "info"
        message = "class within declared research bands"
    return {
        "asset_class": asset_class,
        "severity": severity,
        "message": message,
        "order_instruction": False,
        "live_enabled": False,
        "order_path": False,
    }


def zero_trust_report() -> dict[str, object]:
    """Defensive cyber and data-security architecture for the research plane."""
    return {
        "version": "0.9.0",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "trust_zones": list(TRUST_ZONES),
        "control_families": list(CONTROL_FAMILIES),
        "principles": [
            "treat every fixture and feed as untrusted until attested",
            "least privilege: researcher can scan, nobody can place an order",
            "secrets, seeds, and personal data are refused and have zero retention",
            "parameter changes require a new catalog digest and two acknowledgements",
            "break-glass cannot enable live trading or a withdrawal path",
            "backups cover synthetic fixtures and redacted audit only",
        ],
        "crypto_expectation": "AES-256-GCM at rest and TLS in transit, keys outside git",
        "residency": "research fixtures only; no personal data; PDPA tripwire remains a tripwire, not legal advice",
        "severity_levels": list(SEVERITY),
    }


def acknowledge_change(digest: str, *, first: str, second: str) -> dict[str, object]:
    """Dual acknowledgement of a research-parameter digest. Cannot enable live trading."""
    if not digest or len(digest) < 16:
        raise ValueError("digest is required")
    if not first or not second or first == second:
        raise PermissionError("two distinct acknowledgements are required")
    token = hashlib.sha256(f"{digest}:{first}:{second}".encode()).hexdigest()
    return {
        "digest": digest,
        "acknowledged": True,
        "token": token,
        "live_enabled": False,
        "order_path": False,
        "can_enable_live": False,
    }


def research_cycle(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline information cycle. Summarises already-scored rows. No network."""
    alerts = []
    for row in rows:
        asset_class = str(row.get("asset_class", ""))
        if asset_class not in GUARD_NOTES:
            continue
        alerts.append(
            route_alert(
                asset_class,
                deviation=float(row.get("deviation", 0.0)),
                stress=bool(row.get("stress", False)),
            )
        )
    halts = [item for item in alerts if item["severity"] == "research_halt"]
    return {
        "version": "0.9.0",
        "rows": len(rows),
        "alerts": alerts,
        "research_halt": bool(halts),
        "live_enabled": False,
        "order_path": False,
        "network_default": False,
    }
