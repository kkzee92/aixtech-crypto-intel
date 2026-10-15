"""Asset-class strategy research rules.

Transparent heuristics for paper research. Not forecasts and not a recommendation
to trade. Each class has an entry, an invalidation, a regime overlay, and
volatility-aware sizing. Version 0.7 adds simple trend strength confirmation
and minor adaptive refinements on top of multi-factor (EMA/MACD/BB).
"""

from __future__ import annotations

from statistics import fmean, pstdev

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify, atr_pct

PLAYBOOK: dict[AssetClass, dict[str, str]] = {
    AssetClass.MAJOR: {
        "hypothesis": "Liquid majors trend with multi-EMA, MACD-style momentum, Bollinger-style envelope, and positive trend strength, except when RSI is stretched or the book is in stress.",
        "entry": "Fast > mid > slow EMA, positive MACD proxy, price near/above mid-band with positive slope, trend strength > 0.2, adaptive RSI band in trend or range. Washed-out adaptive RSI only in range. Vol-scaled size.",
        "invalidation": "Stress regime, or RSI stretched beyond adaptive limit, or weak trend strength.",
        "horizon": "8 bars mean-reversion, 20 bars trend",
    },
    AssetClass.LARGE_CAP_ALT: {
        "hypothesis": "Breakouts without volume are noise, and stress-regime breakouts are mostly gap risk. Adaptive volume + momentum + MACD + trend strength.",
        "entry": "Close above the prior five-bar high, volume at least adaptive mult, positive momentum, MACD, trend strength, outside stress.",
        "invalidation": "Stress regime or missing confirmation.",
        "horizon": "12 bars",
    },
    AssetClass.STABLECOIN: {
        "hypothesis": "The useful signal is a peg break, not direction. Adaptive bands with sustained check.",
        "entry": "Deviation beyond adaptive thresholds raises an alert. No order.",
        "invalidation": "Not applicable. Size stays zero.",
        "horizon": "1 bar monitor",
    },
    AssetClass.DEFI: {
        "hypothesis": "Trend only in a calm realised-vol regime with volume, momentum, and trend strength support.",
        "entry": "Close above 8-bar EMA, realised vol within adaptive, volume support, positive momentum and strength, not in stress.",
        "invalidation": "Stress regime or high realised vol.",
        "horizon": "10 bars",
    },
    AssetClass.MEME: {
        "hypothesis": "Most bursts are untradeable. A qualified burst still gets a hard time stop, tighter adaptive extension, volume accel, RSI filter, consistent direction.",
        "entry": "15% four-bar burst, rising volume with accel, volume floor, extension under adaptive, RSI not overbought, 3 rising closes.",
        "invalidation": "Thin liquidity proxy or chase extension or overbought or inconsistent.",
        "horizon": "3 bars",
    },
    AssetClass.L2: {
        "hypothesis": "L2 tokens are relative-strength bets versus a benchmark, with vol, relative volume, and trend strength filter.",
        "entry": "Six-bar excess return above threshold versus benchmark, benchmark not in stress, own ATR contained, relative volume ok, own strength positive.",
        "invalidation": "Missing benchmark or benchmark stress.",
        "horizon": "12 bars",
    },
    AssetClass.RWA: {
        "hypothesis": "Tokenised real-world assets should be slow. Adaptive gaps are a halt. Momentum and strength confirmation.",
        "entry": "Close above 8-bar EMA and above the close five bars ago, gap inside adaptive, positive momentum and strength.",
        "invalidation": "Open gap above adaptive or stress regime.",
        "horizon": "24 bars",
    },
    AssetClass.PERPETUAL: {
        "hypothesis": "Negative funding with contained adaptive drift, moderate ATR, stable funding, and contained trend strength is a carry observation.",
        "entry": "Funding at or below -5 bps and absolute six-bar drift under adaptive, ATR not extreme, funding stable, strength not extreme.",
        "invalidation": "Funding at or above 10 bps, or drift/vol/stability/strength not contained.",
        "horizon": "8 bars",
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


def _macd_proxy(closes: list[float]) -> float:
    """Simple MACD-style: EMA12 - EMA26. Research proxy."""
    if len(closes) < 26:
        return 0.0
    return _ema(closes, 12) - _ema(closes, 26)


def _bollinger_proxy(closes: list[float], window: int = 20) -> tuple[float, float]:
    """Simple Bollinger-style: mid = SMA, upper/lower = mid ± 2*stdev. Returns (mid, upper)."""
    if len(closes) < window:
        mid = fmean(closes)
        return mid, mid
    window_closes = closes[-window:]
    mid = fmean(window_closes)
    std = pstdev(window_closes) if len(window_closes) > 1 else 0.0
    return mid, mid + 2 * std


def _trend_strength(closes: list[float], period: int = 8) -> float:
    """Simple directional strength proxy: net directional move / total absolute move. Range -1 to 1."""
    if len(closes) < period + 1:
        return 0.0
    diffs = [closes[i] - closes[i - 1] for i in range(-period, 0)]
    pos = sum(d for d in diffs if d > 0)
    neg = sum(abs(d) for d in diffs if d < 0)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _rsi(closes: list[float], period: int = 14) -> float:
    changes = _returns(closes[-(period + 1) :])
    gains = [max(change, 0.0) for change in changes]
    losses = [abs(min(change, 0.0)) for change in changes]
    average_loss = fmean(losses) if losses else 0.0
    if average_loss == 0:
        return 100.0
    rs = fmean(gains) / average_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _vol_scaled_size(base_size: float, candles: list[Candle], target_atr: float = 0.02) -> float:
    """Scale size inversely with recent ATR so higher-vol assets take smaller risk."""
    atr = atr_pct(candles, 8)
    if atr <= 0:
        return base_size
    scale = min(1.0, target_atr / atr)
    return round(base_size * scale, 4)


def _base(
    candles: list[Candle],
    side: Side,
    confidence: float,
    reason: str,
    size: float,
    bars: int,
    scale_vol: bool = True,
) -> Signal:
    last = candles[-1]
    regime = classify(candles)
    final_size = _vol_scaled_size(size, candles) if scale_vol and size > 0 else size
    return Signal(
        symbol=last.symbol,
        asset_class=last.asset_class,
        side=side,
        confidence=round(max(0.0, min(confidence, 1.0)), 4),
        reason=f"{reason}; regime={regime.value}",
        stop_distance_pct=round(max(atr_pct(candles) * 1.5, 0.01), 4),
        size_fraction=final_size,
        horizon_bars=bars,
    )


def signal_for(candles: list[Candle], benchmark: list[Candle] | None = None) -> Signal:
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    closes = [c.close for c in candles]
    regime = classify(candles)
    atr = atr_pct(candles, 8)
    high_vol = atr > 0.03
    if asset_class is AssetClass.MAJOR:
        return _major(candles, closes, regime, high_vol)
    if asset_class is AssetClass.LARGE_CAP_ALT:
        return _breakout(candles, closes, size=0.04, bars=12, regime=regime, high_vol=high_vol)
    if asset_class is AssetClass.STABLECOIN:
        return _stable(candles, high_vol)
    if asset_class is AssetClass.DEFI:
        return _defi(candles, closes, regime, high_vol)
    if asset_class is AssetClass.MEME:
        return _meme(candles, closes, high_vol)
    if asset_class is AssetClass.L2:
        return _l2(candles, closes, benchmark, high_vol)
    if asset_class is AssetClass.RWA:
        return _rwa(candles, closes, regime, high_vol)
    return _perpetual(candles, closes, high_vol)


def _major(candles: list[Candle], closes: list[float], regime: Regime, high_vol: bool) -> Signal:
    fast, mid, slow = _ema(closes, 5), _ema(closes, 8), _ema(closes, 13)
    rsi = _rsi(closes, 12 if high_vol else 14)
    rsi_upper = 65 if high_vol else 70
    rsi_lower = 28 if high_vol else 30
    macd = _macd_proxy(closes)
    bb_mid, bb_upper = _bollinger_proxy(closes)
    price = closes[-1]
    bb_confirm = price >= bb_mid * 0.995 and (len(closes) < 2 or closes[-1] >= closes[-2])
    strength = _trend_strength(closes)
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.45, "major stress: stand aside", 0.0, 1, scale_vol=False)
    if fast > mid > slow and macd > 0 and bb_confirm and strength > 0.2 and 45 <= rsi <= rsi_upper:
        return _base(candles, Side.LONG, 0.80, "major multi-EMA + MACD + BB envelope + trend strength, adaptive RSI not stretched", 0.06, 20)
    if regime is Regime.RANGE and rsi < rsi_lower and closes[-1] > closes[-3]:
        return _base(candles, Side.LONG, 0.65, "major mean-reversion: washed-out adaptive RSI in range", 0.03, 8)
    return _base(candles, Side.FLAT, 0.4, "major: no aligned trend or reversion edge", 0.0, 1, scale_vol=False)


def _breakout(candles: list[Candle], closes: list[float], size: float, bars: int, regime: Regime, high_vol: bool) -> Signal:
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.4, "breakout suppressed in stress", 0.0, 1, scale_vol=False)
    window = closes[-6:-1]
    volume_now = candles[-1].volume
    volume_base = fmean(c.volume for c in candles[-6:-1])
    vol_mult = 1.5 if high_vol else 1.3
    mom = closes[-1] / closes[-4] - 1.0
    macd = _macd_proxy(closes)
    strength = _trend_strength(closes)
    strength_req = 0.15 if high_vol else 0.1
    if closes[-1] > max(window) and volume_now > volume_base * vol_mult and mom > 0.005 and macd > 0 and strength > strength_req:
        return _base(candles, Side.LONG, 0.76, "breakout with adaptive volume, momentum, MACD, and trend strength", size, bars)
    return _base(candles, Side.FLAT, 0.35, "no confirmed breakout", 0.0, 1, scale_vol=False)


