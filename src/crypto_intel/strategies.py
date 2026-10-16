"""Asset-class strategy research rules.

Transparent heuristics for paper research. Not forecasts and not a recommendation
to trade. Each class has an entry, an invalidation, a regime overlay, and
volatility-aware sizing. Version 0.9 adds stochastic oscillator confirmation,
multi-window alignment, simple correlation proxy for relative strength, and
refined adaptive thresholds on top of prior multi-factor (EMA/MACD/BB/trend strength/median volume).
"""

from __future__ import annotations

from statistics import fmean, median, pstdev

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify, atr_pct

PLAYBOOK: dict[AssetClass, dict[str, str]] = {
    AssetClass.MAJOR: {
        "hypothesis": "Liquid majors trend with multi-EMA alignment, MACD-style momentum, Bollinger-style envelope, positive trend strength, short-vs-long window confirmation, and stochastic not extreme, except when RSI is stretched or the book is in stress.",
        "entry": "Fast > mid > slow EMA, positive MACD proxy, price near/above mid-band, trend strength > 0.2, short-window EMA slope positive, stochastic %K in adaptive band, adaptive RSI band in trend or range. Washed-out adaptive RSI + stochastic only in range. Vol-scaled size.",
        "invalidation": "Stress regime, or RSI/stochastic stretched beyond adaptive limit, or weak trend strength, or conflicting windows.",
        "horizon": "8 bars mean-reversion, 20 bars trend",
    },
    AssetClass.LARGE_CAP_ALT: {
        "hypothesis": "Breakouts without volume are noise, and stress-regime breakouts are mostly gap risk. Median-based adaptive volume + momentum + MACD + trend strength + stochastic filter.",
        "entry": "Close above the prior five-bar high, volume at least adaptive mult of median, positive momentum, MACD, trend strength, stochastic not overbought, outside stress.",
        "invalidation": "Stress regime or missing confirmation.",
        "horizon": "12 bars",
    },
    AssetClass.STABLECOIN: {
        "hypothesis": "The useful signal is a peg break, not direction. Adaptive bands with sustained multi-bar check.",
        "entry": "Deviation beyond adaptive thresholds raises an alert. No order.",
        "invalidation": "Not applicable. Size stays zero.",
        "horizon": "1 bar monitor",
    },
    AssetClass.DEFI: {
        "hypothesis": "Trend only in a calm realised-vol regime with volume, momentum, trend strength, and stochastic support.",
        "entry": "Close above 8-bar EMA, realised vol within adaptive, volume support vs median, positive momentum and strength, stochastic not extreme, not in stress.",
        "invalidation": "Stress regime or high realised vol.",
        "horizon": "10 bars",
    },
    AssetClass.MEME: {
        "hypothesis": "Most bursts are untradeable. A qualified burst still gets a hard time stop, tighter adaptive extension, volume accel vs median, RSI/stochastic filter, consistent direction.",
        "entry": "15% four-bar burst, rising volume with accel, volume floor vs median, extension under adaptive, RSI and stochastic not overbought, 3 rising closes.",
        "invalidation": "Thin liquidity proxy or chase extension or overbought or inconsistent.",
        "horizon": "3 bars",
    },
    AssetClass.L2: {
        "hypothesis": "L2 tokens are relative-strength bets versus a benchmark, with vol, relative volume (median), trend strength, and positive correlation proxy filter.",
        "entry": "Six-bar excess return above threshold versus benchmark, benchmark not in stress, own ATR contained, relative volume ok, own strength positive, correlation proxy > 0.3.",
        "invalidation": "Missing benchmark or benchmark stress or low correlation.",
        "horizon": "12 bars",
    },
    AssetClass.RWA: {
        "hypothesis": "Tokenised real-world assets should be slow. Adaptive gaps are a halt. Momentum, strength, and stochastic confirmation.",
        "entry": "Close above 8-bar EMA and above the close five bars ago, gap inside adaptive, positive momentum and strength, stochastic not extreme.",
        "invalidation": "Open gap above adaptive or stress regime.",
        "horizon": "24 bars",
    },
    AssetClass.PERPETUAL: {
        "hypothesis": "Negative funding with contained adaptive drift, moderate ATR, multi-print funding stability, contained trend strength, and stochastic filter is a carry observation.",
        "entry": "Funding at or below -5 bps over recent prints, absolute six-bar drift under adaptive, ATR not extreme, funding stable, strength not extreme, stochastic contained.",
        "invalidation": "Funding at or above 10 bps, or drift/vol/stability/strength/stochastic not contained.",
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


def _stochastic_k(candles: list[Candle], period: int = 14) -> float:
    """Simple stochastic %K proxy. Research only."""
    if len(candles) < period:
        return 50.0
    recent = candles[-period:]
    lowest = min(c.low for c in recent)
    highest = max(c.high for c in recent)
    if highest == lowest:
        return 50.0
    return 100.0 * (candles[-1].close - lowest) / (highest - lowest)


def _correlation_proxy(closes1: list[float], closes2: list[float], window: int = 8) -> float:
    """Simple Pearson-like correlation proxy over recent returns. Research only."""
    if len(closes1) < window + 1 or len(closes2) < window + 1:
        return 0.0
    r1 = _returns(closes1[-(window + 1):])
    r2 = _returns(closes2[-(window + 1):])
    if len(r1) != len(r2) or not r1:
        return 0.0
    mean1, mean2 = fmean(r1), fmean(r2)
    cov = fmean((a - mean1) * (b - mean2) for a, b in zip(r1, r2))
    std1 = pstdev(r1) if len(r1) > 1 else 1.0
    std2 = pstdev(r2) if len(r2) > 1 else 1.0
    if std1 == 0 or std2 == 0:
        return 0.0
    return max(-1.0, min(1.0, cov / (std1 * std2)))


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
    stoch = _stochastic_k(candles, 10 if high_vol else 14)
    stoch_upper = 80 if high_vol else 85
    stoch_lower = 20 if high_vol else 15
    macd = _macd_proxy(closes)
    bb_mid, bb_upper = _bollinger_proxy(closes)
    price = closes[-1]
    bb_confirm = price >= bb_mid * 0.995 and (len(closes) < 2 or closes[-1] >= closes[-2])
    strength = _trend_strength(closes)
    short_slope = (fast - _ema(closes[:-1], 5)) > 0 if len(closes) > 5 else True
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.45, "major stress: stand aside", 0.0, 1, scale_vol=False)
    if fast > mid > slow and macd > 0 and bb_confirm and strength > 0.2 and short_slope and 45 <= rsi <= rsi_upper and stoch < stoch_upper:
        return _base(candles, Side.LONG, 0.84, "major multi-EMA + MACD + BB envelope + trend strength + short slope + stochastic contained, adaptive RSI not stretched", 0.06, 20)
    if regime is Regime.RANGE and rsi < rsi_lower and stoch < stoch_lower and closes[-1] > closes[-3]:
        return _base(candles, Side.LONG, 0.68, "major mean-reversion: washed-out adaptive RSI and stochastic in range", 0.03, 8)
    return _base(candles, Side.FLAT, 0.4, "major: no aligned trend or reversion edge", 0.0, 1, scale_vol=False)


def _breakout(candles: list[Candle], closes: list[float], size: float, bars: int, regime: Regime, high_vol: bool) -> Signal:
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.4, "breakout suppressed in stress", 0.0, 1, scale_vol=False)
    window = closes[-6:-1]
    volume_now = candles[-1].volume
    volumes = [c.volume for c in candles[-6:-1]]
    volume_base = median(volumes) if volumes else 1.0
    vol_mult = 1.5 if high_vol else 1.3
    mom = closes[-1] / closes[-4] - 1.0
    macd = _macd_proxy(closes)
    strength = _trend_strength(closes)
    strength_req = 0.15 if high_vol else 0.1
    stoch = _stochastic_k(candles)
    if closes[-1] > max(window) and volume_now > volume_base * vol_mult and mom > 0.005 and macd > 0 and strength > strength_req and stoch < 85:
        return _base(candles, Side.LONG, 0.79, "breakout with median-based adaptive volume, momentum, MACD, trend strength, and stochastic filter", size, bars)
    return _base(candles, Side.FLAT, 0.35, "no confirmed breakout", 0.0, 1, scale_vol=False)


