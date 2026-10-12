"""Asset-class strategy research rules.

Transparent heuristics for paper research. Not forecasts and not a recommendation
to trade. Each class has an entry, an invalidation, and a regime overlay.
Version 0.28 adds MACD histogram, Bollinger width, and additional class guards.
"""

from __future__ import annotations

from statistics import fmean, stdev

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify

PLAYBOOK: dict[AssetClass, dict[str, str]] = {
    AssetClass.MAJOR: {
        "hypothesis": "Liquid majors trend, except when RSI is stretched or the book is in stress. Volume, multi-TF EMA, MACD, and Bollinger width reduce false breaks.",
        "entry": "Fast EMA above slow EMA with RSI 45-70, rising volume, 21-bar EMA not falling, positive MACD histogram, and BB width not contracted, outside stress.",
        "invalidation": "Stress regime, RSI above 70, falling volume, declining longer EMA, negative MACD, or low BB width.",
        "horizon": "8 bars mean-reversion, 20 bars trend",
    },
    AssetClass.LARGE_CAP_ALT: {
        "hypothesis": "Breakouts without volume are noise, and stress-regime breakouts are mostly gap risk. RSI guard, volume acceleration, and relative volume percentile avoid weak chase.",
        "entry": "Close above the prior five-bar high, volume ≥1.2x base and accelerating, RSI under 75, volume percentile high, outside stress.",
        "invalidation": "Stress regime, volume confirmation missing, or RSI stretched.",
        "horizon": "12 bars",
    },
    AssetClass.STABLECOIN: {
        "hypothesis": "The useful signal is a peg break, not direction. Persistence preferred.",
        "entry": "Deviation of 50 bps or more raises an alert (2-bar preferred). No order.",
        "invalidation": "Not applicable. Size stays zero.",
        "horizon": "1 bar monitor",
    },
    AssetClass.DEFI: {
        "hypothesis": "Trend only in a calm realised-vol regime with supporting volume, multi-timeframe confirmation, and vol decay.",
        "entry": "Close above 8-bar EMA, 8-bar and 13-bar realised vol ≤6%/5%, rising volume, vol not expanding, not in stress.",
        "invalidation": "Stress regime, elevated vol, or falling volume.",
        "horizon": "10 bars",
    },
    AssetClass.MEME: {
        "hypothesis": "Most bursts are untradeable. A qualified burst still gets a hard time stop, tighter liquidity, volume acceleration, and anti-pump check.",
        "entry": "15% four-bar burst, rising and accelerating volume, volume floor of 2000, not extended 40%, and price not lagging volume spike.",
        "invalidation": "Thin liquidity proxy, chase extension, or volume-only pump.",
        "horizon": "3 bars",
    },
    AssetClass.L2: {
        "hypothesis": "L2 tokens are relative-strength bets versus a non-declining benchmark, with multi-period consistency.",
        "entry": "Six-bar excess return above 3% versus benchmark, own return positive, benchmark not in stress/declining, and RS consistent over 3 periods.",
        "invalidation": "Missing benchmark, benchmark stress, or inconsistent RS.",
        "horizon": "12 bars",
    },
    AssetClass.RWA: {
        "hypothesis": "Tokenised real-world assets should be slow. Gaps are a halt. Low realised vol, participation, and volume/ATR preferred.",
        "entry": "Close above 8-bar EMA and above the close five bars ago, gap inside 8%, realised vol under 3%, volume not collapsing, participation score ok.",
        "invalidation": "Open gap above 8% or stress regime.",
        "horizon": "24 bars",
    },
    AssetClass.PERPETUAL: {
        "hypothesis": "Negative funding with contained drift, persistence, and MA confirmation is a carry observation. Crowded funding with extension is a paper short fade.",
        "entry": "Negative funding with 3-bar persistence, MA negative, and drift inside 4%. Crowded funding plus drift above 4% is a paper short fade.",
        "invalidation": "Crowded funding without extended drift is an alert, not a fade.",
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


def _macd_histogram(closes: list[float]) -> float:
    if len(closes) < 26:
        return 0.0
    ema12 = _ema(closes[-26:], 12)
    ema26 = _ema(closes[-26:], 26)
    return ema12 - ema26


def _bb_width(closes: list[float], period: int = 20) -> float:
    if len(closes) < period:
        return 0.1
    window = closes[-period:]
    mean = fmean(window)
    if mean == 0:
        return 0.1
    sd = stdev(window) if len(window) > 1 else 0.0
    return (4 * sd) / mean  # approx 2-std width relative


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


def _volume_rising(candles: list[Candle], bars: int = 3) -> bool:
    if len(candles) < bars + 1:
        return False
    recent = [c.volume for c in candles[-bars:]]
    return recent[-1] > fmean(recent[:-1]) if recent[:-1] else True


def _volume_accelerating(candles: list[Candle]) -> bool:
    if len(candles) < 5:
        return False
    prior = fmean(c.volume for c in candles[-4:-1])
    return candles[-1].volume > prior * 1.5 if prior else True


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
    longer = _ema(closes, 21) if len(closes) >= 21 else slow
    rsi = _rsi(closes)
    vol_ok = _volume_rising(candles)
    mtf_ok = longer >= _ema(closes[:-1], 21) if len(closes) >= 22 else True
    macd_ok = _macd_histogram(closes) > 0
    bb_ok = _bb_width(closes) > 0.02
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.45, "major stress: stand aside", 0.0, 1)
    if fast > slow and 45 <= rsi <= 70 and vol_ok and mtf_ok and macd_ok and bb_ok:
        return _base(candles, Side.LONG, 0.80, "major trend: EMA cross, RSI, volume, multi-TF, MACD, BB width ok", 0.06, 20)
    if regime is Regime.RANGE and rsi < 30 and closes[-1] > closes[-3]:
        return _base(candles, Side.LONG, 0.64, "major mean-reversion: washed-out RSI in range", 0.03, 8)
    return _base(candles, Side.FLAT, 0.4, "major: no trend or reversion edge", 0.0, 1)


def _breakout(candles: list[Candle], closes: list[float], size: float, bars: int, regime: Regime) -> Signal:
    if regime is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.4, "breakout suppressed in stress", 0.0, 1)
    window = closes[-6:-1]
    volume_now = candles[-1].volume
    volume_base = fmean(c.volume for c in candles[-6:-1])
    rsi = _rsi(closes)
    accel = _volume_accelerating(candles)
    vols = [c.volume for c in candles[-20:]] if len(candles) >= 20 else [c.volume for c in candles]
    vol_pct = sum(1 for v in vols if v < volume_now) / len(vols) if vols else 0.5
    if closes[-1] > max(window) and volume_now > volume_base * 1.2 and rsi < 75 and accel and vol_pct > 0.7:
        return _base(candles, Side.LONG, 0.76, "breakout with volume confirmation, acceleration, RSI and percentile guard", size, bars)
    return _base(candles, Side.FLAT, 0.35, "no confirmed breakout", 0.0, 1)