def _stable(candles: list[Candle], high_vol: bool) -> Signal:
    deviation = abs(candles[-1].close - 1.0)
    watch = 0.003 if high_vol else 0.002
    depeg = 0.007 if high_vol else 0.005
    if deviation >= depeg:
        return _base(candles, Side.ALERT, 0.92, f"stablecoin depeg monitor: deviation {deviation:.4f}", 0.0, 1, scale_vol=False)
    if deviation >= watch:
        return _base(candles, Side.ALERT, 0.7, f"stablecoin watch band: deviation {deviation:.4f}", 0.0, 1, scale_vol=False)
    return _base(candles, Side.FLAT, 0.8, "stablecoin inside peg band", 0.0, 1, scale_vol=False)


def _defi(candles: list[Candle], closes: list[float], regime: Regime, high_vol: bool) -> Signal:
    realised = fmean(abs(v) for v in _returns(closes[-8:]))
    vol_limit = 0.05 if high_vol else 0.06
    vol_avg = fmean(c.volume for c in candles[-5:])
    mom = closes[-1] / closes[-5] - 1.0
    strength = _trend_strength(closes)
    if regime is Regime.STRESS or realised > vol_limit:
        return _base(candles, Side.FLAT, 0.48, "defi volatility regime: stand aside", 0.0, 1, scale_vol=False)
    if closes[-1] > _ema(closes, 8) and candles[-1].volume > vol_avg * 0.8 and mom > 0 and strength > 0.1:
        return _base(candles, Side.LONG, 0.74, "defi trend in calm regime with volume, momentum, and strength", 0.02, 10)
    return _base(candles, Side.FLAT, 0.4, "defi: no calm trend", 0.0, 1, scale_vol=False)


