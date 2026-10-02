"""Chronological paper split. Scores describe the supplied series only."""

from __future__ import annotations

from crypto_intel.engine import backtest
from crypto_intel.models import Candle


def split_walkforward(candles: list[Candle], train_fraction: float = 0.7) -> dict[str, object]:
    if not 0.5 <= train_fraction < 1.0:
        raise ValueError("train_fraction must be in [0.5, 1)")
    if len(candles) < 16:
        raise ValueError("walk-forward split needs at least 16 bars")
    cut = int(len(candles) * train_fraction)
    cut = min(max(cut, 10), len(candles) - 6)
    train = backtest(candles[:cut])
    holdout = backtest(candles[cut - 8 :])
    return {
        "symbol": candles[-1].symbol,
        "asset_class": candles[-1].asset_class.value,
        "train_bars": cut,
        "holdout_bars": len(candles) - cut + 8,
        "train": train,
        "holdout": holdout,
        "note": "Synthetic or supplied-series research score. Not a forecast.",
        "live_enabled": False,
    }
