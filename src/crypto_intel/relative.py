"""Major-pair relative sleeve. Information only, never a live order.

BTC and ETH stay in the major class. The sleeve records which one is leading
so a reviewer can see pair context that a single-symbol EMA cannot.
"""

from __future__ import annotations

from crypto_intel.models import Candle
from crypto_intel.regime import Regime, classify

RELATIVE_THRESHOLD = 0.04
SLEEVE_CAP = 0.02


def _six_bar(closes: list[float]) -> float:
    return closes[-1] / closes[-6] - 1.0


def major_relative(btc: list[Candle], eth: list[Candle]) -> dict[str, object]:
    """Compare six-bar ETH return with six-bar BTC return."""
    if len(btc) < 8 or len(eth) < 8:
        raise ValueError("relative sleeve needs at least 8 bars on both majors")
    btc_stress = classify(btc) is Regime.STRESS
    eth_stress = classify(eth) is Regime.STRESS
    excess = _six_bar([c.close for c in eth]) - _six_bar([c.close for c in btc])
    leader = "flat"
    size = 0.0
    reason = "majors: relative spread inside band"
    if btc_stress or eth_stress:
        reason = "majors: relative sleeve stood aside because a leg is in stress"
    elif excess >= RELATIVE_THRESHOLD:
        leader = "ETH-USD"
        size = SLEEVE_CAP
        reason = "majors: ETH leading BTC by the relative threshold"
    elif excess <= -RELATIVE_THRESHOLD:
        leader = "BTC-USD"
        size = SLEEVE_CAP
        reason = "majors: BTC leading ETH by the relative threshold"
    return {
        "sleeve": "eth_btc_relative",
        "asset_class": "major",
        "excess_return": round(excess, 4),
        "leader": leader,
        "size_fraction": size,
        "size_cap": SLEEVE_CAP,
        "reason": reason,
        "live_enabled": False,
    }
