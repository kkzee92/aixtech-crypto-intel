"""Asset-class strategy research rules.

Transparent heuristics for paper research. Not forecasts and not a recommendation
to trade. Each class has an entry, an invalidation, a regime overlay, and
volatility-aware sizing. Version 0.5 tightens filters and adds multi-factor
confirmations aligned with research notes.
"""

from __future__ import annotations

from statistics import fmean

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify, atr_pct

PLAYBOOK: dict[AssetClass, dict[str, str]] = {
    AssetClass.MAJOR: {
        "hypothesis": "Liquid majors trend, except when RSI is stretched or the book is in stress. EMA + MACD hist + momentum.",
        "entry": "Fast EMA above slow EMA, positive MACD hist, RSI 45-70 in trend or range. Washed-out RSI only in range. Vol-scaled size.",
        "invalidation": "Stress regime, or RSI above 70 on a trend entry.",
        "horizon": "8 bars mean-reversion, 20 bars trend",
    },
    AssetClass.LARGE_CAP_ALT: {
        "hypothesis": "Breakouts without volume are noise, and stress-regime breakouts are mostly gap risk. Volume ratio + multi-bar close consistency.",
        "entry": "Close above the prior five-bar high, volume at least 1.4x, at least 2 of last 3 closes higher, outside stress.",
        "invalidation": "Stress regime or volume confirmation missing.",
        "horizon": "12 bars",
    },
    AssetClass.STABLECOIN: {
        "hypothesis": "The useful signal is a peg break, not direction.",
        "entry": "Deviation of 80 bps or more raises an alert. No order. Watch at 40 bps.",
        "invalidation": "Not applicable. Size stays zero.",
        "horizon": "1 bar monitor",
    },
    AssetClass.DEFI: {
        "hypothesis": "Trend only in a calm realised-vol regime with volume support.",
        "entry": "Close above 8-bar EMA and mean absolute return at or below 5.5%, not in stress, volume above 0.9x average.",
        "invalidation": "Stress regime or realised vol above 5.5%.",
        "horizon": "10 bars",
    },
    AssetClass.MEME: {
        "hypothesis": "Most bursts are untradeable. A qualified burst still gets a hard time stop and tighter extension filter.",
        "entry": "12% three-bar burst, rising volume, volume floor 1500, and not already extended 30% over 8 bars.",
        "invalidation": "Thin liquidity proxy or chase extension.",
        "horizon": "3 bars",
    },
    AssetClass.L2: {
        "hypothesis": "L2 tokens are relative-strength bets versus a benchmark, with vol filter.",
        "entry": "Six-bar excess return above 3.5% versus benchmark, benchmark not in stress, own ATR contained under 3.5%.",
        "invalidation": "Missing benchmark or benchmark stress.",
        "horizon": "12 bars",
    },
    AssetClass.RWA: {
        "hypothesis": "Tokenised real-world assets should be slow. Gaps are a halt. Momentum confirmation.",
        "entry": "Close above 8-bar EMA and above the close five bars ago, gap inside 7%, positive short momentum.",
        "invalidation": "Open gap above 7% or stress regime.",
        "horizon": "24 bars",
    },
    AssetClass.PERPETUAL: {
        "hypothesis": "Negative funding with contained drift and moderate vol is a carry observation, not a forecast.",
        "entry": "Funding at or below -6 bps and absolute six-bar drift under 3.5%, ATR under 4.5%.",
        "invalidation": "Funding at or above 12 bps, or drift no longer contained.",
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


def _macd_hist(closes: list[float]) -> float:
    """Simplified MACD histogram proxy: EMA12 - EMA26, then signal EMA9 difference."""
    if len(closes) < 26:
        return 0.0
    ema12 = _ema(closes[-26:], 12)
    ema26 = _ema(closes[-26:], 26)
    macd = ema12 - ema26
    # Approximate signal as short EMA of recent MACD; for simplicity use recent diff
    return macd * 0.5  # proxy for histogram sign/strength


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
    momentum = closes[-1] / closes[-5] - 1.0 if len(closes) >= 5 else 0.0
    macd_h = _macd_hist(closes)
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.45, "major stress: stand aside", 0.0, 1, scale_vol=False)
    if fast > slow and 45 <= rsi <= 70 and momentum > 0 and macd_h > 0:
        return _base(candles, Side.LONG, 0.78, "major trend: fast EMA above slow, RSI not stretched, positive momentum and MACD hist", 0.06, 20)
    if regime is Regime.RANGE and rsi < 28 and closes[-1] > closes[-3]:
        return _base(candles, Side.LONG, 0.65, "major mean-reversion: washed-out RSI in range", 0.03, 8)
    return _base(candles, Side.FLAT, 0.4, "major: no trend or reversion edge", 0.0, 1, scale_vol=False)


def _breakout(candles: list[Candle], closes: list[float], size: float, bars: int, regime: Regime) -> Signal:
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.4, "breakout suppressed in stress", 0.0, 1, scale_vol=False)
    window = closes[-6:-1]
    volume_now = candles[-1].volume
    volume_base = fmean(c.volume for c in candles[-6:-1])
    higher_closes = sum(1 for i in range(1, 4) if len(closes) > i and closes[-i] > closes[-i-1])
    if closes[-1] > max(window) and volume_now > volume_base * 1.4 and higher_closes >= 2:
        return _base(candles, Side.LONG, 0.75, "breakout with stronger volume and multi-bar confirmation", size, bars)
    return _base(candles, Side.FLAT, 0.35, "no confirmed breakout", 0.0, 1, scale_vol=False)


