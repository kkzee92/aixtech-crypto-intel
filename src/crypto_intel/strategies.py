"""Asset-class strategy research rules (v0.3).

Transparent heuristics for paper research. Not forecasts and not a recommendation
to trade. Each class has an entry, an invalidation, a regime overlay, and
quality filters. Version 0.3 adds multi-horizon confirmation, breakout quality,
velocity checks, and stricter meme/perp controls.
"""

from __future__ import annotations

from statistics import fmean, pstdev

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify

PLAYBOOK: dict[AssetClass, dict[str, str]] = {
    AssetClass.MAJOR: {
        "hypothesis": "Liquid majors trend when multi-horizon EMAs align and RSI is not extreme; stress stands aside.",
        "entry": "Fast EMA > slow EMA, higher-horizon EMA support, RSI 40-68, non-stress.",
        "invalidation": "Stress regime or RSI > 72.",
        "horizon": "20 bars trend; 8 bars range reversion",
    },
    AssetClass.LARGE_CAP_ALT: {
        "hypothesis": "Volume-confirmed breakouts outside stress with range expansion have better quality.",
        "entry": "Close above prior 5-bar high, volume >1.3x, range expansion, non-stress.",
        "invalidation": "Stress or missing volume/expansion.",
        "horizon": "12 bars",
    },
    AssetClass.STABLECOIN: {
        "hypothesis": "Peg deviation and its velocity are the useful monitors. No directional order.",
        "entry": "Deviation >=50 bps or rapid velocity raises alert. Size always zero.",
        "invalidation": "N/A",
        "horizon": "1 bar monitor",
    },
    AssetClass.DEFI: {
        "hypothesis": "Trend only in calm realised-vol and adequate liquidity proxy.",
        "entry": "Close > 8-bar EMA, realised vol <=5.5%, volume floor, non-stress.",
        "invalidation": "Stress or elevated vol.",
        "horizon": "10 bars",
    },
    AssetClass.MEME: {
        "hypothesis": "Most bursts fail. Qualified bursts need acceleration, volume floor, and no extreme extension.",
        "entry": "15% 4-bar burst + volume acceleration + volume floor + extension <35% over 8 bars.",
        "invalidation": "Thin volume proxy or chase.",
        "horizon": "3 bars hard time stop",
    },
    AssetClass.L2: {
        "hypothesis": "Relative strength vs non-stress benchmark is the edge.",
        "entry": "6-bar excess >3% vs benchmark, benchmark not in stress.",
        "invalidation": "Missing or stressed benchmark.",
        "horizon": "12 bars",
    },
    AssetClass.RWA: {
        "hypothesis": "Slow trend only; gaps and stress are hard halts.",
        "entry": "Close > 8-bar EMA and prior 5-bar close, gap <6%, low realised vol, non-stress.",
        "invalidation": "Gap >6% or stress.",
        "horizon": "24 bars",
    },
    AssetClass.PERPETUAL: {
        "hypothesis": "Negative funding + contained drift = carry observation. Crowded funding + extension = research fade.",
        "entry": "Funding <= -5 bps and |6-bar drift| < 3.5%. Crowded + drift >4% is paper short fade.",
        "invalidation": "Drift not contained or extreme funding without structure.",
        "horizon": "8 bars carry / 4 bars fade",
    },
}


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
    regime = classify(candles)
    return Signal(
        symbol=last.symbol,
        asset_class=last.asset_class,
        side=side,
        confidence=round(max(0.0, min(confidence, 1.0)), 4),
        reason=f"{reason}; regime={regime.value}",
        stop_distance_pct=round(max(_atr_pct(candles) * 1.5, 0.01), 4),
        size_fraction=size,
        horizon_bars=bars,
    )


def signal_for(candles: list[Candle], benchmark: list[Candle] | None = None) -> Signal:
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    closes = [c.close for c in candles]
    regime = classify(candles)
    if asset_class is AssetClass.MAJOR:
        return _major(candles, closes, regime)
    if asset_class is AssetClass.LARGE_CAP_ALT:
        return _breakout(candles, closes, size=0.04, bars=12, regime=regime)
    if asset_class is AssetClass.STABLECOIN:
        return _stable(candles)
    if asset_class is AssetClass.DEFI:
        return _defi(candles, closes, regime)
    if asset_class is AssetClass.MEME:
        return _meme(candles, closes)
    if asset_class is AssetClass.L2:
        return _l2(candles, closes, benchmark)
    if asset_class is AssetClass.RWA:
        return _rwa(candles, closes, regime)
    return _perpetual(candles, closes)


def _major(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.45, "major stress: stand aside", 0.0, 1)
    fast, slow = _ema(closes, 5), _ema(closes, 13)
    higher = _ema(closes, 21)
    rsi = _rsi(closes)
    if fast > slow > higher and 40 <= rsi <= 68:
        return _base(candles, Side.LONG, 0.76, "major multi-horizon trend alignment, RSI contained", 0.06, 20)
    if regime is Regime.RANGE and rsi < 32 and closes[-1] > closes[-3]:
        return _base(candles, Side.LONG, 0.63, "major mean-reversion: washed-out RSI in range", 0.03, 8)
    return _base(candles, Side.FLAT, 0.4, "major: no multi-horizon or reversion edge", 0.0, 1)