def _stable(candles: list[Candle]) -> Signal:
    deviation = abs(candles[-1].close - 1.0)
    persistent = len(candles) >= 2 and abs(candles[-2].close - 1.0) >= 0.002
    if deviation >= 0.005:
        reason = f"stablecoin depeg monitor: deviation {deviation:.4f}"
        if persistent:
            reason += " (persistent)"
        return _base(candles, Side.ALERT, 0.94 if persistent else 0.92, reason, 0.0, 1)
    if deviation >= 0.002:
        return _base(candles, Side.ALERT, 0.72, f"stablecoin watch band: deviation {deviation:.4f}", 0.0, 1)
    return _base(candles, Side.FLAT, 0.8, "stablecoin inside peg band", 0.0, 1)


def _defi(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    realised8 = fmean(abs(v) for v in _returns(closes[-8:])) if len(closes) >= 8 else 1.0
    realised13 = fmean(abs(v) for v in _returns(closes[-13:])) if len(closes) >= 13 else realised8
    vol_ok = _volume_rising(candles)
    vol_decay = realised8 <= realised13 * 1.1 if realised13 else True
    if regime is Regime.STRESS or realised8 > 0.06 or realised13 > 0.05 or not vol_ok or not vol_decay:
        return _base(candles, Side.FLAT, 0.48, "defi volatility, volume or expansion regime: stand aside", 0.0, 1)
    if closes[-1] > _ema(closes, 8):
        return _base(candles, Side.LONG, 0.74, "defi trend in calm multi-TF regime with volume and decay", 0.02, 10)
    return _base(candles, Side.FLAT, 0.4, "defi: no calm trend", 0.0, 1)


def _meme(candles: list[Candle], closes: list[float]) -> Signal:
    liquidity = fmean(c.volume for c in candles[-5:])
    burst = closes[-1] / closes[-4] - 1.0
    extension = closes[-1] / closes[-8] - 1.0
    accel = _volume_accelerating(candles)
    # anti-pump: volume spike without price confirmation
    price_follow = closes[-1] > closes[-2]
    if liquidity < 2000:
        return _base(candles, Side.FLAT, 0.2, "meme liquidity proxy too thin", 0.0, 1)
    if extension > 0.40:
        return _base(candles, Side.FLAT, 0.35, "meme chase filter: 8-bar extension too large", 0.0, 1)
    if burst > 0.15 and candles[-1].volume > candles[-2].volume and accel and price_follow:
        return _base(candles, Side.LONG, 0.81, "meme momentum burst with acceleration and price follow; hard time stop applies", 0.005, 3)
    return _base(candles, Side.FLAT, 0.3, "meme: no qualified burst", 0.0, 1)


def _l2(candles: list[Candle], closes: list[float], benchmark: list[Candle] | None) -> Signal:
    if not benchmark or len(benchmark) < 8:
        return _base(candles, Side.FLAT, 0.3, "l2 requires a benchmark series", 0.0, 1)
    if classify(benchmark) is Regime.STRESS:
        return _base(candles, Side.FLAT, 0.42, "l2 benchmark in stress", 0.0, 1)
    own = closes[-1] / closes[-6] - 1.0
    bench_closes = [c.close for c in benchmark]
    bench = bench_closes[-1] / bench_closes[-6] - 1.0
    bench8 = bench_closes[-1] / bench_closes[-8] - 1.0 if len(bench_closes) >= 8 else 0.0
    # simple multi-period consistency
    rs1 = (closes[-1] / closes[-3] - 1) - (bench_closes[-1] / bench_closes[-3] - 1) if len(closes) >= 3 and len(bench_closes) >= 3 else 0
    rs2 = (closes[-1] / closes[-6] - 1) - (bench_closes[-1] / bench_closes[-6] - 1)
    consistent = rs1 > 0 and rs2 > 0
    if own - bench > 0.03 and own > 0 and bench8 >= 0 and consistent:
        return _base(candles, Side.LONG, 0.75, "l2 relative strength versus non-declining benchmark with consistency", 0.03, 12)
    return _base(candles, Side.FLAT, 0.4, "l2 not leading benchmark", 0.0, 1)


def _rwa(candles: list[Candle], closes: list[float], regime: Regime) -> Signal:
    gap = candles[-1].open / candles[-2].close - 1.0
    realised = fmean(abs(v) for v in _returns(closes[-8:])) if len(closes) >= 8 else 0.0
    vol_ok = _volume_rising(candles, bars=5)
    atr = _atr_pct(candles)
    participation = (candles[-1].volume / max(atr, 0.001)) if atr else 0
    part_ok = participation > 1000  # synthetic threshold
    if abs(gap) > 0.08 or regime is Regime.STRESS or realised > 0.03 or not vol_ok or not part_ok:
        return _base(candles, Side.FLAT, 0.5, "rwa gap, stress, elevated vol, thin participation or low volume/ATR halt", 0.0, 1)
    if closes[-1] > _ema(closes, 8) and closes[-1] > closes[-5]:
        return _base(candles, Side.LONG, 0.71, "rwa slow trend in low vol with participation", 0.02, 24)
    return _base(candles, Side.FLAT, 0.4, "rwa: no slow trend", 0.0, 1)


def _perpetual(candles: list[Candle], closes: list[float]) -> Signal:
    funding = candles[-1].funding_rate
    drift = closes[-1] / closes[-6] - 1.0
    persistent = all(c.funding_rate <= -0.0005 for c in candles[-3:]) if len(candles) >= 3 else False
    funding_ma = fmean(c.funding_rate for c in candles[-5:]) if len(candles) >= 5 else funding
    if funding >= 0.001 and drift > 0.04:
        return _base(candles, Side.SHORT, 0.68, "perp crowded-funding fade research; hard size cap", 0.01, 4)
    if funding >= 0.001:
        return _base(candles, Side.ALERT, 0.7, "perp funding crowded: monitor, no fade", 0.0, 1)
    if funding <= -0.0005 and abs(drift) < 0.04 and persistent and funding_ma < -0.0003:
        return _base(candles, Side.LONG, 0.78, "perp funding carry: negative funding with persistence, MA, basis contained", 0.02, 8)
    if funding <= -0.0005:
        return _base(candles, Side.FLAT, 0.5, "perp funding attractive but drift, persistence or MA not confirmed", 0.0, 1)
    return _base(candles, Side.FLAT, 0.4, "perp: no carry edge", 0.0, 1)
