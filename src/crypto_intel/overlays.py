"""Version 0.8 per-class research overlays.

Each overlay can shrink or refuse a paper size. None can raise a class cap,
open a socket, or place an order. Stablecoins stay at zero size.
"""

from __future__ import annotations

from statistics import fmean

from crypto_intel.models import AssetClass, Candle, Side

OVERLAY_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "weak-close haircut when the close is in the bottom quarter of the bar",
    AssetClass.LARGE_CAP_ALT.value: "upper-wick veto when the wick is more than 60 percent of the range",
    AssetClass.STABLECOIN.value: "three-bar peg-persistence watch; size stays zero",
    AssetClass.DEFI.value: "liquidity-drain haircut when volume is below 40 percent of the recent mean",
    AssetClass.MEME.value: "wick-rejection veto when the upper wick is more than half the range",
    AssetClass.L2.value: "benchmark-divergence veto when six-bar excess return is below -5 percent",
    AssetClass.RWA.value: "intrabar divergence haircut when open-to-close exceeds 3 percent",
    AssetClass.PERPETUAL.value: "crowded-funding veto when absolute funding is at least 15 bps",
}


def apply_overlay(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
    benchmark: list[Candle] | None = None,
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
        "overlay": OVERLAY_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
    }


def _bar_range(candle: Candle) -> float:
    return candle.high - candle.low


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = _bar_range(last)
    if span <= 0 or size <= 0:
        return size, "major: weak-close haircut not triggered"
    location = (last.close - last.low) / span
    if location < 0.25:
        return size * 0.5, "major weak-close haircut"
    return size, "major: weak-close haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = _bar_range(last)
    if span <= 0 or size <= 0:
        return size, "large-cap alt: upper-wick veto not triggered"
    wick = last.high - max(last.open, last.close)
    if wick / span > 0.60:
        return 0.0, "large-cap alt upper-wick veto"
    return size, "large-cap alt: upper-wick veto not triggered"


def _stable(candles: list[Candle]) -> str:
    outside = sum(abs(candle.close - 1.0) >= 0.002 for candle in candles[-3:])
    if outside >= 3:
        return "stablecoin three-bar peg-persistence watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    base = fmean(candle.volume for candle in candles[-6:-1])
    if base > 0 and candles[-1].volume < base * 0.40 and size > 0:
        return size * 0.5, "defi liquidity-drain haircut"
    return size, "defi: liquidity-drain haircut not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = _bar_range(last)
    if span <= 0 or size <= 0:
        return size, "meme: wick-rejection veto not triggered"
    wick = last.high - max(last.open, last.close)
    if wick / span > 0.50:
        return 0.0, "meme wick-rejection veto"
    return size, "meme: wick-rejection veto not triggered"


def _l2(candles: list[Candle], size: float, benchmark: list[Candle] | None) -> tuple[float, str]:
    if not benchmark or len(benchmark) < 8:
        return 0.0, "l2 overlay: missing benchmark"
    own = candles[-1].close / candles[-6].close - 1.0
    bench = benchmark[-1].close / benchmark[-6].close - 1.0
    if own - bench < -0.05 and size > 0:
        return 0.0, "l2 benchmark-divergence veto"
    return size, "l2: benchmark-divergence veto not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    if not last.close or size <= 0:
        return size, "rwa: intrabar divergence haircut not triggered"
    divergence = abs(last.close - last.open) / last.close
    if divergence > 0.03:
        return size * 0.5, "rwa intrabar divergence haircut"
    return size, "rwa: intrabar divergence haircut not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    if abs(candles[-1].funding_rate) >= 0.0015 and size > 0:
        return 0.0, "perp crowded-funding veto"
    return size, "perp: crowded-funding veto not triggered"
