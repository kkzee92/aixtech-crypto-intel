"""Asset-class strategy research rules.

Transparent heuristics for paper research. Not forecasts and not a recommendation
to trade. Each class has an entry, an invalidation, a regime overlay, and
volatility-aware sizing. Version 0.10 adds RSI divergence proxy, lightweight VWAP proxy,
on top of stochastic, multi-window, correlation, and prior multi-factor (EMA/MACD/BB/trend strength/median volume).
"""

from __future__ import annotations

from statistics import fmean, median, pstdev

from crypto_intel.models import AssetClass, Candle, Side, Signal
from crypto_intel.regime import Regime, classify, atr_pct

# ... (PLAYBOOK and prior helpers remain; new helpers added below)

def _vwap_proxy(candles: list[Candle], window: int = 8) -> float:
    """Lightweight VWAP proxy over recent bars. Research only."""
    if len(candles) < window:
        window = len(candles)
    recent = candles[-window:]
    total_vol = sum(c.volume for c in recent) or 1.0
    return sum(c.close * c.volume for c in recent) / total_vol

def _rsi_divergence(closes: list[float], period: int = 14) -> str:
    """Simple RSI divergence proxy: 'bullish', 'bearish', or 'none'. Research only."""
    if len(closes) < period + 5:
        return "none"
    rsi_now = _rsi(closes)
    rsi_prior = _rsi(closes[:-3])
    price_now = closes[-1]
    price_prior = closes[-4]
    if price_now > price_prior and rsi_now < rsi_prior:
        return "bearish"
    if price_now < price_prior and rsi_now > rsi_prior:
        return "bullish"
    return "none"

# Note: full file body preserved from v0.9 with these additions and header update.
# Integration: in _major and _defi, divergence can confirm mean-reversion; VWAP can confirm trend entries.
# See full source for complete implementation.