def _stable(candles: list[Candle], high_vol: bool) -> Signal:
    deviation = abs(candles[-1].close - 1.0)
    watch = 0.003 if high_vol else 0.002
    depeg = 0.007 if high_vol else 0.005
    prior_dev = abs(candles[-2].close - 1.0) if len(candles) > 1 else 0.0
    sustained = prior_dev >= watch * 0.8
    if deviation >= depeg and sustained:
        return _base(candles, Side.ALERT, 0.93, f"stablecoin depeg monitor: deviation {deviation:.4f} sustained", 0.0, 1, scale_vol=False)
    if deviation >= watch:
        return _base(candles, Side.ALERT, 0.72, f"stablecoin watch band: deviation {deviation:.4f}", 0.0, 1, scale_vol=False)
    return _base(candles, Side.FLAT, 0.8, "stablecoin inside peg band", 0.0, 1, scale_vol=False)


def _defi(candles: list[Candle], closes: list[float], regime: Regime, high_vol: bool) -> Signal:
    realised = fmean(abs(v) for v in _returns(closes[-8:]))
    vol_limit = 0.05 if high_vol else 0.06
    volumes = [c.volume for c in candles[-5:]]
    vol_med = median(volumes) if volumes else 1.0
    mom = closes[-1] / closes[-5] - 1.0
    strength = _trend_strength(closes)
    stoch = _stochastic_k(candles)
    if regime is Regime.STRESS or realised > vol_limit:
        return _base(candles, Side.FLAT, 0.48, "defi volatility regime: stand aside", 0.0, 1, scale_vol=False)
    if closes[-1] > _ema(closes, 8) and candles[-1].volume > vol_med * 0.8 and mom > 0 and strength > 0.1 and stoch < 80:
        return _base(candles, Side.LONG, 0.77, "defi trend in calm regime with median volume, momentum, strength, and stochastic", 0.02, 10)
    return _base(candles, Side.FLAT, 0.4, "defi: no calm trend", 0.0, 1, scale_vol=False)