def _breakout(candles: list[Candle], closes: list[float], size: float, bars: int, regime: Regime) -> Signal:
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.4, "breakout suppressed in stress", 0.0, 1)
    window = closes[-6:-1]
    volume_now = candles[-1].volume
    volume_base = fmean(c.volume for c in candles[-6:-1])
    range_now = (candles[-1].high - candles[-1].low) / candles[-1].close if candles[-1].close else 0
    range_base = fmean((c.high - c.low) / c.close for c in candles[-6:-1] if c.close)
    if (closes[-1] > max(window) and volume_now > volume_base * 1.3
            and range_now > range_base * 1.1):
        return _base(candles, Side.LONG, 0.73, "breakout with volume and range expansion", size, bars)
    return _base(candles, Side.FLAT, 0.35, "no quality breakout", 0.0, 1)


def _stable(candles: list[Candle]) -> Signal:
    deviation = abs(candles[-1].close - 1.0)
    prev_dev = abs(candles[-2].close - 1.0) if len(candles) > 1 else 0.0
    velocity = deviation - prev_dev
    if deviation >= 0.005 or velocity >= 0.003:
        return _base(candles, Side.ALERT, 0.93, f"stablecoin depeg/velocity alert: dev={deviation:.4f} vel={velocity:.4f}", 0.0, 1)
    if deviation >= 0.002:
        return _base(candles, Side.ALERT, 0.72, f"stablecoin watch band: deviation {deviation:.4f}", 0.0, 1)
    return _base(candles, Side.FLAT, 0.82, "stablecoin inside peg band", 0.0, 1)


def _defi(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    realised = fmean(abs(v) for v in _returns(closes[-8:]))
    vol_floor = fmean(c.volume for c in candles[-5:])
    if regime is Regime.STRESS or realised > 0.055 or vol_floor < 500:
        return _base(candles, Side.FLAT, 0.48, "defi volatility or liquidity regime: stand aside", 0.0, 1)
    if closes[-1] > _ema(closes, 8):
        return _base(candles, Side.LONG, 0.70, "defi trend in calm regime with liquidity", 0.02, 10)
    return _base(candles, Side.FLAT, 0.4, "defi: no calm trend", 0.0, 1)


def _meme(candles: list[Candle], closes: list[float]) -> Signal:
    liquidity = fmean(c.volume for c in candles[-5:])
    burst = closes[-1] / closes[-4] - 1.0
    extension = closes[-1] / closes[-8] - 1.0
    vol_accel = candles[-1].volume > candles[-2].volume > candles[-3].volume
    if liquidity < 1500:
        return _base(candles, Side.FLAT, 0.2, "meme liquidity proxy too thin", 0.0, 1)
    if extension > 0.35:
        return _base(candles, Side.FLAT, 0.35, "meme chase filter: 8-bar extension too large", 0.0, 1)
    if burst > 0.15 and vol_accel:
        return _base(candles, Side.LONG, 0.77, "meme qualified burst with volume acceleration; hard time stop", 0.005, 3)
    return _base(candles, Side.FLAT, 0.3, "meme: no qualified burst", 0.0, 1)


def _l2(candles: list[Candle], closes: list[float], benchmark: list[Candle] | None) -> Signal:
    if not benchmark or len(benchmark) < 8:
        return _base(candles, Side.FLAT, 0.3, "l2 requires a benchmark series", 0.0, 1)
    if classify(benchmark) is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.42, "l2 benchmark in stress", 0.0, 1)
    own = closes[-1] / closes[-6] - 1.0
    bench_closes = [c.close for c in benchmark]
    bench = bench_closes[-1] / bench_closes[-6] - 1.0
    if own - bench > 0.03:
        return _base(candles, Side.LONG, 0.71, "l2 relative strength versus non-stress benchmark", 0.03, 12)
    return _base(candles, Side.FLAT, 0.4, "l2 not leading benchmark", 0.0, 1)


def _rwa(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    gap = candles[-1].open / candles[-2].close - 1.0 if len(candles) > 1 else 0.0
    realised = fmean(abs(v) for v in _returns(closes[-8:]))
    if abs(gap) > 0.06 or regime is Regime.STRESS or realised > 0.04:
        return _base(candles, Side.FLAT, 0.5, "rwa gap, stress, or elevated vol halt", 0.0, 1)
    if closes[-1] > _ema(closes, 8) and closes[-1] > closes[-5]:
        return _base(candles, Side.LONG, 0.68, "rwa slow trend in calm conditions", 0.02, 24)
    return _base(candles, Side.FLAT, 0.4, "rwa: no slow trend", 0.0, 1)


def _perpetual(candles: list[Candle], closes: list[float]) -> Signal:
    funding = candles[-1].funding_rate
    drift = closes[-1] / closes[-6] - 1.0
    if funding >= 0.001 and drift > 0.04:
        return _base(candles, Side.SHORT, 0.67, "perp crowded-funding fade research; hard size cap", 0.01, 4)
    if funding >= 0.001:
        return _base(candles, Side.ALERT, 0.7, "perp funding crowded: monitor only", 0.0, 1)
    if funding <= -0.0005 and abs(drift) < 0.035:
        return _base(candles, Side.LONG, 0.76, "perp funding carry: negative funding, tighter basis containment", 0.02, 8)
    if funding <= -0.0005:
        return _base(candles, Side.FLAT, 0.5, "perp funding attractive but drift not contained", 0.0, 1)
    return _base(candles, Side.FLAT, 0.4, "perp: no carry edge", 0.0, 1)
