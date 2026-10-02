"""Informed paper decision: quality, class rule, confirmation, vol targeting.

The v0.3 `run_once` path is unchanged. This module is the v0.4 information
path used by `crypto-intel intel`. It still cannot place a live order.
"""

from __future__ import annotations

from crypto_intel.confirm import confirm
from crypto_intel.models import Candle, ExecutionMode, Side, Signal
from crypto_intel.quality import assess
from crypto_intel.regime import classify
from crypto_intel.risk import evaluate
from crypto_intel.security import assert_paper_only
from crypto_intel.sizing import vol_targeted_size
from crypto_intel.strategies import signal_for


def inform(
    candles: list[Candle],
    *,
    benchmark: list[Candle] | None = None,
    kill_switch: bool = False,
    drawdown: float = 0.0,
    mode: ExecutionMode = ExecutionMode.PAPER,
) -> dict[str, object]:
    assert_paper_only(mode)
    quality = assess(candles)
    signal = signal_for(candles, benchmark)
    confirmed, confirmation = confirm(candles, signal, benchmark)
    gap = 0.0
    if len(candles) >= 2 and candles[-2].close:
        gap = candles[-1].open / candles[-2].close - 1.0
    decision = evaluate(signal, kill_switch=kill_switch, drawdown=drawdown, gap_pct=gap)
    size = decision.size_fraction
    reasons = list(decision.reasons)
    side = signal.side
    if not quality.ok:
        size = 0.0
        if side in {Side.LONG, Side.SHORT}:
            side = Side.FLAT
        reasons.append("quality gate: " + ",".join(quality.issues))
    elif not confirmed:
        size = 0.0
        if side in {Side.LONG, Side.SHORT}:
            side = Side.FLAT
        reasons.append(confirmation)
    else:
        size = vol_targeted_size(size, candles, signal.asset_class)
        reasons.append(confirmation)
    return {
        "symbol": signal.symbol,
        "asset_class": signal.asset_class.value,
        "regime": classify(candles).value,
        "primary_side": signal.side.value,
        "side": side.value,
        "confidence": signal.confidence,
        "size_fraction": size,
        "quality_ok": quality.ok,
        "quality_score": quality.score,
        "quality_issues": list(quality.issues),
        "confirmation": confirmation,
        "reason": signal.reason,
        "notes": reasons,
        "mode": mode.value,
        "live_enabled": False,
    }


def sleeve(signal: Signal) -> str:
    if signal.symbol.endswith("-LST") or signal.symbol.endswith("/LST"):
        return "liquid_staking"
    return signal.asset_class.value
