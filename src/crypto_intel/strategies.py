"""Asset-class strategy research rules.

These are transparent heuristics for paper research. They are not forecasts
and not a recommendation to trade.
"""

from __future__ import annotations

from statistics import fmean

from crypto_intel.models import AssetClass, Candle, Side, Signal


def _returns(closes: list[float]) -> list[float]:
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]


def _ema(values: list[float], span: int) -> float:
    alpha = 2.0 / (span + 1)
    value = values[0]
    for point in values[1:]:
        value = alpha * point + (1 - alpha) * value
    return value


def _rsi(closes: list[float], period: int = 14) -> float:
    changes = _returns(closes[-(period + 1) :])
    gains = [max(change, 0.0) for change in changes]
    losses = [abs(min(change, 0.0)) for change in changes]
    average_loss = fmean(losses) if losses else 0.0
    if average_loss == 0:
        return 100.0
    rs = fmean(gains) / average_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _atr_pct(candles: list[Candle]) -> float:
    ranges = [(c.high - c.low) / c.close for c in candles[-14:] if c.close]
    return fmean(ranges) if ranges else 0.0


def _base(candles: list[Candle], side: Side, confidence: float, reason: str, size: float, bars: int) -> Signal:
    last = candles[-1]
    return Signal(
        symbol=last.symbol,
        asset_class=last.asset_class,
        side=side,
        confidence=round(max(0.0, min(confidence, 1.0)), 4),
        reason=reason,
        stop_distance_pct=round(max(_atr_pct(candles) * 1.5, 0.01), 4),
        size_fraction=size,
        horizon_bars=bars,
    )


def signal_for(candles: list[Candle], benchmark: list[Candle] | None = None) -> Signal:
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    closes = [c.close for c in candles]
    if asset_class is AssetClass.MAJOR:
        return _major(candles, closes)
    if asset_class is AssetClass.LARGE_CAP_ALT:
        return _breakout(candles, closes, size=0.04, bars=12)
    if asset_class is AssetClass.STABLECOIN:
        return _stable(candles)
    if asset_class is AssetClass.DEFI:
        return _defi(candles, closes)
    if asset_class is AssetClass.MEME:
        return _meme(candles, closes)
    if asset_class is AssetClass.L2:
        return _l2(candles, closes, benchmark)
    if asset_class is AssetClass.RWA:
        return _rwa(candles, closes)
    return _perpetual(candles, closes)


def _major(candles: list[Candle], closes: list[float]) -> Signal:
    fast, slow = _ema(closes, 5), _ema(closes, 13)
    rsi = _rsi(closes)
    if fast > slow and 45 <= rsi <= 70:
        return _base(candles, Side.LONG, 0.72, "major trend: fast EMA above slow, RSI not stretched", 0.06, 20)
    if rsi < 30 and closes[-1] > closes[-3]:
        return _base(candles, Side.LONG, 0.6, "major mean-reversion: washed-out RSI stabilising", 0.03, 8)
    return _base(candles, Side.FLAT, 0.4, "major: no trend or reversion edge", 0.0, 1)


def _breakout(candles: list[Candle], closes: list[float], size: float, bars: int) -> Signal:
    window = closes[-6:-1]
    volume_now = candles[-1].volume
    volume_base = fmean(c.volume for c in candles[-6:-1])
    if closes[-1] > max(window) and volume_now > volume_base * 1.2:
        return _base(candles, Side.LONG, 0.7, "breakout with volume confirmation", size, bars)
    return _base(candles, Side.FLAT, 0.35, "no confirmed breakout", 0.0, 1)


def _stable(candles: list[Candle]) -> Signal:
    deviation = abs(candles[-1].close - 1.0)
    if deviation >= 0.005:
        return _base(candles, Side.ALERT, 0.9, f"stablecoin depeg monitor: deviation {deviation:.4f}", 0.0, 1)
    return _base(candles, Side.FLAT, 0.8, "stablecoin inside peg band", 0.0, 1)


def _defi(candles: list[Candle], closes: list[float]) -> Signal:
    realised = fmean(abs(v) for v in _returns(closes[-8:]))
    if realised > 0.06:
        return _base(candles, Side.FLAT, 0.45, "defi volatility regime: stand aside", 0.0, 1)
    if closes[-1] > _ema(closes, 8):
        return _base(candles, Side.LONG, 0.68, "defi trend in calm regime", 0.02, 10)
    return _base(candles, Side.FLAT, 0.4, "defi: no calm trend", 0.0, 1)


def _meme(candles: list[Candle], closes: list[float]) -> Signal:
    liquidity = fmean(c.volume for c in candles[-5:])
    burst = closes[-1] / closes[-4] - 1.0
    if liquidity < 1000:
        return _base(candles, Side.FLAT, 0.2, "meme liquidity proxy too thin", 0.0, 1)
    if burst > 0.15 and candles[-1].volume > candles[-2].volume:
        return _base(candles, Side.LONG, 0.78, "meme momentum burst; hard time stop applies", 0.005, 3)
    return _base(candles, Side.FLAT, 0.3, "meme: no qualified burst", 0.0, 1)


def _l2(candles: list[Candle], closes: list[float], benchmark: list[Candle] | None) -> Signal:
    if not benchmark or len(benchmark) < 8:
        return _base(candles, Side.FLAT, 0.3, "l2 requires a benchmark series", 0.0, 1)
    own = closes[-1] / closes[-6] - 1.0
    bench_closes = [c.close for c in benchmark]
    bench = bench_closes[-1] / bench_closes[-6] - 1.0
    if own - bench > 0.03:
        return _base(candles, Side.LONG, 0.7, "l2 relative strength versus benchmark", 0.03, 12)
    return _base(candles, Side.FLAT, 0.4, "l2 not leading benchmark", 0.0, 1)


def _rwa(candles: list[Candle], closes: list[float]) -> Signal:
    gap = candles[-1].open / candles[-2].close - 1.0
    if abs(gap) > 0.08:
        return _base(candles, Side.FLAT, 0.5, "rwa gap halt", 0.0, 1)
    if closes[-1] > _ema(closes, 8) and closes[-1] > closes[-5]:
        return _base(candles, Side.LONG, 0.66, "rwa slow trend", 0.02, 24)
    return _base(candles, Side.FLAT, 0.4, "rwa: no slow trend", 0.0, 1)


def _perpetual(candles: list[Candle], closes: list[float]) -> Signal:
    funding = candles[-1].funding_rate
    drift = closes[-1] / closes[-6] - 1.0
    if funding <= -0.0005 and abs(drift) < 0.04:
        return _base(candles, Side.LONG, 0.74, "perp funding carry: negative funding, basis contained", 0.02, 8)
    if funding >= 0.001:
        return _base(candles, Side.FLAT, 0.55, "perp funding too crowded for long carry", 0.0, 1)
    return _base(candles, Side.FLAT, 0.4, "perp: no carry edge", 0.0, 1)