def _meme(candles: list[Candle], closes: list[float], high_vol: bool) -> Signal:
    liquidity = fmean(c.volume for c in candles[-5:])
    burst = closes[-1] / closes[-4] - 1.0
    extension = closes[-1] / closes[-8] - 1.0
    vol_accel = candles[-1].volume / max(candles[-2].volume, 1)
    rsi = _rsi(closes)
    rising = closes[-1] > closes[-2] > closes[-3]
    ext_limit = 0.30 if high_vol else 0.35
    accel_req = 1.3 if high_vol else 1.2
    if liquidity < 1000:
        return _base(candles, Side.FLAT, 0.2, "meme liquidity proxy too thin", 0.0, 1, scale_vol=False)
    if extension > ext_limit or rsi > 75:
        return _base(candles, Side.FLAT, 0.35, "meme chase filter: extension or overbought RSI", 0.0, 1, scale_vol=False)
    if burst > 0.15 and vol_accel > accel_req and rising:
        return _base(candles, Side.LONG, 0.81, "meme momentum burst with volume accel, consistency, and filters; hard time stop applies", 0.005, 3)
    return _base(candles, Side.FLAT, 0.3, "meme: no qualified burst", 0.0, 1, scale_vol=False)


def _l2(candles: list[Candle], closes: list[float], benchmark: list[Candle] | None, high_vol: bool) -> Signal:
    if not benchmark or len(benchmark) < 8:
        return _base(candles, Side.FLAT, 0.3, "l2 requires a benchmark series", 0.0, 1, scale_vol=False)
    if classify(benchmark) is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.42, "l2 benchmark in stress", 0.0, 1, scale_vol=False)
    own = closes[-1] / closes[-6] - 1.0
    bench_closes = [c.close for c in benchmark]
    bench = bench_closes[-1] / bench_closes[-6] - 1.0
    own_atr = atr_pct(candles, 8)
    thresh = 0.035 if high_vol else 0.03
    own_vol = fmean(c.volume for c in candles[-6:])
    bench_vol = fmean(c.volume for c in benchmark[-6:]) if benchmark else 1
    rel_vol = own_vol / max(bench_vol, 1)
    strength = _trend_strength(closes)
    if own - bench > thresh and own_atr < 0.04 and rel_vol > 0.7 and strength > 0.1:
        return _base(candles, Side.LONG, 0.75, "l2 relative strength versus benchmark, ATR contained, relative volume, own strength ok", 0.03, 12)
    return _base(candles, Side.FLAT, 0.4, "l2 not leading benchmark", 0.0, 1, scale_vol=False)


