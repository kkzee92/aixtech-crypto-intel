"""Declared research cost assumptions by asset class.

These are not live venue fees. They keep paper results from ignoring friction.
"""

from __future__ import annotations

from crypto_intel.models import AssetClass

# Round-trip assumption in basis points: spread + slippage + a small fee buffer.
COST_BPS: dict[AssetClass, float] = {
    AssetClass.MAJOR: 8.0,
    AssetClass.LARGE_CAP_ALT: 14.0,
    AssetClass.STABLECOIN: 2.0,
    AssetClass.DEFI: 22.0,
    AssetClass.MEME: 45.0,
    AssetClass.L2: 16.0,
    AssetClass.RWA: 12.0,
    AssetClass.PERPETUAL: 10.0,
}


def round_trip_cost(asset_class: AssetClass) -> float:
    return COST_BPS[asset_class] / 10_000.0
