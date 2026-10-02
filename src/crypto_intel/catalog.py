"""Versioned research-parameter catalog.

The catalog is the auditable description of each asset-class rule. Strategy
code remains the executable form. A digest lets a reviewer see when parameters
changed. These are research settings, not a promise of return.
"""

from __future__ import annotations

import hashlib
import json

from crypto_intel.models import AssetClass

CATALOG_VERSION = "0.3.0"

SPECS: dict[AssetClass, dict[str, object]] = {
    AssetClass.MAJOR: {
        "size_cap": 0.08,
        "cost_bps": 8.0,
        "fast_ema": 5,
        "slow_ema": 13,
        "rsi_low": 45,
        "rsi_high": 70,
        "reversion_rsi": 30,
        "horizon_trend": 20,
        "horizon_reversion": 8,
    },
    AssetClass.LARGE_CAP_ALT: {
        "size_cap": 0.04,
        "cost_bps": 14.0,
        "volume_multiple": 1.2,
        "breakout_lookback": 5,
        "horizon": 12,
    },
    AssetClass.STABLECOIN: {
        "size_cap": 0.0,
        "cost_bps": 2.0,
        "watch_deviation": 0.002,
        "depeg_deviation": 0.005,
        "horizon": 1,
    },
    AssetClass.DEFI: {
        "size_cap": 0.02,
        "cost_bps": 22.0,
        "vol_ceiling": 0.06,
        "ema": 8,
        "horizon": 10,
    },
    AssetClass.MEME: {
        "size_cap": 0.005,
        "cost_bps": 45.0,
        "burst": 0.15,
        "chase_extension": 0.40,
        "min_volume": 1000,
        "horizon": 3,
    },
    AssetClass.L2: {
        "size_cap": 0.03,
        "cost_bps": 16.0,
        "excess_return": 0.03,
        "lookback": 6,
        "horizon": 12,
    },
    AssetClass.RWA: {
        "size_cap": 0.02,
        "cost_bps": 12.0,
        "gap_halt": 0.08,
        "ema": 8,
        "horizon": 24,
    },
    AssetClass.PERPETUAL: {
        "size_cap": 0.02,
        "short_cap": 0.01,
        "cost_bps": 10.0,
        "carry_funding": -0.0005,
        "crowded_funding": 0.001,
        "drift_band": 0.04,
        "horizon_carry": 8,
        "horizon_fade": 4,
    },
}


def parameter_digest() -> str:
    """Stable digest of the research catalog. A change means the rules changed."""
    material = json.dumps(
        {"version": CATALOG_VERSION, "specs": {key.value: SPECS[key] for key in AssetClass}},
        sort_keys=True,
    )
    return hashlib.sha256(material.encode()).hexdigest()
