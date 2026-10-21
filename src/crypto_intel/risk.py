"""Risk gates. Strategies propose; this module decides.

Version 0.3 adds light volatility scaling so high-ATR environments shrink size.
"""

from __future__ import annotations

from crypto_intel.models import AssetClass, RiskDecision, Side, Signal
from crypto_intel.regime import atr_pct

CLASS_LIMITS: dict[AssetClass, float] = {
    AssetClass.MAJOR: 0.08,
    AssetClass.LARGE_CAP_ALT: 0.04,
    AssetClass.STABLECOIN: 0.0,
    AssetClass.DEFI: 0.02,
    AssetClass.MEME: 0.005,
    AssetClass.L2: 0.03,
    AssetClass.RWA: 0.02,
    AssetClass.PERPETUAL: 0.02,
}

MIN_CONFIDENCE = {
    AssetClass.MAJOR: 0.55,
    AssetClass.LARGE_CAP_ALT: 0.60,
    AssetClass.STABLECOIN: 0.50,
    AssetClass.DEFI: 0.65,
    AssetClass.MEME: 0.75,
    AssetClass.L2: 0.60,
    AssetClass.RWA: 0.60,
    AssetClass.PERPETUAL: 0.65,
}


def evaluate(
    signal: Signal,
    *,
    kill_switch: bool = False,
    drawdown: float = 0.0,
    max_drawdown: float = 0.12,
    gap_pct: float = 0.0,
    candles=None,
) -> RiskDecision:
    reasons: list[str] = []
    if kill_switch:
        reasons.append("kill switch engaged")
    if drawdown >= max_drawdown:
        reasons.append("max drawdown halt")
    if signal.asset_class is AssetClass.RWA and abs(gap_pct) > 0.08:
        reasons.append("rwa gap halt")
    if signal.asset_class is AssetClass.STABLECOIN and signal.side is not Side.ALERT:
        reasons.append("stablecoins are monitor-only")
    if signal.confidence < MIN_CONFIDENCE[signal.asset_class]:
        reasons.append("confidence below class threshold")
    cap = CLASS_LIMITS[signal.asset_class]
    size = min(signal.size_fraction, cap)
    if candles and len(candles) >= 8:
        vol = atr_pct(candles)
        if vol > 0.04:
            scale = max(0.5, 1.0 - (vol - 0.04) * 5)
            size = round(size * scale, 4)
            reasons.append(f"volatility scale applied (atr={vol:.3f})")
    if signal.side is Side.ALERT:
        reasons.append("monitor only, no order")
    if signal.side is Side.FLAT:
        size = 0.0
    if reasons and not (len(reasons) == 1 and "volatility" in reasons[0]):
        return RiskDecision(False, 0.0, tuple(reasons))
    if size <= 0 and signal.side is Side.LONG:
        reasons.append("class size cap is zero")
        return RiskDecision(False, 0.0, tuple(reasons))
    if not reasons:
        reasons = ["within class limits"]
    return RiskDecision(True, size, tuple(reasons))
