"""Version 0.10 class microstructure guards and cyber architecture.

Sixth research pass. Guards can shrink or refuse a paper size. They cannot
raise a class cap, open a socket, store a secret, or place an order. The
architecture report is a defensive control description, not a certification
and not legal advice.
"""

from __future__ import annotations

import hashlib
import json
from statistics import fmean, median

from crypto_intel.models import AssetClass, Candle, Side

PASS_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "session-liquidity haircut when volume is under half the 8-bar median",
    AssetClass.LARGE_CAP_ALT.value: "wash-print veto when volume doubles but the bar range is under 0.4 percent",
    AssetClass.STABLECOIN.value: "peg-persistence watch across three closes; size stays zero",
    AssetClass.DEFI.value: "liquidity-cliff haircut when volume falls 60 percent bar over bar",
    AssetClass.MEME.value: "wick-rejection veto when the close is in the bottom 40 percent of the bar",
    AssetClass.L2.value: "fee-spike proxy haircut when bar range exceeds 3.5 percent",
    AssetClass.RWA.value: "NAV-gap halt when the open gaps more than 3 percent from the prior close",
    AssetClass.PERPETUAL.value: "basis-blowout veto when six-bar absolute drift exceeds 6 percent",
}

CLASS_DATA_POLICY: dict[str, dict[str, str]] = {
    AssetClass.MAJOR.value: {
        "fields": "ohlcv, public ticker",
        "integrity": "monotonic timestamps, jump check, volume floor",
        "retention": "synthetic fixture or redacted research session",
    },
    AssetClass.LARGE_CAP_ALT.value: {
        "fields": "ohlcv",
        "integrity": "volume-range consistency; reject wash-like prints",
        "retention": "synthetic fixture or redacted research session",
    },
    AssetClass.STABLECOIN.value: {
        "fields": "peg close only",
        "integrity": "three-print persistence before a research watch",
        "retention": "alert text only; no account identifiers",
    },
    AssetClass.DEFI.value: {
        "fields": "ohlcv",
        "integrity": "volume cliff and bar-range checks",
        "retention": "synthetic fixture or redacted research session",
    },
    AssetClass.MEME.value: {
        "fields": "ohlcv",
        "integrity": "close location and liquidity floor",
        "retention": "synthetic fixture; no social handles",
    },
    AssetClass.L2.value: {
        "fields": "ohlcv plus benchmark series",
        "integrity": "benchmark required; range proxy for fee stress",
        "retention": "synthetic fixture or redacted research session",
    },
    AssetClass.RWA.value: {
        "fields": "ohlcv",
        "integrity": "NAV-style open gap halt",
        "retention": "synthetic fixture; no holder registry",
    },
    AssetClass.PERPETUAL.value: {
        "fields": "ohlcv, public funding rate",
        "integrity": "drift containment before any carry observation",
        "retention": "research feature only; no position or margin account",
    },
}

CYBER_CONTROLS: tuple[dict[str, str], ...] = (
    {"control": "paper-only mode", "objective": "no live order path exists in this process"},
    {"control": "credential purpose binding", "objective": "trade, withdraw, and transfer names are refused"},
    {"control": "default-deny egress", "objective": "network fetch is injected in tests and unused by default"},
    {"control": "class data policy", "objective": "each asset class declares fields, integrity, and retention"},
    {"control": "evidence digest", "objective": "policy text is hashed so a silent edit changes the digest"},
    {"control": "size monotonicity", "objective": "this pass cannot increase a proposed paper size"},
)


def apply_v10(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
    benchmark: list[Candle] | None = None,
) -> dict[str, object]:
    """Sixth-pass research guard. Size cannot increase."""
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
        "guard": PASS_NOTES[asset_class.value],
        "data_policy": CLASS_DATA_POLICY[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    volumes = [candle.volume for candle in candles[-8:]]
    baseline = median(volumes)
    if size > 0 and baseline > 0 and candles[-1].volume < baseline * 0.5:
        return size * 0.5, "major session-liquidity haircut"
    return size, "major: session-liquidity haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    baseline = fmean(candle.volume for candle in candles[-6:-1])
    span = (last.high - last.low) / last.close if last.close else 0.0
    if size > 0 and baseline > 0 and last.volume > baseline * 2.0 and span < 0.004:
        return 0.0, "large-cap alt wash-print veto"
    return size, "large-cap alt: wash-print veto not triggered"


def _stable(candles: list[Candle]) -> str:
    deviations = [abs(candle.close - 1.0) for candle in candles[-3:]]
    if all(deviation >= 0.0015 for deviation in deviations):
        return "stablecoin peg-persistence watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].volume
    if size > 0 and previous > 0 and candles[-1].volume < previous * 0.4:
        return size * 0.5, "defi liquidity-cliff haircut"
    return size, "defi: liquidity-cliff haircut not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = last.high - last.low
    if size > 0 and span > 0 and (last.close - last.low) / span < 0.4:
        return 0.0, "meme wick-rejection veto"
    return size, "meme: wick-rejection veto not triggered"


def _l2(candles: list[Candle], size: float, benchmark: list[Candle] | None) -> tuple[float, str]:
    if not benchmark or len(benchmark) < 8:
        return 0.0, "l2 fee-spike pass requires a benchmark series"
    last = candles[-1]
    span = (last.high - last.low) / last.close if last.close else 0.0
    if size > 0 and span > 0.035:
        return size * 0.5, "l2 fee-spike proxy haircut"
    return size, "l2: fee-spike proxy haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].close
    if previous <= 0 or size <= 0:
        return size, "rwa: NAV-gap halt not triggered"
    gap = abs(candles[-1].open / previous - 1.0)
    if gap > 0.03:
        return 0.0, "rwa NAV-gap halt"
    return size, "rwa: NAV-gap halt not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    start = candles[-6].close
    if start <= 0 or size <= 0:
        return size, "perp: basis-blowout veto not triggered"
    drift = abs(candles[-1].close / start - 1.0)
    if drift > 0.06:
        return 0.0, "perp basis-blowout veto"
    return size, "perp: basis-blowout veto not triggered"


def evidence_digest() -> str:
    material = json.dumps(
        {"policies": CLASS_DATA_POLICY, "controls": list(CYBER_CONTROLS), "passes": PASS_NOTES},
        sort_keys=True,
    ).encode()
    return hashlib.sha256(material).hexdigest()


def cyber_architecture_report() -> dict[str, object]:
    """Defensive architecture snapshot. Cannot enable live trading."""
    return {
        "version": "0.10",
        "mode": "paper",
        "live_enabled": False,
        "execution_zone": False,
        "egress": "default-deny; fetchers are injected",
        "zones": ("untrusted_input", "research", "control", "audit", "evidence"),
        "class_data_policy": CLASS_DATA_POLICY,
        "controls": list(CYBER_CONTROLS),
        "evidence_digest": evidence_digest(),
        "order_path": False,
    }


def information_cycle(rows: list[dict[str, object]]) -> dict[str, object]:
    """Route class research notes. Alerts are not orders."""
    watches = [row for row in rows if "watch" in str(row.get("note", "")) or "veto" in str(row.get("note", ""))]
    return {
        "mode": "paper",
        "rows": len(rows),
        "watches": len(watches),
        "live_enabled": False,
        "order_path": False,
        "evidence_digest": evidence_digest(),
    }
