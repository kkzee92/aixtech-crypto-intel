"""Per-asset-class research enhancements.

Each rule can shrink or refuse a paper size. None can raise a class cap, open
a socket, or place an order. Parameters live in the catalog overlays.
"""

from __future__ import annotations

from statistics import fmean, median

from crypto_intel.catalog import OVERLAYS
from crypto_intel.models import AssetClass, Candle, Side

_RULES = OVERLAYS["class_enhance"]


def _returns(closes: list[float]) -> list[float]:
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]


def apply_class_enhancement(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
    benchmark: list[Candle] | None = None,
) -> dict[str, object]:
    """Second-pass research rule for the series asset class."""
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    size = proposed_size if side in {Side.LONG, Side.SHORT} else 0.0
    note = "class enhancement: unchanged"
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
    size = min(size, proposed_size)
    return {
        "symbol": candles[-1].symbol,
        "asset_class": asset_class.value,
        "side": side.value if size > 0 else Side.FLAT.value,
        "size_fraction": round(max(size, 0.0), 6),
        "note": note,
        "live_enabled": False,
        "can_increase_size": False,
    }


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [c.close for c in candles]
    realised = fmean(abs(v) for v in _returns(closes[-14:]))
    ceiling = float(_RULES["major_vol_dampen"])
    if realised > ceiling and size > 0:
        return size * 0.5, f"major vol dampener: realised {realised:.4f} above {ceiling:.4f}"
    return size, "major: vol dampener not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    volumes = [c.volume for c in candles[-4:]]
    if volumes[-1] < volumes[-2] < volumes[-3] and size > 0:
        return 0.0, "large-cap alt: three-bar volume fade veto"
    return size, "large-cap alt: volume fade not triggered"


def _stable(candles: list[Candle]) -> str:
    outside = sum(abs(c.close - 1.0) >= 0.002 for c in candles[-2:])
    if outside == 2:
        return "stablecoin: consecutive peg watches, size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    bar_range = (last.high - last.low) / last.close if last.close else 0.0
    halt = float(_RULES["defi_bar_range_halt"])
    if bar_range > halt and size > 0:
        return 0.0, f"defi bar-range halt: {bar_range:.4f} above {halt:.4f}"
    return size, "defi: bar-range halt not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    volumes = [c.volume for c in candles[-8:]]
    base = median(volumes[:-1]) or 1.0
    multiple = float(_RULES["meme_impact_multiple"])
    if volumes[-1] > base * multiple and size > 0:
        return size * 0.5, "meme impact haircut: last volume above 5x median"
    return size, "meme: impact haircut not triggered"


def _l2(candles: list[Candle], size: float, benchmark: list[Candle] | None) -> tuple[float, str]:
    if not benchmark or len(benchmark) < 8:
        return 0.0, "l2 enhancement: missing benchmark"
    own = candles[-1].close / candles[-6].close - 1.0
    bench = benchmark[-1].close / benchmark[-6].close - 1.0
    lag = float(_RULES["l2_lag_veto"])
    if own - bench < -lag and size > 0:
        return 0.0, "l2 lag veto: trailing benchmark"
    return size, "l2: lag veto not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    drift = candles[-1].close / candles[-10].close - 1.0 if len(candles) >= 10 else 0.0
    ceiling = float(_RULES["rwa_fast_drift"])
    if abs(drift) > ceiling and size > 0:
        return 0.0, "rwa fast-drift invalidation: too quick for a slow sleeve"
    return size, "rwa: fast-drift invalidation not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    funding = abs(candles[-1].funding_rate)
    halt = float(_RULES["perp_funding_halt"])
    if funding >= halt and size > 0:
        return 0.0, "perp extreme-funding halt: liquidation risk proxy"
    return size, "perp: extreme-funding halt not triggered"