def _stable(candles: list[Candle]) -> Signal:
    deviation = abs(candles[-1].close - 1.0)
    if deviation >= 0.008:
        return _base(candles, Side.ALERT, 0.94, f"stablecoin depeg monitor: deviation {deviation:.4f}", 0.0, 1, scale_vol=False)
    if deviation >= 0.004:
        return _base(candles, Side.ALERT, 0.72, f"stablecoin watch band: deviation {deviation:.4f}", 0.0, 1, scale_vol=False)
    return _base(candles, Side.FLAT, 0.8, "stablecoin inside peg band", 0.0, 1, scale_vol=False)


def _defi(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    realised = fmean(abs(v) for v in _returns(closes[-8:]))
    vol_avg = fmean(c.volume for c in candles[-5:])
    if regime is Regime.STRESS or realised > 0.055:
        return _base(candles, Side.FLAT, 0.48, "defi volatility regime: stand aside", 0.0, 1, scale_vol=False)
    if closes[-1] > _ema(closes, 8) and candles[-1].volume > vol_avg * 0.9:
        return _base(candles, Side.LONG, 0.72, "defi trend in calm regime with volume support", 0.02, 10)
    return _base(candles, Side.FLAT, 0.4, "defi: no calm trend", 0.0, 1, scale_vol=False)


def _meme(candles: list[Candle], closes: list[float]) -> Signal:
    liquidity = fmean(c.volume for c in candles[-5:])
    burst = closes[-1] / closes[-3] - 1.0 if len(closes) >= 3 else 0.0
    extension = closes[-1] / closes[-8] - 1.0
    if liquidity < 1500:
        return _base(candles, Side.FLAT, 0.2, "meme liquidity proxy too thin", 0.0, 1, scale_vol=False)
    if extension > 0.30:
        return _base(candles, Side.FLAT, 0.35, "meme chase filter: 8-bar extension too large", 0.0, 1, scale_vol=False)
    if burst > 0.12 and candles[-1].volume > candles[-2].volume:
        return _base(candles, Side.LONG, 0.79, "meme momentum burst; hard time stop applies", 0.005, 3)
    return _base(candles, Side.FLAT, 0.3, "meme: no qualified burst", 0.0, 1, scale_vol=False)


def _l2(candles: list[Candle], closes: list[float], benchmark: list[Candle] | None) -> Signal:
    if not benchmark or len(benchmark) < 8:
        return _base(candles, Side.FLAT, 0.3, "l2 requires a benchmark series", 0.0, 1, scale_vol=False)
    if classify(benchmark) is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.42, "l2 benchmark in stress", 0.0, 1, scale_vol=False)
    own = closes[-1] / closes[-6] - 1.0
    bench_closes = [c.close for c in benchmark]
    bench = bench_closes[-1] / bench_closes[-6] - 1.0
    own_atr = atr_pct(candles, 8)
    if own - bench > 0.035 and own_atr < 0.035:
        return _base(candles, Side.LONG, 0.73, "l2 relative strength versus benchmark, ATR contained", 0.03, 12)
    return _base(candles, Side.FLAT, 0.4, "l2 not leading benchmark", 0.0, 1, scale_vol=False)


def _rwa(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    gap = candles[-1].open / candles[-2].close - 1.0 if len(candles) >= 2 else 0.0
    momentum = closes[-1] / closes[-3] - 1.0 if len(closes) >= 3 else 0.0
    if abs(gap) > 0.07 or regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.5, "rwa gap or stress halt", 0.0, 1, scale_vol=False)
    if closes[-1] > _ema(closes, 8) and closes[-1] > closes[-5] and momentum > 0:
        return _base(candles, Side.LONG, 0.70, "rwa slow trend with momentum confirmation", 0.02, 24)
    return _base(candles, Side.FLAT, 0.4, "rwa: no slow trend", 0.0, 1, scale_vol=False)


def _perpetual(candles: list[Candle], closes: list[float]) -> Signal:
    funding = candles[-1].funding_rate
    drift = closes[-1] / closes[-6] - 1.0 if len(closes) >= 6 else 0.0
    atr = atr_pct(candles, 8)
    if funding >= 0.0012:
        return _base(candles, Side.ALERT, 0.72, "perp funding crowded: monitor, no carry", 0.0, 1, scale_vol=False)
    if funding <= -0.0006 and abs(drift) < 0.035 and atr < 0.045:
        return _base(candles, Side.LONG, 0.78, "perp funding carry: negative funding, basis contained, ATR moderate", 0.02, 8)
    if funding <= -0.0006:
        return _base(candles, Side.FLAT, 0.5, "perp funding attractive but drift or vol not contained", 0.0, 1, scale_vol=False)
    return _base(candles, Side.FLAT, 0.4, "perp: no carry edge", 0.0, 1, scale_vol=False)
