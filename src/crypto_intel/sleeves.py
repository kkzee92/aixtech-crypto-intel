"""Version 0.7 asset-class sleeves.

Each sleeve can shrink or refuse a paper size. None can raise a class cap,
open a socket, or place an order. Stablecoins stay at zero size.
"""

from __future__ import annotations

from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

SLEEVE_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "ATR expansion haircut when the last bar range exceeds 2x the prior median",
    AssetClass.LARGE_CAP_ALT.value: "relative-lag veto versus a benchmark of more than 2 percent",
    AssetClass.STABLECOIN.value: "peg-dispersion watch from bar range; size stays zero",
    AssetClass.DEFI.value: "protocol-gap halt when the open gaps more than 5 percent",
    AssetClass.MEME.value: "volume-decay haircut after a burst loses half its recent peak",
    AssetClass.L2.value: "sequencer-gap proxy veto above a 4 percent open gap",
    AssetClass.RWA.value: "stale-print haircut when the last three closes are identical",
    AssetClass.PERPETUAL.value: "funding-sign flip veto; carry is invalid if funding flips",
}


def apply_sleeve(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
    benchmark: list[Candle] | None = None,
) -> dict[str, object]:
    """Third-pass research sleeve. Size cannot increase."""
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    size = proposed_size if side in {Side.LONG, Side.SHORT} else 0.0
    if asset_class is AssetClass.MAJOR:
        size, note = _major(candles, size)
    elif asset_class is AssetClass.LARGE_CAP_ALT:
        size, note = _alt(candles, size, benchmark)
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
        "sleeve": SLEEVE_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
    }


def _range_pct(candle: Candle) -> float:
    if not candle.close:
        return 0.0
    return (candle.high - candle.low) / candle.close


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    prior = [_range_pct(candle) for candle in candles[-8:-1]]
    base = median(prior) or 0.0
    last = _range_pct(candles[-1])
    if base > 0 and last > base * 2.0 and size > 0:
        return size * 0.5, "major ATR expansion haircut"
    return size, "major: ATR expansion not triggered"


def _alt(candles: list[Candle], size: float, benchmark: list[Candle] | None) -> tuple[float, str]:
    if not benchmark or len(benchmark) < 8:
        return 0.0, "large-cap alt sleeve: missing benchmark"
    own = candles[-1].close / candles[-6].close - 1.0
    bench = benchmark[-1].close / benchmark[-6].close - 1.0
    if own - bench < -0.02 and size > 0:
        return 0.0, "large-cap alt relative-lag veto"
    return size, "large-cap alt: relative-lag veto not triggered"


def _stable(candles: list[Candle]) -> str:
    last = candles[-1]
    dispersion = _range_pct(last)
    if dispersion >= 0.004:
        return "stablecoin peg-dispersion watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    gap = candles[-1].open / candles[-2].close - 1.0
    if abs(gap) > 0.05 and size > 0:
        return 0.0, "defi protocol-gap halt"
    return size, "defi: protocol-gap halt not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    peak = max(candle.volume for candle in candles[-4:-1])
    if peak > 0 and candles[-1].volume < peak * 0.5 and size > 0:
        return size * 0.5, "meme volume-decay haircut"
    return size, "meme: volume-decay haircut not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    gap = candles[-1].open / candles[-2].close - 1.0
    if abs(gap) > 0.04 and size > 0:
        return 0.0, "l2 sequencer-gap proxy veto"
    return size, "l2: sequencer-gap proxy not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [candle.close for candle in candles[-3:]]
    if closes[0] == closes[1] == closes[2] and size > 0:
        return size * 0.5, "rwa stale-print haircut"
    return size, "rwa: stale-print haircut not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    previous = candles[-2].funding_rate
    current = candles[-1].funding_rate
    flipped = previous * current < 0
    if flipped and size > 0:
        return 0.0, "perp funding-sign flip veto"
    return size, "perp: funding-sign flip not triggered"
