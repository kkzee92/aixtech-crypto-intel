"""Volatility-targeted paper size. Never raises a class cap.

Liquid-staking symbols are a DeFi sleeve with a tighter cap. The sleeve is an
information overlay, not a new asset class.
"""

from __future__ import annotations

from statistics import fmean

from crypto_intel.catalog import SPECS
from crypto_intel.models import AssetClass, Candle

TARGET_VOL: dict[AssetClass, float] = {
    AssetClass.MAJOR: 0.020,
    AssetClass.LARGE_CAP_ALT: 0.030,
    AssetClass.STABLECOIN: 0.0,
    AssetClass.DEFI: 0.025,
    AssetClass.MEME: 0.050,
    AssetClass.L2: 0.028,
    AssetClass.RWA: 0.015,
    AssetClass.PERPETUAL: 0.020,
}
LST_CAP = 0.01


def realised_vol(candles: list[Candle]) -> float:
    closes = [candle.close for candle in candles[-9:]]
    if len(closes) < 2:
        return 0.0
    moves = [abs(closes[index] / closes[index - 1] - 1.0) for index in range(1, len(closes))]
    return fmean(moves)


def class_cap(symbol: str, asset_class: AssetClass) -> float:
    cap = float(SPECS[asset_class]["size_cap"])
    if symbol.endswith("-LST") or symbol.endswith("/LST"):
        return min(cap, LST_CAP)
    return cap


def vol_targeted_size(base: float, candles: list[Candle], asset_class: AssetClass) -> float:
    symbol = candles[-1].symbol if candles else ""
    cap = class_cap(symbol, asset_class)
    target = TARGET_VOL[asset_class]
    if base <= 0 or cap <= 0 or target <= 0:
        return 0.0
    realised = realised_vol(candles)
    if realised <= 0:
        return 0.0
    scaled = base * min(1.0, target / realised)
    return round(min(scaled, cap, base), 6)