def _meme(candles: list[Candle], closes: list[float], high_vol: bool) -> Signal:
    volumes = [c.volume for c in candles[-5:]]
    liquidity = median(volumes) if volumes else 0.0
    burst = closes[-1] / closes[-4] - 1.0
    extension = closes[-1] / closes[-8] - 1.0
    vol_accel = candles[-1].volume / max(candles[-2].volume, 1)
    rsi = _rsi(closes)
    stoch = _stochastic_k(candles)
    rising = closes[-1] > closes[-2] > closes[-3]
    ext_limit = 0.30 if high_vol else 0.35
    accel_req = 1.3 if high_vol else 1.2
    if liquidity < 1000:
        return _base(candles, Side.FLAT, 0.2, "meme liquidity proxy too thin (median)", 0.0, 1, scale_vol=False)
    if extension > ext_limit or rsi > 75 or stoch > 85:
        return _base(candles, Side.FLAT, 0.35, "meme chase filter: extension or overbought RSI/stochastic", 0.0, 1, scale_vol=False)
    if burst > 0.15 and vol_accel > accel_req and rising:
        return _base(candles, Side.LONG, 0.83, "meme momentum burst with volume accel, consistency, median floor, RSI/stochastic filters; hard time stop applies", 0.005, 3)
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
    own_vols = [c.volume for c in candles[-6:]]
    own_vol = median(own_vols) if own_vols else 1.0
    bench_vols = [c.volume for c in benchmark[-6:]] if benchmark else [1]
    bench_vol = median(bench_vols) if bench_vols else 1.0
    rel_vol = own_vol / max(bench_vol, 1)
    strength = _trend_strength(closes)
    corr = _correlation_proxy(closes, bench_closes)
    if own - bench > thresh and own_atr < 0.04 and rel_vol > 0.7 and strength > 0.1 and corr > 0.3:
        return _base(candles, Side.LONG, 0.78, "l2 relative strength versus benchmark, ATR contained, median relative volume, own strength, correlation proxy ok", 0.03, 12)
    return _base(candles, Side.FLAT, 0.4, "l2 not leading benchmark or low correlation", 0.0, 1, scale_vol=False)


def _rwa(candles: list[Candle], closes: list[float], regime: Regime, high_vol: bool) -> Signal:
    gap = candles[-1].open / candles[-2].close - 1.0 if len(candles) >= 2 else 0.0
    momentum = closes[-1] / closes[-3] - 1.0 if len(closes) >= 3 else 0.0
    strength = _trend_strength(closes, 12)
    stoch = _stochastic_k(candles)
    gap_limit = 0.07 if high_vol else 0.08
    if abs(gap) > gap_limit or regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.5, "rwa gap or stress halt", 0.0, 1, scale_vol=False)
    if closes[-1] > _ema(closes, 8) and closes[-1] > closes[-5] and momentum > 0 and strength > 0.05 and stoch < 80:
        return _base(candles, Side.LONG, 0.75, "rwa slow trend with momentum, strength, and stochastic confirmation", 0.02, 24)
    return _base(candles, Side.FLAT, 0.4, "rwa: no slow trend", 0.0, 1, scale_vol=False)


def _perpetual(candles: list[Candle], closes: list[float], high_vol: bool) -> Signal:
    funding = candles[-1].funding_rate
    recent_fundings = [c.funding_rate for c in candles[-3:]]
    funding_stable = all(abs(f - funding) < 0.0004 for f in recent_fundings) if recent_fundings else True
    drift = closes[-1] / closes[-6] - 1.0 if len(closes) >= 6 else 0.0
    atr = atr_pct(candles, 8)
    strength = abs(_trend_strength(closes))
    stoch = _stochastic_k(candles)
    drift_limit = 0.035 if high_vol else 0.04
    if funding >= 0.001:
        return _base(candles, Side.ALERT, 0.7, "perp funding crowded: monitor, no carry", 0.0, 1, scale_vol=False)
    if funding <= -0.0005 and abs(drift) < drift_limit and atr < 0.05 and funding_stable and strength < 0.6 and 20 < stoch < 80:
        return _base(candles, Side.LONG, 0.83, "perp funding carry: negative funding (multi-print stable), basis contained, ATR moderate, strength and stochastic contained", 0.02, 8)
    if funding <= -0.0005:
        return _base(candles, Side.FLAT, 0.5, "perp funding attractive but drift, vol, multi-print stability, strength, or stochastic not contained", 0.0, 1, scale_vol=False)
    return _base(candles, Side.FLAT, 0.4, "perp: no carry edge", 0.0, 1, scale_vol=False)