def _rwa(candles: list[Candle], closes: list[float], regime: Regime, high_vol: bool) -> Signal:
    gap = candles[-1].open / candles[-2].close - 1.0 if len(candles) >= 2 else 0.0
    momentum = closes[-1] / closes[-3] - 1.0 if len(closes) >= 3 else 0.0
    strength = _trend_strength(closes, 12)
    gap_limit = 0.07 if high_vol else 0.08
    if abs(gap) > gap_limit or regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.5, "rwa gap or stress halt", 0.0, 1, scale_vol=False)
    if closes[-1] > _ema(closes, 8) and closes[-1] > closes[-5] and momentum > 0 and strength > 0.05:
        return _base(candles, Side.LONG, 0.72, "rwa slow trend with momentum and strength confirmation", 0.02, 24)
    return _base(candles, Side.FLAT, 0.4, "rwa: no slow trend", 0.0, 1, scale_vol=False)


def _perpetual(candles: list[Candle], closes: list[float], high_vol: bool) -> Signal:
    funding = candles[-1].funding_rate
    prev_funding = candles[-2].funding_rate if len(candles) > 1 else funding
    drift = closes[-1] / closes[-6] - 1.0 if len(closes) >= 6 else 0.0
    atr = atr_pct(candles, 8)
    strength = abs(_trend_strength(closes))
    drift_limit = 0.035 if high_vol else 0.04
    funding_stable = abs(funding - prev_funding) < 0.0003
    if funding >= 0.001:
        return _base(candles, Side.ALERT, 0.7, "perp funding crowded: monitor, no carry", 0.0, 1, scale_vol=False)
    if funding <= -0.0005 and abs(drift) < drift_limit and atr < 0.05 and funding_stable and strength < 0.6:
        return _base(candles, Side.LONG, 0.80, "perp funding carry: negative funding, basis contained, ATR moderate, stable, strength contained", 0.02, 8)
    if funding <= -0.0005:
        return _base(candles, Side.FLAT, 0.5, "perp funding attractive but drift, vol, stability, or strength not contained", 0.0, 1, scale_vol=False)
    return _base(candles, Side.FLAT, 0.4, "perp: no carry edge", 0.0, 1, scale_vol=False)
