"""Walk-forward paper scorecard by asset class.

Results describe the synthetic fixture after declared costs. They are not
forecasts.
"""

from __future__ import annotations

from crypto_intel.engine import backtest
from crypto_intel.models import AssetClass, Candle
from crypto_intel.security import AuditLog


def score_book(grouped: dict[str, list[Candle]]) -> dict[str, object]:
    by_class: dict[str, dict[str, float]] = {}
    rows = []
    for symbol, series in grouped.items():
        asset_class = series[-1].asset_class
        result = backtest(series, audit=AuditLog())
        row = {
            "symbol": symbol,
            "asset_class": asset_class.value,
            "ending_equity": result["ending_equity"],
            "trades": result["trades"],
            "max_drawdown": result["max_drawdown"],
        }
        rows.append(row)
        bucket = by_class.setdefault(
            asset_class.value,
            {"symbols": 0.0, "trades": 0.0, "ending_equity_sum": 0.0},
        )
        bucket["symbols"] += 1
        bucket["trades"] += result["trades"]
        bucket["ending_equity_sum"] += result["ending_equity"]
    summary = []
    for asset_class in AssetClass:
        bucket = by_class.get(asset_class.value)
        if not bucket:
            continue
        summary.append(
            {
                "asset_class": asset_class.value,
                "symbols": int(bucket["symbols"]),
                "trades": bucket["trades"],
                "mean_ending_equity": round(bucket["ending_equity_sum"] / bucket["symbols"], 6),
            }
        )
    return {
        "mode": "paper",
        "fixture": "synthetic",
        "disclaimer": "scores describe the fixture after declared costs, not future returns",
        "classes": summary,
        "rows": rows,
    }
