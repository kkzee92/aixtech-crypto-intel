"""Enhanced asset-class strategy research rules — v0.24 multi-factor overlays.

Transparent heuristics for paper research only. Not forecasts and not a recommendation
to trade. New multi-factor confirmation can only shrink or zero paper size.
Preserves all prior class rules and invariants.
"""

from __future__ import annotations

from statistics import fmean

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify


def _atr_pct(candles: list[Candle], period: int = 14) -> float:
    ranges = [(c.high - c.low) / c.close for c in candles[-period:] if c.close]
    return fmean(ranges) if ranges else 0.0


def _adaptive_ema_span(atr_pct: float, base: int = 8) -> int:
    """Shorter span in high vol, longer in low vol. Bounded."""
    if atr_pct > 0.04:
        return max(5, base - 3)
    if atr_pct < 0.015:
        return min(21, base + 5)
    return base


def _ema(values: list[float], span: int) -> float:
    alpha = 2.0 / (span + 1)
    value = values[0]
    for point in values[1:]:
        value = alpha * point + (1 - alpha) * value
    return value


def _rsi(closes: list[float], period: int = 14) -> float:
    changes = [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]
    changes = changes[-period:]
    gains = [max(c, 0.0) for c in changes]
    losses = [abs(min(c, 0.0)) for c in changes]
    average_loss = fmean(losses) if losses else 0.0
    if average_loss == 0:
        return 100.0
    rs = fmean(gains) / average_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _macd_hist(closes: list[float]) -> float:
    """Simple MACD histogram proxy (fast 12, slow 26)."""
    if len(closes) < 26:
        return 0.0
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    return ema12 - ema26


def _volume_confirm(candles: list[Candle], lookback: int = 20, mult: float = 1.1) -> bool:
    if len(candles) < lookback:
        return False
    avg = fmean(c.volume for c in candles[-lookback:-1])
    return candles[-1].volume >= avg * mult


def multi_factor_confirm(candles: list[Candle], side: Side) -> tuple[bool, str]:
    """Returns (passed, reason). Failure means size should be zeroed or halved."""
    if side is not Side.LONG:
        return True, "non-long"
    closes = [c.close for c in candles]
    rsi = _rsi(closes)
    macd_h = _macd_hist(closes)
    vol_ok = _volume_confirm(candles)
    regime = classify(candles)

    reasons = []
    if regime is Regime.STRESS:
        reasons.append("stress")
    if not vol_ok:
        reasons.append("volume")
    if rsi > 75 or rsi < 25:
        reasons.append("rsi_extreme")
    if macd_h <= 0:
        reasons.append("momentum")

    passed = len(reasons) == 0
    return passed, ",".join(reasons) if reasons else "aligned"


def apply_v024_overlay(signal: Signal, candles: list[Candle]) -> Signal:
    """Can only shrink size. Never raises. Never changes side to enable execution."""
    if signal.side is not Side.LONG or signal.size_fraction <= 0:
        return signal
    passed, reason = multi_factor_confirm(candles, signal.side)
    if not passed:
        new_size = 0.0 if "stress" in reason or "rsi_extreme" in reason else signal.size_fraction * 0.5
        return Signal(
            symbol=signal.symbol,
            asset_class=signal.asset_class,
            side=signal.side,
            confidence=max(0.0, signal.confidence - 0.1),
            reason=f"{signal.reason}; v024 multi-factor failed ({reason})",
            stop_distance_pct=signal.stop_distance_pct,
            size_fraction=round(new_size, 4),
            horizon_bars=signal.horizon_bars,
        )
    return signal
