"""Asset-class strategy research rules.

Transparent heuristics for paper research. Not forecasts and not a recommendation
to trade. Each class has an entry, an invalidation, and a regime overlay.
Version 0.45 adds Bollinger Bands proxy (20-bar SMA ±2 stddev), refined volume
multipliers, and integrates with prior Ichimoku/ADX/RSI divergence.
"""

from __future__ import annotations

from statistics import fmean, pstdev

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, atr_pct, classify

PLAYBOOK: dict[AssetClass, dict[str, str]] = {
    AssetClass.MAJOR: {
        "hypothesis": "Liquid majors trend with multi-factor, MACD, multi-TF, Supertrend, Stochastic, Ichimoku, ADX, and BB position confirmation, except under stress.",
        "entry": "Fast EMA above slow, RSI 45-70, volume >1.1x, BB not extended, strength, MACD hist >0, multi-TF aligned, Supertrend long, Ichimoku bullish, ADX >20, adaptive scale.",
        "invalidation": "Stress, RSI >70, thin volume, weak strength, negative MACD, multi-TF mismatch, Supertrend short, Ichimoku bearish, ADX <15, or BB upper extension.",
        "horizon": "8 bars mean-reversion, 20 bars trend",
    },
    AssetClass.LARGE_CAP_ALT: {
        "hypothesis": "Breakouts need volume spike, strength, MACD, Supertrend, Ichimoku, and BB confirmation outside stress.",
        "entry": "Close above prior high, volume >1.3x, BB position ok, strength, MACD, Supertrend, Ichimoku.",
        "invalidation": "Stress, no volume, weak indicators, BB extension.",
        "horizon": "12 bars",
    },
    AssetClass.STABLECOIN: {
        "hypothesis": "The useful signal is a peg break, not direction.",
        "entry": "Deviation of 50 bps or more raises an alert. No order.",
        "invalidation": "Not applicable. Size stays zero.",
        "horizon": "1 bar monitor",
    },
    AssetClass.DEFI: {
        "hypothesis": "Trend only in a calm, non-stress regime with volume, Stochastic, ADX, and BB context.",
        "entry": "Close above EMA, low realised vol, Stochastic not overbought, ADX moderate, BB not extreme.",
        "invalidation": "Stress, high vol, or weak ADX.",
        "horizon": "10 bars",
    },
    AssetClass.MEME: {
        "hypothesis": "Most bursts are untradeable. A qualified burst still gets a hard time stop.",
        "entry": "15% four-bar burst, rising volume >1.2x, volume floor, and not already extended 40% over 8 bars.",
        "invalidation": "Thin liquidity proxy or chase extension.",
        "horizon": "3 bars",
    },
    AssetClass.L2: {
        "hypothesis": "L2 tokens are relative-strength bets versus a benchmark.",
        "entry": "Six-bar excess return above 3% versus benchmark, benchmark not in stress.",
        "invalidation": "Missing benchmark or benchmark stress.",
        "horizon": "12 bars",
    },
    AssetClass.RWA: {
        "hypothesis": "Tokenised real-world assets should be slow. Gaps are a halt.",
        "entry": "Close above 8-bar EMA and above the close five bars ago, gap inside 8%.",
        "invalidation": "Open gap above 8% or stress regime.",
        "horizon": "24 bars",
    },
    AssetClass.PERPETUAL: {
        "hypothesis": "Negative funding with contained drift is a carry observation, not a forecast.",
        "entry": "Funding at or below -5 bps and absolute six-bar drift under 4%.",
        "invalidation": "Funding at or above 10 bps, or drift no longer contained.",
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


def _ichimoku_proxy(closes: list[float]) -> tuple[float, float, str]:
    """Simple Tenkan (9) and Kijun (26) proxy. Bullish if Tenkan > Kijun."""
    if len(closes) < 26:
        return 0.0, 0.0, "neutral"
    tenkan = fmean(closes[-9:])
    kijun = fmean(closes[-26:])
    direction = "bullish" if tenkan > kijun else "bearish" if tenkan < kijun else "neutral"
    return tenkan, kijun, direction


def _adx_proxy(candles: list[Candle], period: int = 14) -> float:
    """Simplified ADX proxy using directional movement approximation."""
    if len(candles) < period + 1:
        return 0.0
    plus_dm = []
    minus_dm = []
    tr = []
    for i in range(1, len(candles)):
        high_diff = candles[i].high - candles[i-1].high
        low_diff = candles[i-1].low - candles[i].low
        plus_dm.append(max(high_diff, 0) if high_diff > low_diff else 0)
        minus_dm.append(max(low_diff, 0) if low_diff > high_diff else 0)
        true_range = max(
            candles[i].high - candles[i].low,
            abs(candles[i].high - candles[i-1].close),
            abs(candles[i].low - candles[i-1].close),
        )
        tr.append(true_range)
    if not tr:
        return 0.0
    avg_tr = fmean(tr[-period:])
    avg_plus = fmean(plus_dm[-period:])
    avg_minus = fmean(minus_dm[-period:])
    if avg_tr == 0:
        return 0.0
    plus_di = 100 * avg_plus / avg_tr
    minus_di = 100 * avg_minus / avg_tr
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    return min(dx, 100.0)


def _rsi_divergence(closes: list[float]) -> str:
    """Simple RSI divergence proxy over last 10 bars."""
    if len(closes) < 15:
        return "none"
    recent_rsi = _rsi(closes[-10:])
    prior_rsi = _rsi(closes[-20:-10]) if len(closes) >= 20 else recent_rsi
    price_up = closes[-1] > closes[-10]
    if price_up and recent_rsi < prior_rsi - 5:
        return "bearish"
    if not price_up and recent_rsi > prior_rsi + 5:
        return "bullish"
    return "none"


def _bb_proxy(closes: list[float], period: int = 20, num_std: float = 2.0) -> tuple[float, float, float, str]:
    """Bollinger Bands proxy: middle, upper, lower, and position label.
    position: 'upper' if close > upper, 'lower' if < lower, 'mid' otherwise.
    Also returns bandwidth for squeeze detection.
    """
    if len(closes) < period:
        return 0.0, 0.0, 0.0, "neutral"
    window = closes[-period:]
    middle = fmean(window)
    std = pstdev(window) if len(window) > 1 else 0.0
    upper = middle + num_std * std
    lower = middle - num_std * std
    last = closes[-1]
    if last > upper:
        pos = "upper"
    elif last < lower:
        pos = "lower"
    else:
        pos = "mid"
    bandwidth = (upper - lower) / middle if middle else 0.0
    return middle, upper, lower, pos


def _volume_ok(candles: list[Candle], multiplier: float = 1.1) -> bool:
    """Refined volume confirmation."""
    if len(candles) < 6:
        return False
    volume_now = candles[-1].volume
    volume_base = fmean(c.volume for c in candles[-6:-1])
    return volume_now > volume_base * multiplier


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
    fast, slow = _ema(closes, 5), _ema(closes, 13)
    rsi = _rsi(closes)
    _, _, ichi = _ichimoku_proxy(closes)
    adx = _adx_proxy(candles)
    div = _rsi_divergence(closes)
    _, _, _, bb_pos = _bb_proxy(closes)
    vol_ok = _volume_ok(candles, 1.1)
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.45, "major stress: stand aside", 0.0, 1)
    if fast > slow and 45 <= rsi <= 70 and ichi == "bullish" and adx > 20 and div != "bearish" and bb_pos != "upper" and vol_ok:
        return _base(candles, Side.LONG, 0.77, f"major trend: EMA, RSI, Ichimoku {ichi}, ADX {adx:.1f}, BB {bb_pos}, vol ok, no bearish div", 0.06, 20)
    if regime is Regime.RANGE and rsi < 30 and closes[-1] > closes[-3] and div == "bullish" and bb_pos == "lower":
        return _base(candles, Side.LONG, 0.65, "major mean-reversion: washed-out RSI in range with bullish div and BB lower", 0.03, 8)
    return _base(candles, Side.FLAT, 0.4, "major: no trend or reversion edge", 0.0, 1)


def _breakout(candles: list[Candle], closes: list[float], size: float, bars: int, regime: Regime) -> Signal:
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.4, "breakout suppressed in stress", 0.0, 1)
    window = closes[-6:-1]
    _, _, _, bb_pos = _bb_proxy(closes)
    vol_ok = _volume_ok(candles, 1.3)
    _, _, ichi = _ichimoku_proxy(closes)
    if closes[-1] > max(window) and vol_ok and ichi == "bullish" and bb_pos != "upper":
        return _base(candles, Side.LONG, 0.74, f"breakout with volume, Ichimoku, BB {bb_pos}", size, bars)
    return _base(candles, Side.FLAT, 0.35, "no confirmed breakout", 0.0, 1)


