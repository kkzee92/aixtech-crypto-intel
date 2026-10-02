"""Second-check confirmation overlay, one rule per asset class.

A failed confirmation vetoes a directional paper idea. Alerts and flats are
left unchanged. This is a research control, not a forecast.
"""

from __future__ import annotations

from statistics import fmean

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify


def _ema(values: list[float], span: int) -> float:
    alpha = 2.0 / (span + 1)
    value = values[0]
    for point in values[1:]:
        value = alpha * point + (1.0 - alpha) * value
    return value


def confirm(
    candles: list[Candle],
    signal: Signal,
    benchmark: list[Candle] | None = None,
) -> tuple[bool, str]:
    if signal.side in {Side.FLAT, Side.ALERT}:
        return True, "no directional idea to confirm"
    asset_class = signal.asset_class
    if classify(candles) is Regime.STRESS and asset_class is not AssetClass.PERPETUAL:
        return False, "confirmation veto: stress regime"
    closes = [candle.close for candle in candles]
    if asset_class is AssetClass.MAJOR:
        return _major(closes)
    if asset_class is AssetClass.LARGE_CAP_ALT:
        return _volume(candles, "large-cap breakout")
    if asset_class is AssetClass.DEFI:
        return _defi(closes)
    if asset_class is AssetClass.MEME:
        return _meme(closes)
    if asset_class is AssetClass.L2:
        return _l2(closes, benchmark)
    if asset_class is AssetClass.RWA:
        return _rwa(candles)
    if asset_class is AssetClass.PERPETUAL:
        return _perpetual(candles, signal.side)
    return False, "confirmation veto: stablecoins do not take directional risk"


def _major(closes: list[float]) -> tuple[bool, str]:
    if closes[-1] > _ema(closes, 8):
        return True, "major confirmation: close above 8-bar EMA"
    return False, "confirmation veto: major lost the 8-bar EMA"


def _volume(candles: list[Candle], label: str) -> tuple[bool, str]:
    base = fmean(candle.volume for candle in candles[-6:-1])
    if base <= 0:
        return False, f"confirmation veto: {label} has no volume base"
    if candles[-1].volume >= base:
        return True, f"{label} confirmation: volume still at or above the base"
    return False, f"confirmation veto: {label} volume faded"


def _defi(closes: list[float]) -> tuple[bool, str]:
    realised = fmean(abs(closes[index] / closes[index - 1] - 1.0) for index in range(-7, 0))
    if realised <= 0.06 and closes[-1] > _ema(closes, 8):
        return True, "defi confirmation: calm trend still intact"
    return False, "confirmation veto: defi vol or trend failed"


def _meme(closes: list[float]) -> tuple[bool, str]:
    extension = closes[-1] / closes[-8] - 1.0
    if extension <= 0.40:
        return True, "meme confirmation: extension still inside the chase filter"
    return False, "confirmation veto: meme chase extension"


def _l2(closes: list[float], benchmark: list[Candle] | None) -> tuple[bool, str]:
    if not benchmark or len(benchmark) < 8:
        return False, "confirmation veto: l2 benchmark missing"
    if classify(benchmark) is Regime.STRESS:
        return False, "confirmation veto: l2 benchmark in stress"
    bench = [candle.close for candle in benchmark]
    excess = (closes[-1] / closes[-6] - 1.0) - (bench[-1] / bench[-6] - 1.0)
    if excess > 0.0:
        return True, "l2 confirmation: excess return still positive"
    return False, "confirmation veto: l2 no longer leading"


def _rwa(candles: list[Candle]) -> tuple[bool, str]:
    gap = candles[-1].open / candles[-2].close - 1.0
    if abs(gap) <= 0.08:
        return True, "rwa confirmation: gap inside halt band"
    return False, "confirmation veto: rwa gap halt"


def _perpetual(candles: list[Candle], side: Side) -> tuple[bool, str]:
    funding = candles[-1].funding_rate
    if side is Side.SHORT and funding >= 0.001:
        return True, "perp confirmation: crowded funding still present"
    if side is Side.LONG and funding <= -0.0005:
        return True, "perp confirmation: negative funding still present"
    return False, "confirmation veto: perp funding no longer supports the idea"
