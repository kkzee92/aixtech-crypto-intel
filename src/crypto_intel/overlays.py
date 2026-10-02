"""v0.5 class-specific research overlays.

These overlays sit on top of the v0.4 primary rule. They can flatten a
directional idea or leave it unchanged. They cannot raise a size cap and they
cannot create a live order.
"""

from __future__ import annotations

from statistics import fmean

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify

ENHANCEMENTS: dict[AssetClass, str] = {
    AssetClass.MAJOR: "Trend needs close above the slow EMA and a non-negative five-bar slope.",
    AssetClass.LARGE_CAP_ALT: "Breakout is flattened when the benchmark regime is stress.",
    AssetClass.STABLECOIN: "A depeg with a volume spike raises alert confidence. Size stays zero.",
    AssetClass.DEFI: "A rising close on falling volume is treated as weak participation.",
    AssetClass.MEME: "A bar range above 25% of close is a wick filter, not an entry.",
    AssetClass.L2: "Relative strength also needs volume at or above its five-bar mean.",
    AssetClass.RWA: "Slow trend is flattened if five-bar mean absolute return exceeds 2.5%.",
    AssetClass.PERPETUAL: "Carry and fade are flattened when 14-bar range exceeds 6% of price.",
}


def _mean_volume(candles: list[Candle]) -> float:
    window = candles[-6:-1]
    return fmean(c.volume for c in window) if window else 0.0


def _flatten(signal: Signal, reason: str) -> Signal:
    return Signal(
        symbol=signal.symbol,
        asset_class=signal.asset_class,
        side=Side.FLAT if signal.side in {Side.LONG, Side.SHORT} else signal.side,
        confidence=signal.confidence,
        reason=f"{signal.reason}; v0.5 {reason}",
        stop_distance_pct=signal.stop_distance_pct,
        size_fraction=0.0,
        horizon_bars=1,
    )


def apply_class_enhancement(
    candles: list[Candle],
    signal: Signal,
    benchmark: list[Candle] | None = None,
) -> Signal:
    """Apply the v0.5 overlay. Directional size never increases."""
    if signal.side not in {Side.LONG, Side.SHORT, Side.ALERT}:
        return signal
    closes = [c.close for c in candles]
    asset_class = signal.asset_class
    if asset_class is AssetClass.MAJOR and signal.side is Side.LONG:
        slow = fmean(closes[-13:]) if len(closes) >= 13 else fmean(closes)
        slope = closes[-1] / closes[-5] - 1.0 if len(closes) >= 5 else 0.0
        if closes[-1] <= slow or slope < 0:
            return _flatten(signal, "major agreement filter: close or slope failed")
    if asset_class is AssetClass.LARGE_CAP_ALT and signal.side is Side.LONG:
        if benchmark and classify(benchmark) is Regime.STRESS:
            return _flatten(signal, "large-cap breakout blocked by benchmark stress")
    if asset_class is AssetClass.STABLECOIN and signal.side is Side.ALERT:
        base = _mean_volume(candles)
        deviation = abs(candles[-1].close - 1.0)
        if deviation >= 0.005 and base and candles[-1].volume >= base * 2:
            return Signal(
                symbol=signal.symbol,
                asset_class=signal.asset_class,
                side=Side.ALERT,
                confidence=min(0.97, round(signal.confidence + 0.05, 4)),
                reason=f"{signal.reason}; v0.5 depeg volume confirmation",
                stop_distance_pct=signal.stop_distance_pct,
                size_fraction=0.0,
                horizon_bars=signal.horizon_bars,
            )
        return signal
    if asset_class is AssetClass.DEFI and signal.side is Side.LONG:
        base = _mean_volume(candles)
        if base and candles[-1].volume < base * 0.8 and closes[-1] > closes[-2]:
            return _flatten(signal, "defi participation filter: rising price, falling volume")
    if asset_class is AssetClass.MEME and signal.side is Side.LONG:
        last = candles[-1]
        if last.close and (last.high - last.low) / last.close > 0.25:
            return _flatten(signal, "meme wick filter: bar range above 25%")
    if asset_class is AssetClass.L2 and signal.side is Side.LONG:
        base = _mean_volume(candles)
        if base and candles[-1].volume < base:
            return _flatten(signal, "l2 volume confirmation missing")
    if asset_class is AssetClass.RWA and signal.side is Side.LONG:
        window = closes[-6:]
        realised = fmean(abs(window[i] / window[i - 1] - 1.0) for i in range(1, len(window)))
        if realised > 0.025:
            return _flatten(signal, "rwa realised-vol filter")
    if asset_class is AssetClass.PERPETUAL and signal.side in {Side.LONG, Side.SHORT}:
        ranges = [(c.high - c.low) / c.close for c in candles[-14:] if c.close]
        if ranges and fmean(ranges) > 0.06:
            return _flatten(signal, "perp range filter: basis proxy unstable")
    return signal