def _stable(candles: list[Candle]) -> Signal:
    deviation = abs(candles[-1].close - 1.0)
    if deviation >= 0.005:
        return _base(candles, Side.ALERT, 0.92, f"stablecoin depeg monitor: deviation {deviation:.4f}", 0.0, 1)
    if deviation >= 0.002:
        return _base(candles, Side.ALERT, 0.7, f"stablecoin watch band: deviation {deviation:.4f}", 0.0, 1)
    return _base(candles, Side.FLAT, 0.8, "stablecoin inside peg band", 0.0, 1)


def _defi(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    realised = fmean(abs(v) for v in _returns(closes[-8:]))
    adx = _adx_proxy(candles)
    _, _, _, bb_pos = _bb_proxy(closes)
    if regime is Regime.STRESS or realised > 0.06 or adx < 15 or bb_pos == "upper":
        return _base(candles, Side.FLAT, 0.48, "defi volatility, weak ADX or BB extension: stand aside", 0.0, 1)
    if closes[-1] > _ema(closes, 8):
        return _base(candles, Side.LONG, 0.72, f"defi trend in calm regime with ADX {adx:.1f}, BB {bb_pos}", 0.02, 10)
    return _base(candles, Side.FLAT, 0.4, "defi: no calm trend", 0.0, 1)


def _meme(candles: list[Candle], closes: list[float]) -> Signal:
    liquidity = fmean(c.volume for c in candles[-5:])
    burst = closes[-1] / closes[-4] - 1.0
    extension = closes[-1] / closes[-8] - 1.0
    vol_ok = _volume_ok(candles, 1.2)
    if liquidity < 1000:
        return _base(candles, Side.FLAT, 0.2, "meme liquidity proxy too thin", 0.0, 1)
    if extension > 0.40:
        return _base(candles, Side.FLAT, 0.35, "meme chase filter: 8-bar extension too large", 0.0, 1)
    if burst > 0.15 and vol_ok:
        return _base(candles, Side.LONG, 0.78, "meme momentum burst with volume; hard time stop applies", 0.005, 3)
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
        return _base(candles, Side.LONG, 0.7, "l2 relative strength versus benchmark", 0.03, 12)
    return _base(candles, Side.FLAT, 0.4, "l2 not leading benchmark", 0.0, 1)


def _rwa(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    gap = candles[-1].open / candles[-2].close - 1.0
    if abs(gap) > 0.08 or regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.5, "rwa gap or stress halt", 0.0, 1)
    if closes[-1] > _ema(closes, 8) and closes[-1] > closes[-5]:
        return _base(candles, Side.LONG, 0.67, "rwa slow trend", 0.02, 24)
    return _base(candles, Side.FLAT, 0.4, "rwa: no slow trend", 0.0, 1)


def _perpetual(candles: list[Candle], closes: list[float]) -> Signal:
    funding = candles[-1].funding_rate
    drift = closes[-1] / closes[-6] - 1.0
    if funding >= 0.001:
        return _base(candles, Side.ALERT, 0.7, "perp funding crowded: monitor, no carry", 0.0, 1)
    if funding <= -0.0005 and abs(drift) < 0.04:
        return _base(candles, Side.LONG, 0.75, "perp funding carry: negative funding, basis contained", 0.02, 8)
    if funding <= -0.0005:
        return _base(candles, Side.FLAT, 0.5, "perp funding attractive but drift not contained", 0.0, 1)
    return _base(candles, Side.FLAT, 0.4, "perp: no carry edge", 0.0, 1)
